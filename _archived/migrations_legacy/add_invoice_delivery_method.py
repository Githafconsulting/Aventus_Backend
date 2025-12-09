"""
Migration: Add invoice_delivery_method field to clients table
Date: 2025-01-18
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
    """Add invoice_delivery_method column to clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding invoice_delivery_method column to clients table...")
            conn.execute(text("""
                ALTER TABLE clients
                ADD COLUMN IF NOT EXISTS invoice_delivery_method VARCHAR
            """))
            conn.commit()
            logger.info("✓ Successfully added invoice_delivery_method column to clients table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove invoice_delivery_method column from clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing invoice_delivery_method column from clients table...")
            conn.execute(text("""
                ALTER TABLE clients
                DROP COLUMN IF EXISTS invoice_delivery_method
            """))
            conn.commit()
            logger.info("✓ Successfully removed invoice_delivery_method column from clients table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add invoice_delivery_method to clients")
    upgrade()
    print("Migration completed successfully!")
