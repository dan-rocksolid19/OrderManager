from datetime import datetime, timezone
from librepy.model.base_dao import BaseDAO
from librepy.model.model import Events


class EventsDAO(BaseDAO):
    
    # Event status color coding configuration
    EVENT_STATUS_COLORS = {
        'Urgent': 0xC0392B,      # Strong Red
        'Approved': 0x27AE60,    # Dark Green
        'Meeting': 0x2980B9,     # Steel Blue
        'Pending': 0xF39C12,     # Orange
        'Canceled': 0x7F8C8D,    # Medium Gray
        'Unassigned': 0xBDC3C7,  # Light Gray for unassigned
    }
    
    # Available event statuses
    AVAILABLE_STATUSES = list(EVENT_STATUS_COLORS.keys())
    
    def __init__(self, logger):
        super().__init__(Events, logger)
    
    def add_event(self, title, start_date=None, end_date=None, description=None, status='Pending'):
        """
        Create a single event record.
        
        Args:
            title (str): The event title (required)
            start_date (date): The event start date (optional)
            end_date (date): The event end date (optional)
            description (str): The event description (optional)
            status (str): The event status (optional, defaults to 'Pending')
            
        Returns:
            Events: The created event instance
        """
        title = self.validate_string_field(title, "title", max_length=255, required=True)
        if description is not None:
            description = self.validate_string_field(description, "description", required=False)
        if status not in self.AVAILABLE_STATUSES:
            status = 'Pending'  # Default to Pending if invalid status
        
        now = datetime.now(timezone.utc)
        
        return self.safe_execute(
            "creating event",
            lambda: self.model_class.create(
                title=title,
                start_date=start_date,
                end_date=end_date,
                description=description,
                status=status,
                created_at=now,
                updated_at=now
            ),
            reraise_integrity=True
        )
    
    def update_event(self, event_id, title=None, start_date=None, end_date=None, description=None, status=None):
        """
        Update an existing event.
        
        Args:
            event_id (int): The event ID to update
            title (str): The event title (optional)
            start_date (date): The event start date (optional)
            end_date (date): The event end date (optional)
            description (str): The event description (optional)
            status (str): The event status (optional)
            
        Returns:
            bool: True if successful
        """
        event_id = self.validate_numeric_field(event_id, "event_id", min_value=1, required=True)
        
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        
        if title is not None:
            update_fields["title"] = self.validate_string_field(title, "title", max_length=255, required=True)
        if start_date is not None:
            update_fields["start_date"] = start_date
        if end_date is not None:
            update_fields["end_date"] = end_date
        if description is not None:
            update_fields["description"] = self.validate_string_field(description, "description", required=False)
        if status is not None and status in self.AVAILABLE_STATUSES:
            update_fields["status"] = status
        
        rows = self.safe_execute(
            f"updating {self.model_class.__name__} ID {event_id}",
            lambda: self.model_class.update(**update_fields).where(self.model_class.id == event_id).execute(),
            default_return=0,
            reraise_integrity=True
        )
        if rows == 0:
            raise Exception(f"Failed to update {self.model_class.__name__} ID {event_id}")
        return True
    
    def remove_event(self, event_id):
        """
        Delete event by ID.
        
        Args:
            event_id (int): The event ID to delete
            
        Returns:
            bool: True if successful
        """
        event_id = self.validate_numeric_field(event_id, "event_id", min_value=1, required=True)
        
        rows = self.safe_execute(
            f"deleting {self.model_class.__name__} ID {event_id}",
            lambda: self.model_class.delete().where(self.model_class.id == event_id).execute(),
            default_return=0,
            reraise_integrity=False
        )
        if rows == 0:
            raise Exception(f"Failed to delete {self.model_class.__name__} ID {event_id}")
        return True
    
    def get_event_by_id(self, event_id):
        """
        Get an event by ID.
        
        Args:
            event_id (int): The event ID to fetch
            
        Returns:
            Events: The event instance or None if not found
        """
        event_id = self.validate_numeric_field(event_id, "event_id", min_value=1, required=True)
        
        return self.safe_execute(
            f"fetching {self.model_class.__name__} ID {event_id}",
            lambda: self.model_class.get_by_id(event_id),
            default_return=None
        )
    
    def get_all_events(self):
        """
        Return list of all events ordered by start_date (nulls last), then by title.
        
        Returns:
            list[Events]: List of event instances
        """
        return self.safe_execute(
            "fetching all events",
            lambda: list(self.model_class.select().order_by(
                self.model_class.start_date.asc(nulls='LAST'),
                self.model_class.title
            )),
            default_return=[]
        )
    
    def get_events_by_date_range(self, start_date=None, end_date=None):
        """
        Get events within a date range.
        
        Args:
            start_date (date): Start of date range (optional)
            end_date (date): End of date range (optional)
            
        Returns:
            list[Events]: List of event instances within the date range
        """
        query = self.model_class.select()
        
        if start_date is not None:
            query = query.where(
                (self.model_class.end_date >= start_date) | 
                (self.model_class.end_date.is_null())
            )
        
        if end_date is not None:
            query = query.where(
                (self.model_class.start_date <= end_date) | 
                (self.model_class.start_date.is_null())
            )
        
        return self.safe_execute(
            f"fetching events by date range ({start_date} to {end_date})",
            lambda: list(query.order_by(
                self.model_class.start_date.asc(nulls='LAST'),
                self.model_class.title
            )),
            default_return=[]
        )
    
    def get_events_for_date(self, target_date):
        """
        Get events that occur on a specific date.
        
        Args:
            target_date (date): The target date to check
            
        Returns:
            list[Events]: List of event instances occurring on the target date
        """
        return self.safe_execute(
            f"fetching events for date {target_date}",
            lambda: list(self.model_class.select().where(
                (self.model_class.start_date <= target_date) &
                ((self.model_class.end_date >= target_date) | 
                 (self.model_class.end_date.is_null()))
            ).order_by(self.model_class.title)),
            default_return=[]
        )
    
    def get_event_status_color(self, status):
        """
        Get the color for a specific event status.
        
        Args:
            status (str): The event status
            
        Returns:
            int: Color code for the status (hex format)
        """
        return self.EVENT_STATUS_COLORS.get(status, self.EVENT_STATUS_COLORS['Pending'])
    
    def get_available_statuses(self):
        """
        Get list of available event statuses.
        
        Returns:
            list[str]: List of available status options
        """
        return self.AVAILABLE_STATUSES.copy()