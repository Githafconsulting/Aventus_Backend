"""
Migration: Add PENDING_CDS_CS status to contractor status enum
This status indicates the contractor is waiting for Costing & Deal Sheet / Cost Sheet to be filled
"""
from sqlalchemy import create_engine, text
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Add PENDING_CDS_CS status to contractorstatus enum"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding PENDING_CDS_CS status to contractorstatus enum...")

            # Add new enum value
            conn.execute(text("""
                ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS 'pending_cds_cs' AFTER 'pending_third_party_response'
            """))

            conn.commit()
            logger.info("✓ Successfully added PENDING_CDS_CS status")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add PENDING_CDS_CS status to contractorstatus enum")
    upgrade()
    print("Migration completed successfully!")
