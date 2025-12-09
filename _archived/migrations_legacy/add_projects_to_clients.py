"""
Migration: Add projects field to clients table
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
    """Add projects column to clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding projects column to clients table...")
            conn.execute(text("""
                ALTER TABLE clients
                ADD COLUMN IF NOT EXISTS projects JSON DEFAULT '[]'::json
            """))
            conn.commit()
            logger.info("✓ Successfully added projects column to clients table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove projects column from clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing projects column from clients table...")
            conn.execute(text("""
                ALTER TABLE clients
                DROP COLUMN IF EXISTS projects
            """))
            conn.commit()
            logger.info("✓ Successfully removed projects column from clients table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add projects to clients")
    upgrade()
    print("Migration completed successfully!")
