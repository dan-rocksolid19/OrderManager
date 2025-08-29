import traceback
from decimal import Decimal
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.jobmanager.data.job_dao import JobDAO

class ItemsHoursDialog(DialogBase):
    POS_SIZE = 0, 0, 550, 400
    DISPOSE = True

    def __init__(self, parent, ctx, smgr, frame, ps, job_id=None, **props):
        self.parent = parent
        self.logger = parent.logger
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.job_id = job_id
        self.job_dao = JobDAO(self.logger)
        self.listeners = listeners.Listeners()
        super().__init__(ctx, smgr, **props)
        self.items_data = []
        self.hours_data = []

    def _create(self):
        print("ItemsHoursDialog._create")
        self._dialog.Title = "Items & Hours"
        button_width = 100
        button_height = 22
        section_label_x = 25
        section_label_y = 10

        self.add_label("lbl_items", section_label_x, section_label_y, 250, 20, Label="Item Used On Job (For Job Costing)", FontHeight=18, FontWeight=150)

        add_item_x = self.POS_SIZE[2] - button_width - 40
        self.btn_add_item = self.add_button("btnAddItem", add_item_x, section_label_y, button_width, button_height, Label="+ Add Item", callback=self.add_item, BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)

        grid_y = section_label_y + 25
        grid_height = 100
        grid_width = self.POS_SIZE[2] - section_label_x * 2
        self.items_grid, self.items_grid_model = self.add_grid("grdItems", section_label_x, grid_y, grid_width, grid_height, 
            titles=[
                ("Item", "item_number", 150, 1),
                ("Product/Service", "product_service", 150, 1),
                ("Qty", "quantity", 60, 1), 
                ("Price", "unit_price", 80, 1), 
                ("Sub-total", "total", 90, 1)
            ]
        )
        total_y = grid_y + grid_height + 5*2

        self.add_label("lbl_items_total", self.POS_SIZE[2] - 180, total_y, 40, 18, Label="Total", FontHeight=11, FontWeight=120, Align = 2)
        self.items_total = self.add_edit("ItemsTotal", self.POS_SIZE[2] - 130, total_y, 90, 18, ReadOnly=True)
        sep_y = total_y + 30
        self.add_line("line_sep1", section_label_x, sep_y, self.POS_SIZE[2] - section_label_x * 2, 2)
        hours_label_y = sep_y + 10

        self.add_label("lbl_hours", section_label_x, hours_label_y, 100, 20, Label="Hours", FontHeight=18, FontWeight=150)
        self.btn_add_hours = self.add_button("btnAddHours", add_item_x, hours_label_y, button_width, button_height, Label="+ Add Hours", callback=self.add_hours, BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        hours_grid_y = hours_label_y + 25
        self.hours_grid, self.hours_grid_model = self.add_grid("grdHours", section_label_x, hours_grid_y, grid_width, grid_height,
            titles=[
                ("Employee", "employee", 120, 1), 
                ("Start Date", "start_date", 80, 1), 
                ("End Date", "end_date", 80, 1), 
                ("Hours", "hours", 50, 1), 
                ("Rate", "rate", 70, 1), 
                ("Total", "total", 70, 1)
            ]
        )
        hours_total_y = hours_grid_y + grid_height + 5

        self.add_label("lbl_hours_total", self.POS_SIZE[2] - 180, hours_total_y, 40, 18, Label="Total", FontHeight=11, FontWeight=120, Align = 2)
        self.hours_total = self.add_edit("HoursTotal", self.POS_SIZE[2] - 130, hours_total_y, 90, 18, ReadOnly=True)

        bottom_y = hours_total_y + 15
        buttons_total = 220
        center_x = (self.POS_SIZE[2] - buttons_total) // 2
        self.cancel_btn = self.add_cancel("CancelButton", center_x, bottom_y + 25, 100, 28, BackgroundColor=0xA0A0A0, TextColor=0xFFFFFF, FontHeight=12, FontWeight=150)
        self.save_btn = self.add_button("SaveButton", center_x + 120, bottom_y + 25, 100, 28, Label="Save", callback=self.save_action, BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=12, FontWeight=150)

    def _prepare(self):
        if self.job_id:
            try:
                data = self.job_dao.get_items_and_hours(self.job_id)
                self.items_data = data.get("items", [])
                self.hours_data = data.get("hours", [])
                
                # Convert decimal values to strings for grid display
                for item in self.items_data:
                    if isinstance(item.get('total'), Decimal):
                        item['total'] = f"${float(item['total']):.2f}"
                    if isinstance(item.get('product_service'), Decimal):
                        item['product_service'] = str(item['product_service'])
                    if isinstance(item.get('unit_price'), Decimal):
                        item['unit_price'] = f"${float(item['unit_price']):.2f}"
                    if isinstance(item.get('quantity'), Decimal):
                        item['quantity'] = f"{float(item['quantity']):.2f}"
                
                for entry in self.hours_data:
                    if isinstance(entry.get('total'), Decimal):
                        entry['total'] = f"${float(entry['total']):.2f}"
                    if isinstance(entry.get('rate'), Decimal):
                        entry['rate'] = f"${float(entry['rate']):.2f}"
                    if isinstance(entry.get('hours'), Decimal):
                        entry['hours'] = f"{float(entry['hours']):.2f}"
                    # Convert dates to strings
                    if entry.get('start_date'):
                        entry['start_date'] = entry['start_date'].strftime('%Y-%m-%d')
                    if entry.get('end_date'):
                        entry['end_date'] = entry['end_date'].strftime('%Y-%m-%d')
                
                self.items_grid.set_data(self.items_data, heading="id")
                self.hours_grid.set_data(self.hours_data, heading="id")
                totals = self.job_dao.totals(self.job_id)
                self.items_total.Text = f"${float(totals['items_total']):.2f}"
                self.hours_total.Text = f"${float(totals['hours_total']):.2f}"
            except Exception as e:
                self.logger.error(f"Error loading items/hours: {e}")
                self.logger.error(traceback.format_exc())
                msgbox(f"Error loading data: {e}", "Error")

    def add_item(self, event):
        """Handle add item manually button click"""
        self.logger.info("Add Item Manually clicked")
        try:
            from librepy.jobmanager.components.joblist.add_item_dlg import AddItemDialog
            
            dialog = AddItemDialog(self, self.ctx, self.smgr, self.frame, self.ps)
            result = dialog.execute()
            
            if result == 1:
                item_data = dialog.get_item_data()
                if item_data:
                    # Add to items_data array and update grid
                    self.items_data.append(item_data)
                    self.items_grid.set_data(self.items_data, heading='item_number')
                    self.logger.info(f"Added item: {item_data['item_number']}")
            
            dialog.dispose()
            
        except Exception as e:
            self.logger.error(f"Error opening add item dialog: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error opening add item dialog: {e}", "Error")

    def add_hours(self, event):
        """Handle add hours manually button click"""
        self.logger.info("Add Hours Manually clicked")
        try:
            from librepy.jobmanager.components.joblist.add_hours_dlg import AddHoursDialog
            dlg = AddHoursDialog(self, self.ctx, self.smgr, self.frame, self.ps)
            if dlg.execute() == 1:
                hours_data = dlg.get_hours_data()
                if hours_data:
                    # Add to hours_data array and update grid
                    self.hours_data.append(hours_data)
                    self.hours_grid.set_data(self.hours_data, heading='employee')
                    self.logger.info(f"Added hours: {hours_data['employee']}")
                    
            dlg.dispose()
        except Exception as e:
            self.logger.error(f"Error opening add hours dialog: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error opening add hours dialog: {e}", "Error")

    def go_back(self, event):
        self.end_execute(0)

    def print_report(self, event):
        msgbox("Print not implemented yet.", "Info")

    def save_pdf(self, event):
        msgbox("Save as PDF not implemented yet.", "Info")

    def save_action(self, event):
        try:
            # Delete existing items and hours first
            self.job_dao.delete_items_by_document(self.job_id)
            self.job_dao.delete_hours_by_document(self.job_id)
            
            # Save new items and hours
            self._save_items()
            self._save_hours()
            self.end_execute(1)
        except Exception as e:
            self.logger.error(f"Error saving items and hours: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error saving items and hours: {e}", "Error")

    def _save_items(self):
        for itm in self.items_data:
            num = itm.get('item_number')
            svc = itm.get('product_service')
            qty_str = str(itm.get('quantity', '0')).replace(',', '')
            up_str = str(itm.get('unit_price', '')).replace('$', '').replace(',', '')
            try:
                qty_val = float(qty_str)
            except ValueError:
                qty_val = 0.0
            try:
                up_val = float(up_str)
            except ValueError:
                up_val = 0.0
            self.job_dao.add_job_item(self.job_id, num, svc, qty_val, up_val)
            self.logger.info(f"Added item: {num} {svc} {qty_val} {up_val}")

    def _save_hours(self):
        for hrs in self.hours_data:
            emp = hrs.get('employee')
            start_date = hrs.get('start_date')
            end_date = hrs.get('end_date')
            hrs_str = str(hrs.get('hours', '0')).replace(',', '')
            rate_str = str(hrs.get('rate', '')).replace('$', '').replace(',', '')
            try:
                hrs_val = float(hrs_str)
            except ValueError:
                hrs_val = 0.0
            try:
                rate_val = float(rate_str)
            except ValueError:
                rate_val = 0.0
            self.job_dao.add_job_hours(self.job_id, emp, start_date, end_date, hrs_val, rate_val)

    def dispose(self):
        try:
            if hasattr(self, "container"):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc()) 