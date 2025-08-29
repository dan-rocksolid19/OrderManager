'''
Utility module for converting between Python types and UNO types.

This module provides functions to convert Python standard types (datetime, date, etc.)
to their UNO equivalents for use with LibreOffice UNO API.
'''

import datetime
import logging
import uno

logger = logging.getLogger(__name__)

def python_date_to_uno(py_date):
    """
    Convert Python datetime.date to com.sun.star.util.Date.
    
    Args:
        py_date (datetime.date): Python date object to convert
        
    Returns:
        com.sun.star.util.Date or None: Converted UNO date object, or None if input is None
    """
    if not py_date:
        return None
        
    try:
        uno_date = uno.createUnoStruct("com.sun.star.util.Date")
        uno_date.Year = py_date.year
        uno_date.Month = py_date.month
        uno_date.Day = py_date.day
        return uno_date
    except Exception as e:
        logger.error("Error converting date %s to UNO struct: %s" % (str(py_date), str(e)))
        return None

def python_datetime_to_uno(py_datetime):
    """
    Convert Python datetime.datetime to com.sun.star.util.DateTime.
    
    Args:
        py_datetime (datetime.datetime): Python datetime object to convert
        
    Returns:
        com.sun.star.util.DateTime or None: Converted UNO datetime object, or None if input is None
    """
    if not py_datetime:
        return None
        
    try:
        uno_datetime = uno.createUnoStruct("com.sun.star.util.DateTime")
        uno_datetime.Year = py_datetime.year
        uno_datetime.Month = py_datetime.month
        uno_datetime.Day = py_datetime.day
        uno_datetime.Hours = py_datetime.hour
        uno_datetime.Minutes = py_datetime.minute
        uno_datetime.Seconds = py_datetime.second
        uno_datetime.NanoSeconds = py_datetime.microsecond * 1000
        return uno_datetime
    except Exception as e:
        logger.error("Error converting datetime %s to UNO struct: %s" % (str(py_datetime), str(e)))
        return None

def python_time_to_uno(py_time):
    """
    Convert Python datetime.time to com.sun.star.util.Time.
    
    Args:
        py_time (datetime.time): Python time object to convert
        
    Returns:
        com.sun.star.util.Time or None: Converted UNO time object, or None if input is None
    """
    if not py_time:
        return None
        
    try:
        uno_time = uno.createUnoStruct("com.sun.star.util.Time")
        uno_time.Hours = py_time.hour
        uno_time.Minutes = py_time.minute
        uno_time.Seconds = py_time.second
        uno_time.NanoSeconds = py_time.microsecond * 1000 if hasattr(py_time, 'microsecond') else 0
        return uno_time
    except Exception as e:
        logger.error("Error converting time %s to UNO struct: %s" % (str(py_time), str(e)))
        return None

def auto_convert_to_uno(value):
    """
    Automatically convert Python values to UNO equivalents based on type.
    
    This is a convenience function that detects the type of the input value
    and calls the appropriate converter function.
    
    Args:
        value: Python value to convert
        
    Returns:
        Converted UNO object or original value if no conversion needed
    """
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return python_date_to_uno(value)
    elif isinstance(value, datetime.datetime):
        return python_datetime_to_uno(value)
    elif isinstance(value, datetime.time):
        return python_time_to_uno(value)
    else:
        # Return original value for types that don't need conversion
        return value

def uno_date_to_python(uno_date):
    """
    Convert com.sun.star.util.Date to Python datetime.date.
    
    Args:
        uno_date (com.sun.star.util.Date): UNO date object to convert
        
    Returns:
        datetime.date or None: Converted Python date object, or None if input is None
    """
    if not uno_date:
        return None
        
    try:
        return datetime.date(
            year=uno_date.Year,
            month=uno_date.Month,
            day=uno_date.Day
        )
    except Exception as e:
        logger.error("Error converting UNO date %s to Python: %s" % (str(uno_date), str(e)))
        return None

def uno_datetime_to_python(uno_datetime):
    """
    Convert com.sun.star.util.DateTime to Python datetime.datetime.
    
    Args:
        uno_datetime (com.sun.star.util.DateTime): UNO datetime object to convert
        
    Returns:
        datetime.datetime or None: Converted Python datetime object, or None if input is None
    """
    if not uno_datetime:
        return None
        
    try:
        return datetime.datetime(
            year=uno_datetime.Year,
            month=uno_datetime.Month,
            day=uno_datetime.Day,
            hour=uno_datetime.Hours,
            minute=uno_datetime.Minutes,
            second=uno_datetime.Seconds,
            microsecond=int(uno_datetime.NanoSeconds / 1000)
        )
    except Exception as e:
        logger.error("Error converting UNO datetime %s to Python: %s" % (str(uno_datetime), str(e)))
        return None

def uno_time_to_python(uno_time):
    """
    Convert com.sun.star.util.Time to Python datetime.time.
    
    Args:
        uno_time (com.sun.star.util.Time): UNO time object to convert
        
    Returns:
        datetime.time or None: Converted Python time object, or None if input is None
    """
    if not uno_time:
        return None
        
    try:
        return datetime.time(
            hour=uno_time.Hours,
            minute=uno_time.Minutes,
            second=uno_time.Seconds,
            microsecond=int(uno_time.NanoSeconds / 1000)
        )
    except Exception as e:
        logger.error("Error converting UNO time %s to Python: %s" % (str(uno_time), str(e)))
        return None

def auto_convert_from_uno(value):
    """
    Automatically convert UNO values to Python equivalents based on type.
    
    This is a convenience function that detects the type of the input value
    and calls the appropriate converter function.
    
    Args:
        value: UNO value to convert
        
    Returns:
        Converted Python object or original value if no conversion needed
    """
    try:
        if hasattr(value, 'Year') and hasattr(value, 'Month') and hasattr(value, 'Day'):
            if hasattr(value, 'Hours'):
                return uno_datetime_to_python(value)
            else:
                return uno_date_to_python(value)
        elif hasattr(value, 'Hours') and hasattr(value, 'Minutes') and hasattr(value, 'Seconds'):
            return uno_time_to_python(value)
        else:
            return value
    except Exception as e:
        logger.error("Error in auto conversion from UNO: %s" % str(e))
        return value