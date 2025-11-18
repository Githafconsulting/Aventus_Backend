"""
Script to verify Tawuniya client was added to the database
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.client import Client

def verify_tawuniya_client():
    """Verify Tawuniya client exists in database"""

    db = SessionLocal()

    try:
        # Check if client exists
        client = db.query(Client).filter(Client.company_name == "Tawuniya").first()

        if client:
            print("SUCCESS: Tawuniya client found in database!")
            print(f"\nClient Details:")
            print(f"  ID: {client.id}")
            print(f"  Company Name: {client.company_name}")
            print(f"  Industry: {client.industry}")
            print(f"  Address Line 1: {client.address_line1}")
            print(f"  Address Line 2: {client.address_line2}")
            print(f"  Address Line 3: {client.address_line3}")
            print(f"  Country: {client.country}")
            print(f"  Contact Person: {client.contact_person_name}")
            print(f"  Contact Email: {client.contact_person_email}")
            print(f"  Timesheet Required: {client.timesheet_required}")
            print(f"  Timesheet Approver: {client.timesheet_approver_name}")
            print(f"  PO Number: {client.po_number}")
            print(f"  Contractor Pay Frequency: {client.contractor_pay_frequency}")
            print(f"  Client Invoice Frequency: {client.client_invoice_frequency}")
            print(f"  Payment Terms: {client.client_payment_terms}")
            print(f"  Invoicing Preferences: {client.invoicing_preferences}")
            print(f"  Supporting Documents: {client.supporting_documents_required}")
            print(f"  Active: {client.is_active}")
            print(f"  Created At: {client.created_at}")
            return True
        else:
            print("ERROR: Tawuniya client not found in database!")
            return False

    except Exception as e:
        print(f"ERROR verifying client: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    verify_tawuniya_client()
