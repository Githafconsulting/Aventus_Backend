"""
Migration: Add client signature fields to work_orders table
Date: 2025-11-19
"""

from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add client signature fields and new status enum values to work_orders"""
    print("Starting migration: Add work order client signature fields...")

    with engine.connect() as conn:
        # 1. Add new enum values to workorderstatus
        print("1. Adding new work order status enum values...")
        try:
            conn.execute(text("""
                ALTER TYPE workorderstatus ADD VALUE IF NOT EXISTS 'pending_client_signature';
            """))
            conn.commit()
            print("✓ Added status: pending_client_signature")
        except Exception as e:
            print(f"- pending_client_signature: {str(e)}")

        try:
            conn.execute(text("""
                ALTER TYPE workorderstatus ADD VALUE IF NOT EXISTS 'client_signed';
            """))
            conn.commit()
            print("✓ Added status: client_signed")
        except Exception as e:
            print(f"- client_signed: {str(e)}")

        # 2. Add client signature fields to work_orders table
        print("2. Adding client signature fields to work_orders table...")
        conn.execute(text("""
            ALTER TABLE work_orders
            ADD COLUMN IF NOT EXISTS client_signature_token VARCHAR UNIQUE,
            ADD COLUMN IF NOT EXISTS client_signature_type VARCHAR,
            ADD COLUMN IF NOT EXISTS client_signature_data TEXT,
            ADD COLUMN IF NOT EXISTS client_signed_date TIMESTAMP WITH TIME ZONE;
        """))
        conn.commit()

        # 3. Create index on client_signature_token
        print("3. Creating index on client_signature_token...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_work_orders_client_signature_token
            ON work_orders(client_signature_token);
        """))
        conn.commit()

        print("[SUCCESS] Migration completed successfully!")

def downgrade():
    """Remove client signature fields from work_orders table"""
    with engine.connect() as conn:
        conn.execute(text("""
            DROP INDEX IF EXISTS ix_work_orders_client_signature_token;
        """))
        conn.execute(text("""
            ALTER TABLE work_orders
            DROP COLUMN IF EXISTS client_signature_token,
            DROP COLUMN IF EXISTS client_signature_type,
            DROP COLUMN IF EXISTS client_signature_data,
            DROP COLUMN IF EXISTS client_signed_date;
        """))
        conn.commit()
        print("[SUCCESS] Downgrade completed")

if __name__ == "__main__":
    print("Running migration: Add work order client signature fields")
    upgrade()
    print("Migration completed")
