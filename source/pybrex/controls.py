#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Dialog controls
# Created: 7/27/2018
# Copyright (C) 2018, Timothy Hoover




import uno
import unohelper
import traceback

from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.grid import GridBase
from librepy.pybrex.listeners import Listeners
from librepy.pybrex.uno_date_time_converters import (
    uno_time_to_python,
    uno_date_to_python,
    python_time_to_uno,
    python_date_to_uno
)

import logging
logger = logging.getLogger(__name__)


class Controls(Listeners):
    def __init__(self, ctx=None, smgr=None):
        self._controls = {}
        self._pages = {}
        self._data_types = {}
        self._values = DataRow()
        self.format = '0 ##/##'
        self.ctx = ctx
        self.smgr = smgr
        Listeners.__init__(self)
        
    def get_ctr_str_value(self, ctr):
        'Get effective value from control'
        v = ctr.Model.EffectiveValue
        if v is None:
            return ""
        else:
            return str(v)
        
    def get_ctr_int_value(self, ctr):
        'Get effective value from control'
        v = ctr.Model.EffectiveValue
        if v is None:
            return 0
        else:
            return int(v)
        get_ctr_float_val
    def get_ctr_float_value(self, ctr):
        'Get effective value from control'
        v = ctr.Model.EffectiveValue
        if v is None:
            return 0.0
        else:
            return float(v)
            
    def set_ctr_value(self, ctr, value):
        ctr.Model.EffectiveValue = value
    
    def get_values(self):
        for key, ctr in self._controls.items():
            if key in self._data_types and key in self._values:
                dt = self._data_types[key]
                if dt == 'str':
                    self._values[key] = ctr.getText()
                elif dt in ('int', 'long'):
                    self._values[key] = int(ctr.getValue())
                elif dt in ( 'double', 'float'):
                    self._values[key] = float(ctr.getValue())
                elif dt == 'e_str':
                    self._values[key] = self.get_ctr_str_value(ctr)
                elif dt in ('e_int', 'e_long'):
                    self._values[key] = self.get_ctr_int_value(ctr)
                elif dt in ('e_double', 'e_float'):
                    self._values[key] = self.get_ctr_float_value(ctr)
                elif dt == 'time':
                    self._values[key] = uno_time_to_python(ctr.getTime())
                elif dt == 'date':
                    self._values[key] = uno_date_to_python(ctr.getDate())
                elif dt == 'check':
                    self._values[key] = bool(ctr.getState())
                elif dt == 'option' or dt == 'int_check':
                    self._values[key] = ctr.getState()
                elif dt == 'item':
                    self._values[key] = ctr.getSelectedItem()
        return self._values
                    
    def set_values(self, values):
        
        for key, value in values.items():
            if key in self._controls and key in self._data_types:
                ctr = self._controls[key]
                dt = self._data_types[key]
                if dt == 'str':
                    ctr.setText(value)
                elif dt in ('long', 'int', 'double', 'float'):
                    ctr.setValue(value)
                elif dt in ('e_str', 'e_long', 'e_float', 'e_int', 'e_double'):
                    ctr.Model.EffectiveValue = value
                elif dt == 'time':
                    ctr.setTime(python_time_to_uno(value))
                elif dt == 'date':
                    ctr.setDate(python_date_to_uno(value))
                elif dt == 'check':
                    ctr.setState(int(value))
                elif dt == 'option' or dt == 'int_check':
                    ctr.setState(value)
                elif dt == 'item':
                    ctr.selectItem(value, True)
                    
    def clear_values(self):
        for key, ctr in self._controls.items():
            if key in self._data_types:
                dt = self._data_types[key]
                if dt == 'str':
                    ctr.setText('')
                elif dt in ('int', 'long', 'double', 'float'):
                    ctr.setValue(0)
                elif dt in ('e_str', 'e_long', 'e_float', 'e_int', 'e_double'):
                    ctr.Model.EffectiveValue = 0
                elif dt == 'time':
                    ctr.setEmpty()
                elif dt == 'date':
                    ctr.setEmpty()
                elif dt == 'check' or dt == 'int_check':
                    ctr.setState(0)
                elif dt == 'option':
                    ctr.setState(False)
                #elif dt == 'item':
                    #ctr.selectItem(value, True)
    
    def add_control(self, s_type, name, x, y, width, height, page = None, **props):
        '''Add a control to the dialog'''
        if page is not None:
            dlg = page
            model = page.Model
        else:
            dlg = self._dialog
            model = self._dialog_model
        #create the control
        ctr_mod = model.createInstance(s_type)
        #set the controls properties
        ctr_mod.setPropertyValues(
                ("Height", "PositionX", "PositionY", "Width", "Name" ),
                (height, x, y, width, name))
        if len(props) > 0:
            ctr_mod.setPropertyValues(tuple(props.keys()), tuple(props.values()))
        #insert the control
        model.insertByName(name, ctr_mod)
        return dlg.getControl(name)
    
    def add_button(self, name, x, y, width, height, callback = None, **props):
        ctr = self.add_control("com.sun.star.awt.UnoControlButtonModel", name, x, y, width, height, **props)
        if callback is not None:
            self.add_action_listener(ctr, callback)
        self._controls[name] = ctr
        return ctr
        
    def add_ok(self, name, x, y, width, height, **props):
        return self.add_button(name, x, y, width, height, 
            DefaultButton = True, Label = 'OK', PushButtonType = 1, **props)
            
    def add_cancel(self, name, x, y, width, height, **props):
        self._controls[name] = self.add_button(name, x, y, width, height,
            Label = 'Cancel', PushButtonType = 2, **props)
        return self._controls[name]
            
    def add_ok_cancel(self, px = None):
        width, height = self.POS_SIZE[2], self.POS_SIZE[3]
        if px is None: px = width - 90
        b1 = self.add_ok('OkayButton', px, height - 20, 40, 15)
        b2 = self.add_cancel('CancelButton', px + 43, height - 20, 40, 15)
        self._controls['OkayButton'] = b1
        self._controls['CancelButton'] = b2
        return b1, b2
            
    def add_done(self, px = None):
        width, height = self.POS_SIZE[2], self.POS_SIZE[3]
        if px is None: px = width - 60
        b1 = self.add_button('DoneButton', px, height - 20, 50, 15, Label = "Done", PushButtonType = 2)
        self._controls['DoneButton'] = b1
        return b1
        
    def add_label(self, name, x, y, width, height, **props):
        self._controls[name] = self.add_control("com.sun.star.awt.UnoControlFixedTextModel", name, x, y, width, height, **props)
        return self._controls[name]
        
    def add_check(self, name, x, y, width, height, callback = None, data_type = 'check', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlCheckBoxModel", name, x, y, width, height, **props)
        if callback is not None:
            self.add_item_listener(self._controls[name], callback)
        return self._controls[name]
    add_checkbox = add_check
        
    def add_list(self, name, x, y, width, height, data_type = 'list', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlListBoxModel", name, x, y, width, height, **props)
        return self._controls[name]
    add_listbox = add_list
            
    def add_combo(self, name, x, y, width, height, data_type = 'str', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlComboBoxModel", name, x, y, width, height, **props)
        return self._controls[name]
    add_combobox = add_combo
    
    def add_radio(self, name, x, y, width, height, callback = None, data_type = 'option', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlRadioButtonModel", name, x, y, width, height, **props)
        if callback is not None:
            self.add_item_listener(self._controls[name], callback)
        return self._controls[name]
    add_option = add_radio
            
    def add_line(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlFixedLineModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_numeric(self, name, x, y, width, height, data_type = 'float', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlNumericFieldModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_edit(self, name, x, y, width, height, data_type = 'str', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlEditModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_date(self, name, x, y, width, height, data_type = 'date', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlDateFieldModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_format(self, name, x, y, width, height, format = None, data_type = 'e_float', **props):
        if data_type:
            self._data_types[name] = data_type
        ctr = self.add_control("com.sun.star.awt.UnoControlFormattedFieldModel", name, x, y, width, height, **props)
        if format:
            self.set_format(ctr.Model, format)
        elif self.format:
            self.set_format(ctr.Model, self.format)
        self._controls[name] = ctr
        return ctr
            
    def add_time(self, name, x, y, width, height, data_type = 'time', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlTimeFieldModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_currency(self, name, x, y, width, height, data_type = 'float', **props):
        if data_type:
            self._data_types[name] = data_type
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlCurrencyFieldModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_scrollbar(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlScrollBarModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_progressbar(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlProgressBarModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_image(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlImageControlModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_groupbox(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoControlGroupBoxModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_tree(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.tree.TreeControlModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_page_container(self, name, x, y, width, height, **props):
        self._controls[name] =  self.add_control("com.sun.star.awt.UnoMultiPageModel", name, x, y, width, height, **props)
        return self._controls[name]
            
    def add_grid(self, name, x, y, width, height, titles, page = None, **props):
        if not self.ctx:
            raise RuntimeError("Context not set. Set provide ctx in constructor")
        
        if not self.smgr:
            self.smgr = self.ctx.ServiceManager
            
        g_base = GridBase(self.ctx, self.smgr)
        
        grid_ctr, grid_model = g_base.create_grid_dialog(name, x, y, width, height, titles, self._dialog, self._dialog_model, page, **props)
        
        self._controls[name] = grid_ctr
        
        return g_base, self._controls[name]
        
    """Inserts tab pages into the tab page container"""
    def add_page(self, pageContainer, name, title):
        pageModel = pageContainer.Model.createInstance("com.sun.star.awt.UnoPageModel")
        #pageModel.BackgroundColor = 0xF6F5F4
        pageModel.initialize(())
        pageModel.Title = title
        #Add the tab page to the container
        pageContainer.Model.insertByName(name, pageModel)
        page = pageContainer.getControl(name)
        self._pages[name] = page
        return page   

    def set_format(self, Control,  sFormat):
        #get the locale
        oLocale = uno.createUnoStruct("com.sun.star.lang.Locale")
        #get the format supplier
        oSupplier = self.create_service("com.sun.star.util.NumberFormatsSupplier")
        Control.FormatsSupplier = oSupplier
        oSupplier = Control.FormatsSupplier
        oFormats = oSupplier.getNumberFormats()
        #See if the number format exists by obtaining the key.
        nKey = oFormats.queryKey(sFormat, oLocale, True)
        # If the number format does not exist, add it.
        if (nKey == -1) :
            nKey = oFormats.addNew(sFormat, oLocale)
            # If it failed to add, and it should not fail to add, then use zero.
            if (nKey == -1) :
                nKey = 0
        #Now, set the key for the desired formatting.
        Control.FormatKey = nKey
    
    def get_control(self, name):
        return self._dialog.getControl(name)
    
    def get_model(self, name):
        return self._dialog_model.getByName(name)


class DataRow(dict):
        
    def __getattr__(self, name):
        return super().__getitem__(name)
        
    def __setattr__(self, name, value):
        super().__setitem__(name)
        
    def __delattr__(self, name):
        super().__delitem__(name)
