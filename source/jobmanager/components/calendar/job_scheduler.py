from datetime import timedelta, date
from typing import Optional, List, Dict, Any

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


class SchedulerError(Exception):
    pass


# Helpers centralized here to avoid duplication with UI

def _normalize_dates_and_beta(current: Dict[str, Any], updated_data: Dict[str, Any]):
    orig_start: date = current.get('start_date')
    orig_end: date = current.get('end_date') or orig_start
    new_start: date = updated_data.get('start_date') or orig_start
    new_end: date = updated_data.get('end_date') or new_start
    if new_end < new_start:
        new_end = new_start
    beta_days: int = (new_end - orig_end).days
    return orig_start, orig_end, new_start, new_end, beta_days


def _select_followers(dao, orig_start: date, entry_id: Any) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = dao.get_entries_by_date_range(
        orig_start,
        None,
        exclude_locked=True,
    ) or []
    return [e for e in entries if e.get('id') != entry_id]


def preview_block_shift(dao, entry_id: int, updated_data: dict) -> Dict[str, Any]:
    """
    Build a non-mutating preview of the block shift.
    Returns dict with keys: beta_days, has_followers, first_start, last_start, count.
    Raises SchedulerError when entry is not found.
    """
    current = dao.get_entry_by_id(entry_id)
    if not current:
        raise SchedulerError(f"Entry {entry_id} not found")

    orig_start, orig_end, new_start, new_end, beta_days = _normalize_dates_and_beta(current, updated_data)

    result: Dict[str, Any] = {
        'beta_days': beta_days,
        'has_followers': False,
        'first_start': None,
        'last_start': None,
        'count': 0,
    }

    if beta_days != 0:
        followers = _select_followers(dao, orig_start, entry_id)
        if followers:
            result['has_followers'] = True
            result['count'] = len(followers)
            # followers already exclude the target
            first_start = min(e.get('start_date') for e in followers)
            last_start = max(e.get('start_date') for e in followers)
            result['first_start'] = first_start
            result['last_start'] = last_start

    return result


def apply_block_shift(dao, entry_id: int, updated_data: dict, logger: Optional[_Logger] = None) -> List[Move]:
    """
    Block-shift strategy when editing an existing entry.
    Rules:
      - Entries with start_date < orig_start are untouched.
      - If beta = new_end - orig_end is 0 days, only update the edited entry.
      - If beta != 0, shift every entry with start_date >= orig_start by beta days
        (both start_date and end_date). Overlaps are allowed.

    Returns the list of follower moves applied. Raises SchedulerError on failure.
    """
    # Load current entry
    current = dao.get_entry_by_id(entry_id)
    if not current:
        raise SchedulerError(f"Entry {entry_id} not found")

    orig_start, orig_end, new_start, new_end, beta_days = _normalize_dates_and_beta(current, updated_data)

    # If beta == 0, simply update the target entry; do not move others
    if beta_days == 0:
        payload = dict(updated_data)
        payload['start_date'] = new_start
        payload['end_date'] = new_end
        ok = dao.update_entry(entry_id, payload)
        if not ok:
            raise SchedulerError(f"Failed to update entry {entry_id}")
        if logger:
            try:
                logger.info(f"apply_block_shift: updated entry_id={entry_id} (beta=0; no follower shifts)")
            except Exception:
                pass
        return []

    # beta != 0: shift the block of entries with start_date >= orig_start
    if logger:
        try:
            logger.info(f"apply_block_shift: entry_id={entry_id} beta={beta_days}d; followers with start_date >= {orig_start}")
        except Exception:
            pass

    followers = _select_followers(dao, orig_start, entry_id)

    applied: List[Move] = []

    # Transaction: followers + target together
    with dao.database.transaction():
        for e in followers:
            eid = e.get('id')
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
                raise SchedulerError(f"Failed to update follower {eid}")

        payload = dict(updated_data)
        payload['start_date'] = new_start
        payload['end_date'] = new_end
        if not dao.update_entry(entry_id, payload):
            raise SchedulerError(f"Failed to update entry {entry_id}")

    if logger:
        try:
            logger.info(f"apply_block_shift: target id={entry_id} updated; shifted followers={len(applied)} (beta={beta_days})")
        except Exception:
            pass

    return applied
