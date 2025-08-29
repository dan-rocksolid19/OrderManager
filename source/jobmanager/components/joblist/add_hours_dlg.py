import uno
import traceback
from datetime import datetime
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox

class AddHoursDialog(DialogBase):
    
    POS_SIZE = 0, 0, 220, 270
    DISPOSE = True
    
    def __init__(self, parent, ctx, smgr, frame, ps, edit_mode=False, hours_data=None, **props):
        self.edit_mode = edit_mode
        self.hours_data = hours_data or {}
        self.hours_result = None
        self.listeners = listeners.Listeners()
        super().__init__(ctx, smgr, **props)
        self.parent = parent
        self.logger = parent.logger
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger.info("AddHoursDialog initialized")
        
    def _create(self):
        title = "Edit Hours" if self.edit_mode else "Add Hours"
        self._dialog.Title = title

        label_height = 15
        field_height = 20
        field_width = 120
        label_width = 50
        start_x = 20
        start_y = 20
        row_spacing = 35

        self.add_label("lbl_employee", start_x, start_y, label_width, label_height,
                      Label="Employee:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.employee = self.add_edit("Employee", start_x + label_width + 10, start_y, field_width, field_height)

        self.add_label("lbl_start_date", start_x, start_y + row_spacing, label_width, label_height,
                      Label="Start Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.start_date = self.add_date("StartDate", start_x + label_width + 10, start_y + row_spacing, field_width, field_height, Dropdown=True)

        self.add_label("lbl_end_date", start_x, start_y + row_spacing * 2, label_width, label_height,
                      Label="End Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.end_date = self.add_date("EndDate", start_x + label_width + 10, start_y + row_spacing * 2, field_width, field_height, Dropdown=True)

        self.add_label("lbl_hours", start_x, start_y + row_spacing * 3, label_width, label_height,
                      Label="Hours:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.hours = self.add_numeric("Hours", start_x + label_width + 10, start_y + row_spacing * 3, field_width, field_height, 
                                     data_type='float', DecimalAccuracy=2, ValueMin=0.01, ValueMax=999999)

        self.add_label("lbl_rate", start_x, start_y + row_spacing * 4, label_width, label_height,
                      Label="Rate:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.rate = self.add_currency("Rate", start_x + label_width + 10, start_y + row_spacing * 4, field_width, field_height,
                                     data_type='float', ValueMin=0.01, ValueMax=999999, 
                                     CurrencySymbol="$", PrependCurrencySymbol=True)

        self.add_label("lbl_total", start_x, start_y + row_spacing * 5, label_width, label_height,
                      Label="Total:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.total = self.add_currency("Total", start_x + label_width + 10, start_y + row_spacing * 5, field_width, field_height,
                                      data_type='float', ReadOnly=True, 
                                      CurrencySymbol="$", PrependCurrencySymbol=True)

        button_y = start_y + row_spacing * 6 + 10
        button_width = 80
        button_height = 25
        button_spacing = 10
        
        total_width = button_width * 2 + button_spacing
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.save_btn = self.add_button("SaveButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                       Label="Add", callback=self.save_hours,
                                       BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

        # Add listeners for auto-calculation
        self.listeners.add_focus_listener(self.hours, lost=self.calculate_total)
        self.listeners.add_focus_listener(self.rate, lost=self.calculate_total)

    def _prepare(self):
        if self.edit_mode and self.hours_data:
            self.employee.Text = str(self.hours_data.get('employee', ''))
            
            # Handle start date
            start_date_str = self.hours_data.get('start_date', '')
            if start_date_str:
                try:
                    if isinstance(start_date_str, str):
                        # Parse date string (YYYY-MM-DD format)
                        date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        self.start_date.Text = date_obj.strftime('%m/%d/%Y')
                    else:
                        # Assume it's already a date object
                        self.start_date.Text = start_date_str.strftime('%m/%d/%Y')
                except Exception as e:
                    self.logger.warning(f"Could not parse start date: {e}")
                    # Set to today's date as fallback
                    today = datetime.now().date()
                    self.start_date.Text = today.strftime('%m/%d/%Y')
            else:
                # Set to today's date
                today = datetime.now().date()
                self.start_date.Text = today.strftime('%m/%d/%Y')

            # Handle end date
            end_date_str = self.hours_data.get('end_date', '')
            if end_date_str:
                try:
                    if isinstance(end_date_str, str):
                        # Parse date string (YYYY-MM-DD format)
                        date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        self.end_date.Text = date_obj.strftime('%m/%d/%Y')
                    else:
                        # Assume it's already a date object
                        self.end_date.Text = end_date_str.strftime('%m/%d/%Y')
                except Exception as e:
                    self.logger.warning(f"Could not parse end date: {e}")
                    # Set to today's date as fallback
                    today = datetime.now().date()
                    self.end_date.Text = today.strftime('%m/%d/%Y')
            else:
                # Set to today's date
                today = datetime.now().date()
                self.end_date.Text = today.strftime('%m/%d/%Y')
            
            # Handle hours
            hours_str = self.hours_data.get('hours', '0')
            try:
                self.hours.setValue(float(hours_str))
            except ValueError:
                self.hours.setValue(1.0)
            
            # Handle rate
            rate_str = self.hours_data.get('rate', '0')
            if rate_str.startswith('$'):
                rate_str = rate_str[1:]
            try:
                self.rate.setValue(float(rate_str))
            except ValueError:
                self.rate.setValue(0.0)
                
            self.calculate_total()
        else:
            # Set default dates to today for new entries
            today = datetime.now().date()
            self.start_date.Text = today.strftime('%m/%d/%Y')
            self.end_date.Text = today.strftime('%m/%d/%Y')

    def calculate_total(self, event=None):
        try:
            hours = self.hours.getValue()
            rate = self.rate.getValue()
            
            if hours > 0 and rate > 0:
                total = hours * rate
                self.total.setValue(total)
            else:
                self.total.setValue(0.0)
        except Exception as e:
            self.logger.error(f"Error calculating total: {e}")
            self.total.setValue(0.0)

    def save_hours(self, event):
        if not self.validate_fields():
            return
        
        try:
            hours = self.hours.getValue()
            rate = self.rate.getValue()
            total = hours * rate
            
            start_date_str = self.start_date.Text.strip()
            end_date_str = self.end_date.Text.strip()
            
            self.hours_result = {
                'employee': self.employee.Text.strip(),
                'start_date': start_date_str,
                'end_date': end_date_str,
                'hours': str(int(hours)) if hours.is_integer() else str(hours),
                'rate': f"${rate:.2f}",
                'total': f"${total:.2f}"
            }
            
            self.end_execute(1)
            
        except Exception as e:
            self.logger.error(f"Error saving hours: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error saving hours: {e}", "Error")

    def validate_fields(self):
        if not self.employee.Text.strip():
            msgbox("Employee name is required.", "Validation Error")
            return False
        
        if not self.start_date.Text.strip():
            msgbox("Start date is required.", "Validation Error")
            return False

        if not self.end_date.Text.strip():
            msgbox("End date is required.", "Validation Error")
            return False
        
        try:
            hours = self.hours.getValue()
            if hours <= 0:
                msgbox("Hours must be greater than 0.", "Validation Error")
                return False
        except Exception:
            msgbox("Please enter valid hours.", "Validation Error")
            return False
        
        try:
            rate = self.rate.getValue()
            if rate <= 0:
                msgbox("Rate must be greater than 0.", "Validation Error")
                return False
        except Exception:
            msgbox("Please enter a valid rate.", "Validation Error")
            return False
        
        return True

    def get_hours_data(self):
        return self.hours_result

    def dispose(self):
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc()) 