from librepy.pybrex import ctr_container
from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.listeners import Listeners
from librepy.jobmanager.data.orders_dao import AcctTransDAO
from librepy.jobmanager.data.settings_dao import SettingsDAO
import traceback

class JobList(ctr_container.Container):
    component_name = 'job_list'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.logger = parent.logger
        self.logger.info("Job List initialized")
        self.parent = parent  
        self.logger.info(f"Parent: {self.parent}")        
        self.ctx = ctx            
        self.logger.info(f"Context: {self.ctx}")
        self.smgr = smgr         
        self.logger.info(f"SMGR: {self.smgr}")
        self.frame = frame        
        self.logger.info(f"Frame: {self.frame}")
        self.ps = ps             
        self.logger.info(f"PS: {self.ps}")
        self.db_manager = ""
        self.logger.info(f"DB Manager: {self.db_manager}")
        self.listeners = Listeners()
        self.logger.info(f"Listeners: {self.listeners}")
        # Initialize SettingsDAO for persisting UI state
        self.settings_dao = SettingsDAO(self.logger)
        self.logger.info(f"SettingsDAO: {self.settings_dao}")
        # Add toolbar offset
        self.toolbar_offset = 0
        
        # Settings configuration
        self.list_config = {
            'button_width': int(ps[2] * 0.20),  # 20% of window width
            'button_height': int(ps[3] * 0.15),  # 15% of window height
            'padding_x': int(ps[2] * 0.02),      # 2% horizontal padding
            'padding_y': int(ps[3] * 0.05),      # 5% vertical padding
            'top_offset': self.toolbar_offset,
            'colors': {
                'border': 0x000000,      # Black border
                'button_normal': 0xFFFFFF,   # White
                'button_hover': 0xF0F0F0,    # Light white
                'button_pressed': 0xE0E0E0,  # Slightly darker white
            }
        }
        self.logger.info(f"List config: {self.list_config}")
        
        self.logger.warning("Sidebar manager not available or job list container not found, creating job list container directly on frame window")
        # Use available area passed from ComponentManager (accounts for sidebar width)
        container_ps = ps
        
        # Initialize the parent Container class properly
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
        self.logger.info(f"Window width: {self.window_width}")
        self.logger.info(f"Window height: {self.window_height}")
        
        self.current_tab = 'jobs'
        self._create()
        self.show()

    def _create(self):
        # Create buttons on the right side
        create_button_width = 160
        create_button_height = 30
        right_margin = 50
        create_y = 15

        # Calculate starting X position for right-aligned buttons
        create_start_x = self.window_width - (create_button_width + right_margin)
        
        self.btn_create_job = self.add_button(
            "btnCreateJob",
            create_start_x, create_y, create_button_width, create_button_height,
            Label="Refresh",
            callback=self.refresh_orders,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=11,
            Border=6
        )
        

        # List title
        self.lbl_list_title = self.add_label(
            "lblListTitle", 
            40, 20, 200, 40, 
            Label="Order List",
            FontHeight=21, 
            FontWeight=150, 
            FontName='Sans-serif'
        )
        
        # Search field and button
        control_y = 95
        control_height = 30
        search_field_width = 300
        search_button_width = 100
        left_margin = 25
        search_x_field = left_margin
        search_x_button = search_x_field + search_field_width + 5

        # Create search field
        self.edt_search_field = self.add_edit(
            "edtSearchField",
            search_x_field, control_y,
            search_field_width, control_height
        )
        
        # Wire dynamic search: per-keystroke with debounce
        try:
            # Initialize search timer holder
            self._search_timer = None
            # Debounced text-change handler
            self.listeners.add_text_listener(self.edt_search_field, callback=self._on_search_text_changed)
            # Optional: Enter key triggers immediate search
            self.listeners.add_key_listener(self.edt_search_field, pressed=self.on_search_key_pressed)
        except Exception:
            # Fallback: ignore if listeners not available
            pass

        # Create search button
        self.btn_search = self.add_button(
            "btnSearch",
            search_x_button, control_y,
            search_button_width, control_height,
            Label="Search",
            callback=self.search_data,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=11,
            Border=6
        )
        
        # Data grid
        grid_y = 150
        grid_height = self.window_height - grid_y - 50
        
        self.data_grid, self.data_grid_model = self.add_grid(
            "grdData",
            25, grid_y, self.window_width - 50, grid_height,
            HeaderBar=True,
            ShowRowHeader=False,
            ShowColumnHeader=True,
            AutoVScroll=True,
            GridLines=True,
            BackgroundColor=0xFFFFFF,
            titles=[
                ("Order #", "transid", 120, 1),
                ("Reference", "referencenumber", 180, 1),
                ("Customer", "orgname", 180, 1),
                ("Phone", "phone", 180, 1),
                ("Calendar Entry", "has_entries", 180, 1),
                ("Start Date", "transdate", 120, 1),
                ("End Date", "expecteddate", 120, 1),
            ]
        )
        
        # Add double-click listener to the data grid
        self.listeners.add_mouse_listener(self.data_grid_model, pressed=self.on_data_double_click)
        self.logger.info("Double-click listener set for data grid")

    def _prepare(self):
        pass

    # Search and sort methods
    def search_data(self, event):
        """Filter grid rows based on search field text"""
        try:
            query = ""
            if hasattr(self, 'edt_search_field'):
                # Prefer Text attr if present (UNO controls), else use getText()
                query = getattr(self.edt_search_field, 'Text', None)
                if query is None:
                    query = self.edt_search_field.getText()
                query = (query or "").strip()
            self.logger.info(f"Search clicked with query: '{query}'")
            self.load_data(query if query else None)
        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            self.logger.error(traceback.format_exc())
    
    def on_search_key_pressed(self, event):
        """Handle Enter key in search field to trigger immediate search."""
        try:
            key = getattr(event, 'KeyCode', None)
            if key in (13, 1280):
                # Trigger immediate search
                self.search_data(event)
        except Exception:
            pass

    def _on_search_text_changed(self, event=None):
        """Debounce text changes and then filter orders."""
        try:
            import threading
            # cancel previous timer if exists
            if getattr(self, '_search_timer', None):
                try:
                    self._search_timer.cancel()
                except Exception:
                    pass
            # schedule filtering after 250ms
            self._search_timer = threading.Timer(0.25, self.filter_orders)
            self._search_timer.daemon = True
            self._search_timer.start()
        except Exception:
            # Fallback: filter immediately
            self.filter_orders()

    def _read_search_text(self):
        try:
            if not hasattr(self, 'edt_search_field'):
                return ""
            txt = getattr(self.edt_search_field, 'Text', None)
            if txt is None:
                txt = self.edt_search_field.getText()
            return (txt or "").strip()
        except Exception:
            return ""

    def filter_orders(self, event=None):
        """Apply current search text to the grid (case-insensitive)."""
        try:
            search_text = self._read_search_text()
            if not search_text:
                self.load_data(None)
            else:
                # Allow simple cleanup akin to example (remove commas)
                search_text = search_text.replace(',', '').strip()
                self.load_data(search_text)
        except Exception as e:
            self.logger.error(f"Error during dynamic filter: {e}")
            self.logger.error(traceback.format_exc())
    
    def sort_data(self, event):
        pass  # Sorting removed
    
    def load_data(self, search_query = None):
        """Load data and optionally filter by search_query (case-insensitive)."""
        try:
            dao = AcctTransDAO(self.logger)
            orders_data = dao.list_sale_orders()
            data = orders_data
            self.logger.info(f"Loaded {len(data)} orders")

            # Apply search filter if provided
            if search_query:
                search_lower = str(search_query).lower().strip()
                filtered = []
                for row in data:
                    ref = str(row.get("referencenumber", "")).lower()
                    org = str(row.get("orgname", "")).lower()
                    phone = str(row.get("phone", "")).lower()
                    transid = str(row.get("transid", "")).lower()
                    if (
                        search_lower in ref
                        or search_lower in org
                        or search_lower in phone
                        or search_lower in transid
                    ):
                        filtered.append(row)
                data = filtered

            # Load the (possibly filtered) data into the grid
            self.data_grid.set_data(data, heading='transid')
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            self.logger.error(traceback.format_exc())
    
    def on_data_double_click(self, event):
        """Handle double-click events on the data grid"""
        try:
            if event.Buttons == 1 and event.ClickCount == 2:
                selected_id = self.data_grid.active_row_heading()
                if selected_id:
                    self.logger.info(f"Double-clicked item ID: {selected_id}")
                    from librepy.jobmanager.components.joblist.order_dlg import OrderDialog
                    dlg = OrderDialog(
                        self.parent, self.ctx, self.smgr, self.frame, self.ps,
                        order_id=int(selected_id),
                    )
                    dlg.execute()
                    # self.load_data()
        except Exception as e:
            self.logger.error(f"Error handling double-click: {e}")
            self.logger.error(traceback.format_exc())

    def show(self):
        super().show()
        self.load_data()
        self.resize(self.window_width, self.window_height)

    def hide(self):
        super().hide()

    def resize(self, width, height):
        """Handle window resize events"""
        try:
            # Update stored dimensions
            self.window_width = width
            self.window_height = height - self.toolbar_offset
            
            # Update settings configuration
            self.list_config.update({
                'button_width': int(width * 0.20),
                'button_height': int((height - self.toolbar_offset) * 0.15),
                'padding_x': int(width * 0.02),
                'padding_y': int((height - self.toolbar_offset) * 0.05),
            })
            
            # Get current sidebar width to maintain proper positioning
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
            
            # Update create buttons (only those that exist)
            if hasattr(self, 'btn_create_job'):
                self.btn_create_job.setPosSize(
                    pos['create_start_x'],
                    pos['create_y'],
                    pos['create_button_width'],
                    pos['create_button_height'],
                    POSSIZE
                )
            
            # Update list title
            if hasattr(self, 'lbl_list_title'):
                self.lbl_list_title.setPosSize(
                    40, pos['title_y'], 200, pos['title_height'], POSSIZE
                )
            
            # Update search field and button
            if hasattr(self, 'edt_search_field'):
                self.edt_search_field.setPosSize(
                    pos['search_field_x'],
                    pos['search_y'],
                    pos['search_field_width'],
                    pos['search_height'],
                    POSSIZE
                )

            if hasattr(self, 'btn_search'):
                self.btn_search.setPosSize(
                    pos['search_button_x'],
                    pos['search_y'],
                    pos['search_button_width'],
                    pos['search_height'],
                    POSSIZE
                )
            
            # Update data grid
            if hasattr(self, 'data_grid'):
                self.data_grid._ctr.setPosSize(
                    pos['grid_x'],
                    pos['grid_y'],
                    pos['grid_width'],
                    pos['grid_height'],
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
        """Dispose of all controls and grids"""
        try:
            self.logger.info("Disposing of List page")
            
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
        # Navigation tabs at the top
        tab_y = 15
        tab_height = 40
        tab_width = 120
        tab_spacing = 5
        start_x = 40
        
        # Create buttons on the right side
        create_button_width = 160
        create_button_height = 30
        create_button_spacing = 5
        right_margin = 50
        create_y = 15
        create_y_increment = 35
        
        # Calculate starting X position for right-aligned buttons
        create_start_x = self.window_width - (create_button_width + right_margin)
        
        # List title
        title_y = 20
        title_height = 40
        
        # Search field and button
        control_y = 95
        control_height = 30

        search_field_width = 300
        search_x_field = 25
        search_x_button = search_x_field + search_field_width + 5

        grid_x = 25
        grid_y = 150
        grid_width = self.window_width - 50  # Leave margin on both sides
        grid_height = self.window_height - grid_y - 50
        
        return {
            'button_y': tab_y,
            'button_height': tab_height,
            'button_width': tab_width,
            'title_y': title_y,
            'title_height': title_height,
            'search_y': control_y,
            'search_height': control_height,
            'create_start_x': create_start_x,
            'create_y': create_y,
            'create_y_increment': create_y_increment,
            'create_button_width': create_button_width,
            'create_button_height': create_button_height,
            'create_button_spacing': create_button_spacing,
            'grid_x': grid_x,
            'grid_y': grid_y,
            'grid_width': grid_width,
            'grid_height': grid_height,
            'search_field_x': search_x_field,
            'search_field_width': search_field_width,
            'search_button_x': search_x_button,
            'search_button_width': 100,
            'search_button_height': control_height
        }

    def refresh_orders(self, event):
        """Refresh the orders list from the database."""
        try:
            self.logger.info("Refresh clicked")
            self.load_data()
        except Exception as e:
            self.logger.error(f"Error refreshing: {e}")
            self.logger.error(traceback.format_exc())
