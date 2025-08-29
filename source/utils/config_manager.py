import os
import threading
from configparser import ConfigParser
import logging
import uno

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_name, default_values=None):
        """Initialize a configuration manager.

        Args:
            config_name (str): Name of the config file (e.g., 'database.conf')
            default_values (dict): Default values for sections/keys
        """
        self.config_name = config_name
        self.default_values = default_values or {}
        self._config = None
        self._config_dir = None
        self._config_path = None
        self._lock = threading.RLock()  # Thread-safe lock for config operations
        self._missing_keys = set()

    @property
    def config_dir(self):
        """Get the configuration directory path."""
        if not self._config_dir:
            user_path = uno.fileUrlToSystemPath(getUserPath())
            try:
                from librepy.pybrex.values import APP_NAME as _APP_NAME
            except Exception:
                logger.error("APP_NAME not found, using default: PybrexApp")
                _APP_NAME = "PybrexApp"
            self._config_dir = os.path.join(user_path, f"{_APP_NAME}_config")
        return self._config_dir

    @property
    def config_path(self):
        """Get the full configuration file path."""
        if not self._config_path:
            self._config_path = os.path.join(self.config_dir, self.config_name)
        return self._config_path

    def ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            logger.debug(f"Ensured config directory exists: {self.config_dir}")
        except Exception as e:
            logger.error(f"Failed to create config directory: {str(e)}")
            raise

    def load_config(self):
        """Load configuration from file.

        Returns:
            ConfigParser: The loaded configuration object
        """
        with self._lock:
            try:
                self._config = ConfigParser()
                if os.path.exists(self.config_path):
                    self._config.read(self.config_path)
                else:
                    logger.debug(f"Config file not found at: {self.config_path}")
                    # Apply default values if file doesn't exist
                    self._apply_defaults()
                return self._config
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
                raise

    def save_config(self):
        """Save current configuration to file."""
        with self._lock:
            try:
                self.ensure_config_dir()
                logger.debug(f"Saving config to: {self.config_path}")
                with open(self.config_path, 'w') as f:
                    self._config.write(f)
            except Exception as e:
                logger.error(f"Error saving config: {str(e)}")
                raise

    def get_value(self, section, key, default=None):
        """Get a configuration value.

        Args:
            section (str): Configuration section name
            key (str): Configuration key
            default: Default value if not found

        Returns:
            The configuration value or default if not found
        """
        with self._lock:
            if not self._config:
                self.load_config()
            try:
                return self._config.get(section, key)
            except:
                if (section, key) not in self._missing_keys:
                    self._missing_keys.add((section, key))
                return default

    def set_value(self, section, key, value):
        """Set a configuration value.

        Args:
            section (str): Configuration section name
            key (str): Configuration key
            value: Value to set
        """
        with self._lock:
            if not self._config:
                self.load_config()
            try:
                if not self._config.has_section(section):
                    self._config.add_section(section)
                self._config.set(section, key, str(value))
                logger.debug(f"Set config value {section}.{key} = {value}")
            except Exception as e:
                logger.error(f"Error setting config value: {str(e)}")
                raise

    def get_section(self, section):
        """Get all values in a section as dict.

        Args:
            section (str): Configuration section name

        Returns:
            dict: Section key-value pairs or empty dict if section not found
        """
        with self._lock:
            if not self._config:
                self.load_config()
            try:
                if self._config.has_section(section):
                    return dict(self._config.items(section))
                logger.debug(f"Section not found: {section}")
                return {}
            except Exception as e:
                logger.error(f"Error getting section: {str(e)}")
                raise

    def _apply_defaults(self):
        """Apply default values to the configuration."""
        try:
            for section, values in self.default_values.items():
                if not self._config.has_section(section):
                    self._config.add_section(section)
                for key, value in values.items():
                    if not self._config.has_option(section, key):
                        self._config.set(section, key, str(value))
            logger.debug("Applied default values to configuration")
        except Exception as e:
            logger.error(f"Error applying default values: {str(e)}")
            raise

    def delete_section(self, section):
        """Delete a configuration section.

        Args:
            section (str): Configuration section name

        Returns:
            bool: True if section was deleted, False if it didn't exist
        """
        with self._lock:
            if not self._config:
                self.load_config()
            try:
                result = self._config.remove_section(section)
                if result:
                    logger.debug(f"Deleted section: {section}")
                else:
                    logger.debug(f"Section not found for deletion: {section}")
                return result
            except Exception as e:
                logger.error(f"Error deleting section: {str(e)}")
                raise

    def delete_value(self, section, key):
        """Delete a configuration value.

        Args:
            section (str): Configuration section name
            key (str): Configuration key

        Returns:
            bool: True if value was deleted, False if it didn't exist
        """
        with self._lock:
            if not self._config:
                self.load_config()
            try:
                result = self._config.remove_option(section, key)
                if result:
                    logger.debug(f"Deleted value: {section}.{key}")
                else:
                    logger.debug(f"Value not found for deletion: {section}.{key}")
                return result
            except Exception as e:
                logger.error(f"Error deleting value: {str(e)}")
                raise 