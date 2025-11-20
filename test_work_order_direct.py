"""Direct test of work order endpoint"""
import asyncio
from app.database import SessionLocal
from app.models.user import User
from app.routes.contractors import approve_contractor_work_order
from unittest.mock import Mock

async def test_work_order():
    print("=== Testing Work Order Endpoint Directly ===\n")

    # Get database session
    db = SessionLocal()

    # Get consultant user
    consultant = db.query(User).filter(User.email == 'papcynfor@gmail.com').first()
    if not consultant:
        print("[ERROR] Consultant user not found!")
        return

    print(f"[OK] Found consultant: {consultant.email}")

    # Create mock current_user
    mock_user = Mock()
    mock_user.id = consultant.id
    mock_user.email = consultant.email
    mock_user.role = consultant.role

    contractor_id = "4bed957d-c545-49f3-bcc9-a4cfa228e402"

    print(f"[OK] Testing contractor ID: {contractor_id}")
    print("\nCalling approve_contractor_work_order...")
    print("(This will create work order and attempt to send email)\n")

    try:
        result = await approve_contractor_work_order(
            contractor_id=contractor_id,
            db=db,
            current_user=mock_user
        )

        print("[SUCCESS]")
        print(f"\nResult:")
        print(f"  Message: {result['message']}")
        print(f"  Work Order ID: {result.get('work_order_id')}")
        print(f"  Work Order Number: {result.get('work_order_number')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Client Signature Link: {result.get('client_signature_link')}")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_work_order())
