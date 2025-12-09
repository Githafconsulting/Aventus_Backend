"""
Add REJECTED status to ContractorStatus enum
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

def upgrade():
    """Add REJECTED to contractor status enum"""
    with engine.connect() as conn:
        # Add the new value to the enum type
        conn.execute(text("""
            ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS 'rejected';
        """))
        conn.commit()
        print("[SUCCESS] Added REJECTED status to ContractorStatus enum")

if __name__ == "__main__":
    print("Running migration: Add REJECTED status to ContractorStatus enum")
    upgrade()
    print("Migration completed successfully!")
