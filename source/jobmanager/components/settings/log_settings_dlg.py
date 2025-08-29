'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''

from librepy.pybrex import dialog
from librepy.pybrex.values import LOG_DIR
from librepy.utils.log_config_manager import LoggingConfigManager
import os
import traceback
import uno

class LogSettingsDialog(dialog.DialogBase):
    """Dialog for configuring log folder location"""

    POS_SIZE = 0, 0, 340, 110
    
    MARGIN = 8
    LABEL_HEIGHT = 10
    FIELD_HEIGHT = 18
    FIELD_WIDTH = 320
    SECTION_SPACING = 15
    
    BTN_WIDTH = 120
    BTN_HEIGHT = 20
    BTN_NORMAL_COLOR = 0x0078D7
    BTN_TEXT_COLOR = 0xFFFFFF
    
    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = 'Log Settings'
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        
        self.save_successful = False
        self.current_log_path = None
        self.config_manager = None
        
        self.txt_log_path = None
        self.btn_select_folder = None
        
        try:
            self.config_manager = LoggingConfigManager()
        except Exception as e:
            error_msg = f"Error initializing logging config manager: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
        
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        """Create the dialog UI components"""
        try:
            field_width = self.FIELD_WIDTH
            button_width = self.BTN_WIDTH
            x_left = self.MARGIN
            y = self.MARGIN * 2
            
            # Title label
            self.add_label(
                'LblLogSettings',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT + 2,
                Label="Log Settings",
                FontWeight=150
            )
            
            y += self.LABEL_HEIGHT + 10
            
            # Current Log Path label
            self.add_label(
                'LblLogPath',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT,
                Label="Current Log Directory:"
            )
            
            y += self.LABEL_HEIGHT + 2
            
            # Non-editable text field showing current path
            self.txt_log_path = self.add_edit(
                'TxtLogPath',
                x_left, y,
                field_width - button_width - self.MARGIN,
                self.FIELD_HEIGHT,
                Border=1,
                ReadOnly=True
            )
            
            # Select Folder button
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
            
            # Add note about folder permissions
            y += self.FIELD_HEIGHT + 10
            
            self.add_label(
                'LblNote',
                x_left, y,
                field_width,
                self.LABEL_HEIGHT * 2,
                Label="Note: Please select a folder with write permissions. Application logs will be saved to this location.",
                FontHeight=8,
                TextColor=0x818683,
                MultiLine=True
            )
            
            # Add standard OK/Cancel buttons
            self.add_ok_cancel()
            
        except Exception as e:
            error_msg = f"Error creating log settings dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "UI Creation Error")
            raise

    def _prepare(self):
        """Prepare the dialog - load current log path"""
        try:
            # Load current log path from config
            if self.config_manager:
                self.current_log_path = self.config_manager.get_value('logging', 'log_directory')
                
                # Fallback to default LOG_DIR if config value is empty
                if not self.current_log_path:
                    self.current_log_path = LOG_DIR
            else:
                # Fallback to default if config manager failed to initialize
                self.current_log_path = LOG_DIR
                
            self._update_path_display()
                
        except Exception as e:
            error_msg = f"Error preparing log settings dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            # Fallback to default on any error
            self.current_log_path = LOG_DIR
            self._update_path_display()
            MsgBox(error_msg, 16, "Data Loading Error")

    def _dispose(self):
        """Clean up resources when dialog is closed"""
        pass
            
    def _handle_select_folder(self, event):
        """Handle Select Folder button click"""
        try:
            # Start from home directory instead of current working directory
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

            self.current_log_path = folder
            self._update_path_display()
                
        except Exception as e:
            error_msg = f"Error selecting folder: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Folder Selection Error")
    
    def _update_path_display(self):
        """Update the path display text field"""
        if self.txt_log_path and self.current_log_path:
            self.txt_log_path.setText(self.current_log_path)
            
    def _done(self, ret):
        """
        Gets called when the dialog closes with the result code.
        1 = OK button was clicked
        0 = Cancel button was clicked
        """
        if ret == 1:  # OK button
            try:
                if not self.current_log_path:
                    MsgBox("No log directory selected", 16, "Validation Error")
                    return 0  # Cancel the dialog close
                    
                if not os.path.exists(self.current_log_path):
                    try:
                        os.makedirs(self.current_log_path)
                    except Exception as e:
                        error_msg = f"Error creating log directory: {str(e)}"
                        self.logger.error(error_msg)
                        MsgBox(error_msg, 16, "Directory Creation Error")
                        return 0  # Cancel the dialog close
                
                if not self.config_manager:
                    MsgBox("Configuration manager not available", 16, "Save Failed")
                    return 0  # Cancel the dialog close
                
                success = self.config_manager.set_log_directory(self.current_log_path)
                
                if success:
                    self.save_successful = True
                    MsgBox("Log directory updated successfully. Changes will take effect after restarting the application.", 64, "Success")
                    return 1
                else:
                    MsgBox("Failed to save log directory setting", 16, "Save Failed")
                    return 0  # Cancel the dialog close
                        
            except Exception as e:
                error_msg = f"Error saving log settings: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                MsgBox(error_msg, 16, "Save Error")
                return 0  # Cancel the dialog close
                
        return ret  # Return the original result for Cancel 