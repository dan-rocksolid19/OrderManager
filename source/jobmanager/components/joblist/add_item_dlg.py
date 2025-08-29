import uno
import traceback
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox

class AddItemDialog(DialogBase):
    
    POS_SIZE = 0, 0, 220, 240
    DISPOSE = True
    
    def __init__(self, parent, ctx, smgr, frame, ps, edit_mode=False, item_data=None, **props):
        self.edit_mode = edit_mode
        self.item_data = item_data or {}
        self.item_result = None
        self.listeners = listeners.Listeners()
        super().__init__(ctx, smgr, **props)
        self.parent = parent
        self.logger = parent.logger
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger.info("AddItemDialog initialized")
        
    def _create(self):
        title = "Edit Item" if self.edit_mode else "Add Item"
        self._dialog.Title = title

        label_height = 15
        field_height = 20
        field_width = 120
        label_width = 50
        start_x = 20
        start_y = 20
        row_spacing = 35

        self.add_label("lbl_item_number", start_x, start_y, label_width, label_height,
                      Label="Item Number:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.item_number = self.add_edit("ItemNumber", start_x + label_width + 10, start_y, field_width, field_height)

        self.add_label("lbl_product_service", start_x, start_y + row_spacing, label_width, label_height,
                      Label="Product/Service:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.product_service = self.add_edit("ProductService", start_x + label_width + 10, start_y + row_spacing, field_width, field_height)

        self.add_label("lbl_quantity", start_x, start_y + row_spacing * 2, label_width, label_height,
                      Label="Quantity:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.quantity = self.add_numeric("Quantity", start_x + label_width + 10, start_y + row_spacing * 2, field_width, field_height, 
                                        data_type='float', DecimalAccuracy=2, ValueMin=0.01, ValueMax=999999)

        self.add_label("lbl_unit_price", start_x, start_y + row_spacing * 3, label_width, label_height,
                      Label="Unit Price:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.unit_price = self.add_currency("UnitPrice", start_x + label_width + 10, start_y + row_spacing * 3, field_width, field_height,
                                           data_type='float', ValueMin=0.01, ValueMax=999999, 
                                           CurrencySymbol="$", PrependCurrencySymbol=True)

        self.add_label("lbl_total", start_x, start_y + row_spacing * 4, label_width, label_height,
                      Label="Total:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.total = self.add_label("Total", start_x + label_width + 10, start_y + row_spacing * 4, field_width, label_height,
                                   Label="$0.00", FontHeight=12, FontWeight=120, Align=0, VerticalAlign=2)

        button_y = start_y + row_spacing * 5 + 10
        button_width = 80
        button_height = 25
        button_spacing = 10
        
        total_width = button_width * 2 + button_spacing
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.save_btn = self.add_button("SaveButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                       Label="Add", callback=self.save_item,
                                       BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

        self.listeners.add_focus_listener(self.quantity, lost=self.calculate_total)
        self.listeners.add_focus_listener(self.unit_price, lost=self.calculate_total)

    def _prepare(self):
        if self.edit_mode and self.item_data:
            self.item_number.Text = str(self.item_data.get('item_number', ''))
            self.product_service.Text = self.item_data.get('product_service', '')
            
            quantity_str = self.item_data.get('quantity', '0')
            try:
                self.quantity.setValue(float(quantity_str))
            except ValueError:
                self.quantity.setValue(1.0)
            
            unit_price_str = self.item_data.get('unit_price', '0')
            if unit_price_str.startswith('$'):
                unit_price_str = unit_price_str[1:]
            try:
                self.unit_price.setValue(float(unit_price_str))
            except ValueError:
                self.unit_price.setValue(0.0)
                
            self.calculate_total()

    def calculate_total(self, event=None):
        try:
            quantity = self.quantity.getValue()
            unit_price = self.unit_price.getValue()
            
            if quantity > 0 and unit_price > 0:
                total = quantity * unit_price
                self.total.Model.Label = f"${total:.2f}"
            else:
                self.total.Model.Label = "$0.00"
        except Exception as e:
            self.logger.error(f"Error calculating total: {e}")
            self.total.Model.Label = "$0.00"

    def save_item(self, event):
        if not self.validate_fields():
            return
        
        try:
            quantity = self.quantity.getValue()
            unit_price = self.unit_price.getValue()
            total = quantity * unit_price
            
            self.item_result = {
                'item_number': self.item_number.Text.strip(),
                'product_service': self.product_service.Text.strip(),
                'quantity': str(int(quantity)) if quantity.is_integer() else str(quantity),
                'unit_price': f"${unit_price:.2f}",
                'total': f"${total:.2f}"
            }
            
            self.end_execute(1)
            
        except Exception as e:
            self.logger.error(f"Error saving item: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error saving item: {e}", "Error")

    def validate_fields(self):
        if not self.item_number.Text.strip():
            msgbox("Item Number is required.", "Validation Error")
            return False
        
        if not self.product_service.Text.strip():
            msgbox("Product/Service is required.", "Validation Error")
            return False
        
        try:
            quantity = self.quantity.getValue()
            if quantity <= 0:
                msgbox("Quantity must be greater than 0.", "Validation Error")
                return False
        except Exception:
            msgbox("Please enter a valid quantity.", "Validation Error")
            return False
        
        try:
            unit_price = self.unit_price.getValue()
            if unit_price <= 0:
                msgbox("Unit Price must be greater than 0.", "Validation Error")
                return False
        except Exception:
            msgbox("Please enter a valid unit price.", "Validation Error")
            return False
        
        return True

    def get_item_data(self):
        return self.item_result

    def dispose(self):
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc()) 