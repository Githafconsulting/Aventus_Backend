"""
Migration: Add new CDS form fields to contractors table
Date: 2024-12-01
Description: Adds new fields for the updated CDS form based on Google Sheet structure
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    """Add new columns to contractors table for updated CDS form"""

    engine = create_engine(DATABASE_URL)

    # List of new columns to add
    new_columns = [
        # Section 1: Contractor - New fields
        ("middle_names", "VARCHAR"),
        ("country_of_residence", "VARCHAR"),
        ("address_line1", "VARCHAR"),
        ("mobile_no", "VARCHAR"),
        ("contractor_bank_name", "VARCHAR"),
        ("contractor_account_name", "VARCHAR"),
        ("contractor_account_no", "VARCHAR"),
        ("contractor_iban", "VARCHAR"),
        ("contractor_swift_bic", "VARCHAR"),

        # Section 2: Management Company - New fields
        ("mgmt_address_line1", "VARCHAR"),
        ("mgmt_address_line2", "VARCHAR"),
        ("mgmt_address_line3", "VARCHAR"),
        ("mgmt_address_line4", "VARCHAR"),
        ("mgmt_country", "VARCHAR"),
        ("mgmt_bank_name", "VARCHAR"),
        ("mgmt_account_name", "VARCHAR"),
        ("mgmt_account_number", "VARCHAR"),
        ("mgmt_iban_number", "VARCHAR"),
        ("mgmt_swift_bic", "VARCHAR"),

        # Section 3: Placement Details - New fields
        ("rate_type", "VARCHAR"),
        ("charge_rate_month", "VARCHAR"),
        ("gross_salary", "VARCHAR"),
        ("charge_rate_day", "VARCHAR"),
        ("day_rate", "VARCHAR"),

        # Section 5: Invoice Details - New fields
        ("invoice_email1", "VARCHAR"),
        ("invoice_email2", "VARCHAR"),
        ("client_contact1", "VARCHAR"),
        ("client_contact2", "VARCHAR"),
        ("tax_number", "VARCHAR"),
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

def rollback_migration():
    """Remove the new columns (use with caution!)"""

    engine = create_engine(DATABASE_URL)

    columns_to_remove = [
        "middle_names", "country_of_residence", "address_line1", "mobile_no",
        "contractor_bank_name", "contractor_account_name", "contractor_account_no",
        "contractor_iban", "contractor_swift_bic",
        "mgmt_address_line1", "mgmt_address_line2", "mgmt_address_line3",
        "mgmt_bank_name", "mgmt_account_name", "mgmt_account_number",
        "mgmt_iban_number", "mgmt_swift_bic",
        "rate_type", "charge_rate_month", "gross_salary", "charge_rate_day", "day_rate",
        "invoice_email1", "invoice_email2", "client_contact1", "client_contact2", "tax_number"
    ]

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
        print("Running migration to add new CDS fields...")
        run_migration()
