"""Fix onboarding route enum"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    print("Fixing onboarding_route enum...")

    # Step 1: Add temp column
    print("Step 1: Adding temp column...")
    conn.execute(text("ALTER TABLE contractors ADD COLUMN onboarding_route_temp VARCHAR(50);"))
    conn.commit()

    # Step 2: Copy data
    print("Step 2: Copying data...")
    conn.execute(text("UPDATE contractors SET onboarding_route_temp = onboarding_route::text WHERE onboarding_route IS NOT NULL;"))
    conn.commit()

    # Step 3: Drop old column and enum
    print("Step 3: Dropping old column and enum...")
    conn.execute(text("ALTER TABLE contractors DROP COLUMN onboarding_route;"))
    conn.commit()
    conn.execute(text("DROP TYPE IF EXISTS onboardingroute;"))
    conn.commit()

    # Step 4: Create new enum with lowercase values
    print("Step 4: Creating new enum...")
    conn.execute(text("""
        CREATE TYPE onboardingroute AS ENUM ('wps_freelancer', 'third_party');
    """))
    conn.commit()

    # Step 5: Add column back
    print("Step 5: Adding column back...")
    conn.execute(text("ALTER TABLE contractors ADD COLUMN onboarding_route onboardingroute;"))
    conn.commit()

    # Step 6: Copy data back (converting to lowercase)
    print("Step 6: Copying data back...")
    conn.execute(text("UPDATE contractors SET onboarding_route = LOWER(onboarding_route_temp)::onboardingroute WHERE onboarding_route_temp IS NOT NULL;"))
    conn.commit()

    # Step 7: Drop temp column
    print("Step 7: Dropping temp column...")
    conn.execute(text("ALTER TABLE contractors DROP COLUMN onboarding_route_temp;"))
    conn.commit()

    print("[SUCCESS] onboarding_route enum fixed!")

print("\nTesting query...")
from app.database import SessionLocal
from app.models.contractor import Contractor

db = SessionLocal()
try:
    contractors = db.query(Contractor).all()
    print(f"[SUCCESS] Found {len(contractors)} contractors")
    for c in contractors:
        print(f"  - {c.first_name} {c.surname}: status={c.status}, route={c.onboarding_route}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
