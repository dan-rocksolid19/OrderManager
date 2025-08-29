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

from librepy.peewee import sdbc_dbapi

def main(host, port, user, password, database, *args):
    """Test database connection with robust error handling"""
    try:
        # First verify we have all required parameters
        if not database:
            return False, "Please select a database before testing the connection."

        # Establish connection
        conn = sdbc_dbapi.connect(host=host, port=port, user=user, password=password, database=database)
        
        try:
            # Create a cursor and try a simple query to verify connection
            cursor = conn.cursor()
            try:
                # Test query that should work on any PostgreSQL database
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                return True, version
            finally:
                cursor.close()
        finally:
            conn.close()
            
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            return False, "Authentication failed. Please check your username and password."
        elif "connection refused" in error_msg.lower():
            return False, f"Connection refused. Please verify:\n- Host: {host}\n- Port: {port}\n- Server is running"
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            return False, f"Database '{database}' does not exist."
        else:
            return False, f"Connection failed: {error_msg}"