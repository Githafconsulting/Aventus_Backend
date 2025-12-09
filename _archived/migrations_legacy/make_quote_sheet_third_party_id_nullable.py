"""
Migration: Make third_party_id nullable in quote_sheets table
This allows for direct email quote sheet requests (SAUDI route) without requiring
the third party to be in the database.
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
    """Make third_party_id nullable in quote_sheets table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Making third_party_id nullable in quote_sheets table...")

            # First, drop the foreign key constraint
            conn.execute(text("""
                ALTER TABLE quote_sheets
                DROP CONSTRAINT IF EXISTS quote_sheets_third_party_id_fkey
            """))

            # Make the column nullable
            conn.execute(text("""
                ALTER TABLE quote_sheets
                ALTER COLUMN third_party_id DROP NOT NULL
            """))

            # Re-add the foreign key constraint (now allowing NULL)
            conn.execute(text("""
                ALTER TABLE quote_sheets
                ADD CONSTRAINT quote_sheets_third_party_id_fkey
                FOREIGN KEY (third_party_id) REFERENCES third_parties(id) ON DELETE CASCADE
            """))

            conn.commit()
            logger.info("✓ Successfully made third_party_id nullable")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Make third_party_id nullable in quote_sheets table")
    upgrade()
    print("Migration completed successfully!")
