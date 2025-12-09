"""
Migration: Add company_type to third_parties table
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
    """Add company_type column to third_parties table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding company_type column to third_parties table...")

            # Add company_type column
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS company_type VARCHAR
            """))

            conn.commit()
            logger.info("✓ Successfully added company_type column")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add company_type to third_parties")
    upgrade()
    print("Migration completed successfully!")
