"""
Migration: Add new CDS form fields to contractors table

Run this script to add the new columns:
    python migrations/add_cds_form_fields.py
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Add new CDS form fields to contractors table"""

    engine = create_engine(settings.database_url)

    columns_to_add = [
        # Additional Info
        ("laptop_provided_by", "VARCHAR"),
        ("any_notes", "TEXT"),

        # Summary Calculations
        ("total_monthly_costs", "VARCHAR"),
        ("total_contractor_fixed_costs", "VARCHAR"),
        ("monthly_contractor_fixed_costs", "VARCHAR"),
        ("total_contractor_monthly_cost", "VARCHAR"),

        # Invoice Details
        ("invoice_country", "VARCHAR"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f"""
                    ALTER TABLE contractors
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type};
                """))
                conn.commit()
                print(f"[OK] {column_name} column added successfully")
            except Exception as e:
                print(f"[INFO] {column_name} column may already exist or error: {e}")

if __name__ == "__main__":
    print("Running migration: add_cds_form_fields")
    print("-" * 50)
    run_migration()
    print("-" * 50)
    print("Migration complete!")
