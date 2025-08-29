import uno
import traceback
from datetime import datetime
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, python_date_to_uno
from librepy.jobmanager.data.events_dao import EventsDAO

class EventDialog(DialogBase):
    POS_SIZE = 0, 0, 280, 280
    DISPOSE = True

    def __init__(self, parent, ctx, smgr, frame, ps, edit_mode=False, event_data=None, **props):
        self.edit_mode = edit_mode
        self.event_data = event_data or {}
        self.event_result = None
        self.listeners = listeners.Listeners()
        self.parent = parent
        self.logger = parent.logger
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.events_dao = EventsDAO(self.logger)
        super().__init__(ctx, smgr, **props)

    def _create(self):
        title = "Edit Event" if self.edit_mode else "Add Event"
        self._dialog.Title = title
        
        label_height = 15
        field_height = 20
        field_width = 160
        label_width = 55
        start_x = 10
        start_y = 20
        row_spacing = 30
        
        # Title field
        self.add_label("lbl_title", start_x, start_y, label_width, label_height, 
                      Label="Title:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.title_field = self.add_edit("EventTitle", start_x + label_width + 10, start_y, field_width, field_height)
        
        # Start date field
        self.add_label("lbl_start_date", start_x, start_y + row_spacing, label_width, label_height, 
                      Label="Start Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.start_date = self.add_date("StartDate", start_x + label_width + 10, start_y + row_spacing, field_width, field_height, Dropdown=True)
        
        # End date field
        self.add_label("lbl_end_date", start_x, start_y + row_spacing * 2, label_width, label_height, 
                      Label="End Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.end_date = self.add_date("EndDate", start_x + label_width + 10, start_y + row_spacing * 2, field_width, field_height, Dropdown=True)
        
        # Status field
        self.add_label("lbl_status", start_x, start_y + row_spacing * 3, label_width, label_height, 
                      Label="Status:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.status_combo = self.add_combo("EventStatus", start_x + label_width + 10, start_y + row_spacing * 3, field_width, field_height, Dropdown=True)
        
        # Populate status dropdown
        statuses = self.events_dao.get_available_statuses()
        self.status_combo.Model.StringItemList = tuple(statuses)
        

        # Description field (multiline text area)
        self.add_label("lbl_description", start_x, start_y + row_spacing * 4, label_width, label_height, 
                      Label="Description:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.description_field = self.add_edit("EventDescription", start_x + label_width + 10, start_y + row_spacing * 4, field_width, 60, 
                                              MultiLine=True, VScroll=True)
        
        # Buttons
        button_y = start_y + row_spacing * 5 + 40
        button_width = 80
        button_height = 25
        button_spacing = 10
        total_width = button_width * 2 + button_spacing
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height, 
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        self.save_btn = self.add_button("SaveButton", center_x + button_width + button_spacing, button_y, button_width, button_height, 
                                       Label="Save", callback=self.save_event, BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

    def _prepare(self):
        self.status_combo.Text = 'Pending'
        if self.edit_mode and self.event_data:
            # Handle both model objects and dictionary data
            if hasattr(self.event_data, 'title'):
                # It's a model object
                self.title_field.Text = self.event_data.title or ''
                start_date = self.event_data.start_date
                end_date = self.event_data.end_date
                description = self.event_data.description or ''
                status = getattr(self.event_data, 'status', 'Pending')
            else:
                # It's a dictionary
                self.title_field.Text = self.event_data.get('title', '')
                start_date = self.event_data.get('start_date')
                end_date = self.event_data.get('end_date')
                description = self.event_data.get('description', '')
                status = self.event_data.get('status', 'Pending')
            
            # Handle start date
            if start_date:
                try:
                    if isinstance(start_date, str):
                        d = datetime.strptime(start_date, '%Y-%m-%d').date()
                    else:
                        d = start_date  # Assume it's already a date object
                    self.start_date.setDate(python_date_to_uno(d))
                except Exception as e:
                    self.logger.error(f"Error setting start date: {e}")
            
            # Handle end date
            if end_date:
                try:
                    if isinstance(end_date, str):
                        d = datetime.strptime(end_date, '%Y-%m-%d').date()
                    else:
                        d = end_date  # Assume it's already a date object
                    self.end_date.setDate(python_date_to_uno(d))
                except Exception as e:
                    self.logger.error(f"Error setting end date: {e}")
            
            # Handle description
            self.description_field.Text = description
            
            # Handle status
            if status in self.events_dao.get_available_statuses():
                self.status_combo.setText(status)
            else:
                self.status_combo.setText('Pending')

    def save_event(self, event):
        # Validate required fields
        if not self.title_field.Text.strip():
            msgbox("Title is required.", "Validation Error")
            return
        
        try:
            # Get date values
            sd_uno = self.start_date.getDate()
            ed_uno = self.end_date.getDate()
            sd_py = uno_date_to_python(sd_uno) if sd_uno.Year > 0 else None
            ed_py = uno_date_to_python(ed_uno) if ed_uno.Year > 0 else None
            
            # Validate that end date is not before start date
            if sd_py and ed_py and ed_py < sd_py:
                msgbox("End date cannot be before start date.", "Validation Error")
                return
            
            title = self.title_field.Text.strip()
            description = self.description_field.Text.strip() if self.description_field.Text.strip() else None
            status = self.status_combo.getText() if self.status_combo.getText() else 'Pending'
            
            if self.edit_mode and self.event_data:
                # Update existing event
                if hasattr(self.event_data, 'id'):
                    event_id = self.event_data.id  # Model object
                else:
                    event_id = self.event_data.get('id')  # Dictionary
                self.events_dao.update_event(
                    event_id=event_id,
                    title=title,
                    start_date=sd_py,
                    end_date=ed_py,
                    description=description,
                    status=status
                )
                self.event_result = self.events_dao.get_event_by_id(event_id)
            else:
                # Create new event
                self.event_result = self.events_dao.add_event(
                    title=title,
                    start_date=sd_py,
                    end_date=ed_py,
                    description=description,
                    status=status
                )
            
            self.end_execute(1)  # Close dialog with OK result
            
        except Exception as e:
            self.logger.error(f"Error saving event: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error saving event: {e}", "Error")

    def get_event_data(self):
        """Returns the event data after successful save"""
        return self.event_result

    def dispose(self):
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())
