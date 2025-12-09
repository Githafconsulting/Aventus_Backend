"""
Migration: Create work_orders table
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
    """Create work_orders table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Creating work_orders table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS work_orders (
                    id VARCHAR PRIMARY KEY,
                    work_order_number VARCHAR UNIQUE NOT NULL,
                    contractor_id VARCHAR NOT NULL REFERENCES contractors(id),
                    third_party_id VARCHAR REFERENCES third_parties(id),
                    title VARCHAR NOT NULL,
                    description VARCHAR,
                    location VARCHAR,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP,
                    hourly_rate FLOAT,
                    fixed_price FLOAT,
                    estimated_hours FLOAT,
                    actual_hours FLOAT DEFAULT 0,
                    status VARCHAR NOT NULL DEFAULT 'draft',
                    notes VARCHAR,
                    documents JSON DEFAULT '[]'::json,
                    created_by VARCHAR NOT NULL REFERENCES users(id),
                    approved_by VARCHAR REFERENCES users(id),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))

            # Create indexes
            logger.info("Creating indexes on work_orders table...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_work_orders_work_order_number
                ON work_orders(work_order_number)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_work_orders_contractor_id
                ON work_orders(contractor_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_work_orders_third_party_id
                ON work_orders(third_party_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_work_orders_status
                ON work_orders(status)
            """))

            conn.commit()
            logger.info("✓ Successfully created work_orders table with indexes")

        except Exception as e:
            logger.error(f"✗ Error during migration: {e}")
            conn.rollback()
            raise


def downgrade():
    """Drop work_orders table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Dropping work_orders table...")
            conn.execute(text("DROP TABLE IF EXISTS work_orders CASCADE"))
            conn.commit()
            logger.info("✓ Successfully dropped work_orders table")

        except Exception as e:
            logger.error(f"✗ Error during migration rollback: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Create work_orders table")
    upgrade()
    print("Migration completed successfully!")
