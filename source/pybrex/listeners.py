#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Listeners for controls
# Created: 7/27/2018
# Copyright (C) 2018, Timothy Hoover


import uno
import unohelper
import traceback

from librepy.pybrex.msgbox import msgbox

from com.sun.star.awt import XActionListener, XMouseListener, XMouseMotionListener, \
    XItemListener, XAdjustmentListener, XTextListener, XFocusListener, XKeyListener, XSpinListener
from com.sun.star.view import XSelectionChangeListener
from com.sun.star.awt.grid import XGridSelectionListener

import logging
logger = logging.getLogger(__name__)

class Listeners(object):
    def __init__(self):
        pass
    '''Listener methods'''
    def add_action_listener(self, ctr, callback):
        listener = self.ActionListener(callback)
        ctr.addActionListener(listener)
        return listener
    def add_adjustment_listener(self, ctr, callback):
        listener = self.AdjustmentListener(callback)
        ctr.addAdjustmentListener(listener)
        return listener
    def add_item_listener(self, ctr, callback):
        listener = self.ItemListener(callback)
        ctr.addItemListener(listener)
        return listener
    def add_text_listener(self, ctr, callback):
        listener = self.TextListener(callback)
        ctr.addTextListener(listener)
        return listener
    def add_focus_listener(self, ctr, gained = None, lost = None):
        listener = self.FocusListener(gained, lost)
        ctr.addFocusListener(listener)
        return listener
    def add_key_listener(self, ctr, pressed = None, released = None):
        listener = self.KeyListener(pressed, released)
        ctr.addKeyListener(listener)
        return listener
    def add_spin_listener(self, ctr, up = None, down = None, first = None, last =None):
        listener = self.SpinListener(up, down, first, last)
        ctr.addSpinListener(listener)
        return listener
    def add_mouse_listener(self, ctr, pressed = None, released = None, entered = None, exited =None):
        listener = self.MouseListener(pressed, released, entered, exited)
        ctr.addMouseListener(listener)
        return listener
    def add_mousemotion_listener(self, ctr, dragged = None, moved = None):
        listener = self.MouseMotionListener(dragged, moved)
        ctr.addMouseMotionListener(listener)
        return listener
        
    def add_scroll_function(self, ctr, step, value = 0):
        'This tries to correct a bug where the numbers do not scroll correctly when using mouse wheel scroll'
        listener = self.ScrollListener(ctr, step, value)
        ctr.addSpinListener(listener)
        return listener
        
    '''Listener classes'''
    class ListenerBase(unohelper.Base):
        
        def __init__(self, *callbacks):
            self.callbacks = callbacks
            
        def disposing(self, ev):
            self.callbacks = None
            
        def _run(self, callback, ev):
            if callback is None:
                return
            try:
                callback(ev)
            except Exception as e:
                logger.error(traceback.format_exc())
                msgbox(traceback.format_exc())
            
    class ActionListener(ListenerBase, XActionListener):
        def actionPerformed(self, ev):
            self._run(self.callbacks[0], ev)
    class AdjustmentListener(ListenerBase, XAdjustmentListener):
        def adjustmentValueChanged(self, ev):
            self._run(self.callbacks[0], ev)
    class ItemListener(ListenerBase, XItemListener):
        def itemStateChanged(self, ev):
            self._run(self.callbacks[0], ev)
    class TextListener(ListenerBase, XTextListener):
        def textChanged(self, ev):
            self._run(self.callbacks[0], ev)
    class FocusListener(ListenerBase, XFocusListener):
        def focusGained(self, ev):
            self._run(self.callbacks[0], ev)
        def focusLost(self, ev):
            self._run(self.callbacks[1], ev)
    class KeyListener(ListenerBase, XKeyListener):
        def keyPressed(self, ev):
            self._run(self.callbacks[0], ev)
        def keyReleased(self, ev):
            self._run(self.callbacks[1], ev)
    class SpinListener(ListenerBase, XSpinListener):
        def up(self, ev):
            self._run(self.callbacks[0], ev)
        def down(self, ev):
            self._run(self.callbacks[1], ev)
        def first(self, ev):
            self._run(self.callbacks[2], ev)
        def last(self, ev):
            self._run(self.callbacks[3], ev)
    class MouseListener(ListenerBase, XMouseListener):
        def mousePressed(self, ev):
            self._run(self.callbacks[0], ev)
        def mouseReleased(self, ev):
            self._run(self.callbacks[1], ev)
        def mouseEntered(self, ev):
            self._run(self.callbacks[2], ev)
        def mouseExited(self, ev):
            self._run(self.callbacks[3], ev)
    class MouseMotionListener(ListenerBase, XMouseMotionListener):
        def mouseDragged(self, ev):
            self._run(self.callbacks[0], ev)
        def mouseMoved(self, ev):
            self._run(self.callbacks[1], ev)
            
            
    class ScrollListener(unohelper.Base, XSpinListener):
        
        def __init__(self, ctr, step, value):
            self.ctr = ctr
            self.step = step
            self.value = value
            
        def disposing(self, ev):
            pass
            
        def up(self, ev):
            if self.value >= self.ctr.Model.EffectiveMax:
                self.vaue = self.ctr.Model.EffectiveMax
            else:
                self.value += self.step
            self.ctr.Model.EffectiveValue = self.value
            
        def down(self, ev):
            if self.value <= self.ctr.Model.EffectiveMin:
                self.vaue = self.ctr.Model.EffectiveMain
            else:
                self.value -= self.step
            self.ctr.Model.EffectiveValue = self.value
            
        def first(self, ev):
            pass
            
        def last(self, ev):
            pass

