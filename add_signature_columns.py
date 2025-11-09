"""
Migration script to add signature columns to users table
"""
from app.database import engine
from sqlalchemy import text

def add_signature_columns():
    """Add signature_type and signature_data columns to users table"""
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Add signature_type column
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS signature_type VARCHAR
            """))

            # Add signature_data column
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS signature_data TEXT
            """))

            trans.commit()
            print("✓ Successfully added signature columns to users table")

        except Exception as e:
            trans.rollback()
            print(f"✗ Error adding signature columns: {e}")
            raise

if __name__ == "__main__":
    print("Adding signature columns to users table...")
    add_signature_columns()
    print("Migration complete!")
