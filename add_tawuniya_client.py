"""
Script to add Tawuniya client to the database
"""
import requests
import json

# API endpoint
API_URL = "http://localhost:8000/api/v1/clients/"

# Login first to get token
login_url = "http://localhost:8000/api/v1/auth/login"

# You'll need to replace these with actual credentials
# For now, this script shows the structure
login_data = {
    "email": "admin@example.com",  # Replace with actual admin email
    "password": "admin_password"   # Replace with actual password
}

def add_tawuniya_client(token):
    """Add Tawuniya client with provided details"""

    client_data = {
        "company_name": "Tawuniya",
        "industry": "Insurance",
        "company_reg_no": "",
        "company_vat_no": "",
        "address_line1": "Tawuniya - HO&CRO - Head office & Central Regional Office",
        "address_line2": "Additional 45, Building No. 6507,",
        "address_line3": "Unit No. 55 Al Rabie District, Al Thumama Street Riyadh, 15 - SA",
        "address_line4": "",
        "country": "Saudi Arabia",
        "contact_person_name": "Hamad Alharthi",
        "contact_person_email": "halharthi@tawuniya.com",
        "contact_person_phone": "",
        "contact_person_title": "",
        "bank_name": "",
        "account_number": "",
        "iban_number": "",
        "swift_code": "",
        "website": "",
        "notes": "Invoice Email: halharthi@tawuniya.com, malnowaiser@tawuniya.com\nClient Contacts: Hamad Alharthi, Mohammed Alnowaiser",
        "is_active": True,
        # Workflow Configuration
        "work_order_applicable": False,
        "proposal_applicable": False,
        # Timesheet Configuration
        "timesheet_required": True,
        "timesheet_approver_name": "MUHAMMAD ABU SIRAJ",
        # Payment Terms
        "po_required": False,
        "po_number": "PO-Q2-10096-25",
        "contractor_pay_frequency": "Monthly",
        "client_invoice_frequency": "Monthly",
        "client_payment_terms": "Net 14",
        "invoicing_preferences": "Per Worker",
        "invoice_instructions": "",
        # Supporting Documents
        "supporting_documents_required": ["Invoice"]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print("Adding Tawuniya client...")
    print(json.dumps(client_data, indent=2))

    response = requests.post(API_URL, json=client_data, headers=headers)

    if response.status_code == 201:
        print("\n✓ Client created successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n✗ Error creating client: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Please login to get authentication token")
    print(f"Login URL: {login_url}")
    print("\nThen call add_tawuniya_client(token) with your token")
    print("\nOr manually enter the token below:")

    token = input("Enter your auth token: ").strip()

    if token:
        add_tawuniya_client(token)
    else:
        print("No token provided. Exiting.")
