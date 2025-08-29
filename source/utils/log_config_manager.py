import os
import logging
from librepy.utils.config_manager import ConfigManager

# Initialize basic logger for this module
logger = logging.getLogger(__name__)

class LoggingConfigManager(ConfigManager):
    """Manages logging configuration settings."""

    # Define valid logging levels
    VALID_LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self):
        """Initialize logging configuration manager with default values."""
        # Import here to avoid circular import
        from librepy.pybrex.values import LOG_DIR, APP_NAME
        
        super().__init__(f'{APP_NAME}.conf', {
            'logging': {
                'log_directory': LOG_DIR,
                'log_level': 'DEBUG',
                'log_file': f'{APP_NAME}.log',
                'max_file_size': '5242880',  # 5MB in bytes
                'backup_count': '2'
            }
        })

    def get_log_path(self):
        """Get the configured log file path.

        Returns:
            str: Full path to the log file
        """
        try:
            log_dir = self.get_value('logging', 'log_directory')
            log_file = self.get_value('logging', 'log_file')
            
            if not log_dir or not log_file:
                # Fall back to defaults from values.py
                from librepy.pybrex.values import DEFAULT_LOG_FILE
                return DEFAULT_LOG_FILE
                
            return os.path.join(log_dir, log_file)
            
        except Exception as e:
            logger.error(f"Error getting log path: {str(e)}")
            # Fall back to default
            from librepy.pybrex.values import DEFAULT_LOG_FILE
            return DEFAULT_LOG_FILE

    def get_log_level(self):
        """Get the configured logging level.

        Returns:
            int: Logging level constant from logging module
        """
        try:
            level_name = self.get_value('logging', 'log_level', 'DEBUG').upper()
            return self.VALID_LOG_LEVELS.get(level_name, logging.DEBUG)
        except Exception as e:
            logger.error(f"Error getting log level: {str(e)}")
            return logging.DEBUG

    def set_log_directory(self, directory):
        """Set the log directory.

        Args:
            directory (str): Path to log directory

        Returns:
            bool: True if directory was set and created successfully
        """
        try:
            # Validate and create directory
            os.makedirs(directory, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(directory, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                logger.error(f"Directory not writable: {str(e)}")
                return False
            
            # Save configuration
            self.set_value('logging', 'log_directory', directory)
            self.save_config()
            
            logger.info(f"Set log directory to: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting log directory: {str(e)}")
            return False

    def set_log_level(self, level):
        """Set the logging level.

        Args:
            level (str): Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            bool: True if level was set successfully
        """
        try:
            level_upper = level.upper()
            if level_upper not in self.VALID_LOG_LEVELS:
                logger.error(f"Invalid log level: {level}")
                return False
                
            self.set_value('logging', 'log_level', level_upper)
            self.save_config()
            
            logger.info(f"Set log level to: {level_upper}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting log level: {str(e)}")
            return False

    def get_rotation_params(self):
        """Get log rotation parameters.

        Returns:
            tuple: (max_bytes, backup_count) for log rotation
        """
        try:
            max_bytes = int(self.get_value('logging', 'max_file_size', '5242880'))
            backup_count = int(self.get_value('logging', 'backup_count', '2'))
            return max_bytes, backup_count
        except ValueError as e:
            logger.error(f"Invalid rotation parameters: {str(e)}")
            return 5242880, 2  # Default values

    def configure_logger(self, logger_instance, name=None):
        """Configure an existing logger with current settings.

        Args:
            logger_instance (logging.Logger): Logger instance to configure
            name (str): Logger name (optional)

        Returns:
            logging.Logger: Configured logger instance
        """
        try:
            # Set level
            logger_instance.setLevel(self.get_log_level())
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Create file handler
            from logging.handlers import RotatingFileHandler
            max_bytes, backup_count = self.get_rotation_params()
            
            # Ensure log directory exists
            log_dir = os.path.dirname(self.get_log_path())
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                self.get_log_path(),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            # Clear existing handlers
            logger_instance.handlers.clear()
            
            # Add handlers
            logger_instance.addHandler(file_handler)
            logger_instance.addHandler(console_handler)
            
            return logger_instance
            
        except Exception as e:
            logger.error(f"Error configuring logger: {str(e)}")
            return logger_instance  # Return original logger on error 