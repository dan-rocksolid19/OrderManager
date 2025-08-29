import traceback
from librepy.pybrex.dialog import DialogBase
from librepy.jobmanager.data.request_dao import RequestDAO
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.uno_date_time_converters import python_date_to_uno, python_time_to_uno, uno_date_to_python, uno_time_to_python
from librepy.utils import project_folder_manager

class Request(DialogBase):
    
    POS_SIZE = 0, 0, 450, 450
    DISPOSE = True
    
    MARGIN = 20
    LABEL_HEIGHT = 15
    FIELD_HEIGHT = 15
    FIELD_WIDTH = 170
    SECTION_SPACING = 20
    
    def __init__(self, parent, ctx, smgr, frame, ps, request_id=None, **props):
        props['Title'] = 'Request'
        self.parent = parent
        self.logger = parent.logger
        self.request_dao = RequestDAO(self.logger)
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.request_id = request_id
        
        self.save_successful = False
        self.request_data = None
        
        # Control references
        self.customer_name = None
        self.company_name = None
        self.phone_number = None
        self.email = None
        self.address = None
        self.city = None
        self.state = None
        self.zip_code = None
        self.information = None
        self.residential_commercial = None
        self.day_works_best = None
        self.another_day = None
        self.preferred_time = None
        self.save_btn = None
        self.project_folder = None
        self.photo_dir = None
        self.doc_dir = None
        
        self.listeners = listeners.Listeners()
        super().__init__(ctx, smgr, **props)
        self.logger.info("Request dialog initialized")
        
    def _create(self):
        """Create the dialog UI components"""
        try:
            # Title and action buttons at the top
            self.add_label("lbl_request", 20, 10, 100, 20, Label="Request", FontHeight=22, FontWeight=150)
            
            # Top action buttons (right side)
            button_width = 80
            button_height = 20
            button_spacing = 5
            start_x = self.POS_SIZE[2] - (button_width * 3 + button_spacing * 2 + 20)
            
            self.add_button("btnAttachPhotos", start_x, 5, button_width, button_height, 
                           Label="Attach Photos", callback=self.attach_photos,
                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
            
            self.add_button("btnAttachDocuments", start_x + button_width + button_spacing, 5, button_width, button_height,
                           Label="Attach Documents", callback=self.attach_documents,
                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
            
            self.add_button("btnConvertQuote", start_x + (button_width + button_spacing) * 2, 5, button_width, button_height,
                           Label="Convert to Quote", callback=self.convert_to_quote,
                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)

            # Customer Information Section
            y = 40
            column1_x = 40
            column2_x = 240
            row_spacing = self.LABEL_HEIGHT + self.FIELD_HEIGHT
            label_spacing = 12
            
            # Left column fields (create all left column fields first for proper tab order)
            y1 = y
            self.add_label("lbl_customer_name", column1_x, y1, self.FIELD_WIDTH, self.LABEL_HEIGHT, 
                          Label="Customer Name *", FontHeight=12, FontWeight=120)
            self.customer_name = self.add_edit("CustomerName", column1_x, y1 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y1 += row_spacing
            self.add_label("lbl_company_name", column1_x, y1, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Company Name", FontHeight=12, FontWeight=120)
            self.company_name = self.add_edit("CompanyName", column1_x, y1 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y1 += row_spacing
            self.add_label("lbl_phone_number", column1_x, y1, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Phone Number *", FontHeight=12, FontWeight=120)
            self.phone_number = self.add_edit("PhoneNumber", column1_x, y1 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y1 += row_spacing
            self.add_label("lbl_email", column1_x, y1, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Email", FontHeight=12, FontWeight=120)
            self.email = self.add_edit("Email", column1_x, y1 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)

            # Right column fields (create all right column fields after left column)
            y2 = y
            self.add_label("lbl_address", column2_x, y2, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Address", FontHeight=12, FontWeight=120)
            self.address = self.add_edit("Address", column2_x, y2 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y2 += row_spacing
            self.add_label("lbl_city", column2_x, y2, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="City", FontHeight=12, FontWeight=120)
            self.city = self.add_edit("City", column2_x, y2 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y2 += row_spacing
            self.add_label("lbl_state", column2_x, y2, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="State", FontHeight=12, FontWeight=120)
            self.state = self.add_edit("State", column2_x, y2 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)
            
            y2 += row_spacing
            self.add_label("lbl_zip_code", column2_x, y2, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Zip Code", FontHeight=12, FontWeight=120)
            self.zip_code = self.add_edit("ZipCode", column2_x, y2 + label_spacing, self.FIELD_WIDTH, self.FIELD_HEIGHT)

            # Service Information Section
            service_y = y1 + self.FIELD_HEIGHT + 20
            
            self.add_line("line_service_info", 20, service_y, 405, 1, BackgroundColor=0x000000)
            service_y += 10
            
            self.add_label("lbl_service_info", 20, service_y, 100, 20,
                          Label="Service Information", FontHeight=14, FontWeight=150)
            service_y += 20
            
            # Information text area
            self.add_label("lbl_information", column1_x, service_y, 120, self.LABEL_HEIGHT,
                          Label="Information", FontHeight=12, FontWeight=120)
            info_width = self.FIELD_WIDTH * 2 + 30
            self.information = self.add_edit("Information", column1_x, service_y + 10, info_width, 80, MultiLine=True)
            service_y += 100
            
            # Residential/Commercial dropdown
            self.add_label("lbl_res_comm", column1_x, service_y, self.FIELD_WIDTH, self.LABEL_HEIGHT,
                          Label="Residential/Commercial", FontHeight=12, FontWeight=120)
            self.residential_commercial = self.add_combo("ResidentialCommercial", column1_x, service_y + 10, 200, self.FIELD_HEIGHT,
                                                           Dropdown=True)
            service_y += self.FIELD_HEIGHT + 20

            # Appointment Section
            appointment_y = service_y
            self.add_line("line_appointment", 20, appointment_y, 405, 1, BackgroundColor=0x000000)
            appointment_y += 10
            
            self.add_label("lbl_appointment", 20, appointment_y, 100, 20,
                          Label="Appointment", FontHeight=14, FontWeight=150)
            appointment_y += 20
            
            field_width = 100
            field_spacing = field_width + 20
            
            # Appointment fields
            self.add_label("lbl_day_works_best", column1_x, appointment_y, field_width, self.LABEL_HEIGHT,
                          Label="What day works best?", FontHeight=12, FontWeight=120)
            self.day_works_best = self.add_date("DayWorksBest", column1_x, appointment_y + 10, field_width, self.FIELD_HEIGHT, Dropdown=True)
            
            self.add_label("lbl_another_day", column1_x + field_spacing, appointment_y, field_width, self.LABEL_HEIGHT,
                          Label="Another day that works?", FontHeight=12, FontWeight=120)
            self.another_day = self.add_date("AnotherDay", column1_x + field_spacing, appointment_y + 10, field_width, self.FIELD_HEIGHT, Dropdown=True)   
            
            self.add_label("lbl_preferred_time", column1_x + field_spacing*2, appointment_y, field_width, self.LABEL_HEIGHT,
                          Label="Preferred time of arrival", FontHeight=12, FontWeight=120)
            self.preferred_time = self.add_time("PreferredTime", column1_x + field_spacing*2, appointment_y + 10, field_width, self.FIELD_HEIGHT, Spin=True, StrictFormat=False, TimeFormat=2)

            # Bottom buttons
            button_y = appointment_y + 45
            button_width = 80
            button_height = 25
            button_spacing = 20
            
            # Center the buttons
            total_width = button_width * 2 + button_spacing
            center_x = (self.POS_SIZE[2] - total_width) // 2
            
            self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                           BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
            
            self.save_btn = self.add_button("SaveButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                            Label="Save", callback=self.save_request,
                                            BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
            
        except Exception as e:
            self.logger.error(traceback.format_exc())
            error_msg = f"Error creating request dialog: {str(e)}"
            self.logger.error(error_msg)
            msgbox(error_msg, "UI Creation Error")
            raise

    def _prepare(self):
        """Prepare the dialog - load existing request data if editing"""
        try:
            # Populate dropdown items
            self.residential_commercial.addItem("Residential", 0)
            self.residential_commercial.addItem("Commercial", 1)
            
            if self.request_id:
                self._load_request_data()
                self.save_btn.Model.Label = "Update"
                self.save_btn.Model.BackgroundColor = 0x4A90E2  # Blue for update
                
        except Exception as e:
            error_msg = f"Error preparing request dialog: {str(e)}"
            self.logger.error(error_msg)
            msgbox(error_msg, "Data Loading Error")

    def _dispose(self):
        """Clean up resources when dialog is closed"""
        try:
            if hasattr(self, 'listeners'):
                pass  # Any cleanup needed for listeners
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")

    def _refresh_project_folder(self):
        if not self.request_id:
            return False
        try:
            data = self.request_dao.get_request_by_document_id(self.request_id)
            if data and 'document' in data:
                document = data['document']
                if document and hasattr(document, 'project_folder') and document.project_folder:
                    import pathlib
                    self.project_folder = pathlib.Path(document.project_folder)
                    self.photo_dir = self.project_folder / "Photos"
                    self.doc_dir = self.project_folder / "Documents"
                    return True
        except Exception as e:
            self.logger.warning(f"Failed to refresh project folder: {e}")
        return False

    def _validate_form(self):
        """Validate form inputs before saving"""
        if not self.customer_name.Text.strip():
            msgbox("Customer Name is required.", "Validation Error")
            return False
        
        if not self.phone_number.Text.strip():
            msgbox("Phone Number is required.", "Validation Error")
            return False
        
        return True

    def _get_form_values(self):
        """Get values from form fields"""
        day_works_best = None
        try:
            if hasattr(self.day_works_best, 'getDate'):
                uno_date = self.day_works_best.getDate()
                day_works_best = uno_date_to_python(uno_date) if uno_date and uno_date.Year > 0 else None
        except:
            day_works_best = None
            
        another_day = None
        try:
            if hasattr(self.another_day, 'getDate'):
                uno_date = self.another_day.getDate()
                another_day = uno_date_to_python(uno_date) if uno_date and uno_date.Year > 0 else None
        except:
            another_day = None
            
        preferred_time = None
        try:
            if hasattr(self.preferred_time, 'getTime'):
                uno_time = self.preferred_time.getTime()
                if uno_time:
                    python_time = uno_time_to_python(uno_time)
                    # Only save non-default times (not 00:00:00)
                    if python_time and (python_time.hour != 0 or python_time.minute != 0 or python_time.second != 0):
                        preferred_time = python_time
        except:
            preferred_time = None
        
        return {
            'customer_name': self.customer_name.Text.strip(),
            'phone_number': self.phone_number.Text.strip(),
            'company_name': self.company_name.Text.strip() or None,
            'email': self.email.Text.strip() or None,
            'address_line': self.address.Text.strip() or None,
            'city': self.city.Text.strip() or None,
            'state': self.state.Text.strip() or None,
            'zip_code': self.zip_code.Text.strip() or None,
            'information': self.information.Text.strip() or None,
            'residential_commercial': self.residential_commercial.Text.strip() or None,
            'day_works_best': day_works_best,
            'another_day': another_day,
            'preferred_time': preferred_time,
            'project_folder': str(self.project_folder) if self.project_folder else None
        }

    def _done(self, ret):
        """Gets called when the dialog closes"""
        return ret  # Return the original result

    def _load_request_data(self):
        """Load existing request data from database"""
        try:
            self.request_data = self.request_dao.get_request_by_document_id(self.request_id)
            
            if self.request_data:
                customer = self.request_data['customer']
                address = self.request_data['address']
                request = self.request_data['request']
                
                # Populate customer fields
                self.customer_name.Text = customer.customer_name or ''
                self.company_name.Text = customer.company_name or ''
                self.phone_number.Text = customer.phone_number or ''
                self.email.Text = customer.email or ''
                
                # Populate address fields
                if address:
                    self.address.Text = address.address_line or ''
                    self.city.Text = address.city or ''
                    self.state.Text = address.state or ''
                    self.zip_code.Text = address.zip_code or ''
                
                # Populate request fields
                self.information.Text = request.information or ''
                self.residential_commercial.Text = request.residential_commercial or ''
                
                # Set date fields
                if request.day_works_best:
                    try:
                        uno_date = python_date_to_uno(request.day_works_best)
                        if uno_date and hasattr(self.day_works_best, 'setDate'):
                            self.day_works_best.setDate(uno_date)
                    except Exception as e:
                        self.logger.warning(f"Failed to set day_works_best date: {e}")
                
                if request.another_day:
                    try:
                        uno_date = python_date_to_uno(request.another_day)
                        if uno_date and hasattr(self.another_day, 'setDate'):
                            self.another_day.setDate(uno_date)
                    except Exception as e:
                        self.logger.warning(f"Failed to set another_day date: {e}")
                
                if request.preferred_time:
                    try:
                        uno_time = python_time_to_uno(request.preferred_time)
                        if uno_time and hasattr(self.preferred_time, 'setTime'):
                            self.preferred_time.setTime(uno_time)
                    except Exception as e:
                        self.logger.warning(f"Failed to set preferred_time: {e}")
                else:
                    try:
                        if hasattr(self.preferred_time, 'Model'):
                            self.preferred_time.Model.Text = ""
                    except Exception as e:
                        self.logger.warning(f"Failed to clear preferred_time: {e}")
                
                self.logger.info(f"Loaded request data for document ID: {self.request_id}")
                document = self.request_data['document'] if 'document' in self.request_data else None
                if document and hasattr(document, 'project_folder') and document.project_folder:
                    import pathlib
                    self.project_folder = pathlib.Path(document.project_folder)
                    self.photo_dir = self.project_folder / "Photos"
                    self.doc_dir = self.project_folder / "Documents"
                else:
                    cust_name = customer.customer_name
                    if cust_name:
                        try:
                            self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(cust_name.strip(), self.logger)
                            self._save_project_folder_if_needed()
                        except Exception as ee:
                            self.logger.warning(f"Could not set up project folders for existing request: {ee}")
            else:
                self.logger.warning(f"No data found for request document ID: {self.request_id}")
                msgbox(f"No data found for request ID: {self.request_id}", "Warning")
                
        except Exception as e:
            error_msg = f"Error loading request data: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            msgbox(error_msg, "Data Loading Error")

    # Button callback methods
    def _save_project_folder_if_needed(self):
        """Save project folder to database if we have a request ID and the folder was just created"""
        if self.request_id and self.project_folder:
            try:
                form_data = self._get_form_values()
                self.request_dao.update_request_with_customer_and_address(
                    document_id=self.request_id,
                    **form_data
                )
                self.logger.info(f"Updated project folder for request {self.request_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update project folder: {e}")

    def attach_photos(self, event):
        """Handle attach photos button click"""
        self.logger.info("Attach Photos clicked")
        try:
            if not self.photo_dir:
                refreshed = self._refresh_project_folder()
            if not self.photo_dir:
                customer_name = self.customer_name.Text.strip()
                if not customer_name:
                    msgbox("Customer name is required to attach photos.", "Validation Error")
                    return
                self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name, self.logger)
                self._save_project_folder_if_needed()
            picker = self.ctx.getServiceManager().createInstanceWithContext("com.sun.star.ui.dialogs.FilePicker", self.ctx)
            picker.setMultiSelectionMode(True)
            picker.appendFilter("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")
            picker.appendFilter("All files", "*.*")
            import os
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.exists(pictures_dir):
                import uno
                pictures_url = uno.systemPathToFileUrl(pictures_dir)
                picker.setDisplayDirectory(pictures_url)
            if picker.execute() == 1:
                selected_files = picker.getSelectedFiles()
                if selected_files:
                    copied = project_folder_manager.copy_files_to_folder(selected_files, self.photo_dir, "Photos", self.logger)
                    if not copied:
                        msgbox("No files were copied.", "No Files")
                    else:
                        self.logger.info(f"Successfully copied {len(copied)} file(s) to Photos folder")
            picker.dispose()
        except Exception as e:
            self.logger.error(f"Error attaching photos: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error attaching photos: {e}", "Error")
    
    def attach_documents(self, event):
        """Handle attach documents button click"""
        self.logger.info("Attach Documents clicked")
        try:
            if not self.doc_dir:
                refreshed = self._refresh_project_folder()
            if not self.doc_dir:
                customer_name = self.customer_name.Text.strip()
                if not customer_name:
                    msgbox("Customer name is required to attach documents.", "Validation Error")
                    return
                self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name, self.logger)
                self._save_project_folder_if_needed()
            picker = self.ctx.getServiceManager().createInstanceWithContext("com.sun.star.ui.dialogs.FilePicker", self.ctx)
            picker.setMultiSelectionMode(True)
            picker.appendFilter("Document files", "*.pdf;*.doc;*.docx;*.txt;*.rtf")
            picker.appendFilter("Spreadsheet files", "*.xls;*.xlsx;*.ods")
            picker.appendFilter("All files", "*.*")
            import os
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(documents_dir):
                import uno
                documents_url = uno.systemPathToFileUrl(documents_dir)
                picker.setDisplayDirectory(documents_url)
            if picker.execute() == 1:
                selected_files = picker.getSelectedFiles()
                if selected_files:
                    copied = project_folder_manager.copy_files_to_folder(selected_files, self.doc_dir, "Documents", self.logger)
                    if not copied:
                        msgbox("No files were copied.", "No Files")
                    else:
                        self.logger.info(f"Successfully copied {len(copied)} file(s) to Documents folder")
            picker.dispose()
        except Exception as e:
            self.logger.error(f"Error attaching documents: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error attaching documents: {e}", "Error")
    
    def convert_to_quote(self, event):
        """Handle convert to quote button click"""
        self.logger.info("Convert to Quote clicked")
        
        try:
            # Ensure we have a saved request to convert
            if not self.request_id:
                # If no request_id, we need to save first
                if not self._validate_form():
                    return
                
                form_data = self._get_form_values()
                document_id = self.request_dao.create_request_with_customer_and_address(**form_data)
                
                if not document_id:
                    msgbox("Failed to save request before conversion.", "Error")
                    return
                
                self.request_id = document_id
                self.logger.info(f"Created request with ID {self.request_id} for conversion")
            
            # Check if request has unsaved changes and save them
            elif hasattr(self, 'request_data') and self.request_data:
                # If we're editing an existing request, save any changes first
                if self._validate_form():
                    form_data = self._get_form_values()
                    success = self.request_dao.update_request_with_customer_and_address(
                        document_id=self.request_id,
                        **form_data
                    )
                    if not success:
                        msgbox("Failed to save request changes before conversion.", "Error")
                        return
                    self.logger.info(f"Updated request {self.request_id} before conversion")
            
            # Convert the request to a quote
            quote_document_id = self.request_dao.convert_request_to_quote(self.request_id)
            
            if quote_document_id:
                self.logger.info(f"Successfully converted request {self.request_id} to quote {quote_document_id}")
                
                # Close this request dialog
                self.end_execute(1)
                
                # Open the quote dialog with the new quote
                from librepy.jobmanager.components.joblist.quote import Quote
                quote_dialog = Quote(self.parent, self.ctx, self.smgr, self.frame, self.ps, 
                                   quote_id=quote_document_id)
                quote_dialog.execute()
                
                # Mark conversion as successful so parent can refresh if needed
                self.save_successful = True
                
            else:
                msgbox("Failed to convert request to quote.", "Conversion Error")
                
        except Exception as e:
            error_msg = f"Error converting request to quote: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            msgbox(error_msg, "Conversion Error")
    
    def save_request(self, event):
        """Handle save button click"""
        self.logger.info("Save Request clicked")
        
        try:
            if not self._validate_form():
                return  # Keep dialog open if validation fails
                
            form_data = self._get_form_values()
            
            if self.request_id:
                # Update existing request
                success = self.request_dao.update_request_with_customer_and_address(
                    document_id=self.request_id,
                    **form_data
                )
                
                if success:
                    self._refresh_project_folder()
                    self.save_successful = True
                    self.logger.info(f"Successfully updated request {self.request_id}")
                    self.end_execute(1)  # Close dialog on success
                else:
                    msgbox("Failed to update request", "Error")
                    return  # Keep dialog open on error
            else:
                # Create new request
                document_id = self.request_dao.create_request_with_customer_and_address(**form_data)
                
                if document_id:
                    self.request_id = document_id
                    self._refresh_project_folder()
                    self.save_successful = True
                    self.logger.info(f"Successfully created request {self.request_id}")
                    self.end_execute(1)  # Close dialog on success
                else:
                    msgbox("Failed to create request", "Error")
                    return  # Keep dialog open on error
                    
        except Exception as e:
            error_msg = f"Error saving request: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            msgbox(error_msg, "Save Error")
            return  # Keep dialog open on error
