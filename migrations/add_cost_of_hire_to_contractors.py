"""
Migration: Add cost of hire fields to contractors table
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
    """Add cost of hire columns to contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding cost of hire columns to contractors table...")

            # Add recruitment_cost column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS recruitment_cost VARCHAR
            """))

            # Add onboarding_cost column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS onboarding_cost VARCHAR
            """))

            # Add equipment_cost column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS equipment_cost VARCHAR
            """))

            # Add administrative_cost column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS administrative_cost VARCHAR
            """))

            # Add relocation_cost column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS relocation_cost VARCHAR
            """))

            # Add total_cost_of_hire column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS total_cost_of_hire VARCHAR
            """))

            # Add cost_of_hire_notes column
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS cost_of_hire_notes TEXT
            """))

            # Add cost_breakdown column as JSON
            conn.execute(text("""
                ALTER TABLE contractors
                ADD COLUMN IF NOT EXISTS cost_breakdown JSON
            """))

            conn.commit()
            logger.info("✓ Successfully added cost of hire columns to contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove cost of hire columns from contractors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing cost of hire columns from contractors table...")
            conn.execute(text("""
                ALTER TABLE contractors
                DROP COLUMN IF EXISTS recruitment_cost,
                DROP COLUMN IF EXISTS onboarding_cost,
                DROP COLUMN IF EXISTS equipment_cost,
                DROP COLUMN IF EXISTS administrative_cost,
                DROP COLUMN IF EXISTS relocation_cost,
                DROP COLUMN IF EXISTS total_cost_of_hire,
                DROP COLUMN IF EXISTS cost_of_hire_notes,
                DROP COLUMN IF EXISTS cost_breakdown
            """))
            conn.commit()
            logger.info("✓ Successfully removed cost of hire columns from contractors table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Add cost of hire to contractors")
    upgrade()
    print("Migration completed successfully!")
