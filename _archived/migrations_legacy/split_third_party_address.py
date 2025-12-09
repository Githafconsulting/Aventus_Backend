"""
Migration: Split registered_address into address_line1-4 for third_parties table
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
    """Split registered_address into address_line1-4 columns"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding address_line1-4 columns to third_parties table...")

            # Add new columns
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS address_line1 VARCHAR,
                ADD COLUMN IF NOT EXISTS address_line2 VARCHAR,
                ADD COLUMN IF NOT EXISTS address_line3 VARCHAR,
                ADD COLUMN IF NOT EXISTS address_line4 VARCHAR
            """))

            # Copy data from registered_address to address_line1
            conn.execute(text("""
                UPDATE third_parties
                SET address_line1 = registered_address
                WHERE registered_address IS NOT NULL
            """))

            # Drop old column
            conn.execute(text("""
                ALTER TABLE third_parties
                DROP COLUMN IF EXISTS registered_address
            """))

            conn.commit()
            logger.info("✓ Successfully split registered_address into address_line1-4 in third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Revert address_line1-4 back to registered_address"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Reverting address fields to registered_address in third_parties table...")

            # Add back registered_address column
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS registered_address VARCHAR
            """))

            # Concatenate address lines back to registered_address
            conn.execute(text("""
                UPDATE third_parties
                SET registered_address =
                    COALESCE(address_line1, '') || ' ' ||
                    COALESCE(address_line2, '') || ' ' ||
                    COALESCE(address_line3, '') || ' ' ||
                    COALESCE(address_line4, '')
                WHERE address_line1 IS NOT NULL OR
                      address_line2 IS NOT NULL OR
                      address_line3 IS NOT NULL OR
                      address_line4 IS NOT NULL
            """))

            # Drop new columns
            conn.execute(text("""
                ALTER TABLE third_parties
                DROP COLUMN IF EXISTS address_line1,
                DROP COLUMN IF EXISTS address_line2,
                DROP COLUMN IF EXISTS address_line3,
                DROP COLUMN IF EXISTS address_line4
            """))

            conn.commit()
            logger.info("✓ Successfully reverted to registered_address in third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Split third party address fields")
    upgrade()
    print("Migration completed successfully!")
