#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Toolbar for main frame
# Created: 3-29-2018
#Modified 11.18.2021
# Copyright (C) 2018, Timothy Hoover

import unohelper
import traceback

from librepy.pybrex import toolbar
from com.sun.star.awt.PosSize import POSSIZE, SIZE

import logging
logger = logging.getLogger(__name__)

def my_toolbar(parent, ctx, smgr, frame):
    '''Create toolbar
    index 0 = Control type
    index 1 = Display text
    index 2 = Image name
    index 3 = command
    index 4 = Help text
    index 5 = Width offset
    '''
    
    toolbar_list = [
        ['Button', 'New', 'document-new.png', parent.new_file,  'Open a new file', 0 ],
        ['Button', 'Open', 'document-open.png', parent.open_file, 'Open an existing file', 0 ],
        ['Button', 'Save', 'document-save.png', parent.save_file, 'Save the current file', 0 ],
        ['Line', 'line1'],
        ['Button', 'Settings', 'document-properties.png', parent.settings, 'Settings', 15],
        ['Line', 'line2'],
        ['Button', 'About', 'help-about.png', parent.show_about, 'About', 0 ]  
    ]
        
    return toolbar.ToolBar(parent, ctx, smgr, frame, toolbar_list)
