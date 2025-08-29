#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Initialize and save dialogs
# Created: 7/28/2018
# Copyright (C) 2018, Timothy Hoover


import traceback


from librepy.pybrex.dialogs.misc_dialogs import DialogList

from librepy.pybrex.msgbox import msgbox

import logging
logger = logging.getLogger(__name__)



class Dialogs(object):
    '''Class to load and keep track of all the dialogs'''
    def __init__(self, ctx, smgr, parent):
        self.ctx = ctx
        self.smgr = smgr
        self.parent = parent
        self.dialog_list = DialogList()
        self.name = None
        
    def __getattr__(self, name):
        if name[:1] == '_':
            return False
        else:
            self.name = name
            return self._get_dialog
            

    def _get_dialog(self, *args, **kwargs):
        name = self.name
        dlg = getattr(self, '_%s' % name)
        if not dlg or dlg._dialog.getAccessibleContext() is None:
            #get the dialog class
            dlg_class = self.dialog_list.dialogs[name] #getattr(self.dialog_list, name)
            #initialize dialog 
            dlg = dlg_class(self.ctx, self.parent, *args, **kwargs) 
            setattr(self, '_%s' % name, dlg)
        return getattr(self, '_%s' % name)
        
    def dispose(self):
        #Dispose all dialogs that exist
        try:
            for name in self.dialog_list.dialogs:
                dlg = getattr(self, '_%s' % name)
                if not dlg or dlg._dialog.getAccessibleContext() is None:
                    pass
                else:
                    dlg._dialog.dispose()
        except Exception as e:
            msgbox('Failed to dispose dialogs.\n%s' % traceback.format_exc())
