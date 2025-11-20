"""Test sending to papcyai@gmail.com"""
import resend
from app.config import settings

resend.api_key = settings.resend_api_key

print("=== Testing Email to papcyai@gmail.com ===\n")

try:
    params = {
        "from": settings.from_email,
        "to": ["papcyai@gmail.com"],
        "subject": "TEST - Work Order System Test",
        "html": """
        <html>
        <body>
            <h1>Test Email to Gmail</h1>
            <p>This is a test to verify papcyai@gmail.com can receive emails.</p>
            <p>If you receive this, everything is working!</p>
        </body>
        </html>
        """
    }

    print(f"From: {settings.from_email}")
    print(f"To: papcyai@gmail.com")
    print("Sending...")

    response = resend.Emails.send(params)

    print(f"\n[SUCCESS]")
    print(f"Email ID: {response['id']}")
    print(f"\nCheck:")
    print(f"  1. Resend dashboard: https://resend.com/emails")
    print(f"  2. Gmail inbox: papcyai@gmail.com")
    print(f"  3. Gmail spam folder (just in case)")

except Exception as e:
    print(f"\n[ERROR]")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
