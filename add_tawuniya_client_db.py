"""
Script to add Tawuniya client directly to the database
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.client import Client
from datetime import datetime
import uuid

def add_tawuniya_client():
    """Add Tawuniya client with provided details"""

    db = SessionLocal()

    try:
        # Check if client already exists
        existing = db.query(Client).filter(Client.company_name == "Tawuniya").first()
        if existing:
            print("✗ Client 'Tawuniya' already exists!")
            print(f"   ID: {existing.id}")
            print(f"   Created at: {existing.created_at}")
            return

        # Create new client
        client = Client(
            id=str(uuid.uuid4()),
            company_name="Tawuniya",
            industry="Insurance",
            company_reg_no=None,
            company_vat_no=None,
            address_line1="Tawuniya - HO&CRO - Head office & Central Regional Office",
            address_line2="Additional 45, Building No. 6507,",
            address_line3="Unit No. 55 Al Rabie District, Al Thumama Street Riyadh, 15 - SA",
            address_line4=None,
            country="Saudi Arabia",
            contact_person_name="Hamad Alharthi",
            contact_person_email="halharthi@tawuniya.com",
            contact_person_phone=None,
            contact_person_title=None,
            bank_name=None,
            account_number=None,
            iban_number=None,
            swift_code=None,
            website=None,
            notes="Invoice Email: halharthi@tawuniya.com, malnowaiser@tawuniya.com\nClient Contacts: Hamad Alharthi, Mohammed Alnowaiser",
            is_active=True,
            # Workflow Configuration
            work_order_applicable=False,
            proposal_applicable=False,
            # Timesheet Configuration
            timesheet_required=True,
            timesheet_approver_name="MUHAMMAD ABU SIRAJ",
            # Payment Terms
            po_required=False,
            po_number="PO-Q2-10096-25",
            contractor_pay_frequency="Monthly",
            client_invoice_frequency="Monthly",
            client_payment_terms="Net 14",
            invoicing_preferences="Per Worker",
            invoice_instructions=None,
            # Supporting Documents
            supporting_documents_required=["Invoice"],
            documents=[],
            created_at=datetime.utcnow(),
            updated_at=None
        )

        db.add(client)
        db.commit()
        db.refresh(client)

        print("✓ Tawuniya client created successfully!")
        print(f"   ID: {client.id}")
        print(f"   Company Name: {client.company_name}")
        print(f"   Contact: {client.contact_person_name} ({client.contact_person_email})")
        print(f"   Address: {client.address_line1}")
        print(f"   Timesheet Required: {client.timesheet_required}")
        print(f"   Timesheet Approver: {client.timesheet_approver_name}")
        print(f"   Contractor Pay Frequency: {client.contractor_pay_frequency}")
        print(f"   Client Invoice Frequency: {client.client_invoice_frequency}")
        print(f"   Payment Terms: {client.client_payment_terms}")
        print(f"   Invoicing Preferences: {client.invoicing_preferences}")
        print(f"   PO Number: {client.po_number}")
        print(f"   Supporting Documents: {client.supporting_documents_required}")

    except Exception as e:
        db.rollback()
        print(f"✗ Error creating client: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding Tawuniya client to database...\n")
    add_tawuniya_client()
