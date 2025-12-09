"""
Migration script to replace Payment Details with Invoice Details fields.

This script:
1. Drops old payment_details columns
2. Adds new invoice_details columns

Run this script directly: python migrations/replace_payment_details_with_invoice_details.py
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

        # Drop old payment details columns
        print("Dropping old payment details columns...")
        old_columns = [
            'umbrella_or_direct', 'candidate_bank_details', 'candidate_iban',
            'candidate_account_number', 'candidate_mobile', 'current_location'
        ]

        for column in old_columns:
            try:
                conn.execute(text(f"ALTER TABLE contractors DROP COLUMN IF EXISTS {column};"))
                print(f"  [OK] Dropped {column}")
            except Exception as e:
                print(f"  Note: Could not drop {column}: {e}")

        # Add new Invoice Details columns
        print("\nAdding new Invoice Details columns...")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS timesheet_required VARCHAR;
            """))
            print("  [OK] timesheet_required column added")
        except Exception as e:
            print(f"  Note: timesheet_required column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS timesheet_approver_name VARCHAR;
            """))
            print("  [OK] timesheet_approver_name column added")
        except Exception as e:
            print(f"  Note: timesheet_approver_name column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_email VARCHAR;
            """))
            print("  [OK] invoice_email column added")
        except Exception as e:
            print(f"  Note: invoice_email column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS client_contact VARCHAR;
            """))
            print("  [OK] client_contact column added")
        except Exception as e:
            print(f"  Note: client_contact column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_address_line1 VARCHAR;
            """))
            print("  [OK] invoice_address_line1 column added")
        except Exception as e:
            print(f"  Note: invoice_address_line1 column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_address_line2 VARCHAR;
            """))
            print("  [OK] invoice_address_line2 column added")
        except Exception as e:
            print(f"  Note: invoice_address_line2 column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_address_line3 VARCHAR;
            """))
            print("  [OK] invoice_address_line3 column added")
        except Exception as e:
            print(f"  Note: invoice_address_line3 column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_address_line4 VARCHAR;
            """))
            print("  [OK] invoice_address_line4 column added")
        except Exception as e:
            print(f"  Note: invoice_address_line4 column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_po_box VARCHAR;
            """))
            print("  [OK] invoice_po_box column added")
        except Exception as e:
            print(f"  Note: invoice_po_box column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_tax_number VARCHAR;
            """))
            print("  [OK] invoice_tax_number column added")
        except Exception as e:
            print(f"  Note: invoice_tax_number column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS contractor_pay_frequency VARCHAR;
            """))
            print("  [OK] contractor_pay_frequency column added")
        except Exception as e:
            print(f"  Note: contractor_pay_frequency column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS client_invoice_frequency VARCHAR;
            """))
            print("  [OK] client_invoice_frequency column added")
        except Exception as e:
            print(f"  Note: client_invoice_frequency column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS client_payment_terms VARCHAR;
            """))
            print("  [OK] client_payment_terms column added")
        except Exception as e:
            print(f"  Note: client_payment_terms column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoicing_preferences VARCHAR;
            """))
            print("  [OK] invoicing_preferences column added")
        except Exception as e:
            print(f"  Note: invoicing_preferences column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS invoice_instructions TEXT;
            """))
            print("  [OK] invoice_instructions column added")
        except Exception as e:
            print(f"  Note: invoice_instructions column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS supporting_docs_required VARCHAR;
            """))
            print("  [OK] supporting_docs_required column added")
        except Exception as e:
            print(f"  Note: supporting_docs_required column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS po_required VARCHAR;
            """))
            print("  [OK] po_required column added")
        except Exception as e:
            print(f"  Note: po_required column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS po_number VARCHAR;
            """))
            print("  [OK] po_number column added")
        except Exception as e:
            print(f"  Note: po_number column may already exist: {e}")

    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server to load the updated models")
    print("2. The CDS form now has 'Invoice Details' tab instead of 'Payment Details'")
    print("3. New fields: Timesheet info, Invoice email, Client contact, Address lines, PO details, etc.")

if __name__ == "__main__":
    run_migration()
