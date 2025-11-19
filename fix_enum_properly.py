"""Fix the enum to use lowercase values"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    print("Fixing enum to use lowercase values...")

    # Drop the wrong enum
    print("Step 1: Dropping incorrect enum...")
    conn.execute(text("DROP TYPE IF EXISTS contractorstatus CASCADE;"))
    conn.commit()

    # Create enum with LOWERCASE values (the actual values from the Python enum)
    print("Step 2: Creating enum with lowercase values...")
    conn.execute(text("""
        CREATE TYPE contractorstatus AS ENUM (
            'draft',
            'pending_documents',
            'documents_uploaded',
            'pending_third_party_response',
            'pending_review',
            'approved',
            'rejected',
            'pending_signature',
            'signed',
            'active',
            'suspended'
        );
    """))
    conn.commit()

    # Add status column back
    print("Step 3: Adding status column...")
    conn.execute(text("""
        ALTER TABLE contractors
        ADD COLUMN status contractorstatus NOT NULL DEFAULT 'draft';
    """))
    conn.commit()

    print("[SUCCESS] Enum fixed!")

# Test query
print("\nTesting query...")
from app.database import SessionLocal
from app.models.contractor import Contractor

db = SessionLocal()
try:
    contractors = db.query(Contractor).all()
    print(f"[SUCCESS] Found {len(contractors)} contractors")
    for c in contractors[:3]:
        print(f"  - {c.email}: {c.status}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
