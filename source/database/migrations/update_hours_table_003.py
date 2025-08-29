"""
Migration 003: Update Hours table to use start_date and end_date instead of work_date
"""

def migrate(migrator, db):
    # Check and add start_date column if it doesn't exist
    db.execute_sql("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'hours' 
                AND table_schema = 'job_manager'
                AND column_name = 'start_date'
            ) THEN
                ALTER TABLE hours ADD COLUMN start_date DATE;
            END IF;
        END $$
    """)
    
    # Check and add end_date column if it doesn't exist
    db.execute_sql("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'hours' 
                AND table_schema = 'job_manager'
                AND column_name = 'end_date'
            ) THEN
                ALTER TABLE hours ADD COLUMN end_date DATE;
            END IF;
        END $$
    """)
    
    # Update data only if work_date column exists (for existing users)
    db.execute_sql("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'hours' 
                AND table_schema = 'job_manager'
                AND column_name = 'work_date'
            ) THEN
                UPDATE hours 
                SET start_date = work_date, end_date = work_date 
                WHERE work_date IS NOT NULL 
                AND start_date IS NULL 
                AND end_date IS NULL;
            END IF;
        END $$
    """)
    
    # Drop work_date column if it exists
    db.execute_sql("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'hours' 
                AND table_schema = 'job_manager'
                AND column_name = 'work_date'
            ) THEN
                ALTER TABLE hours DROP COLUMN work_date;
            END IF;
        END $$
    """)
    return []