from datetime import datetime, timezone
from librepy.model.base_dao import BaseDAO
from librepy.model.model import Settings


class SettingsDAO(BaseDAO):
    
    def __init__(self, logger):
        super().__init__(Settings, logger)
    
    def get_value(self, key, default=None):
        """
        Get a setting value by key.
        
        Args:
            key (str): The setting key to look up
            default: Default value to return if key not found
            
        Returns:
            str | None: The setting value or default if not found
        """
        key = self.validate_string_field(key, "key", max_length=255, required=True)
        
        setting = self.safe_execute(
            f"fetching setting with key '{key}'",
            lambda: Settings.get_or_none(Settings.setting_key == key)
        )
        
        if setting is None:
            return default
        
        return setting.setting_value
    
    def set_value(self, key, value):
        """
        Set a setting value by key. Creates new setting if key doesn't exist,
        updates existing setting if key already exists.
        
        Args:
            key (str): The setting key
            value (str): The setting value
            
        Returns:
            bool: True if successful
        """
        key = self.validate_string_field(key, "key", max_length=255, required=True)
        value = str(value) if value is not None else None
        
        with self.database.connection_context():
            existing_setting = self.safe_execute(
                f"checking for existing setting with key '{key}'",
                lambda: Settings.get_or_none(Settings.setting_key == key)
            )
            
            if existing_setting:
                rows_updated = self.safe_execute(
                    f"updating setting with key '{key}'",
                    lambda: Settings.update(
                        setting_value=value,
                        updated_at=datetime.now(timezone.utc)
                    ).where(Settings.setting_key == key).execute(),
                    reraise_integrity=True
                )
                return rows_updated > 0
            else:
                new_setting = self.safe_execute(
                    f"creating new setting with key '{key}'",
                    lambda: Settings.create(
                        setting_key=key,
                        setting_value=value,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ),
                    reraise_integrity=True
                )
                return new_setting is not None
    
    def get_master_folder(self):
        """
        Get the master folder path for attachments.
        
        Returns:
            str | None: The master folder path or None if not configured
        """
        return self.get_value('master_folder.attachments_directory') 