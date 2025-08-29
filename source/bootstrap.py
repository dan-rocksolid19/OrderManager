"""
Bootstrap utilities to guarantee a working database connection before the UI loads.
"""

import os
from librepy.utils.db_config_manager import DatabaseConfigManager
from librepy.database import test_connection
from librepy.database.run_migration import apply_pending_migrations
from librepy.model.db_connection import reinitialize_database_connection, get_database_connection
from librepy.pybrex.msgbox import msgbox

MAX_RETRIES = 3


def ensure_database_ready(logger):
    """Return True when the database is reachable and migrations are up-to-date."""
    logger.info("Starting database readiness check")
    cfg_mgr = DatabaseConfigManager()
    retries = 0
    while retries < MAX_RETRIES:
        params = cfg_mgr.get_connection_params()
        # Treat missing user config file as absence of configuration
        if not params or not os.path.exists(cfg_mgr.config_path):
            logger.info("No database configuration found, prompting user")
            if not cfg_mgr.prompt_configuration():
                msgbox("Database configuration is required to run the application.", "Database Setup")
                return False
            continue
        logger.info("Testing database connection")
        ok, message = test_connection.main(**params)
        if ok:
            logger.info("Database connection successful, reinitializing connection")
            reinitialize_database_connection()
            db = get_database_connection()
            logger.info("Applying database migrations")
            apply_pending_migrations(logger, db)
            logger.info("Database is ready and up-to-date")
            return True
        logger.warning(f"Database connection failed: {message}")
        msgbox(message, "Database Connection Error")
        if not cfg_mgr.prompt_configuration():
            msgbox("Database configuration is required to run the application.", "Database Setup")
            return False
        retries += 1
    logger.error("Unable to establish database connection after multiple attempts")
    msgbox("Unable to establish a database connection after multiple attempts.", "Database Error")
    return False 