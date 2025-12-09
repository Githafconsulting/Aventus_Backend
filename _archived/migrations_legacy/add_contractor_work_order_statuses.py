"""
Migration: Add work order related status values to contractorstatus enum
Date: 2025-11-19
"""

from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add work order and contract related status enum values to contractorstatus"""
    print("Starting migration: Add contractor work order status values...")

    status_values = [
        'pending_client_wo_signature',
        'work_order_completed',
        'pending_contract_upload',
        'contract_uploaded',
        'contract_approved'
    ]

    with engine.connect() as conn:
        for status_value in status_values:
            try:
                conn.execute(text(f"""
                    ALTER TYPE contractorstatus ADD VALUE IF NOT EXISTS '{status_value}';
                """))
                conn.commit()
                print(f"✓ Added status: {status_value}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"- Status already exists: {status_value}")
                else:
                    print(f"Warning for {status_value}: {str(e)}")

    print("[SUCCESS] Migration completed successfully!")

def downgrade():
    """Note: PostgreSQL doesn't support removing enum values once added"""
    print("[INFO] Downgrade not supported for enum values in PostgreSQL")

if __name__ == "__main__":
    print("Running migration: Add contractor work order status values")
    upgrade()
    print("Migration completed")
