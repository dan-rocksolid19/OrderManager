'''
An idea in progresss

This could be used for resize.... that would reduce boilerplate code in the __init__.

It could also be used to tie events to the toolbar and menubar.
'''

from enum import Enum
from typing import Any, Callable, Dict, List, Set
#from dataclasses import dataclass
import logging
import traceback

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Enum defining all possible event types"""
    WINDOW_RESIZE = "window_resize"
    WINDOW_CLOSE = "window_close"
    WINDOW_SHOW = "window_show"
    WINDOW_HIDE = "window_hide"
    # Add more event types as needed
    TOOLBAR_UPDATE = "toolbar_update"
    MENUBAR_UPDATE = "menubar_update"
    FRAME_DISPOSE = "frame_dispose"

#@dataclass
class Event:
    """Event data container"""
    type = None
    source = None
    data = None

class EventManager:
    """Centralized event management system"""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure one event manager instance"""
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize event manager if not already initialized"""
        if not self._initialized:
            self._listeners = {
                set() for event_type in EventType
            }
            self._initialized = True
            logger.info("EventManager initialized")
    
    def subscribe(self, event_type, callback):
        """Subscribe to an event type"""
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self._listeners[event_type].add(callback)
        logger.debug("Subscribed to {}: {}".format(event_type.value, callback.__qualname__))
    
    def unsubscribe(self, event_type, callback):
        """Unsubscribe from an event type"""
        try:
            self._listeners[event_type].remove(callback)
            logger.debug("Unsubscribed from {}: {}".format(event_type.value, callback.__qualname__))
        except KeyError:
            logger.warning("Attempted to unsubscribe non-existent listener: {}".format(callback.__qualname__))
    
    def emit(self, event: Event):
        """Emit an event to all subscribers"""
        logger.debug("Emitting event: {}".format(event.type.value))
        for callback in self._listeners[event.type].copy():  # Copy to allow modification during iteration
            try:
                callback(event)
            except Exception as e:
                logger.error("Error in event handler {}: {}".format(callback.__qualname__, e))
                logger.error(traceback.format_exc())

    def clear_all(self):
        """Clear all event subscriptions"""
        for event_type in self._listeners:
            self._listeners[event_type].clear()
        logger.info("All event subscriptions cleared")


# Example usage

#base_frame.py

from librepy.pybrex.events import EventManager, EventType, Event

class BaseFrame:
    def __init__(self, parent, ctx, smgr, title="PyBrex Window", frame_name="pybrex_frame", **kwargs):
        # ... existing init code ...
        
        # Get the singleton event manager instance
        self.event_manager = EventManager()

    def window_resizing(self, width, height):
        """Handle window resize events"""
        # Emit resize event
        self.event_manager.emit(Event(
            type=EventType.WINDOW_RESIZE,
            source=self,
            data={'width': width, 'height': height}
        ))
        
        # Maintain parent notification for backward compatibility
        if self.parent and hasattr(self.parent, 'window_resizing'):
            self.parent.window_resizing(width, height)

    def dispose(self):
        """Clean up window resources"""
        # Emit dispose event before cleanup
        self.event_manager.emit(Event(
            type=EventType.FRAME_DISPOSE,
            source=self
        ))
        # ... rest of dispose code ...


#toolbar.py
from librepy.pybrex.events import EventManager, EventType, Event

class ToolBar(object):
    def __init__(self, parent, ctx, smgr, frame, toolbar_list, **kwargs):
        # ... existing init code ...
        
        # Get event manager instance and subscribe to resize events
        self.event_manager = EventManager()
        self.event_manager.subscribe(EventType.WINDOW_RESIZE, self._handle_resize)
        
    def _handle_resize(self, event: Event) -> None:
        """Handle window resize events"""
        if event.data:
            self.resize(event.data['width'], event.data['height'])
        
    def dispose(self):
        """Dispose of the toolbar"""
        # Unsubscribe from events
        self.event_manager.unsubscribe(EventType.WINDOW_RESIZE, self._handle_resize)
        self.container.dispose()
