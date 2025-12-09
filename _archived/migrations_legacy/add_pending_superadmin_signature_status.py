"""Add pending_superadmin_signature status to ContractorStatus enum"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add pending_superadmin_signature to contractor status enum"""
    with engine.connect() as conn:
        # Add new enum value to contractor status
        conn.execute(text("""
            ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS 'pending_superadmin_signature';
        """))
        print("[SUCCESS] Added pending_superadmin_signature status to ContractorStatus enum")

        conn.commit()
        print("[SUCCESS] Migration completed: Added pending_superadmin_signature status")

def downgrade():
    """
    Note: PostgreSQL does not support removing enum values directly.
    You would need to recreate the enum type if rollback is needed.
    """
    print("[WARNING] Downgrade not supported for enum values in PostgreSQL")
    print("[WARNING] To remove this status, you need to manually recreate the enum type")

if __name__ == "__main__":
    print("Running migration: Add pending_superadmin_signature status")
    upgrade()
    print("Migration completed successfully")
