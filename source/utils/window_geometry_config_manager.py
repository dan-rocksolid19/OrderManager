from librepy.pybrex.values import pybrex_logger, APP_NAME
from librepy.utils.config_manager import ConfigManager

logger = pybrex_logger(__name__)

class WindowGeometryConfigManager(ConfigManager):
    """Manages window geometry configuration settings."""

    def __init__(self):
        """Initialize window geometry configuration manager with default values."""
        super().__init__(f'{APP_NAME}.conf', {
            'window': {
                'x': '0',
                'y': '0', 
                'width': '1800',
                'height': '1000'
            },
            'sidebar': {
                'expanded': '0'
            }
        })

    def get_geometry(self):
        """Get saved window geometry.

        Returns:
            tuple: (x, y, width, height) or None if configuration is invalid
        """
        try:
            config = self.get_section('window')
            if not config:
                logger.debug("No window geometry configuration found")
                return None

            try:
                x = int(config.get('x', '0'))
                y = int(config.get('y', '0'))
                width = int(config.get('width', '1800'))
                height = int(config.get('height', '1000'))
            except ValueError as e:
                logger.error(f"Invalid geometry values in config: {e}")
                return None

            if width <= 0 or height <= 0:
                logger.warning(f"Invalid geometry dimensions: {width}x{height}")
                return None

            logger.debug(f"Retrieved window geometry: ({x}, {y}, {width}, {height})")
            return (x, y, width, height)

        except Exception as e:
            logger.error(f"Error getting window geometry: {str(e)}")
            return None

    def save_geometry(self, geometry):
        """Save window geometry.

        Args:
            geometry (tuple): (x, y, width, height) coordinates and dimensions

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if not geometry or len(geometry) != 4:
                logger.error("Invalid geometry tuple provided")
                return False

            x, y, width, height = geometry

            if width <= 0 or height <= 0:
                logger.warning(f"Refusing to save invalid geometry: {width}x{height}")
                return False

            self.set_value('window', 'x', str(x))
            self.set_value('window', 'y', str(y))
            self.set_value('window', 'width', str(width))
            self.set_value('window', 'height', str(height))

            self.save_config()
            logger.info(f"Saved window geometry: ({x}, {y}, {width}, {height})")
            return True

        except Exception as e:
            logger.error(f"Error saving window geometry: {str(e)}")
            return False

    def reset_to_defaults(self):
        """Reset window geometry to default values.

        Returns:
            bool: True if reset successfully, False otherwise
        """
        try:
            default_geometry = (0, 0, 1800, 1000)
            return self.save_geometry(default_geometry)
        except Exception as e:
            logger.error(f"Error resetting window geometry: {str(e)}")
            return False

    def is_geometry_valid_for_screen(self, geometry, screen_width=None, screen_height=None):
        """Validate that geometry is visible on current screen.

        Args:
            geometry (tuple): (x, y, width, height) to validate
            screen_width (int): Screen width (optional, for future screen detection)
            screen_height (int): Screen height (optional, for future screen detection)

        Returns:
            bool: True if geometry appears to be valid and visible
        """
        if not geometry or len(geometry) != 4:
            return False

        x, y, width, height = geometry

        if width <= 0 or height <= 0:
            return False

        if x < -width or y < -height:
            logger.warning(f"Window geometry appears to be off-screen: ({x}, {y})")
            return False

        if screen_width and screen_height:
            if x > screen_width or y > screen_height:
                logger.warning(f"Window geometry extends beyond screen bounds")
                return False

        return True

    # Sidebar expanded state methods

    def get_sidebar_expanded(self):
        """Return True if sidebar was last saved in expanded state, else False."""
        try:
            value = self.get_value('sidebar', 'expanded', '0')
            return str(value) == '1'
        except Exception as e:
            logger.error(f"Error getting sidebar state: {e}")
            return False

    def save_sidebar_expanded(self, expanded):
        """Persist sidebar expanded state.

        Args:
            expanded (bool): True if sidebar expanded, False if collapsed
        """
        try:
            self.set_value('sidebar', 'expanded', '1' if expanded else '0')
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error saving sidebar state: {e}")
            return False 