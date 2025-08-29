import traceback
from librepy.pybrex.sidebar import Sidebar
from librepy.utils.window_geometry_config_manager import WindowGeometryConfigManager

class SidebarManager(object):
    """Manages the sidebar and main containers for the JobManager application"""
    
    def __init__(self, parent, ctx, smgr, frame_manager, ps):
        """Initialize the sidebar manager
        
        Args:
            parent: The main JobManager instance
            ctx: UNO context
            smgr: Service manager
            frame_manager: Frame manager instance
            ps: Position and size tuple (x, y, width, height)
        """
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame_manager = frame_manager
        self.ps = ps
        self.logger = parent.logger

        # Determine default sidebar state based on saved preference
        try:
            _geom_mgr = WindowGeometryConfigManager()
            _expanded_pref = _geom_mgr.get_sidebar_expanded()
        except Exception:
            _expanded_pref = False

        default_state_pref = 'expanded' if _expanded_pref else 'closed'

        # Define sidebar items
        self.sidebar_items = [
            ('Button', 'Order List', 'job_list.png', lambda: self.parent.show_screen('job_list'), 'List of jobs'),
            ('Separator',),
            ('Button', 'Calendar', 'calendar.png', lambda: self.parent.show_screen('calendar'), 'Calendar of events')
        ]
        
        # Create the sidebar
        self.sidebar = Sidebar(
            parent=parent,
            ctx=ctx,
            smgr=smgr,
            frame=frame_manager,
            sidebar_items=self.sidebar_items,
            width=64,
            expanded_width=180,
            default_state=default_state_pref,
            title='OM',
            expanded_title='Order Manager',
            position='left',
            colors={
                'background': 0x1F4E79,  # Darker blue background
                'selected': 0x173B5C,    # Even darker for selected state
                'hover': 0x245A8E,       # Slightly lighter for hover
                'text': 0xFFFFFF,
                'text_selected': 0xFFFFFF,
                'text_hover': 0xFFFFFF,
                'title_text': 0xFFFFFF
            }
        )
        
        # Store current width for reference
        self.width = self.sidebar.get_width()
        
        self.logger.info("SidebarManager initialized")
    
    def resize(self, width, height):
        """Handle resize events
        
        Args:
            width: New width
            height: New height
        """
        try:
            # Update stored dimensions
            self.ps = (self.ps[0], self.ps[1], width, height)
            
            # Resize sidebar
            if hasattr(self.sidebar, 'resize'):
                self.sidebar.resize(width, height)
                        
        except Exception as e:
            self.logger.error(f"Error during resize: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    def toggle_sidebar(self):
        """Toggle sidebar open/closed"""
        try:
            old_width = self.width
            self.sidebar.toggle()
            new_width = self.sidebar.get_width()
            
            if old_width != new_width:
                self.width = new_width
                # Update parent's sidebar_width tracking
                if hasattr(self.parent, 'sidebar_width'):
                    self.parent.sidebar_width = new_width
                # Trigger resize to adjust main containers
                self.resize(self.ps[2], self.ps[3])
                # Persist sidebar expanded state
                try:
                    _geom_mgr = WindowGeometryConfigManager()
                    _geom_mgr.save_sidebar_expanded(self.sidebar.is_expanded)
                except Exception:
                    pass
                
                if hasattr(self.parent, 'component_manager'):
                    self.parent.component_manager.resize_active_component(self.ps[2], self.ps[3])
                
        except Exception as e:
            self.logger.error(f"Error toggling sidebar: {str(e)}")
            self.logger.error(traceback.format_exc())
    
    def dispose(self):
        """Clean up resources"""
        try:
            # Dispose of sidebar
            if hasattr(self, 'sidebar'):
                self.sidebar.dispose() 
            self.logger.info("SidebarManager disposed")
            
        except Exception as e:
            self.logger.error(f"Error during SidebarManager disposal: {str(e)}")
            self.logger.error(traceback.format_exc())


    # Visibility helpers
    def hide(self):
        """Hide the entire sidebar container"""
        try:
            if hasattr(self.sidebar, 'sidebar_container'):
                self.sidebar.sidebar_container.setVisible(False)
        except Exception:
            pass

    def show(self):
        """Show the sidebar container"""
        try:
            if hasattr(self.sidebar, 'sidebar_container'):
                self.sidebar.sidebar_container.setVisible(True)
        except Exception:
            pass