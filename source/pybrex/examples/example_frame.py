#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Initialize main application window
# Created: 11-18-21
# Copyright (C) 2021, Timothy Hoover

"""
PyBrex Example Frame Module

This module demonstrates how to create a basic LibreOffice window application using PyBrex.
It provides a template for building windowed applications with menus, toolbars, and basic
window management functionality.

Key Components:
- ExampleWindow: Main window class that creates and manages the application window
- Frame: Handles window creation and event listeners (imported from frame.py)
- Menubar: Provides menu functionality (imported from menubar.py)
- Toolbar: Provides toolbar functionality (imported from toolbar.py)

Example Usage:
    from librepy.pybrex.examples import example_frame
    
    # Create a new window with custom dimensions
    window = example_frame.ExampleWindow(
        getDefaultContext(),
        width=500,
        height=400
    )

Window Features:
- Resizable window with automatic toolbar adjustment
- Menu bar with File and Help menus
- Toolbar with common actions
- Proper window cleanup on close
"""

import traceback
import uno

from librepy.pybrex.examples import frame, menubar, toolbar
from librepy.pybrex.msgbox import msgbox

import logging
logger = logging.getLogger(__name__)


class ExampleWindow(object):
    """
    Main window class that creates and manages a LibreOffice application window.
    
    This class demonstrates the basic structure needed to create a windowed application
    with menus and toolbars using the PyBrex framework.
    
    Attributes:
        ctx (ComponentContext): LibreOffice component context
        smgr (ServiceManager): LibreOffice service manager
        frame (Frame): Window frame object handling window creation and events
        menubar (Menubar): Menu bar object providing application menus
        toolbar (Toolbar): Toolbar object providing button actions
        
    Args:
        ctx (ComponentContext, optional): LibreOffice component context. Defaults to current context.
        **args: Window position and size arguments
            - posx (int): Window X position. Defaults to 100
            - posy (int): Window Y position. Defaults to 100
            - width (int): Window width. Defaults to 400
            - height (int): Window height. Defaults to 400
    """
    
    def __init__(self, ctx=uno.getComponentContext(), **args):
        self.logger = logger
        
        self.ctx = ctx
        self.smgr = ctx.getServiceManager()
        
        # Set position and size of window with defaults
        posx = args['posx'] if 'posx' in args else 100
        posy = args['posy'] if 'posy' in args else 100
        width = args['width'] if 'width' in args else 400
        height = args['height'] if 'height' in args else 400
        
        # Create main frame
        self.frame = frame.Frame(self, self.ctx, self.smgr, 
                               (posx, posy, width, height),
                               title='Example frame',
                               frame_name='example_frame')
        
        # Create menubar and toolbar
        self.menubar = menubar.my_menubar(self, self.ctx, self.smgr, self.frame)
        self.toolbar = toolbar.my_toolbar(self, self.ctx, self.smgr, self.frame)
        
        # Make window visible
        self.frame.window.setVisible(True)
        
    def window_resizing(self, width, height):
        """Handle window resize events by adjusting toolbar dimensions."""
        self.toolbar.resize(width, height)
        
    # Placeholder methods for menu and toolbar actions
    def new_file(self, *args):
        """Create new file. Override this method to implement functionality."""
        pass
        
    def open_file(self, *args):
        """Open existing file. Override this method to implement functionality."""
        pass
        
    def save_file(self, *args):
        """Save current file. Override this method to implement functionality."""
        pass
        
    def settings(self, *args):
        """Show settings dialog. Override this method to implement functionality."""
        pass
        
    def show_about(self, *args):
        """Show about dialog. Override this method to implement functionality."""
        pass
        
    def dispose(self):
        """
        Clean up window resources.
        
        This method ensures proper cleanup of menu bar and toolbar resources
        when the window is closed. The frame handles its own cleanup.
        """
        try:
            self.menubar.dispose()
        except:
            logger.error(traceback.format_exc())
            
        try:
            self.toolbar.dispose()
        except:
            logger.error(traceback.format_exc())

def test():
    
    def tester(**args):
        posx = args['posx'] if 'posx' in args else 100
        print(posx)
            
    tester(posx = 10)
    
def no():
    pass
