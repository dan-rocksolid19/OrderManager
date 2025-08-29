#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Popup menu
# Created: 1/29/19
# Copyright (C) 2019, Timothy Hoover


import uno, unohelper
import os


from librepy.pybrex.values import TOOLBAR_GRAPHICS_DIR
from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.menubar import create_key_event
from librepy.pybrex.my_mri import mri

from com.sun.star.awt import XMouseListener, KeyEvent, Point, Rectangle
from com.sun.star.awt.MouseButton import RIGHT as MB_RIGHT, LEFT as MB_LEFT
from com.sun.star.beans import NamedValue, PropertyValue

from com.sun.star.awt import XActionListener, XItemListener, XKeyListener, \
    XMouseListener, XMouseMotionListener, XMenuListener, XWindowListener

import logging
logger = logging.getLogger(__name__)

class MenuItem(object):
    def __init__(self, id, name, cmd = None, style = 0,
        graphic = None, key = None, submenu = None):
        self.id = id
        self.name = name
        self.cmd = cmd
        self.style = style
        self.graphic = graphic
        self.key = key
        self.submenu = submenu

class PopupMenu(object):
    "Class to create and handle popup menus"
    def __init__(self, ctx, parent, menu_items, menu_commands = None):
        self.ctx = ctx
        self.parent = parent
        self.graphics_dir = parent.values.GRAPHICS_DIR
        self.menu_items = menu_items
        self.menu_commands = menu_commands
        self.listener = self.MenuListener(self)
        self.run_fn = None
        self.popup = self.create_popup()
        
        
    def execute(self, run_fn = None, ev = None, pos = None, peer = None, **args):
        "Execute the popup menu"
        self.run_fn = run_fn
        if pos is None:
            #pos = ev.Source.getPosSize()
            pos = Rectangle(ev.X, ev.Y, 0, 0)
        #Execute popup menu
        if peer is None:
            peer = ev.Source.getPeer()
        n = self.popup.execute(peer, pos, 0)
        return n
        
    def run_command(self, cmd, check_state):
        pass
        
    def create_popup(self):
        "Create a popup menu"
        popup = self.parent.create_instance('com.sun.star.awt.PopupMenu')
        self.create_menu_items(popup, self.menu_items)
        return popup

    def create_menu_items(self, parent, menu_items):
        "Recursively create menu items"
        parent.addMenuListener(self.listener)
        ctx = self.ctx
        smgr = ctx.ServiceManager
        for i, menu_item in enumerate(menu_items):
            if menu_item.id is not None:
                #Insert the menu item
                parent.insertItem(menu_item.id, menu_item.name, menu_item.style, i)
                #Set command
                if menu_item.cmd is not None:
                    parent.setCommand(menu_item.id, menu_item.cmd)
                #Set graphic
                if menu_item.graphic is not None:
                    graphic_provider = smgr.createInstanceWithContext('com.sun.star.graphic.GraphicProvider', ctx)
                    g_dir = os.path.join(TOOLBAR_GRAPHICS_DIR, menu_item.graphic)
                    prop_value = PropertyValue()
                    prop_value.Name = 'URL'
                    prop_value.Value = uno.systemPathToFileUrl(g_dir)
                    graphic = graphic_provider.queryGraphic((prop_value, ))
                    parent.setItemImage(menu_item.id, graphic, True)
                if menu_item.key:
                    parent.setAcceleratorKeyEvent(menu_item.id, create_key_event(ctx, smgr, menu_item.key))
                #Recursively create the sub menus
                if menu_item.submenu is not None:
                    sub_popup = self.parent.create_instance('com.sun.star.awt.PopupMenu')
                    self.create_menu_items(sub_popup, menu_item.submenu)
                    #Add the sub popup to the parent popup
                    parent.setPopupMenu(menu_item.id, sub_popup)
            else:
                parent.insertSeparator(i)
                
    def enable_items(self, items, enable, popup = None, hide = False):
        "Recursively enable/disable popup items"
        if popup is None:
            popup = self.popup
        for item in items:
            if isinstance(item, int):
                popup.enableItem(item, enable)
            elif isinstance(item, str):
                item_id = self.get_item_by_command(item)
                if item_id is not None:
                    popup.enableItem(item_id, enable)
            else:
                self.enable_items(item, enable, popup = popup.getPopupMenu(item), hide = hide)
        
        #popup.hideDisabledEntries(hide)
        
    def disable_all_items(self, popup = None, hide = False):
        if popup is None:
            popup = self.popup
        for i in range(popup.getItemCount()):
            popup.enableItem(popup.getItemId(i), False)
        #popup.hideDisabledEntries(hide)
        
    def get_item_by_command(self, cmd):
        for item in self.menu_items:
            if item.cmd == cmd:
                return item.id
        else:
            return None
        
    def hide_disabled_items(self, hide):
        "Show/hide disabled popup items"
        self.popup.hideDisabledEntries(hide)
        
    class MenuListener(unohelper.Base, XMenuListener):
        """ Listener for menubar """
    
        def __init__(self, parent):
            self.parent = parent
            
    
        def disposing(self,ev): pass
        def itemActivated(self, ev): pass
        def itemDeactivated(self, ev): pass
        def itemSelected(self, ev):
            try:
                
                cmd = ev.Source.getCommand(ev.MenuId)
                
                if self.parent.run_fn is not None:
                    self.parent.run_fn(cmd, ev.Source.isItemChecked(ev.MenuId))
                
            except:
                logger.error(traceback.format_exc())
