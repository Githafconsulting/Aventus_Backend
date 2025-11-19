"""Test script to check third parties API serialization"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.models.third_party import ThirdParty
from app.schemas.third_party import ThirdPartyResponse
import json

load_dotenv()

# Test database connection and serialization
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Query third parties
    third_parties = db.query(ThirdParty).all()
    print(f"Found {len(third_parties)} third parties in database\n")

    if third_parties:
        # Test serialization
        for tp in third_parties:
            try:
                response = ThirdPartyResponse.model_validate(tp)
                print(f"OK - Successfully serialized: {response.company_name}")
                print(f"  - ID: {response.id}")
                print(f"  - Country: {response.country}")
                print(f"  - Address Line 1: {response.address_line1}")
                print(f"  - Address Line 2: {response.address_line2}")
                print(f"  - Company Type: {response.company_type}")
                print()
            except Exception as e:
                print(f"ERROR - Failed to serialize {tp.company_name}: {e}")
                print()
    else:
        print("No third parties found in database")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
