"""
Migration script to create timesheets table
"""
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.database_url)

def run_migration():
    with engine.connect() as conn:
        # Create timesheets table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS timesheets (
                id SERIAL PRIMARY KEY,
                contractor_id VARCHAR NOT NULL REFERENCES contractors(id),
                month VARCHAR NOT NULL,
                year INTEGER NOT NULL,
                month_number INTEGER NOT NULL,
                timesheet_data JSONB,
                total_days FLOAT DEFAULT 0,
                work_days INTEGER DEFAULT 0,
                sick_days INTEGER DEFAULT 0,
                vacation_days INTEGER DEFAULT 0,
                holiday_days INTEGER DEFAULT 0,
                unpaid_days INTEGER DEFAULT 0,
                status VARCHAR DEFAULT 'pending',
                submitted_date TIMESTAMP,
                approved_date TIMESTAMP,
                declined_date TIMESTAMP,
                manager_name VARCHAR,
                notes TEXT,
                decline_reason TEXT,
                timesheet_file_url VARCHAR,
                approval_file_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Create index on contractor_id
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_timesheets_contractor_id
            ON timesheets(contractor_id);
        """))

        # Create index on status
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_timesheets_status
            ON timesheets(status);
        """))

        conn.commit()
        print("Timesheets table created successfully!")

if __name__ == "__main__":
    run_migration()
