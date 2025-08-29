'''
Base Data Access Object (DAO) for all DAOs in the FertilizerCommandCenter

This module provides a base class with common functionality for database operations.
It ensures proper handling of database connections by using Peewee's model-database binding.
'''

from librepy.peewee.peewee import DoesNotExist, IntegrityError


class BaseDAO:
    """
    Base Data Access Object for all DAOs in the FertilizerCommandCenter.
    Provides common database access patterns and uses the model's bound database connection.
    
    This design follows Peewee's philosophy where models are bound to database instances,
    and all operations automatically use that binding.
    
    Connection Management:
    - Single operations: DAO methods automatically manage connections
    - Multiple operations: Use connection context for efficiency:
      
      with dao.database.connection_context():
          result1 = dao.method1()
          result2 = dao.method2()
    """
    
    def __init__(self, model_class, logger):
        """
        Initialize the BaseDAO
        
        Args:
            model_class: The Peewee model class this DAO operates on
            logger: Logger instance for this DAO
        """
        self.model_class = model_class
        self.logger = logger
    
    @property
    def database(self):
        """
        Get the database instance from the model's metadata.
        This ensures the DAO always uses whatever database the model is currently bound to.
        
        Returns:
            Database: The database instance bound to the model
        """
        return self.model_class._meta.database
    
    def _ensure_connection(self, operation_func):
        """
        Execute database operation, using existing connection if available,
        or creating a new one if needed.
        
        This method provides efficient connection management:
        - If a connection already exists (e.g., within a connection_context), reuse it
        - If no connection exists, create one for this operation only
        
        Args:
            operation_func: Function to execute within connection context
            
        Returns:
            Result of operation_func
            
        Usage:
            return self._ensure_connection(lambda: self.model_class.get_by_id(1))
        """
        if self.database.is_closed():
            with self.database.connection_context():
                return operation_func()
        else:
            return operation_func()
    
    def execute_query(self, query_func, *args, **kwargs):
        """
        Execute a database query with proper connection management.
        
        Args:
            query_func: The function to execute (usually a model's select, get, or create)
            *args: Arguments to pass to the query function
            **kwargs: Keyword arguments to pass to the query function
            
        Returns:
            The result of the query function
            
        Example:
            ```python
            # Instead of directly calling:
            # users = User.select().where(User.active == True)
            
            # Use this pattern:
            users = self.execute_query(
                lambda: list(User.select().where(User.active == True))
            )
            ```
            
        Note:
            This method automatically handles connection management, reusing existing
            connections when available or creating new ones when needed.
        """
        return self._ensure_connection(lambda: query_func(*args, **kwargs))
    
    def safe_execute(self, operation_name, query_func, default_return=None, reraise_integrity=True):
        """
        Execute a query with standardized error handling and logging.
        
        Args:
            operation_name (str): Description of the operation for logging
            query_func: The function to execute
            default_return: Value to return on error (default: None)
            reraise_integrity (bool): Whether to reraise IntegrityError exceptions
            
        Returns:
            The result of query_func or default_return on error
            
        Example:
            ```python
            def get_field_by_id(self, field_id):
                return self.safe_execute(
                    f"fetching field with ID {field_id}",
                    lambda: Field.get_by_id(field_id),
                    default_return=None
                )
            ```
        """
        try:
            return self.execute_query(query_func)
        except DoesNotExist:
            self.logger.info(f"Entity not found during {operation_name}")
            return default_return
        except IntegrityError as e:
            self.logger.error(f"Integrity error during {operation_name}: {str(e)}")
            if reraise_integrity:
                raise
            return default_return
        except Exception as e:
            self.logger.error(f"Error during {operation_name}: {str(e)}")
            return default_return
    
    def get_by_id(self, entity_id, operation_name=None):
        """
        Generic get by ID with standardized error handling.
        Uses the DAO's model class automatically.
        
        Args:
            entity_id: The ID to look up
            operation_name (str): Optional operation description for logging
            
        Returns:
            Model instance or None if not found
        """
        operation_name = operation_name or f"fetching {self.model_class.__name__} with ID {entity_id}"
        return self.safe_execute(
            operation_name,
            lambda: self.model_class.get_by_id(entity_id)
        )
    
    def get_all(self, order_by=None, where_clause=None, operation_name=None):
        """
        Generic get all with optional ordering and filtering.
        Uses the DAO's model class automatically.
        
        Args:
            order_by: Field or expression to order by
            where_clause: Optional where condition
            operation_name (str): Optional operation description for logging
            
        Returns:
            List of model instances or empty list on error
        """
        operation_name = operation_name or f"fetching all {self.model_class.__name__} records"
        
        def query_func():
            query = self.model_class.select()
            if where_clause is not None:
                query = query.where(where_clause)
            if order_by is not None:
                query = query.order_by(order_by)
            return list(query)
        
        return self.safe_execute(operation_name, query_func, default_return=[])
    
    def validate_string_field(self, value, field_name, max_length=None, required=True):
        """
        Validate and normalize string fields.
        
        Args:
            value: The value to validate
            field_name (str): Name of the field for error messages
            max_length (int): Maximum allowed length
            required (bool): Whether the field is required
            
        Returns:
            str: Normalized string value
            
        Raises:
            ValueError: If validation fails
        """
        if value is None or value == "":
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        
        normalized = str(value).strip()
        
        if required and not normalized:
            raise ValueError(f"{field_name} cannot be empty")
        
        if max_length and len(normalized) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters")
        
        return normalized
    
    def validate_numeric_field(self, value, field_name, min_value=None, max_value=None, required=True):
        """
        Validate and convert numeric fields.
        
        Args:
            value: The value to validate
            field_name (str): Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            required (bool): Whether the field is required
            
        Returns:
            float: Converted numeric value or None
            
        Raises:
            ValueError: If validation fails
        """
        if value is None or value == "":
            if required:
                raise ValueError(f"{field_name} is required")
            return None
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid number")
        
        if min_value is not None and numeric_value < min_value:
            raise ValueError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and numeric_value > max_value:
            raise ValueError(f"{field_name} cannot exceed {max_value}")
        
        return numeric_value 