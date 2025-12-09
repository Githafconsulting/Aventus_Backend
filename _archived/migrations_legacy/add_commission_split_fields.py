"""
Migration: Add commission split fields to contractors table
Date: 2024-12-06
Description: Replaces the single 'any_splits' text field with two percentage fields:
             - aventus_split: Aventus commission split percentage
             - resourcer_split: Resourcer commission split percentage
             These two values should always total 100%.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add commission split columns to contractors table"""

    engine = create_engine(DATABASE_URL)

    new_columns = [
        ("aventus_split", "VARCHAR"),
        ("resourcer_split", "VARCHAR"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in new_columns:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'contractors'
                    AND column_name = '{column_name}'
                """))

                if result.fetchone() is None:
                    # Column doesn't exist, add it
                    conn.execute(text(f"""
                        ALTER TABLE contractors
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    print(f"Added column: {column_name}")
                else:
                    print(f"Column already exists: {column_name}")

            except Exception as e:
                print(f"Error adding column {column_name}: {e}")

        conn.commit()
        print("\nMigration completed successfully!")
        print("Note: The 'any_splits' column is kept for backwards compatibility but is no longer used.")

def rollback_migration():
    """Remove the commission split columns (use with caution!)"""

    engine = create_engine(DATABASE_URL)

    columns_to_remove = ["aventus_split", "resourcer_split"]

    with engine.connect() as conn:
        for column_name in columns_to_remove:
            try:
                conn.execute(text(f"""
                    ALTER TABLE contractors
                    DROP COLUMN IF EXISTS {column_name}
                """))
                print(f"Removed column: {column_name}")
            except Exception as e:
                print(f"Error removing column {column_name}: {e}")

        conn.commit()
        print("\nRollback completed!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Rolling back migration...")
        rollback_migration()
    else:
        print("Running migration to add commission split fields...")
        run_migration()
