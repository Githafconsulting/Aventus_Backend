"""
Migration: Add candidate_pay_rate_period and vacation_days columns to contractors table

Run this script to add the new columns:
    python migrations/add_pay_rate_period_vacation_days.py
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Add candidate_pay_rate_period and vacation_days columns to contractors table"""

    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Add candidate_pay_rate_period column
        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS candidate_pay_rate_period VARCHAR;
            """))
            conn.commit()
            print("[OK] candidate_pay_rate_period column added successfully")
        except Exception as e:
            print(f"[INFO] candidate_pay_rate_period column may already exist or error: {e}")

        # Add vacation_days column
        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS vacation_days VARCHAR;
            """))
            conn.commit()
            print("[OK] vacation_days column added successfully")
        except Exception as e:
            print(f"[INFO] vacation_days column may already exist or error: {e}")

if __name__ == "__main__":
    print("Running migration: add_pay_rate_period_vacation_days")
    print("-" * 50)
    run_migration()
    print("-" * 50)
    print("Migration complete!")
