"""Test if contractors can be fetched"""
from app.database import SessionLocal
from app.models.contractor import Contractor

db = SessionLocal()

try:
    contractors = db.query(Contractor).all()
    print(f'SUCCESS: Found {len(contractors)} contractors')
    for c in contractors[:3]:
        print(f'  - {c.email}: {c.status}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
