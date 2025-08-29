'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple MsgBox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''

import os
import traceback
from configparser import ConfigParser
from librepy.pybrex import dialog
from librepy.peewee import sdbc_dbapi
from librepy.database import test_connection
from librepy.pybrex.msgbox import confirm_action
from librepy.pybrex.values import APP_NAME
from librepy.database.db_exceptions import DBCanceledException
from librepy.model.db_connection import reinitialize_database_connection

import uno

class DBDialog(dialog.DialogBase):

    POS_SIZE = 0,0,290,150

    def __init__(self, ctx, cast, logger, **props):
        # Add Title to the props dictionary
        props['Title'] = 'Database Connection Settings'
        super().__init__(ctx, cast, **props)

        self.ctx = ctx
        self.logger = logger
        self.logger.info("DBDialog initialized")
        self.DEFAULT_HOST = "localhost"
        self.DEFAULT_PORT = "5432"
        self.DEFAULT_USER = "postgres"
        self.DEFAULT_PASSWORD = "true"
        self.DEFAULT_DATABASE = "postgres"

        # Construct config path using user profile directory
        user_path = uno.fileUrlToSystemPath(getUserPath())
        self.config_dir = os.path.join(user_path, f"{APP_NAME}_config")
        self.config_path = os.path.join(self.config_dir, f'{APP_NAME}.conf')
        
        # Flag to track whether configuration was saved
        self.config_saved = False

    def _create(self):
        label_height = 9
        edit_height = 14
        chk_height = 9
        full_width = 105

        # Title
        self.add_label("Label00", 30, 5, full_width, label_height, Label="PostgreSQL Connection Settings", FontWeight=150, Align=1)
        
        # Advanced
        self.advanced = self.add_check("chkAdvanced", 150, 5, full_width, chk_height, Label="Show Advanced Options", 
                                       FontWeight=150, callback=self._toggle_advanced_options)
        self.advanced.State = 0
        
        # Group
        self.add_groupbox("grpConnInfo", 10, 15, 130, 100)
        
        # GroupAdvanced
        self.adv_grp = self.add_groupbox("grpAdvConnInfo", 150, 15, 130, 100)
        self.adv_grp.setVisible(False)
        
        # Host
        self.add_label("Label0", 20, 20, full_width, label_height, Label="Host", FontWeight=150, Align=1)
        self.host = self.add_edit("txtHost", 20, 30, full_width, edit_height)
        
        # Database
        self.add_label("Label4", 20, 50, full_width, label_height, Label="Database", FontWeight=150, Align=1)
        self.database = self.add_list("lstDatabase", 20, 60, full_width, edit_height, Dropdown=True, Border=1)
        
        # NewDb
        self.add_button("btnNewDb", 20, 90, 50, 15, Label="New Database", FontWeight=150, Align=1, callback=self._new_db)
        
        # Refresh
        self.add_button("btnRefresh", 80, 90, 50, 15, Label="Refresh", FontWeight=150, Align=1, callback=self._load_databases)
        
        # Port
        self.port_lbl = self.add_label("Label1", 160, 20, full_width, label_height, Label="Port", FontWeight=150, Align=1)
        self.port = self.add_edit("txtPort", 160, 30, full_width, edit_height)
        
        # Reset port button
        self.port_btn = self.add_button("btnPort", 230, 18, 30, 10, Label="Reset", FontWeight=150, Align=1, callback=self._reset)
        
        # User
        self.user_lbl = self.add_label("Label2", 160, 50, full_width, label_height, Label="User", FontWeight=150, Align=1)
        self.user = self.add_edit("txtUser", 160, 60, full_width, edit_height)
        
        # Password
        self.password_lbl = self.add_label("Label3", 160, 80, full_width, label_height, Label="Password", FontWeight=150, Align=1)
        self.password = self.add_edit("txtPassword", 160, 90, full_width, edit_height)
        
        # Test Connection
        self.add_button("btnTest", 30, 130, 70, 15, Label="Test Connection", FontWeight=150, Align=1, callback=self._test_conn)
        
        # Save
        self.add_button("btnSave", 110, 130, 70, 15, Label="Save & Exit", FontWeight=150, Align=1, callback=self._save)
        
        # Cancel
        self.add_button("btnCancel", 190, 130, 70, 15, Label="Cancel", FontWeight=150, Align=1, callback=self._close)


    def _prepare(self):
        self.logger.debug("Preparing DBDialog interface")
        self.advanced.State = 0
        self.port_lbl.setVisible(False)
        self.port.setVisible(False)
        self.port_btn.setVisible(False)
        self.user_lbl.setVisible(False)
        self.user.setVisible(False)
        self.password_lbl.setVisible(False)
        self.password.setVisible(False)

        # Set default values before loading config
        self.host.Text = self.DEFAULT_HOST
        self.port.Text = self.DEFAULT_PORT
        self.user.Text = self.DEFAULT_USER
        self.password.Text = self.DEFAULT_PASSWORD

        # Load config first and get the saved database name
        saved_db = self._load_config()
        
        # Then load databases using the configured values
        self._load_databases()
        
        # Select the saved database after the list is populated
        if saved_db:
            self.database.selectItem(saved_db, True)
            self.logger.info(f"Selected previously configured database: {saved_db}")

    def _toggle_advanced_options(self, *args):
        visible = self.advanced.State == 1
        self.port_lbl.setVisible(visible)
        self.port.setVisible(visible)
        self.port_btn.setVisible(visible)
        self.user_lbl.setVisible(visible)
        self.user.setVisible(visible)
        self.password_lbl.setVisible(visible)
        self.password.setVisible(visible)

    def _reset(self, *args):
        self.host.Text = self.DEFAULT_HOST
        self.port.Text = self.DEFAULT_PORT
        self.user.Text = self.DEFAULT_USER
        
    def _load_config(self):
        """Load saved configuration if it exists"""
        self.logger.info(f"Loading configuration from {self.config_path}")
        saved_db = None
        try:
            # Use the pre-calculated config_path
            if os.path.exists(self.config_path):
                config = ConfigParser()
                config.read(self.config_path)

                if config.has_section('database'):
                    self.host.Text = config.get('database', 'host', fallback=self.DEFAULT_HOST)
                    self.port.Text = config.get('database', 'port', fallback=self.DEFAULT_PORT)
                    self.user.Text = config.get('database', 'user', fallback=self.DEFAULT_USER)
                    self.password.Text = config.get('database', 'password', fallback=self.DEFAULT_PASSWORD)
                    
                    # Store the saved database name to return it
                    saved_db = config.get('database', 'database', fallback=None)
                    if saved_db:
                        self.logger.info(f"Loaded database configuration for {saved_db}")
                    else:
                        self.logger.info("No database selected in configuration")
            else:
                self.logger.info("No configuration file found, using defaults")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self.logger.debug(traceback.format_exc())
            MsgBox("Unable to load saved database settings. Default values will be used.")
        
        return saved_db

    def _load_databases(self, *args):
        """Load list of available databases"""
        self.logger.info(f"Loading database list from {self.host.Text}:{self.port.Text}")
        try:
            # Clear existing items
            self.database.removeItems(0, self.database.getItemCount())
            
            # Convert port to integer
            try:
                port = int(self.port.Text) if self.port.Text else int(self.DEFAULT_PORT)
            except ValueError:
                self.logger.error(f"Invalid port number: {self.port.Text}")
                MsgBox("Invalid port number. Please enter a valid integer.")
                return
            
            # Get connection parameters
            conn_params = {
                'host': self.host.Text,
                'port': port,  # Now an integer
                'user': self.user.Text,
                'password': self.password.Text,
                'database': 'postgres'  # Connect to postgres to get list of databases
            }
            
            # Connect to database and get list of databases
            conn = sdbc_dbapi.connect(**conn_params)
            cursor = conn.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            
            # Add databases to list
            for db in cursor.fetchall():
                self.database.addItem(db[0], 0)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error loading databases: {str(e)}")
            self.logger.debug(traceback.format_exc())
            MsgBox("Unable to retrieve database list. Please check your connection settings.")

    def _test_conn(self, *args):
        """Test the database connection by actually querying the database"""
        try:
            port = int(self.port.Text) if self.port.Text else int(self.DEFAULT_PORT)
        except ValueError:
            self.logger.error(f"Invalid port number: {self.port.Text}")
            MsgBox("Invalid port number. Please enter a valid integer.")
            return

        conn_params = {
            'host': self.host.Text,
            'port': port,  # Now an integer
            'user': self.user.Text,
            'password': self.password.Text,
            'database': self.database.getSelectedItem()
        }

        if not conn_params['database']:
            self.logger.warning("Database not selected before testing connection")
            MsgBox("Please select a database before testing the connection.")
            return

        result, message = test_connection.main(**conn_params)
        if result:
            self.logger.info(f"Connection test successful. Server version: {message}")
            MsgBox("Connection successful!")
        else:
            self.logger.error(f"Connection test failed: {message}")
            MsgBox("Connection failed. Please check your settings and try again.")

    def _new_db(self, *args):
        """Create a new database"""
        from librepy.pybrex import dialog
        
        class NewDbDialog(dialog.DialogBase):
            POS_SIZE = 0, 0, 200, 80
            
            def _create(self):
                self.add_label("lblName", 10, 10, 180, 15, Label="Enter name for new database:", FontWeight=150, Align=1)
                self.txtName = self.add_edit("txtName", 10, 30, 180, 15, data_type="str")
                self.add_ok_cancel()
                
            def _done(self, ret):
                if ret == 1:
                    values = {'txtName': self.txtName.Text}
                    return ret, values
                return ret, None
        
        self.logger.info("Opening new database dialog")
        input_dialog = NewDbDialog(self.ctx, None, Title="New Database")
        result = input_dialog.execute()
        
        if not result or result[0] != 1 or not result[1].get('txtName', '').strip():
            self.logger.debug("User cancelled new database dialog or provided empty name")
            return
            
        new_db_name = result[1]['txtName'].strip()
        self.logger.info(f"Attempting to create new database: {new_db_name}")
            
        try:
            conn_params = {
                'host': self.host.Text,
                'port': self.port.Text or self.DEFAULT_PORT,
                'user': self.user.Text,
                'password': self.password.Text,
                'database': 'postgres'
            }
            
            self.logger.debug(f"Connecting to postgres with params: host={conn_params['host']}, port={conn_params['port']}, user={conn_params['user']}")
            conn = sdbc_dbapi.connect(**conn_params)
            conn.autocommit = True
            cursor = conn.cursor()
            
            cursor.execute("SELECT datname FROM pg_database WHERE datname = ?", (new_db_name,))
            if cursor.fetchone():
                self.logger.warning(f"Database '{new_db_name}' already exists")
                MsgBox(f"Database '{new_db_name}' already exists.")
                cursor.close()
                conn.close()
                return
                
            self.logger.info(f"Creating new database: {new_db_name}")
            cursor.execute(f"CREATE DATABASE {new_db_name}")
            cursor.close()
            conn.close()
            
            self.logger.debug("Reloading database list")
            self._load_databases()
            self.database.selectItem(new_db_name, True)
            
            self.logger.info(f"Successfully created new database: {new_db_name}")
            MsgBox(f"Database '{new_db_name}' created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating database: {str(e)}", exc_info=True)
            MsgBox("Unable to create database. Please check your permissions and connection settings.")

    def _save(self, *args):
        """Save the database connection settings to config file"""
        self.logger.info("Saving database configuration")
        try:
            # Convert port to integer and validate
            try:
                port = int(self.port.Text) if self.port.Text else int(self.DEFAULT_PORT)
            except ValueError:
                self.logger.error(f"Invalid port number: {self.port.Text}")
                MsgBox("Invalid port number. Please enter a valid integer.")
                return

            config = {
                'host': self.host.Text,
                'port': port,  # Now an integer
                'user': self.user.Text,
                'password': self.password.Text,
                'database': self.database.getSelectedItem()
            }
            
            self.logger.debug(f"Configuration values: host={config['host']}, port={config['port']}, "
                            f"user={config['user']}, database={config['database']}")

            if not config['database']:
                self.logger.warning("No database selected before saving configuration")
                MsgBox("Please select a database before saving the configuration.")
                return

            self.logger.debug("Testing connection with config values")
            result, message = test_connection.main(**config)
            if not result:
                self.logger.warning(f"Connection test failed before saving: {message}")
                self.logger.debug(f"Connection test failure details: {message}")
                if not confirm_action("Unable to connect with these settings. Do you still want to save them?", "Warning"):
                    self.logger.debug("User chose not to save invalid connection settings")
                    return
                self.logger.debug("User chose to save settings despite connection failure")
            else:
                self.logger.debug("Connection test successful")
            
            # Save configuration file
            self.logger.debug(f"Creating config directory if needed: {self.config_dir}")
            os.makedirs(self.config_dir, exist_ok=True)
            
            self.logger.debug(f"Writing configuration to: {self.config_path}")
            with open(self.config_path, 'w') as f:
                f.write('[database]\n')
                for key, value in config.items():
                    f.write(f'{key} = {value}\n')
                    self.logger.debug(f"Wrote config entry: {key} = {value}")

            if not reinitialize_database_connection():
                self.logger.error("Failed to refresh database connection after saving configuration")
                MsgBox("Failed to refresh database connection. The application may need to be restarted.")
            else:
                self.logger.info("Successfully refreshed database connection with new settings")
                
            from librepy.model.db_connection import get_database_connection
            database = get_database_connection()

            database.connect()

            self.logger.info(f"Configuration saved to {self.config_path}")
            self.config_saved = True

            database.close()

            self.close()
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            self.logger.debug(f"Full error details: {traceback.format_exc()}")
            MsgBox("Unable to save configuration. Please check the application logs for details.")

    def _close(self, *args):
        """Close the dialog without saving"""
        self.close()

    def close(self, *args):
        """Close the dialog"""
        self.end_execute(0)  # 0 indicates cancel/close without saving

    def execute(self):
        """Execute the dialog and return whether configuration was saved"""
        super().execute()
        return self.config_saved

def main(*args):
    """Main entry point for showing database dialog"""
    ctx = getDefaultContext()
    parent = None
    
    # Create a logger for DBDialog when called directly
    from librepy.pybrex.values import pybrex_logger
    logger = pybrex_logger(__name__)
    
    db_dialog = DBDialog(ctx, parent, logger)
    config_saved = db_dialog.execute()
    
    if not config_saved:
        logger.warning("User canceled database configuration dialog")
        raise DBCanceledException("Database configuration canceled by user")
        
    return config_saved
