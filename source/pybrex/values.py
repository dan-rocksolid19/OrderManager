#coding:utf-8
# Author:  Timothy Hoover
# Purpose: Global values
# Created: 02.10.2018
# Copyright (C) 2018, Timothy Hoover


import os
import uno
import logging

PYBREX_NAME = 'Pybrex'
PYBREX_VERSION = '1.0'
PYBREX_ID = 'pybrex'
APP_NAME = 'OrderManager'


def get_dir_path(path):
    ctx = uno.getComponentContext()
    pst = ctx.getServiceManager().createInstanceWithContext(
        "com.sun.star.util.PathSubstitution", ctx)
    url = pst.substituteVariables(path, True)
    return url

def get_home_directory():
    """Get the user's home directory by extracting it from getUserPath"""
    try:
        user_path = uno.fileUrlToSystemPath(getUserPath())
        path_parts = user_path.split(os.sep)
        if len(path_parts) >= 3:
            home_dir = os.sep.join(path_parts[:3])
            return home_dir
        else:
            return os.path.expanduser("~")
    except:
        return os.path.expanduser("~")
    
HOME_DIR = get_home_directory()
    
USER_DIR = uno.fileUrlToSystemPath(get_dir_path("$(user)"))
INSTALL_DIR = os.path.split(os.path.split(USER_DIR)[0])[0]

PROGRAM_FILES = os.path.split(__file__)[0]

GRAPHICS_DIR = os.path.join(PROGRAM_FILES, 'graphics')
TOOLBAR_GRAPHICS_DIR = os.path.join(GRAPHICS_DIR, 'toolbar')
SIDEBAR_GRAPHICS_DIR = os.path.join(GRAPHICS_DIR, 'sidebar')

def _resolve_jasper_reports_dir():
    """
    Return a real filesystem dir for /jasper_reports/templates.

    1) Dev: use ../jasper_reports/templates next to your code if it exists on disk.
    2) Embedded: extract 'Scripts/python/jasper_reports/templates/*' from the
       currently open document into $(user)/Scripts/python/jasper_reports/templates.
    """
    # dev candidate: <parent_of_PROGRAM_FILES>/jasper_reports/templates
    dev_candidate = os.path.join(os.path.split(PROGRAM_FILES)[0], 'jasper_reports', 'templates')
    if os.path.isdir(dev_candidate):
        return dev_candidate

    # embedded fallback target: $(user)/Scripts/python/jasper_reports/templates
    target_dir = os.path.join(USER_DIR, 'Scripts', 'python', 'jasper_reports', 'templates')
    try:
        os.makedirs(target_dir, exist_ok=True)

        # If empty or missing a known file, try to extract from the current document
        known = os.path.join(target_dir, 'CalendarEntriesReport.jrxml')
        if not os.path.isfile(known):
            try:
                # get current component's file path
                ctx = uno.getComponentContext()
                smgr = ctx.getServiceManager()
                desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
                comp = desktop.getCurrentComponent()
                doc_url = comp.getURL()  # file:///.../YourDoc.ods
                doc_path = uno.fileUrlToSystemPath(doc_url)

                import zipfile
                with zipfile.ZipFile(doc_path) as zf:
                    prefix = 'Scripts/python/jasper_reports/templates/'
                    for name in zf.namelist():
                        if not name.startswith(prefix) or name.endswith('/'):
                            continue
                        rel = name[len(prefix):]
                        dst = os.path.join(target_dir, rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        with zf.open(name) as src, open(dst, 'wb') as out:
                            out.write(src.read())
            except Exception:
                # If extraction fails, we still return target_dir so callers have a real dir.
                pass
    except Exception:
        pass

    return target_dir

JASPER_REPORTS_DIR = _resolve_jasper_reports_dir()
DOCUMENT_REPORT_PATH = os.path.join(JASPER_REPORTS_DIR, 'CalendarEntriesReport.jrxml')


# Pybrex Color Scheme
GRID_HEADER_BG_COLOR = 0x99ccff
GRID_ROW_BG_COLOR1 = 0xFFFFFF
GRID_ROW_BG_COLOR2 = 0xE5E5E5

# Default Logging configuration - now uses home directory
LOG_DIR = os.path.join(HOME_DIR, f'{APP_NAME}_logs')
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, f'{APP_NAME}.log')

# Config file path
CONFIG_DIR = os.path.join(USER_DIR, f'{APP_NAME}_config')
CONFIG_PATH = os.path.join(CONFIG_DIR, f'{APP_NAME}.conf')

# Create logs directory if it doesn't exist
try:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
except Exception as e:
    print("Failed to create log directory: {}".format(e))

def pybrex_logger(name=__name__, level=logging.DEBUG):
    """Configure and return a logger instance with both file and console output
    
    Args:
        name (str): Logger name, defaults to module name
        level (int): Logging level, defaults to DEBUG
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create basic logger first
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    try:
        # Import here to avoid circular import
        from librepy.utils.log_config_manager import LoggingConfigManager
        config_manager = LoggingConfigManager()
        return config_manager.configure_logger(logger, name)
    except Exception as e:
        # Fall back to basic configuration if LoggingConfigManager fails
        if not logger.handlers:
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Ensure log directory exists
            os.makedirs(LOG_DIR, exist_ok=True)
            
            # Create file handler
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                DEFAULT_LOG_FILE,
                maxBytes=5242880,  # 5MB
                backupCount=2,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger