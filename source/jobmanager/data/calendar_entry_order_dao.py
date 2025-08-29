from librepy.model.base_dao import BaseDAO
from librepy.model.model import CalendarEntryOrder, AcctTrans, Org, CalendarEntryStatus
from librepy.peewee.peewee import JOIN, fn, SQL


class CalendarEntryOrderDAO(BaseDAO):
    """
    DAO for CalendarEntryOrder entries joined with AcctTrans (SALE orders) and Org.
    Provides range-based retrieval suitable for calendar rendering.
    """

    def __init__(self, logger):
        super().__init__(CalendarEntryOrder, logger)

    def _q(self):
        m = self.model_class
        # LEFT OUTER join so entries without an order are also returned; also join status
        return (
            m.select(m, AcctTrans, Org, CalendarEntryStatus)
             .join(AcctTrans, join_type=JOIN.LEFT_OUTER, on=(m.order == AcctTrans.transid))
             .join(Org, join_type=JOIN.LEFT_OUTER, on=(AcctTrans.org == Org.org_id))
             .switch(m)
             .join(CalendarEntryStatus, join_type=JOIN.LEFT_OUTER, on=(m.status == CalendarEntryStatus.status_id))
        )

    def get_entries_by_date_range(self, start_date, end_date):
        """
        List CalendarEntryOrder rows that overlap the [start_date, end_date] range.
        Returns UI-friendly dicts that the calendar can expand per-day.
        """
        def _query():
            q = self._q()
            # Keep entries with no order OR with order type 'SALEORD'
            type_pred = (CalendarEntryOrder.order.is_null(True)) | (AcctTrans.transtypecode == 'SALEORD')
            # Broad DB-side predicate on start_date to reduce rows; detailed overlap check in Python
            q = q.where(type_pred & (CalendarEntryOrder.start_date <= end_date))

            items = []
            for e in q:
                s = e.start_date
                eend = e.end_date or e.start_date
                if s is None:
                    continue
                # Overlap check: [s, eend] intersects [start_date, end_date]
                if not (s <= end_date and eend >= start_date):
                    continue

                # IMPORTANT: guard against NULL FK; do not dereference e.order when order_id is None
                order_id = getattr(e, 'order_id', None)
                orgname = ''
                refer = ''
                if order_id is not None:
                    order_obj = getattr(e, 'order', None)
                    if order_obj is not None:
                        refer = getattr(order_obj, 'referencenumber', '') or ''
                        org_obj = getattr(order_obj, 'org', None)
                        orgname = getattr(org_obj, 'orgname', '') if org_obj else ''

                # Status details
                status_id = getattr(e, 'status_id', None)
                status_name = ''
                status_color = ''
                status_obj = getattr(e, 'status', None)
                if status_obj is not None:
                    status_name = getattr(status_obj, 'status', '') or ''
                    status_color = getattr(status_obj, 'color', '') or ''

                items.append({
                    'id': e.entry_id,
                    'title': e.event_name or '',
                    'start_date': s,
                    'end_date': eend,
                    'description': e.event_description or '',
                    'order_id': order_id,
                    'orgname': orgname,
                    'referencenumber': refer,
                    'type': 'order_entry',
                    'reminder': bool(getattr(e, 'reminder', False)),
                    'days_before': getattr(e, 'days_before', None),
                    'lock_dates': bool(getattr(e, 'lock_dates', False)),
                    'fixed_dates': bool(getattr(e, 'fixed_dates', False)),
                    'status_id': status_id,
                    'status': status_name,
                    'status_color': status_color,
                })
            return items

        return self.safe_execute(
            f"listing CalendarEntryOrder in range {start_date}..{end_date}",
            _query,
            default_return=[]
        )

    def _to_dict(self, e):
        """Convert a CalendarEntryOrder row (with optional joined order/org) to UI dict."""
        # Guarded access to related order/org
        order_id = getattr(e, 'order_id', None)
        orgname = ''
        refer = ''
        if order_id is not None:
            order_obj = getattr(e, 'order', None)
            if order_obj is not None:
                refer = getattr(order_obj, 'referencenumber', '') or ''
                org_obj = getattr(order_obj, 'org', None)
                orgname = getattr(org_obj, 'orgname', '') if org_obj else ''
        s = e.start_date
        eend = e.end_date or e.start_date
        return {
            'id': e.entry_id,
            'title': e.event_name or '',
            'start_date': s,
            'end_date': eend,
            'description': e.event_description or '',
            'order_id': order_id,
            'orgname': orgname,
            'referencenumber': refer,
            'type': 'order_entry',
            'reminder': bool(getattr(e, 'reminder', False)),
            'days_before': getattr(e, 'days_before', None),
            'lock_dates': bool(getattr(e, 'lock_dates', False)),
            'fixed_dates': bool(getattr(e, 'fixed_dates', False)),
            'status_id': getattr(e, 'status_id', None),
            'status': (getattr(getattr(e, 'status', None), 'status', '') or '') if getattr(e, 'status', None) else '',
            'status_color': (getattr(getattr(e, 'status', None), 'color', '') or '') if getattr(e, 'status', None) else '',
        }

    def get_entry_by_id(self, entry_id):
        def _query():
            # Use left joins to fetch optional order/org labels
            q = self._q().where(CalendarEntryOrder.entry_id == entry_id)
            e = q.first()
            if not e:
                return None
            return self._to_dict(e)
        return self.safe_execute(f"get CalendarEntryOrder by id {entry_id}", _query, default_return=None)

    def create_entry(self, data):
        """Create a new CalendarEntryOrder. Returns new entry_id or None on failure."""
        def _create():
            s = data.get('start_date')
            if not s:
                raise ValueError('start_date is required')
            eend = data.get('end_date') or s
            name = (data.get('event_name') or data.get('title') or '').strip()
            desc = (data.get('event_description') or data.get('description') or '').strip()
            order_id = data.get('order_id')
            # Build create kwargs; allow order to be None for this page
            kwargs = {
                'start_date': s,
                'end_date': eend,
                'event_name': name,
                'event_description': desc or None,
                'reminder': bool(data.get('reminder', False)),
                'days_before': data.get('days_before'),
                'lock_dates': bool(data.get('lock_dates', False)),
                'fixed_dates': bool(data.get('fixed_dates', False)),
            }
            if order_id:
                kwargs['order'] = order_id
            status_id = data.get('status_id')
            if status_id is not None:
                kwargs['status'] = status_id
                self.logger.debug(f"CalendarEntryOrderDAO.create_entry incoming data={data}")
                self.logger.debug(f"CalendarEntryOrderDAO.create_entry kwargs={kwargs} (status_id={status_id})")
            obj = CalendarEntryOrder.create(**kwargs)
            self.logger.debug(f"CalendarEntryOrderDAO.create_entry created entry_id={obj.entry_id}, stored status_id={getattr(obj, 'status_id', None)}")
            return obj.entry_id
        return self.safe_execute("create CalendarEntryOrder", _create, default_return=None)

    def update_entry(self, entry_id, data):
        def _update():
            obj = CalendarEntryOrder.get_or_none(CalendarEntryOrder.entry_id == entry_id)
            if not obj:
                return False
            s = data.get('start_date') or obj.start_date
            eend = data.get('end_date') or s
            if eend and s and eend < s:
                # Normalize to at least s
                eend = s
            obj.start_date = s
            obj.end_date = eend
            name = (data.get('event_name') or data.get('title'))
            if name is not None:
                obj.event_name = name
            desc = data.get('event_description') if 'event_description' in data else data.get('description')
            if desc is not None:
                obj.event_description = desc or None
            if 'order_id' in data:
                obj.order = data.get('order_id')
            if 'reminder' in data:
                obj.reminder = bool(data.get('reminder'))
            if 'days_before' in data:
                obj.days_before = data.get('days_before')
            if 'lock_dates' in data:
                obj.lock_dates = bool(data.get('lock_dates'))
            if 'fixed_dates' in data:
                obj.fixed_dates = bool(data.get('fixed_dates'))
            if 'status_id' in data:
                obj.status = data.get('status_id')
            self.logger.debug(f"CalendarEntryOrderDAO.update_entry {entry_id} incoming data={data}, pre-save status_id={getattr(obj, 'status_id', None)}")
            obj.save()
            self.logger.debug(f"CalendarEntryOrderDAO.update_entry {entry_id} post-save status_id={getattr(obj, 'status_id', None)}")
            return True
        return self.safe_execute(f"update CalendarEntryOrder {entry_id}", _update, default_return=False)

    def get_due_reminders(self, today=None):
        """
        Return entries whose reminder is due today: start_date - today == days_before.
        Optional `today` allows deterministic testing; when None, the DB current date is used.
        """
        def _query():
            q = self._q()

            # Mirror business rule from range method: include entries with no order OR SALEORD
            type_pred = (CalendarEntryOrder.order.is_null(True)) | (AcctTrans.transtypecode == 'SALEORD')

            # Use DB current date when `today` not provided
            today_expr = today if today is not None else SQL('CURRENT_DATE')

            # Core predicates
            preds = [
                (CalendarEntryOrder.reminder == True),
                CalendarEntryOrder.start_date.is_null(False),
                CalendarEntryOrder.days_before.is_null(False),
                ((CalendarEntryOrder.start_date - today_expr) == CalendarEntryOrder.days_before),
            ]

            q = q.where(type_pred & preds[0] & preds[1] & preds[2] & preds[3])

            # Map rows to dicts using existing helper
            return [self._to_dict(e) for e in q]

        return self.safe_execute("list due reminder CalendarEntryOrder entries", _query, default_return=[])

    def delete_entry(self, entry_id):
        def _delete():
            obj = CalendarEntryOrder.get_or_none(CalendarEntryOrder.entry_id == entry_id)
            if not obj:
                return False
            obj.delete_instance()
            return True
        return self.safe_execute(f"delete CalendarEntryOrder {entry_id}", _delete, default_return=False)
