"""
Migration: Create templates table
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
    """Create templates table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Creating templates table...")

            # Create TemplateType enum
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

            # Create templates table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS templates (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    template_type templatetype NOT NULL,
                    description TEXT,
                    content TEXT NOT NULL,
                    country VARCHAR,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))

            # Create indexes
            logger.info("Creating indexes on templates table...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_templates_type
                ON templates(template_type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_templates_country
                ON templates(country)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_templates_is_active
                ON templates(is_active)
            """))

            conn.commit()
            logger.info("✓ Successfully created templates table with indexes")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Drop templates table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Dropping templates table...")
            conn.execute(text("DROP TABLE IF EXISTS templates CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS templatetype CASCADE"))
            conn.commit()
            logger.info("✓ Successfully dropped templates table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Create templates table")
    upgrade()
    print("Migration completed successfully!")
