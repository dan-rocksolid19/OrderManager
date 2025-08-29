#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Control container module for application windows
# Created: 03.17.2018
# Copyright (C) 2018, Timothy Hoover


import uno, unohelper
import traceback

from librepy.pybrex.controls import Controls
from librepy.pybrex.grid import GridBase

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.my_mri import mri

from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.awt import XAdjustmentListener, XTextListener, XMouseListener, XFocusListener, XKeyListener
from com.sun.star.style.VerticalAlignment import MIDDLE as VA_MIDDLE
from com.sun.star.awt.TextAlign import CENTER as TA_CENTER

import logging

logger = logging.getLogger(__name__)

class Container(Controls):
    
    def __init__(self, ctx, smgr, window, ps, background_color=0xDCDAD5):
        self.ctx = ctx
        self.smgr = smgr
        self.window = window
        self.ps = ps
        self.background_color = background_color
        super().__init__(ctx=self.ctx, smgr=self.smgr)
        self.container = self.create_container(ps)
        
    def create_container(self, ps):
        ctx, smgr = self.ctx, self.smgr
        '''Create a control container in a window'''
        toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
        cont = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlContainer', ctx)
        cont_model = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlContainerModel', ctx)
        cont.setModel(cont_model)
        cont.createPeer(toolkit, self.window)
        cont.setPosSize(ps[0], ps[1], ps[2], ps[3], POSSIZE)
        cont_model.BackgroundColor = self.background_color
        return cont
    
    def resize(self, width, height):
        self.container.setPosSize(0, 0, width, height, SIZE)
    
    def show(self):
        self.container.setVisible(True)
        
    def hide(self):
        self.container.setVisible(False)
        
    def dispose(self):
        self.container.dispose()

    def redraw(self):
        '''Force a redraw of the container'''
        peer = self.container.getPeer()
        if peer:
            peer.invalidate(0)
        
    def add_control(self, s_type, name, x, y, width, height, page = None, **props):
        '''Add a control to the container'''
        ctx, smgr = self.ctx, self.smgr
        if page is not None:
            dlg = page
        else:
            dlg = self.container
        #create the control
        ctr = smgr.createInstanceWithContext(s_type[:-5], ctx)
        ctr_mod = smgr.createInstanceWithContext(s_type, ctx)
        #set the controls properties
        if len(props) > 0:
            ctr_mod.setPropertyValues(tuple(props.keys()), tuple(props.values()))
        ctr.setPosSize(x, y, width, height, POSSIZE)
        #insert the control
        ctr.setModel(ctr_mod)
        self.container.addControl(name, ctr)
        return ctr
        
    def add_grid(self, name, x, y, width, height, titles, **props):
        ''' Override the default add_grid function '''

        g_base = GridBase(self.ctx, self.smgr)

        g_base.titles = titles

        grid_ctr, grid_model = g_base.create_grid(name, x, y, width, height, titles, **props)
        
        #insert the control
        self.container.addControl(name, grid_ctr)
        
        self._controls[name] = grid_ctr
        return g_base, grid_ctr
    
def create_control(ctx, smgr, ctrType, px, py, width, height, **props):
    '''Create a control for the container'''
    ctr = smgr.createInstanceWithContext('com.sun.star.awt.UnoControl%s' % ctrType, ctx)
    ctr_mod = smgr.createInstanceWithContext('com.sun.star.awt.UnoControl%sModel' % ctrType, ctx)
    ctr_mod.setPropertyValues(tuple(props.keys()), tuple(props.values()))
    ctr.setModel(ctr_mod)
    ctr.setPosSize(px, py, width, height, POSSIZE)
    return ctr
    
def create_container(ctx, smgr, window, ps):
    '''Create a control container in a window'''
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    cont = smgr.createInstanceWithContext(
        'com.sun.star.awt.UnoControlContainer', ctx)
    cont_model = smgr.createInstanceWithContext(
        'com.sun.star.awt.UnoControlContainerModel', ctx)
    cont.setModel(cont_model)
    cont.createPeer(toolkit,window)
    cont.setPosSize(ps[0], ps[1], ps[2], ps[3], POSSIZE)
    cont_model.BackgroundColor = 0xDCDAD5
    return cont
