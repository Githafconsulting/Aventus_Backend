"""Restore the status column"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    print("Restoring status column...")

    # Add status column back with the enum type
    conn.execute(text("""
        ALTER TABLE contractors
        ADD COLUMN status contractorstatus NOT NULL DEFAULT 'draft';
    """))
    conn.commit()

    print("[SUCCESS] Status column restored!")

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
finally:
    db.close()
