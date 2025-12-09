"""
Migration script to add third party functionality and business_type field to contractors table.

This script:
1. Creates the third_parties table
2. Adds business_type and third_party_id columns to the contractors table

Run this script directly: python migrations/add_third_party_and_business_type.py
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

        # Create third_parties table
        print("Creating third_parties table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS third_parties (
                id VARCHAR PRIMARY KEY,
                company_name VARCHAR NOT NULL,
                registered_address VARCHAR,
                company_vat_no VARCHAR,
                company_reg_no VARCHAR,
                contact_person_name VARCHAR,
                contact_person_email VARCHAR,
                contact_person_phone VARCHAR,
                bank_name VARCHAR,
                account_number VARCHAR,
                iban_number VARCHAR,
                swift_code VARCHAR,
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        print("[OK] third_parties table created")

        # Add business_type column to contractors table
        print("Adding business_type column to contractors table...")
        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS business_type VARCHAR;
            """))
            print("[OK] business_type column added")
        except Exception as e:
            print(f"Note: business_type column may already exist: {e}")

        # Add third_party_id column to contractors table
        print("Adding third_party_id column to contractors table...")
        try:
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS third_party_id VARCHAR;
            """))
            print("[OK] third_party_id column added")
        except Exception as e:
            print(f"Note: third_party_id column may already exist: {e}")

    print("\nMigration completed successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server to load the new models")
    print("2. Access the Third Parties page from admin/superadmin dashboard")
    print("3. Create third party companies")
    print("4. Use them in the CDS form when creating contractors")

if __name__ == "__main__":
    run_migration()
