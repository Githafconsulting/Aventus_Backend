"""
Migration: Add documents field to third_parties table
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
    """Add documents column to third_parties table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            # Add documents column as JSON type with default empty array
            logger.info("Adding documents column to third_parties table...")
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS documents JSON DEFAULT '[]'::json
            """))
            conn.commit()
            logger.info("✓ Successfully added documents column to third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove documents column from third_parties table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing documents column from third_parties table...")
            conn.execute(text("""
                ALTER TABLE third_parties
                DROP COLUMN IF EXISTS documents
            """))
            conn.commit()
            logger.info("✓ Successfully removed documents column from third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add documents to third_parties")
    upgrade()
    print("Migration completed successfully!")
