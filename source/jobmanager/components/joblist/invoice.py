import traceback
from datetime import datetime
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.jobmanager.data.invoice_dao import InvoiceDAO
import uno
import os
from librepy.pybrex.values import GRAPHICS_DIR

class Invoice(DialogBase):
    
    POS_SIZE = 0, 0, 510, 460
    DISPOSE = True
    
    def __init__(self, parent, ctx, smgr, frame, ps, invoice_id=None, **props):
        # Set logger before calling parent constructor
        self.listeners = listeners.Listeners()
        # Get cached icon URL from component manager
        if hasattr(parent, 'component_manager') and parent.component_manager:
            self.copy_past_icon = parent.component_manager.get_cached_icon_url('copy_arrow_right.png')
        else:
            # Fallback to direct loading (might not work if document is closed)
            self.copy_past_icon = uno.systemPathToFileUrl(os.path.join(GRAPHICS_DIR, "copy_arrow_right.png"))
        super().__init__(ctx, smgr, **props)
        self.parent = parent
        self.logger = parent.logger
        self.invoice_dao = InvoiceDAO(self.logger)
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.invoice_id = invoice_id
        self.items_data = []
        self.logger.info("Invoice dialog initialized")
        
    def _create(self):
        self._dialog.Title = "Invoice"

        # Title (no action buttons at top for Invoice)
        self.add_label("lbl_invoice", 20, 10, 100, 20, Label="Invoice", FontHeight=22, FontWeight=150)

        # Customer Information Section
        section_y = 45
        label_height = 15
        label_width = 50
        label_spacing = 15
        field_height = 15
        field_width = 130
        field_spacing = 30
        column1_x = 30
        column2_x = 190
        column3_x = 365
        row_spacing = label_height + field_height + 5
        row1 = 60
        row2 = row1 + row_spacing
        row3 = row2 + row_spacing
        row4 = row3 + row_spacing
        
        # Customer Information Section (Left Column)
        self.add_groupbox("lbl_customer_info", 20, section_y, 150, 157,
                      Label="Customer Information", FontHeight=14, FontWeight=150)
        
        # Customer Name
        self.add_label("lbl_customer_name", column1_x, row1, field_width, label_height, 
                      Label="Customer Name", FontHeight=12, FontWeight=120)
        self.customer_name = self.add_edit("CustomerName", column1_x, row1 + label_spacing, field_width, field_height)
        
        # Company Name  
        self.add_label("lbl_company_name", column1_x, row2, field_width, label_height,
                      Label="Company Name", FontHeight=12, FontWeight=120)
        self.company_name = self.add_edit("CompanyName", column1_x, row2 + label_spacing, field_width, field_height)
        
        # Phone Number
        self.add_label("lbl_phone_number", column1_x, row3, field_width, label_height,
                      Label="Phone Number", FontHeight=12, FontWeight=120)
        self.phone_number = self.add_edit("PhoneNumber", column1_x, row3 + label_spacing, field_width, field_height)
        
        # Email
        self.add_label("lbl_email", column1_x, row4, field_width, label_height,
                      Label="Email", FontHeight=12, FontWeight=120)
        self.email = self.add_edit("Email", column1_x, row4 + label_spacing, field_width, field_height)

        # Billing Address Section (Middle Column)
        self.add_groupbox("lbl_billing_address", column2_x - 10, section_y, 150, 157,
                      Label="Billing Address", FontHeight=14, FontWeight=150)
        
        # Billing Address fields
        self.add_label("lbl_billing_addr", column2_x, row1, field_width, label_height,
                      Label="Address", FontHeight=12, FontWeight=120)
        self.billing_address = self.add_edit("BillingAddress", column2_x, row1 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_billing_city", column2_x, row2, field_width, label_height,
                      Label="City", FontHeight=12, FontWeight=120)
        self.billing_city = self.add_edit("BillingCity", column2_x, row2 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_billing_state", column2_x, row3, field_width, label_height,
                      Label="State", FontHeight=12, FontWeight=120)
        self.billing_state = self.add_edit("BillingState", column2_x, row3 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_billing_zip", column2_x, row4, field_width, label_height,
                      Label="Zip Code", FontHeight=12, FontWeight=120)
        self.billing_zip = self.add_edit("BillingZip", column2_x, row4 + label_spacing, field_width, field_height)

        self.copy_past_btn = self.add_image("btnCopyPast", 335, row2 + 10, 15, 15,
                                             ImageURL=self.copy_past_icon,
                                             ScaleImage=True)
        
        self.listeners.add_mouse_listener(self.copy_past_btn, pressed=self.copy_paste)


        # Site Location Section (Right Column)
        self.add_groupbox("lbl_site_location", column3_x - 10, section_y, 150, 157,
                      Label="Site Location", FontHeight=14, FontWeight=150)
        
        # Site Location fields
        self.add_label("lbl_site_addr", column3_x, row1, field_width, label_height,
                      Label="Address", FontHeight=12, FontWeight=120)
        self.site_address = self.add_edit("SiteAddress", column3_x, row1 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_site_city", column3_x, row2, field_width, label_height,
                      Label="City", FontHeight=12, FontWeight=120)
        self.site_city = self.add_edit("SiteCity", column3_x, row2 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_site_state", column3_x, row3, field_width, label_height,
                      Label="State", FontHeight=12, FontWeight=120)
        self.site_state = self.add_edit("SiteState", column3_x, row3 + label_spacing, field_width, field_height)
        
        self.add_label("lbl_site_zip", column3_x, row4, field_width, label_height,
                      Label="Zip Code", FontHeight=12, FontWeight=120)
        self.site_zip = self.add_edit("SiteZip", column3_x, row4 + label_spacing, field_width, field_height)

        #########################################################
        # Items Section                                        #
        #########################################################
        
        items_y = row4 + 47
        items_x = column1_x + 25
        
        self.add_label("lbl_items", items_x, items_y, 100, 20,
                      Label="Items", FontHeight=16, FontWeight=150)
        
        # Add Item button (right side)
        button_width = 80
        button_height = 20
        add_item_x = self.POS_SIZE[2] - button_width - 20
        
        self.btn_add_item = self.add_button("btnAddItem", add_item_x, items_y, button_width, button_height,
                                           Label="+ Add Item", callback=self.add_item,
                                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        
        # Items grid
        grid_y = items_y + 25
        grid_height = 100
        grid_width = 400
        
        self.items_grid, self.items_grid_model = self.add_grid("grdItems", items_x, grid_y, grid_width, grid_height,
            titles=[
                ("Item #", "item_number", 60, 1),
                ("Product/Service", "product_service", 180, 1),
                ("Qty", "quantity", 50, 1),
                ("Unit Price", "unit_price", 70, 1),
                ("Total", "total", 70, 1)
            ]
        )
        
        # Add double-click listener to the items grid
        self.listeners.add_mouse_listener(self.items_grid_model, pressed=self.on_item_double_click)

        # Notes Section - Private Notes comes first in Invoice
        notes_y = grid_y + grid_height + 15
        notes_width = 395
        notes_height = 20
        
        self.add_label("lbl_private_notes", items_x, notes_y, 120, label_height,
                      Label="Private Notes", FontHeight=12, FontWeight=120)
        self.private_notes = self.add_edit("PrivateNotes", items_x, notes_y + 10, notes_width, notes_height, MultiLine=True)
        notes_y += 35
        
        self.add_label("lbl_notes", items_x, notes_y, 100, label_height,
                      Label="Notes", FontHeight=12, FontWeight=120)
        self.notes = self.add_edit("Notes", items_x, notes_y + 10, notes_width, notes_height, MultiLine=True)

        # Bottom buttons
        button_y = notes_y + 40
        button_width = 80
        button_height = 25
        button_spacing = 20
        
        # Center the three buttons
        total_width = button_width * 3 + button_spacing * 2
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.print_btn = self.add_button("PrintButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                        Label="Save & Print", callback=self.print_invoice,
                                        BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.save_pdf_btn = self.add_button("SavePDFButton", center_x + (button_width + button_spacing) * 2, button_y, button_width, button_height,
                                           Label="Save as PDF", callback=self.save_as_pdf,
                                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

    def _prepare(self):
        if self.invoice_id:
            self.load_invoice_data()
            self.print_btn.Model.Label = "Update & Print"
            self.print_btn.Model.BackgroundColor = 0x4A90E2  # Blue for update
        else:
            # Set default values for new invoice
            self.load_sample_items()
    
    def load_sample_items(self):
        """Load sample items for demonstration"""
        self.items_data = []
        self.items_grid.set_data(self.items_data, heading='item_number')
    
    def copy_paste(self, event):
        self.logger.info("Copy Past clicked")
        self.site_address.Text = self.billing_address.Text
        self.site_city.Text = self.billing_city.Text
        self.site_state.Text = self.billing_state.Text
        self.site_zip.Text = self.billing_zip.Text

    # Item management callbacks
    def add_item(self, event):
        """Handle add item button click"""
        self.logger.info("Add Item clicked")
        try:
            from librepy.jobmanager.components.joblist.add_item_dlg import AddItemDialog
            
            dialog = AddItemDialog(self, self.ctx, self.smgr, self.frame, self.ps)
            result = dialog.execute()
            
            if result == 1:
                item_data = dialog.get_item_data()
                if item_data:
                    item_data["item_source"] = "manual"
                    self.items_data.append(item_data)
                    self.items_grid.set_data(self.items_data, heading='item_number')
                    self.logger.info(f"Added item: {item_data['item_number']}")
            
            dialog.dispose()
            
        except Exception as e:
            self.logger.error(f"Error opening add item dialog: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error opening add item dialog: {e}", "Error")
    
    def on_item_double_click(self, event):
        """Handle double-click events on the items grid"""
        try:
            if event.Buttons == 1 and event.ClickCount == 2:
                row = self.items_grid_model.getCurrentRow()
                if row == -1:
                    return
                selected_id = self.items_grid._data_model.getRowHeading(row)
                if selected_id:
                    self.logger.info(f"Double-clicked item: {selected_id}")
                    
                    selected_item = None
                    selected_index = -1
                    
                    for i, item in enumerate(self.items_data):
                        if item.get('item_number') == selected_id:
                            selected_item = item
                            selected_index = i
                            break
                    
                    if selected_item:
                        from librepy.jobmanager.components.joblist.add_item_dlg import AddItemDialog
                        
                        dialog = AddItemDialog(self, self.ctx, self.smgr, self.frame, self.ps, 
                                             edit_mode=True, item_data=selected_item)
                        result = dialog.execute()
                        
                        if result == 1:
                            updated_item = dialog.get_item_data()
                            if updated_item:
                                updated_item["item_source"] = selected_item.get("item_source", "manual")
                                self.items_data[selected_index] = updated_item
                                self.items_grid.set_data(self.items_data, heading='item_number')
                                self.logger.info(f"Updated item: {updated_item['item_number']}")
                        
                        dialog.dispose()
        except Exception as e:
            self.logger.error(f"Error handling item double-click: {e}")
            self.logger.error(traceback.format_exc())
    
    # Main action button callbacks
    def print_invoice(self, event):
        """Handle print/save button click"""
        self.logger.info("Print/Save Invoice clicked")
        
        if not self._validate_invoice_fields():
            return
        
        if not self._save_invoice_if_needed():
            return
        
        try:
            from librepy.jasper_reports.print_doc import print_doc
            print_doc(self.invoice_id, "Invoice")
            self.logger.info(f"Successfully printed invoice {self.invoice_id}")
            self.end_execute(1)
        except Exception as print_error:
            self.logger.error(f"Error printing invoice: {print_error}")
            msgbox(f"Invoice saved successfully, but printing failed: {print_error}", "Print Warning")
    
    def save_as_pdf(self, event):
        """Handle save as PDF button click"""
        self.logger.info("Save as PDF clicked")
        
        if not self._validate_invoice_fields():
            return
        
        if not self._save_invoice_if_needed():
            return
        
        try:
            from librepy.jasper_reports.print_doc import save_doc_as_pdf
            save_doc_as_pdf(self.invoice_id, "Invoice")
            self.logger.info(f"Successfully saved invoice {self.invoice_id} as PDF")
            self.end_execute(1)
        except Exception as pdf_error:
            self.logger.error(f"Error saving invoice as PDF: {pdf_error}")
            msgbox(f"Invoice saved successfully, but PDF generation failed: {pdf_error}", "PDF Warning")
    
    def create_invoice(self):
        """Create a new invoice in the database"""
        try:
            self.logger.info("Creating new invoice...")
            
            document_id = self.invoice_dao.create_invoice_with_customer_and_address(
                customer_name=self.customer_name.Text,
                phone_number=self.phone_number.Text,
                company_name=self.company_name.Text,
                email=self.email.Text,
                billing_address_line=self.billing_address.Text,
                billing_city=self.billing_city.Text,
                billing_state=self.billing_state.Text,
                billing_zip_code=self.billing_zip.Text,
                site_address_line=self.site_address.Text,
                site_city=self.site_city.Text,
                site_state=self.site_state.Text,
                site_zip_code=self.site_zip.Text,
                notes=self.notes.Text,
                private_notes=self.private_notes.Text
            )
            
            if document_id:
                self.invoice_id = document_id
                self.logger.info(f"Invoice created with document ID: {self.invoice_id}")
                self._save_items()
            else:
                msgbox("Failed to create invoice.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error creating invoice: {e}", "Error")
    
    def update_invoice(self):
        """Update existing invoice in the database"""
        try:
            self.logger.info(f"Updating invoice ID: {self.invoice_id}")
            
            success = self.invoice_dao.update_invoice_with_customer_and_address(
                document_id=self.invoice_id,
                customer_name=self.customer_name.Text,
                phone_number=self.phone_number.Text,
                company_name=self.company_name.Text,
                email=self.email.Text,
                billing_address_line=self.billing_address.Text,
                billing_city=self.billing_city.Text,
                billing_state=self.billing_state.Text,
                billing_zip_code=self.billing_zip.Text,
                site_address_line=self.site_address.Text,
                site_city=self.site_city.Text,
                site_state=self.site_state.Text,
                site_zip_code=self.site_zip.Text,
                notes=self.notes.Text,
                private_notes=self.private_notes.Text
            )
            
            if success:
                self.invoice_dao.delete_items_by_document(self.invoice_id)
                self._save_items()
                self.logger.info("Invoice updated successfully")
            else:
                msgbox("Failed to update invoice.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error updating invoice: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error updating invoice: {e}", "Error")
    
    def load_invoice_data(self):
        """Load existing invoice data from database"""
        try:
            invoice_data = self.invoice_dao.get_invoice_by_document_id(self.invoice_id)
            
            if invoice_data:
                customer = invoice_data['customer']
                billing_address = invoice_data['billing_address']
                site_address = invoice_data['site_address']
                invoice = invoice_data['invoice']
                document = invoice_data['document']
                
                # Populate form fields
                self.customer_name.Text = customer.customer_name or ''
                self.company_name.Text = customer.company_name or ''
                self.phone_number.Text = customer.phone_number or ''
                self.email.Text = customer.email or ''
                
                # Billing address
                if billing_address:
                    self.billing_address.Text = billing_address.address_line or ''
                    self.billing_city.Text = billing_address.city or ''
                    self.billing_state.Text = billing_address.state or ''
                    self.billing_zip.Text = billing_address.zip_code or ''
                
                # Site location
                if site_address:
                    self.site_address.Text = site_address.address_line or ''
                    self.site_city.Text = site_address.city or ''
                    self.site_state.Text = site_address.state or ''
                    self.site_zip.Text = site_address.zip_code or ''
                
                # Notes
                self.notes.Text = document.notes or ''
                self.private_notes.Text = document.private_notes or ''
                
                # Load invoice items
                self.load_invoice_items()
                
                self.logger.info(f"Loaded invoice data for ID: {self.invoice_id}")
            else:
                self.logger.warning(f"No data found for invoice ID: {self.invoice_id}")
                
        except Exception as e:
            self.logger.error(f"Error loading invoice data: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error loading invoice data: {e}", "Error")
    
    def load_invoice_items(self):
        """Load invoice items from database"""
        try:
            items = self.invoice_dao.get_invoice_items(self.invoice_id)
            
            # Convert to grid format
            self.items_data = []
            for item in items:
                item_dict = {
                    'item_number': str(item['item_number']),
                    'product_service': item['product_service'],
                    'quantity': str(item['quantity']),
                    'unit_price': f"${float(item['unit_price']):.2f}",
                    'total': f"${float(item['total']):.2f}"
                }
                self.items_data.append(item_dict)
            
            # Load data into the items grid
            self.items_grid.set_data(self.items_data, heading='item_number')
            self.logger.info(f"Loaded {len(self.items_data)} invoice items")
            
        except Exception as e:
            self.logger.error(f"Error loading invoice items: {e}")
            self.logger.error(traceback.format_exc())

    def _validate_invoice_fields(self):
        """Validate required fields for invoice operations"""
        if not self.customer_name.Text.strip():
            msgbox("Customer Name is required.", "Validation Error")
            return False
        
        if not self.phone_number.Text.strip():
            msgbox("Phone Number is required.", "Validation Error")
            return False
        
        if not self.items_data:
            msgbox("At least one item is required.", "Validation Error")
            return False
        
        return True

    def _save_invoice_if_needed(self):
        """Save the invoice if needed (create new or update existing)"""
        if self.invoice_id:
            self.update_invoice()
        else:
            self.create_invoice()
        return self.invoice_id is not None

    def _save_items(self):
        """Save items to database"""
        for item in self.items_data:
            item_number = item.get('item_number')
            product_service = item.get('product_service')
            quantity_str = str(item.get('quantity', '0')).replace(',', '')
            unit_price_str = str(item.get('unit_price', '')).replace('$', '').replace(',', '')
            
            try:
                quantity_val = float(quantity_str)
            except ValueError:
                quantity_val = 0.0
            
            try:
                unit_price_val = float(unit_price_str)
            except ValueError:
                unit_price_val = 0.0
            
            self.invoice_dao.add_invoice_item(
                self.invoice_id, 
                item_number, 
                product_service, 
                quantity_val, 
                unit_price_val
            )
