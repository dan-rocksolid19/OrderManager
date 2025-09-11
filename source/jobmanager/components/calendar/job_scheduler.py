from datetime import timedelta, date
from typing import Optional, Tuple, List, Dict, Any

# Minimal logger protocol for typing
class _Logger:
    def debug(self, msg: str): ...
    def info(self, msg: str): ...
    def warning(self, msg: str): ...
    def error(self, msg: str): ...


class Move:
    def __init__(self, id: Any, old_start: date, old_end: date, new_start: date, new_end: date):
        self.id = id
        self.old_start = old_start
        self.old_end = old_end
        self.new_start = new_start
        self.new_end = new_end

    def __repr__(self):
        return f"Move(id={self.id}, {self.old_start}..{self.old_end} -> {self.new_start}..{self.new_end})"


def apply_block_shift(dao, entry_id: int, updated_data: dict, logger: Optional[_Logger] = None) -> Tuple[bool, List[Move], Optional[str]]:
    """
    Block-shift strategy when editing an existing entry.
    Rules:
      - Entries with start_date < orig_start are untouched.
      - If beta = new_end - orig_end is 0 days, only update the edited entry.
      - If beta != 0, shift every entry with start_date >= orig_start by beta days
        (both start_date and end_date). Respect lock_dates/fixed_dates by skipping them.
      - Overlaps are allowed. No attempt to resolve.

    Returns (ok, applied_moves, err).
    """
    # Load current entry
    current = dao.get_entry_by_id(entry_id)
    if not current:
        return False, [], f"Entry {entry_id} not found"

    orig_start: date = current.get('start_date')
    orig_end: date = current.get('end_date') or orig_start

    # Normalize new dates from payload, defaulting to current
    new_start: date = updated_data.get('start_date') or orig_start
    new_end: date = updated_data.get('end_date') or new_start
    if new_end < new_start:
        new_end = new_start

    # Compute beta (end shift) in days
    beta_days: int = (new_end - orig_end).days

    # If beta == 0, simply update the target entry; do not move others
    if beta_days == 0:
        payload = dict(updated_data)
        payload['start_date'] = new_start
        payload['end_date'] = new_end
        ok = dao.update_entry(entry_id, payload)
        if not ok:
            return False, [], f"Failed to update entry {entry_id}"
        if logger:
            try:
                logger.info(f"apply_block_shift: updated entry_id={entry_id} (beta=0; no follower shifts)")
            except Exception:
                pass
        return True, [], None

    # beta != 0: shift the block of entries with start_date >= orig_start
    # Build a wide range starting at orig_start to fetch potentially affected entries.
    rng_start = orig_start

    # Add upper bound to include far-future followers
    rng_end = new_end + timedelta(days=3650)

    if logger:
        try:
            logger.info(f"apply_block_shift: entry_id={entry_id} beta={beta_days}d; selecting entries with start_date >= {orig_start}")
        except Exception:
            pass

    # Fetch entries in a wide range, then filter by start_date >= orig_start
    entries: List[Dict[str, Any]] = dao.get_entries_by_date_range(rng_start, rng_end) or []

    # Ensure we include the target even if not returned by range (should be included though)
    # Filter: start_date >= orig_start, and skip locked/fixed.
    to_shift: List[Dict[str, Any]] = []
    for e in entries:
        s = e.get('start_date')
        if not s:
            continue
        if s < orig_start:
            continue
        # Respect lock/fixed dates: skip if true
        if bool(e.get('lock_dates', False)):
            continue
        to_shift.append(e)

    # Deduplicate and ensure target included (if it meets filter it will be updated separately anyway)
    seen_ids = set()
    filtered: List[Dict[str, Any]] = []
    for e in to_shift:
        eid = e.get('id')
        if eid in seen_ids:
            continue
        seen_ids.add(eid)
        filtered.append(e)

    applied: List[Move] = []

    # Apply shifts to followers (including any with start inside original interval); do NOT touch entries before orig_start
    for e in filtered:
        eid = e.get('id')
        if eid == entry_id:
            # We'll update the edited entry after loop using updated_data; skip here
            continue
        old_s: date = e.get('start_date')
        old_e: date = e.get('end_date') or old_s
        new_s = old_s + timedelta(days=beta_days)
        new_e = old_e + timedelta(days=beta_days)
        if dao.update_entry(eid, {'start_date': new_s, 'end_date': new_e}):
            applied.append(Move(eid, old_s, old_e, new_s, new_e))
            if logger:
                try:
                    logger.debug(f"apply_block_shift: shifted id={eid} {old_s}..{old_e} -> {new_s}..{new_e}")
                except Exception:
                    pass
        else:
            if logger:
                logger.error(f"apply_block_shift: failed to update follower {eid} to {new_s}..{new_e}")

    # Finally, update the edited entry to requested new_start/new_end and other fields
    payload = dict(updated_data)
    payload['start_date'] = new_start
    payload['end_date'] = new_end
    if not dao.update_entry(entry_id, payload):
        return False, applied, f"Failed to update target entry {entry_id}"

    if logger:
        try:
            logger.info(f"apply_block_shift: done; target id={entry_id} updated, shifted followers={len(applied)}")
        except Exception:
            pass

    return True, applied, None
