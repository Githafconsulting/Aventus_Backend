"""
Migration: Add work order tracking fields to contractors table
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
    """Add work order tracking fields to contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding work order tracking fields to contractors table...")

            # Add new status value to enum
            conn.execute(text("""
                ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS 'awaiting_work_order_approval'
            """))

            # Add work order tracking columns
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS work_order_id VARCHAR,
                ADD COLUMN IF NOT EXISTS work_order_generated_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS work_order_approved_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS work_order_approved_by VARCHAR,
                ADD COLUMN IF NOT EXISTS work_order_sent_date TIMESTAMP WITH TIME ZONE
            """))

            conn.commit()
            logger.info("✓ Successfully added work order tracking fields to contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove work order tracking fields from contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing work order tracking fields from contractors table...")

            # Remove work order tracking columns
            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN IF EXISTS work_order_id,
                DROP COLUMN IF EXISTS work_order_generated_date,
                DROP COLUMN IF EXISTS work_order_approved_date,
                DROP COLUMN IF EXISTS work_order_approved_by,
                DROP COLUMN IF EXISTS work_order_sent_date
            """))

            conn.commit()
            logger.info("✓ Successfully removed work order tracking fields from contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add work order tracking fields to contractors table")
    upgrade()
    print("Migration completed successfully!")
