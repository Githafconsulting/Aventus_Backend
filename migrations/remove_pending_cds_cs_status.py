"""
Migration: Remove PENDING_CDS_CS status from contractor status enum
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
    """Remove PENDING_CDS_CS status from contractorstatus enum"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing PENDING_CDS_CS status from contractorstatus enum...")

            # First, check if any contractors are using this status
            result = conn.execute(text("""
                SELECT COUNT(*) FROM contractors WHERE status = 'pending_cds_cs'
            """))
            count = result.scalar()

            if count > 0:
                logger.error(f"Cannot remove enum value: {count} contractors are still using 'pending_cds_cs' status")
                logger.info("Please update these contractors first")
                return

            # PostgreSQL doesn't support removing enum values directly
            # We need to recreate the enum without pending_cds_cs
            logger.info("Creating new enum type without pending_cds_cs...")

            # Create new enum type
            conn.execute(text("""
                CREATE TYPE contractorstatus_new AS ENUM (
                    'draft',
                    'pending_documents',
                    'documents_uploaded',
                    'pending_third_party_response',
                    'pending_review',
                    'approved',
                    'rejected',
                    'pending_signature',
                    'signed',
                    'active',
                    'suspended'
                )
            """))
            conn.commit()

            logger.info("Updating contractors table to use new enum...")

            # Alter the column to use the new enum
            conn.execute(text("""
                ALTER TABLE contractors
                ALTER COLUMN status TYPE contractorstatus_new
                USING status::text::contractorstatus_new
            """))
            conn.commit()

            logger.info("Dropping old enum type...")

            # Drop old enum
            conn.execute(text("DROP TYPE contractorstatus"))
            conn.commit()

            logger.info("Renaming new enum to original name...")

            # Rename new enum to original name
            conn.execute(text("ALTER TYPE contractorstatus_new RENAME TO contractorstatus"))
            conn.commit()

            logger.info("✓ Successfully removed PENDING_CDS_CS status")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Remove PENDING_CDS_CS status from contractorstatus enum")
    upgrade()
    print("Migration completed successfully!")
