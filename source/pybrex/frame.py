#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Application window module
# Created: 02.10.2018
# Copyright (C) 2018, Timothy Hoover

 
from random import randint

from librepy.pybrex.msgbox import msgbox

from com.sun.star.awt import Rectangle, WindowDescriptor
from com.sun.star.beans import NamedValue, PropertyValue
from com.sun.star.awt.WindowClass import SIMPLE, CONTAINER, TOP, MODALTOP
from com.sun.star.awt.VclWindowPeerAttribute import CLIPCHILDREN, HSCROLL, VSCROLL, AUTOVSCROLL
from com.sun.star.awt.WindowAttribute import BORDER, SHOW
from com.sun.star.awt.PosSize import POSSIZE, SIZE


import logging
logger = logging.getLogger(__name__)

def create_frame(ctx, smgr, ps, title, name):
    '''Create a frame'''
    frame = smgr.createInstanceWithContext(
        'com.sun.star.frame.TaskCreator', ctx).createInstanceWithArguments(
        (NamedValue('FrameName', name),
        NamedValue('PosSize', Rectangle(*ps))))
    window = frame.getContainerWindow()
    desktop = smgr.createInstanceWithContext(
        'com.sun.star.frame.Desktop', ctx)
    frame.setTitle(title)
    frame.setCreator(desktop)
    desktop.getFrames().append(frame)
    return frame, window

def create_window(toolkit, parent, wtype, service, attrs, ps):
    aWindowDescriptor = WindowDescriptor()
    aWindowDescriptor.Type = service
    aWindowDescriptor.WindowServiceName = wtype
    aWindowDescriptor.Parent = parent
    aWindowDescriptor.ParentIndex = 1
    aWindowDescriptor.Bounds = Rectangle(*ps)
    aWindowDescriptor.WindowAttributes = attrs
    return toolkit.createWindow(aWindowDescriptor)
        
def vertical_splitter(toolkit, parent, ps, listener = None):
        #Create splitter window
        spl = create_window(
            toolkit, parent, 'splitter', SIMPLE, 
            CLIPCHILDREN | BORDER | SHOW | HSCROLL,
            ps)
        #Set attributes
        spl.setProperty('BackgroundColor', 0xDCDAD5)
        spl.setProperty('Border',0)
        spl.setProperty('Text', '....')
        spl.setProperty('FontOrientation', 2)
        if not listener is None:
            spl.addMouseListener(listener)
            spl.addMouseMotionListener(listener)
        return spl
        
def horizontal_splitter(toolkit, parent, ps, listener = None):
        #Create splitter window
        spl = create_window(
            toolkit, parent, 'splitter', SIMPLE, 
            CLIPCHILDREN | BORDER | SHOW | VSCROLL,
            ps)
        #Set attributes
        spl.setProperty('BackgroundColor', 0xDCDAD5)
        spl.setProperty('Border',0)
        spl.setProperty('Text', '....')
        spl.setProperty('FontOrientation', 1)
        if not listener is None:
            spl.addMouseListener(listener)
            spl.addMouseMotionListener(listener)
        return spl
        
        

def  create_document(smgr, ctx, window, ps, props, doc_type = 'sdraw'):
    '''Create a drawing document in the window'''
    #Create the window
    xToolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    xWindow = create_window(
        xToolkit, window, 'dockingwindow', SIMPLE, CLIPCHILDREN + BORDER + SHOW, ps)
    #create a frame and initialize it with the created window...
    m_xFrame = smgr.createInstanceWithContext("com.sun.star.frame.Frame", ctx)
    m_xFrame.initialize(xWindow)
    oDoc = m_xFrame.loadComponentFromURL('private:factory/%s' % doc_type, "_self", 0, tuple(props))
    return xWindow, oDoc
    
    
        
def get_frame_name(ctx, smgr, frame_name):
    'Get a unique frame name'
    my_name = '%s_0000' % frame_name
    desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    frames = desktop.getFrames()
    names = []
    for i in range(frames.getCount()):
        n = frames.getByIndex(i).getName()
        if len(n) == len(my_name) and n.startswith(my_name[:-4]):
            names.append(n[-4:])

        #Get a unique ID for this session
    id_n = randint(1000, 9000)
    id_s = str(id_n)
    my_name = my_name[:-4] + id_s
    return my_name
