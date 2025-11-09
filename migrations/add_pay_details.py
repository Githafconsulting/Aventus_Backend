"""
Migration script to add Pay Details fields.

This script:
1. Adds new pay_details columns (umbrella_or_direct, candidate_bank_details, candidate_iban)

Run this script directly: python migrations/add_pay_details.py
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

        # Add new Pay Details columns
        print("Adding new Pay Details columns...")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS umbrella_or_direct VARCHAR;
            """))
            print("  [OK] umbrella_or_direct column added")
        except Exception as e:
            print(f"  Note: umbrella_or_direct column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS candidate_bank_details VARCHAR;
            """))
            print("  [OK] candidate_bank_details column added")
        except Exception as e:
            print(f"  Note: candidate_bank_details column may already exist: {e}")

        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS candidate_iban VARCHAR;
            """))
            print("  [OK] candidate_iban column added")
        except Exception as e:
            print(f"  Note: candidate_iban column may already exist: {e}")

    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server to load the updated models")
    print("2. The CDS form now has 'Pay Details' tab after 'Invoice Details'")
    print("3. New fields: Umbrella or Direct?, Candidate Bank Details, Candidate IBAN")

if __name__ == "__main__":
    run_migration()
