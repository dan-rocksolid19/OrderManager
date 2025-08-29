'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''


import uno
import unohelper

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex.dialogs.misc_dialogs import FilePickerDlg

from com.sun.star.awt import XWindowListener
from com.sun.star.beans import NamedValue, PropertyValue

import logging, traceback
logger = logging.getLogger(__name__)


class ExampleDialog(DialogBase):
    
    POS_SIZE = 0, 0, 260, 180
    DISPOSE = False
    
    def __init__(self, ctx, cast, **props):
        DialogBase.__init__(self, ctx, cast, **props)
    
    def _create(self):
        'Create method'
        self.add_ok_cancel()
        x, y = 15, 10
        self.add_groupbox('infobox', x-4, y, 240, 120, Label = 'Company info', FontWeight = 110)
        y += 10
        self.add_label('NameLabel', x, y, 100, 11, Label = '~Name:')
        self.add_edit('name', x, y+13, 150, 13)
        y += 33
        self.add_label('Phone1Label', x, y, 70, 11, Label = "Phone 1:")
        self.add_edit('phone1', x, y+13, 70, 13)
        self.add_label('Phone2Label', x+80, y, 70, 11, Label = "Phone 2:")
        self.add_edit('phone2', x+80, y+13, 70, 13)
        self.add_label('FaxLabel', x+160, y, 70, 11, Label = "Fax:")
        self.add_edit('fax', x+160, y+13, 70, 13)
        
        #Path example
        y += 40
        self.add_label('pathLocLabel', x, y, 50, 11, Label = 'Path location:')
        y += 13
        ctr = self.add_edit('path_location', x, y, 200, 11)
        
        self.add_button('browse_path_loc', x + 210, y, 15, 13, Label = '...', callback = self.browse_path_clicked)
        y += 22
        
        
    def select_file(self, base_path,  filters = (('Image files', '*.png'), ('All files', '*'))):
        ''' Select a folder from the file system '''
        dlg = FilePickerDlg(self.ctx, self.cast)
        return dlg.execute(base_path,  filters = filters)
        
            
    def browse_path_clicked(self, ev):
        'Browse icon button clicked'
        ctr = self._controls['path_location']
        f = self.select_file(ctr.Text)
        if f is not None and len(f) > 0:
            ctr.Text = uno.fileUrlToSystemPath(f[0])
        
    def _prepare(self):
        'Prepare dialog for display'
        self.clear_values()
        self.set_values(self._values)
        #Must be called here
        self._controls['name'].setFocus()
    
    def _done(self, ret):
        if ret == 1:
            self.get_values()
        return ret, self._values
    
    def execute(self, values):
        self._values = values.copy()
        return DialogBase.execute(self)
        
        