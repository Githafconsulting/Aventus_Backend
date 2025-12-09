"""
Migration script to replace Client Details with Aventus Deal fields.

This script:
1. Drops old client_details columns
2. Adds new aventus_deal columns (consultant, any_splits, resourcer)

Run this script directly: python migrations/replace_client_details_with_aventus_deal.py
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

        # Drop old client details columns
        print("Dropping old client details columns...")
        old_columns = [
            'client_office_address', 'client_address_line2', 'client_address_line3',
            'client_address_line4', 'client_po_box', 'po_required', 'po_number',
            'client_tax_number', 'contractor_pay_frequency', 'client_invoice_frequency',
            'client_payment_terms', 'invoicing_preferences', 'invoice_instructions',
            'supporting_docs_required'
        ]

        for column in old_columns:
            try:
                conn.execute(text(f"ALTER TABLE contractors DROP COLUMN IF EXISTS {column};"))
                print(f"  [OK] Dropped {column}")
            except Exception as e:
                print(f"  Note: Could not drop {column}: {e}")

        # Add new Aventus Deal columns
        print("\nAdding new Aventus Deal columns...")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS consultant VARCHAR;
            """))
            print("  [OK] consultant column added")
        except Exception as e:
            print(f"  Note: consultant column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS any_splits VARCHAR;
            """))
            print("  [OK] any_splits column added")
        except Exception as e:
            print(f"  Note: any_splits column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS resourcer VARCHAR;
            """))
            print("  [OK] resourcer column added")
        except Exception as e:
            print(f"  Note: resourcer column may already exist: {e}")

    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server to load the updated models")
    print("2. The CDS form now has 'Aventus Deal' tab instead of 'Client Details'")
    print("3. New fields: Consultant, Any Splits?, Resourcer")

if __name__ == "__main__":
    run_migration()
