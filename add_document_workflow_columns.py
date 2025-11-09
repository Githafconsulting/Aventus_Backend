"""
Quick fix: Add uppercase enum values to database to match SQLAlchemy behavior
"""
import psycopg2
from app.config import settings

def add_uppercase_enum_values():
    """Add uppercase versions of enum values"""

    db_url = settings.database_url
    print(f"[INFO] Connecting to database...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("[INFO] Connected successfully!")

        # Values to add (uppercase versions that SQLAlchemy is trying to use)
        uppercase_values = [
            'PENDING_DOCUMENTS',
            'DOCUMENTS_UPLOADED',
            'PENDING_REVIEW',
            'APPROVED'
        ]

        print(f"[INFO] Adding uppercase enum values...")

        for value in uppercase_values:
            try:
                cursor.execute(f"ALTER TYPE contractorstatus ADD VALUE '{value}'")
                print(f"[SUCCESS] Added '{value}' to contractorstatus enum")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"[SKIP] '{value}' already exists")
                else:
                    print(f"[ERROR] Failed to add '{value}': {str(e)}")

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
    add_uppercase_enum_values()
