"""
Final fix for contractor status enum - Force recreation without introspection
"""
from sqlalchemy import create_engine, text, MetaData
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'), echo=False)

with engine.connect() as conn:
    print("Step 1: Dropping old enum type...")
    conn.execute(text("DROP TYPE IF EXISTS contractorstatus CASCADE;"))
    conn.commit()

    print("Step 2: Creating new enum type...")
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

    print("Step 3: Adding status column back...")
    conn.execute(text("""
        ALTER TABLE contractors
        ADD COLUMN status contractorstatus NOT NULL DEFAULT 'draft';
    """))
    conn.commit()

    print("[SUCCESS] Database enum fixed!")

# Clear SQLAlchemy metadata cache
print("\nStep 4: Clearing SQLAlchemy metadata cache...")
MetaData().clear()

print("\nStep 5: Testing with fresh connection...")
# Create a completely fresh engine without cache
test_engine = create_engine(os.getenv('DATABASE_URL'), echo=False, pool_pre_ping=True)

with test_engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, first_name, status FROM contractors LIMIT 3"))
    rows = result.fetchall()
    print(f"\n[SUCCESS] Found {len(rows)} contractors:")
    for row in rows:
        print(f"  - {row[2]} ({row[1]}): {row[3]}")

test_engine.dispose()
engine.dispose()

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. RESTART your backend server completely")
print("2. Make sure it fully stops first (Ctrl+C)")
print("3. Then start fresh: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
print("4. Refresh your frontend")
print("="*60)
