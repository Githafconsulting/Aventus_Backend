"""
Migration: Update work_orders table for contractor workflow
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
    """Update work_orders table with contractor workflow fields"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Adding contractor workflow fields to work_orders table...")

            # Add new status values to enum
            conn.execute(text("""
                ALTER TYPE workorderstatus ADD VALUE IF NOT EXISTS 'pending_approval'
            """))
            conn.execute(text("""
                ALTER TYPE workorderstatus ADD VALUE IF NOT EXISTS 'sent'
            """))
            conn.execute(text("""
                ALTER TYPE workorderstatus ADD VALUE IF NOT EXISTS 'declined'
            """))

            # Add new columns
            conn.execute(text("""
                ALTER TABLE work_orders
                ADD COLUMN IF NOT EXISTS contractor_name VARCHAR,
                ADD COLUMN IF NOT EXISTS client_name VARCHAR,
                ADD COLUMN IF NOT EXISTS project_name VARCHAR,
                ADD COLUMN IF NOT EXISTS role VARCHAR,
                ADD COLUMN IF NOT EXISTS duration VARCHAR,
                ADD COLUMN IF NOT EXISTS currency VARCHAR DEFAULT 'AED',
                ADD COLUMN IF NOT EXISTS business_type VARCHAR,
                ADD COLUMN IF NOT EXISTS umbrella_company_name VARCHAR,
                ADD COLUMN IF NOT EXISTS charge_rate VARCHAR,
                ADD COLUMN IF NOT EXISTS pay_rate VARCHAR,
                ADD COLUMN IF NOT EXISTS work_order_content VARCHAR,
                ADD COLUMN IF NOT EXISTS generated_by VARCHAR,
                ADD COLUMN IF NOT EXISTS generated_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS approved_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS sent_by VARCHAR,
                ADD COLUMN IF NOT EXISTS sent_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS declined_by VARCHAR,
                ADD COLUMN IF NOT EXISTS declined_date TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS decline_reason VARCHAR
            """))

            conn.commit()
            logger.info("✓ Successfully added contractor workflow fields to work_orders table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove contractor workflow fields from work_orders table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Removing contractor workflow fields from work_orders table...")

            # Remove columns
            conn.execute(text("""
                ALTER TABLE work_orders
                DROP COLUMN IF EXISTS contractor_name,
                DROP COLUMN IF EXISTS client_name,
                DROP COLUMN IF EXISTS project_name,
                DROP COLUMN IF EXISTS role,
                DROP COLUMN IF EXISTS duration,
                DROP COLUMN IF EXISTS currency,
                DROP COLUMN IF EXISTS business_type,
                DROP COLUMN IF EXISTS umbrella_company_name,
                DROP COLUMN IF EXISTS charge_rate,
                DROP COLUMN IF EXISTS pay_rate,
                DROP COLUMN IF EXISTS work_order_content,
                DROP COLUMN IF EXISTS generated_by,
                DROP COLUMN IF EXISTS generated_date,
                DROP COLUMN IF EXISTS approved_date,
                DROP COLUMN IF EXISTS sent_by,
                DROP COLUMN IF EXISTS sent_date,
                DROP COLUMN IF EXISTS declined_by,
                DROP COLUMN IF EXISTS declined_date,
                DROP COLUMN IF EXISTS decline_reason
            """))

            conn.commit()
            logger.info("✓ Successfully removed contractor workflow fields from work_orders table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Update work_orders table for contractor workflow")
    upgrade()
    print("Migration completed successfully!")
