"""
Migration script to add bank_name field to contractors table.
Run this script to add the management company bank name field.
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """Add bank_name column to contractors table"""

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'contractors' AND column_name = 'bank_name'
        """))

        if result.fetchone() is None:
            print("Adding bank_name column to contractors table...")
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN bank_name VARCHAR NULL
            """))
            conn.commit()
            print("Successfully added bank_name column!")
        else:
            print("bank_name column already exists, skipping...")

if __name__ == "__main__":
    run_migration()
