"""
Fix contractor status enum to match current model definition

This migration fixes the PostgreSQL enum type mismatch that prevents
contractors from being fetched from the database.
"""

from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    database_url = os.getenv("DATABASE_URL")

settings = Settings()

def run_migration():
    """Update the contractorstatus enum in PostgreSQL"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        try:
            print("Starting contractor status enum migration...")

            # Step 1: Add a temporary column
            print("Step 1: Adding temporary column...")
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS status_temp VARCHAR(50);
            """))
            conn.commit()

            # Step 2: Copy data to temporary column
            print("Step 2: Copying status data to temporary column...")
            conn.execute(text("""
                UPDATE contractors
                SET status_temp = status::text;
            """))
            conn.commit()

            # Step 3: Drop the status column
            print("Step 3: Dropping old status column...")
            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN status;
            """))
            conn.commit()

            # Step 4: Drop the old enum type
            print("Step 4: Dropping old enum type...")
            conn.execute(text("""
                DROP TYPE IF EXISTS contractorstatus;
            """))
            conn.commit()

            # Step 5: Create new enum type with all current values
            print("Step 5: Creating new enum type...")
            conn.execute(text("""
                CREATE TYPE contractorstatus AS ENUM (
                    'draft',
                    'pending_documents',
                    'documents_uploaded',
                    'pending_third_party_response',
                    'pending_review',
                    'approved',
                    'rejected',
                    'pending_signature',
                    'signed',
                    'active',
                    'suspended'
                );
            """))
            conn.commit()

            # Step 6: Add status column back with new enum type
            print("Step 6: Adding status column with new enum type...")
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN status contractorstatus NOT NULL DEFAULT 'draft';
            """))
            conn.commit()

            # Step 7: Copy data back from temporary column (converting to lowercase)
            print("Step 7: Copying data back from temporary column...")
            conn.execute(text("""
                UPDATE contractors
                SET status = LOWER(status_temp)::contractorstatus;
            """))
            conn.commit()

            # Step 8: Drop temporary column
            print("Step 8: Dropping temporary column...")
            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN status_temp;
            """))
            conn.commit()

            print("[SUCCESS] Migration completed successfully!")
            return True

        except Exception as e:
            print(f"[ERROR] Migration failed: {str(e)}")
            conn.rollback()
            return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
