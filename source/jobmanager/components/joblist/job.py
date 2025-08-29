import uno
import os
import traceback
import pathlib
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.jobmanager.data.job_dao import JobDAO
from librepy.jobmanager.components.joblist.step_dlg import StepDialog
from librepy.utils import project_folder_manager
from librepy.pybrex.values import GRAPHICS_DIR

class Job(DialogBase):
    
    POS_SIZE = 0, 0, 510, 460
    DISPOSE = True
    
    def __init__(self, parent, ctx, smgr, frame, ps, job_id=None, **props):
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
        self.job_dao = JobDAO(self.logger)
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.job_id = job_id
        self.pending_steps = []  # store steps added before job is persisted
        self.project_folder = None
        self.photo_dir = None
        self.doc_dir = None
        self.logger.info("Job dialog initialized")
        
    def _create(self):
        self._dialog.Title = "Job"

        # Title and action buttons at the top
        self.add_label("lbl_job", 20, 10, 100, 20, Label="Job", FontHeight=22, FontWeight=150)
        
        # Top action buttons (right side)
        button_width = 100
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
        
        self.btn_complete_job = self.add_button("btnCompleteJob", start_x + (button_width + button_spacing) * 2, start_y, button_width, button_height,
                                               Label="Complete Job (Create Invoice)", callback=self.complete_job,
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
        # Steps Section                                        #
        #########################################################
        
        steps_y = row4 + 47
        
        self.add_label("lbl_steps", column1_x + 25, steps_y, 100, 20,
                      Label="Steps", FontHeight=16, FontWeight=150)
        
        # Add Step button (right side)
        add_step_button_width = 80
        add_step_x = start_x + (button_width + button_spacing) * 2
        
        self.btn_add_step = self.add_button("btnAddStep", add_step_x, steps_y, add_step_button_width, button_height,
                                           Label="+ Add Step", callback=self.add_step,
                                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=11)
        
        # Steps grid
        grid_y = steps_y + 30
        grid_height = 100
        grid_width = 400
        
        self.steps_grid, self.steps_grid_model = self.add_grid("grdSteps", column1_x + 25, grid_y, grid_width, grid_height,
            titles=[
                ("Step", "step", 150, 1),
                ("Start Date", "start_date", 85, 1),
                ("End Date", "end_date", 85, 1),
                ("Crew Assigned", "crew_assigned", 80, 1)
            ]
        )
        
        # Add double-click listener to the steps grid
        self.listeners.add_mouse_listener(self.steps_grid_model, pressed=self.on_step_double_click)

        # View Items & Hours button
        view_items_y = grid_y + grid_height + 20
        view_items_button_width = 150
        view_items_x = column1_x + 25
        
        self.btn_view_items = self.add_button("btnViewItems", view_items_x, view_items_y, button_width, button_height,
                                             Label="View Items & Hours", callback=self.view_items_hours,
                                             BackgroundColor=0x5D6D7E, TextColor=0xFFFFFF, FontHeight=12, FontWeight=150)

        # Bottom buttons
        button_y = view_items_y + 50
        button_width = 100
        button_height = 25
        button_spacing = 20
        
        # Center the buttons
        total_width = button_width * 2 + button_spacing
        center_x = (self.POS_SIZE[2] - total_width) // 2
        
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height,
                                         BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        
        self.schedule_btn = self.add_button("ScheduleButton", center_x + button_width + button_spacing, button_y, button_width, button_height,
                                           Label="Schedule Job", callback=self.schedule_job,
                                           BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

    def _prepare(self):
        if self.job_id:
            self.load_job_data()
            self.schedule_btn.Model.Label = "Update Job"
            self.schedule_btn.Model.BackgroundColor = 0x4A90E2
        else:
            # For new jobs we start with an empty grid; nothing else to do
            pass
    
    # Top action button callbacks
    def attach_photos(self, event):
        """Handle attach photos button click"""
        self.logger.info("Attach Photos clicked")
        
        try:
            if not self.photo_dir:
                self._refresh_project_folder()
            if not self.photo_dir:
                customer_name = self.customer_name.Text.strip()
                if not customer_name:
                    msgbox("Customer name is required to attach photos.", "Validation Error")
                    return
                self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name, self.logger)
                self._save_project_folder_if_needed()
            
            # Create file picker for photos
            picker = self.ctx.getServiceManager().createInstanceWithContext("com.sun.star.ui.dialogs.FilePicker", self.ctx)
            picker.setMultiSelectionMode(True)
            picker.appendFilter("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff")
            picker.appendFilter("All files", "*.*")
            
            # Set initial directory to user's Pictures folder if it exists
            import os
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
            if os.path.exists(pictures_dir):
                pictures_url = uno.systemPathToFileUrl(pictures_dir)
                picker.setDisplayDirectory(pictures_url)
            
            # Execute the picker
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
                self._refresh_project_folder()
            if not self.doc_dir:
                customer_name = self.customer_name.Text.strip()
                if not customer_name:
                    msgbox("Customer name is required to attach documents.", "Validation Error")
                    return
                self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name, self.logger)
                self._save_project_folder_if_needed()
            
            # Create file picker for documents
            picker = self.ctx.getServiceManager().createInstanceWithContext("com.sun.star.ui.dialogs.FilePicker", self.ctx)
            picker.setMultiSelectionMode(True)
            picker.appendFilter("Document files", "*.pdf;*.doc;*.docx;*.txt;*.rtf")
            picker.appendFilter("Spreadsheet files", "*.xls;*.xlsx;*.ods")
            picker.appendFilter("All files", "*.*")
            
            # Set initial directory to user's Documents folder if it exists
            import os
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(documents_dir):
                documents_url = uno.systemPathToFileUrl(documents_dir)
                picker.setDisplayDirectory(documents_url)
            
            # Execute the picker
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
    
    def complete_job(self, event):
        """Handle complete job (create invoice) button click"""
        self.logger.info("Complete Job (Create Invoice) clicked")
        
        try:
            if not self.job_id:
                if not self.customer_name.Text.strip():
                    msgbox("Customer Name is required before completion.", "Validation Error")
                    return
                if not self.phone_number.Text.strip():
                    msgbox("Phone Number is required before completion.", "Validation Error")
                    return

                self.create_job()

                if not self.job_id:
                    msgbox("Failed to create job before completion.", "Error")
                    return
            else:
                self.update_job()
            
            result = self.job_dao.mark_job_complete(self.job_id)
            
            if result['job_updated'] and result['invoice_created']:
                self.end_execute(1)
                
                from librepy.jobmanager.components.joblist.invoice import Invoice
                invoice_dialog = Invoice(self.parent, self.ctx, self.smgr, self.frame, self.ps, 
                                      invoice_id=result['invoice_document_id'])
                invoice_dialog.execute()
            else:
                msgbox("Failed to complete job and create invoice.", "Conversion Error")
                
        except Exception as e:
            self.logger.error(f"Error completing job: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error completing job: {e}", "Error")
    
    def copy_paste(self, event):
        self.logger.info("Copy Past clicked")
        self.site_address.Text = self.billing_address.Text
        self.site_city.Text = self.billing_city.Text
        self.site_state.Text = self.billing_state.Text
        self.site_zip.Text = self.billing_zip.Text
        
    # Step management callbacks
    def add_step(self, event):
        self.logger.info("Add Step clicked")
        dlg = StepDialog(self, self.ctx, self.smgr, self.frame, self.ps)
        if dlg.execute() == 1:
            data = dlg.get_step_data()
            if not data:
                return
            if self.job_id:
                # Persist immediately for existing jobs
                step_order = self.steps_grid._data_model.RowCount + 1
                self.job_dao.add_job_step(
                    document_id=self.job_id,
                    step_order=step_order,
                    step=data['step'],
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    crew_assigned=data['crew_assigned']
                )
                self.load_job_steps()
            else:
                # Stash for later persistence and add to grid
                self.pending_steps.append(data)
                self._refresh_pending_grid()
    
    def on_step_double_click(self, event):
        try:
            row_idx = self.steps_grid_model.getCurrentRow()
            if row_idx == -1:
                return
            selected_id = self.steps_grid._data_model.getRowHeading(row_idx)
            if selected_id is not None:
                if self.job_id and str(selected_id).isdigit():
                    # Persisted step
                    steps = self.job_dao.get_job_steps(self.job_id)
                    step_data = next((s for s in steps if str(s['id']) == str(selected_id)), None)
                    if step_data:
                        dlg = StepDialog(self, self.ctx, self.smgr, self.frame, self.ps, edit_mode=True, step_data=step_data)
                        if dlg.execute() == 1:
                            data = dlg.get_step_data()
                            if data:
                                self.job_dao.update_job_step(
                                    step_id=step_data['id'],
                                    step=data['step'],
                                    start_date=data['start_date'],
                                    end_date=data['end_date'],
                                    crew_assigned=data['crew_assigned']
                                )
                                self.load_job_steps()
                else:
                    # Pending step (unsaved job)
                    if 0 <= row_idx < len(self.pending_steps):
                        orig = self.pending_steps[row_idx]
                        dlg_data = {
                            'step': orig['step'],
                            'start_date': orig['start_date'].strftime('%Y-%m-%d') if orig['start_date'] else '',
                            'end_date': orig['end_date'].strftime('%Y-%m-%d') if orig['end_date'] else '',
                            'crew_assigned': orig['crew_assigned']
                        }
                        dlg = StepDialog(self, self.ctx, self.smgr, self.frame, self.ps, edit_mode=True, step_data=dlg_data)
                        if dlg.execute() == 1:
                            data = dlg.get_step_data()
                            if data:
                                self.pending_steps[row_idx] = data
                                self._refresh_pending_grid()
        except Exception as e:
            self.logger.error(f"Error handling step double-click: {e}")
            self.logger.error(traceback.format_exc())
    
    def view_items_hours(self, event):
        """Handle view items & hours button click"""
        self.logger.info("View Items & Hours clicked")
        from librepy.jobmanager.components.joblist.items_hours_dlg import ItemsHoursDialog
        dlg = ItemsHoursDialog(self, self.ctx, self.smgr, self.frame, self.ps, job_id=self.job_id)
        dlg.execute()
    
    def _save_project_folder_if_needed(self):
        """Save project folder to database if we have a job ID and the folder was just created"""
        if self.job_id and self.project_folder:
            try:
                success = self.job_dao.update_job_with_customer_and_address(
                    document_id=self.job_id,
                    customer_name=self.customer_name.Text.strip(),
                    phone_number=self.phone_number.Text.strip(),
                    company_name=self.company_name.Text.strip() or None,
                    email=self.email.Text.strip() or None,
                    billing_address_line=self.billing_address.Text.strip() or None,
                    billing_city=self.billing_city.Text.strip() or None,
                    billing_state=self.billing_state.Text.strip() or None,
                    billing_zip_code=self.billing_zip.Text.strip() or None,
                    site_address_line=self.site_address.Text.strip() or None,
                    site_city=self.site_city.Text.strip() or None,
                    site_state=self.site_state.Text.strip() or None,
                    site_zip_code=self.site_zip.Text.strip() or None,
                    project_folder=str(self.project_folder)
                )
                if success:
                    self.logger.info(f"Updated project folder for job {self.job_id}")
                    self._refresh_project_folder()
                else:
                    self.logger.warning(f"Failed to update project folder for job {self.job_id}")
            except Exception as e:
                self.logger.warning(f"Failed to update project folder: {e}")
    
    # Main action button callbacks
    def schedule_job(self, event):
        """Handle schedule job button click"""
        self.logger.info("Schedule Job clicked")
        
        # Validate required fields
        if not self.customer_name.Text.strip():
            msgbox("Customer Name is required.", "Validation Error")
            return
        
        if not self.phone_number.Text.strip():
            msgbox("Phone Number is required.", "Validation Error")
            return
        
        # TODO: Save the job data to database
        if self.job_id:
            self.update_job()
        else:
            self.create_job()
        
        self.end_execute(1)
    
    def create_job(self):
        """Create a new job in the database"""
        try:
            self.logger.info("Creating new job...")
            
            # Ensure project folders are set up before creating job
            customer_name = self.customer_name.Text.strip()
            if not self.project_folder:
                try:
                    self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name, self.logger)
                except Exception as e:
                    self.logger.warning(f"Could not set up project folders for new job: {e}")
            
            document_id = self.job_dao.create_job_with_customer_and_address(
                customer_name=customer_name,
                phone_number=self.phone_number.Text.strip(),
                company_name=self.company_name.Text.strip() or None,
                email=self.email.Text.strip() or None,
                billing_address_line=self.billing_address.Text.strip() or None,
                billing_city=self.billing_city.Text.strip() or None,
                billing_state=self.billing_state.Text.strip() or None,
                billing_zip_code=self.billing_zip.Text.strip() or None,
                site_address_line=self.site_address.Text.strip() or None,
                site_city=self.site_city.Text.strip() or None,
                site_state=self.site_state.Text.strip() or None,
                site_zip_code=self.site_zip.Text.strip() or None,
                status="Scheduled",
                project_folder=str(self.project_folder) if self.project_folder else None
            )
            
            if document_id:
                self.job_id = document_id

                # Persist any pending steps
                for idx, step_data in enumerate(self.pending_steps, start=1):
                    self.job_dao.add_job_step(
                        document_id=self.job_id,
                        step_order=idx,
                        step=step_data['step'],
                        start_date=step_data['start_date'],
                        end_date=step_data['end_date'],
                        crew_assigned=step_data['crew_assigned']
                    )
                self.pending_steps.clear()
                self.load_job_steps()

                self.logger.info(f"Job created with document ID: {self.job_id}")
            else:
                msgbox("Failed to create job.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error creating job: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error creating job: {e}", "Error")
    
    def update_job(self):
        """Update existing job in the database"""
        try:
            self.logger.info(f"Updating job document ID: {self.job_id}")
            
            success = self.job_dao.update_job_with_customer_and_address(
                document_id=self.job_id,
                customer_name=self.customer_name.Text.strip(),
                phone_number=self.phone_number.Text.strip(),
                company_name=self.company_name.Text.strip() or None,
                email=self.email.Text.strip() or None,
                billing_address_line=self.billing_address.Text.strip() or None,
                billing_city=self.billing_city.Text.strip() or None,
                billing_state=self.billing_state.Text.strip() or None,
                billing_zip_code=self.billing_zip.Text.strip() or None,
                site_address_line=self.site_address.Text.strip() or None,
                site_city=self.site_city.Text.strip() or None,
                site_state=self.site_state.Text.strip() or None,
                site_zip_code=self.site_zip.Text.strip() or None,
                project_folder=str(self.project_folder) if self.project_folder else None
            )
            
            if success:
                self.logger.info("Job updated successfully")
                self._refresh_project_folder()
            else:
                msgbox("Failed to update job.", "Error")
            
        except Exception as e:
            self.logger.error(f"Error updating job: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error updating job: {e}", "Error")
    
    def load_job_data(self):
        """Load existing job data from database"""
        try:
            job_data = self.job_dao.get_job_by_document_id(self.job_id)
            
            if job_data:
                customer = job_data['customer']
                billing_address = job_data['billing_address']
                site_address = job_data['site_address']
                document = job_data['document']
                
                # Populate customer fields
                self.customer_name.Text = customer.customer_name or ''
                self.company_name.Text = customer.company_name or ''
                self.phone_number.Text = customer.phone_number or ''
                self.email.Text = customer.email or ''
                
                # Populate billing address
                if billing_address:
                    self.billing_address.Text = billing_address.address_line or ''
                    self.billing_city.Text = billing_address.city or ''
                    self.billing_state.Text = billing_address.state or ''
                    self.billing_zip.Text = billing_address.zip_code or ''
                
                # Populate site location
                if site_address:
                    self.site_address.Text = site_address.address_line or ''
                    self.site_city.Text = site_address.city or ''
                    self.site_state.Text = site_address.state or ''
                    self.site_zip.Text = site_address.zip_code or ''
                
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
                            self.project_folder, self.photo_dir, self.doc_dir = project_folder_manager.setup_project_folders(customer_name.strip(), self.logger)
                            self._save_project_folder_if_needed()
                        except Exception as e:
                            self.logger.warning(f"Could not set up project folders for existing job: {e}")
                
                # Load job steps
                self.load_job_steps()
                
                self.logger.info(f"Loaded job data for document ID: {self.job_id}")
            else:
                self.logger.warning(f"No data found for job document ID: {self.job_id}")
                
        except Exception as e:
            self.logger.error(f"Error loading job data: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error loading job data: {e}", "Error")
    
    def load_job_steps(self):
        """Load job steps from database"""
        try:
            steps_data = self.job_dao.get_job_steps(self.job_id)
            
            # Load data into the steps grid
            self.steps_grid.set_data(steps_data, heading='id')
            self.logger.info(f"Loaded {len(steps_data)} job steps")
            
        except Exception as e:
            self.logger.error(f"Error loading job steps: {e}")
            self.logger.error(traceback.format_exc())

    def dispose(self):
        """Dispose of all controls"""
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())

    def _refresh_pending_grid(self):
        def _to_display(row):
            return {
                'step': row['step'],
                'start_date': row['start_date'].strftime('%Y-%m-%d') if row['start_date'] else '',
                'end_date': row['end_date'].strftime('%Y-%m-%d') if row['end_date'] else '',
                'crew_assigned': row['crew_assigned'] or ''
            }
        display_rows = [_to_display(r) for r in self.pending_steps]
        self.steps_grid.set_data(display_rows, heading='step')

    def _refresh_project_folder(self):
        if not self.job_id:
            return False
        try:
            data = self.job_dao.get_job_by_document_id(self.job_id)
            if data and 'document' in data:
                doc = data['document']
                if doc and hasattr(doc, 'project_folder') and doc.project_folder:
                    self.project_folder = pathlib.Path(doc.project_folder)
                    self.photo_dir = self.project_folder / "Photos"
                    self.doc_dir = self.project_folder / "Documents"
                    return True
        except Exception as e:
            self.logger.warning(f"Failed to refresh project folder: {e}")
        return False
