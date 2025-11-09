"""
Test Resend email sending
"""
import resend
from app.config import settings

resend.api_key = settings.resend_api_key

print(f"Testing Resend with API key: {settings.resend_api_key[:10]}...")
print(f"From email: {settings.from_email}")
print(f"To email: papcynfor@gmail.com")

try:
    params = {
        "from": settings.from_email,
        "to": ["papcynfor@gmail.com"],
        "subject": "Test Email from Aventus HR",
        "html": "<h1>Test Email</h1><p>If you receive this, Resend is working!</p>",
    }

    result = resend.Emails.send(params)
    print(f"\n[SUCCESS] Email sent!")
    print(f"Result: {result}")

except Exception as e:
    print(f"\n[ERROR] Failed to send email:")
    print(f"Error: {str(e)}")
