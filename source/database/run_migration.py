'''
Run database migrations

This script runs available migrations to update the database schema.
'''

from pathlib import Path
import importlib.util
from datetime import datetime, timezone
from librepy.model.db_connection import get_database_connection
from librepy.peewee.playhouse.migrate import PostgresqlMigrator
from librepy.database.migrations import initial_001, create_auth_tables_002, update_hours_table_003, create_events_table_004

_APPLIED_DATABASES = set()


def apply_pending_migrations(logger, db=None):
    """Apply any migrations that have not yet been run.

    Guards against running twice on the same database object within a single
    application session by keeping an in-memory registry.
    """
    logger.info("Starting migration check and application process")
    
    if db is not None and id(db) in _APPLIED_DATABASES:
        logger.info("Migrations already applied for this database instance in current session")
        return True

    created_connection = False
    if db is None:
        db = get_database_connection()
        created_connection = True
        logger.debug("Created new database connection for migrations")
        
    # Use connection_context to ensure the connection is open only for the
    # duration of the migration process.
    with db.connection_context():
        logger.debug("Ensuring schema_migrations table exists")
        db.execute_sql('CREATE SCHEMA IF NOT EXISTS job_manager')
        db.execute_sql('SET search_path TO job_manager, public')
        db.execute_sql('CREATE TABLE IF NOT EXISTS schema_migrations (filename VARCHAR PRIMARY KEY, applied_at TIMESTAMP)')
        
        logger.debug("Querying existing applied migrations")
        existing = {row[0] for row in db.execute_sql('SELECT filename FROM schema_migrations').fetchall()}
        logger.info(f"Found {len(existing)} previously applied migrations: {sorted(existing)}")
        
        migrations = [
            ('001_initial.py', initial_001),
            ('002_create_auth_tables.py', create_auth_tables_002),
            ('003_update_hours_table.py', update_hours_table_003),
            ('004_create_events_table.py', create_events_table_004)
        ]
        
        pending_migrations = [(name, mod) for name, mod in migrations if name not in existing]
        
        if not pending_migrations:
            logger.info("No pending migrations to apply")
        else:
            logger.info(f"Found {len(pending_migrations)} pending migrations: {[name for name, mod in pending_migrations]}")
        
        for name, mod in pending_migrations:
            logger.info(f"Applying migration: {name}")
            
            migrator = PostgresqlMigrator(db)
            
            with db.atomic():
                if hasattr(mod, 'migrate'):
                    logger.debug(f"Executing migrate function for {name}")
                    mod.migrate(migrator, db)
                    logger.debug(f"Migration function completed for {name}")
                else:
                    logger.warning(f"Migration file {name} has no migrate function")
                    
                db.execute_sql('INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)', (name, datetime.now(timezone.utc)))
                
            logger.info(f'Applied migration {name}')
            
        # mark as applied for session
        _APPLIED_DATABASES.add(id(db))
        logger.info("Migration process completed successfully")
        
    return True


def main(logger, database):
    return apply_pending_migrations(logger, database)
    