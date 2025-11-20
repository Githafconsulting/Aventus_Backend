"""Add contract upload fields to contractors table"""
from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add contract upload token and related fields to contractors table"""
    with engine.connect() as conn:
        # Add contract upload fields
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS contract_upload_token VARCHAR UNIQUE,
            ADD COLUMN IF NOT EXISTS contract_upload_token_expiry TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS client_uploaded_contract VARCHAR,
            ADD COLUMN IF NOT EXISTS contract_uploaded_date TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS contract_approved_date TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS contract_approved_by VARCHAR;
        """))

        # Create index on contract_upload_token
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_contractors_contract_upload_token
            ON contractors(contract_upload_token);
        """))

        conn.commit()
        print("[SUCCESS] Added contract upload fields to contractors table")

def downgrade():
    """Remove contract upload fields from contractors table"""
    with engine.connect() as conn:
        conn.execute(text("""
            DROP INDEX IF EXISTS ix_contractors_contract_upload_token;
        """))

        conn.execute(text("""
            ALTER TABLE contractors
            DROP COLUMN IF EXISTS contract_upload_token,
            DROP COLUMN IF EXISTS contract_upload_token_expiry,
            DROP COLUMN IF EXISTS client_uploaded_contract,
            DROP COLUMN IF EXISTS contract_uploaded_date,
            DROP COLUMN IF EXISTS contract_approved_date,
            DROP COLUMN IF EXISTS contract_approved_by;
        """))

        conn.commit()
        print("[SUCCESS] Removed contract upload fields from contractors table")

if __name__ == "__main__":
    print("Running migration: Add contract upload fields to contractors")
    upgrade()
    print("Migration completed successfully")
