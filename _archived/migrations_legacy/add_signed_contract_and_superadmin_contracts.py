"""Add signed_contract_url to contractors and contracts_signed to users"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add signed contract URL to contractors and contracts signed array to users"""
    with engine.connect() as conn:
        # Add signed_contract_url to contractors table
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS signed_contract_url VARCHAR;
        """))
        print("[SUCCESS] Added signed_contract_url to contractors table")

        # Add contracts_signed to users table (JSON field for superadmin)
        conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS contracts_signed JSON;
        """))
        print("[SUCCESS] Added contracts_signed to users table")

        conn.commit()
        print("[SUCCESS] Migration completed: Added signed contract tracking fields")

def downgrade():
    """Remove signed contract tracking fields"""
    with engine.connect() as conn:
        # Remove signed_contract_url from contractors
        conn.execute(text("""
            ALTER TABLE contractors
            DROP COLUMN IF EXISTS signed_contract_url;
        """))

        # Remove contracts_signed from users
        conn.execute(text("""
            ALTER TABLE users
            DROP COLUMN IF EXISTS contracts_signed;
        """))

        conn.commit()
        print("[SUCCESS] Removed signed contract tracking fields")

if __name__ == "__main__":
    print("Running migration: Add signed_contract_url and contracts_signed fields")
    upgrade()
    print("Migration completed successfully")
