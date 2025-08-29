#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Menubar for main application window
# Created: 02.10.2018
#Modified 11.18.2021
# Copyright (C) 2018, Timothy Hoover

import unohelper, traceback

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex import menubar

import logging
logger = logging.getLogger(__name__)

        
def my_menubar(parent, ctx, smgr, frame):
    '''Main menus'''
    
    #Menu bar items
    m = menubar.Menu
    sm = menubar.SubMenu
    menulist = [
    m(0, '~File', None, (
        sm(0, '~New', 'f_new', graphic = 'document-new.png', key = 'Ctr N'),
        sm(1, '~Open', 'f_open', graphic = 'document-open.png', key = 'Ctr O'),
        sm(2, '~Save', 'f_save', graphic = 'document-save.png', key = 'Ctr S'),
        sm(None, 'Divider'),
        sm(3, '~Settings', 'p_settings', graphic = 'document-properties.png'))),
    m(1, '~Help', None, (
        sm(0, '~About', 'h_about', graphic = 'help-about.png'), )), 
    ]
    
    #Meun bar functions
    fn = {}
    fn['f_new'] = parent.new_file
    fn['f_open'] = parent.open_file
    fn['f_save'] = parent.save_file
    fn['p_settings'] = parent.settings

    fn['h_about'] = parent.show_about
    #Create and return
    return menubar.Menubar(parent, ctx, smgr, frame, menulist, fn)
    
