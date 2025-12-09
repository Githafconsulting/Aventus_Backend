"""
Migration: Create quote_sheets table
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
    """Create quote_sheets table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Creating quote_sheets table...")

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quote_sheets (
                    id VARCHAR PRIMARY KEY,
                    contractor_id VARCHAR NOT NULL,
                    third_party_id VARCHAR NOT NULL,
                    consultant_id VARCHAR NOT NULL,
                    upload_token VARCHAR UNIQUE NOT NULL,
                    token_expiry TIMESTAMP NOT NULL,
                    contractor_name VARCHAR,
                    third_party_company_name VARCHAR,
                    proposed_rate FLOAT,
                    currency VARCHAR DEFAULT 'AED',
                    payment_terms VARCHAR,
                    document_url VARCHAR,
                    document_filename VARCHAR,
                    additional_documents JSON DEFAULT '[]',
                    status VARCHAR DEFAULT 'pending',
                    notes VARCHAR,
                    consultant_notes VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_at TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE,
                    FOREIGN KEY (third_party_id) REFERENCES third_parties(id) ON DELETE CASCADE,
                    FOREIGN KEY (consultant_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))

            # Create index on upload_token
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quote_sheets_upload_token ON quote_sheets(upload_token)
            """))

            conn.commit()
            logger.info("✓ Successfully created quote_sheets table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Create quote_sheets table")
    upgrade()
    print("Migration completed successfully!")
