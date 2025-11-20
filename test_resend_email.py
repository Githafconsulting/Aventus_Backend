"""Test Resend API directly"""
import resend
from app.config import settings

# Initialize Resend
resend.api_key = settings.resend_api_key

print("=== Testing Resend Email API ===\n")
print(f"API Key: {settings.resend_api_key[:20]}...")
print(f"From Email: {settings.from_email}")
print(f"To Email: donald@hsbc.co.uk")  # Test with the client email
print()

try:
    params = {
        "from": settings.from_email,
        "to": ["donald@hsbc.co.uk"],  # Client email from database
        "subject": "TEST - Work Order Email System",
        "html": """
        <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email from Aventus HR Backend.</p>
            <p>If you receive this, the email system is working correctly!</p>
        </body>
        </html>
        """
    }

    print("Sending test email...")
    response = resend.Emails.send(params)

    print("\n[SUCCESS]")
    print(f"Response: {response}")

except Exception as e:
    print(f"\n[ERROR]")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")

    # Check for common issues
    if "domain" in str(e).lower():
        print("\n[HINT] Your domain 'papcy.com' may not be verified in Resend")
        print("   Go to: https://resend.com/domains")
        print("   And verify your domain or use a Resend test domain")

    if "api" in str(e).lower() or "key" in str(e).lower():
        print("\n[HINT] Check your Resend API key is correct")
        print("   Go to: https://resend.com/api-keys")

    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
