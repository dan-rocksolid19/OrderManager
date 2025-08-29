import uno
import os
import traceback
import pathlib
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox, confirm_action
from librepy.jobmanager.data.quote_dao import QuoteDAO
from librepy.utils import project_folder_manager
from librepy.ca_link.ui.item_selector_dialog import ItemSelectorDialog
from librepy.pybrex.values import GRAPHICS_DIR

class Quote(DialogBase):
    
    POS_SIZE = 0, 0, 510, 460
    DISPOSE = True
    
    def __init__(self, parent, ctx, smgr, frame, ps, quote_id=None, **props):
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
        self.quote_dao = QuoteDAO(self.logger)
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.quote_id = quote_id
        self.items_data = []  # Store items data separately
        self.project_folder = None
        self.photo_dir = None
        self.doc_dir = None
        self.logger.info("Quote dialog initialized")
        
    def _create(self):
        self._dialog.Title = "Quote"

        # Title and action buttons at the top
        self.add_label("lbl_quote", 20, 10, 100, 20, Label="Quote", FontHeight=22, FontWeight=150)
        
        # Top action buttons (right side)
        button_width = 80
        button_height = 20
        button_spacing = 5
        start_x = self.POS_SIZE[2] - (button_width * 3 + button_spacing * 2 + 20)
        start_y = 10
        
        self.btn_attach_photos = self.add_button("btnAttachPhotos", start_x, start_y, button_width, button_height, 
                                                 Label="Attach Photos", callback=self.attach_photos,
                                                 BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        
        self.btn_attach_documents = self.add_button("btnAttachDocuments", start_x + button_width + button_spacing, start_y, button_width, button_height,
                                                   Label="Attach Documents", callback=self.attach_documents,
                                                   BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        
        self.btn_convert_job = self.add_button("btnConvertJob", start_x + (button_width + button_spacing) * 2, start_y, button_width, button_height,
                                              Label="Convert to Job", callback=self.convert_to_job,
                                              BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)

        # Customer Information Section
        section_y = 45
        label_height = 15
        label_width = 50
        field_height = 15
        field_width = 130
        label_spacing = 15
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
        
        self.btn_add_item_manually = self.add_button("btnAddItemManually", start_x + button_width + button_spacing, items_y, button_width, button_height,
                                                    Label="+ Add Item Manually", callback=self.add_item_manually,
                                                    BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        
        self.btn_add_item_ca = self.add_button("btnAddItemCA", start_x + (button_width + button_spacing) * 2, items_y, button_width, button_height,
                                              Label="+ Add Item from CA", callback=self.add_item_from_ca,
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
                ("Total", "total", 70, 1),
                ("Source", "item_source", 0, 0)
            ]
        )
        
        # Add double-click listener to the items grid
        self.listeners.add_mouse_listener(self.items_grid_model, pressed=self.on_item_double_click)
        
        # Add right-click listener for context menu
        self.listeners.add_mouse_listener(self.items_grid_model, pressed=self.on_item_right_click)

        # Notes Section
        notes_y = grid_y + grid_height + 15
        notes_width = 395
        notes_height = 20
        
        self.add_label("lbl_notes", items_x, notes_y, 100, label_height,
                      Label="Notes", FontHeight=12, FontWeight=120)
        self.notes = self.add_edit("Notes", items_x, notes_y + 10, notes_width, notes_height, MultiLine=True)
        notes_y += 35
        
        self.add_label("lbl_private_notes", items_x, notes_y, 120, label_height,
                      Label="Private Notes", FontHeight=12, FontWeight=120)
        self.private_notes = self.add_edit("PrivateNotes", items_x, notes_y + 10, notes_width, notes_height, MultiLine=True)

        # Bottom buttons - using same dimensions and spacing as Request dialog
        button_y = notes_y + 40
        button_width = 80
        button_height = 25
        button_spacing = 20
        
        # Center the buttons
        total_width = button_width * 3 + button_spacing * 2
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.print_btn = self.add_button("PrintButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                        Label="Print", callback=self.print_quote,
                                        BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.save_pdf_btn = self.add_button("SavePDFButton", center_x + (button_width + button_spacing) * 2, button_y, button_width, button_height,
                                           Label="Save as PDF", callback=self.save_as_pdf,
                                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

    def _prepare(self):
        if self.quote_id:
            self.load_quote_data()
            self.print_btn.Model.BackgroundColor = 0x4A90E2  # Blue for update
        else:
            # Set default values for new quote
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

    def setup_project_folders(self, customer_name):
        """
        Set up project folders for the given customer name.
        
        Args:
            customer_name (str): The customer name to create folders for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not customer_name or not customer_name.strip():
                msgbox("Customer name is required to set up attachment folders.", "Validation Error")
                return False
            
            self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name.strip(), self.logger)
            self.logger.info(f"Project folders set up for customer: {customer_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up project folders: {e}")
            msgbox(f"Error setting up project folders: {e}", "Error")
            return False
    
    def copy_files_to_folder(self, file_urls, dest_folder, folder_type):
        """
        Copy files from file URLs to destination folder.
        
        Args:
            file_urls: List of file URLs from LibreOffice file picker
            dest_folder: pathlib.Path destination folder
            folder_type: String describing the folder type for user messages
        """
        try:
            copied_files = project_folder_manager.copy_files_to_folder(file_urls, dest_folder, folder_type, self.logger)
            if not copied_files:
                msgbox("No files were copied.", "No Files")
            else:
                self.logger.info(f"Successfully copied {len(copied_files)} file(s) to {folder_type} folder")
                
        except Exception as e:
            self.logger.error(f"Error copying files to {folder_type} folder: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error copying files to {folder_type} folder: {e}", "Error")
    
    # Top action button callbacks
    def attach_photos(self, event):
        """Handle attach photos button click"""
        self.logger.info("Attach Photos clicked")
        
        try:
            # Ensure project folders are set up
            if not self.photo_dir:
                self._refresh_project_folder()
            if not self.photo_dir:
                customer_name = self.customer_name.Text.strip()
                if not self.setup_project_folders(customer_name):
                    return
            
            # Create file picker for photos
            picker = self.ctx.getServiceManager().createInstanceWithContext(
                "com.sun.star.ui.dialogs.FilePicker", self.ctx
            )
            
            # Enable multiple selection
            picker.setMultiSelectionMode(True)
            
            # Set photo filters
            picker.appendFilter("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")
            picker.appendFilter("All files", "*.*")
            
            # Set initial directory to user's Pictures folder if it exists
            import os
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.exists(pictures_dir):
                import uno
                pictures_url = uno.systemPathToFileUrl(pictures_dir)
                picker.setDisplayDirectory(pictures_url)
            
            # Execute the picker
            if picker.execute() == 1:
                selected_files = picker.getSelectedFiles()
                if selected_files:
                    self.copy_files_to_folder(selected_files, self.photo_dir, "Photos")
            
            picker.dispose()
            
        except Exception as e:
            self.logger.error(f"Error in attach photos: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error attaching photos: {e}", "Error")
    
    def attach_documents(self, event):
        """Handle attach documents button click"""
        self.logger.info("Attach Documents clicked")
        
        try:
            # Ensure project folders are set up
            if not self.doc_dir:
                self._refresh_project_folder()
            if not self.doc_dir:
                customer_name = self.customer_name.Text.strip()
                if not self.setup_project_folders(customer_name):
                    return
            
            # Create file picker for documents
            picker = self.ctx.getServiceManager().createInstanceWithContext(
                "com.sun.star.ui.dialogs.FilePicker", self.ctx
            )
            
            # Enable multiple selection
            picker.setMultiSelectionMode(True)
            
            # Set document filters
            picker.appendFilter("Document files", "*.pdf;*.doc;*.docx;*.txt;*.rtf")
            picker.appendFilter("Spreadsheet files", "*.xls;*.xlsx;*.ods")
            picker.appendFilter("All files", "*.*")
            
            # Set initial directory to user's Documents folder if it exists
            import os
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(documents_dir):
                import uno
                documents_url = uno.systemPathToFileUrl(documents_dir)
                picker.setDisplayDirectory(documents_url)
            
            # Execute the picker
            if picker.execute() == 1:
                selected_files = picker.getSelectedFiles()
                if selected_files:
                    self.copy_files_to_folder(selected_files, self.doc_dir, "Documents")
            
            picker.dispose()
            
        except Exception as e:
            self.logger.error(f"Error in attach documents: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error attaching documents: {e}", "Error")
    
    def convert_to_job(self, event):
        """Handle convert to job button click"""
        self.logger.info("Convert to Job clicked")

        try:
            if not self.quote_id:
                if not self.customer_name.Text.strip():
                    msgbox("Customer Name is required before conversion.", "Validation Error")
                    return
                if not self.phone_number.Text.strip():
                    msgbox("Phone Number is required before conversion.", "Validation Error")
                    return

                self.create_quote()

                if not self.quote_id:
                    msgbox("Failed to create quote before conversion.", "Error")
                    return
            else:
                self.update_quote()

            job_document_id = self.quote_dao.convert_quote_to_job(self.quote_id)

            if job_document_id:
                self.end_execute(1)

                from librepy.jobmanager.components.joblist.job import Job
                job_dialog = Job(self.parent, self.ctx, self.smgr, self.frame, self.ps, job_id=job_document_id)
                job_dialog.execute()
            else:
                msgbox("Failed to convert quote to job.", "Conversion Error")

        except Exception as e:
            self.logger.error(f"Error converting quote to job: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error converting quote to job: {e}", "Conversion Error")
    
    # Item management callbacks
    def add_item_manually(self, event):
        """Handle add item manually button click"""
        self.logger.info("Add Item Manually clicked")
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
    
    def add_item_from_ca(self, event):
        """Handle add item from CA button click"""
        self.logger.info("Add Item from CA clicked")
        try:
            ca_items = [item for item in self.items_data if item.get('item_source') == 'CA']
            current_item_numbers = [item.get('item_number') for item in ca_items if item.get('item_number')]
            
            dialog = ItemSelectorDialog(self, self.ctx, self.smgr, self.frame, self.ps, 
                                      pre_selected_item_numbers=current_item_numbers,
                                      current_items_data=ca_items)
            result = dialog.execute()
            if result == 1 and dialog.selected_items:
                ca_item_numbers = [item.get('item_number') for item in dialog.selected_items]
                
                self.items_data = [item for item in self.items_data if item.get('item_source') != 'CA']
                
                self.items_data.extend(dialog.selected_items)
                self.items_grid.set_data(self.items_data, heading="item_number")
                self.logger.info(f"Updated items from CA selector: {len(dialog.selected_items)} item(s)")
        except Exception as e:
            self.logger.error(f"Error opening CA item selector: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error opening CA item selector: {e}", "Error")
    

    
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
    
    def on_item_right_click(self, event):
        """Handle right-click events on the items grid"""
        try:
            if event.Buttons == 2:
                row = self.items_grid_model.getCurrentRow()
                if row == -1:
                    return
                selected_id = self.items_grid._data_model.getRowHeading(row)
                if selected_id:
                    self.logger.info(f"Right-clicked item: {selected_id}")
                    
                    if confirm_action("Are you sure you want to delete this item?", "Delete Item"):
                        original_count = len(self.items_data)
                        self.items_data = [item for item in self.items_data if item.get('item_number') != selected_id]
                        
                        if len(self.items_data) < original_count:
                            self.items_grid.set_data(self.items_data, heading='item_number')
                            self.logger.info(f"Deleted item: {selected_id}")
                            msgbox("Item deleted successfully!", "Success")
                        else:
                            msgbox("Item not found.", "Error")
        except Exception as e:
            self.logger.error(f"Error handling item right-click: {e}")
            self.logger.error(traceback.format_exc())
    
    # Main action button callbacks
    def _save_quote_if_needed(self):
        """Save the quote if needed (create new or update existing)"""
        if self.quote_id:
            self.update_quote()
        else:
            self.create_quote()
        return self.quote_id is not None

    def _validate_quote_fields(self):
        """Validate required fields for quote operations"""
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

    def print_quote(self, event):
        """Handle print button click"""
        self.logger.info("Print Quote clicked")
        
        if not self._validate_quote_fields():
            return
        
        if not self._save_quote_if_needed():
            return
        
        try:
            from librepy.jasper_reports.print_doc import print_doc
            print_doc(self.quote_id, "Quote")
            self.logger.info(f"Successfully printed quote {self.quote_id}")
            self.end_execute(1)
        except Exception as print_error:
            self.logger.error(f"Error printing quote: {print_error}")
            msgbox(f"Quote saved successfully, but printing failed: {print_error}", "Print Warning")
    
    def save_as_pdf(self, event):
        """Handle save as PDF button click"""
        self.logger.info("Save as PDF clicked")
        
        if not self._validate_quote_fields():
            return
        
        if not self._save_quote_if_needed():
            return
        
        try:
            from librepy.jasper_reports.print_doc import save_doc_as_pdf
            save_doc_as_pdf(self.quote_id, "Quote")
            self.logger.info(f"Successfully saved quote {self.quote_id} as PDF")
        except Exception as pdf_error:
            self.logger.error(f"Error saving quote as PDF: {pdf_error}")
            msgbox(f"Quote saved successfully, but PDF generation failed: {pdf_error}", "PDF Warning")
    
    def create_quote(self):
        """Create a new quote in the database"""
        try:
            if not self.items_data:
                msgbox("At least one item is required.", "Validation Error")
                return

            self.logger.info("Creating new quote...")

            customer_name = self.customer_name.Text.strip()
            if not self.project_folder:
                if not self.setup_project_folders(customer_name):
                    return

            document_id = self.quote_dao.create_quote_with_customer_and_address(
                customer_name=customer_name,
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
                private_notes=self.private_notes.Text,
                project_folder=str(self.project_folder) if self.project_folder else None
            )
            
            if document_id:
                self.quote_id = document_id
                self.logger.info(f"Quote created with document ID: {self.quote_id}")
                self._save_items()
                self._refresh_project_folder()
            else:
                msgbox("Failed to create quote.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error creating quote: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error creating quote: {e}", "Error")
    
    def update_quote(self):
        """Update existing quote in the database"""
        try:
            if not self.items_data:
                msgbox("At least one item is required.", "Validation Error")
                return

            self.logger.info(f"Updating quote ID: {self.quote_id}")
            
            success = self.quote_dao.update_quote_with_customer_and_address(
                document_id=self.quote_id,
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
                private_notes=self.private_notes.Text,
                project_folder=str(self.project_folder) if self.project_folder else None
            )
            
            if success:
                self.quote_dao.delete_items_by_document(self.quote_id)
                self._save_items()
                self.logger.info("Quote updated successfully")
                self._refresh_project_folder()
            else:
                msgbox("Failed to update quote.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error updating quote: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error updating quote: {e}", "Error")
    
    def load_quote_data(self):
        """Load existing quote data from database"""
        try:
            quote_data = self.quote_dao.get_quote_by_document_id(self.quote_id)
            
            if quote_data:
                customer = quote_data['customer']
                billing_address = quote_data['billing_address']
                site_address = quote_data['site_address']
                quote = quote_data['quote']
                document = quote_data['document']
                
                self.customer_name.Text = customer.customer_name or ''
                self.company_name.Text = customer.company_name or ''
                self.phone_number.Text = customer.phone_number or ''
                self.email.Text = customer.email or ''
                
                if billing_address:
                    self.billing_address.Text = billing_address.address_line or ''
                    self.billing_city.Text = billing_address.city or ''
                    self.billing_state.Text = billing_address.state or ''
                    self.billing_zip.Text = billing_address.zip_code or ''
                
                if site_address:
                    self.site_address.Text = site_address.address_line or ''
                    self.site_city.Text = site_address.city or ''
                    self.site_state.Text = site_address.state or ''
                    self.site_zip.Text = site_address.zip_code or ''
                
                self.notes.Text = document.notes or ''
                self.private_notes.Text = document.private_notes or ''
                
                # Load project folder paths
                if hasattr(document, 'project_folder') and document.project_folder:
                    self.project_folder = pathlib.Path(document.project_folder)
                    self.photo_dir = self.project_folder / "Photos"
                    self.doc_dir = self.project_folder / "Documents"
                    self.logger.info(f"Loaded project folder: {self.project_folder}")
                else:
                    # If no project folder is stored, try to set up folders based on customer name
                    customer_name = customer.customer_name
                    if customer_name:
                        try:
                            self.setup_project_folders(customer_name.strip())
                        except Exception as e:
                            self.logger.warning(f"Could not set up project folders for existing quote: {e}")
                
                self.load_quote_items()
                
                self.logger.info(f"Loaded quote data for ID: {self.quote_id}")
            else:
                self.logger.warning(f"No data found for quote ID: {self.quote_id}")
                
        except Exception as e:
            self.logger.error(f"Error loading quote data: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error loading quote data: {e}", "Error")
    
    def load_quote_items(self):
        """Load quote items from database"""
        try:
            items = self.quote_dao.get_quote_items(self.quote_id)
            
            self.items_data = []
            for item in items:
                item_dict = {
                    'item_number': str(item['item_number']),
                    'product_service': item['product_service'],
                    'quantity': str(item['quantity']),
                    'unit_price': f"${float(item['unit_price']):.2f}",
                    'total': f"${float(item['total']):.2f}",
                    'item_source': item.get('item_source', 'manual')
                }
                self.items_data.append(item_dict)
            
            self.items_grid.set_data(self.items_data, heading='item_number')
            self.logger.info(f"Loaded {len(self.items_data)} quote items")
            
        except Exception as e:
            self.logger.error(f"Error loading quote items: {e}")
            self.logger.error(traceback.format_exc())

    def dispose(self):
        """Dispose of all controls"""
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())

    def _refresh_project_folder(self):
        if not self.quote_id:
            return False
        try:
            data = self.quote_dao.get_quote_by_document_id(self.quote_id)
            if data and 'document' in data:
                document = data['document']
                if document and hasattr(document, 'project_folder') and document.project_folder:
                    self.project_folder = pathlib.Path(document.project_folder)
                    self.photo_dir = self.project_folder / "Photos"
                    self.doc_dir = self.project_folder / "Documents"
                    return True
        except Exception as e:
            self.logger.warning(f"Failed to refresh project folder: {e}")
        return False

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
            self.quote_dao.add_quote_item(self.quote_id, num, svc, qty_val, up_val)
