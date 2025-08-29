# dao_acct_trans.py
from datetime import date, timedelta
from typing import List, Optional

from librepy.peewee.peewee import fn, JOIN
from librepy.model.base_dao import BaseDAO
from librepy.model.model import AcctTrans, Org, OrgAddress, CalendarEntryOrder


class AcctTransDAO(BaseDAO):
    """
    DAO for acct_trans that only operates on SALE orders.
    All queries are constrained to transtypecode='SALEORD'.
    """

    SALE_ORDER_CODE = "SALEORD"

    def __init__(self, logger):
        super().__init__(AcctTrans, logger)

    def _sale_q(self):
        """Base SELECT limited to SALEORD, selecting order and joined org."""
        m = self.model_class
        return (
            m.select(m, Org)
             .join(Org, join_type=JOIN.LEFT_OUTER, on=(m.org == Org.org_id))
             .where(m.transtypecode == self.SALE_ORDER_CODE)
        )


    def get_sale_order_by_id(self, transid: int):
        """Fetch a single SALE order by ID, or None if not found / not SALEORD."""
        m = self.model_class
        return self.safe_execute(
            f"fetching SALE order with ID {transid}",
            lambda: self._sale_q().where(m.transid == transid).get()
        )

    def get_sale_order_with_address_by_id(self, transid: int, preferred_addrtype: str = 'SHIPTO'):
        """Fetch a single SALE order by ID with Org and one preferred OrgAddress joined.
        Uses LEFT OUTER JOINs and limits OrgAddress by addrtype to avoid duplicates.
        Falls back to any address if a preferred one is not available.
        """
        m = self.model_class

        def _q_preferred():
            exists_subq = (CalendarEntryOrder
                           .select(1)
                           .where(CalendarEntryOrder.order == m.transid)
                           .limit(1))
            q = (
                m.select(m, Org, OrgAddress, fn.EXISTS(exists_subq).alias('has_calendar_entry'))
                 .join(Org, join_type=JOIN.LEFT_OUTER, on=(m.org == Org.org_id))
                 .switch(Org)
                 .join(
                     OrgAddress,
                     join_type=JOIN.LEFT_OUTER,
                     on=((OrgAddress.org == Org.org_id) & (OrgAddress.addrtype == preferred_addrtype))
            )
                 .where((m.transtypecode == self.SALE_ORDER_CODE) & (m.transid == transid))
            )
            # self.logger.debug(f'query dict {q.__dict__}')
            # self.logger.debug(f'query sql {q.sql()}')
            r = q.get()
            # self.logger.debug(f'query result {r.__dict__}')
            # self.logger.debug(f'customer {r.org.orgaddress.__dict__}')
            addr = getattr(r.org, 'orgaddress', None)
            # self.logger.debug(f'joined addr: {addr.__data__ if addr else None}')
            return r

        # Try preferred type first
        o = self.safe_execute(f"fetching SALE order with preferred address type '{preferred_addrtype}' ID {transid}", _q_preferred)

        # Determine if a joined OrgAddress actually exists on the row (LEFT JOIN may yield NULLs)
        addr_obj = None
        # self.logger.debug(f'query result safe execute {o.__dict__}')
        if o is not None:
            for attr in ('orgaddress', 'org_address', 'OrgAddress'):
                if hasattr(o, attr):
                    addr_obj = getattr(o, attr)
                    break
            try:
                if self.logger:
                    if addr_obj:
                        addr_id = getattr(addr_obj, 'addr_id', None)
                        addr_type = getattr(addr_obj, 'addrtype', None)
                        org_fk = getattr(addr_obj, 'org_id', None) or getattr(addr_obj, 'org', None)
                        self.logger.debug(f"AcctTransDAO: Preferred address join result for transid={transid} org={getattr(o, 'org_id', None) or getattr(getattr(o, 'org', None), 'org_id', None)}: addr_id={addr_id}, addrtype={addr_type}, preferred='{preferred_addrtype}'")
                    else:
                        self.logger.debug(f"AcctTransDAO: No preferred '{preferred_addrtype}' address joined for transid={transid}; will attempt fallback")
            except Exception:
                pass

        # If we got a row AND it has a joined address, return it; otherwise try fallback
        if o is not None and addr_obj is not None:
            return o

        # Fallback: any address, and collapse potential multiples using first()
        def _q_fallback():
            exists_subq = (CalendarEntryOrder
                           .select(1)
                           .where(CalendarEntryOrder.order == m.transid)
                           .limit(1))
            q = (
                m.select(m, Org, OrgAddress, fn.EXISTS(exists_subq).alias('has_calendar_entry'))
                 .join(Org, join_type=JOIN.LEFT_OUTER, on=(m.org == Org.org_id))
                 .switch(Org)
                 .join(
                     OrgAddress,
                     join_type=JOIN.LEFT_OUTER,
                     on=(OrgAddress.org == Org.org_id)
                 )
                 .where((m.transtypecode == self.SALE_ORDER_CODE) & (m.transid == transid))
            )
            return q.first()

        o_fb = self.safe_execute(f"fetching SALE order with any address ID {transid}", _q_fallback)
        try:
            if self.logger:
                if o_fb:
                    # Check if we have a joined address on fallback
                    fb_addr = None
                    for attr in ('orgaddress', 'org_address', 'OrgAddress'):
                        if hasattr(o_fb, attr):
                            fb_addr = getattr(o_fb, attr)
                            break
                    if fb_addr:
                        fb_id = getattr(fb_addr, 'addr_id', None)
                        fb_type = getattr(fb_addr, 'addrtype', None)
                        self.logger.debug(f"AcctTransDAO: Fallback address join used for transid={transid}: addr_id={fb_id}, addrtype={fb_type}")
                    else:
                        self.logger.debug(f"AcctTransDAO: Fallback returned a row but no joined address for transid={transid}")
                else:
                    self.logger.debug(f"AcctTransDAO: Fallback query returned no row for transid={transid}")
        except Exception:
            pass
        return o_fb

    def get_preferred_org_address(self, org_id: int, priorities=(
        'BILLTO', 'BILLING', 'MAILTO', 'MAILING', 'SHIPTO', 'SHIPPING'
    )):
        """Return the preferred OrgAddress for an org_id using a simple priority list.
        Normalizes addrtype values to uppercase/stripped before comparison.
        """
        def _q():
            return list(OrgAddress.select().where(OrgAddress.org == org_id))

        rows = self.safe_execute(f"fetching preferred org_address for org_id={org_id}", _q, default_return=[])
        def norm(s):
            return (s or '').strip().upper()
        chosen = None
        for p in priorities:
            chosen = next((a for a in rows if norm(getattr(a, 'addrtype', None)) == p), None)
            if chosen:
                break
        if not chosen and rows:
            chosen = rows[0]
        if self.logger:
            if chosen:
                self.logger.debug(
                    f"AcctTransDAO: get_preferred_org_address -> addr_id={getattr(chosen,'addr_id',None)}, type={getattr(chosen,'addrtype',None)} for org_id={org_id}"
                )
            else:
                self.logger.debug(f"AcctTransDAO: get_preferred_org_address -> no addresses for org_id={org_id}")
        return chosen


    def list_sale_orders(
            self,
            *,
            org_id: Optional[int] = None,
            from_date: Optional[date] = None,
            to_date: Optional[date] = None,
            newest_first: bool = True,
    ) -> list[dict]:
        """
        List SALE orders with optional org/date filters.
        Replicates the JobDAO.list_jobs pattern: returns a list of dicts
        ready for the UI grid (not Peewee model instances).
        """
        from datetime import date as _date
        m = self.model_class

        def _query():
            q = self._sale_q()

            exists_subq = (CalendarEntryOrder
                           .select(1)
                           .where(CalendarEntryOrder.order == m.transid)
                           .limit(1))
            q = q.select_extend(fn.EXISTS(exists_subq).alias('has_entries'))

            if org_id is not None:
                q = q.where(m.org == org_id)
            if from_date is not None:
                q = q.where(m.transdate >= from_date)
            if to_date is not None:
                q = q.where(m.transdate <= to_date)
            q = q.order_by(m.transdate.desc() if newest_first else m.transdate.asc())

            result = []
            for o in q:
                # UI-friendly date like jobs list (MM/DD/YY); change if you prefer ISO
                if isinstance(o.transdate, _date):
                    transdate_str = o.transdate.strftime('%m/%d/%y')
                else:
                    transdate_str = str(o.transdate) if o.transdate is not None else ''

                if o.expecteddate and isinstance(o.expecteddate, _date):
                    expecteddate_str = o.expecteddate.strftime('%m/%d/%y')
                else:
                    expecteddate_str = str(o.expecteddate) if o.expecteddate is not None else ''

                # o.org may be None due to LEFT OUTER JOIN
                org_obj = getattr(o, 'org', None)
                orgname = org_obj.orgname if org_obj else ''
                phone = org_obj.phone if org_obj else ''

                has_entries = bool(getattr(o, 'has_entries', False))

                result.append({
                    'transid': o.transid,  # used as heading
                    'transdate': transdate_str,  # ("Date", "transdate", ...)
                    'referencenumber': o.referencenumber or '',  # ("Customer Name", "referencenumber", ...)
                    'orgname': orgname,
                    'phone': phone,
                    'expecteddate': expecteddate_str,
                    'has_entries': 'YES' if has_entries else 'NO'
                })
            return result

        return self.safe_execute("listing SALE orders", _query, default_return=[])
