from librepy.model.base_dao import BaseDAO
from librepy.model.model import CalendarEntryStatus


class CalendarEntryStatusDAO(BaseDAO):
    """
    DAO for CalendarEntryStatus to retrieve available status options
    with proper database connection management via BaseDAO.
    """

    def __init__(self, logger):
        super().__init__(CalendarEntryStatus, logger)

    def list_statuses(self):
        """Return all statuses ordered by name."""
        return self.get_all(
            order_by=CalendarEntryStatus.status,
            operation_name="listing CalendarEntryStatus"
        )
