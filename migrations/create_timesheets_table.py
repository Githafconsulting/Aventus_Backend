"""
Migration script to create timesheets table with all required columns
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
                contractor_id INTEGER NOT NULL REFERENCES contractors(id),
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
                manager_email VARCHAR,
                notes TEXT,
                decline_reason TEXT,
                review_token VARCHAR UNIQUE,
                review_token_expiry TIMESTAMP,
                timesheet_file_url VARCHAR,
                approval_file_url VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # Add missing columns if table already exists
        columns_to_add = [
            ("manager_email", "VARCHAR"),
            ("review_token", "VARCHAR"),
            ("review_token_expiry", "TIMESTAMP"),
        ]

        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f"""
                    ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                """))
                print(f"Added/verified column: {column_name}")
            except Exception as e:
                print(f"Column {column_name}: {e}")

        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_timesheets_contractor_id
            ON timesheets(contractor_id);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_timesheets_status
            ON timesheets(status);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_timesheets_review_token
            ON timesheets(review_token);
        """))

        conn.commit()
        print("Timesheets table migration completed successfully!")

if __name__ == "__main__":
    run_migration()
