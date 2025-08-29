#coding:utf-8
# Author:  Joshua Aguilar, Timothy Hoover
# Purpose: Base frame for creating LibreOffice window applications
# Created: 01.07.2025

import uno
import unohelper
import traceback
from random import randint

from com.sun.star.awt import XActionListener, XItemListener, XKeyListener, \
    XMouseListener, XMouseMotionListener, XMenuListener, XWindowListener
from com.sun.star.document import XEventListener
from com.sun.star.util import XCloseListener
from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.util import CloseVetoException
from com.sun.star.awt import Rectangle
from com.sun.star.beans import NamedValue
from com.sun.star.awt import WindowDescriptor
from com.sun.star.awt.WindowClass import SIMPLE, CONTAINER, TOP, MODALTOP
from com.sun.star.awt.VclWindowPeerAttribute import CLIPCHILDREN, HSCROLL, VSCROLL, AUTOVSCROLL
from com.sun.star.awt.WindowAttribute import BORDER, SHOW

import logging
logger = logging.getLogger(__name__)

class BaseFrame:
    """
    Base class for creating LibreOffice window frames.
    
    This class combines the core functionality from frame.py and example_frame.py
    to provide a simplified way to create window applications.

    Args:
        parent: Parent window instance. Used in several scenarios:
            - Modal dialogs: Set the parent to the window that spawned the dialog
            - Child windows: Set the parent to control window hierarchies
            - Window chains: Enable parent-child communication for events
            Example:
                # Create a settings dialog with main window as parent
                class MainWindow(BaseFrame):
                    def show_settings(self):
                        settings = SettingsDialog(parent=self, ctx=self.ctx, ...)
                        
                class SettingsDialog(BaseFrame):
                    def apply_changes(self):
                        # Access main window through parent
                        self.parent.update_settings(self.new_settings)
        
        ctx (ComponentContext): LibreOffice component context
        smgr (ServiceManager): LibreOffice service manager
        title (str): Window title
        frame_name (str): Base name for the frame
        **kwargs: Window position and size arguments
            - pos (tuple): Window position as (x, y). Defaults to (100, 100)
            - size (tuple): Window size as (width, height). Defaults to (400, 400)
            - menubar_height (int): Height of menubar in pixels. Defaults to 25
            
            Alternative individual arguments:
            - posx (int): Window X position. Defaults to 100
            - posy (int): Window Y position. Defaults to 100
            - width (int): Window width. Defaults to 400
            - height (int): Window height. Defaults to 400
    
    Note:
        The parent parameter is distinct from class inheritance. While your window
        class may inherit from BaseFrame (making BaseFrame the parent class), the
        parent parameter refers to window relationships at runtime. Set parent=None
        for top-level windows.
    """
    
    DEFAULT_MENUBAR_HEIGHT = 25  # Default value
    
    def __init__(self, parent, ctx, smgr, title="PyBrex Window", frame_name="pybrex_frame", ps=(0, 0, 400, 400), **kwargs):
        """Initialize a new BaseFrame window."""
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        
        # Get position and size from ps tuple
        self.posx, self.posy, self.width, self.height = ps

        # Get menubar height from kwargs or use default
        self.menubar_height = kwargs.pop('menubar_height', self.DEFAULT_MENUBAR_HEIGHT)
        
        # Create frame
        self._create_frame(title, frame_name)
        
        # Set up listeners
        self._setup_listeners()
        
    def _create_frame(self, title, frame_name):
        """Creates the window frame with a unique name"""
        # Generate unique frame name
        unique_name = self._get_unique_frame_name(frame_name)
        
        # Create frame
        ps = (self.posx, self.posy, self.width, self.height)
        self.frame = self.smgr.createInstanceWithContext(
            'com.sun.star.frame.TaskCreator', 
            self.ctx
        ).createInstanceWithArguments((
            NamedValue('FrameName', unique_name),
            NamedValue('PosSize', Rectangle(*ps))
        ))
        
        # Get window and set properties
        self.window = self.frame.getContainerWindow()
        desktop = self.smgr.createInstanceWithContext(
            'com.sun.star.frame.Desktop', self.ctx)
        self.frame.setTitle(title)
        self.frame.setCreator(desktop)
        desktop.getFrames().append(self.frame)
        
    def _get_unique_frame_name(self, base_name):
        """Generates a unique frame name to avoid conflicts.
        
        Args:
            base_name (str): Base name for the frame
            
        Returns:
            str: Unique frame name (e.g., 'myapp_main_1234')
        """
        template = "{}_0000".format(base_name)
        desktop = self.smgr.createInstanceWithContext('com.sun.star.frame.Desktop', self.ctx)
        frames = desktop.getFrames()
        existing_names = set()
        
        # Collect existing frame names
        for i in range(frames.getCount()):
            name = frames.getByIndex(i).getName()
            if len(name) == len(template) and name.startswith(base_name):
                existing_names.add(name[-4:])
        
        # Generate unique ID (try up to 10 times)
        for _ in range(10):
            id_str = "{:04d}".format(randint(1000, 9999))
            if id_str not in existing_names:
                return "{}_{}".format(base_name, id_str)
                
        # Fallback with timestamp if all attempts fail
        from time import time
        return "{}_{:04d}".format(base_name, int(time()*1000)%10000)
        
    def _setup_listeners(self):
        """Sets up basic window listeners"""
        self.listeners = {}
        
        # Close listener
        close_listener = BaseFrameCloseListener(self)
        self.frame.addCloseListener(close_listener)
        self.listeners['close'] = close_listener
        
        # Window listener
        window_listener = BaseWindowListener(self)
        self.window.addWindowListener(window_listener)
        self.listeners['window'] = window_listener
        
    def show(self):
        """Makes the window visible"""
        self.window.setVisible(True)
        
    def dispose(self):
        """Cleans up window resources"""
        try:
            # Remove listeners
            for listener_type, listener in self.listeners.items():
                if listener_type == 'window':
                    self.window.removeWindowListener(listener)
                elif listener_type == 'close':
                    self.frame.removeCloseListener(listener)  
        except Exception as e:
            logger.error(traceback.format_exc())

        # Check window size and save geometry if valid
        try:
            ps = self.window.PosSize
            if ps.Width < 50 or ps.Height < 50:
                logger.error("Frame size error!")
            else:
                self.save_window_geometry()  # Call overridable method
        except Exception as e:
            logger.error(traceback.format_exc())
        
        # Dispose parent if it exists and has a dispose method
        if self.parent is not None and hasattr(self.parent, 'dispose') and callable(self.parent.dispose):
            try:
                self.parent.dispose()
            except:
                logger.error(traceback.format_exc())
        
        # Dispose frame
        try:
            self.frame.dispose()
        except:
            logger.error(traceback.format_exc())

    def save_window_geometry(self):
        """Save window geometry for future use.
        
        This method is called during window disposal to save the window's
        position and size. Override this method in subclasses to implement
        custom geometry saving logic.
        
        The window size is validated before calling this method to ensure
        the values are reasonable (width and height > 50px).
        
        Example:
            def save_window_geometry(self):
                ps = self.window.PosSize
                self.settings.window_geometry = {
                    'width': ps.Width,
                    'height': ps.Height,
                    'x': ps.X,
                    'y': ps.Y
                }
        """
        if self.parent:
            if hasattr(self.parent, 'save_window_geometry'):
                self.parent.save_window_geometry()
            else:
                logger.info("Parent has no save_window_geometry method")
        else:
            logger.info("Has no parent")

    def window_resizing(self, width, height):
        """Override this method to handle window resize events"""
        if self.parent:
            if hasattr(self.parent, 'window_resizing'):
                self.parent.window_resizing(width, height)
            else:
                logger.info("Parent has no window_resizing method")
        else:
            logger.info("Has no parent")

    def window_closing(self):
        """Called when the window is about to close.
        
        Override this method in subclasses to perform cleanup or other
        actions before the window closes. This is called after can_close()
        returns True.
        
        By default, this method calls dispose(). When overriding, make sure
        to either call super().window_closing() or self.dispose() to ensure
        proper cleanup.
        
        Example:
            def window_closing(self):
                # Save window position and size
                ps = self.window.PosSize
                self.settings.save_window_geometry(ps.Width, ps.Height, ps.X, ps.Y)
                
                # Call parent to handle disposal
                super().window_closing()
        """
        if self.parent:
            if hasattr(self.parent, 'window_closing'):
                self.parent.window_closing()
            else:
                logger.info("Parent has no window_closing method")
        else:
            logger.info("Has no parent")
        
        self.dispose()

    def can_close(self):
        """Controls whether the window can be closed.
        
        Override this method in subclasses to implement custom closing logic.
        For example, checking for unsaved changes or ongoing operations.
        
        Returns:
            bool: True to allow closing, False to prevent closing
            
        Example:
            def can_close(self):
                if self.has_unsaved_changes:
                    return msgbox.show_yes_no("Save changes?") == "yes"
                return True
        """
        if self.parent:
            if hasattr(self.parent, 'can_close'):
                return self.parent.can_close()
            else:
                logger.info("Parent has no can_close method")
                return True
        else:
            logger.info("Has no parent")
            return True
          # Default behavior: allow closing

    def create_child_window(self, wtype, service, attrs, ps):
        """Creates a child window with specified attributes.
        
        Args:
            wtype (str): Window type ('container', 'splitter', 'dockingwindow', etc.)
            service (WindowClass): Window class service (SIMPLE, CONTAINER, etc.)
            attrs (int): Window attributes bitmask
            ps (tuple): Position and size (x, y, width, height)
            
        Returns:
            Window: Created UNO window instance
        """
        toolkit = self.smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", self.ctx)
        descriptor = WindowDescriptor()
        descriptor.Type = service
        descriptor.WindowServiceName = wtype
        descriptor.Parent = self.window
        descriptor.ParentIndex = 1
        descriptor.Bounds = Rectangle(*ps)
        descriptor.WindowAttributes = attrs
        return toolkit.createWindow(descriptor)

    def create_vertical_splitter(self, ps, listener=None, **kwargs):
        """Creates a vertical splitter for resizing adjacent panes.
        
        Args:
            ps (tuple): Position and size (x, y, width, height)
            listener (MouseListener, optional): Custom drag behavior
            **kwargs: Optional splitter properties
                - background_color (int): RGB color value. Defaults to 0xDCDAD5
                - border (int): Border width. Defaults to 0
                - text (str): Splitter text. Defaults to '....'
            
        Returns:
            Window: Configured vertical splitter
        """
        spl = self.create_child_window(
            'splitter', 
            SIMPLE,
            CLIPCHILDREN | BORDER | SHOW | HSCROLL,
            ps
        )
        self._configure_splitter(spl, True, listener, **kwargs)  # True = vertical
        return spl

    def create_horizontal_splitter(self, ps, listener=None, **kwargs):
        """Creates a horizontal splitter for resizing adjacent panes.
        
        Args:
            ps (tuple): Position and size (x, y, width, height)
            listener (MouseListener, optional): Custom drag behavior
            **kwargs: Optional splitter properties
                - background_color (int): RGB color value. Defaults to 0xDCDAD5
                - border (int): Border width. Defaults to 0
                - text (str): Splitter text. Defaults to '....'
        """
        spl = self.create_child_window(
            'splitter',
            SIMPLE,
            CLIPCHILDREN | BORDER | SHOW | VSCROLL,
            ps
        )
        self._configure_splitter(spl, False, listener, **kwargs)  # False = horizontal
        return spl

    def _configure_splitter(self, splitter, is_vertical, listener, **kwargs):
        """Configure common splitter properties.
        
        Args:
            splitter: Splitter window to configure
            is_vertical: True for vertical orientation, False for horizontal
            listener: Optional mouse listener
            **kwargs: Optional property overrides
        """
        splitter.setProperty('BackgroundColor', 
            kwargs.get('background_color', 0xDCDAD5))
        splitter.setProperty('Border',
            kwargs.get('border', 0))
        splitter.setProperty('Text',
            kwargs.get('text', '....'))
        splitter.setProperty('FontOrientation',
            2 if is_vertical else 1)  # 2=vertical, 1=horizontal
        
        if listener:
            splitter.addMouseListener(listener)
            splitter.addMouseMotionListener(listener)

    def embed_document(self, ps, props=None, doc_type='sdraw'):
        """Embeds a LibreOffice document in the window.
        
        Args:
            ps (tuple): Position and size (x, y, width, height)
            props (list, optional): Document properties
            doc_type (str): Document type ('sdraw', 'scalc', 'swriter', etc.)
            
        Returns:
            tuple: (window, document)
        """
        props = props or []
        
        # Create document window
        doc_window = self.create_child_window(
            'dockingwindow',
            SIMPLE,
            CLIPCHILDREN | BORDER | SHOW,
            ps
        )
        
        # Create and initialize frame
        doc_frame = self.smgr.createInstanceWithContext("com.sun.star.frame.Frame", self.ctx)
        doc_frame.initialize(doc_window)
        
        # Load document
        doc = doc_frame.loadComponentFromURL(
            'private:factory/{}'.format(doc_type),
            "_self",
            0,
            tuple(props)
        )
        
        return doc_window, doc

    

# Listener classes
class BaseFrameCloseListener(unohelper.Base, XCloseListener):
    """Window closing"""
    def __init__(self, parent):
        self.parent = parent
    
    def queryClosing(self, event, owner):
        """Window close querying"""
        b_close = True
        try:
            b_close = self.parent.can_close()
        except Exception as e:
            logger.error(traceback.format_exc())
        
        if not b_close:
            logger.debug('Vetoing close')
            raise CloseVetoException() 
        
    def notifyClosing(self, event):
        try:
            # Only call window_closing, it will handle dispose
            self.parent.window_closing()
        except Exception as e:
            logger.error(traceback.format_exc())
        
    def disposing(self, event):
        logger.debug('Close disposing')

class BaseWindowListener(unohelper.Base, XWindowListener):
    """Window listener for the BaseFrame class"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def disposing(self, event):
        self.parent = None
        
    def windowResized(self, ev):
        """Called when the window is resized"""
        if self.parent:
            ps = self.parent.window.PosSize
            self.parent.window_resizing(ps.Width, ps.Height)
            
    def windowMoved(self, event):
        pass
        
    def windowShown(self, event):
        pass
        
    def windowHidden(self, event):
        pass