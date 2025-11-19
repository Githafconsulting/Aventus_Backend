"""
Complete the contractor status enum migration
Continues from where the previous migration left off
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

def complete_migration():
    """Complete the contractor status enum migration"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        try:
            print("Completing contractor status enum migration...")

            # Step 1: Copy data back from temporary column (converting to lowercase)
            print("Step 1: Copying data back from temporary column...")
            conn.execute(text("""
                UPDATE contractors
                SET status = LOWER(status_temp)::contractorstatus;
            """))
            conn.commit()

            # Step 2: Drop temporary column
            print("Step 2: Dropping temporary column...")
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
    success = complete_migration()
    sys.exit(0 if success else 1)
