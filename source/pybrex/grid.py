#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Grid control module
# Created: 7/28/2018
# Copyright (C) 2018, Timothy Hoover


from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.values import GRID_HEADER_BG_COLOR, GRID_ROW_BG_COLOR1, GRID_ROW_BG_COLOR2
from com.sun.star.awt.MouseButton import LEFT as MB_LEFT
from com.sun.star.awt.PosSize import POSSIZE

import logging
logger = logging.getLogger(__name__)



class GridBase(object):
    '''
    column types
    1: Regular text
    2: Boolean Yes/No
    3: Text with new line characters
    '''
    
    def __init__(self, ctx, smgr, **props):
        self.ctx = ctx
        self.smgr = smgr
        self.current_row = None
        self.mouse_doubleclick_fn = None
        self.color1 = GRID_ROW_BG_COLOR1
        self.color2 = GRID_ROW_BG_COLOR2
        if 'color1' in props:
            self.color1 = props['color1']
        if 'color2' in props:
            self.color2 = props['color2']

    def _build_default_props(self, name, x, y, width, height, **props):
        d = {
            "Name": name,
            "Height": height,
            "PositionX": x,
            "PositionY": y,
            "Width": width,
            "Border": 1,
            "HScroll": True,
            "VScroll": True,
            "SelectionModel": 1,
            "UseGridLines": True,
            "HeaderBackgroundColor": GRID_HEADER_BG_COLOR,
            "ShowColumnHeader": True,
            "ShowRowHeader": False
        }
        d.update(props)
        return d

    def _initialise_data_model(self, grid_model):
        dm = grid_model.GridDataModel
        if not dm:
            dm = self.smgr.createInstanceWithContext("com.sun.star.awt.grid.DefaultGridDataModel", self.ctx)
            grid_model.GridDataModel = dm
        return dm

    def _create_columns(self, titles):
        columns = self.smgr.createInstanceWithContext("com.sun.star.awt.grid.DefaultGridColumnModel", self.ctx)
        for title in titles:
            column = self.smgr.createInstanceWithContext("com.sun.star.awt.grid.GridColumn", self.ctx)
            column.Title = title[0]
            column.ColumnWidth = title[2]
            columns.addColumn(column)
        return columns

    def create_grid(self, name, x, y, width, height, titles, **props):        
        '''Create a grid control and set the columns'''
        self.titles = titles

        grid_model = self.smgr.createInstanceWithContext("com.sun.star.awt.grid.UnoControlGridModel", self.ctx)
        grid_ctr = self.smgr.createInstanceWithContext("com.sun.star.awt.grid.UnoControlGrid", self.ctx)
        grid_ctr.setModel(grid_model)

        self._model = grid_model
        self._ctr = grid_ctr

        self.default_props = self._build_default_props(name, x, y, width, height, **props)

        grid_model.setPropertyValues(
            tuple(self.default_props.keys()),
            tuple(self.default_props.values())
        )

        grid_model.RowBackgroundColors = (self.color1, self.color2)

        grid_ctr.setPosSize(x, y, width, height, POSSIZE)

        self._data_model = self._initialise_data_model(grid_model)
        
        columns = self._create_columns(titles)

        grid_model.ColumnModel = columns

        return grid_ctr, grid_model
    
    def create_grid_dialog(self, name, x, y, width, height, titles, dialog=None, dialog_model=None, page=None, **props):
        self.titles = titles

        grid_model = dialog_model.createInstance("com.sun.star.awt.grid.UnoControlGridModel")

        self.default_props = self._build_default_props(name, x, y, width, height, **props)

        grid_model.setPropertyValues(
            tuple(self.default_props.keys()),
            tuple(self.default_props.values())
        )

        grid_model.RowBackgroundColors = (self.color1, self.color2)
        self._data_model = self._initialise_data_model(grid_model)
        
        columns = self._create_columns(titles)

        grid_model.ColumnModel = columns

        if page is not None:
            page.Model.insertByName(name, grid_model)
            grid_ctr = page.getControl(name)
        else:
            dialog_model.insertByName(name, grid_model)
            grid_ctr = dialog.getControl(name)

        self._ctr = grid_ctr
        self._model = grid_model

        return grid_ctr, grid_model

    def set_data(self, data, heading = 'id', clear=True, resort = True):
        'Set data to grid'
        dm = self._data_model
        if resort:
            #Save the current sort
            sort_props = dm.getCurrentSortOrder()
        if clear:
            #Clear the grid
            dm.removeAllRows()
        rows = []
        headings = []
        for data_row in data:
            if heading:
                headings.append(data_row[heading])
            row = []
            for title in self.titles:
                row.append(self.data_value(data_row, title))
            rows.append(tuple(row))
        rows = tuple(rows)
        if heading:
            headings = tuple(headings)
        else:
            headings = tuple(["%s" % i for i in range(len(data))])
        #Add data to grid
        dm.addRows(headings, rows)
        
        if resort:
            #Resort columns
            if sort_props.First > 0:
                dm.sortByColumn(sort_props.First, sort_props.Second)
                
    def clear(self):
        self._data_model.removeAllRows()
        
    def data_value(self, data, title):
        if title[3] == 1:
            return data[title[1]]
        elif title[3] == 2:
            v = data[title[1]]
            if v: return 'Y'
            else: return 'N'
        elif title[3] == 3:
            return data[title[1]].replace('\n', ', ')
            
    def active_row_heading(self):
        try:
            selected_rows = self._ctr.getSelectedRows()
            if isinstance(selected_rows, tuple) and len(selected_rows) > 0:
                row = self._ctr.getCurrentRow()
                if row >= 0 and row < self._data_model.RowCount:
                    self.current_row = row
                    return self._data_model.getRowHeading(row)
            self.current_row = None
            return None
        except:
            self.current_row = None
            return None
            
    def reload(self, data):
        self.set_data(data, heading = 'id', clear = True)
            
    def update(self, data):
        if self.current_row is None:
            return False
        columns = tuple([i for i,t in enumerate(self.titles)])
        values = []
        for t in self.titles:
            values.append(self.data_value(data, t))
        values = tuple(values)
        
        self._data_model.updateRowData(columns, self.current_row, values)
        return True
            
    def delete(self):
        if self.current_row is None:
            return False
        self._data_model.removeRow(self.current_row)
        return True
        
    def add(self, data, heading):
        values = []
        for t in self.titles:
            values.append(self.data_value(data, t))
        self._data_model.addRow(heading, tuple(values))
        
    def set_last_line_color(self, color):
        colors = []
        for i in range(0, self._data_model.RowCount - 1, 2):
            colors += [self.color1, self.color2]
        if len(colors) == self._data_model.RowCount and len(colors) > 0:
            colors.pop()
        colors.append(color)
        self._model.RowBackgroundColors = tuple(colors)
        
    def mouse_doubleclicked(self, ev):
        '''Mouse double clicked function'''
        if self.mouse_doubleclick_fn is None:
            return
        #Use only correct button
        if not ev.Buttons == MB_LEFT:
            return
        #Use only double click
        if not ev.ClickCount == 2:
            return
        #Use only if actually clicked on a row
        row = self._ctr.getRowAtPoint(ev.X, ev.Y)
        row = self._ctr.getRowAtPoint(ev.X, ev.Y)
        if row == -1:
            return
        #Run the callback function
        self.mouse_doubleclick_fn(ev)
