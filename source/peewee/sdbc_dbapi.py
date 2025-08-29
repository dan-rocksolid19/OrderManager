"""
SDBC to Python DB-API 2.0 Wrapper (SDBC_DBAPI)

This module provides a DB-API 2.0 compliant interface to LibreOffice's
SDBC (StarOffice Database Connectivity) PostgreSQL driver.

Features:
- Complete DB-API 2.0 compliance for Python database access
- Conversion between Python and SDBC data types
- Error handling and mapping to DB-API exception hierarchy
- Support for parameterized queries with proper type binding
- Type-aware NULL binding with parameter type inference
- Connection and cursor management
- Optimized performance for large result sets using:
  - Type information caching
  - Row prefetching with configurable batch sizes
  - Fast direct type conversion paths

Performance Optimization:
- For large result sets, increase cursor.arraysize (default: 1000)
- Use cursor.set_prefetch_size(n) to control memory/performance tradeoff
- Consider fetching results in batches with fetchmany() rather than fetchall()
- When processing millions of rows, consider using executemany() with reasonable
  batch sizes to reduce round trips

Usage Notes:
- For type-safe NULL binding, you can provide parameter_types to execute/executemany
- Decimal values are converted to float which may cause precision loss; 
  for applications requiring precise Decimal handling, consider string conversion
- Parameter metadata capabilities depend on the underlying SDBC driver implementation
"""

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.uno import Exception as UnoException
from com.sun.star.sdbc import DataType
import warnings
from decimal import Decimal, InvalidOperation
import datetime

import logging

logger = logging.getLogger(__name__)

# DB-API 2.0 Module Interface
apilevel = '2.0'
threadsafety = 0  # Threads may not share the module or connections
paramstyle = 'qmark'  # Primary style is qmark

# DB-API 2.0 extension. For psycopg2 compatibility.
TRANSACTION_STATUS_IDLE = 0
TRANSACTION_STATUS_ACTIVE = 1
TRANSACTION_STATUS_INTRANS = 2
TRANSACTION_STATUS_INERROR = 3

# Use underscore-prefixed imports to avoid shadowing constructor names
from decimal import Decimal as _Decimal
import datetime as _datetime

# DB-API 2.0 type object class
class _DbType:
    """
    Type objects as defined by PEP 249.
    
    These objects serve as type descriptor constants for providing metadata 
    about database column types via the cursor.description attribute.
    """
    def __init__(self, name):
        self.name = name
    
    def __eq__(self, other):
        # Check if 'other' is the same type as 'self'
        # This is more robust against module reloads than isinstance(other, _DbType)
        if type(self) is type(other): 
            return self.name == other.name
            
        # --- Keep the original logic for comparing with Python types ---
        # Allow comparison with Python types
        # Get the corresponding _DbType for the Python type 'other'
        mapped_db_type = _PY_TYPE_MAP.get(other) 
        # Check if self is equal to that mapped type
        return mapped_db_type is not None and self.name == mapped_db_type.name
    
    def __hash__(self):
        # Make the object hashable based on its immutable name attribute
        return hash(self.name)
    
    def __repr__(self):
        return f"<{self.name}>"

# Module level DB-API 2.0 type objects
STRING = _DbType("STRING")    # Character/string columns
BINARY = _DbType("BINARY")    # Binary columns (BLOB, etc)
NUMBER = _DbType("NUMBER")    # Numeric columns (int, float, decimal)
DATETIME = _DbType("DATETIME")  # Date/time columns
ROWID = _DbType("ROWID")      # Row ID column type

# Mapping from SDBC DataType constants to DB-API type objects
_SDBC_TYPE_MAP = {
    # String types
    DataType.VARCHAR: STRING,
    DataType.CHAR: STRING,
    DataType.LONGVARCHAR: STRING,
    
    # Binary types
    DataType.BINARY: BINARY,
    DataType.VARBINARY: BINARY,
    DataType.LONGVARBINARY: BINARY,
    DataType.BLOB: BINARY,
    
    # Numeric types
    DataType.INTEGER: NUMBER,
    DataType.SMALLINT: NUMBER,
    DataType.TINYINT: NUMBER,
    DataType.BIGINT: NUMBER,
    DataType.FLOAT: NUMBER,
    DataType.REAL: NUMBER,
    DataType.DOUBLE: NUMBER,
    DataType.NUMERIC: NUMBER,
    DataType.DECIMAL: NUMBER,
    DataType.BOOLEAN: NUMBER,  # Typically mapped to NUMBER
    
    # DateTime types
    DataType.DATE: DATETIME,
    DataType.TIME: DATETIME,
    DataType.TIMESTAMP: DATETIME,
    
    # Note: The ROWID type object is included for DB-API 2.0 compliance,
    # but PostgreSQL doesn't have a direct ROWID concept like Oracle.
    # In PostgreSQL, system columns like 'oid' or 'ctid' serve a similar purpose
    # but they're not directly mapped to a specific SDBC DataType.
    # Users should not rely on ROWID for PostgreSQL-specific applications.
    
    # Default for unknown types
    DataType.OTHER: STRING,
}

# Map Python types to DB-API types for equality comparison
_PY_TYPE_MAP = {
    str: STRING,
    bytes: BINARY,
    bytearray: BINARY,
    int: NUMBER,
    float: NUMBER,
    bool: NUMBER,
    _Decimal: NUMBER,
    _datetime.date: DATETIME,
    _datetime.time: DATETIME,
    _datetime.datetime: DATETIME,
}

# Exception hierarchy
class Warning(Exception):
    """Raised for important warnings"""
    pass

class Error(Exception):
    """Base class for all exceptions raised by this module"""
    pass

class InterfaceError(Error):
    """Raised for errors related to the database interface"""
    pass

class DatabaseError(Error):
    """Raised for errors related to the database"""
    pass

class DataError(DatabaseError):
    """Raised for errors related to the data"""
    pass

class OperationalError(DatabaseError):
    """Raised for errors related to the database operation"""
    pass

class IntegrityError(DatabaseError):
    """Raised for integrity constraint violations"""
    pass

class InternalError(DatabaseError):
    """Raised for errors internal to the database"""
    pass

class ProgrammingError(DatabaseError):
    """Raised for programming errors"""
    pass

class NotSupportedError(DatabaseError):
    """Raised for unsupported operations"""
    pass

# Internal utility function to map SDBC exceptions to DB-API exceptions
def _map_sdbc_error(e):
    """
    Map SDBC exceptions to appropriate DB-API exceptions.
    
    This function analyzes UnoException objects from SDBC and determines the 
    appropriate DB-API exception type based on SQLState codes, error codes,
    or message content.
    
    Args:
        e (UnoException): The exception to map
        
    Returns:
        Exception: An appropriate DB-API exception instance
        
    Notes:
        - SQLState codes are checked first (most reliable)
        - Error codes are checked second (if available)
        - Message content is checked last (least reliable)
        - Standard SQLSTATE code classes are used for mapping:
            - Class 23: Integrity constraint violations (foreign key, unique, etc.)
            - Class 22: Data exceptions (invalid data, numeric range, etc.)
            - Class 42: Syntax errors or access rule violations
            - Class 08: Connection exceptions
            - Class 3F: Statement completion issues
    """
    error_msg = str(e)
    sqlstate = None
    error_code = None
    
    # Extract SQLState and ErrorCode if available
    try:
        sqlstate = getattr(e, 'SQLState', None)
        error_code = getattr(e, 'ErrorCode', None)
    except:
        pass
        
    # Map based on SQLState (standard SQL error codes)
    if sqlstate:
        # Class 23: Integrity Constraint Violation
        if sqlstate.startswith('23'):
            return IntegrityError(f"Integrity error [{sqlstate}]: {error_msg}")
        # Class 22: Data Exception
        if sqlstate.startswith('22'):
            return DataError(f"Data error [{sqlstate}]: {error_msg}")
        # Class 42: Syntax Error or Access Rule Violation
        if sqlstate.startswith('42'):
            return ProgrammingError(f"SQL syntax error [{sqlstate}]: {error_msg}")
        # Class 08: Connection Exception
        if sqlstate.startswith('08'):
            return OperationalError(f"Connection error [{sqlstate}]: {error_msg}")
        # Class 3F: Statement Not Prepared
        if sqlstate.startswith('3F'):
            return ProgrammingError(f"Statement not prepared [{sqlstate}]: {error_msg}")
        # Class 28: Invalid Authorization Specification
        if sqlstate.startswith('28'):
            return OperationalError(f"Authorization error [{sqlstate}]: {error_msg}")
        # Class 0A: Feature Not Supported
        if sqlstate.startswith('0A'):
            return NotSupportedError(f"Feature not supported [{sqlstate}]: {error_msg}")
    
    # Fallback to string-based detection (less reliable)
    if "syntax error" in error_msg.lower():
        return ProgrammingError(f"SQL syntax error: {error_msg}")
    if "does not exist" in error_msg.lower():
        return ProgrammingError(f"Object does not exist: {error_msg}")
    if "permission denied" in error_msg.lower():
        return OperationalError(f"Permission denied: {error_msg}")
    if "unique constraint" in error_msg.lower() or "duplicate key" in error_msg.lower():
        return IntegrityError(f"Unique constraint violation: {error_msg}")
    if "foreign key constraint" in error_msg.lower():
        return IntegrityError(f"Foreign key constraint violation: {error_msg}")
    if "check constraint" in error_msg.lower():
        return IntegrityError(f"Check constraint violation: {error_msg}")
    if "not null constraint" in error_msg.lower():
        return IntegrityError(f"Not null constraint violation: {error_msg}")
    if "deadlock" in error_msg.lower():
        return OperationalError(f"Deadlock detected: {error_msg}")
    if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
        return OperationalError(f"Operation timed out: {error_msg}")
    if "out of memory" in error_msg.lower() or "insufficient memory" in error_msg.lower():
        return OperationalError(f"Out of memory: {error_msg}")
    if "too many connections" in error_msg.lower():
        return OperationalError(f"Too many connections: {error_msg}")
    if "division by zero" in error_msg.lower():
        return DataError(f"Division by zero: {error_msg}")
    if "invalid data" in error_msg.lower() or "invalid input" in error_msg.lower():
        return DataError(f"Invalid data: {error_msg}")
    
    # Default case
    return OperationalError(f"Database error: {error_msg}")

# Type constructors
def Date(year, month, day):
    """Construct an object holding a date value."""
    from datetime import date
    return date(year, month, day)

def Time(hour, minute, second):
    """Construct an object holding a time value."""
    from datetime import time
    return time(hour, minute, second)

def Timestamp(year, month, day, hour, minute, second):
    """Construct an object holding a timestamp value."""
    from datetime import datetime
    return datetime(year, month, day, hour, minute, second)

def DateFromTicks(ticks):
    """Construct an object holding a date value from the given ticks value."""
    import time
    return Date(*time.localtime(ticks)[:3])

def TimeFromTicks(ticks):
    """Construct an object holding a time value from the given ticks value."""
    import time
    return Time(*time.localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    """Construct an object holding a timestamp value from the given ticks value."""
    import time
    return Timestamp(*time.localtime(ticks)[:6])

def Binary(string):
    """Construct an object capable of holding a binary (long) string value."""
    return bytes(string)

# Connection function
def connect(dsn=None, user=None, password=None, host=None, database=None, port=5432, connect_timeout=5):
    """
    Connect to a PostgreSQL database using LibreOffice's SDBC driver.
    
    This implements the DB-API 2.0 connect() function with standard parameters in the correct order.
    Additional parameters (port, connect_timeout) are provided as extensions.
    
    Args:
        dsn (str, optional): Data source name (if using DSN-style connection)
        user (str, optional): Username for authentication 
        password (str, optional): Password for authentication
        host (str, optional): Database server hostname or IP address (default: None)
        database (str, optional): Database name to connect to
        port (int, optional): Port number (default: 5432)
        connect_timeout (int, optional): Connection timeout in seconds (default: 5)
        
    Returns:
        Connection: A DB-API 2.0 compliant Connection object
        
    Raises:
        OperationalError: If a connection cannot be established
        InterfaceError: If parameters are invalid
        
    Notes:
        - Either 'database' or 'dsn' must be provided
        - DSN-style connections use the format "sdbc:postgresql:{dsn}"
        - Parameter-style connections build a connection string with the provided parameters
        - Authentication failures typically raise OperationalError with a message from the database
        - Network timeouts are controlled by connect_timeout parameter
        - For SSL connections, use a properly configured DSN
    """
    # Validate essential parameters
    if database is None and dsn is None:
        raise InterfaceError("Either database or dsn must be specified")
    
    try:
        # Build connection URL
        if dsn:
            # DSN-style connection
            connection_url = f"sdbc:postgresql:{dsn}"
        else:
            # Parameter-style connection
            connection_url = f"sdbc:postgresql:dbname={database} host={host or 'localhost'} port={port} connect_timeout={connect_timeout}"
        
        # Create connection properties
        props = []
        if user:
            props.append(PropertyValue(Name="user", Value=user))
        if password:
            props.append(PropertyValue(Name="password", Value=password))
        
        # Get the UNO service manager and SDBC driver manager
        local_context = uno.getComponentContext()
        service_manager = local_context.ServiceManager
        driver_manager = service_manager.createInstanceWithContext(
            "com.sun.star.sdbc.DriverManager", local_context)
        
        # Establish the connection
        sdbc_connection = driver_manager.getConnectionWithInfo(connection_url, tuple(props))
        
        conn = Connection(sdbc_connection)
        logger.debug(f"Connection object created with ID: {id(conn)}")
        return conn
    
    except UnoException as e:
        # Use the new error mapping function
        raise _map_sdbc_error(e)
    except Exception as e:
        raise InterfaceError(f"Error establishing connection: {str(e)}")

class Connection:
    """
    DB-API 2.0 compliant database connection wrapper for SDBC.
    """
    
    def __init__(self, sdbc_connection):
        """
        Initialize a Connection object.
        
        Args:
            sdbc_connection: The underlying SDBC connection object
        """
        self._conn = sdbc_connection
        self.closed = False
        
        # Add required DB-API 2.0 attributes
        self.Error = Error
        self.Warning = Warning
        
    def close(self):
        """Close the connection and release resources."""
        if self.closed:
            logger.debug(f"Connection ID: {id(self)} already closed, returning early")
            return
        
        try:
            # First try standard SDBC close
            self._conn.close()
            
            # Then dispose of the underlying component
            self._conn.dispose()
            
            # Clear the connection reference
            self._conn = None
            
            # Mark the connection as closed
            self.closed = True
            logger.debug(f"Connection ID: {id(self)} closed successfully")
        except UnoException as e:
            self.closed = True
            logger.error(f"UnoException during connection close: {e}")
            raise _map_sdbc_error(e)
            
    def commit(self):
        """Commit any pending transactions."""
        if self.closed:
            raise InterfaceError("Connection is closed")
        try:
            # In SDBC, we need to check if autoCommit is enabled
            # If autoCommit is enabled, there's nothing to commit
            if not self._conn.getAutoCommit():
                self._conn.commit()
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def rollback(self):
        """Roll back pending transactions."""
        if self.closed:
            raise InterfaceError("Connection is closed")
        try:
            # First try standard SDBC rollback
            current_autocommit = self._conn.getAutoCommit()
            
            # Only attempt rollback if autoCommit is disabled or we force it
            if not current_autocommit:
                # Standard rollback should work when autocommit is off
                self._conn.rollback()
            else:
                # If autocommit is on, warn the user that rollback might not work as expected
                warnings.warn(
                    "Attempting to rollback while autocommit is enabled. "
                    "This may not have the expected effect. "
                    "Consider using set_autocommit(False) before operations that need transaction control.",
                    UserWarning  # Use built-in UserWarning instead of Warning
                )
                
                # Try rollback anyway in case the driver supports it
                try:
                    self._conn.rollback()
                except:
                    # Fall back to a SQL ROLLBACK if the standard method fails
                    try:
                        statement = self._conn.createStatement()
                        statement.executeUpdate("ROLLBACK")
                        statement.close()
                        statement.dispose()
                    except Exception as e:
                        warnings.warn(f"Could not execute SQL ROLLBACK: {str(e)}", UserWarning)
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def set_autocommit(self, auto_commit):
        """
        Set the auto-commit mode of the connection.
        
        When auto-commit is enabled, each SQL statement is committed immediately upon execution.
        When disabled, statements are grouped into transactions that must be explicitly committed.
        
        Args:
            auto_commit (bool): True to enable auto-commit, False to disable
        
        Raises:
            InterfaceError: If the connection is closed
            OperationalError: If the database encounters an error changing the mode
        
        Notes:
            - This is an extension to the DB-API 2.0 specification
            - Default auto-commit mode is database-dependent
            - When disabled, you must call commit() to persist changes or rollback() to discard them
            - Setting auto-commit to True will implicitly commit any pending transaction
            - In multi-statement operations, consider disabling auto-commit for better performance
            - Some PostgreSQL features like COPY require auto-commit to be disabled
        """
        if self.closed:
            raise InterfaceError("Connection is closed")
        try:
            # First, attempt to set autocommit mode using standard SDBC method
            self._conn.setAutoCommit(auto_commit)
            
            # Verify that autocommit was actually set
            current_autocommit = self._conn.getAutoCommit()
            
            # If the setting didn't take effect, try an alternative approach
            if current_autocommit != auto_commit:
                # For PostgreSQL, we might need to use direct SQL for some driver versions
                if not auto_commit:
                    # Execute BEGIN to start a transaction when turning autocommit off
                    statement = self._conn.createStatement()
                    statement.executeUpdate("BEGIN")
                    statement.close()
                    statement.dispose()
                else:
                    # If we can't enable autocommit, at least commit any pending transaction
                    self._conn.commit()
                
                # Re-check autocommit state
                current_autocommit = self._conn.getAutoCommit()
                
                # If it still doesn't match, warn the user
                if current_autocommit != auto_commit:
                    warnings.warn(
                        f"Could not set autocommit to {auto_commit}. " 
                        f"The driver reported autocommit is {current_autocommit}. "
                        f"This may affect transaction behavior.",
                        UserWarning  # Use built-in UserWarning instead of Warning
                    )
            
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def cursor(self):
        """Create a new cursor object."""
        if self.closed:
            raise InterfaceError("Connection is closed")
        return Cursor(self)

    def get_transaction_status(self):
        """
        Get the current transaction status.
        This is a partial implementation for Peewee compatibility, as the SDBC
        API does not provide a direct way to inspect transaction status.
        Returns:
            int: TRANSACTION_STATUS_IDLE or TRANSACTION_STATUS_INTRANS.
        """
        try:
            if self._conn.getAutoCommit():
                return TRANSACTION_STATUS_IDLE
            else:
                return TRANSACTION_STATUS_INTRANS
        except UnoException:
            # If connection is dead, assume idle state or handle error
            return TRANSACTION_STATUS_IDLE

    def __enter__(self):
        """
        Enter the runtime context for this connection.
        
        This method allows the connection to be used in a with statement,
        ensuring proper cleanup regardless of how the block exits.
        
        Returns:
            Connection: Self reference
            
        Example:
            ```python
            with connect(database='test') as conn:
                cursor = conn.cursor()
                # Work with the cursor...
            # Connection is automatically closed when exiting the block
            ```
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context for this connection.
        
        This method is called when exiting a with statement block.
        It ensures the connection is properly closed even when exceptions occur.
        
        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The traceback, if an exception was raised
            
        Returns:
            bool: False to propagate exceptions, True to suppress them
        """
        self.close()
        # Return False to propagate exceptions
        return False

class Cursor:
    """
    DB-API 2.0 compliant cursor wrapper for SDBC.
    """
    
    def __init__(self, connection):
        """
        Initialize a Cursor object.
        
        Args:
            connection: The parent Connection object
        """
        self.connection = connection
        self._statement = None
        self._resultset = None
        self.description = None
        self._cached_meta = None  # Cache for column metadata to avoid repeated lookups
        self.rowcount = -1
        self.arraysize = 1000  # Default to a larger batch size for better performance
        self._row_cache = []   # Cache for fetched rows
        self._cache_position = 0  # Position in the row cache
        self._cache_size = 5000  # Number of rows to prefetch
        self.closed = False
        # Cache for tracking parameter types based on previous bindings
        self._parameter_type_cache = {}  # format: {param_index: sdbc_type}
        
    def close(self):
        """Close the cursor, releasing resources."""
        if self.closed:
            return
            
        try:
            if self._resultset is not None:
                try:
                    self._resultset.close()
                    self._resultset.dispose()
                except Exception as e:
                    logger.warning(f"Error closing resultset: {e}")
                finally:
                    self._resultset = None
                
            if self._statement is not None:
                try:
                    self._statement.close()
                    self._statement.dispose()
                except Exception as e:
                    logger.warning(f"Error closing statement: {e}")
                finally:
                    self._statement = None
            
            # Reset cursor state to initial values
            self.description = None
            self._cached_meta = None
            self.rowcount = -1
            
            # Clear the row cache to release memory
            self._row_cache = []
            self._cache_position = 0
            # Clear parameter type cache
            self._parameter_type_cache = {}

            self.connection = None
            self.closed = True
            
        except UnoException as e:
            logger.error(f"UnoException during cursor close: {e}")
            raise _map_sdbc_error(e)
            
    def execute(self, operation, parameters=None, parameter_types=None):
        """
        Execute a database operation.
        
        Args:
            operation (str): SQL statement
            parameters (tuple/list, optional): Parameters for the operation
            parameter_types (list, optional): Type hints for parameters (especially useful for NULL values)
            
        Returns:
            Cursor: Self reference for method chaining
            
        Raises:
            InterfaceError: If cursor is closed
            ProgrammingError: If there's an error in the SQL or parameters
            OperationalError: If there's a database operation error
            
        Type Handling:
            - Python None → SQL NULL (depends on parameter_types for type-safe binding)
            - Python str → SQL VARCHAR/TEXT
            - Python int → SQL INTEGER
            - Python float → SQL DOUBLE PRECISION/FLOAT
            - Python Decimal → SQL NUMERIC/DECIMAL (with potential precision loss, converts to float)
            - Python bool → SQL BOOLEAN
            - Python date → SQL DATE
            - Python time → SQL TIME
            - Python datetime → SQL TIMESTAMP
            - Python bytes/bytearray → SQL BINARY/BLOB
            
        Notes:
            - Parameter binding uses question mark (?) style placeholders
            - Parameter count must match placeholder count
            - For NULL values with specific types, provide parameter_types list
            - Decimal values are converted to float which may cause precision loss
            - For precise Decimal handling, consider binding as string instead
            - Large integers may overflow if they exceed database limits
            - After execution, cursor.description is populated for SELECT queries
            - For non-SELECT operations, rowcount contains affected row count
            - The underlying connection must be open and valid
            
        NULL Binding:
            For reliable NULL binding, consider these approaches (in order of reliability):
            
            1. Provide explicit parameter_types list:
               ```python
               # Using DataType constants
               cursor.execute("INSERT INTO table VALUES (?, ?)", 
                             [None, None], 
                             [DataType.INTEGER, DataType.VARCHAR])
               
               # Using helper method (recommended)
               cursor.execute("INSERT INTO table VALUES (?, ?)", 
                             [None, None], 
                             cursor.create_parameter_types(int, str))
               ```
            
            2. Mix NULL and non-NULL values of the same type:
               ```python
               # Non-NULL values help infer types for subsequent NULL values
               cursor.execute("INSERT INTO table VALUES (?, ?, ?)", 
                             [42, None, "text"])
               ```
               
            3. Default fallback (least reliable):
               If no type information is provided, NULL parameters default to VARCHAR,
               which may cause errors if the target column expects a different type.
        """
        if self.closed:
            raise ProgrammingError("Cursor is closed")
            
        try:
            # Close any existing resultset and statement
            if self._resultset is not None:
                self._resultset.close()
                self._resultset = None
            if self._statement is not None:
                self._statement.close()
                self._statement = None
            
            # Set initial rowcount
            self.rowcount = -1
                
            # For parameterized queries, we use question mark style (?)
            if parameters is not None:
                # Validate and convert parameters
                sql, params = self._convert_parameters(operation, parameters)
                
                # If after conversion we have no parameters, use non-parameterized execution path
                if not params:
                    # Execute a direct statement without parameters
                    try:
                        self._statement = self.connection._conn.createStatement()
                    except UnoException as e:
                        raise _map_sdbc_error(e)
                    
                    # Try to determine if this is a SELECT query by looking at the SQL
                    operation_upper = sql.strip().upper()
                    is_select = operation_upper.startswith("SELECT")
                    
                    try:
                        if is_select:
                            # Execute as SELECT
                            self._resultset = self._statement.executeQuery(sql)
                        else:
                            # Execute as UPDATE/INSERT/DELETE
                            self.rowcount = self._statement.executeUpdate(sql)
                    except UnoException as e:
                        raise _map_sdbc_error(e)
                else:
                    # Normal parameterized query path
                    # Verify we have a valid SQL statement before preparing
                    if not sql or not sql.strip(): # Only check if SQL is genuinely empty or just whitespace
                        raise ProgrammingError("Invalid SQL statement: SQL string is empty")
                    
                    # Create and prepare the statement
                    try:
                        self._statement = self.connection._conn.prepareStatement(sql)
                    except UnoException as e:
                        raise _map_sdbc_error(e)
                    
                    # Bind each parameter
                    for i, param in enumerate(params):
                        # Get type hint if available
                        type_hint = None
                        if parameter_types and i < len(parameter_types):
                            type_hint = parameter_types[i]
                        
                        self._bind_parameter(i + 1, param, type_hint)
                    
                    # Try to determine if this is a SELECT query by looking at the SQL
                    is_select = sql.strip().upper().startswith("SELECT")
                    
                    try:
                        if is_select:
                            # Execute as SELECT
                            self._resultset = self._statement.executeQuery()
                        else:
                            # Execute as UPDATE/INSERT/DELETE
                            self.rowcount = self._statement.executeUpdate()
                    except UnoException as e:
                        raise _map_sdbc_error(e)
            else:
                # Execute a direct statement without parameters
                try:
                    self._statement = self.connection._conn.createStatement()
                except UnoException as e:
                    raise _map_sdbc_error(e)
                
                # Try to determine if this is a SELECT query by looking at the SQL
                # This is a best-effort check - not foolproof for all SQL dialects
                operation_upper = operation.strip().upper()
                is_select = operation_upper.startswith("SELECT")
                
                try:
                    if is_select:
                        # Execute as SELECT
                        self._resultset = self._statement.executeQuery(operation)
                    else:
                        # Execute as UPDATE/INSERT/DELETE
                        self.rowcount = self._statement.executeUpdate(operation)
                except UnoException as e:
                    raise _map_sdbc_error(e)
                
            # Update description if we have a result set
            if self._resultset is not None:
                self._update_description()
                
            return self
        except UnoException as e:
            # Generic catch-all for any other SDBC exceptions
            raise _map_sdbc_error(e)
            
    def executemany(self, operation, seq_of_parameters, parameter_types=None):
        """
        Execute multiple operations efficiently.
        
        This method executes the operation against each parameter set in sequence.
        It's optimized for INSERT, UPDATE, and DELETE operations with many parameter sets.
        
        Args:
            operation (str): SQL statement with parameter placeholders
            seq_of_parameters (sequence): Sequence of parameter sets
            parameter_types (list, optional): Type hints for parameters (especially useful for NULL values)
            
        Returns:
            Cursor: Self reference for method chaining
            
        Raises:
            InterfaceError: If cursor is closed
            ProgrammingError: If there's an error in SQL or parameters
            
        Performance Notes:
            - For optimal performance, consider:
              1. Disabling autocommit before calling executemany
              2. Using reasonable batch sizes (1000-5000 rows)
              3. Explicitly committing after executemany completes
            - Each parameter set is executed individually, not as a true batch operation
            - Total rowcount is the sum of affected rows from all operations
            
        Error Handling:
            - If an error occurs during execution, the operation stops at that point
            - No automatic rollback is performed if an error occurs
            - Previously successful operations in the batch remain committed 
              (unless autocommit is disabled)
            - To implement all-or-nothing behavior, disable autocommit and handle
              exceptions with explicit rollback
            
        Type Handling:
            - Same type conversion rules as execute() apply to each parameter set
            - parameter_types applies the same type hints to all parameter sets
            
        NULL Binding:
            For reliable NULL handling in executemany(), you can:
            
            1. Use the create_parameter_types helper method:
               ```python
               # Using Python types as hints
               param_types = cursor.create_parameter_types(int, str, datetime.date)
               
               # Execute with multiple parameter sets
               cursor.executemany(
                   "INSERT INTO users VALUES (?, ?, ?)",
                   [
                       [1, "Alice", None],
                       [None, "Bob", datetime.date(2020, 1, 1)],
                       [3, None, datetime.date(2021, 5, 15)]
                   ],
                   param_types
               )
               ```
               
            2. Use sequential execute calls with non-NULL values first to establish type cache:
               ```python
               # Execute non-NULL parameters first to establish type patterns
               cursor.execute("INSERT INTO table VALUES (?, ?)", [1, "text"])
               
               # Then execute NULL parameters which can use the established pattern
               cursor.execute("INSERT INTO table VALUES (?, ?)", [None, None])
               ```
        """
        if self.closed:
            raise InterfaceError("Cursor is closed")
            
        try:
            total_rowcount = 0
            for parameters in seq_of_parameters:
                self.execute(operation, parameters, parameter_types)
                # If this was an INSERT/UPDATE/DELETE, accumulate the rowcount
                if self.rowcount != -1:
                    total_rowcount += self.rowcount
            
            # Set the total rowcount if we accumulated any
            if total_rowcount > 0:
                self.rowcount = total_rowcount
                
            return self
        except UnoException as e:
            raise _map_sdbc_error(e)
        except Exception as e:
            if isinstance(e, (ProgrammingError, OperationalError, IntegrityError, DataError)):
                # Re-raise if it's already a DB-API exception
                raise
            else:
                # Wrap other exceptions
                raise ProgrammingError(f"Error in executemany: {str(e)}")
            
    def set_prefetch_size(self, size):
        """
        Set the prefetch cache size for this cursor.
        
        Args:
            size (int): Number of rows to prefetch into memory
            
        Returns:
            None
            
        Note: This is an extension to the DB-API 2.0 specification.
        """
        if size < 1:
            raise ValueError("Prefetch size must be at least 1")
        self._cache_size = size
        
    def _prefetch_rows(self):
        """
        Prefetch a batch of rows into the row cache.
        """
        if self._resultset is None:
            return
            
        # Reset cache
        self._row_cache = []
        self._cache_position = 0
        
        # Prefetch rows
        count = 0
        try:
            while count < self._cache_size:
                if not self._resultset.next():
                    break
                self._row_cache.append(self._get_row())
                count += 1
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def fetchone(self):
        """
        Fetch the next row of a query result set.
        
        This method retrieves a single row from the result set. It advances the cursor
        position to the next row if available. When prefetching is enabled, rows are
        retrieved from the cache for better performance.
        
        Returns:
            tuple: A row as a tuple of values, or None when no more data is available
            
        Raises:
            ProgrammingError: If cursor is closed
            OperationalError: If a database error occurs during fetch
            
        Performance Notes:
            - Uses row prefetching to improve performance on large result sets
            - For optimal performance with large datasets:
              1. Increase arraysize attribute for batch operations (default: 1000)
              2. Adjust prefetch size with set_prefetch_size() if needed
            - Memory usage increases with larger prefetch sizes
            
        Notes:
            - Returns None when no more rows are available
            - Cursor must be associated with a result set from a prior execute() call
            - Type conversion to Python types happens automatically
            - NULL values are converted to Python None
        """
        if self.closed:
            raise ProgrammingError("Cursor is closed")
        
        if self._resultset is None:
            return None
            
        try:
            # Check if we have cached rows
            if self._row_cache and self._cache_position < len(self._row_cache):
                row = self._row_cache[self._cache_position]
                self._cache_position += 1
                return row
                
            # If we've exhausted the cache or have no cache, try to get the next row directly
            if self._resultset.next():
                row = self._get_row()
                
                # If this is the first row after exhausting the cache, prefetch more rows
                if self._cache_position >= len(self._row_cache):
                    # Add this row to a new cache and prefetch more
                    self._row_cache = [row]
                    self._cache_position = 1
                    
                    # Prefetch more rows (one less since we already fetched one)
                    count = 1
                    while count < self._cache_size:
                        if not self._resultset.next():
                            break
                        self._row_cache.append(self._get_row())
                        count += 1
                    
                    # Return the first row we already fetched
                    return row
                else:
                    return row
            
            return None
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def fetchmany(self, size=None):
        """
        Fetch the next set of rows of a query result.
        
        This method retrieves multiple rows from the result set efficiently, using
        the row cache when possible and fetching additional rows as needed.
        
        Args:
            size (int, optional): The number of rows to fetch. Defaults to cursor's arraysize.
        
        Returns:
            list: A list of rows, each row as a tuple of values
            
        Raises:
            ProgrammingError: If cursor is closed
            OperationalError: If a database error occurs during fetch
            
        Performance Notes:
            - For large result sets, prefer fetchmany() over fetchall() to control memory usage
            - The default size is determined by the cursor's arraysize attribute (default: 1000)
            - Rows are retrieved from the prefetch cache when available
            - Setting an appropriate arraysize can significantly improve performance:
              * Too small: many round-trips to the database
              * Too large: excessive memory usage
            - After fetching, the cache is refreshed if depleted
            
        Notes:
            - Returns an empty list if no rows are available
            - Result will contain fewer than 'size' rows if fewer are available
            - Type conversion to Python types happens automatically
            - NULL values are converted to Python None
        """
        if self.closed:
            raise ProgrammingError("Cursor is closed")
        
        if size is None:
            size = self.arraysize
            
        # Optimized batch fetching using the row cache
        result = []
        
        # First, get any rows from the existing cache
        while self._row_cache and self._cache_position < len(self._row_cache) and len(result) < size:
            result.append(self._row_cache[self._cache_position])
            self._cache_position += 1
            
        # If we need more rows, fetch them directly
        remaining = size - len(result)
        if remaining > 0 and self._resultset is not None:
            try:
                # Use a smaller loop that doesn't create a new cache for each row
                for _ in range(remaining):
                    if not self._resultset.next():
                        break
                    result.append(self._get_row())
                    
                # After this direct fetch, if we've fetched some rows and our cache is depleted,
                # it's a good time to refresh the cache for future fetches
                if len(result) > len(self._row_cache) - self._cache_position:
                    self._prefetch_rows()
            except UnoException as e:
                raise _map_sdbc_error(e)
                
        return result
        
    def fetchall(self):
        """
        Fetch all (remaining) rows of a query result.
        
        This method retrieves all remaining rows from the result set, starting from
        the current cursor position. It uses the row cache when possible and fetches
        additional rows as needed.
        
        Returns:
            list: A list of all remaining rows, each row as a tuple of values
            
        Raises:
            ProgrammingError: If cursor is closed
            OperationalError: If a database error occurs during fetch
            
        Performance Notes:
            - This method may consume a large amount of memory for large result sets
            - For memory efficiency with large result sets, consider:
              1. Using fetchmany() with appropriate batch sizes
              2. Processing rows iteratively rather than all at once
            - For very large results (millions of rows), this method may cause
              out-of-memory conditions
            
        Notes:
            - Returns an empty list if no rows are available
            - Cursor position is exhausted after this call
            - Row cache is reset after fetchall() completes
            - Type conversion to Python types happens automatically
            - NULL values are converted to Python None
        """
        if self.closed:
            raise ProgrammingError("Cursor is closed")
        
        if self._resultset is None:
            return []
            
        # Start with any rows from the existing cache
        result = []
        if self._row_cache and self._cache_position < len(self._row_cache):
            result.extend(self._row_cache[self._cache_position:])
        
        # Then fetch all remaining rows
        try:
            while self._resultset.next():
                result.append(self._get_row())
        except UnoException as e:
            raise _map_sdbc_error(e)
            
        # Reset the cache since we've fetched everything
        self._row_cache = []
        self._cache_position = 0
            
        return result
        
    def _convert_parameters(self, operation, parameters):
        """
        Validate parameters for qmark style used by this driver.

        Args:
            operation (str): SQL statement with parameter placeholders (?)
            parameters (tuple/list): Parameters to substitute

        Returns:
            tuple: (operation, parameter_list) - operation is unchanged

        Raises:
            ProgrammingError: If there is a parameter count mismatch
        """
        if not parameters:
            # No parameters provided, SQL should have no placeholders
            if '?' in operation:
                pass
            return operation, []

        # Ensure parameters is a sequence if not None
        if not isinstance(parameters, (list, tuple)):
            parameters = [parameters] # Handle single parameter case

        qmark_count = operation.count('?')

        # Validate parameter count against '?' placeholders
        if qmark_count != len(parameters):
            raise ProgrammingError(
                f"Parameter count mismatch: SQL statement has {qmark_count} '?' placeholders, "
                f"but {len(parameters)} parameters were provided. SQL: {operation!r}"
            )

        # No conversion needed, just return the original operation and params
        return operation, parameters
        
    def _infer_parameter_type(self, index, sql_type_hint=None):
        """
        Infer parameter type for NULL binding based on available information.
        
        This method implements a multi-strategy approach to determine the most appropriate
        SDBC DataType for NULL parameters, in order of reliability:
        
        1. Use directly provided type hint (most reliable)
        2. Check parameter metadata if available from SDBC driver
        3. Look up previously bound non-NULL values at the same position
        4. Use generic VARCHAR as fallback (least reliable)
        
        Args:
            index (int): Parameter index (1-based)
            sql_type_hint: Optional type hint provided by caller (SDBC DataType constant)
            
        Returns:
            int: SDBC DataType constant appropriate for the parameter
            
        Notes:
            - For reliable NULL binding, always provide parameter_types to execute/executemany
            - Type inference from previous non-NULL parameters only works within the same prepared
              statement and position
            - The fallback to VARCHAR is a safe default but may not be optimal for all data types
            - For improved NULL binding reliability, consider:
                1. Providing explicit parameter_types (most reliable)
                2. Binding non-NULL values before NULL values when possible
                3. Avoiding binding only NULL values without type hints
        """
        # 1. Use directly provided type hint if available (highest priority)
        if sql_type_hint is not None:
            return sql_type_hint
        
        # 2. Try to get type from parameter metadata if available
        try:
            param_meta = self._statement.getParameterMetaData()
            if param_meta:
                try:
                    # Get parameter type directly from driver metadata
                    return param_meta.getParameterType(index)
                except Exception:
                    # If getParameterType fails, try other methods
                    pass
        except Exception:
            # Parameter metadata not available, continue with other approaches
            pass
            
        # 3. Check if we have seen a non-NULL value at this position before
        # This uses our cached parameter types from previous bindings
        if index in self._parameter_type_cache:
            return self._parameter_type_cache[index]
            
        # 4. If all else fails, use generic VARCHAR
        # This is a safe default but may not be optimal for all cases
        return DataType.VARCHAR
        
    def _bind_parameter(self, index, value, sql_type_hint=None):
        """
        Bind a parameter to a prepared statement.
        
        This internal method handles type conversion from Python types to SDBC types
        and properly binds parameters to prepared statements.
        
        Args:
            index (int): Parameter index (1-based)
            value: Parameter value
            sql_type_hint: Optional SQL type hint for NULL values (SDBC DataType constant)
            
        Raises:
            OperationalError: If there's a database error during binding
            ProgrammingError: If there's a type conversion error
            
        Type Handling:
            - None → NULL (uses type_hint or inferred type)
            - str → VARCHAR/TEXT (setString)
            - int → INTEGER (setInt)
            - float → DOUBLE PRECISION (setDouble)
            - Decimal → DOUBLE PRECISION (setDouble, precision loss possible)
            - bool → BOOLEAN (setBoolean)
            - date → DATE (setDate with SDBC Date structure)
            - time → TIME (setTime with SDBC Time structure)
            - datetime → TIMESTAMP (setTimestamp with SDBC DateTime structure)
            - bytes/bytearray → BINARY (setBytes with UNO ByteSequence)
            - Other types → VARCHAR (converted to string)
            
        Notes:
            - For NULL values, type_hint should be a SDBC DataType constant
            - If no type_hint is provided for NULL, type will be inferred
            - Decimal values are converted to float which may cause precision loss
            - For precise Decimal values, consider binding as string
            - datetime binding attempts to use struct binding first, with fallback to string
        """
        try:
            # Handle None (NULL)
            if value is None:
                # Get appropriate type for NULL value
                param_type = self._infer_parameter_type(index, sql_type_hint)
                self._statement.setNull(index, param_type)
            # String types
            elif isinstance(value, str):
                self._statement.setString(index, value)
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.VARCHAR
            # Numeric types
            elif isinstance(value, int):
                self._statement.setInt(index, value)
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.INTEGER
            elif isinstance(value, float):
                self._statement.setDouble(index, value)
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.DOUBLE
            elif isinstance(value, Decimal):
                # NOTE: Direct Decimal binding is not available in SDBC API.
                # Using setDouble which may cause precision loss for Decimal values.
                # For applications requiring precise Decimal handling, consider:
                # 1. Converting to string: self._statement.setString(index, str(value))
                # 2. Or custom handling based on the required precision
                self._statement.setDouble(index, float(value))
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.DECIMAL
            # Boolean type
            elif isinstance(value, bool):
                self._statement.setBoolean(index, value)
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.BOOLEAN
            # Date/Time types
            elif isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                # Create an SDBC Date object
                try:
                    # Use util.Date for date values
                    sdbc_date = uno.createUnoStruct("com.sun.star.util.Date")
                    sdbc_date.Year = value.year
                    sdbc_date.Month = value.month
                    sdbc_date.Day = value.day
                    self._statement.setDate(index, sdbc_date)
                    # Cache parameter type for future NULL bindings
                    self._parameter_type_cache[index] = DataType.DATE
                except Exception as e:
                    # Fallback to sdbc.Date if util.Date fails
                    try:
                        sdbc_date = uno.createUnoStruct("com.sun.star.sdbc.Date")
                        sdbc_date.Year = value.year
                        sdbc_date.Month = value.month
                        sdbc_date.Day = value.day
                        self._statement.setDate(index, sdbc_date)
                        # Cache parameter type for future NULL bindings
                        self._parameter_type_cache[index] = DataType.DATE
                    except Exception as e2:
                        raise OperationalError(f"Error binding date parameter: {str(e2)}")
            elif isinstance(value, datetime.time):
                # Create an SDBC Time object
                try:
                    # Use util.Time for time values
                    sdbc_time = uno.createUnoStruct("com.sun.star.util.Time")
                    sdbc_time.Hours = value.hour
                    sdbc_time.Minutes = value.minute
                    sdbc_time.Seconds = value.second
                    self._statement.setTime(index, sdbc_time)
                    # Cache parameter type for future NULL bindings
                    self._parameter_type_cache[index] = DataType.TIME
                except Exception as e:
                    # Fallback to sdbc.Time if util.Time fails
                    try:
                        sdbc_time = uno.createUnoStruct("com.sun.star.sdbc.Time")
                        sdbc_time.Hours = value.hour
                        sdbc_time.Minutes = value.minute
                        sdbc_time.Seconds = value.second
                        self._statement.setTime(index, sdbc_time)
                        # Cache parameter type for future NULL bindings
                        self._parameter_type_cache[index] = DataType.TIME
                    except Exception as e2:
                        raise OperationalError(f"Error binding time parameter: {str(e2)}")
            elif isinstance(value, datetime.datetime):
                # Try to create and use a proper UNO DateTime structure
                try:
                    # First attempt with util.DateTime (preferred)
                    sdbc_datetime = uno.createUnoStruct("com.sun.star.util.DateTime")
                    sdbc_datetime.Year = value.year
                    sdbc_datetime.Month = value.month
                    sdbc_datetime.Day = value.day
                    sdbc_datetime.Hours = value.hour
                    sdbc_datetime.Minutes = value.minute
                    sdbc_datetime.Seconds = value.second
                    # Convert microseconds to nanoseconds
                    sdbc_datetime.NanoSeconds = value.microsecond * 1000
                    
                    # Now try to use setTimestamp if available
                    try:
                        self._statement.setTimestamp(index, sdbc_datetime)
                        # Cache parameter type for future NULL bindings
                        self._parameter_type_cache[index] = DataType.TIMESTAMP
                    except Exception:
                        # If setTimestamp isn't available or doesn't accept util.DateTime,
                        # fall back to string conversion
                        iso_datetime = value.isoformat(' ')
                        self._statement.setString(index, iso_datetime)
                        # Cache parameter type for future NULL bindings
                        self._parameter_type_cache[index] = DataType.VARCHAR
                except Exception:
                    # Fall back to string conversion if structure creation fails
                    iso_datetime = value.isoformat(' ')
                    self._statement.setString(index, iso_datetime)
                    # Cache parameter type for future NULL bindings
                    self._parameter_type_cache[index] = DataType.VARCHAR
            # Bytestring/Buffer (for BLOB type)
            elif isinstance(value, (bytes, bytearray)):
                self._statement.setBytes(index, uno.ByteSequence(value))
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.BLOB
            # Default handling for other types - convert to string
            else:
                self._statement.setString(index, str(value))
                # Cache parameter type for future NULL bindings
                self._parameter_type_cache[index] = DataType.VARCHAR
        except UnoException as e:
            raise _map_sdbc_error(e)
        except Exception as e:
            raise ProgrammingError(f"Error converting parameter at index {index}: {str(e)}")
            
    def _update_description(self):
        """Update the description attribute based on result set metadata."""
        if self._resultset is not None:
            try:
                metadata = self._resultset.getMetaData()
                column_count = metadata.getColumnCount()
                self.description = []
                
                # Initialize the column metadata cache
                self._cached_meta = {'types': [], 'names': [], 'precision': [], 'scale': []}
                
                for i in range(1, column_count + 1):
                    name = metadata.getColumnName(i)
                    sdbc_type_code = metadata.getColumnType(i)
                    
                    # Store the raw SDBC type code in our cache for faster lookups
                    self._cached_meta['types'].append(sdbc_type_code)
                    self._cached_meta['names'].append(name)
                    self._cached_meta['precision'].append(metadata.getPrecision(i))
                    self._cached_meta['scale'].append(metadata.getScale(i))
                    
                    # Map SDBC type to DB-API type
                    dbapi_type = _SDBC_TYPE_MAP.get(sdbc_type_code, STRING)  # Default to STRING if unknown
                    
                    display_size = metadata.getColumnDisplaySize(i)
                    internal_size = metadata.getPrecision(i)
                    precision = metadata.getPrecision(i)
                    scale = metadata.getScale(i)
                    null_ok = metadata.isNullable(i) != 0
                    
                    # Use the mapped DB-API type, not the raw SDBC type code
                    self.description.append((name, dbapi_type, display_size, 
                                           internal_size, precision, scale, null_ok))
            except UnoException as e:
                raise _map_sdbc_error(e)
                
    def _get_row(self):
        """
        Convert the current row to a tuple of Python values.
        
        Returns:
            tuple: Current row as a tuple of values
        """
        if self._resultset is None:
            return None
            
        try:
            row = []
            column_count = len(self.description)
            
            # Use cached type information for faster lookups
            cached_types = self._cached_meta['types'] if self._cached_meta else None
            
            # If _cached_meta isn't populated, we need to ensure it's created
            if not cached_types:
                # Force update of metadata cache
                self._update_description()
                cached_types = self._cached_meta['types']
                
            for i in range(1, column_count + 1):
                # Always use the optimized method with direct SDBC type information
                sdbc_type = cached_types[i-1]
                value = self._get_value_by_index_and_type(i, sdbc_type)
                    
                if self._resultset.wasNull():
                    row.append(None)
                else:
                    row.append(value)
                    
            return tuple(row)
        except UnoException as e:
            raise _map_sdbc_error(e)
            
    def _get_value_by_index_and_type(self, index, sdbc_type):
        """
        Optimized method to get a value from result set based on its SDBC type.
        
        This method provides a fast path for retrieving and converting values from
        the result set, avoiding expensive metadata lookups for improved performance.
        
        Args:
            index (int): Column index (1-based)
            sdbc_type (int): SDBC DataType constant
            
        Returns:
            The converted value in appropriate Python type
            
        Raises:
            OperationalError: If there's a database error during retrieval
            
        Performance Notes:
            - Significantly faster than _get_value_by_type for large result sets
            - Avoids repeated metadata lookups by using cached type information
            - Uses direct type-specific getters when possible
            - Falls back to string conversion for problematic cases
            
        Type Conversions:
            - VARCHAR/CHAR/LONGVARCHAR → str (getString)
            - INTEGER/SMALLINT/TINYINT → int (getInt)
            - BIGINT → int (using string conversion to avoid overflow)
            - DOUBLE/FLOAT/REAL → float (getDouble)
            - BOOLEAN → bool (getBoolean)
            - DATE → datetime.date (using SDBC Date structure)
            - TIME → datetime.time (using SDBC Time structure)
            - TIMESTAMP → datetime.datetime (using SDBC Timestamp structure or string parsing)
            - NUMERIC/DECIMAL → decimal.Decimal or float (string conversion for precision)
            - BINARY/BLOB → bytes (using UNO ByteSequence)
            - Other types → str (fallback to getString)
            
        Notes:
            - NULL values are checked separately after retrieval
            - For timestamp values, direct structure access is attempted first
            - For problematic types, string conversion is used as a fallback
            - Large integers (BIGINT) use string conversion to avoid overflow
            - Decimal values are converted via string to maintain precision
        """
        # Fast path for common types
        try:
            # Handle different SDBC types directly without needing to call getMetaData()
            if sdbc_type == DataType.VARCHAR or sdbc_type == DataType.CHAR or sdbc_type == DataType.LONGVARCHAR:
                return self._resultset.getString(index)
            elif sdbc_type == DataType.INTEGER or sdbc_type == DataType.SMALLINT or sdbc_type == DataType.TINYINT:
                return self._resultset.getInt(index)
            elif sdbc_type == DataType.BIGINT:
                # For very large integers, getString might be safer to avoid overflow
                big_int_str = self._resultset.getString(index)
                return int(big_int_str) if big_int_str else 0
            elif sdbc_type == DataType.DOUBLE or sdbc_type == DataType.FLOAT or sdbc_type == DataType.REAL:
                return self._resultset.getDouble(index)
            elif sdbc_type == DataType.BOOLEAN:
                return self._resultset.getBoolean(index)
            elif sdbc_type == DataType.DATE:
                sdbc_date = self._resultset.getDate(index)
                if self._resultset.wasNull():
                    return None
                return Date(sdbc_date.Year, sdbc_date.Month, sdbc_date.Day)
            elif sdbc_type == DataType.TIME:
                sdbc_time = self._resultset.getTime(index)
                if self._resultset.wasNull():
                    return None
                return Time(sdbc_time.Hours, sdbc_time.Minutes, sdbc_time.Seconds)
            elif sdbc_type == DataType.TIMESTAMP:
                # Try to get timestamp directly first
                try:
                    sdbc_timestamp = self._resultset.getTimestamp(index)
                    if self._resultset.wasNull():
                        return None
                    return Timestamp(
                        sdbc_timestamp.Year,
                        sdbc_timestamp.Month,
                        sdbc_timestamp.Day,
                        sdbc_timestamp.Hours,
                        sdbc_timestamp.Minutes,
                        sdbc_timestamp.Seconds
                    )
                except:
                    # Fall back to string parsing
                    timestamp_str = self._resultset.getString(index)
                    if not timestamp_str or self._resultset.wasNull():
                        return None
                    # Simple parsing for common timestamp format
                    if ' ' in timestamp_str and ':' in timestamp_str:
                        date_part, time_part = timestamp_str.split(' ', 1)
                        year, month, day = map(int, date_part.split('-'))
                        time_parts = time_part.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(float(time_parts[2])) if len(time_parts) > 2 else 0
                        return Timestamp(year, month, day, hour, minute, second)
                    return timestamp_str
            elif sdbc_type == DataType.NUMERIC or sdbc_type == DataType.DECIMAL:
                # Get numeric/decimal as string and convert to maintain precision
                val_str = self._resultset.getString(index)
                if self._resultset.wasNull():
                    return None
                try:
                    return Decimal(val_str)
                except (ValueError, InvalidOperation):
                    return float(val_str) if val_str else 0.0
            elif sdbc_type == DataType.BINARY or sdbc_type == DataType.VARBINARY or sdbc_type == DataType.LONGVARBINARY or sdbc_type == DataType.BLOB:
                return bytes(self._resultset.getBytes(index))
            else:
                # Fall back to string for types we don't handle specifically
                return self._resultset.getString(index)
        except UnoException as e:
            # Fall back to string as a last resort
            try:
                return self._resultset.getString(index)
            except:
                raise _map_sdbc_error(e)
            
    # Keep the original method for backward compatibility            
    def _get_value_by_type(self, index, type_code):
        """
        Get value from result set based on its SQL type.
        
        Args:
            index (int): Column index (1-based)
            type_code (_DbType): DB-API type object from cursor.description
            
        Returns:
            The converted value
            
        Notes:
            - This method is kept only for backward compatibility
            - It's a thin wrapper around _get_value_by_index_and_type
            - New code should use _get_value_by_index_and_type directly
        """
        # Get SDBC type information from the cached metadata or determine it from the DB-API type
        if self._cached_meta and 'types' in self._cached_meta and len(self._cached_meta['types']) >= index:
            return self._get_value_by_index_and_type(index, self._cached_meta['types'][index-1])
        
        # If cached metadata doesn't have this column, we need to use the DB-API type
        # to determine the appropriate SDBC type
        if type_code == NUMBER:
            return self._get_value_by_index_and_type(index, DataType.NUMERIC)
        elif type_code == STRING:
            return self._get_value_by_index_and_type(index, DataType.VARCHAR)
        elif type_code == BINARY:
            return self._get_value_by_index_and_type(index, DataType.BINARY)
        elif type_code == DATETIME:
            return self._get_value_by_index_and_type(index, DataType.TIMESTAMP)
        elif type_code == ROWID:
            # PostgreSQL doesn't have a standard ROWID concept like Oracle
            # Return as string since it could be OID or ctid or any other unique identifier
            return self._get_value_by_index_and_type(index, DataType.VARCHAR)
        else:
            # Default to VARCHAR for unknown types
            return self._get_value_by_index_and_type(index, DataType.VARCHAR)

    def create_parameter_types(self, *type_specs):
        """
        Create a list of parameter type hints for use with execute and executemany.
        
        This helper method makes it easier to provide type hints for NULL values and
        ensures that the correct SDBC DataType constants are used.
        
        Args:
            *type_specs: Variable list of type specifications, which can be:
                - SDBC DataType constants (e.g., DataType.INTEGER)
                - Python type objects (e.g., int, str, float)
                - DB-API type objects (e.g., NUMBER, STRING)
                - None for parameters where type inference is acceptable
                
        Returns:
            list: A list of SDBC DataType constants suitable for parameter_types argument
            
        Examples:
            # Using SDBC DataType constants
            types = cursor.create_parameter_types(DataType.INTEGER, DataType.VARCHAR)
            
            # Using Python types
            types = cursor.create_parameter_types(int, str, float)
            
            # Using DB-API type objects
            types = cursor.create_parameter_types(NUMBER, STRING, NUMBER)
            
            # Mixed approach
            types = cursor.create_parameter_types(int, DataType.VARCHAR, None, NUMBER)
            
            # Using with execute
            cursor.execute("INSERT INTO users VALUES (?, ?, ?)", 
                          [None, "test", None],
                          cursor.create_parameter_types(int, str, datetime.date))
        """
        result = []
        
        for type_spec in type_specs:
            if type_spec is None:
                # None means no specific type hint, append None to let _infer_parameter_type handle it
                result.append(None)
            elif isinstance(type_spec, int) and hasattr(DataType, 'VARCHAR'):
                # It's already a SDBC DataType constant
                result.append(type_spec)
            elif type_spec == int or type_spec == NUMBER:
                result.append(DataType.INTEGER)
            elif type_spec == float:
                result.append(DataType.DOUBLE)
            elif type_spec == str or type_spec == STRING:
                result.append(DataType.VARCHAR)
            elif type_spec == bool:
                result.append(DataType.BOOLEAN)
            elif type_spec == datetime.date:
                result.append(DataType.DATE)
            elif type_spec == datetime.time:
                result.append(DataType.TIME)
            elif type_spec == datetime.datetime or type_spec == DATETIME:
                result.append(DataType.TIMESTAMP)
            elif type_spec == bytes or type_spec == bytearray or type_spec == BINARY:
                result.append(DataType.BLOB)
            elif type_spec == Decimal:
                result.append(DataType.DECIMAL)
            elif type_spec == ROWID:
                # PostgreSQL doesn't have a direct ROWID type, use VARCHAR
                result.append(DataType.VARCHAR)
            else:
                # Unknown type, default to VARCHAR
                result.append(DataType.VARCHAR)
                
        return result

    def __iter__(self):
        """
        Return the cursor as its own iterator.
        
        This method allows the cursor to be used as an iterator in a for loop.
        Each iteration will yield the next row from the result set.
        
        Returns:
            Cursor: Self reference as iterator
            
        Example:
            ```python
            cursor.execute("SELECT * FROM users")
            for row in cursor:
                print(row)
            ```
        """
        return self
        
    def __next__(self):
        """
        Return the next row from the result set.
        
        This method is called automatically when iterating over the cursor.
        It fetches one row at a time until the result set is exhausted.
        
        Returns:
            tuple: The next row as a tuple of values
            
        Raises:
            StopIteration: When there are no more rows to fetch
            
        Example:
            ```python
            cursor.execute("SELECT * FROM users")
            try:
                while True:
                    row = next(cursor)
                    print(row)
            except StopIteration:
                pass
            ```
        """
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def __enter__(self):
        """
        Enter the runtime context for this cursor.
        
        This method allows the cursor to be used in a with statement,
        ensuring proper cleanup regardless of how the block exits.
        
        Returns:
            Cursor: Self reference
            
        Example:
            ```python
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                for row in cursor:
                    print(row)
            # Cursor is automatically closed when exiting the block
            ```
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context for this cursor.
        
        This method is called when exiting a with statement block.
        It ensures the cursor is properly closed even when exceptions occur.
        
        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception value, if an exception was raised
            exc_tb: The traceback, if an exception was raised
            
        Returns:
            bool: False to propagate exceptions, True to suppress them
        """
        self.close()
        # Return False to propagate exceptions
        return False
