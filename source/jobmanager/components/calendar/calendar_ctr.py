from librepy.pybrex import ctr_container
from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.frame import create_document
from librepy.pybrex.listeners import Listeners
from com.sun.star.awt.ScrollBarOrientation import VERTICAL as SB_VERT
import traceback
import calendar
from datetime import datetime, timedelta
from librepy.jobmanager.data.calendar_entry_order_dao import CalendarEntryOrderDAO

# Calendar configuration constants
DEFAULT_WEEK_ROW_HEIGHT = 130  # Fixed height per week row (will become dynamic)

class Calendar(ctr_container.Container):
    component_name = 'calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.parent = parent          
        self.ctx = ctx            
        self.smgr = smgr         
        self.frame = frame        
        self.ps = ps             
        self.db_manager = ""
        self.listeners = Listeners()
        self.logger = parent.logger
        self.logger.info("Calendar Page initialized")
        
        # Initialize CalendarEntryOrderDAO for calendar entries
        self.order_entries_dao = CalendarEntryOrderDAO(self.logger)
        
        # Add toolbar offset
        self.toolbar_offset = 0
        
        # Calendar state
        self.current_date = datetime.now()
        self.selected_crew = "All"
        
        # Calendar data storage
        self.calendar_data = {}  # Will store jobs grouped by date
        self.events_data = {}    # Will store events grouped by date
        self.job_buttons = {}    # Will store job button controls by date
        self.event_buttons = {}  # Will store event button controls by date
        
        # Enhanced calendar configuration for label + job button layout
        self.calendar_config = {
            'cell_width': 140,           # Will be calculated dynamically based on available width
            'day_label_height': 20,      # Small space for day number
            'job_button_height': 24,     # Increased height for better readability
            'job_button_spacing': 3,     # Increased spacing between job buttons
            'min_cell_height': 20,       # Minimum height (day label + padding)
            'max_jobs_display': None,    # NO LIMIT - show all jobs
            'job_font_size': 9,          # Increased font size for better readability
            'padding_x': int(ps[2] * 0.02),
            'padding_y': int(ps[3] * 0.02),
            'top_offset': self.toolbar_offset,
            'colors': {
                'border': 0x000000,
                'day_label_bg': 0xF8F8F8,
                'day_label_border': 0xDDDDDD,
                'calendar_bg': 0xFFFFFF,
                'calendar_border': 0xDDDDDD,
                'current_month': 0x000000,
                'other_month': 0x999999,
            }
        }
        
        
        # Use available area passed from ComponentManager (accounts for sidebar width)
        container_ps = ps
        
        super().__init__(
            ctx, 
            smgr, 
            frame.window,
            container_ps,
            background_color=0xF2F2F2
        )
        
        # Store initial container size from available area
        self.window_width = ps[2]
        self.window_height = ps[3]
        self.main_container = None
        
        # Calculate initial cell width based on available space
        self._calculate_cell_width()
        
        # Calendar grid storage
        self.day_headers = {}    # Store day header labels (Sun, Mon, etc.)
        self.day_labels = {}     # Store day label controls
        self.calendar_buttons = {}  # Keep for compatibility, but will store job buttons
        
        # Scrollbar-related properties
        self.scroll_offset = 0
        self.scrollbar = None
        self._base_positions = {}  # Store original positions: name → (x, y, w, h, week_num)
        
        # Row-based scrolling properties
        self.row_heights = []
        self.grid_start_y = 0
        self.visible_rows = 0
        self.current_scroll_row = 0
        
        # Fine-grained row tracking
        self.calendar_rows = []
        self.visible_calendar_rows = 0
        self.scroll_multiplier = 100  # For smooth scrolling
        
        self._create()
        self.show()

    def _calculate_cell_width(self):
        """Calculate optimal cell width based on available window width"""
        # Calculate available width for calendar grid
        grid_start_x = 40  # Left margin
        grid_end_margin = 50  # Right margin
        available_width = self.window_width - grid_start_x - grid_end_margin
        
        # Calculate cell width for 7 columns (days of week)
        calculated_width = available_width // 7
        
        # Set minimum cell width (no maximum to use full available space)
        min_cell_width = 120
        
        # Apply constraints
        if calculated_width < min_cell_width:
            cell_width = min_cell_width
        else:
            cell_width = calculated_width
        
        # Update the configuration
        self.calendar_config['cell_width'] = cell_width
        
        self.logger.info(f"Calculated cell width: {cell_width}px (available: {available_width}px)")

    def _create(self):
        # Title
        self.lbl_title = self.add_label(
            "lblTitle", 
            40, 20, 200, 40, 
            Label="Calendar",
            FontHeight=21, 
            FontWeight=150, 
            FontName='Sans-serif'
        )
        
        # Top row buttons
        top_button_width = 140
        top_button_height = 30
        top_button_y = 20
        button_spacing = 10
        right_margin = 50
        
        print_x = self.window_width - (top_button_width + right_margin)
        add_entry_x = print_x - (top_button_width + button_spacing)
        
        # Add Entry button (right side)
        self.btn_create_job = self.add_button(
            "btnCreateEntry",
            add_entry_x, top_button_y, top_button_width, top_button_height,
            Label="Create Entry",
            callback=self.create_calendar_entry,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=11,
            Border=6
        )
        
        # Print Calendar button (rightmost)
        self.btn_print_calendar = self.add_button(
            "btnPrintCalendar",
            print_x, top_button_y, top_button_width, top_button_height,
            Label="Print Calendar",
            callback=self.print_calendar,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=11,
            Border=6
        )
        
        # Create Event button (leftmost of the three)
        # self.btn_create_event = self.add_button(
        #     "btnCreateEvent",
        #     create_event_x, top_button_y, top_button_width, top_button_height,
        #     Label="+ Create Event",
        #     callback=self.create_event,
        #     BackgroundColor=0x2C3E50,
        #     TextColor=0xFFFFFF,
        #     FontWeight=150,
        #     FontHeight=11,
        #     Border=6
        # )
        
        # Navigation controls - aligned to the left
        nav_y = 95
        nav_height = 30
        nav_button_width = 40
        nav_start_x = 40  # Left-justified, under the title
        
        # Previous month button
        self.btn_prev = self.add_button(
            "btnPrev",
            nav_start_x, nav_y, nav_button_width, nav_height,
            Label="<",
            callback=self.prev_month,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Next month button
        self.btn_next = self.add_button(
            "btnNext",
            nav_start_x + nav_button_width + 5, nav_y, nav_button_width, nav_height,
            Label=">",
            callback=self.next_month,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Month/Year display - positioned between nav buttons and right buttons
        month_year_text = self.current_date.strftime("%B %Y")
        month_label_start_x = nav_start_x + (nav_button_width * 2) + 20
        self.lbl_month_year = self.add_label(
            "lblMonthYear",
            month_label_start_x, nav_y, 180, nav_height,
            Label=month_year_text,
            FontHeight=16,
            FontWeight=150,
            FontName='Sans-serif'
        )
        
        # Create vertical scrollbar (hidden initially)
        scrollbar_width = 20
        self.scrollbar = self.add_scrollbar(
            "scrCalendar",
            self.window_width - scrollbar_width - 20,  # Right edge with margin
            200,  # Start below navigation controls
            scrollbar_width,
            self.window_height - 220,  # Height = remaining window space
            Orientation=SB_VERT,
            Visible=False  # Hidden until needed
        )
        
        # Add scroll buttons at top and bottom of scrollbar
        button_size = 18
        scrollbar_x = self.window_width - scrollbar_width - 20
        scrollbar_y = 200
        scrollbar_height = self.window_height - 220
        
        # Up scroll button (positioned just above scrollbar)
        self.btn_scroll_up = self.add_button(
            "btnScrollUp",
            scrollbar_x + 1,  # Center horizontally with scrollbar
            scrollbar_y - button_size - 2,  # Just above scrollbar
            button_size,
            button_size,
            Label="▲",
            callback=self.scroll_up,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontHeight=10,
            FontWeight=150,
            Border=2,
            Visible=False  # Hidden until scrolling is needed
        )
        
        # Down scroll button (positioned just below scrollbar)
        self.btn_scroll_down = self.add_button(
            "btnScrollDown",
            scrollbar_x + 1,  # Center horizontally with scrollbar
            scrollbar_y + scrollbar_height + 2,  # Just below scrollbar
            button_size,
            button_size,
            Label="▼",
            callback=self.scroll_down,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontHeight=10,
            FontWeight=150,
            Border=2,
            Visible=False  # Hidden until scrolling is needed
        )
        
        # Add scroll listener
        self.listeners.add_adjustment_listener(self.scrollbar, self.on_scroll)
        
        # Add keyboard/mouse wheel support to the main container
        try:
            self.listeners.add_key_listener(
                self.container,
                pressed=self.on_key_pressed
            )
            self.logger.info("Keyboard/mouse wheel support added to calendar container")
        except Exception as e:
            self.logger.debug(f"Keyboard/mouse wheel support not available: {e}")
        
        # Create calendar grid
        self._create_calendar_grid()

    def _create_calendar_grid(self):
        # Calendar grid starting position
        grid_start_x = 40
        grid_start_y = 200
        
        # Enhanced calendar dimensions for job buttons
        cell_width = self.calendar_config['cell_width']
        day_label_height = self.calendar_config['day_label_height']
        job_button_height = self.calendar_config['job_button_height']
        job_button_spacing = self.calendar_config['job_button_spacing']
        
        # Clear existing day headers
        for header_name, header in self.day_headers.items():
            try:
                header.dispose()
            except:
                pass
        self.day_headers.clear()
        
        # Day headers - store them for resizing
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(days):
            header_name = f"lblDayHeader{i}"
            day_header = self.add_label(
                header_name,
                grid_start_x + (i * cell_width), grid_start_y - 32,
                cell_width, 28,
                Label=day,
                FontHeight=12,
                FontWeight=150,
                BackgroundColor=0xE0E0E0,  # Slightly darker for better contrast
                TextColor=0x333333,       # Darker text for better readability
                Border=2
            )
            self.day_headers[header_name] = day_header
        
        # Clear existing day labels and job buttons
        for lbl_name, lbl in self.day_labels.items():
            try:
                lbl.dispose()
            except:
                pass
        self.day_labels.clear()
        
        for btn_name, btn in self.calendar_buttons.items():
            try:
                btn.dispose()
            except:
                pass
        self.calendar_buttons.clear()
        
        # Clear existing job buttons storage
        for date_str, buttons in self.job_buttons.items():
            for button in buttons:
                try:
                    button.dispose()
                except:
                    pass
        self.job_buttons.clear()
        
        # Clear existing event buttons storage
        for date_str, buttons in self.event_buttons.items():
            for button in buttons:
                try:
                    button.dispose()
                except:
                    pass
        self.event_buttons.clear()
        
        # Generate calendar data
        cal = calendar.Calendar(6)  # Start week on Sunday
        month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
        
        # Clear position cache
        self._base_positions.clear()
        
        # Track all horizontal rows in the calendar for fine-grained scrolling
        self.calendar_rows = []  # Each item: {'y': y_position, 'height': row_height, 'week_num': week, 'row_type': 'day_label'|'job_row', 'job_row_index': index}
        
        # Dynamic row heights - track actual height needed for each week
        row_heights = [DEFAULT_WEEK_ROW_HEIGHT] * 6  # Start with default, will be updated
        
        # Store row heights for reference
        self.row_heights = row_heights
        self.grid_start_y = grid_start_y
        
        # Create calendar day labels and job buttons
        for week_num in range(6):  # 6 weeks maximum
            # Calculate current row top based on actual heights of previous weeks
            current_week_top = grid_start_y + sum(row_heights[:week_num])
            week_max_height = self.calendar_config['min_cell_height']  # Start with minimum
            
            # Track the maximum number of items (jobs + events) in this week
            max_items_in_week = 0
            
            # First pass: create day labels and determine max items for this week
            week_jobs_data = {}    # day_num -> jobs_for_day
            week_events_data = {}  # day_num -> events_for_day
            for day_num in range(7):  # 7 days per week
                day_index = week_num * 7 + day_num
                if day_index < len(month_days):
                    date = month_days[day_index]
                    date_str = date.strftime('%Y-%m-%d')
                    jobs_for_day = self.calendar_data.get(date_str, [])
                    events_for_day = self.events_data.get(date_str, [])
                    week_jobs_data[day_num] = jobs_for_day
                    week_events_data[day_num] = events_for_day
                    
                    # Total items = jobs first (priority), then events
                    total_items = len(jobs_for_day) + len(events_for_day)
                    if total_items > max_items_in_week:
                        max_items_in_week = total_items
            
            # Create day number row for this week
            day_label_y = current_week_top
            self.calendar_rows.append({
                'y': day_label_y,
                'height': day_label_height,
                'week_num': week_num,
                'row_type': 'day_label',
                'job_row_index': -1
            })
            
            # Create day labels
            for day_num in range(7):
                day_index = week_num * 7 + day_num
                if day_index < len(month_days):
                    date = month_days[day_index]
                    x = grid_start_x + (day_num * cell_width)
                    
                    # Determine if this day is in the current month
                    is_current_month = date.month == self.current_date.month
                    text_color = 0x000000 if is_current_month else 0x999999
                    
                    # Create day label
                    day_label_name = f"dayLabel_{date.day}_{date.month}_{date.year}"
                    day_label = self.add_label(
                        day_label_name,
                        x, day_label_y, cell_width, day_label_height,
                        Label=str(date.day),
                        FontHeight=11,
                        FontWeight=150,
                        TextColor=text_color,
                        BackgroundColor=self.calendar_config['colors']['day_label_bg'],
                        Border=1
                    )
                    
                    self.day_labels[day_label_name] = day_label
                    
                    # Cache day label position with row index
                    row_index = len(self.calendar_rows) - 1
                    self._base_positions[day_label_name] = (x, day_label_y, cell_width, day_label_height, row_index)
            
            # Create item button rows (jobs + events) for this week
            item_button_spacing = self.calendar_config['job_button_spacing']
            item_button_height = self.calendar_config['job_button_height']
            
            for item_row_index in range(max_items_in_week):
                item_row_y = day_label_y + day_label_height + 1 + (item_row_index * (item_button_height + item_button_spacing))
                
                # Add this item row to calendar rows
                self.calendar_rows.append({
                    'y': item_row_y,
                    'height': item_button_height,
                    'week_num': week_num,
                    'row_type': 'item_row',
                    'job_row_index': item_row_index
                })
                
                row_index = len(self.calendar_rows) - 1
                
                # Create items (jobs first, then events) for this row across all days
                for day_num in range(7):
                    day_index = week_num * 7 + day_num
                    if day_index < len(month_days):
                        date = month_days[day_index]
                        x = grid_start_x + (day_num * cell_width)
                        
                        # Get jobs and events for this day
                        jobs_for_day = week_jobs_data.get(day_num, [])
                        events_for_day = week_events_data.get(day_num, [])
                        
                        # Jobs have priority - show them first
                        if item_row_index < len(jobs_for_day):
                            job = jobs_for_day[item_row_index]
                            self.create_single_job_button(date, job, x, item_row_y, cell_width, item_button_height, item_row_index, row_index)
                        else:
                            # Show events after jobs
                            event_index = item_row_index - len(jobs_for_day)
                            if event_index < len(events_for_day):
                                entry = events_for_day[event_index]
                                self.create_single_order_entry_button(date, entry, x, item_row_y, cell_width, item_button_height, event_index, row_index)
            
            # Calculate total height for this week
            week_total_height = day_label_height + 1 + (max_items_in_week * (item_button_height + item_button_spacing))
            if max_items_in_week > 0:
                week_total_height -= item_button_spacing  # Remove last spacing
            
            row_heights[week_num] = max(week_total_height, DEFAULT_WEEK_ROW_HEIGHT)
        
        # Store final row data
        self.row_heights = row_heights
        
        # Add extra empty rows at the end for better scrolling space
        # This ensures there's always room to scroll past the last events
        if len(self.calendar_rows) > 0:
            last_row = self.calendar_rows[-1]
            
            # Add 3 extra empty rows for plenty of scrolling space
            for i in range(3):
                extra_row_y = last_row['y'] + last_row['height'] + job_button_spacing + (i * (job_button_height + job_button_spacing))
                
                self.calendar_rows.append({
                    'y': extra_row_y,
                    'height': job_button_height,  # Same height as job buttons
                    'week_num': 6 + i,  # Beyond normal weeks
                    'row_type': 'empty_row',
                    'job_row_index': -1
                })
        
        # Calculate scrollbar settings for row-by-row scrolling
        # Reserve space at bottom equal to one job button height plus spacing for whitespace
        job_button_height = self.calendar_config['job_button_height']
        job_button_spacing = self.calendar_config['job_button_spacing']
        bottom_whitespace = job_button_height + job_button_spacing
        visible_height = self.window_height - grid_start_y - 20 - bottom_whitespace
        
        # Calculate how many calendar rows can fit in visible area
        self.visible_calendar_rows = 0
        accumulated_height = 0
        for row_data in self.calendar_rows:
            # Use a more generous threshold to allow more content to be considered "visible"
            if accumulated_height + (row_data['height'] * 0.5) <= visible_height:  # 50% visible threshold
                accumulated_height += row_data['height']
                self.visible_calendar_rows += 1
            else:
                break
        
        # Ensure we can see at least some rows
        if self.visible_calendar_rows == 0 and len(self.calendar_rows) > 0:
            self.visible_calendar_rows = 1
        
        # Calculate maximum scroll based on whether content actually exceeds visible area
        # Only allow scrolling if there are more rows than can fit in the visible space
        if len(self.calendar_rows) <= self.visible_calendar_rows:
            # All content fits in visible area - no scrolling needed
            max_scroll_rows = 0
        else:
            # Content exceeds visible area - allow scrolling to show all rows
            max_scroll_rows = len(self.calendar_rows) - self.visible_calendar_rows
            # Add small buffer to ensure last rows are fully visible
            max_scroll_rows += 2
        
        # Configure scrollbar for row-by-row scrolling
        if self.scrollbar:
            scrollbar_model = self.scrollbar.Model
            
            # Use a larger range for smoother scrolling
            # Each row gets 100 units, making scrolling much more responsive
            scroll_multiplier = 100
            max_scroll_value = max_scroll_rows * scroll_multiplier
            
            scrollbar_model.ScrollValueMin = 0
            scrollbar_model.ScrollValueMax = max_scroll_value
            scrollbar_model.BlockIncrement = scroll_multiplier  # Page scroll = 1 row worth
            scrollbar_model.LineIncrement = 20  # Increase for more responsive scrolling
            scrollbar_model.ScrollValue = 0     # Reset to top
            
            # Set visible amount (thumb size) - make it smaller for better scroll range
            if max_scroll_value > 0:
                # Use a much smaller visible size to allow full range scrolling
                # The thumb size should be minimal to maximize scroll range
                # In LibreOffice, max draggable position = ScrollValueMax - VisibleSize
                # So we need VisibleSize to be very small to reach the full range
                visible_amount = max_scroll_value // 20  # Much smaller: 1/20th of total range
                # Set minimum thumb size to be very small
                scrollbar_model.VisibleSize = max(visible_amount, 10)  # Minimum thumb size very small
            else:
                scrollbar_model.VisibleSize = 10
            
            # Store the multiplier for use in scroll event
            self.scroll_multiplier = scroll_multiplier
            
            # Show scrollbar only if scrolling is needed
            scrolling_needed = max_scroll_rows > 0
            self.scrollbar.setVisible(scrolling_needed)
            
            # Show/hide scroll buttons based on scrollbar visibility
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                self.btn_scroll_up.setVisible(scrolling_needed)
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                self.btn_scroll_down.setVisible(scrolling_needed)
                
            # Update button states if scrolling is enabled
            if scrolling_needed:
                self._update_scroll_button_states()
        else:
            self.scroll_multiplier = 100
            
        # Reset scroll offset
        self.scroll_offset = 0
        self.current_scroll_row = 0
            
        self.logger.info(f"Created {len(self.calendar_rows)} calendar rows")
        self.logger.info(f"Visible calendar rows: {self.visible_calendar_rows}, Max scroll rows: {max_scroll_rows}")
        self.logger.info(f"Scrollbar range: 0 to {max_scroll_value if 'max_scroll_value' in locals() else 0}")
        self.logger.info(f"Cached {len(self._base_positions)} control positions")

    def prev_month(self, event):
        """Navigate to previous month"""
        self.logger.info("Previous month clicked")
        if self.current_date.month == 1:
            # Go to December of previous year, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12, day=1)
        else:
            # Go to previous month, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(month=self.current_date.month - 1, day=1)
        self._update_calendar()

    def next_month(self, event):
        """Navigate to next month"""
        self.logger.info("Next month clicked")
        if self.current_date.month == 12:
            # Go to January of next year, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            # Go to next month, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        self._update_calendar()

    def _update_calendar(self):
        """Update the calendar display"""
        # Update month/year label
        month_year_text = self.current_date.strftime("%B %Y")
        self.lbl_month_year.Model.Label = month_year_text
        
        # Reload calendar data for new month
        self.load_calendar_data()
        
        # Recreate the calendar grid with new data
        self._create_calendar_grid()

    def on_day_clicked(self, event, date):
        """Handle day label clicks - no longer needed since jobs have individual buttons"""
        # Note: This method is no longer used since each job has its own button
        # Day labels are now just for display, job buttons handle their own clicks
        self.logger.info(f"Day label clicked: {date} (jobs have individual buttons)")
        pass

    def open_job_for_editing(self, document_id):
        """Open job dialog for editing"""
        try:
            from librepy.jobmanager.components.joblist import job
            dlg = job.Job(self.parent, self.ctx, self.smgr, self.frame, self.ps, job_id=document_id)
            result = dlg.execute()
            
            if result == 1:  # Job was saved
                # Reload calendar data to reflect changes
                self.load_calendar_data()
                self._create_calendar_grid()
                
        except Exception as e:
            self.logger.error(f"Error opening job for editing: {e}")
            self.logger.error(traceback.format_exc())

    def create_calendar_entry(self, event):
        """Open the Calendar Entry dialog and create a new entry on save."""
        self.logger.info("Create Calendar Entry clicked")
        try:
            from librepy.jobmanager.components.calendar.entry_dlg import EntryDialog
            dlg = EntryDialog(self, self.ctx, self.smgr, self.frame, self.ps, edit_mode=False)
            result = dlg.execute()
            if result == 1:
                self.load_calendar_data()
                self._create_calendar_grid()
        except Exception as e:
            self.logger.error(f"Error creating calendar entry: {e}")
            self.logger.error(traceback.format_exc())

    def get_display_date_range(self):
        """Return the inclusive date range currently displayed in the month grid.
        Uses the same logic as load_calendar_data (calendar.itermonthdates with Sunday start).
        """
        try:
            cal = calendar.Calendar(6)
            month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if not month_days:
                self.logger.warning("get_display_date_range: month_days empty")
                return None, None
            start_date, end_date = month_days[0], month_days[-1]
            self.logger.info(f"Display date range: {start_date} .. {end_date}")
            return start_date, end_date
        except Exception as e:
            self.logger.error(f"Error computing display date range: {e}")
            self.logger.error(traceback.format_exc())
            return None, None

    def print_calendar(self, event):
        """Print the calendar events for the currently displayed date range."""
        try:
            self.logger.info("Print Calendar clicked")
            start_date, end_date = self.get_display_date_range()
            if not start_date or not end_date:
                self.logger.warning("No calendar range available to print")
                return
            from librepy.jasper_reports.print_calendar import save_calendar_range_as_pdf
            self.logger.info(f"Invoking PDF export for range {start_date}..{end_date}")
            save_calendar_range_as_pdf(start_date, end_date)
            self.logger.info("Calendar PDF export invoked successfully")
        except Exception as e:
            self.logger.error(f"Error printing calendar: {e}")
            self.logger.error(traceback.format_exc())

    def load_calendar_data(self):
        """Load calendar events from database"""
        try:
            # Calculate date range for current month
            start_date = self.current_date.replace(day=1)
            
            # Get the last day of the month
            if self.current_date.month == 12:
                end_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = self.current_date.replace(month=self.current_date.month + 1, day=1) - timedelta(days=1)
            
            # Extend range to include previous/next month days shown in calendar
            cal = calendar.Calendar(6)  # Start week on Sunday
            month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if month_days:
                start_date = month_days[0]
                end_date = month_days[-1]
            
            # Jobs/events discontinued for calendar rendering
            self.calendar_data = {}

            # Load CalendarEntryOrder entries and expand per-day
            entries = self.order_entries_dao.get_entries_by_date_range(start_date, end_date)
            self.events_data = {}
            for e in entries:
                if not e.get('start_date'):
                    continue
                cur = e['start_date']
                end_lim = e.get('end_date') or e['start_date']
                while cur <= end_lim:
                    key = cur.strftime('%Y-%m-%d')
                    self.events_data.setdefault(key, []).append(e)
                    cur += timedelta(days=1)

            self.logger.info(f"Loading order entries for {start_date} to {end_date}")
            self.logger.info(f"Days with entries: {len(self.events_data)}")
            
        except Exception as e:
            self.logger.error(f"Error loading calendar data: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}
            self.events_data = {}

    def update_crew_dropdown(self):
        """Update crew dropdown with crews from database"""
        try:
            crews = self.job_dao.get_available_crews()
            crew_list = ["All"] + crews + ["Events"]
            self.crew_dropdown.Model.StringItemList = tuple(crew_list)
            self.crew_dropdown.setText(self.selected_crew)
            self.logger.info(f"Updated crew dropdown with {len(crews)} crews + Events option")
        except Exception as e:
            self.logger.error(f"Error updating crew dropdown: {e}")
            # Fallback to default crews
            self.crew_dropdown.Model.StringItemList = ("All", "Crew 1", "Crew 2", "Crew 3", "Events")
            self.crew_dropdown.setText(self.selected_crew)

    def show(self):
        # Load calendar data first
        self.load_calendar_data()
        super().show()
        self.resize(self.window_width, self.window_height)

    def hide(self):
        super().hide()

    def resize(self, width, height):
        """Handle window resize events"""
        try:
            # Update stored dimensions
            self.window_width = width
            self.window_height = height - self.toolbar_offset
            
            # Recalculate cell width based on new window size
            self._calculate_cell_width()
            
            # Update configuration (keep enhanced layout settings)
            self.calendar_config.update({
                'padding_x': int(width * 0.02),
                'padding_y': int((height - self.toolbar_offset) * 0.02),
            })
        
            sidebar_width = getattr(self.parent, 'sidebar_width', 0)
            
            # Resize the main container (preserve sidebar offset for X position)
            self.container.setPosSize(
                sidebar_width,  # Start after sidebar, not at 0
                self.toolbar_offset,
                width, 
                height - self.toolbar_offset,
                POSSIZE
            )
            
            # Calculate positions for all components
            pos = self._calculate_positions()
            
            # Update top row buttons: left nav, right action buttons
            if hasattr(self, 'btn_create_job'):
                self.btn_create_job.setPosSize(
                    pos['add_entry_x'],
                    pos['top_button_y'],
                    pos['top_button_width'],
                    pos['top_button_height'],
                    POSSIZE
                )
            
            if hasattr(self, 'btn_print_calendar'):
                self.btn_print_calendar.setPosSize(
                    pos['print_x'],
                    pos['top_button_y'],
                    pos['top_button_width'],
                    pos['top_button_height'],
                    POSSIZE
                )
            
            if hasattr(self, 'btn_prev'):
                self.btn_prev.setPosSize(
                    pos['nav_start_x'],
                    pos['nav_y'],
                    pos['nav_button_width'],
                    pos['nav_height'],
                    POSSIZE
                )
            
            if hasattr(self, 'btn_next'):
                self.btn_next.setPosSize(
                    pos['nav_start_x'] + pos['nav_button_width'] + 5,
                    pos['nav_y'],
                    pos['nav_button_width'],
                    pos['nav_height'],
                    POSSIZE
                )
            
            if hasattr(self, 'lbl_month_year'):
                self.lbl_month_year.setPosSize(
                    pos['month_label_x'],
                    pos['nav_y'],
                    180,
                    pos['nav_height'],
                    POSSIZE
                )
            
            if hasattr(self, 'lbl_title'):
                self.lbl_title.setPosSize(
                    pos['title_x'],
                    pos['title_y'],
                    pos['title_width'],
                    pos['title_height'],
                    POSSIZE
                )
            
            # Update calendar grid (recreate with new dimensions)
            if hasattr(self, 'calendar_buttons'):
                self._create_calendar_grid()
            
            # Update scrollbar position and size
            if hasattr(self, 'scrollbar') and self.scrollbar:
                scrollbar_width = 20
                scrollbar_x = width - scrollbar_width - 20
                scrollbar_y = 200
                scrollbar_height = height - self.toolbar_offset - 220
                
                self.scrollbar.setPosSize(
                    scrollbar_x,  # Right edge with margin
                    scrollbar_y,  # Start below navigation controls
                    scrollbar_width,
                    scrollbar_height,  # Adjust for toolbar offset
                    POSSIZE
                )
                
                # Update scroll button positions
                button_size = 18
                if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                    self.btn_scroll_up.setPosSize(
                        scrollbar_x + 1,  # Center horizontally with scrollbar
                        scrollbar_y - button_size - 2,  # Just above scrollbar
                        button_size,
                        button_size,
                        POSSIZE
                    )
                    
                if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                    self.btn_scroll_down.setPosSize(
                        scrollbar_x + 1,  # Center horizontally with scrollbar
                        scrollbar_y + scrollbar_height + 2,  # Just below scrollbar
                        button_size,
                        button_size,
                        POSSIZE
                    )
                
            # Force redraw
            if hasattr(self, 'container') and self.container.getPeer():
                peer = self.container.getPeer()
                peer.invalidate(0)
                
        except Exception as e:
            self.logger.error(f"Error during resize: {e}")
            self.logger.error(traceback.format_exc())

    def dispose(self):
        """Dispose of all controls and calendar components"""
        try:
            self.logger.info("Disposing of Calendar page")
            
            # Dispose day headers
            for header_name, header in self.day_headers.items():
                try:
                    header.dispose()
                except:
                    pass
            self.day_headers.clear()
            
            # Dispose day labels
            for lbl_name, lbl in self.day_labels.items():
                try:
                    lbl.dispose()
                except:
                    pass
            self.day_labels.clear()
            
            # Dispose job buttons
            for date_str, buttons in self.job_buttons.items():
                for button in buttons:
                    try:
                        button.dispose()
                    except:
                        pass
            self.job_buttons.clear()
            
            # Dispose calendar buttons (job buttons are also stored here)
            for btn_name, btn in self.calendar_buttons.items():
                try:
                    btn.dispose()
                except:
                    pass
            self.calendar_buttons.clear()
            
            # Dispose scroll buttons
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up is not None:
                try:
                    self.btn_scroll_up.dispose()
                except Exception as scroll_up_error:
                    self.logger.error(f"Error disposing scroll up button: {str(scroll_up_error)}")
                finally:
                    self.btn_scroll_up = None
                    
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down is not None:
                try:
                    self.btn_scroll_down.dispose()
                except Exception as scroll_down_error:
                    self.logger.error(f"Error disposing scroll down button: {str(scroll_down_error)}")
                finally:
                    self.btn_scroll_down = None
            
            # Dispose scrollbar
            if hasattr(self, 'scrollbar') and self.scrollbar is not None:
                try:
                    self.scrollbar.dispose()
                except Exception as scrollbar_error:
                    self.logger.error(f"Error disposing scrollbar: {str(scrollbar_error)}")
                finally:
                    self.scrollbar = None
            
            # Dispose of main container
            if hasattr(self, 'container') and self.container is not None:
                try:
                    # Make sure the container window is hidden
                    try:
                        self.container.getPeer().setVisible(False)
                    except:
                        pass
                    
                    # Then dispose the container
                    self.container.dispose()
                except Exception as container_error:
                    self.logger.error(f"Error disposing container: {str(container_error)}")
                finally:
                    self.container = None
            
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())

    def _calculate_positions(self):
        """Calculate positions for UI components based on current window size"""
        # Top row buttons
        top_button_width = 140
        top_button_height = 30
        top_button_y = 20
        button_spacing = 10
        right_margin = 50
        left_margin = 40
        
        # Right-justified buttons
        print_x = self.window_width - (top_button_width + right_margin)
        add_entry_x = print_x - (top_button_width + button_spacing)
        
        # Left-justified navigation controls
        nav_y = 95
        nav_height = 30
        nav_button_width = 40
        nav_start_x = left_margin
        month_label_x = nav_start_x + (nav_button_width * 2) + 20
        
        # Title
        title_x = 40
        title_y = 20
        title_width = 200
        title_height = 40
        
        return {
            'top_button_y': top_button_y,
            'top_button_width': top_button_width,
            'top_button_height': top_button_height,
            'add_entry_x': add_entry_x,
            'print_x': print_x,
            'nav_start_x': nav_start_x,
            'nav_y': nav_y,
            'nav_button_width': nav_button_width,
            'nav_height': nav_height,
            'month_label_x': month_label_x,
            'title_x': title_x,
            'title_y': title_y,
            'title_width': title_width,
            'title_height': title_height,
        }

    # def log_out(self, event):
    #     try:
    #         from librepy.pybrex.msgbox import confirm_action
    #         if not confirm_action("Are you sure you want to log out?", "Confirm Logout"):
    #             return
    #     except Exception:
    #         pass
    #     self.logger.info("Log out clicked")
    #     if hasattr(self.parent, 'sidebar_manager'):
    #         try:
    #             self.parent.sidebar_manager.hide()
    #         except Exception:
    #             pass
    #     self.parent.ui_initialized = False
    #     self.parent.show_screen('log_in')

    def create_single_job_button(self, date, job, x, y, cell_width, job_button_height, job_row_index, row_index):
        """Create a single job button for a specific row and position"""
        try:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in self.job_buttons:
                self.job_buttons[date_str] = []
            
            # Format job button text
            crew_name = job.get('crew_assigned', 'Unassigned')
            customer_name = job.get('customer_name', 'Unknown')
            
            # Improved text formatting for better readability
            max_total_length = 18
            
            # Format: "Crew1: Customer" or just "Customer" if no crew
            if crew_name and crew_name != 'Unassigned':
                # Truncate crew name if too long
                if len(crew_name) > 10:
                    crew_display = crew_name[:8] + ".."
                else:
                    crew_display = crew_name
                
                # Calculate remaining space for customer name
                prefix_length = len(crew_display) + 2  # +2 for ": "
                remaining_space = max_total_length - prefix_length
                
                if len(customer_name) > remaining_space and remaining_space > 3:
                    customer_display = customer_name[:remaining_space-2] + ".."
                else:
                    customer_display = customer_name
                
                button_text = f"{crew_display}: {customer_display}"
            else:
                # No crew, use more space for customer name
                if len(customer_name) > max_total_length:
                    button_text = customer_name[:max_total_length-2] + ".."
                else:
                    button_text = customer_name
            
            # Get crew color for this specific job
            crew_color = self.job_dao.get_crew_color(crew_name)
            
            # Use lighter color for text if background is dark
            text_color = 0xFFFFFF if crew_color in [0x2C3E50, 0xE74C3C, 0x9B59B6] else 0x000000
            
            job_button_name = f"jobBtn_{date_str}_{job_row_index}"
            
            # Create individual job button
            job_button = self.add_button(
                job_button_name,
                x + 2, y, cell_width - 4, job_button_height,
                Label=button_text,
                callback=lambda event, doc_id=job.get('document_id'): self.open_job_for_editing(doc_id),
                BackgroundColor=crew_color,
                TextColor=text_color,
                FontHeight=self.calendar_config['job_font_size'],
                FontWeight=150,
                Border=0
            )
            
            self.job_buttons[date_str].append(job_button)
            self.calendar_buttons[job_button_name] = job_button
            
            # Cache job button position with row index
            self._base_positions[job_button_name] = (x + 2, y, cell_width - 4, job_button_height, row_index)
            
        except Exception as e:
            self.logger.error(f"Error creating job button for {date}: {e}")
            self.logger.error(traceback.format_exc())

    def create_single_event_button(self, date, event, x, y, cell_width, event_button_height, event_row_index, row_index):
        """Create a single event button for a specific row and position"""
        try:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in self.event_buttons:
                self.event_buttons[date_str] = []
            
            # Format event button text
            title = event.get('title', 'Untitled Event')
            
            # Text formatting for events
            max_total_length = 18
            
            # Truncate title if too long
            if len(title) > max_total_length:
                button_text = title[:max_total_length-2] + ".."
            else:
                button_text = title
            
            # Get event status color
            event_status = event.get('status', 'Pending')
            event_bg_color = self.events_dao.get_event_status_color(event_status)
            
            # Use white text for better contrast
            text_color = 0xFFFFFF
            
            event_button_name = f"eventBtn_{date_str}_{event_row_index}"
            
            # Create individual event button
            event_button = self.add_button(
                event_button_name,
                x + 2, y, cell_width - 4, event_button_height,
                Label=button_text,
                callback=lambda ev, event_id=event.get('id'): self.open_event_for_editing(event_id),
                BackgroundColor=event_bg_color,
                TextColor=text_color,
                FontHeight=self.calendar_config['job_font_size'],
                FontWeight=150,
                Border=0
            )
            
            self.event_buttons[date_str].append(event_button)
            self.calendar_buttons[event_button_name] = event_button
            
            # Cache event button position with row index
            self._base_positions[event_button_name] = (x + 2, y, cell_width - 4, event_button_height, row_index)
            
        except Exception as e:
            self.logger.error(f"Error creating event button for {date}: {e}")
            self.logger.error(traceback.format_exc())

    def create_single_order_entry_button(self, date, entry, x, y, cell_width, entry_button_height, entry_row_index, row_index):
        """Create a single calendar entry button (order-less) for a specific row and position"""
        try:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in self.event_buttons:
                self.event_buttons[date_str] = []

            # Build label from entry's own fields (no order assumed)
            name = entry.get('title') or entry.get('description') or 'Entry'
            max_total_length = 18
            if len(name) > max_total_length:
                button_text = name[:max_total_length-2] + ".."
            else:
                button_text = name

            # Default color for calendar entries (blue)
            entry_bg_color = 0x2B579A
            text_color = 0xFFFFFF

            # If a status color is provided (like "#FFFFFF"), use it
            raw_color = entry.get('status_color')
            if isinstance(raw_color, str):
                hex_str = raw_color.strip()
                if hex_str.startswith('#'):
                    hex_str = hex_str[1:]
                if len(hex_str) == 6 and all(c in '0123456789abcdefABCDEF' for c in hex_str):
                    try:
                        entry_bg_color = int(hex_str, 16)
                    except Exception:
                        pass
            # Optional: adjust text color for readability based on luminance
            try:
                r = (entry_bg_color >> 16) & 0xFF
                g = (entry_bg_color >> 8) & 0xFF
                b = entry_bg_color & 0xFF
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                text_color = 0x000000 if luminance > 180 else 0xFFFFFF
            except Exception:
                pass

            btn_name = f"orderEntryBtn_{date_str}_{entry_row_index}"
            entry_id = entry.get('id')

            entry_button = self.add_button(
                btn_name,
                x + 2, y, cell_width - 4, entry_button_height,
                Label=button_text,
                callback=lambda ev, eid=entry_id: self.open_entry_for_editing(eid),
                BackgroundColor=entry_bg_color,
                TextColor=text_color,
                FontHeight=self.calendar_config['job_font_size'],
                FontWeight=150,
                Border=0
            )

            self.event_buttons[date_str].append(entry_button)
            self.calendar_buttons[btn_name] = entry_button
            # Cache position with row index for scrolling
            self._base_positions[btn_name] = (x + 2, y, cell_width - 4, entry_button_height, row_index)

        except Exception as e:
            self.logger.error(f"Error creating calendar entry button for {date}: {e}")
            self.logger.error(traceback.format_exc())

    def open_order_for_viewing(self, order_id):
        """Open the Order dialog for the given order_id"""
        try:
            if order_id is None:
                self.logger.warn("Order ID is None; cannot open order dialog")
                return
            from librepy.jobmanager.components.joblist.order_dlg import OrderDialog
            dlg = OrderDialog(self, self.ctx, self.smgr, self.frame, self.ps, order_id=order_id)
            dlg.execute()
        except Exception as e:
            self.logger.error(f"Error opening order {order_id}: {e}")
            self.logger.error(traceback.format_exc())

    def open_event_for_editing(self, event_id):
        """Open event dialog for editing an existing event"""
        try:
            # Get the event from database
            event = self.events_dao.get_event_by_id(event_id)
            if not event:
                from librepy.pybrex.msgbox import MsgBox
                MsgBox("Event not found.", 16, "Error")
                return
            
            # Import and create the event dialog
            from librepy.jobmanager.components.calendar.events import EventDialog
            
            event_dialog = EventDialog(
                self, self.ctx, self.smgr, self.frame, self.ps,
                edit_mode=True, event_data=event
            )
            
            result = event_dialog.execute()
            if result == 1:  # Event was updated
                # Reload calendar data to show updated event
                self.load_calendar_data()
                self._create_calendar_grid()
                
        except Exception as e:
            self.logger.error(f"Error editing event {event_id}: {e}")
            self.logger.error(traceback.format_exc())

    def open_entry_for_editing(self, entry_id):
        """Open calendar entry dialog for editing an existing entry (order-less)."""
        try:
            from librepy.pybrex.msgbox import MsgBox, confirm_action
            from librepy.jobmanager.components.calendar.entry_dlg import EntryDialog

            entry = self.order_entries_dao.get_entry_by_id(entry_id)
            if not entry:
                MsgBox("Entry not found.", 16, "Error")
                return

            dlg = EntryDialog(self, self.ctx, self.smgr, self.frame, self.ps, edit_mode=True, entry_data=entry)
            result = dlg.execute()
            if result == 1:
                payload = dlg.get_entry_data() or {}
                if not payload.get('end_date') and payload.get('start_date'):
                    payload['end_date'] = payload['start_date']
                self.logger.debug(f"Calendar.open_entry_for_editing: Update payload for entry {entry_id} = {payload}")
                self.order_entries_dao.update_entry(entry_id, payload)
                self.load_calendar_data()
                self._create_calendar_grid()
            elif result == 2 and getattr(dlg, 'delete_requested', False):
                self.order_entries_dao.delete_entry(entry_id)
                self.load_calendar_data()
                self._create_calendar_grid()
        except Exception as e:
            self.logger.error(f"Error editing calendar entry {entry_id}: {e}")
            self.logger.error(traceback.format_exc())

    def on_scroll(self, ev):
        """Handle scrollbar scroll events - smooth row-by-row scrolling"""
        scroll_value = int(ev.Value)  # Raw scrollbar value (0 to max_scroll_rows * 100)
        
        # Convert scroll value to row index (with smooth interpolation)
        scroll_row = scroll_value // self.scroll_multiplier
        scroll_progress = (scroll_value % self.scroll_multiplier) / self.scroll_multiplier
        
        # Clamp to valid range
        scroll_row = max(0, min(scroll_row, len(self.calendar_rows) - 1))
        
        # For very responsive scrolling, start showing next row as soon as user moves scrollbar
        if scroll_progress > 0.1:  # 10% threshold for immediate response
            scroll_row = min(scroll_row + 1, len(self.calendar_rows) - 1)
        
        if scroll_row == self.current_scroll_row:
            return  # No change needed
            
        old_scroll_row = self.current_scroll_row
        self.current_scroll_row = scroll_row
        
        # Calculate offset for smooth positioning
        offset_y = 0
        if scroll_row > 0 and scroll_row < len(self.calendar_rows):
            target_row_y = self.calendar_rows[scroll_row]['y']
            offset_y = self.grid_start_y - target_row_y
            
            # Add smooth sub-row positioning if we're between rows
            if scroll_progress > 0.1 and scroll_row > 0:
                # Interpolate between current and next row position
                current_row_y = self.calendar_rows[scroll_row - 1]['y'] if scroll_row > 0 else self.grid_start_y
                next_row_y = self.calendar_rows[scroll_row]['y'] if scroll_row < len(self.calendar_rows) else current_row_y
                
                # Smooth interpolation
                interpolated_y = current_row_y + (next_row_y - current_row_y) * scroll_progress
                offset_y = self.grid_start_y - interpolated_y
        
        self.logger.debug(f"Scroll value: {scroll_value}, row: {scroll_row}, progress: {scroll_progress:.2f}, offset: {offset_y}")
        
        # Calculate which rows should be visible
        visible_row_start = scroll_row
        # Allow for more rows beyond calculated visible range to show more content at bottom
        visible_row_end = min(scroll_row + self.visible_calendar_rows + 3, len(self.calendar_rows))  # Increased buffer from 1 to 3
        
        # Update visibility and position for all controls
        controls_moved = 0
        controls_hidden = 0
        
        # Move day labels
        for label_name in self.day_labels.keys():
            if label_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[label_name]
                
                if visible_row_start <= row_index < visible_row_end:
                    # Row is visible
                    self.day_labels[label_name].setPosSize(x, y + offset_y, w, h, POSSIZE)
                    self.day_labels[label_name].setVisible(True)
                    controls_moved += 1
                else:
                    # Row is hidden
                    self.day_labels[label_name].setVisible(False)
                    controls_hidden += 1
        
        # Move job buttons
        for button_name in self.calendar_buttons.keys():
            if button_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[button_name]
                
                if visible_row_start <= row_index < visible_row_end:
                    # Row is visible
                    self.calendar_buttons[button_name].setPosSize(x, y + offset_y, w, h, POSSIZE)
                    self.calendar_buttons[button_name].setVisible(True)
                    controls_moved += 1
                else:
                    # Row is hidden
                    self.calendar_buttons[button_name].setVisible(False)
                    controls_hidden += 1
        
        self.logger.debug(f"Moved {controls_moved} controls, hidden {controls_hidden} controls")
        
        # Update scroll button states based on new scroll position
        self._update_scroll_button_states()
        
        # Force redraw for smoother visual updates
        if hasattr(self, 'container') and self.container.getPeer():
            peer = self.container.getPeer()
            peer.invalidate(0)

    def on_key_pressed(self, ev):
        """Handle key presses for calendar scrolling"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
                
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            new_value = current_value
            
            # Check key codes for scrolling
            if ev.KeyCode == 1025:  # Up arrow
                new_value = max(0, current_value - self.scroll_multiplier)
                self.logger.debug("Up arrow pressed")
            elif ev.KeyCode == 1026:  # Down arrow  
                new_value = min(max_value, current_value + self.scroll_multiplier)
                self.logger.debug("Down arrow pressed")
            elif ev.KeyCode == 1031:  # Page Up
                new_value = max(0, current_value - (self.scroll_multiplier * 3))
                self.logger.debug("Page Up pressed")
            elif ev.KeyCode == 1032:  # Page Down
                new_value = min(max_value, current_value + (self.scroll_multiplier * 3))
                self.logger.debug("Page Down pressed")
            elif ev.KeyCode == 1029:  # Home
                new_value = 0
                self.logger.debug("Home pressed")
            elif ev.KeyCode == 1030:  # End
                new_value = max_value
                self.logger.debug("End pressed")
            else:
                # Log unknown key codes for debugging
                self.logger.debug(f"Key pressed: {ev.KeyCode}")
                return
                
            # Update scrollbar if value changed
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Keyboard scroll: {current_value} -> {new_value}")
                
        except Exception as e:
            self.logger.error(f"Error in key handler: {e}")

    def scroll_up(self, event):
        """Handle up scroll button click - scroll up by one row"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            # Check if scrollbar is visible using Model.Visible
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                # If Model.Visible doesn't work, just proceed
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            new_value = max(min_value, current_value - self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Up button scroll: {current_value} -> {new_value}")
                
                # Manually trigger scroll event to update calendar display
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            self.logger.error(f"Error in scroll_up: {e}")

    def scroll_down(self, event):
        """Handle down scroll button click - scroll down by one row"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            # Check if scrollbar is visible using Model.Visible
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                # If Model.Visible doesn't work, just proceed
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            new_value = min(max_value, current_value + self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Down button scroll: {current_value} -> {new_value}")
                
                # Manually trigger scroll event to update calendar display
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            self.logger.error(f"Error in scroll_down: {e}")

    def _update_scroll_button_states(self):
        """Update scroll button enabled/disabled states based on scrollbar position"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
                
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            max_value = self.scrollbar.Model.ScrollValueMax
            
            # Update up button state
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                # Disable if at minimum, enable otherwise
                up_enabled = current_value > min_value
                self.btn_scroll_up.Model.Enabled = up_enabled
                # Visual feedback - lighter color when disabled
                if up_enabled:
                    self.btn_scroll_up.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_up.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_up.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_up.Model.TextColor = 0x999999
            
            # Update down button state
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                # Disable if at maximum, enable otherwise
                down_enabled = current_value < max_value
                self.btn_scroll_down.Model.Enabled = down_enabled
                # Visual feedback - lighter color when disabled
                if down_enabled:
                    self.btn_scroll_down.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_down.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_down.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_down.Model.TextColor = 0x999999
                    
        except Exception as e:
            self.logger.error(f"Error updating scroll button states: {e}")
