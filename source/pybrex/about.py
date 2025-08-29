#coding:utf-8
# Author:  Timothy Hoover
# Purpose: about AR
# Created: 03/18/20
# Copyright (C) 2020, Timothy Hoover

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.values import PYBREX_NAME, PYBREX_VERSION
        
def show_about():
    msg = '%s %s' \
        '\n\nLibreoffice/python' \
         "\ndeveloper gui." \
         '\n\n(c) 2019-2024 by Timothy Hoover' % (PYBREX_NAME, PYBREX_VERSION)
         
    msgbox(msg)
