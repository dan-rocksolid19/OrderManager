#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Dialog listing
# Created: 7/27/2018
# Copyright (C) 2018, Timothy Hoover

"""
PyBrex Miscellaneous Dialogs

This module provides a collection of specialized dialog classes for common user interface 
interactions in LibreOffice. It builds on top of the base dialog functionality to provide 
ready-to-use dialog implementations.

Key components:
- Value input dialogs (NameInputDlg, ValueInputDlg)
- File and folder selection (FilePickerDlg, FolderPickerDlg)
- Color selection (ColorPickerDlg)
- Dialog registry (DialogList)

The dialogs follow LibreOffice's UNO component model and integrate with the broader 
PyBrex dialog framework while providing simplified interfaces for common dialog operations.
"""


from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.dialog import DialogBase, DialogFake
from librepy.pybrex.my_mri import mri


import os
import uno, unohelper
import time, traceback

from com.sun.star.ui.dialogs.TemplateDescription import FILEOPEN_SIMPLE, FILESAVE_SIMPLE
from com.sun.star.awt.PosSize import POSSIZE, SIZE
from com.sun.star.awt import XWindowListener

import logging
logger = logging.getLogger(__name__)

class NameInputDlg(DialogBase):
    """Simple dialog for getting a text input from the user.
    
    Properties:
        POS_SIZE: (0, 0, 150, 60) - Default dialog dimensions
        DISPOSE: True - Dialog gets disposed after closing
    """
    
    POS_SIZE = 0, 0, 150, 60
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'Enter name', **props):
        DialogBase.__init__(self, ctx, cast, Title = Title, **props)
    
    def _create(self):
        self.add_ok_cancel()
        self.add_label('NameLabel', 10, 10, 100, 11, Label = '~Name:')
        self.add_edit('name', 10, 21, 130, 13)
    
    def _prepare(self):
        self._controls['name'].setFocus()
    
    def _done(self, ret):
        self.get_values()
        return ret, self._values
    
    def execute(self, values):
        self.clear_values()
        self._values = values
        self.set_values(values)
        return DialogBase.execute(self)
        
        
class ValueInputDlg(DialogBase):
    """Simple dialog for getting a numeric value input from the user.
    
    Properties:
        POS_SIZE: (0, 0, 150, 60) - Default dialog dimensions
        DISPOSE: True - Dialog gets disposed after closing
    """
    
    POS_SIZE = 0, 0, 150, 60
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'Enter value', **props):
        DialogBase.__init__(self, ctx, cast, Title = Title, **props)
    
    def _create(self):
        self.add_ok_cancel()
        self.add_label('NameLabel', 10, 10, 100, 11, Label = '~Value:')
        self.add_numeric('value', 10, 21, 130, 13)
    
    def _prepare(self):
        self._controls['value'].setFocus()
    
    def _done(self, ret):
        self.get_values()
        return ret, self._values
    
    def execute(self, values):
        self.clear_values()
        self._values = values
        self.set_values(values)
        return DialogBase.execute(self)
        
        
class ConfirmYesDlg(DialogBase):
    """Dialog that requires user to type 'yes' to confirm an action.
    
    A safety dialog for potentially dangerous operations that requires explicit 
    confirmation by typing 'yes' rather than just clicking a button.
    
    Properties:
        POS_SIZE: (0, 0, 150, 60) - Default dialog dimensions
        DISPOSE: True - Dialog gets disposed after closing
        
    Methods:
        execute(): Shows confirmation dialog
        Returns:
            int: 1 if user typed 'yes', 0 otherwise or if cancelled
    """
    
    POS_SIZE = 0, 0, 150, 60
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'Authorize', **props):
        DialogBase.__init__(self, ctx, cast, Title = Title, **props)
    
    def _create(self):
        self.add_ok_cancel()
        self.add_label('NameLabel', 10, 10, 130, 11, Label = '~Enter yes to continue:')
        self.add_edit('text', 10, 21, 130, 13)
    
    def _prepare(self):
        self._controls['text'].setFocus()
    
    def _done(self, ret):
        if ret != 1:
            return 0
        if self._controls['text'].getText() == 'yes':
            return 1
        else:
            return 0
    
        
            
def get_selected_file_path(ctx, path, name = None, mode='open', filters = (('All files', '*'), )):
    """Helper function to get a file path using the file picker dialog.
    
    Provides a simplified interface to FilePickerDlg for single file selection.
    
    Args:
        ctx: UNO component context
        path: Starting directory path
        name (str, optional): Default filename for save dialogs. Defaults to None.
        mode (str, optional): Dialog mode ('open' or 'save'). Defaults to 'open'.
        filters (tuple, optional): File filters as (description, pattern) tuples. 
                                 Defaults to (('All files', '*'),).
    
    Returns:
        str or list: Selected file path(s) or None if cancelled.
                    Returns list if multiple files selected, str for single file.
    """
    dlg = FilePickerDlg(ctx, None, Title = 'Select file')
    urls = dlg.execute(path, name = name, dlg_mode = mode, multi_selection = False, filters = filters)
    
    if urls is None or urls[0] is None or urls[0] == '':
        return None
    
    if len(urls) > 1:
        paths = []
        for path in urls:
            paths.append(uno.fileUrlToSystemPath(path))
        return paths
    else:
        path = uno.fileUrlToSystemPath(urls[0])
        return path
        
        
        
class FilePickerDlg(object):
    """This class provides a simplified interface to LibreOffice's file picker dialog,
    handling common operations like:
    - File filtering 
    - Multi-file selection
    - Window sizing
    - Directory navigation
    
    Example:
        picker = FilePickerDlg(ctx, parent)
        result = picker.execute(
            folder="/home/user",
            filters=[("Python files", "*.py")]
        )
        
    Properties:
        POS_SIZE: (0, 0, 800, 600) - Default picker dimensions
        DISPOSE: True - Dialog gets disposed after closing
        
    Methods:
        execute(folder, name=None, dlg_mode='open', filters=None, multi_selection=False):
            Shows file picker dialog
            Args:
                folder: Starting directory path
                name: Default filename for save dialogs
                dlg_mode: 'open' or 'save'
                filters: Tuple of (description, pattern) for file filters
                multi_selection: Allow selecting multiple files
            Returns:
                Selected file path(s) or None if cancelled
    """
    
    POS_SIZE = 0, 0, 800, 600
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'File selection', **props):
        self.ctx = ctx
        self.cast = cast
        self._dialog = DialogFake(True)
        
        
    def execute(self, folder, name = None, dlg_mode='open', filters = (('Python files', '*.py'), ('All files', '*')), multi_selection = False):
        f = None
        if dlg_mode.lower() == 'save':
            mode = FILESAVE_SIMPLE
        else:
            mode = FILEOPEN_SIMPLE
        #Create dialog instance
        f_dlg = self.ctx.getServiceManager().createInstanceWithArgumentsAndContext(
            "com.sun.star.ui.dialogs.FilePicker", (mode,), self.ctx)
            
        #Allow multiselection
        f_dlg.setMultiSelectionMode(multi_selection)
        #Hide the help button    
        try:
            f_dlg.setControlProperty('HelpButton', 'Visible', False)
        except:
            pass
        
        #Add listener to set open size
        self.f_dlg = f_dlg
        try:
            f_dlg.Window.addWindowListener(self.WindowListener(self))
        except:
            pass
        
        
        #Set the current folder if it exists
        if os.path.exists(folder):
            f_url = uno.systemPathToFileUrl(folder)
            f_dlg.setDisplayDirectory(f_url)
        #Set the name 
        if dlg_mode == 'save' and name is not None:
            f_dlg.setDefaultName(name)
        #Set filters
        if filters is not None:
            for name, filter in filters:
                f_dlg.appendFilter(name, filter)
        #Get the selected file
        if f_dlg.execute() == 1:
            f = f_dlg.SelectedFiles
        f_dlg.dispose()
        return f
        
        
    class WindowListener(unohelper.Base, XWindowListener):
        '''Window resizing'''
        def __init__(self, parent):
            self.parent = parent
            
        def disposing(self, ev): pass
        def windowMoved(self, ev): pass
        def windowShown(self, ev): 
            'Set the pos and size'
            try:
                self.parent.f_dlg.Window.setPosSize(0, 0, self.parent.POS_SIZE[2], self.parent.POS_SIZE[3], SIZE)
            except:
                logger.warn(traceback.format_exc())
                
        def windowHidden(self, ev):
            'Get the pos and size'
            try:
                ps = self.parent.POS_SIZE
                pos_size = self.parent.f_dlg.Window.Size
                self.parent.POS_SIZE = 0, 0, pos_size.Width, pos_size.Height
            except:
                logger.error('Error when hiding window.')
                logger.debug(traceback.format_exc())
        
        def windowResized(self, ev): pass
        

def get_selected_folder_path(ctx, path):
    'Return a user selected path'
    dlg = FolderPickerDlg(ctx, None, Title = 'Select file')
    url = dlg.execute(path)
    
    if url is None or url == '':
        return None

    path = uno.fileUrlToSystemPath(url)
    return path
        
class FolderPickerDlg(object):
    """Folder selection dialog wrapper around LibreOffice's native folder picker.
    
    Properties:
        POS_SIZE: (0, 0, 800, 600) - Default picker dimensions
        DISPOSE: True - Dialog gets disposed after closing
        
    Methods:
        execute(folder=os.getcwd()): 
            Shows folder picker starting at specified path
            Returns selected folder path or None if cancelled
    """
    
    POS_SIZE = 0, 0, 800, 600
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'Select folder', **props):
        self.ctx = ctx
        self.cast = cast
        self._dialog = DialogFake(True)
        
        
    def execute(self, folder = os.getcwd()):
        f = None
        #Create dialog instance
        f_dlg = self.ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.ui.dialogs.FolderPicker", self.ctx)
        self.f_dlg = f_dlg
        #Hide the help button    
        f_dlg.setControlProperty('HelpButton', 'Visible', False)
        #Set the current folder if it exists
        if os.path.exists(folder):
            f_url = uno.systemPathToFileUrl(folder)
            f_dlg.setDisplayDirectory(f_url)
            
        f_dlg.Window.addWindowListener(self.WindowListener(self))
            
        #Get the selected file
        if f_dlg.execute() == 1:
            f = f_dlg.getDirectory()
            
        f_dlg.dispose()
        
        return f
        
    class WindowListener(unohelper.Base, XWindowListener):
        '''Window resizing'''
        def __init__(self, parent):
            self.parent = parent
            
        def disposing(self, ev): pass
        def windowMoved(self, ev): pass
        def windowShown(self, ev): 
            'Set the pos and size'
            try:
                self.parent.f_dlg.Window.setPosSize(0, 0, self.parent.POS_SIZE[2], self.parent.POS_SIZE[3], SIZE)
            except:
                logger.warn(traceback.format_exc())
                
        def windowHidden(self, ev):
            'Get the pos and size'
            try:
                ps = self.parent.POS_SIZE
                pos_size = self.parent.f_dlg.Window.Size
                self.parent.POS_SIZE = 0, 0, pos_size.Width, pos_size.Height
            except:
                logger.error('Error when hiding window.')
                logger.debug(traceback.format_exc())
        
        def windowResized(self, ev): pass
     
     
     
class ColorPickerDlg(object):
    """Color selection dialog wrapper around LibreOffice's native color picker.
    
    Properties:
        POS_SIZE: (0, 0, 800, 600) - Default picker dimensions
        DISPOSE: True - Dialog gets disposed after closing
        
    Methods:
        execute(color, parent_window):
            Shows color picker with initial color
            Returns selected color value or None if cancelled
    """
    
    POS_SIZE = 0, 0, 800, 600
    DISPOSE = True
    
    def __init__(self, ctx, cast, Title = 'Select a color', **props):
        self.ctx = ctx
        self.cast = cast
        self._dialog = DialogFake(True)
        
        
    def execute(self, color, parent_window):
        'Return selected color'
        #Create dialog instance
        
        #Get the system type and use java color picker if it is Windows
        #At some point we should check into why it is crashing with
        # the libreoffice dialog
        logger.debug("My system is %s" % platform.system())
        
        if platform.system() == "Windows":
            logger.debug("Using Java color chooser")
            tools = self.ctx.getServiceManager().createInstance("kptools.KpTools")
            
            new_color = tools.chooseColor(color)
            #Returns -1 if user cancels
            if new_color == -1:
                return None
            return new_color
        else:
            logger.debug("Using Libreoffice color chooser")
            
            dlg = self.ctx.getServiceManager().createInstanceWithArgumentsAndContext(
                "com.sun.star.ui.dialogs.ColorPicker", (parent_window,), self.ctx)
                
            #Initialize color
            args = (PropertyValue(), )
            args[0].Name = "Color"
            args[0].Value = color
            dlg.setPropertyValues(args)
            
            #Execute dialog
            if dlg.execute() != 1:
                #User canceled
                return None 
                
            #Return color
            props = dlg.getPropertyValues()
            return props[0].Value


class DialogList:
    """Registry of all available dialogs in this module.
    
    Maintains a mapping of dialog names to their corresponding classes.
    Used by the main dialog system to instantiate dialogs by name.
    
    Dialog registry:
        - NameInput: Text input dialog
        - ValueInput: Numeric input dialog
        - ConfirmYes: Confirmation dialog
        - FilePicker: File selection dialog
        - FolderPicker: Folder selection dialog
        - ColorPicker: Color selection dialog
    """
    def __init__(self):
        self.dialogs = {
            'NameInput': NameInputDlg,
            'ValueInput': ValueInputDlg,
            'ConfirmYes': ConfirmYesDlg,
            'FilePicker': FilePickerDlg,
            'FolderPicker': FolderPickerDlg,
            'ColorPicker': ColorPickerDlg,
        }


        
        
        
        
