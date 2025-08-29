#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Dialog base
# Created: 7/27/2018
# Copyright (C) 2018, Timothy Hoover



import uno
import unohelper
import traceback
from librepy.pybrex.controls import Controls

from com.sun.star.awt import Rectangle #rectangle module for popup menu
from com.sun.star.awt.PosSize import X as PS_X, Y as PS_Y

import logging
logger = logging.getLogger(__name__)
        
class DialogBase(Controls):
    
    DISPOSE = True
    POS_SIZE = 0,0,0,0
    
    def __init__(self, ctx, cast, parent_window = None, **props): 
        self.ctx = ctx
        self.cast = cast
        self._ret = False   #Variable to set returned number for end execute function
        Controls.__init__(self, ctx=self.ctx, smgr=self.ctx.ServiceManager)
        self.parent_window = parent_window if parent_window is not None else self.get_top_window()
        self._dialog, self._dialog_model = self._create_dialog(*self.POS_SIZE, **props)
        self._create()
        self._position_x = None
        self._position_y = None
        
    def _create_dialog(self, x, y, width, height, **props):
        #create a dialog
        dlg = self.create_service( "com.sun.star.awt.UnoControlDialog")
        dlg_mod = self.create_service("com.sun.star.awt.UnoControlDialogModel")
        #Set x and y
        if x + y == 0:
            x, y = self._get_window_center(width, height)
            
        if 'Title' in props:
            title = props['Title']
        else:
            title = "no name"
        
        dlg_mod.setPropertyValues(
            ('Height','PositionX','PositionY','Width',), 
            (height, x, y, width,) )
        if len(props) > 0:
            dlg_mod.setPropertyValues(tuple(props.keys()), tuple(props.values()))
        dlg.setModel(dlg_mod)
        #Don't show dialog right away
        dlg.setVisible(False)
        return dlg, dlg_mod
        
        
    def _get_window_center(self, width, height):
        'Get the active window center'
        size = createUnoStruct("com.sun.star.awt.Rectangle")
        if self.parent_window is not None:
            size = self.parent_window.Size
        else:
            size = get_screen_size()
            
        w_width = size.Width
        w_height = size.Height
        #TODO Figure out a way to calculate the difference between these measurements
        x = int((w_width / 4.8 ) - (width / 2))
        y = int((w_height / 3.76) - (height / 2))
        return x, y
        
    def get_screen_size(self):
        'Get size of screen'
        try:
            service = createUnoService("com.sun.star.awt.Toolkit")
            size = service.getWorkArea()
            if size.Width > 100:
                return size
        except:
            pass
        #Try and return current component size
        try:
            service = createUnoService("com.sun.star.awt.Toolkit")
            size = thisComponent.CurrentController.ComponentWindow.PosSize
            if size.Width > 100:
                return size
        except:
            pass
        #Mimic a 768 x 1024 screen
        size = createUnoStruct("com.sun.star.awt.Rectangle")
        size.Width = 1024
        size.Height = 768
        return size
        
        
    def get_top_window(self):
        
        desktop = createUnoService('com.sun.star.frame.Desktop')
        frames = desktop.getFrames()
        cf = []
        #Get mri frames
        window = None
        for i in range(frames.getCount()):
            frame = frames.getByIndex(i)
            window = frame.getContainerWindow()
            if window.hasFocus():
                return window
        return window
    
    def _save_current_position(self):
            'Save x and y position for dialog'
            'TODO: Fix this function'
            return
            ps = self._dialog.PosSize
            x = int(ps.X / 2.4)
            y = int(ps.Y / 1.87)
            #Check top and left boundaries
            if x < 0: x = 0
            if y < 0: y = 0
            #check bottom and right boundaries
            size = self.parent.frame.frame.window.Size
            mw_width = int(size.Width / 2.4)
            mw_height = int(size.Height / 1.87)
            dlg_width = self._dialog_model.Width
            dlg_height = self._dialog_model.Height
            if x + dlg_width > mw_width:
                x = mw_width - dlg_width
            if y + dlg_height > mw_height:
                y = mw_height - dlg_height
                
            self._dialog_model.setPropertyValues( 
                ('PositionX','PositionY'), 
                (x, y,) )
                
            
        
    def execute(self):
        toolkit = self.create_service("com.sun.star.awt.Toolkit")
        self._dialog.createPeer(toolkit, self.parent_window)
        self._prepare()
        #Actual execution
        n = self._dialog.execute()
        if self._ret:
            n = self._ret
        self._ret = False
        ret = self._done(n)
        #Dispose
        if self.DISPOSE:
            self._dispose()
            self._dialog.dispose()
        else:
            self._save_current_position()
        return ret
        
    def show(self):
        self._dialog.setVisible(True)
        
        if self._position_x is not None:
            self._dialog.setPosSize(self._position_x, self._position_y, 0, 0, PS_X + PS_Y)
        
    def hide(self):
        if not self._dialog.isVisible():
            return
        #Save the position
        self._save_current_position()
        ps = self._dialog.getPosSize()
        self._position_x = ps.X
        self._position_y = ps.Y
        self._dialog.setVisible(False)
        
    def end_execute(self, ret):
        'Call this to simulate ending the dialog'
        self._ret = ret
        self._dialog.endExecute()
        
    def _create(self):
        'Implement this to create the dialog'
        
    def _prepare(self):
        'Gets called after the dialog initializes, but before it becomes visible'
    
    def _dispose(self):
        'Gets called when the dialog gets disposed'
        
    def _done(self, ret):
        'Gets called when the dialog closes'
        return ret
    

    def create_service(self, serviceName):
        """ gets a service from Uno """
        sm = self.ctx.ServiceManager
        result = sm.createInstanceWithContext(serviceName, self.ctx)
        return result
    
    def _set_properties(self, ctr, **props):
        for prop,value in props.items():
            ctr.setPropertyValue(prop,value)
    
    def add_control(self, s_type, name, x, y, width, height, page = None, **props):
        '''Add a control to the dialog'''
        if page is not None:
            dlg = page
            model = page.Model
        else:
            dlg = self._dialog
            model = self._dialog_model
        #create the control
        ctr_mod = model.createInstance(s_type)
        #set the controls properties
        ctr_mod.setPropertyValues(
                ("Height", "PositionX", "PositionY", "Width", "Name" ),
                (height, x, y, width, name))
        if len(props) > 0:
            ctr_mod.setPropertyValues(tuple(props.keys()), tuple(props.values()))
        #insert the control
        model.insertByName(name, ctr_mod)
        return dlg.getControl(name)



class DialogFake():
    '''Creates a fake dialog class'''
    def __init__(self, ret):
        self.ret = ret
        
    def getAccessibleContext(self):
        return self.ret
    
    def dispose(self): pass
        
       