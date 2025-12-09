"""
Update Quote Sheet Email template with inline styles for better email client compatibility
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Updated template with inline styles for the button
QUOTE_SHEET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{EMAIL_SUBJECT}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #f5f5f5;
            padding: 20px 0;
        }
        .email-wrapper {
            max-width: 560px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            background-color: #ffffff;
            padding: 24px 24px 16px 24px;
            text-align: center;
            border-bottom: 2px solid #f0f0f0;
        }
        .logo {
            max-width: 120px;
            height: auto;
            margin-bottom: 12px;
        }
        .header-title {
            color: #FF6B00;
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }
        .content {
            padding: 24px;
        }
        .greeting {
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 16px;
        }
        .message-body {
            font-size: 14px;
            color: #4a4a4a;
            margin-bottom: 20px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px 24px;
            text-align: center;
            border-top: 2px solid #f0f0f0;
        }
        .footer-text {
            font-size: 12px;
            color: #6b6b6b;
            margin-bottom: 8px;
        }
        .company-info {
            font-size: 10px;
            color: #999;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header with Logo -->
        <div class="header">
            <img src="{{LOGO_URL}}" alt="Aventus Logo" class="logo">
            <p class="header-title">Quote Sheet Request</p>
        </div>

        <!-- Main Content -->
        <div class="content">
            <p class="greeting">Dear {{THIRD_PARTY_COMPANY_NAME}},</p>

            <div class="message-body">{{EMAIL_BODY}}</div>

            <div style="text-align: center; margin-top: 30px;">
                <a href="{{UPLOAD_URL}}" target="_blank" style="display: inline-block; padding: 14px 32px; background-color: #FF6B00; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
                    Click to Upload Quote Sheet
                </a>
            </div>

            <p style="font-size: 12px; color: #6b6b6b; margin-top: 20px; text-align: center;">
                This link will expire in 30 days
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p class="footer-text">
                <strong>Aventus Resources</strong>
            </p>
            <p class="footer-text">
                If you have any questions, please contact your Aventus consultant:<br/>
                <strong>{{CONSULTANT_NAME}}</strong>
            </p>
            <p class="company-info">
                This is an automated email. Please do not reply to this message.
            </p>
        </div>
    </div>
</body>
</html>
"""

def upgrade():
    """Update quote sheet email template with inline styles"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            print("Updating Quote Sheet Email template with inline styles...")

            # Update the template content
            result = conn.execute(text("""
                UPDATE templates
                SET content = :content,
                    updated_at = NOW()
                WHERE template_type = 'quote_sheet'
                AND name = 'Quote Sheet Request Email'
                RETURNING id
            """), {
                "content": QUOTE_SHEET_EMAIL_TEMPLATE
            })

            updated_id = result.fetchone()

            if updated_id:
                print(f"[SUCCESS] Updated template ID: {updated_id[0]}")
                conn.commit()
            else:
                print("[WARNING] No template found to update")

        except Exception as e:
            print(f"[ERROR] Error during template update: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Update Quote Sheet Email template")
    upgrade()
    print("Migration completed successfully!")
