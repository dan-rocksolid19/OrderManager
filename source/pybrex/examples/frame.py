#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Frame methods for example frame
# Created: 02.10.2018
#Modified 11.18.2021
# Copyright (C) 2018, Timothy Hoover

import unohelper
import traceback
import os, sys
import shutil
from stat import *
from random import randint

from librepy.pybrex.msgbox import msgbox, confirm_action, msgboxYesNoCancel
from librepy.pybrex import frame as fr_frame


from com.sun.star.awt import XActionListener, XItemListener, XKeyListener, \
    XMouseListener, XMouseMotionListener, XMenuListener, XWindowListener
from com.sun.star.document import XEventListener
from com.sun.star.util import XCloseListener
from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.util import CloseVetoException

import logging
logger = logging.getLogger(__name__)


class Frame(object):
    '''Example frame'''
    def __init__(self, parent, ctx, smgr, ps = (100, 100, 100, 100), title = 'My frame', frame_name = 'my_frame', **args):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        
        #Create a unique frame name for this window
        self.name = fr_frame.get_frame_name(ctx, smgr, frame_name)
        #Create
        self.frame, self.window = fr_frame.create_frame(ctx, smgr, ps, title, self.name)
        #Set listeners
        
        self.listeners = self.set_listeners(parent, ctx, smgr)
        

    def set_listeners(self, parent, ctx, smgr):
        '''Set frame listeners'''
        listeners = {}
        lst = FrameCloseListener(self)
        self.frame.addCloseListener(lst)
        listeners['close'] = lst
        lst = WindowListener(self)
        self.window.addWindowListener(lst)
        listeners['window'] = lst
    
        return listeners

    def remove_listeners(self):
        '''Remove frame listeners'''
        listeners = self.listeners
        lst = listeners['window']
        self.window.removeWindowListener(lst)
        lst = listeners['close']
        self.frame.removeCloseListener(lst)
        
    def window_resizing(self, width, height):
        '''Window is being resized'''
        self.parent.window_resizing(width, height)
        
    def window_closing(self, *args):
        '''Window is being closed'''
        self.dispose()
        
    def dispose(self):
        '''Dispose'''
        try:
            self.remove_listeners()
            #Set window size
            ps = self.window.PosSize
            #Every now and then Libreoffice returns incorrect results when closing a frame
            #When this happens, ignore 
            if ps.Width < 50 or ps.Height < 50:
                logger.error("Frame size error!")
            else:
                #Save the window position and size for next execution
                pass
                #c.fr_width, c.fr_height, c.pos_x, c.pos_y = ps.Width, ps.Height, ps.X, ps.Y
        except:
            logger.error(traceback.format_exc())
        
        #Dispose the parent
        try:
            self.parent.dispose()
        except:
            logger.error(traceback.format_exc())
            
        #Dispose myself
        try:
            self.frame.dispose()
        except:
            logger.error(traceback.format_exc())
        

class FrameCloseListener(unohelper.Base, XCloseListener):
    '''Window closing'''
    def __init__(self, parent):
        self.parent = parent
        
    def queryClosing(self, ev, b_owner):
        '''Window close querying'''
        b_close = True
        try:
            #Set b_close to false here to keep window from closing
            pass
        except Exception as e:
            logger.error(traceback.format_exc())
            
        if not b_close:
            #The close veto exception has to be caught by the listener that called this function
            logger.debug('Vetoing close')
            raise CloseVetoException()
        
    def notifyClosing(self, ev): 
        try:
            #Dispose before closing
            self.parent.window_closing()
        except Exception as e:
            logger.error(traceback.format_exc())
        
    def disposing(self, ev):
        logger.debug('Close disposing')

class WindowListener(unohelper.Base, XWindowListener):
    '''Window resizing'''
    def __init__(self, parent):
        self.parent = parent
        
    def disposing(self, ev): pass
    def windowMoved(self, ev): pass
    def windowShown(self, ev): pass
    def windowHidden(self, ev): pass
    def windowResized(self, ev):
        '''Window is resizing'''
        try:
            width = ev.Width
            height = ev.Height - 25 #Minus menubar height
            self.parent.window_resizing(width, height)
        except:
            logger.error(traceback.format_exc())
        
