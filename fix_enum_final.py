"""
Force SQLAlchemy to use the Python enum definition
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    print("Fixing contractor status enum...")

    # Step 1: Drop the old enum type CASCADE (this will temporarily break the column)
    print("Step 1: Dropping old enum type...")
    conn.execute(text("DROP TYPE IF EXISTS contractorstatus CASCADE;"))
    conn.commit()

    # Step 2: Import the model and create tables (this will create the enum from Python definition)
    print("Step 2: Creating enum from Python model...")
    from app.database import Base
    from app.models.contractor import Contractor, ContractorStatus

    # This will create the enum type based on the Python enum
    Base.metadata.create_all(bind=engine, tables=[Contractor.__table__], checkfirst=True)

    print("[SUCCESS] Enum recreated successfully!")
    print(f"Python enum values: {[e.value for e in ContractorStatus]}")

print("\n Testing query...")
from app.database import SessionLocal
db = SessionLocal()
try:
    contractors = db.query(Contractor).all()
    print(f"[SUCCESS] Found {len(contractors)} contractors")
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    db.close()
