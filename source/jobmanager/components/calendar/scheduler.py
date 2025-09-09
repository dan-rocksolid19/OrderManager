from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple, Any

# Minimal logger protocol
class _Logger:
    def debug(self, msg: str): ...
    def info(self, msg: str): ...
    def warning(self, msg: str): ...
    def error(self, msg: str): ...


@dataclass(frozen=True)
class Event:
    id: Any
    start: date
    end: date
    duration: int
    locked: bool = False
    fixed: bool = False

    @staticmethod
    def from_dict(d: dict, id_key: str = 'id', start_key: str = 'start_date', end_key: str = 'end_date', lock_key: str = 'lock_dates') -> 'Event':
        s: date = d[start_key]
        e: date = d.get(end_key) or s
        return Event(
            id=d.get(id_key),
            start=s,
            end=e,
            duration=(e - s).days + 1,
            locked=bool(d.get(lock_key, False)),
            fixed=bool(d.get('fixed_dates', False)),
        )


@dataclass
class Move:
    id: Any
    old_start: date
    old_end: date
    new_start: date
    new_end: date


@dataclass
class Config:
    policy: str = "forward"  # "forward" | "balanced"
    max_cascade: Optional[int] = None
    immovable_flag: str = "lock_dates"
    dry_run: bool = False
    # Lock cascade to a single direction if desired
    sticky_direction: bool = False
    cascade_direction: Optional[str] = None


def _overlaps(a: Tuple[date, date], b: Tuple[date, date]) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1])


def _choose_direction(policy: str, anchor: Tuple[date, date], e: Tuple[date, date], dur: int) -> str:
    aS, aE = anchor
    eS, eE = e

    # Determine base direction from inclusive overlap geometry
    # - Tail overlaps head (anchor.end >= e.start and anchor.start <= e.start) => move E forward
    # - Head overlaps tail (anchor.start <= e.end and anchor.end >= e.end)     => move E backward
    # - Full containment/coverage or ambiguous cases                            => default forward
    base_dir = 'forward'
    if (aS <= eE and aE >= eE):
        # Head overlaps tail => move neighbor backward
        base_dir = 'backward'
    if (aE >= eS and aS <= eS):
        # Tail overlaps head => move neighbor forward (this can override previous if both true; forward default)
        base_dir = 'forward'

    if policy == 'forward':
        return base_dir

    # balanced: compute costs and choose minimal shift; tie -> prefer forward
    f_start = aE + timedelta(days=1)
    cost_f = abs((f_start - eS).days)
    b_end = aS - timedelta(days=1)
    b_start = b_end - timedelta(days=dur - 1)
    cost_b = abs((eS - b_start).days)
    if cost_b < cost_f:
        return 'backward'
    return 'forward'


def plan_moves(existing_events: List[dict], new_event: dict, logger: Optional[_Logger] = None, cfg: Optional[Config] = None) -> Tuple[bool, List[Move], Optional[str]]:
    """
    Compute the list of moves needed to insert new_event without overlaps by moving existing events.
    - existing_events: list of dicts with keys id, start_date, end_date (optional), lock_dates.
    - new_event: dict with start_date, end_date (optional).
    Returns (ok, moves, error_message).
    """
    cfg = cfg or Config()

    # Normalize NEW
    ns: date = new_event['start_date']
    ne: date = new_event.get('end_date') or ns
    if ne < ns:
        ns, ne = ne, ns
    new_anchor = (ns, ne)
    if logger:
        try:
            logger.debug(f"plan_moves: anchor NEW={new_anchor}, policy={cfg.policy}, max_cascade={cfg.max_cascade}")
        except Exception:
            pass

    # Sticky cascade direction setup
    cascade_dir: Optional[str] = getattr(cfg, 'cascade_direction', None)
    sticky: bool = bool(getattr(cfg, 'sticky_direction', False))

    # Build Event list from existing
    events: List[Event] = []
    for d in existing_events:
        if not d.get('start_date'):
            continue
        e = Event.from_dict(d)
        events.append(e)
    # Deterministic iteration for first-move locking
    try:
        events.sort(key=lambda ev: (ev.start, ev.end, str(ev.id)))
    except Exception:
        pass
    if logger:
        try:
            logger.debug(f"plan_moves: {len(events)} existing events considered")
        except Exception:
            pass

    # Proposed map id -> (start, end)
    proposed: Dict[Any, Tuple[date, date]] = {e.id: (e.start, e.end) for e in events}

    moves: List[Move] = []
    steps = 0

    # Note: sticky-direction prevents geometric circular rescheduling; keeping only max_cascade as a global guard.

    # BFS queue of anchors; treat NEW as synthetic anchor first
    queue: List[Tuple[Any, Tuple[date, date]]] = [("NEW", new_anchor)]
    visited: set = {("NEW", new_anchor[0], new_anchor[1])}
    # Track ids currently queued to avoid duplicate anchors for the same id
    in_queue_ids: set = {"NEW"}

    def enqueue(eid: Any, interval: Tuple[date, date]):
        # Do not enqueue duplicate ids; when it pops, we will refresh to latest proposed interval
        if eid in in_queue_ids:
            if logger:
                try:
                    logger.debug(f"plan_moves: skip enqueue for id={eid} (already in queue); latest interval will be used on pop")
                except Exception:
                    pass
            return
        t = (eid, interval[0], interval[1])
        if t not in visited:
            queue.append((eid, interval))
            visited.add(t)
            in_queue_ids.add(eid)
            if logger:
                try:
                    logger.debug(f"plan_moves: enqueue anchor id={eid} interval={interval}")
                except Exception:
                    pass

    while queue:
        anchor_id, a_int = queue.pop(0)
        # Mark id as no longer in queue so it can be enqueued again after it moves
        if anchor_id in in_queue_ids:
            try:
                in_queue_ids.remove(anchor_id)
            except Exception:
                pass
        # Refresh anchor interval to the latest proposed state for this id (if any)
        if anchor_id != "NEW" and anchor_id in proposed:
            a_int = proposed.get(anchor_id, a_int)
        aS, aE = a_int
        if logger:
            try:
                logger.debug(f"plan_moves: pop anchor id={anchor_id} interval={a_int}; queue_len={len(queue)}")
            except Exception:
                pass
        # Find overlaps among existing events
        for e in events:
            if e.id == anchor_id:
                continue
            cur = proposed[e.id]
            if not _overlaps(a_int, cur):
                continue
            # If event has fixed or locked dates, allow overlap and do not reschedule or cascade
            if getattr(e, 'fixed', False) or getattr(e, 'locked', False):
                if logger:
                    try:
                        flag = 'fixed_dates' if getattr(e, 'fixed', False) else 'lock_dates'
                        logger.debug(f"plan_moves: overlap with id={e.id} but {flag}=True; allowing overlap and skipping move")
                    except Exception:
                        pass
                continue
            # Direction with sticky enforcement
            if sticky and cascade_dir:
                dirn = cascade_dir
            else:
                dirn = _choose_direction(cfg.policy, a_int, cur, e.duration)
                if sticky and cascade_dir is None:
                    cascade_dir = dirn
                    if logger:
                        try:
                            logger.debug(f"plan_moves: sticky cascade_dir locked to '{cascade_dir}' on first move (anchor={anchor_id})")
                        except Exception:
                            pass
            if dirn == 'forward':
                new_start = aE + timedelta(days=1)
                new_end = new_start + timedelta(days=e.duration - 1)
            else:
                # Backward snap (inclusive): place neighbor flush before anchor
                new_end = aS - timedelta(days=1)
                new_start = new_end - timedelta(days=e.duration - 1)

            if logger:
                try:
                    logger.debug(f"plan_moves: overlap with id={e.id} cur={cur} dir={dirn} -> target=({new_start},{new_end}) dur={e.duration}")
                except Exception:
                    pass

            if (new_start, new_end) == cur:
                continue

            steps += 1
            if cfg.max_cascade is not None and steps > cfg.max_cascade:
                msg = f"Cascade exceeded limit {cfg.max_cascade}"
                if logger:
                    logger.error(msg)
                return False, moves, msg

            moves.append(Move(e.id, cur[0], cur[1], new_start, new_end))
            proposed[e.id] = (new_start, new_end)
            enqueue(e.id, (new_start, new_end))

    if logger:
        try:
            logger.info(f"plan_moves: completed with {len(moves)} moves")
        except Exception:
            pass
    return True, moves, None


def insert_with_reschedule(dao, new_event: dict, logger: Optional[_Logger] = None, cfg: Optional[Config] = None) -> Tuple[bool, Optional[int], List[Move], Optional[str]]:
    """
    High-level helper that uses the DAO to plan and apply moves, then create the new entry.
    - dao must implement get_entries_by_date_range(start, end), update_entry(id, data), create_entry(data)
    Returns (ok, new_entry_id, applied_moves, error)
    """
    cfg = cfg or Config()

    ns: date = new_event['start_date']
    ne: date = new_event.get('end_date') or ns
    if ne < ns:
        ns, ne = ne, ns

    # Use a generous range to capture potential cascades (10 years buffer each side)
    rng_start = ns - timedelta(days=3650)
    rng_end = ne + timedelta(days=3650)

    if logger:
        try:
            logger.info(f"insert_with_reschedule: planning insert for {ns}..{ne} (range {rng_start}..{rng_end})")
        except Exception:
            pass

    existing = dao.get_entries_by_date_range(rng_start, rng_end) or []
    if logger:
        try:
            logger.debug(f"insert_with_reschedule: fetched {len(existing)} potentially overlapping events")
        except Exception:
            pass

    ok, moves, err = plan_moves(existing, new_event, logger=logger, cfg=cfg)
    if not ok:
        return False, None, moves, err

    if logger:
        try:
            logger.info(f"insert_with_reschedule: applying {len(moves)} neighbor moves and creating new entry")
        except Exception:
            pass

    # Create new entry first or after applying moves? To avoid complicating overlaps, create after planning.
    new_id = dao.create_entry(new_event)
    if not new_id:
        return False, None, [], "Failed to create new entry"

    # Apply moves to existing entries
    applied: List[Move] = []
    for m in moves:
        updated = dao.update_entry(m.id, {'start_date': m.new_start, 'end_date': m.new_end})
        if updated:
            applied.append(m)
            if logger:
                try:
                    logger.debug(f"insert_with_reschedule: moved id={m.id} {m.old_start}..{m.old_end} -> {m.new_start}..{m.new_end}")
                except Exception:
                    pass
        else:
            # If an update fails, log and continue (minimal impact); in a robust impl. we could rollback
            if logger:
                logger.error(f"Failed to update entry {m.id} to {m.new_start}..{m.new_end}")

    if logger:
        try:
            logger.info(f"insert_with_reschedule: done; new_id={new_id}, applied_moves={len(applied)}")
        except Exception:
            pass
    return True, new_id, applied, None


def update_with_reschedule(dao, entry_id: int, updated_data: dict,
                           logger: Optional[_Logger] = None,
                           cfg: Optional[Config] = None) -> Tuple[bool, List[Move], Optional[str]]:
    """
    Reschedule neighbors when updating an existing entry's dates.
    Returns (ok, applied_moves, error)
    """
    cfg = cfg or Config()

    # Fetch current entry
    current = dao.get_entry_by_id(entry_id)
    if not current:
        return False, [], f"Entry {entry_id} not found"

    # Determine new interval (normalize inclusive interval)
    ns: date = updated_data.get('start_date') or current.get('start_date')
    ne: date = updated_data.get('end_date') or ns
    if ne < ns:
        ns, ne = ne, ns

    # If the target has fixed_dates=True or lock_dates=True, do not reschedule neighbors; allow overlap
    target_fixed = bool(updated_data.get('fixed_dates', current.get('fixed_dates', False)))
    target_locked = bool(updated_data.get('lock_dates', current.get('lock_dates', False)))
    if target_fixed or target_locked:
        payload = dict(updated_data)
        payload['start_date'] = ns
        payload['end_date'] = ne
        ok = dao.update_entry(entry_id, payload)
        if not ok:
            return False, [], f"Failed to update target entry {entry_id} ({'locked' if target_locked else 'fixed'})"
        if logger:
            try:
                logger.info(f"update_with_reschedule: target id={entry_id} has {'lock_dates' if target_locked else 'fixed_dates'}=True; updated without rescheduling")
            except Exception:
                pass
        return True, [], None

    if logger:
        try:
            logger.info(f"update_with_reschedule: target id={entry_id} new={ns}..{ne}")
        except Exception:
            pass

    # Big range to capture cascades
    rng_start = ns - timedelta(days=3650)
    rng_end = ne + timedelta(days=3650)

    # Get neighbors excluding the target itself
    existing = dao.get_entries_by_date_range(rng_start, rng_end) or []
    existing = [e for e in existing if e.get('id') != entry_id]
    if logger:
        try:
            logger.debug(f"update_with_reschedule: neighbors fetched={len(existing)}")
        except Exception:
            pass

    # Plan moves with the target's new interval as the anchor (same logic as insertion)
    ok, moves, err = plan_moves(existing, {'start_date': ns, 'end_date': ne}, logger=logger, cfg=cfg)
    if not ok:
        return False, moves, err

    if logger:
        try:
            logger.info(f"update_with_reschedule: applying {len(moves)} neighbor moves")
        except Exception:
            pass

    # Apply neighbor moves first
    applied: List[Move] = []
    for m in moves:
        if dao.update_entry(m.id, {'start_date': m.new_start, 'end_date': m.new_end}):
            applied.append(m)
            if logger:
                try:
                    logger.debug(f"update_with_reschedule: moved id={m.id} {m.old_start}..{m.old_end} -> {m.new_start}..{m.new_end}")
                except Exception:
                    pass
        else:
            if logger:
                logger.error(f"Failed to update entry {m.id} to {m.new_start}..{m.new_end}")

    # Update the target entry with caller's fields
    payload = dict(updated_data)
    payload['start_date'] = ns
    payload['end_date'] = ne
    if not dao.update_entry(entry_id, payload):
        return False, applied, f"Failed to update target entry {entry_id}"

    if logger:
        try:
            logger.info(f"update_with_reschedule: done; target id={entry_id} updated, applied_moves={len(applied)}")
        except Exception:
            pass
    return True, applied, None
