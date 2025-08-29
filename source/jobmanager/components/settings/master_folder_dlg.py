from librepy.pybrex import dialog
from librepy.jobmanager.data.settings_dao import SettingsDAO
from librepy.pybrex.msgbox import MsgBox
from librepy.pybrex.values import APP_NAME
import os
import traceback
import uno

class MasterFolderDialog(dialog.DialogBase):

    POS_SIZE = 0, 0, 380, 120
    
    MARGIN = 8
    LABEL_HEIGHT = 10
    FIELD_HEIGHT = 18
    FIELD_WIDTH = 360
    SECTION_SPACING = 15
    
    BTN_WIDTH = 120
    BTN_HEIGHT = 20
    BTN_NORMAL_COLOR = 0x0078D7
    BTN_TEXT_COLOR = 0xFFFFFF
    
    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = 'Master Folder Settings'
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        
        self.save_successful = False
        self.current_master_folder = None
        self.settings_dao = None
        
        self.txt_master_folder = None
        self.btn_select_folder = None
        
        try:
            self.settings_dao = SettingsDAO(logger)
        except Exception as e:
            error_msg = f"Error initializing settings DAO: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
        
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        try:
            field_width = self.FIELD_WIDTH
            button_width = self.BTN_WIDTH
            x_left = self.MARGIN
            y = self.MARGIN * 2
            
            self.add_label(
                'LblMasterFolderSettings',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT + 2,
                Label="Master Folder Settings",
                FontWeight=150
            )
            
            y += self.LABEL_HEIGHT + 10
            
            self.add_label(
                'LblMasterFolderPath',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT,
                Label="Master Folder for Attachments:"
            )
            
            y += self.LABEL_HEIGHT + 2
            
            self.txt_master_folder = self.add_edit(
                'TxtMasterFolderPath',
                x_left, y,
                field_width - button_width - self.MARGIN,
                self.FIELD_HEIGHT,
                Border=1,
                ReadOnly=True
            )
            
            self.btn_select_folder = self.add_button(
                'BtnSelectFolder',
                x_left + field_width - button_width,
                y,
                button_width,
                self.FIELD_HEIGHT,
                Label='Select Folder',
                FontWeight=150,
                BackgroundColor=self.BTN_NORMAL_COLOR,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._handle_select_folder
            )
            
            y += self.FIELD_HEIGHT + 10
            
            self.add_label(
                'LblNote',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT * 2,
                Label="Note: This folder will store all document attachments (photos, documents, etc.). Please select a location with sufficient storage space and write permissions.",
                FontHeight=8,
                TextColor=0x818683,
                MultiLine=True
            )
            
            self.add_ok_cancel()
            
        except Exception as e:
            error_msg = f"Error creating master folder settings dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "UI Creation Error")
            raise

    def _prepare(self):
        try:
            default_folder = os.path.join(os.path.expanduser("~"), "Documents", f"{APP_NAME}_attachments")
            
            if self.settings_dao:
                self.current_master_folder = self.settings_dao.get_value('master_folder.attachments_directory', default_folder)
            else:
                self.current_master_folder = default_folder
                
            self._update_path_display()
                
        except Exception as e:
            error_msg = f"Error preparing master folder settings dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            default_folder = os.path.join(os.path.expanduser("~"), "Documents", f"{APP_NAME}_attachments")
            self.current_master_folder = default_folder
            self._update_path_display()
            MsgBox(error_msg, 16, "Data Loading Error")

    def _dispose(self):
        pass
            
    def _handle_select_folder(self, event):
        try:
            home_path = os.path.expanduser("~")
            folder = home_path if os.path.exists(home_path) else os.getcwd()
            
            picker = self.ctx.getServiceManager().createInstanceWithContext(
            "com.sun.star.ui.dialogs.FolderPicker", self.ctx)

            if os.path.exists(folder):
                folder_url = uno.systemPathToFileUrl(folder)
                picker.setDisplayDirectory(folder_url)

            if picker.execute() == 1:
                folder_url = picker.getDirectory()
                folder = uno.fileUrlToSystemPath(folder_url)

            self.current_master_folder = folder
            self._update_path_display()
                
        except Exception as e:
            error_msg = f"Error selecting folder: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Folder Selection Error")
    
    def _update_path_display(self):
        if self.txt_master_folder and self.current_master_folder:
            self.txt_master_folder.setText(self.current_master_folder)
            
    def _done(self, ret):
        if ret == 1:
            try:
                if not self.current_master_folder:
                    MsgBox("No master folder selected", 16, "Validation Error")
                    return 0
                    
                if not os.path.exists(self.current_master_folder):
                    try:
                        os.makedirs(self.current_master_folder)
                    except Exception as e:
                        error_msg = f"Error creating master folder: {str(e)}"
                        self.logger.error(error_msg)
                        MsgBox(error_msg, 16, "Directory Creation Error")
                        return 0
                
                if not self.settings_dao:
                    MsgBox("Settings DAO not available", 16, "Save Failed")
                    return 0
                
                success = self.settings_dao.set_value('master_folder.attachments_directory', self.current_master_folder)
                
                if success:
                    self.save_successful = True
                    return 1
                else:
                    MsgBox("Failed to save master folder setting", 16, "Save Failed")
                    return 0
                        
            except Exception as e:
                error_msg = f"Error saving master folder settings: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                MsgBox(error_msg, 16, "Save Error")
                return 0
                
        return ret 