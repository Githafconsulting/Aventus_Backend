"""
Migration: Add COHF fields and update onboarding routes
Adds cohf_data, cohf_status, cohf dates, 3rd party contract fields
Updates onboardingroute and contractorstatus enums
"""
from sqlalchemy import create_engine, text
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Add COHF fields and update enums"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding COHF fields to contractors table...")

            # Add COHF fields
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_data TEXT"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_status VARCHAR(50)"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_submitted_date TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_sent_to_3rd_party_date TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_docusign_received_date TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS cohf_completed_date TIMESTAMP WITH TIME ZONE"))

            logger.info("Adding 3rd party contract fields...")

            # Add 3rd party contract fields
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS third_party_contract_url TEXT"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS third_party_contract_uploaded_date TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS third_party_contract_upload_token VARCHAR(255)"))
            conn.execute(text("ALTER TABLE contractors ADD COLUMN IF NOT EXISTS third_party_contract_token_expiry TIMESTAMP WITH TIME ZONE"))

            conn.commit()
            logger.info("✓ Added columns successfully")

            logger.info("Updating onboardingroute enum...")

            # Add new onboarding route values
            route_values = ['wps', 'freelancer', 'uae', 'saudi', 'offshore']
            for val in route_values:
                try:
                    conn.execute(text(f"ALTER TYPE onboardingroute ADD VALUE IF NOT EXISTS '{val}'"))
                    logger.info(f"  Added onboardingroute value: {val}")
                except Exception as e:
                    logger.info(f"  Value {val} may already exist: {e}")

            conn.commit()

            logger.info("Updating contractorstatus enum...")

            # Add new status values
            status_values = ['pending_cohf', 'cohf_completed', 'pending_third_party_quote', 'pending_3rd_party_contract']
            for val in status_values:
                try:
                    conn.execute(text(f"ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS '{val}'"))
                    logger.info(f"  Added contractorstatus value: {val}")
                except Exception as e:
                    logger.info(f"  Value {val} may already exist: {e}")

            conn.commit()
            logger.info("✓ Successfully completed migration")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove COHF fields (note: enum values cannot be removed easily in PostgreSQL)"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing COHF and 3rd party contract columns...")

            columns_to_drop = [
                'cohf_data', 'cohf_status', 'cohf_submitted_date',
                'cohf_sent_to_3rd_party_date', 'cohf_docusign_received_date',
                'cohf_completed_date', 'third_party_contract_url',
                'third_party_contract_uploaded_date', 'third_party_contract_upload_token',
                'third_party_contract_token_expiry'
            ]

            for col in columns_to_drop:
                conn.execute(text(f"ALTER TABLE contractors DROP COLUMN IF EXISTS {col}"))

            conn.commit()
            logger.info("✓ Successfully removed columns")
            logger.info("Note: Enum values cannot be easily removed in PostgreSQL")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add COHF and route fields")
    upgrade()
    print("Migration completed successfully!")
