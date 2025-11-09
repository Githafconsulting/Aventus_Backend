"""
Migration script to update the contractorstatus enum in the database
to include the new 'pending_documents' status value.
"""
import psycopg2
from app.config import settings

def update_contractor_status_enum():
    """Add missing enum values to contractorstatus enum"""

    # Parse the database URL to get connection parameters
    db_url = settings.database_url
    # postgresql://user:password@host:port/database

    print(f"[INFO] Connecting to database...")

    try:
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[INFO] Connected successfully!")

        # Check current enum values
        print("[INFO] Checking current contractorstatus enum values...")
        cursor.execute("""
            SELECT unnest(enum_range(NULL::contractorstatus))::text;
        """)
        current_values = [row[0] for row in cursor.fetchall()]
        print(f"[INFO] Current enum values: {current_values}")

        # Values that should exist
        required_values = [
            'draft',
            'pending_documents',
            'documents_uploaded',
            'pending_review',
            'approved',
            'pending_signature',
            'signed',
            'active',
            'suspended'
        ]

        # Find missing values
        missing_values = [v for v in required_values if v not in current_values]

        if not missing_values:
            print("[SUCCESS] All enum values are present!")
            cursor.close()
            conn.close()
            return

        print(f"[INFO] Missing enum values: {missing_values}")
        print("[INFO] Adding missing enum values...")

        for value in missing_values:
            try:
                cursor.execute(f"ALTER TYPE contractorstatus ADD VALUE '{value}'")
                print(f"[SUCCESS] Added '{value}' to contractorstatus enum")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[SKIP] '{value}' already exists")
                else:
                    raise

        # Verify final values
        cursor.execute("""
            SELECT unnest(enum_range(NULL::contractorstatus))::text;
        """)
        final_values = [row[0] for row in cursor.fetchall()]
        print(f"[SUCCESS] Final enum values: {final_values}")

        cursor.close()
        conn.close()
        print("[SUCCESS] Database enum updated successfully!")

    except Exception as e:
        print(f"[ERROR] Failed to update enum: {str(e)}")
        raise


if __name__ == "__main__":
    update_contractor_status_enum()
