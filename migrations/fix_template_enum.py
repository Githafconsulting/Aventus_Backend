"""
Migration: Fix template enum to use lowercase values
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
    """Fix template enum values to lowercase"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Fixing template enum to use lowercase values...")

            # Check current templates
            result = conn.execute(text("SELECT template_type FROM templates"))
            current_types = [row[0] for row in result]
            logger.info(f"Current template types in DB: {current_types}")

            # Drop and recreate enum with lowercase values
            logger.info("Dropping old enum...")
            conn.execute(text("ALTER TABLE templates ALTER COLUMN template_type TYPE VARCHAR"))
            conn.execute(text("DROP TYPE IF EXISTS templatetype CASCADE"))

            logger.info("Creating new enum with lowercase values...")
            conn.execute(text("""
                CREATE TYPE templatetype AS ENUM (
                    'contract',
                    'cds',
                    'costing_sheet',
                    'work_order',
                    'proposal',
                    'cohf',
                    'schedule_form',
                    'quote_sheet'
                )
            """))

            logger.info("Updating table to use new enum...")
            conn.execute(text("ALTER TABLE templates ALTER COLUMN template_type TYPE templatetype USING template_type::templatetype"))

            conn.commit()
            logger.info("✓ Successfully fixed template enum")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Fix template enum")
    upgrade()
    print("Migration completed successfully!")
