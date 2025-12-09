"""
Update client address fields to use consistent Address Line 1-4 format
Remove: registered_address, city, postal_code
Add: address_line1, address_line2, address_line3, address_line4
Keep: country
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found in environment variables")

engine = create_engine(database_url)


def upgrade():
    """Update address fields in clients table"""
    with engine.connect() as conn:
        # Add new address line fields
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS address_line1 VARCHAR,
            ADD COLUMN IF NOT EXISTS address_line2 VARCHAR,
            ADD COLUMN IF NOT EXISTS address_line3 VARCHAR,
            ADD COLUMN IF NOT EXISTS address_line4 VARCHAR
        """))

        # Drop old address fields
        conn.execute(text("""
            ALTER TABLE clients
            DROP COLUMN IF EXISTS registered_address,
            DROP COLUMN IF EXISTS city,
            DROP COLUMN IF EXISTS postal_code
        """))

        conn.commit()
        print("✅ Migration completed: Updated client address fields to Address Line 1-4 format")


def downgrade():
    """Revert address fields in clients table"""
    with engine.connect() as conn:
        # Add back old fields
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS registered_address VARCHAR,
            ADD COLUMN IF NOT EXISTS city VARCHAR,
            ADD COLUMN IF NOT EXISTS postal_code VARCHAR
        """))

        # Remove new address line fields
        conn.execute(text("""
            ALTER TABLE clients
            DROP COLUMN IF EXISTS address_line1,
            DROP COLUMN IF EXISTS address_line2,
            DROP COLUMN IF EXISTS address_line3,
            DROP COLUMN IF EXISTS address_line4
        """))

        conn.commit()
        print("✅ Migration rolled back: Reverted to old address field format")


if __name__ == "__main__":
    print("Running migration: update_client_address_fields")
    upgrade()
