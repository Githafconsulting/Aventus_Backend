"""
Migration: Add new personal information and document fields to contractors table

This migration adds:
- marital_status (personal info)
- number_of_children (personal info)
- address_line2 (address)
- id_front_document (document upload)
- id_back_document (document upload)

Run this migration using: python migrations/add_contractor_personal_and_document_fields.py
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Add new fields to contractors table"""
    with engine.connect() as conn:
        # Add marital_status field
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS marital_status VARCHAR
        """))

        # Add number_of_children field
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS number_of_children VARCHAR
        """))

        # Add address_line2 field
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS address_line2 VARCHAR
        """))

        # Add id_front_document field
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS id_front_document VARCHAR
        """))

        # Add id_back_document field
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS id_back_document VARCHAR
        """))

        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Added marital_status column")
        print("   - Added number_of_children column")
        print("   - Added address_line2 column")
        print("   - Added id_front_document column")
        print("   - Added id_back_document column")


def downgrade():
    """Remove the added fields (rollback)"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS marital_status"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS number_of_children"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS address_line2"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS id_front_document"))
        conn.execute(text("ALTER TABLE contractors DROP COLUMN IF EXISTS id_back_document"))
        conn.commit()
        print("✅ Rollback completed successfully!")


if __name__ == "__main__":
    print("Running migration: Add contractor personal and document fields...")
    upgrade()
