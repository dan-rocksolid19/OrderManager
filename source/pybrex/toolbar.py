#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Toolbar methods
# Created: 3-29-2018
#Modified 11.18.2021
# Copyright (C) 2018, Timothy Hoover

import uno, unohelper
import traceback

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex import ctr_container
from librepy.pybrex.values import TOOLBAR_GRAPHICS_DIR

from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.awt import XAdjustmentListener, XTextListener, XMouseListener, XFocusListener, XKeyListener
from com.sun.star.style.VerticalAlignment import MIDDLE as VA_MIDDLE
from com.sun.star.awt.TextAlign import CENTER as TA_CENTER

class ToolBar(object):
    def __init__(self, parent, ctx, smgr, frame, toolbar_list, **kwargs):
        self.logger = parent.logger
        self.logger.info("Toolbar initialized")

        # Get the window dimensions to match the toolbar width
        window_possize = frame.window.getPosSize()
        window_width = window_possize.Width

        # Default configurations
        self.config = {
            'height': 55,
            'button_width': 50,
            'button_height': None, # Will use height minus 5 if None
            'button_spacing': 50,
            'possize': {
                'x': 0,
                'y': 0,
                'width': window_width,  # Use the window width
                'height': None  # Will use height if None
            },
            'colors': {
                'border': 1,  # Border line color
                'button_normal': 0xDCDAD5,  # Normal button state
                'button_hover': 0xF0EFEA,   # Mouse hover state
                'button_pressed': 0xA5A5A5, # Pressed state
            }
        }
        # Update config with any provided kwargs
        self.config.update(kwargs)
        
        # If possize height is None, use the toolbar height
        if self.config['possize']['height'] is None:
            self.config['possize']['height'] = self.config['height']

        # If button height is None, use the toolbar height minus 5 to account for the border
        if self.config['button_height'] is None:
            self.config['button_height'] = self.config['height'] - 5
        
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.height = self.config['height']
        # Use the config values for possize
        self.possize = (
            self.config['possize']['x'],
            self.config['possize']['y'],
            self.config['possize']['width'],
            self.config['possize']['height']
        )
        self.container = ctr_container.create_container(ctx, smgr, frame.window, self.possize)
        
        self.controls = self.container_controls(ctx, smgr, self.container)
        self._add_controls(self.controls, self.container)
        
        self.toolbar = create_toolbar(parent, ctx, smgr, self.container, 
                                    toolbar_list, self.config)

    def container_controls(self, ctx, smgr, cont):
        '''Create the controls in the control container'''
        ctrs = {}
        cc = ctr_container.create_control
        
        ctrs['border_line'] = cc(ctx, smgr, 'FixedLine',
            0, self.height - 4,  # Changed from fixed 35 to height - 4
            self.possize[2], 4, 
            BackgroundColor=self.config['colors']['border'])
        
        return ctrs
            
    def _add_controls(self, ctrs, cont):
        '''Add the controls to the container'''
        for ctr in ctrs.items():
            cont.addControl(ctr[0], ctr[1])
            
    def resize(self, width, height, flags = POSSIZE):
        '''Window size changed'''
        self.container.setPosSize(0, 0, width , self.height, flags)
        ctr = self.controls['border_line']
        ctr.setPosSize(0, self.height-4, width, 4, flags)
        
    def dispose(self):
        self.container.dispose()

def create_toolbar(parent, ctx, smgr, cont, items, config):
    '''Create toolbar controls in a container'''
    g_dir = uno.systemPathToFileUrl(TOOLBAR_GRAPHICS_DIR)
    
    cc = ctr_container.create_control
    ctrs = {}
    l_ctrs = {}
    px = 5
    py = 1
    width = config['button_width']
    height = config['button_height']
    x_step = config['button_spacing']
    
    for item in items:
        if item[0] == 'Line':
            #Create divider line
            ctr = cc(ctx, smgr, 'FixedLine',
                px + 5, py + 2, 1, height - 4, Orientation = 1)
            ctrs[item[1]] = ctr
            px += 12
            cont.addControl(item[1], ctr)
        elif item[0] == 'Button':
            #Create control
            g_url = '%s/%s' % (g_dir, item[2])
            ctr1 = cc(ctx, smgr, 'ImageButton',
                px, py, width + item[5], height - 20, 
                ScaleImage = False, Border = 0, ImageURL = g_url, HelpText = item[4])
            
            ctr2 = cc(ctx, smgr, 'FixedText',
                px , py + height - 20, width + item[5], 20, 
                Label = item[1], Border = 0, HelpText = item[4], VerticalAlign = VA_MIDDLE, Align = TA_CENTER)
            
            px += x_step + item[5]
            
            ctr1.addMouseListener(ToolbarMouseListener(parent, item[3], ctr1, ctr2))
            ctr2.addMouseListener(ToolbarMouseListener(parent, item[3], ctr1, ctr2))
            
            ctrs[item[1]] = ctr1
            cont.addControl(item[1], ctr1)
            cont.addControl(item[1], ctr2)
        
    return ctrs



class ToolbarMouseListener(unohelper.Base, XMouseListener):
    '''Listener for toolbar mouse events'''
    def __init__(self, parent, callback, ctr_1, ctr_2, colors=None):
        self.parent = parent
        self.callback = callback
        self.ctr1 = ctr_1.Model
        self.ctr2 = ctr_2.Model
        self.mouse_pressed = False
        self.colors = colors or {
            'normal': 0xDCDAD5,
            'hover': 0xF0EFEA,
            'pressed': 0xA5A5A5
        }

    def disposing(self,ev): pass
    def mousePressed(self, ev):
        self.ctr1.BackgroundColor = self.colors['pressed']
        self.ctr2.BackgroundColor = self.colors['pressed']
        self.mouse_pressed = True
    def mouseEntered(self,ev):
        self.ctr1.BackgroundColor = self.colors['hover']
        self.ctr2.BackgroundColor = self.colors['hover']
    def mouseExited(self,ev):
        self.ctr1.BackgroundColor = self.colors['normal']
        self.ctr2.BackgroundColor = self.colors['normal']
        self.mouse_pressed = False
    def mouseReleased(self,ev):
        self.ctr1.BackgroundColor = self.colors['normal']
        self.ctr2.BackgroundColor = self.colors['normal']
        if self.mouse_pressed:
            self.mouse_pressed = False
            try:
                #Run the callback command
                if self.callback is not None:
                    self.callback(True)
            except Exception as e:
                logger.error(traceback.format_exc())
            