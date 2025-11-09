"""
Migration script to add project_name column.

This script adds the project_name field to contractors table.

Run this script directly: python migrations/add_project_name.py
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    with engine.begin() as conn:
        print("Running migration...")

        # Add project_name column
        print("Adding project_name column...")
        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS project_name VARCHAR;
            """))
            print("  [OK] project_name column added")
        except Exception as e:
            print(f"  Note: project_name column may already exist: {e}")

    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server to load the updated models")
    print("2. The CDS form now has Client & Project dropdown")

if __name__ == "__main__":
    run_migration()
