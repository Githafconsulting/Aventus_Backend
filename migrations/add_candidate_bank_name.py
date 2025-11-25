"""
Migration: Add candidate_bank_name column to contractors table

Run this script to add the new column:
    python migrations/add_candidate_bank_name.py
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Add candidate_bank_name column to contractors table"""

    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        try:
            # Add the new column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS candidate_bank_name VARCHAR;
            """))
            conn.commit()
            print("[OK] candidate_bank_name column added successfully")
        except Exception as e:
            print(f"[INFO] Column may already exist or error: {e}")

if __name__ == "__main__":
    print("Running migration: add_candidate_bank_name")
    print("-" * 50)
    run_migration()
    print("-" * 50)
    print("Migration complete!")
