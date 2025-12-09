"""
Migration: Add country and current_location fields to contractors table
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
    """Add country and current_location columns to contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding country and current_location columns to contractors table...")

            # Add country column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS country VARCHAR
            """))

            # Add current_location column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS current_location VARCHAR
            """))

            conn.commit()
            logger.info("✓ Successfully added country and current_location columns to contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove country and current_location columns from contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing country and current_location columns from contractors table...")

            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN IF EXISTS country
            """))

            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN IF EXISTS current_location
            """))

            conn.commit()
            logger.info("✓ Successfully removed country and current_location columns from contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: add_country_and_location_to_contractors")
    upgrade()
    print("Migration completed successfully!")
