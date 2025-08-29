#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Selectable combo box
# Created: 9/13/2018
# Copyright (C) 2018, Timothy Hoover



import unohelper
import traceback

from librepy.pybrex.msgbox import msgbox

from com.sun.star.awt import XTextListener, XKeyListener

import logging
logger = logging.getLogger(__name__)

class ComboData( unohelper.Base, XTextListener ):
    
    def __init__(self, ctr):
        self.ctr = ctr
        self.listener = self.TextListener(self)
        ctr.addTextListener(self.listener)
        ctr.addKeyListener(self.KeyListener(self))
        self.selection = None
        self.prvs = ''
        
    def init_data(self, data):
        ctr = self.ctr
        self.config_data(data)
        #Set data to combo box
        ctr.removeItems(0, ctr.getItemCount())
        ctr.addItems(tuple(self.names), 0)
        
    def config_data(self, data):
        #Rename duplicate names
        names, ids = [], []
        name_dict = {}
        self.names, self.ids = names, ids
        self.name_dict = name_dict
        
        #No renaming necessary if 1 or less items
        if len(data) < 2:
            if len(data) == 1:
                names.append(data[0]['name'])
                ids.append(data[0]['id'])
                name_dict[names[0]] = ids[0]
            return
            
        n = 1
        s = data[0]['name']
        new_name = s
        if s == data[1]['name']:
            new_name = '%s (%s)' % (s, n)
            n += 1
        names.append(new_name)
        ids.append(data[0]['id'])
        name_dict[new_name] = data[0]['id']
        
        for i in range(1, len(data)):
            if data[i]['name'] == s:
                new_name = '%s (%s)' % (s, n)
                n += 1
            else:
                n = 1
                s = data[i]['name']
                new_name = s
            names.append(new_name)
            ids.append(data[i]['id'])
            name_dict[new_name]  = data[i]['id']
        return
        
    def get_id(self):
        t = self.ctr.getText()
        return self.name_dict[t] if t in self.names else None
        
    def key_pressed(self, ev):
        if ev.KeyCode == 1283:
            self.ctr.removeTextListener(self.listener)
            self.ctr.setText('')
            self.prvs = ''
            self.ctr.addTextListener(self.listener)
        
    def text_changed(self, ev):
        t = self.ctr.getText()
        if t == '':
            self.prvs = ''
            return
        self.ctr.removeTextListener(self.listener)
        if t in self.names:
            self.prvs = t
            self.selection = self.ctr.getSelection()
        else:
            self.ctr.setText(self.prvs)
            if self.selection:
                self.ctr.setSelection(self.selection)
        self.ctr.addTextListener(self.listener)
        
    class TextListener(unohelper.Base, XTextListener):
        
        def __init__(self, parent):
            self.parent = parent
        def disposing(self, ev):
            pass
        def textChanged(self, ev):
            try:
                self.parent.text_changed(ev)
            except Exception as e:
                logger.error(traceback.format_exc())
    
    class KeyListener(unohelper.Base, XKeyListener):
        
        def __init__(self, parent):
            self.parent = parent
        def disposing(self, ev):
            pass
        def keyPressed(self, ev):
            try:
                self.parent.key_pressed(ev)
            except Exception as e:
                logger.error(traceback.format_exc())
        def keyReleased(self, ev):
            pass
