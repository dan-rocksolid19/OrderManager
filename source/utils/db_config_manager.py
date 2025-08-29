from librepy.pybrex.values import pybrex_logger, APP_NAME
from librepy.utils.config_manager import ConfigManager

# Initialize logger
logger = pybrex_logger(__name__)

class DatabaseConfigManager(ConfigManager):
    """Manages database configuration settings."""

    def __init__(self):
        """Initialize database configuration manager with default values."""
        super().__init__(f'{APP_NAME}.conf', {
            'database': {
                'host': 'localhost',
                'port': '5432',
                'user': 'postgres',
                'password': 'true',
                'database': 'postgres'
            }
        })

    def get_connection_params(self):
        """Get database connection parameters.

        Returns:
            dict: Connection parameters or None if configuration is invalid
        """
        try:
            config = self.get_section('database')
            if not config:
                logger.warning("No database configuration found")
                return None

            # Convert port to integer and validate required fields
            try:
                port = int(config.get('port', '5432'))
            except ValueError:
                logger.error(f"Invalid port number: {config.get('port')}")
                return None

            params = {
                'host': config.get('host'),
                'port': port,
                'user': config.get('user'),
                'password': config.get('password'),
                'database': config.get('database')
            }

            # Validate required fields
            if not all(params.values()):
                logger.warning("Missing required database configuration values")
                return None

            logger.debug(f"Retrieved database connection params for {params['database']} at {params['host']}:{params['port']}")
            return params

        except Exception as e:
            logger.error(f"Error getting database connection params: {str(e)}")
            return None

    def save_connection_params(self, params):
        """Save database connection parameters.

        Args:
            params (dict): Connection parameters containing host, port, user, password, and database

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['host', 'port', 'user', 'password', 'database']
            if not all(field in params for field in required_fields):
                logger.error("Missing required database connection parameters")
                return False

            # Convert port to string for storage
            params['port'] = str(params['port'])

            # Save each parameter
            for key, value in params.items():
                self.set_value('database', key, value)

            # Save to file
            self.save_config()
            logger.info(f"Saved database configuration for {params['database']} at {params['host']}:{params['port']}")
            return True

        except Exception as e:
            logger.error(f"Error saving database connection params: {str(e)}")
            return False

    def validate_connection(self):
        """Validate the current database configuration.

        Returns:
            tuple: (bool, str) - (success, message)
        """
        try:
            from librepy.database import test_connection
            params = self.get_connection_params()
            
            if not params:
                return False, "Invalid or missing database configuration"
                
            return test_connection.main(**params)
            
        except Exception as e:
            logger.error(f"Error validating database connection: {str(e)}")
            return False, str(e)

    def prompt_configuration(self):
        """Show database configuration dialog.

        Returns:
            bool: True if configuration was saved, False if canceled
        """
        try:
            from librepy.database.db_dialog import DBDialog
            
            logger.info("Opening database configuration dialog")
            dlg = DBDialog(getDefaultContext(), None, logger)
            config_saved = dlg.execute()
            
            if not config_saved:
                logger.warning("User canceled database configuration dialog")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error showing database configuration dialog: {str(e)}")
            return False 