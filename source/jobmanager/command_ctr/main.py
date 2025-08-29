'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''
import traceback
from librepy.utils.window_geometry_config_manager import WindowGeometryConfigManager

from librepy.pybrex.values import pybrex_logger
logger = pybrex_logger(__name__)

class JobManager(object):
    """JobManager application"""
    
    def __init__(self, ctx, smgr):
        self.logger = logger
        self.logger.info("JobManager initialized")
        
        self.ctx = ctx
        self.smgr = smgr
        
        self._is_disposing = False
        self._initialization_complete = False
        
        self.ps = (0, 0, 1800, 1000)
        self.menubar_height = 25
        self.toolbar_height = 55
        
        self.component_manager = None
        # self.ui_initialized = False

        self._load_saved_geometry()

        from librepy.jobmanager.command_ctr import frame_manager
        self.frame_manager = frame_manager.FrameManager(
            self,
            ctx, 
            smgr, 
            ps=self.ps,
            menubar_height=self.menubar_height
        )
        self.logger.info("Frame manager initialized")

        # Instantiate sidebar manager in hidden mode so we can host login container without showing sidebar
        self.create_sidebar_manager(hidden=False)
        
        try:
            from librepy.jobmanager.command_ctr.component_manager import ComponentManager
            self.component_manager = ComponentManager(
                self,
                self.ctx,
                self.smgr,
                self.frame_manager,
                self.ps
            )
            
            self.active_screen = 'job_list'
            self.component_manager.switch_component(self.active_screen)
        except Exception:
            self.logger.error("Error creating component manager:")
            self.logger.error(traceback.format_exc())
            self.active_screen = None

        self.sidebar_width = self.sidebar_manager.width if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None else 0
        self.create_menubar_manager()
        try:
            actual_ps = self.frame_manager.window.getPosSize()
            self.ps = (self.ps[0], self.ps[1], actual_ps.Width, actual_ps.Height)
            if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None:
                self.sidebar_manager.resize(self.ps[2], self.ps[3])
        except Exception:
            self.logger.error("Error syncing actual window size:")
            self.logger.error(traceback.format_exc())

        self._initialization_complete = True
        
        if self.component_manager is not None:
            self.logger.info("Initialization complete - forcing component resize")
            self.component_manager.resize_active_component(self.ps[2], self.ps[3])
            self.logger.info(f"Components resized to {self.ps[2]}x{self.ps[3]}")

    def _load_saved_geometry(self):
        """Load saved window geometry and apply it to self.ps if valid"""
        try:
            geometry_manager = WindowGeometryConfigManager()
            saved_geometry = geometry_manager.get_geometry()
            
            if saved_geometry and geometry_manager.is_geometry_valid_for_screen(saved_geometry):
                x, y, width, height = saved_geometry
                self.ps = (x, y, width, height)
                self.logger.info(f"Loaded saved window geometry: ({x}, {y}, {width}, {height})")
            else:
                self.logger.debug("No valid saved geometry found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Error loading saved geometry: {e}")
            self.logger.error(traceback.format_exc())

    def show_screen(self, screen_name):
        """
        Central method to handle screen transitions
        Uses the component manager to switch between components
        
        Args:
            screen_name (str): Name of the screen to show ('log_in', 'job_list', 'calendar', etc.)
        """
        if self.component_manager is None:
            self.logger.error("Cannot show screen: component manager not initialized")
            return
            
        if self.active_screen == screen_name:
            return
            
        component = self.component_manager.switch_component(screen_name)
        
        if component is not None:
            self.active_screen = screen_name
        else:
            self.logger.error(f"Failed to switch to screen: {screen_name}")

    def window_resizing(self, width, height):
        """Handle window resize events"""
        if self.component_manager is None:
            return
            
        self.ps = (self.ps[0], self.ps[1], width, height)
        self.logger.info(f"Window resized to {width}x{height}")
        
        if hasattr(self, 'sidebar_manager') and self.sidebar_manager is not None:
            self.sidebar_manager.resize(width, height)
            
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            self.component_manager.resize_active_component(width, height)
            self.logger.info(f"Components resized to {width}x{height}")

    def dispose(self):
        """Dispose of the JobManager application"""
        if hasattr(self, '_is_disposing') and self._is_disposing:
            return
            
        self._is_disposing = True
        self.logger.info("Disposing JobManager application...")
        
        try:
            if hasattr(self, 'component_manager') and self.component_manager is not None:
                self.component_manager.dispose()
                self.logger.info("Component manager disposed")
        except Exception:
            self.logger.error("Error disposing component manager:")
            self.logger.error(traceback.format_exc())
        
        try:
            if hasattr(self, 'frame_manager'):
                self.frame_manager.dispose()
                self.logger.info("Frame manager disposed")
        except Exception:
            self.logger.error("Error disposing frame manager:")
            self.logger.error(traceback.format_exc())
            
        self._is_disposing = False

    def create_sidebar_manager(self, hidden=False):
        try:
            from librepy.jobmanager.command_ctr import sidebar_manager
            self.sidebar_manager = sidebar_manager.SidebarManager(self, self.ctx, self.smgr, self.frame_manager, self.ps)
            if hidden and hasattr(self.sidebar_manager, 'hide'):
                self.sidebar_manager.hide()
            self.logger.info("Sidebar manager initialized")
        except Exception:
            self.logger.error("Error creating sidebar manager:")
            self.logger.error(traceback.format_exc())
            self.sidebar_manager = None

    def create_menubar_manager(self):
        try:
            from librepy.jobmanager.command_ctr import menubar_manager as _mm
            self.menubar_manager = _mm.MenubarManager(self, self.ctx, self.smgr, self.frame_manager)
            self.logger.info("Menubar manager initialized")
        except Exception:
            self.logger.error("Error creating menubar manager:")
            self.logger.error(traceback.format_exc())


def main(*args):
    """Main function for the JobManager application"""
    ctx = getDefaultContext()
    smgr = ctx.ServiceManager
    jobmanager = JobManager(ctx, smgr)
    
    if not hasattr(jobmanager, '_initialization_complete') or not jobmanager._initialization_complete:
        logger.warning("Application initialization was not completed, exiting...")
        return None
        
    return jobmanager
