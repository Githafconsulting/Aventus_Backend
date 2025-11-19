"""Add client_id column to contractors table"""
from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add client_id column to contractors table"""
    with engine.connect() as conn:
        # Add client_id column
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS client_id VARCHAR;
        """))
        conn.commit()
        print("[SUCCESS] Added client_id column to contractors table")

def downgrade():
    """Remove client_id column from contractors table"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE contractors
            DROP COLUMN IF EXISTS client_id;
        """))
        conn.commit()
        print("[SUCCESS] Removed client_id column from contractors table")

if __name__ == "__main__":
    print("Running migration: Add client_id to contractors")
    upgrade()
    print("Migration completed successfully")
