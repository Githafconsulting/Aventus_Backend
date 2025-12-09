"""
Migration: Add workflow configuration fields to third_parties table
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
    """Add country, feature_config, and workflow_config columns to third_parties table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding workflow configuration fields to third_parties table...")

            # Add country column
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS country VARCHAR;
            """))

            # Add feature_config column (JSON)
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS feature_config JSON DEFAULT '{}'::json;
            """))

            # Add workflow_config column (JSON)
            conn.execute(text("""
                ALTER TABLE third_parties
                ADD COLUMN IF NOT EXISTS workflow_config JSON DEFAULT '{}'::json;
            """))

            conn.commit()
            logger.info("✓ Successfully added workflow configuration fields to third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove workflow configuration fields from third_parties table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing workflow configuration fields from third_parties table...")
            conn.execute(text("""
                ALTER TABLE third_parties
                DROP COLUMN IF EXISTS country,
                DROP COLUMN IF EXISTS feature_config,
                DROP COLUMN IF EXISTS workflow_config;
            """))
            conn.commit()
            logger.info("✓ Successfully removed workflow configuration fields from third_parties table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add workflow configuration to third_parties")
    upgrade()
    print("Migration completed successfully!")
