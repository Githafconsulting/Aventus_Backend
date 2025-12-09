"""
Migration: Add onboarding route and third party workflow fields to contractors table

This migration adds:
- onboarding_route enum field (wps_freelancer or third_party)
- PENDING_THIRD_PARTY_RESPONSE status to contractor status enum
- third_party_company_id field
- third_party_email_sent_date field
- third_party_response_received_date field
- third_party_document field

Run this migration using: python migrations/add_onboarding_route_and_third_party_fields.py
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Add onboarding route and third party fields to contractors table"""
    with engine.connect() as conn:
        # Create OnboardingRoute enum type
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE onboardingroute AS ENUM ('wps_freelancer', 'third_party');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        # Add PENDING_THIRD_PARTY_RESPONSE to ContractorStatus enum
        conn.execute(text("""
            ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS 'pending_third_party_response';
        """))

        # Add onboarding_route column
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS onboarding_route onboardingroute
        """))

        # Add third party tracking columns
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS third_party_company_id VARCHAR
        """))

        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS third_party_email_sent_date TIMESTAMP WITH TIME ZONE
        """))

        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS third_party_response_received_date TIMESTAMP WITH TIME ZONE
        """))

        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS third_party_document VARCHAR
        """))

        conn.commit()
        print("Migration completed successfully!")
        print("   - Created OnboardingRoute enum type")
        print("   - Added PENDING_THIRD_PARTY_RESPONSE to ContractorStatus")
        print("   - Added onboarding_route column")
        print("   - Added third_party_company_id column")
        print("   - Added third_party_email_sent_date column")
        print("   - Added third_party_response_received_date column")
        print("   - Added third_party_document column")


def downgrade():
    """Remove the added fields (rollback)"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS onboarding_route"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS third_party_company_id"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS third_party_email_sent_date"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS third_party_response_received_date"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS third_party_document"))
        conn.execute(text("DROP TYPE IF EXISTS onboardingroute"))
        conn.commit()
        print("Rollback completed successfully!")


if __name__ == "__main__":
    print("Running migration: Add onboarding route and third party fields...")
    upgrade()
