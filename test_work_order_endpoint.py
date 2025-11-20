"""
Test script to verify work order endpoint with a real auth token
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
CONTRACTOR_ID = "4bed957d-c545-49f3-bcc9-a4cfa228e402"

# First, login to get a valid token
print("=" * 60)
print("STEP 1: Login to get auth token")
print("=" * 60)

# You'll need to replace these with your actual login credentials
login_data = {
    "username": "consultant@aventus.com",  # Change this
    "password": "password123"  # Change this
}

try:
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data
    )

    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        print(f"✅ Login successful!")
        print(f"Token: {access_token[:50]}...")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        exit(1)

except Exception as e:
    print(f"❌ Error during login: {str(e)}")
    exit(1)

# Test fetching work order
print("\n" + "=" * 60)
print("STEP 2: Fetch work order")
print("=" * 60)

headers = {
    "Authorization": f"Bearer {access_token}"
}

try:
    wo_response = requests.get(
        f"{BASE_URL}/api/v1/contractors/{CONTRACTOR_ID}/work-order",
        headers=headers
    )

    print(f"Status Code: {wo_response.status_code}")

    if wo_response.status_code == 200:
        print("✅ Work order fetched successfully!")
        work_order = wo_response.json()
        print(f"\nWork Order Details:")
        print(f"  Number: {work_order.get('work_order_number')}")
        print(f"  Contractor: {work_order.get('contractor_name')}")
        print(f"  Client: {work_order.get('client_name')}")
        print(f"  Role: {work_order.get('role')}")
        print(f"  Status: {work_order.get('status')}")
    else:
        print(f"❌ Failed to fetch work order: {wo_response.status_code}")
        print(f"Response: {wo_response.text}")

except Exception as e:
    print(f"❌ Error fetching work order: {str(e)}")

# Test sending work order
print("\n" + "=" * 60)
print("STEP 3: Test send work order endpoint")
print("=" * 60)

try:
    send_response = requests.post(
        f"{BASE_URL}/api/v1/contractors/{CONTRACTOR_ID}/work-order/approve",
        headers=headers
    )

    print(f"Status Code: {send_response.status_code}")

    if send_response.status_code == 200:
        print("✅ Work order sent successfully!")
        result = send_response.json()
        print(f"\nResult:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Failed to send work order: {send_response.status_code}")
        print(f"Response: {send_response.text}")

except Exception as e:
    print(f"❌ Error sending work order: {str(e)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
