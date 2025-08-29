#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Menubar for main application window
# Created: 02.10.2018
# Copyright (C) 2018, Timothy Hoover

import uno, unohelper
import traceback
import os
from collections import namedtuple


from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.my_mri import mri
from librepy.pybrex.values import TOOLBAR_GRAPHICS_DIR

from com.sun.star.beans import NamedValue, PropertyValue
from com.sun.star.awt.MenuItemStyle import CHECKABLE as CHK, AUTOCHECK as ACHK, RADIOCHECK as RCHK
from com.sun.star.awt import XMenuListener


import logging
logger = logging.getLogger(__name__)

class Menu(object):
    def __init__(self, id, name, cmd = None, submenu = None):
        self.id = id
        self.name = name
        self.cmd = cmd
        self.submenu = submenu

class SubMenu(object):
    def __init__(self, id, name, cmd = None, style = 0,
        graphic = None, key = None, submenu = None):
        self.id = id
        self.name = name
        self.cmd = cmd
        self.style = style
        self.graphic = graphic
        self.key = key
        self.submenu = submenu
    
def create_menubar(window, ctx, smgr, menus, listener):
    '''Create and set the menubar to the main window'''
    menubar = smgr.createInstanceWithContext('com.sun.star.awt.MenuBar',ctx)
    menubar.addMenuListener(listener)
    menubar.removeItem(0,menubar.getItemCount())
    for i, menu in enumerate(menus):
        #Set top level menu entries
        menubar.insertItem(menu.id, menu.name, 0, i)
        #if menu.cmd:
        #    menubar.setCommand(menu.id, menu.cmd)
        #if menu.key:
        #    menubar.setAcceleratorKeyEvent(menu.id, menu.key)
        if menu.submenu:
            create_submenu(menubar, menu.id, menu.submenu, ctx, smgr, listener)
    #mri(menubar)
    window.setMenuBar(menubar)
    return menubar
    
def create_submenu(parentmenu, menuid, submenu, ctx, smgr, listener):
    '''Create a popupmenu and add it the parent menu'''
    ppm = smgr.createInstanceWithContext('com.sun.star.awt.PopupMenu',ctx)
    ppm.addMenuListener(listener)
    for i, menu in enumerate(submenu):
        if not menu.id is None:
            ppm.insertItem(menu.id, menu.name, menu.style, i)
            if menu.cmd:
                ppm.setCommand(menu.id, menu.cmd)
            if menu.key:
                ppm.setAcceleratorKeyEvent(menu.id, create_key_event(ctx, smgr, menu.key))
            #Set graphic
            if menu.graphic is not None:
                graphic_provider = smgr.createInstanceWithContext('com.sun.star.graphic.GraphicProvider', ctx)
                g_dir = os.path.join(TOOLBAR_GRAPHICS_DIR, menu.graphic)
                
                prop_value = PropertyValue()
                prop_value.Name = 'URL'
                prop_value.Value = uno.systemPathToFileUrl(g_dir)
                graphic = graphic_provider.queryGraphic((prop_value, ))
                ppm.setItemImage(menu.id, graphic, True)
            if menu.submenu:
                create_submenu(ppm, menu.id, menu.submenu, ctx, smgr, listener)
        else:
            ppm.insertSeparator(i)
    parentmenu.setPopupMenu(menuid, ppm)
    
def remove_listeners(popup_menu, menus, listener):
    #Remove all listeners from a menubar
    popup_menu.removeMenuListener(listener)
    for i, menu in enumerate(menus):
        if menu.submenu:
            #Recursively remove menu listeners
            ppm = popup_menu.getPopupMenu(menu.id)
            remove_listeners(ppm, menu.submenu, listener)

class Menubar(object):
    '''Menubar for kp application window'''
    def __init__(self, parent, ctx, smgr, frame, menulist, menu_functions):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.menulist = menulist
        self.menu_functions = menu_functions
        self.menu_listener = self.MenuListener(self)
        self.menubar = create_menubar(frame.window, ctx, smgr, self.menulist, self.menu_listener)
        
    
    def dispose(self):
        '''Dispose'''
        remove_listeners(self.menubar, self.menulist, self.menu_listener)
        self.frame.window.setMenuBar(None)
        
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
                fn = self.parent.menu_functions[cmd]
                if fn:
                    fn(cmd, ev.Source.isItemChecked(ev.MenuId))
            except:
                logger.error(traceback.format_exc())
                

def key_map():
    km = {}
    km['0'] = 256
    km['1'] = 257
    km['2'] = 258
    km['3'] = 259
    km['4'] = 260
    km['5'] = 261
    km['6'] = 262
    km['7'] = 263
    km['8'] = 264
    km['9'] = 265
    km['A'] = 512
    km['B'] = 513
    km['C'] = 514
    km['D'] = 515
    km['E'] = 516
    km['F'] = 517
    km['G'] = 518
    km['H'] = 519
    km['I'] = 520
    km['J'] = 521
    km['K'] = 522
    km['L'] = 523
    km['M'] = 524
    km['N'] = 525
    km['O'] = 526
    km['P'] = 527
    km['Q'] = 528
    km['R'] = 529
    km['S'] = 530
    km['T'] = 531
    km['U'] = 532
    km['V'] = 533
    km['W'] = 534
    km['X'] = 535
    km['Y'] = 536
    km['Z'] = 537
    km['<'] = 1293
    km['>'] = 1294
    km['{'] = 1315
    km['}'] = 1316
    return km

def create_key_event(ctx, smgr, key):
    'Create a key event for the menubar'
    kv = uno.createUnoStruct('com.sun.star.awt.KeyEvent')
    km = key_map()
    #kv = smgr.createInstanceWithContext('com.sun.star.awt.KeyEvent', ctx)
    keys = key.split(' ')
    mod = 0
    for k in keys:
        if k == 'Ctr':
            mod = mod | 2
        elif k == 'Shift':
            mod = mod | 1
        elif k == 'Alt':
            mod = mod | 3
        elif k in km:
            kv.KeyCode = km[k]
            
    kv.Modifiers = mod
    return kv
