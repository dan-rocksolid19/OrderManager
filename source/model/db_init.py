'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()          # Get the user path of the currently running instance
thisComponent          # Current component instance
getDefaultContext()    # Get the default context
MsgBox()               # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)               # Mri the object. MRI must be installed for this to work
doc_object             # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''

from librepy.model.model import Org, OrgAddress, AcctTrans, CalendarEntryStatus, CalendarEntryOrder

REQUIRED_MODELS = [
    Org, OrgAddress, AcctTrans, CalendarEntryStatus, CalendarEntryOrder
]

def verify_and_create_tables(logger, database):
    """
    Verify if all required tables exist in the database and create them if needed
    Returns tuple of (success, message)
    """
    try:
        try:
            models = REQUIRED_MODELS
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            return False, f"Could not initialize database models: {str(e)}"
        
        # Check if tables exist and create them if they don't
        created_tables = []
        failed_tables = []
        
        for model in models:
            try:
                if not database.table_exists(model._meta.table_name):
                    model.create_table()
                    created_tables.append(model._meta.table_name)
                    logger.info(f"Created table: {model._meta.table_name}")
            except Exception as e:
                failed_tables.append(f"{model._meta.table_name}: {str(e)}")
                logger.error(f"Failed to create table {model._meta.table_name}: {str(e)}")
        
        if failed_tables:
            return False, f"Failed to create the following tables: {', '.join(failed_tables)}"
        
        if created_tables:
            message = f"Successfully created {len(created_tables)} tables: {', '.join(created_tables)}"
        else:
            message = "All required tables already exist"
            
        return True, message
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return False, f"Unexpected error during table verification: {str(e)}"

def initialize_database(logger, database):
    """
    Initialize the database with required tables and default data
    Returns tuple of (success, message)
    """
    success, message = verify_and_create_tables(logger, database)
    if not success:
        database.close()
        return False, f"Table creation failed: {message}"
    
    # Here you can add default data to the database
    
    return True, "Database initialized successfully"