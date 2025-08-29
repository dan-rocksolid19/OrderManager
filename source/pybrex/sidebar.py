#coding:utf-8
# Author: Josiah Aguilar
# Purpose: Reusable Sidebar class
# Created: 2025

import uno
import unohelper
import os
import traceback

import librepy.pybrex.ctr_container as ctr_container
from librepy.pybrex.values import SIDEBAR_GRAPHICS_DIR
from librepy.pybrex.listeners import Listeners

from com.sun.star.awt import PosSize
from com.sun.star.awt import XMouseListener
from com.sun.star.style.VerticalAlignment import MIDDLE as VA_MIDDLE

class Sidebar(object):
    """Reusable sidebar class for creating collapsible sidebars with buttons"""
    """You will need open-sidebar.png and close-sidebar.png in the toolbar graphics directory"""
     
    def __init__(self, parent, ctx, smgr, frame, sidebar_items, **kwargs):
        """Initialize the sidebar
        
        Args:
            parent: Parent window/frame
            ctx: UNO context
            smgr: Service manager
            frame: Frame to attach sidebar to
            sidebar_items: List of sidebar items in format:
                [
                    ('Button', 'Label', 'icon.png', callback_function, 'Help text'),
                    ('Separator',),
                    ('Button', 'Label2', 'icon2.png', callback_function2, 'Help text2'),
                ]
            **kwargs: Configuration overrides
        """
        self.logger = getattr(parent, 'logger', None)
        if self.logger:
            self.logger.info("Sidebar initialized")
        
        # Default configuration
        self.config = {
            'width': 64,  # Collapsed width
            'expanded_width': 150,  # Expanded width
            'fixed_padding': 8,  # Padding to subtract from visible width
            'min_height': 400,  # Minimum sidebar height
            'title': 'App',  # Title when collapsed
            'expanded_title': 'Application',  # Title when expanded
            'position': 'left',  # 'left' or 'right'
            'auto_expand': False,  # Disabled auto expand functionality
            'default_state': 'closed',  # Default to closed state
            'colors': {
                'background': 0x357399,  # Changed to requested color
                'selected': 0x2D6280,    # Darker shade for selected state
                'hover': 0x3A7FA6,       # Lighter shade for hover state
                'text': 0xFFFFFF,        # Normal text color (white)
                'text_selected': 0xFFFFFF,  # Selected text color (white)
                'text_hover': 0xFFFFFF,  # Hover text color (white)
                'title_text': 0xFFFFFF   # Title text color (white)
            },
            'button': {
                'width': 40,
                'height': 30,
                'spacing': 40,  # Vertical spacing between buttons
                'start_y': 50,  # Y position of first button
                'start_x': 10   # X position of buttons
            },
            'title_config': {
                'x': 10,
                'y': 10,
                'width': 40,
                'height': 30,
                'font_size': 16,
                'font_weight': 150,
                'font_name': 'Times New Roman'
            },
            'toggle_button': {
                'width': 40,
                'height': 30,
                'margin_bottom': 10  # Distance from bottom of sidebar
            }
        }
        
        # Update config with provided kwargs
        self.config.update(kwargs)
        
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.sidebar_items = sidebar_items
        
        # State variables - default to closed
        self.width = self.config['width']
        self.expanded_width = self.config['expanded_width']
        self.is_expanded = (self.config['default_state'] == 'expanded')
        self.current_button = None
        self.current_label = None
        self.hovered_button = None
        self.hovered_label = None
        
        # Storage for controls
        self.labels = []
        self.buttons = []
        self.separators = []
        self.toggle_button = None
        
        # Initialize listeners
        self.listeners = Listeners()
        
        # Get frame dimensions
        frame_size = frame.window.getPosSize()
        self.frame_height = frame_size.Height
        self.frame_width = frame_size.Width
        
        # Calculate sidebar height
        sidebar_height = max(self.frame_height, self.config['min_height'])
        self._load_icons_to_memory()
        # Create the main sidebar container
        self._create_sidebar_container(sidebar_height)
        
        # Add controls
        self._add_controls()
        
        # Set initial state
        if not self.is_expanded:
            self._set_collapsed_state()
        else:
            self._set_expanded_state()
        
        if self.logger:
            self.logger.info("Sidebar creation complete")

        self._update_toggle_button_icon()

    def _create_sidebar_container(self, height):
        """Create the main sidebar container"""
        if self.config['position'] == 'left':
            x_pos = 0
        else:
            x_pos = self.frame_width - self.width
            
        container_pos = (x_pos, 0, self.width - self.config['fixed_padding'], height)
        self.sidebar_container = ctr_container.create_container(self.ctx, self.smgr, self.frame.window, container_pos)
        self.sidebar_container.Model.BackgroundColor = self.config['colors']['background']
        
        # Add mouse listener to container for selection toggling
        self.sidebar_container.addMouseListener(self.ContainerMouseListener(self))
    
    def _add_controls(self):
        """Add all controls to the sidebar"""
        self._add_title()
        self._add_items()
        self._add_toggle_button()
    
    def _add_title(self):
        """Add title label to sidebar"""
        title_config = self.config['title_config']
        initial_title = self.config['expanded_title'] if self.is_expanded else self.config['title']
        self.title_control = ctr_container.create_control(
            self.ctx,
            self.smgr,
            'FixedText',
            title_config['x'], 
            title_config['y'],
            title_config['width'], 
            title_config['height'],
            Label=initial_title,
            FontHeight=title_config['font_size'],
            FontWeight=title_config['font_weight'],
            FontName=title_config['font_name'],
            BackgroundColor=self.config['colors']['background'],
            TextColor=self.config['colors']['title_text']
        )
        self.sidebar_container.addControl('title_label', self.title_control)
    
    def _add_items(self):
        """Add sidebar items (buttons, separators, etc.)"""
        current_y = self.config['button']['start_y']
        
        for i, item in enumerate(self.sidebar_items):
            if item[0] == 'Button':
                self._create_button_item(item, current_y, i)
                current_y += self.config['button']['spacing']
            elif item[0] == 'Separator':
                self._create_separator(current_y, i)
                current_y += 20  # Separator spacing
    
    def _add_toggle_button(self):
        """Add toggle button at the bottom of the sidebar"""
        # Calculate position at bottom of sidebar
        sidebar_height = max(self.frame_height, self.config['min_height'])
        toggle_y = sidebar_height - self.config['toggle_button']['height'] - self.config['toggle_button']['margin_bottom']
        
        # Pre-load both icon URLs to avoid path resolution during runtime
        # Copy icons to permanent location since document may be closed
        self.open_sidebar_icon_url = self._copy_icon_to_permanent_location('open-sidebar.png')
        self.close_sidebar_icon_url = self._copy_icon_to_permanent_location('close-sidebar.png')
        
        # Choose initial icon based on current state
        initial_icon_url = self.open_sidebar_icon_url if not self.is_expanded else self.close_sidebar_icon_url
        
        self.toggle_button = ctr_container.create_control(
            self.ctx,
            self.smgr,
            'ImageControl',
            self.config['button']['start_x'],
            toggle_y,
            self.config['toggle_button']['width'],
            self.config['toggle_button']['height'],
            ImageURL=initial_icon_url,
            ScaleImage=True,
            BackgroundColor=self.config['colors']['background'],
            HelpText='Toggle sidebar',
            Border=0
        )
        
        # Add click listener to toggle button
        self.listeners.add_mouse_listener(self.toggle_button,
            lambda ev: self._handle_toggle_click(ev),
            None, None, None)
        
        self.sidebar_container.addControl('toggle_button', self.toggle_button)
    
    def _create_button_item(self, item, y_pos, index):
        """Create a button item with icon and label
        
        Args:
            item: Tuple containing ('Button', label, icon, callback, help_text)
            y_pos: Y position for the button
            index: Index for unique naming
        """
        _, label, icon, callback, help_text = item
        
        button_config = self.config['button']
        
        # Create icon button
        icon_url = uno.systemPathToFileUrl(os.path.join(SIDEBAR_GRAPHICS_DIR, icon))
        image_btn = ctr_container.create_control(
            self.ctx,
            self.smgr,
            'ImageControl',
            button_config['start_x'], 
            y_pos,
            button_config['width'], 
            button_config['height'],
            ImageURL=icon_url,
            ScaleImage=True,
            BackgroundColor=self.config['colors']['background'],
            HelpText=help_text,
            Border=0
        )
        
        # Create label (initially hidden if collapsed)
        label_control = ctr_container.create_control(
            self.ctx,
            self.smgr,
            'FixedText',
            button_config['start_x'] + button_config['width'] + 5,
            y_pos + 8,
            85,
            20,
            Label=label,
            FontHeight=12,
            VerticalAlign=VA_MIDDLE,
            BackgroundColor=self.config['colors']['background'],
            TextColor=self.config['colors']['text'],
            HelpText=help_text
        )
        
        # Store references
        self.labels.append(label_control)
        self.buttons.append((image_btn, label_control, callback))
        
        # Add to container
        button_name = f'button_{index}'
        label_name = f'label_{index}'
        self.sidebar_container.addControl(button_name, image_btn)
        self.sidebar_container.addControl(label_name, label_control)
        
        # Add event listeners
        self._add_button_listeners(image_btn, label_control, callback)
    
    def _create_separator(self, y_pos, index):
        """Create a separator line"""
        separator = ctr_container.create_control(
            self.ctx,
            self.smgr,
            'FixedLine',
            self.config['button']['start_x'],
            y_pos,
            self.width - self.config['fixed_padding'] - 20,
            2,
            BackgroundColor=self.config['colors']['selected']
        )
        
        self.separators.append(separator)
        separator_name = f'separator_{index}'
        self.sidebar_container.addControl(separator_name, separator)
    
    def _add_button_listeners(self, button, label, callback):
        """Add click and hover listeners to button and label"""
        # Click listeners - these will execute the callback, not toggle sidebar
        self.listeners.add_mouse_listener(button, 
            lambda ev: self._handle_button_click(ev, button, label, callback), 
            None, None, None)
        self.listeners.add_mouse_listener(label,
            lambda ev: self._handle_button_click(ev, button, label, callback),
            None, None, None)
        
        # Hover listeners for visual feedback - add proper enter/exit listeners
        button_hover_listener = self.ButtonHoverListener(self, button, label)
        button.addMouseListener(button_hover_listener)
        
        label_hover_listener = self.ButtonHoverListener(self, button, label)
        label.addMouseListener(label_hover_listener)
    
    def _handle_toggle_click(self, ev):
        """Handle toggle button click"""
        if ev.Buttons == 1:  # Left mouse button
            self.toggle()
    
    def _handle_button_click(self, ev, button, label, callback):
        """Handle button click events"""
        if ev.Buttons == 1:  # Left mouse button
            # Reset previous selection
            if self.current_button:
                self.current_button.Model.BackgroundColor = self.config['colors']['background']
            if self.current_label:
                self.current_label.Model.BackgroundColor = self.config['colors']['background']
                self.current_label.Model.TextColor = self.config['colors']['text']
            
            # Set new selection
            self.current_button = button
            self.current_label = label
            button.Model.BackgroundColor = self.config['colors']['selected']
            label.Model.BackgroundColor = self.config['colors']['selected']
            label.Model.TextColor = self.config['colors']['text_selected']
            
            # Execute callback
            try:
                if callable(callback):
                    callback()
                elif hasattr(self.parent, callback):
                    fn = getattr(self.parent, callback)
                    if callable(fn):
                        fn()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error executing callback {callback}: {str(e)}")
                    self.logger.error(traceback.format_exc())
    
    def _handle_button_hover(self, ev, button, label):
        """Handle button hover events - deprecated, using proper mouse listeners now"""        
        pass
    
    def toggle(self):
        """Toggle sidebar open/closed state"""
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
        self.parent.window_resizing(self.frame_width, self.frame_height)
    
    def expand(self):
        """Expand the sidebar"""
        if not self.is_expanded:
            old_width = self.width
            self.is_expanded = True
            self.width = self.expanded_width
            self._set_expanded_state()
            self._resize_container()
            self._update_toggle_button_icon()
            # Ensure selected state is maintained
            self._restore_selection_colors()

    def collapse(self):
        """Collapse the sidebar"""
        if self.is_expanded:
            old_width = self.width
            self.is_expanded = False
            self.width = self.config['width']
            self._set_collapsed_state()
            self._resize_container()
            self._update_toggle_button_icon()
            # Ensure selected state is maintained
            self._restore_selection_colors()
    
    def _set_expanded_state(self):
        """Set controls for expanded state"""
        # Show labels
        for label in self.labels:
            label.setVisible(True)
        
        # Update title
        self.title_control.Model.Label = self.config['expanded_title']
        self.title_control.setPosSize(
            self.config['title_config']['x'],
            self.config['title_config']['y'],
            self.expanded_width - 20,
            self.config['title_config']['height'],
            PosSize.SIZE
        )
    
    def _set_collapsed_state(self):
        """Set controls for collapsed state"""
        # Hide labels
        for label in self.labels:
            label.setVisible(False)
        
        # Update title
        self.title_control.Model.Label = self.config['title']
        self.title_control.setPosSize(
            self.config['title_config']['x'],
            self.config['title_config']['y'],
            self.config['title_config']['width'],
            self.config['title_config']['height'],
            PosSize.SIZE
        )
    
    def _restore_selection_colors(self):
        """Restore selection colors after expand/collapse"""
        if self.current_button:
            self.current_button.Model.BackgroundColor = self.config['colors']['selected']
        if self.current_label:
            self.current_label.Model.BackgroundColor = self.config['colors']['selected']
            self.current_label.Model.TextColor = self.config['colors']['text_selected']
    
    def _update_toggle_button_icon(self):
        """Update the toggle button icon using in-memory graphics"""
        if self.toggle_button:
            try:
                if self.is_expanded:
                    # Try setting graphic directly first
                    if hasattr(self.toggle_button.Model, 'Graphic'):
                        self.toggle_button.Model.Graphic = self.close_sidebar_graphic
                    else:
                        # Fallback to URL approach
                        temp_url = self._create_url_from_graphic(self.close_sidebar_graphic)
                        self.toggle_button.Model.ImageURL = temp_url
                else:
                    if hasattr(self.toggle_button.Model, 'Graphic'):
                        self.toggle_button.Model.Graphic = self.open_sidebar_graphic
                    else:
                        temp_url = self._create_url_from_graphic(self.open_sidebar_graphic)
                        self.toggle_button.Model.ImageURL = temp_url
                    
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error updating icon: {str(e)}")
    
    def _resize_container(self):
        """Resize the sidebar container"""
        if self.config['position'] == 'left':
            x_pos = 0
        else:
            x_pos = self.frame_width - self.width
            
        sidebar_height = max(self.frame_height, self.config['min_height'])
        self.sidebar_container.setPosSize(
            x_pos, 0, 
            self.width - self.config['fixed_padding'], 
            sidebar_height, 
            PosSize.POSSIZE
        )
        
        # Update toggle button position if needed
        if self.toggle_button:
            toggle_y = sidebar_height - self.config['toggle_button']['height'] - self.config['toggle_button']['margin_bottom']
            self.toggle_button.setPosSize(
                self.config['button']['start_x'],
                toggle_y,
                self.config['toggle_button']['width'],
                self.config['toggle_button']['height'],
                PosSize.POSSIZE
            )
    
    def resize(self, width, height):
        """Handle parent window resize"""
        self.frame_width = width
        self.frame_height = height
        self._resize_container()
    
    def get_width(self):
        """Get current sidebar width"""
        return self.width
    
    def _copy_icon_to_permanent_location(self, icon_filename):
        """Copy icon from document to a permanent location
        
        Args:
            icon_filename: Name of the icon file (e.g., 'open-sidebar.png')
            
        Returns:
            file:// URL of the copied icon
        """
        import tempfile
        import shutil
        
        try:
            # Get source path (from document)
            source_path = os.path.join(SIDEBAR_GRAPHICS_DIR, icon_filename)
            
            # Create permanent directory in temp folder
            temp_dir = os.path.join(tempfile.gettempdir(), '.librepy_sidebar_icons')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Destination path
            dest_path = os.path.join(temp_dir, icon_filename)
            
            # Copy file if source exists and destination doesn't exist or is older
            if os.path.exists(source_path):
                if not os.path.exists(dest_path) or os.path.getmtime(source_path) > os.path.getmtime(dest_path):
                    shutil.copy2(source_path, dest_path)
                    if self.logger:
                        self.logger.debug(f"Copied icon {icon_filename} to {dest_path}")
                
                # Return file:// URL
                return uno.systemPathToFileUrl(dest_path)
            else:
                if self.logger:
                    self.logger.warning(f"Source icon not found: {source_path}")
                return ""
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error copying icon {icon_filename}: {str(e)}")
            return ""
    
    def set_selected_button(self, button_index):
        """Programmatically select a button by index"""
        if 0 <= button_index < len(self.buttons):
            button, label, callback = self.buttons[button_index]
            
            # Reset previous selection
            if self.current_button:
                self.current_button.Model.BackgroundColor = self.config['colors']['background']
            if self.current_label:
                self.current_label.Model.BackgroundColor = self.config['colors']['background']
                self.current_label.Model.TextColor = self.config['colors']['text']
            
            # Set new selection
            self.current_button = button
            self.current_label = label
            button.Model.BackgroundColor = self.config['colors']['selected']
            label.Model.BackgroundColor = self.config['colors']['selected']
            label.Model.TextColor = self.config['colors']['text_selected']
    
    def dispose(self):
        """Clean up resources"""
        if hasattr(self, 'sidebar_container'):
            self.sidebar_container.dispose()
        if hasattr(self, 'listeners'):
            self.listeners.dispose()

    def _load_icons_to_memory(self):
        """Load icons as in-memory graphics before document closes"""
        try:
            # Get GraphicProvider service
            graphic_provider = self.ctx.getServiceManager().createInstanceWithContext(
                "com.sun.star.graphic.GraphicProvider", self.ctx)
            
            # Load graphics from document
            open_icon_path = os.path.join(SIDEBAR_GRAPHICS_DIR, 'open-sidebar.png')
            close_icon_path = os.path.join(SIDEBAR_GRAPHICS_DIR, 'close-sidebar.png')
            
            # Create property arrays for loading
            open_props = (uno.createUnoStruct("com.sun.star.beans.PropertyValue", "URL", 0, 
                          uno.systemPathToFileUrl(open_icon_path), 0),)
            close_props = (uno.createUnoStruct("com.sun.star.beans.PropertyValue", "URL", 0, 
                           uno.systemPathToFileUrl(close_icon_path), 0),)
            
            # Load as graphics
            self.open_sidebar_graphic = graphic_provider.queryGraphic(open_props)
            self.close_sidebar_graphic = graphic_provider.queryGraphic(close_props)
            self.logger.info(f"Icons loaded to memory")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading icons to memory: {str(e)}")
            return False

    def _create_url_from_graphic(self, graphic):
        """Create a temporary URL from a graphic object"""
        try:
            # Create a temporary graphic object URL
            graphic_provider = self.ctx.getServiceManager().createInstanceWithContext(
                "com.sun.star.graphic.GraphicProvider", self.ctx)
            
            # This creates a temporary internal URL for the graphic
            return graphic_provider.getGraphicDescriptor(graphic).URL
        except:
            return ""

    class ContainerMouseListener(unohelper.Base, XMouseListener):
        """Mouse listener for sidebar container to handle selection toggling"""
        
        def __init__(self, sidebar):
            self.sidebar = sidebar
        
        def mousePressed(self, ev):
            if ev.Buttons == 1:  # Left mouse button
                # Toggle current selection off if clicking on empty space
                if self.sidebar.current_button:
                    self.sidebar.current_button.Model.BackgroundColor = self.sidebar.config['colors']['background']
                    self.sidebar.current_button = None
                if self.sidebar.current_label:
                    self.sidebar.current_label.Model.BackgroundColor = self.sidebar.config['colors']['background']
                    self.sidebar.current_label = None
        
        def mouseReleased(self, ev): pass
        def mouseEntered(self, ev): pass
        def mouseExited(self, ev): pass
        def disposing(self, ev): pass

    class ButtonHoverListener(unohelper.Base, XMouseListener):
        """Mouse listener for button hover"""
        
        def __init__(self, sidebar, button, label):
            self.sidebar = sidebar
            self.button = button
            self.label = label
        
        def mousePressed(self, ev): pass
        def mouseReleased(self, ev): pass
        def mouseEntered(self, ev):
            # Reset previous hover to proper state
            if self.sidebar.hovered_button and self.sidebar.hovered_button != self.button:
                # Check if previous hovered button is the selected button
                if self.sidebar.hovered_button == self.sidebar.current_button:
                    # Restore to selected color
                    self.sidebar.hovered_button.Model.BackgroundColor = self.sidebar.config['colors']['selected']
                else:
                    # Restore to background color
                    self.sidebar.hovered_button.Model.BackgroundColor = self.sidebar.config['colors']['background']
            
            if self.sidebar.hovered_label and self.sidebar.hovered_label != self.label:
                # Check if previous hovered label is the selected label
                if self.sidebar.hovered_label == self.sidebar.current_label:
                    # Restore to selected color
                    self.sidebar.hovered_label.Model.BackgroundColor = self.sidebar.config['colors']['selected']
                    self.sidebar.hovered_label.Model.TextColor = self.sidebar.config['colors']['text_selected']
                else:
                    # Restore to background color
                    self.sidebar.hovered_label.Model.BackgroundColor = self.sidebar.config['colors']['background']
                    self.sidebar.hovered_label.Model.TextColor = self.sidebar.config['colors']['text']
            
            # Set new hover (only if not currently selected)
            if self.button != self.sidebar.current_button:
                self.sidebar.hovered_button = self.button
                self.sidebar.hovered_label = self.label
                self.button.Model.BackgroundColor = self.sidebar.config['colors']['hover']
                self.label.Model.BackgroundColor = self.sidebar.config['colors']['hover']
                self.label.Model.TextColor = self.sidebar.config['colors']['text_hover']
        
        def mouseExited(self, ev):
            if self.button == self.sidebar.hovered_button:
                # Check if this button is the selected button
                if self.button == self.sidebar.current_button:
                    # Keep selected color
                    self.button.Model.BackgroundColor = self.sidebar.config['colors']['selected']
                    self.label.Model.BackgroundColor = self.sidebar.config['colors']['selected']
                    self.label.Model.TextColor = self.sidebar.config['colors']['text_selected']
                else:
                    # Reset to background color
                    self.button.Model.BackgroundColor = self.sidebar.config['colors']['background']
                    self.label.Model.BackgroundColor = self.sidebar.config['colors']['background']
                    self.label.Model.TextColor = self.sidebar.config['colors']['text']
                
                self.sidebar.hovered_button = None
                self.sidebar.hovered_label = None
        
        def disposing(self, ev): pass


def create_sidebar(parent, ctx, smgr, frame, sidebar_items, **kwargs):
    """Convenience function to create a sidebar
    
    Args:
        parent: Parent object
        ctx: UNO context
        smgr: Service manager
        frame: Frame to attach to
        sidebar_items: List of sidebar items
        **kwargs: Configuration options
    
    Returns:
        Sidebar instance
    """
    return Sidebar(parent, ctx, smgr, frame, sidebar_items, **kwargs)
