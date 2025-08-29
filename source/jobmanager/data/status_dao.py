from librepy.model.base_dao import BaseDAO
from librepy.model.model import CalendarEntryStatus


class StatusDAO(BaseDAO):
    """
    DAO for CalendarEntryStatus records.
    Provides simple APIs used by the Statuses dialog to list and replace statuses.
    """
    def __init__(self, logger):
        super().__init__(CalendarEntryStatus, logger)

    def get_all_statuses(self):
        """
        Return list of all statuses ordered by status name.
        Returns:
            list[CalendarEntryStatus]
        """
        return self.safe_execute(
            "fetching all calendar entry statuses",
            lambda: list(self.model_class.select().order_by(self.model_class.status)),
            default_return=[]
        )

    def replace_all(self, statuses):
        """
        Replace all statuses with the provided collection.
        Deletes all existing CalendarEntryStatus rows and inserts the new set.
        Args:
            statuses: Iterable of either (status, color) tuples or dicts with keys 'status' and 'color'.
        Returns:
            bool
        """
        if statuses is None:
            raise ValueError("statuses must not be None")

        # Normalize input to list of dicts with validated fields
        normalized = []
        for item in list(statuses):
            if isinstance(item, dict):
                name = item.get('status')
                color = item.get('color')
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                name, color = item[0], item[1]
            else:
                raise ValueError("Each status must be a dict with 'status' and 'color' or a (status, color) tuple")

            name = self.validate_string_field(name, "status", max_length=50, required=True)
            # Ensure status names are stored in uppercase
            name = name.upper()
            color = self.validate_string_field(color, "color", max_length=20, required=True)
            normalized.append({"status": name, "color": color})

        # Perform transactional replace (delete all then insert all)
        with self.database.connection_context():
            with self.database.atomic():
                self.safe_execute(
                    "deleting all existing calendar entry statuses",
                    lambda: self.model_class.delete().execute(),
                    default_return=0
                )
                if normalized:
                    self.safe_execute(
                        f"inserting {len(normalized)} calendar entry statuses",
                        lambda: self.model_class.insert_many(normalized).execute(),
                        reraise_integrity=True
                    )
        return True
