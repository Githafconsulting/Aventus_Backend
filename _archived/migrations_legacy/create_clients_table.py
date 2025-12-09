"""
Migration: Create clients table
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
    """Create clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Creating clients table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clients (
                    id VARCHAR PRIMARY KEY,
                    company_name VARCHAR UNIQUE NOT NULL,
                    industry VARCHAR,
                    company_reg_no VARCHAR,
                    company_vat_no VARCHAR,
                    registered_address VARCHAR,
                    city VARCHAR,
                    country VARCHAR,
                    postal_code VARCHAR,
                    contact_person_name VARCHAR,
                    contact_person_email VARCHAR,
                    contact_person_phone VARCHAR,
                    contact_person_title VARCHAR,
                    bank_name VARCHAR,
                    account_number VARCHAR,
                    iban_number VARCHAR,
                    swift_code VARCHAR,
                    website VARCHAR,
                    notes VARCHAR,
                    documents JSON DEFAULT '[]'::json,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))

            # Create indexes
            logger.info("Creating indexes on clients table...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_clients_company_name
                ON clients(company_name)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_clients_is_active
                ON clients(is_active)
            """))

            conn.commit()
            logger.info("✓ Successfully created clients table with indexes")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Drop clients table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Dropping clients table...")
            conn.execute(text("DROP TABLE IF EXISTS clients CASCADE"))
            conn.commit()
            logger.info("✓ Successfully dropped clients table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Create clients table")
    upgrade()
    print("Migration completed successfully!")
