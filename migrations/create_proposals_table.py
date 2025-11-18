"""
Migration: Create proposals table
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
    """Create proposals table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Creating proposals table...")

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id VARCHAR PRIMARY KEY,
                    proposal_number VARCHAR UNIQUE NOT NULL,
                    client_id VARCHAR NOT NULL,
                    consultant_id VARCHAR NOT NULL,
                    client_company_name VARCHAR,
                    project_name VARCHAR NOT NULL,
                    project_description TEXT,
                    scope_of_work TEXT,
                    deliverables JSON DEFAULT '[]',
                    estimated_duration VARCHAR,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    milestones JSON DEFAULT '[]',
                    currency VARCHAR DEFAULT 'AED',
                    total_amount FLOAT,
                    payment_schedule JSON DEFAULT '[]',
                    terms_and_conditions TEXT,
                    assumptions TEXT,
                    exclusions TEXT,
                    proposal_content TEXT,
                    document_url VARCHAR,
                    attachments JSON DEFAULT '[]',
                    status VARCHAR DEFAULT 'draft',
                    valid_until TIMESTAMP,
                    sent_at TIMESTAMP,
                    viewed_at TIMESTAMP,
                    responded_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
                    FOREIGN KEY (consultant_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))

            # Create index on proposal_number
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proposals_proposal_number ON proposals(proposal_number)
            """))

            # Create index on client_id
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_proposals_client_id ON proposals(client_id)
            """))

            conn.commit()
            logger.info("✓ Successfully created proposals table")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Create proposals table")
    upgrade()
    print("Migration completed successfully!")
