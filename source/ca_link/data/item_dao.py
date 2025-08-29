from librepy.peewee.peewee import fn
from librepy.ca_link.ca_model import ItmItems

class ItemDAO:
    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, msg):
        if self.logger:
            self.logger.info(msg)

    def search_items(self, term="", limit=200):
        db = ItmItems._meta.database
        with db.connection_context():
            term = term.strip()
            # Only select the fields we actually need
            q = ItmItems.select(
                ItmItems.itemnumber,
                ItmItems.itemname,
                ItmItems.salesdesc,
                ItmItems.price
            )
            if term:
                ilike = f"%{term.lower()}%"
                q = q.where(
                    (fn.LOWER(ItmItems.itemnumber).contains(term.lower())) |
                    (fn.LOWER(ItmItems.itemname).contains(term.lower())) |
                    (fn.LOWER(ItmItems.salesdesc).contains(term.lower()))
                )
            q = q.limit(limit)
            self._log(f"Executing item search term='{term}' limit={limit} db_id={id(db)}")
            items = []
            for itm in q:
                items.append({
                    "item_number": itm.itemnumber,
                    "item_name": itm.itemname,
                    "salesdesc": itm.salesdesc,
                    "price": itm.price
                })
            return items
