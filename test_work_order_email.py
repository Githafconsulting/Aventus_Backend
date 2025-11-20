"""Test work order email sending with real data"""
from app.utils.email import send_work_order_to_client
from app.database import SessionLocal
from app.models.work_order import WorkOrder

db = SessionLocal()

# Get the actual work order that was created
work_order = db.query(WorkOrder).filter(WorkOrder.work_order_number == 'WO-2025-0001').first()

if not work_order:
    print("[ERROR] Work order WO-2025-0001 not found!")
    db.close()
    exit(1)

print("=== Work Order Details ===")
print(f"Number: {work_order.work_order_number}")
print(f"Contractor: {work_order.contractor_name}")
print(f"Client: {work_order.client_name}")
print(f"Token: {work_order.client_signature_token[:30]}...")
print()

# Test client email from database
client_email = "donald@hsbc.co.uk"  # From HSBC client
signature_link = f"http://192.168.1.232:3000/sign-work-order/{work_order.client_signature_token}"

print("=== Sending Work Order Email ===")
print(f"To: {client_email}")
print(f"Signature Link: {signature_link}")
print()

try:
    result = send_work_order_to_client(
        client_email=client_email,
        client_company_name=work_order.client_name,
        work_order_number=work_order.work_order_number,
        contractor_name=work_order.contractor_name,
        signature_link=signature_link
    )

    if result:
        print("\n[SUCCESS] Email sent successfully!")
        print("Check the recipient's inbox: donald@hsbc.co.uk")
        print("Also check Resend dashboard: https://resend.com/emails")
    else:
        print("\n[FAILED] Email sending returned False")
        print("Check the error messages above")

except Exception as e:
    print(f"\n[EXCEPTION] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
