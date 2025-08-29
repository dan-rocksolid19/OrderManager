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

import traceback
import os
from librepy.pybrex.values import LOG_DIR
from librepy.utils.db_config_manager import DatabaseConfigManager
from datetime import datetime, date
from librepy.pybrex.values import pybrex_logger
import uno

logger = pybrex_logger(__name__)

def set_report_parameter(report, param_name, param_value, param_type):
    """
    Set a parameter on the report based on its type.
    
    Args:
        report: JasperReport instance
        param_name (str): Name of the parameter
        param_value: Value of the parameter
        param_type (str): Type of parameter. One of:
            - 'string': String value
            - 'int': Integer value
            - 'long': Long value
            - 'double': Double value
            - 'float': Float value
            - 'boolean': Boolean value
            - 'date': Date value (datetime.date or datetime.datetime)
            - 'uno_date': com.sun.star.util.Date value
            - 'image_bytes': Image as bytes array
            - 'image_path': Image as file path
    """
    try:
        logger.info(f"Setting parameter {param_name} with value {param_value} of type {param_type}")
        
        if param_value is None:
            logger.info(f"Parameter {param_name} has None value, skipping")
            return
            
        if param_type == 'string':
            report.setStringParam(param_name, str(param_value))
        elif param_type == 'int' or param_type == 'integer':
            report.setIntParam(param_name, int(param_value))
        elif param_type == 'long':
            report.setLongParam(param_name, int(param_value))  # Python int maps to Java long
        elif param_type == 'double':
            report.setDoubleParam(param_name, float(param_value))
        elif param_type == 'float':
            report.setFloatParam(param_name, float(param_value))
        elif param_type == 'boolean':
            report.setBooleanParam(param_name, bool(param_value))
        elif param_type == 'date':
            logger.info(f"Processing date parameter {param_name}")
            logger.info(f"Value type: {type(param_value)}")
            logger.info(f"Value: {param_value}")
            
            # Handle both datetime and date objects
            if isinstance(param_value, (datetime, date)):
                logger.info(f"Creating UNO date for {param_value}")
                # Create a new UNO date object
                uno_date = uno.createUnoStruct("com.sun.star.util.Date")
                logger.info(f"Created UNO date object: {uno_date}")
                uno_date.Year = param_value.year
                uno_date.Month = param_value.month
                uno_date.Day = param_value.day
                logger.info(f"Setting date parameter with UNO date: Year={uno_date.Year}, Month={uno_date.Month}, Day={uno_date.Day}")
                report.setDateParam(param_name, uno_date)
            else:
                raise ValueError(f"Expected datetime.date or datetime.datetime, got {type(param_value)}")
        elif param_type == 'uno_date':
            # Directly use the UNO date object
            report.setDateParam(param_name, param_value)
        elif param_type == 'image_bytes':
            report.setImageFromBytesParam(param_name, param_value)
        elif param_type == 'image_path':
            report.setImageFromPathParam(param_name, str(param_value))
        elif param_type == 'object':
            # Pass arbitrary objects (e.g., java.util.Map, java.util.List) to Jasper
            # This relies on the UNO bridge supporting the invoked method on the Java side
            try:
                report.setObjectParam(param_name, param_value)
            except Exception:
                # Fallback: try a generic setter name used by some implementations
                if hasattr(report, 'setParamObject'):
                    report.setParamObject(param_name, param_value)
                else:
                    raise
        else:
            raise ValueError(f"Unsupported parameter type: {param_type}")
            
    except Exception as e:
        logger.error(f"Error in set_report_parameter: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error setting parameter {param_name}: {str(e)}")

def main(report_path, report_params=None, print_action=4, *args):
    try:
        logger.info(f"Starting report generation with params: {report_params}")
        
        manager = createUnoService("org.libretools.JasperReportManager")
        if not manager:
            raise Exception("UNO service 'org.libretools.JasperReportManager' is not available (createUnoService returned None). Ensure the Jasper extension is installed and you are running inside the LibreOffice/LibrePy environment.")
        
        jasper_log_file = os.path.join(LOG_DIR, "jasper_reports.log")
        logger.info(f"Jasper log file: {jasper_log_file}")
        manager.setLogFile(jasper_log_file)
        
        # Get database configuration from DatabaseConfigManager
        db_config_manager = DatabaseConfigManager()
        db_config = db_config_manager.get_connection_params()
        
        if not db_config:
            logger.error("Database configuration not found or invalid")
            raise Exception("Database configuration not found or invalid")
        
        # Build JDBC URL with credentials embedded
        url = f"jdbc:postgresql://{db_config['host']}:{db_config['port']}/{db_config['database']}?user={db_config['user']}&password={db_config['password']}"

        logger.info(f"Database URL: {url}")
        
        # Add connection using the URL directly
        manager.addConnection(url)
        
        # Add a report job. This will return a org.libretools.JasperReport instance
        report = manager.addReport(report_path)
         
        # Set report parameters if provided
        if report_params:
            logger.info("Processing report parameters")
            for param_name, param_info in report_params.items():
                try:
                    logger.info(f"Processing parameter: {param_name}")
                    logger.info(f"Parameter info: {param_info}")
                    param_value = param_info.get('value')
                    param_type = param_info.get('type', 'string')  # Default to string if type not specified
                    logger.info(f"Extracted value: {param_value}, type: {param_type}")
                    set_report_parameter(report, param_name, param_value, param_type)
                except Exception as e:
                    logger.error(f"Error processing parameter {param_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise Exception(f"Failed to set parameter {param_name}: {str(e)}")
                
        report.setPromptForParameters(False)

        report.setPrintAction(print_action)
        
        report.execute()
        
    except Exception as e:
        logger.error(f"Error encountered: {str(e)}")
        logger.error(traceback.format_exc())
        MsgBox("Error encountered!\n%s" % e)
        # Re-raise so callers can handle and avoid false success logs
        raise