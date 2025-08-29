import traceback
from decimal import Decimal

from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.ca_link.data import item_dao
from librepy.ca_link.ui.quantity_dialog import QuantityDialog


class ItemSelectorDialog(DialogBase):
    POS_SIZE = 0, 0, 750, 400

    def __init__(self, parent, ctx, smgr, frame, ps, pre_selected_item_numbers=None, current_items_data=None, **props):
        self.listeners = listeners.Listeners()
        super().__init__(ctx, smgr, **props)
        self.parent = parent
        self.logger = getattr(parent, "logger", None)
        self.dao = item_dao.ItemDAO(self.logger)
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.selected_items = []
        self.available_data = []
        self.all_available_data = []
        self.selected_data = []
        self.pre_selected_item_numbers = pre_selected_item_numbers or []
        self.current_items_data = current_items_data or []

    def _create(self):
        self._dialog.Title = "Select CA Item"
        
        # Available items grid (left side)
        grid_start_x = 20
        available_grid_y = 50
        available_grid_width = 300
        available_grid_height = 300
        
        self.add_label("lbl_available", grid_start_x, available_grid_y, 90, 15, Label="Available Items", FontHeight=12, FontWeight=150)
        
        # Search bar and button - inline with Available Items label, positioned to the right
        search_x = grid_start_x + 110
        search_y = available_grid_y
        search_width = 120
        search_height = 15
        self.search_edit = self.add_edit("SearchEdit", search_x, search_y, search_width, search_height)
        self.btn_search = self.add_button("SearchButton", search_x + search_width + 5, search_y, 60, 15, Label="Search", callback=self.on_search, FontWeight=150)
        
        # OK/Cancel buttons - positioned in top right
        button_width = 80
        button_height = 20
        button_spacing = 10
        ok_x = self.POS_SIZE[2] - (button_width * 2 + button_spacing + 20)
        cancel_x = ok_x + button_width + button_spacing
        self.ok_btn = self.add_ok("OkButton", ok_x, 15, button_width, button_height, BackgroundColor=0x4A90E2, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        self.cancel_btn = self.add_cancel("CancelButton", cancel_x, 15, button_width, button_height, BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.available_grid, self.available_grid_model = self.add_grid(
            "AvailableGrid",
            grid_start_x,
            available_grid_y + 20,
            available_grid_width,
            available_grid_height,
            titles=[
                ("Item #", "item_number", 60, 1),
                ("Product/Service", "item_name", 120, 1),
                ("Description", "salesdesc", 80, 1),
                ("Price", "price", 40, 1),
            ],
        )
        self.listeners.add_mouse_listener(self.available_grid_model, pressed=self.on_available_grid_double_click)
        
        # Add/Remove buttons (center)
        button_center_x = grid_start_x + available_grid_width + 15
        button_center_y = available_grid_y + 100
        
        self.btn_add = self.add_button("AddButton", button_center_x, button_center_y, 60, 25, 
                                      Label="Add →", callback=self.add_item,
                                      BackgroundColor=0x4A90E2, TextColor=0xFFFFFF, FontHeight=11, FontWeight=150)
        
        self.btn_remove = self.add_button("RemoveButton", button_center_x, button_center_y + 35, 60, 25,
                                         Label="← Remove", callback=self.remove_item,
                                         BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11, FontWeight=150)
        
        # Selected items grid (right side)
        selected_grid_x = button_center_x + 80
        selected_grid_width = 320
        
        self.add_label("lbl_selected", selected_grid_x, available_grid_y, 150, 15, Label="Selected Items", FontHeight=12, FontWeight=150)
        
        self.add_label("lbl_selected_help", selected_grid_x + selected_grid_width - 220, available_grid_y, 200, 12, Label="Double-click to edit the quantity", FontHeight=10, FontSlant=1, Align=2, VerticalAlign=2)
        
        self.selected_grid, self.selected_grid_model = self.add_grid(
            "SelectedGrid",
            selected_grid_x,
            available_grid_y + 20,
            selected_grid_width,
            available_grid_height - 5,
            titles=[
                ("Item #", "item_number", 50, 1),
                ("Product/Service", "item_name", 100, 1),
                ("Qty", "quantity", 40, 1),
                ("Unit Price", "unit_price", 70, 1),
                ("Total", "total", 60, 1),
            ],
        )
        self.listeners.add_mouse_listener(self.selected_grid_model, pressed=self.on_selected_grid_double_click)

    def _prepare(self):
        self.load_initial()
        self.load_pre_selected_items()

    def load_initial(self):
        try:
            self.all_available_data = self.dao.search_items(limit=200)
            for d in self.all_available_data:
                d["price"] = f"${float(d['price']):.2f}"
            self.refresh_available_items()
            self.selected_grid.set_data(self.selected_data, heading="item_number")
        except Exception as e:
            if self.logger:
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
            msgbox(str(e), "Error")
    
    def refresh_available_items(self):
        """Filter available items to exclude already selected items"""
        selected_item_numbers = {item["item_number"] for item in self.selected_data}
        self.available_data = [
            item for item in self.all_available_data 
            if item["item_number"] not in selected_item_numbers
        ]
        self.available_grid.set_data(self.available_data, heading="item_number")
    
    def load_pre_selected_items(self):
        """Load items that were pre-selected based on item numbers"""
        if not self.pre_selected_item_numbers:
            return
            
        try:
            current_items_by_number = {item.get('item_number'): item for item in self.current_items_data}
            
            for item_number in self.pre_selected_item_numbers:
                ca_items = self.dao.search_items(term=item_number, limit=10)
                
                for ca_item in ca_items:
                    if ca_item["item_number"] == item_number:
                        current_item = current_items_by_number.get(item_number, {})
                        
                        current_qty = current_item.get('quantity', '1')
                        current_unit_price = current_item.get('unit_price', f"${float(ca_item['price']):.2f}")
                        
                        unit_price_val = Decimal(str(current_unit_price).replace('$', '').replace(',', ''))
                        qty_val = Decimal(str(current_qty).replace(',', ''))
                        total_val = qty_val * unit_price_val
                        
                        selected_item = {
                            "item_number": ca_item["item_number"],
                            "item_name": ca_item["item_name"],
                            "salesdesc": ca_item["salesdesc"],
                            "quantity": str(current_qty),
                            "unit_price": f"${unit_price_val:.2f}",
                            "total": f"${total_val:.2f}",
                            "price": unit_price_val,
                            "item_source": "CA"
                        }
                        self.selected_data.append(selected_item)
                        break
            
            if self.selected_data:
                self.selected_grid.set_data(self.selected_data, heading="item_number")
                self.refresh_available_items()
                if self.logger:
                    self.logger.info(f"Pre-populated {len(self.selected_data)} items in CA selector")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading pre-selected items: {e}")
                self.logger.error(traceback.format_exc())

    def on_search(self, ev):
        term = self.search_edit.Text
        try:
            self.all_available_data = self.dao.search_items(term=term, limit=200)
            for d in self.all_available_data:
                d["price"] = f"${float(d['price']):.2f}"
            self.refresh_available_items()
        except Exception as e:
            if self.logger:
                self.logger.error(e)
                self.logger.error(traceback.format_exc())
            msgbox(str(e), "Error")

    def on_available_grid_double_click(self, ev):
        """Handle double-click on available items grid"""
        if ev.Buttons != 1 or ev.ClickCount != 2:
            return
        self.add_item(ev)
        
    def on_selected_grid_double_click(self, ev):
        """Handle double-click on selected items grid to edit quantity"""
        if ev.Buttons != 1 or ev.ClickCount != 2:
            return
        row = self.selected_grid_model.getCurrentRow()
        if row == -1:
            return
        heading = self.selected_grid._data_model.getRowHeading(row)
        for d in self.selected_data:
            if d["item_number"] == heading:
                current_qty = Decimal(str(d["quantity"]).replace(',', ''))
                dlg = QuantityDialog(self, self.ctx, self.smgr, self.frame, self.ps, initial_quantity=current_qty)
                ret = dlg.execute()
                if ret == 1:
                    qty = dlg.get_quantity()
                    price_val = Decimal(str(d["price"]).replace("$", ""))
                    d["quantity"] = str(qty)
                    d["unit_price"] = f"${price_val:.2f}"
                    d["total"] = f"${qty * price_val:.2f}"
                    self.selected_grid.set_data(self.selected_data, heading="item_number")
                break
                
    def add_item(self, ev):
        """Add selected item from available grid to selected grid"""
        row = self.available_grid_model.getCurrentRow()
        if row == -1:
            return
        heading = self.available_grid._data_model.getRowHeading(row)
        for d in self.available_data:
            if d["item_number"] == heading:
                dlg = QuantityDialog(self, self.ctx, self.smgr, self.frame, self.ps, initial_quantity=None)
                ret = dlg.execute()
                if ret == 1:
                    qty = dlg.get_quantity()
                    price_val = Decimal(str(d["price"]).replace("$", ""))
                    total = qty * price_val
                    
                    selected_item = {
                        "item_number": d["item_number"],
                        "item_name": d["item_name"],
                        "salesdesc": d["salesdesc"],
                        "quantity": str(qty),
                        "unit_price": f"${price_val:.2f}",
                        "total": f"${total:.2f}",
                        "price": price_val,
                        "item_source": "CA"
                    }
                    
                    self.selected_data.append(selected_item)
                    self.selected_grid.set_data(self.selected_data, heading="item_number")
                    self.refresh_available_items()
                break
                
    def remove_item(self, ev):
        """Remove selected item from selected grid"""
        row = self.selected_grid_model.getCurrentRow()
        if row == -1:
            return
        heading = self.selected_grid._data_model.getRowHeading(row)
        self.selected_data = [d for d in self.selected_data if d["item_number"] != heading]
        self.selected_grid.set_data(self.selected_data, heading="item_number")
        self.refresh_available_items()

    def _done(self, ret):
        if ret == 1:
            if not self.selected_data:
                msgbox("Please select at least one item.", "No Items Selected")
                return 0
            
            # Transform selected_data to the format expected by Quote dialog
            self.selected_items = []
            for d in self.selected_data:
                self.selected_items.append({
                    "item_number": d["item_number"],
                    "product_service": d["item_name"],
                    "salesdesc": d["salesdesc"],
                    "quantity": d["quantity"],
                    "unit_price": d["unit_price"],
                    "total": d["total"],
                    "item_source": "CA"
                })
        return ret 