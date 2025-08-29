#coding:utf-8
# Author:  Joshua Aguilar, Timothy Hoover
# Purpose: Frame manager for the contact list application
# Created: 01.07.2025

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
import uno

from librepy.pybrex import base_frame
from librepy.utils.window_geometry_config_manager import WindowGeometryConfigManager


class FrameManager(object):
    '''Frame manager for the contact list application'''
    
    def __init__(self, parent, ctx, smgr, ps, **kwargs):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.logger = parent.logger
        self.logger.info("FrameManager initialized")

        self._geometry_manager = None

        # Create the base frame with this manager as the parent
        self.base_frame = base_frame.BaseFrame(
            parent=self,
            ctx=ctx,
            smgr=smgr,
            title="Order Manager",
            frame_name="jobmanager_frame",
            ps=ps,
            **kwargs
        )
        
        self.base_frame.show()

    @property
    def geometry_manager(self):
        """Lazy initialization of geometry config manager"""
        if self._geometry_manager is None:
            self._geometry_manager = WindowGeometryConfigManager()
        return self._geometry_manager

    @property
    def window(self):
        """Access to the underlying window"""
        return self.base_frame.window
    
    @property
    def frame(self):
        """Access to the underlying frame"""
        return self.base_frame.frame

    def window_resizing(self, width, height):
        """Handle window resize events"""
        self.parent.window_resizing(width, height)
    
    def can_close(self):
        """Handle window close request"""
        self.logger.info("Window close request received")
        return True
    
    def save_window_geometry(self):
        """Save window position and size"""
        try:
            if self.window:
                pos_size = self.window.getPosSize()
                geometry = (pos_size.X, pos_size.Y, pos_size.Width, pos_size.Height)
                
                if self.geometry_manager.is_geometry_valid_for_screen(geometry):
                    success = self.geometry_manager.save_geometry(geometry)
                    if success:
                        self.logger.info(f"Window geometry saved: {geometry}")
                    else:
                        self.logger.warning("Failed to save window geometry")
                else:
                    self.logger.warning(f"Invalid geometry not saved: {geometry}")
            else:
                self.logger.warning("Cannot save geometry: window not available")
        except Exception as e:
            self.logger.error(f"Error saving window geometry: {e}")
            self.logger.error(traceback.format_exc())

    def window_closing(self):
        """Handle window close event"""
        self.save_window_geometry()

    def dispose(self):
        """Clean up window resources"""
        try:
            self.logger.info("Cleaning up FrameManager resources...")

            if hasattr(self, 'sidebar_manager'):
                self.sidebar_manager.dispose()
                delattr(self, 'sidebar_manager')

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.logger.error(traceback.format_exc())
