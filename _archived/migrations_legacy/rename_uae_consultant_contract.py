"""
Migration: Rename UAE Consultant Contract to Contractors Contract
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
    """Rename UAE Consultant Contract to Contractors Contract"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Renaming UAE Consultant Contract to Contractors Contract...")

            # Update the template name
            result = conn.execute(text("""
                UPDATE templates
                SET name = 'Contractors Contract'
                WHERE name = 'UAE Consultant Contract'
                AND template_type = 'contract'
                AND country = 'UAE'
            """))

            conn.commit()
            logger.info(f"✓ Successfully renamed template (rows affected: {result.rowcount})")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Rename UAE Consultant Contract")
    upgrade()
    print("Migration completed successfully!")
