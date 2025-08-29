'''
Database connection module to prevent circular imports.
This module establishes the database connection and makes it available to other modules.
NOTE: ALWAYS USE autoconnect=False! It maybe a bit inconvenient, but it prevents REDUNDANT CONNECTIONS!
'''

from librepy.peewee.sdbc_peewee import SDBCPostgresqlDatabase
from librepy.utils.db_config_manager import DatabaseConfigManager

db_config_manager = DatabaseConfigManager()
database = None # Initialize as None

def get_database_connection(force_reinitialize=False):
    global database
    if database is None or force_reinitialize:
        connection_params = db_config_manager.get_connection_params()
        if connection_params and connection_params.get('database'):
            database = SDBCPostgresqlDatabase(
                connection_params['database'],
                user=connection_params.get('user'),
                password=connection_params.get('password'),
                host=connection_params.get('host'),
                port=connection_params.get('port'),
                autoconnect=False  # Disable automatic connections
            )
        else:
            print("Warning: Database connection parameters are not fully configured.")
            database = None
            raise Exception("Database connection parameters are not fully configured.")
    return database

def reinitialize_database_connection():
    new_db = get_database_connection(force_reinitialize=True)
    try:
        from librepy.model import model as _models
        for _name in dir(_models):
            _cls = getattr(_models, _name)
            if isinstance(_cls, type) and hasattr(_cls, '_meta'):
                _cls._meta.database = new_db
    except Exception:
        pass
    
    try:
        from librepy.auth import auth_model as _auth_models
        for _name in dir(_auth_models):
            _cls = getattr(_auth_models, _name)
            if isinstance(_cls, type) and hasattr(_cls, '_meta'):
                _cls._meta.database = new_db
    except Exception:
        pass
    
    return new_db

get_database_connection() 