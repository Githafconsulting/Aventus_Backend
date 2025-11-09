import resend
from app.config import settings
from datetime import datetime
from typing import Optional

# Initialize Resend with API key
resend.api_key = settings.resend_api_key


def send_contract_email(
    contractor_email: str,
    contractor_name: str,
    contract_token: str,
    expiry_date: datetime
) -> bool:
    """
    Send contract signing email to contractor
    """
    contract_link = f"{settings.contract_signing_url}?token={contract_token}"
    expiry_str = expiry_date.strftime("%B %d, %Y at %I:%M %p")
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contract Ready for Signature</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                padding: 20px 0;
            }}
            .email-wrapper {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                text-align: center;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                margin-bottom: 12px;
            }}
            .header-title {{
                color: #FF6B00;
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 16px;
            }}
            .intro-text {{
                font-size: 14px;
                color: #4a4a4a;
                margin-bottom: 16px;
                line-height: 1.6;
            }}
            .contract-box {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .contract-icon {{
                font-size: 36px;
                margin-bottom: 10px;
            }}
            .contract-title {{
                font-size: 16px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 8px;
            }}
            .expiry-notice {{
                background-color: #fffbf0;
                border-left: 3px solid #ffa726;
                padding: 12px 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .expiry-notice strong {{
                color: #f57c00;
                display: block;
                margin-bottom: 4px;
                font-size: 13px;
            }}
            .expiry-notice p {{
                margin: 0;
                color: #5d4037;
                font-size: 13px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin: 20px 0;
            }}
            .cta-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b6b6b;
                margin: 6px 0;
            }}
            .divider {{
                height: 1px;
                background-color: #e0e0e0;
                margin: 20px 0;
            }}
            .signature {{
                margin-top: 20px;
                font-size: 14px;
                color: #4a4a4a;
            }}
            .signature-name {{
                font-weight: 600;
                color: #FF6B00;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="header-title">{settings.company_name}</h1>
            </div>

            <div class="content">
                <h2 class="greeting">Hello, {contractor_name}!</h2>

                <p class="intro-text">
                    Welcome to {settings.company_name}! We're thrilled to have you join our team.
                </p>

                <div class="contract-box">
                    <div class="contract-icon">📄</div>
                    <div class="contract-title">Your Employment Contract is Ready</div>
                    <p style="color: #6b6b6b; font-size: 14px; margin-top: 10px;">
                        Please review and sign your employment contract to complete your onboarding.
                    </p>
                </div>

                <div class="cta-container">
                    <a href="{contract_link}" class="cta-button">Review & Sign Contract</a>
                </div>

                <div class="expiry-notice">
                    <strong>Time-Sensitive Document</strong>
                    <p>This contract link will expire on <strong>{expiry_str}</strong>. Please review and sign it at your earliest convenience.</p>
                </div>

                <div class="divider"></div>

                <p class="intro-text">
                    If you have any questions or concerns about the contract, please don't hesitate to reach out to our HR team. We're here to help make this process as smooth as possible.
                </p>

                <div class="signature">
                    Best regards,<br>
                    <span class="signature-name">The {settings.company_name} Team</span>
                </div>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated message. Please do not reply to this email.</p>
                <p class="footer-text">If you did not expect this email, please contact us immediately.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [contractor_email],
            "subject": f"Your Employment Contract - Action Required",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Contract email sent to {contractor_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send contract email: {str(e)}")
        return False


def send_activation_email(
    contractor_email: str,
    contractor_name: str,
    temporary_password: str
) -> bool:
    """
    Send account activation email with login credentials
    """
    login_link = settings.frontend_url
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to {settings.company_name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.5;
                color: #333333;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .email-container {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 6px;
                overflow: hidden;
                border: 1px solid #e0e0e0;
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                display: block;
                margin-bottom: 8px;
            }}
            .company-name {{
                font-size: 18px;
                font-weight: 600;
                color: #FF6B00;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 12px;
            }}
            .intro {{
                font-size: 14px;
                color: #555555;
                margin-bottom: 20px;
                line-height: 1.6;
            }}
            .credentials {{
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 16px;
                margin: 16px 0;
            }}
            .credentials-title {{
                font-size: 13px;
                font-weight: 600;
                color: #333333;
                margin-bottom: 12px;
            }}
            .cred-row {{
                margin-bottom: 10px;
            }}
            .cred-row:last-child {{
                margin-bottom: 0;
            }}
            .cred-label {{
                font-size: 12px;
                color: #666666;
                display: block;
                margin-bottom: 4px;
            }}
            .cred-value {{
                font-size: 14px;
                color: #1a1a1a;
                font-weight: 500;
                font-family: 'Courier New', monospace;
                background-color: #ffffff;
                padding: 6px 10px;
                border-radius: 3px;
                border: 1px solid #d0d0d0;
                display: inline-block;
            }}
            .notice {{
                background-color: #fffbf0;
                border-left: 3px solid #ffb020;
                padding: 12px;
                margin: 16px 0;
                font-size: 13px;
                color: #666666;
                line-height: 1.5;
            }}
            .button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 11px 28px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 14px;
                margin: 16px 0;
            }}
            .button-container {{
                text-align: center;
                margin: 20px 0 16px 0;
            }}
            .footer {{
                background-color: #f9f9f9;
                padding: 16px 24px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #888888;
                margin: 4px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="company-name">{settings.company_name}</h1>
            </div>

            <div class="content">
                <h2 class="greeting">Welcome, {contractor_name}!</h2>

                <p class="intro">
                    Your account has been created. Below are your login credentials to access your dashboard.
                </p>

                <div class="credentials">
                    <div class="credentials-title">Login Credentials</div>
                    <div class="cred-row">
                        <span class="cred-label">Email</span><br>
                        <span class="cred-value">{contractor_email}</span>
                    </div>
                    <div class="cred-row">
                        <span class="cred-label">Temporary Password</span><br>
                        <span class="cred-value">{temporary_password}</span>
                    </div>
                </div>

                <div class="notice">
                    <strong>Important:</strong> You'll need to change this password when you first login.
                </div>

                <div class="button-container">
                    <a href="{login_link}" class="button">Login to Dashboard</a>
                </div>

                <p class="intro" style="margin-top: 16px; margin-bottom: 8px; font-size: 13px;">
                    If you have any questions, please contact our support team.
                </p>

                <p class="intro" style="margin-top: 8px; font-size: 13px;">
                    Best regards,<br>
                    <strong>{settings.company_name} Team</strong>
                </p>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated message. Please do not reply.</p>
                <p class="footer-text">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [contractor_email],
            "subject": f"Your {settings.company_name} Account is Active - Login Credentials",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Activation email sent to {contractor_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send activation email: {str(e)}")
        return False


def send_password_reset_email(
    user_email: str,
    user_name: str,
    reset_token: str
) -> bool:
    """
    Send password reset email
    """
    reset_link = f"{settings.password_reset_url}?token={reset_token}"
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset Request</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                padding: 20px 0;
            }}
            .email-wrapper {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                text-align: center;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                margin-bottom: 12px;
            }}
            .header-title {{
                color: #FF6B00;
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .icon-wrapper {{
                text-align: center;
                margin-bottom: 16px;
            }}
            .icon {{
                font-size: 48px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 16px;
                text-align: center;
            }}
            .intro-text {{
                font-size: 14px;
                color: #4a4a4a;
                margin-bottom: 16px;
                line-height: 1.6;
                text-align: center;
            }}
            .security-notice {{
                background-color: #fffbf0;
                border-left: 3px solid #ffa726;
                padding: 12px 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .security-notice strong {{
                color: #f57c00;
                display: block;
                margin-bottom: 4px;
                font-size: 13px;
            }}
            .security-notice p {{
                margin: 0;
                color: #5d4037;
                font-size: 13px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin: 20px 0;
            }}
            .cta-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b6b6b;
                margin: 6px 0;
            }}
            .divider {{
                height: 1px;
                background-color: #e0e0e0;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="header-title">{settings.company_name}</h1>
            </div>

            <div class="content">
                <div class="icon-wrapper">
                    <div class="icon">🔒</div>
                </div>

                <h2 class="greeting">Password Reset Request</h2>

                <p class="intro-text">
                    Hello {user_name},<br><br>
                    We received a request to reset your password. Click the button below to create a new password for your account.
                </p>

                <div class="cta-container">
                    <a href="{reset_link}" class="cta-button">Reset Your Password</a>
                </div>

                <div class="security-notice">
                    <strong>Security Information</strong>
                    <p>This link will expire in 1 hour for security reasons. If you didn't request a password reset, please ignore this email - your password will remain unchanged.</p>
                </div>

                <div class="divider"></div>

                <p class="intro-text" style="font-size: 14px; color: #6b6b6b;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <span style="color: #FF6B00; word-break: break-all;">{reset_link}</span>
                </p>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated message. Please do not reply to this email.</p>
                <p class="footer-text">If you have any concerns, please contact our support team.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [user_email],
            "subject": "Password Reset Request",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Password reset email sent to {user_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {str(e)}")
        return False


def send_document_upload_email(
    contractor_email: str,
    contractor_name: str,
    document_token: str,
    expiry_date: datetime
) -> bool:
    """
    Send document upload email to contractor
    """
    document_upload_link = f"{settings.frontend_url}/documents/upload/{document_token}"
    expiry_str = expiry_date.strftime("%B %d, %Y at %I:%M %p")
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document Upload Required</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                padding: 20px 0;
            }}
            .email-wrapper {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                text-align: center;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                margin-bottom: 12px;
            }}
            .header-title {{
                color: #FF6B00;
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 16px;
            }}
            .intro-text {{
                font-size: 14px;
                color: #4a4a4a;
                margin-bottom: 16px;
                line-height: 1.6;
            }}
            .document-box {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
            }}
            .document-icon {{
                font-size: 36px;
                text-align: center;
                margin-bottom: 10px;
            }}
            .document-title {{
                font-size: 16px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 12px;
                text-align: center;
            }}
            .document-list {{
                list-style: none;
                padding: 0;
                margin: 10px 0;
            }}
            .document-list li {{
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
                color: #4a4a4a;
                font-size: 14px;
            }}
            .document-list li:before {{
                content: "✓";
                color: #FF6B00;
                font-weight: bold;
                margin-right: 10px;
            }}
            .document-list li:last-child {{
                border-bottom: none;
            }}
            .expiry-notice {{
                background-color: #fffbf0;
                border-left: 3px solid #ffa726;
                padding: 12px 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .expiry-notice strong {{
                color: #f57c00;
                display: block;
                margin-bottom: 4px;
                font-size: 13px;
            }}
            .expiry-notice p {{
                margin: 0;
                color: #5d4037;
                font-size: 13px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin: 20px 0;
            }}
            .cta-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b6b6b;
                margin: 6px 0;
            }}
            .divider {{
                height: 1px;
                background-color: #e0e0e0;
                margin: 20px 0;
            }}
            .signature {{
                margin-top: 20px;
                font-size: 14px;
                color: #4a4a4a;
            }}
            .signature-name {{
                font-weight: 600;
                color: #FF6B00;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="header-title">{settings.company_name}</h1>
            </div>

            <div class="content">
                <h2 class="greeting">Hello, {contractor_name}!</h2>

                <p class="intro-text">
                    Welcome to {settings.company_name}! We're excited to start your onboarding process.
                </p>

                <p class="intro-text">
                    To continue with your onboarding, we need you to upload the following required documents:
                </p>

                <div class="document-box">
                    <div class="document-icon">📋</div>
                    <div class="document-title">Required Documents</div>
                    <ul class="document-list">
                        <li>Passport (photo page)</li>
                        <li>Recent Photo (passport size)</li>
                        <li>Visa Page (if applicable)</li>
                        <li>Emirates ID or Karma</li>
                        <li>Degree Certificate</li>
                    </ul>
                </div>

                <div class="cta-container">
                    <a href="{document_upload_link}" class="cta-button">Upload Documents</a>
                </div>

                <div class="expiry-notice">
                    <strong>Time-Sensitive Request</strong>
                    <p>This upload link will expire on <strong>{expiry_str}</strong>. Please upload your documents at your earliest convenience to avoid delays in your onboarding.</p>
                </div>

                <div class="divider"></div>

                <p class="intro-text">
                    <strong>Tips for uploading documents:</strong>
                </p>
                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    • Ensure all documents are clear and readable<br>
                    • Accepted formats: PDF, JPG, PNG<br>
                    • Maximum file size: 10MB per document<br>
                    • Make sure all information is visible and not cut off
                </p>

                <div class="divider"></div>

                <p class="intro-text">
                    If you have any questions or encounter any issues, please don't hesitate to contact our HR team. We're here to help!
                </p>

                <div class="signature">
                    Best regards,<br>
                    <span class="signature-name">The {settings.company_name} Team</span>
                </div>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated message. Please do not reply to this email.</p>
                <p class="footer-text">If you did not expect this email, please contact us immediately.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [contractor_email],
            "subject": f"Document Upload Required - {settings.company_name} Onboarding",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Document upload email sent to {contractor_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send document upload email: {str(e)}")
        return False


def send_documents_uploaded_notification(
    consultant_email: str,
    consultant_name: str,
    contractor_name: str,
    contractor_id: str
) -> bool:
    """
    Notify consultant that contractor has uploaded documents
    """
    contractor_link = f"{settings.frontend_url}/dashboard/contractors/{contractor_id}"
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Documents Uploaded</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                padding: 20px 0;
            }}
            .email-wrapper {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                text-align: center;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                margin-bottom: 12px;
            }}
            .header-title {{
                color: #FF6B00;
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 16px;
            }}
            .intro-text {{
                font-size: 14px;
                color: #4a4a4a;
                margin-bottom: 16px;
                line-height: 1.6;
            }}
            .status-box {{
                background-color: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .status-icon {{
                font-size: 36px;
                margin-bottom: 10px;
            }}
            .status-title {{
                font-size: 16px;
                font-weight: 600;
                color: #166534;
                margin-bottom: 8px;
            }}
            .contractor-name {{
                font-size: 18px;
                font-weight: 700;
                color: #FF6B00;
                margin: 8px 0;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin: 20px 0;
            }}
            .cta-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b6b6b;
                margin: 6px 0;
            }}
            .divider {{
                height: 1px;
                background-color: #e0e0e0;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="header-title">{settings.company_name}</h1>
            </div>

            <div class="content">
                <h2 class="greeting">Hello, {consultant_name}!</h2>

                <div class="status-box">
                    <div class="status-icon">✅</div>
                    <div class="status-title">Documents Uploaded</div>
                    <div class="contractor-name">{contractor_name}</div>
                    <p style="color: #166534; font-size: 14px; margin-top: 10px;">
                        has successfully uploaded all required documents
                    </p>
                </div>

                <p class="intro-text">
                    The contractor has completed the document upload phase. The next step is to fill out the costing sheet to proceed with the onboarding.
                </p>

                <div class="cta-container">
                    <a href="{contractor_link}" class="cta-button">Complete Costing Sheet</a>
                </div>

                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    Once the costing sheet is completed, the contractor information will be sent to admins for review and approval.
                </p>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated notification from {settings.company_name}.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [consultant_email],
            "subject": f"Documents Uploaded - {contractor_name}",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Documents uploaded notification sent to {consultant_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send documents uploaded notification: {str(e)}")
        return False


def send_review_notification(
    admin_emails: list,
    contractor_name: str,
    consultant_name: str,
    contractor_id: str
) -> bool:
    """
    Notify admins/superadmins that a contractor is ready for review
    """
    contractor_link = f"{settings.frontend_url}/dashboard/contractors/{contractor_id}"
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contractor Ready for Review</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                padding: 20px 0;
            }}
            .email-wrapper {{
                max-width: 560px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: #ffffff;
                padding: 24px 24px 16px 24px;
                text-align: center;
                border-bottom: 2px solid #f0f0f0;
            }}
            .logo {{
                max-width: 120px;
                height: auto;
                margin-bottom: 12px;
            }}
            .header-title {{
                color: #FF6B00;
                font-size: 18px;
                font-weight: 600;
                margin: 0;
            }}
            .content {{
                padding: 24px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 16px;
            }}
            .intro-text {{
                font-size: 14px;
                color: #4a4a4a;
                margin-bottom: 16px;
                line-height: 1.6;
            }}
            .status-box {{
                background-color: #fef3c7;
                border: 1px solid #fbbf24;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .status-icon {{
                font-size: 36px;
                margin-bottom: 10px;
            }}
            .status-title {{
                font-size: 16px;
                font-weight: 600;
                color: #92400e;
                margin-bottom: 8px;
            }}
            .contractor-name {{
                font-size: 18px;
                font-weight: 700;
                color: #FF6B00;
                margin: 8px 0;
            }}
            .info-row {{
                background-color: #f8f9fa;
                padding: 12px;
                border-radius: 4px;
                margin: 10px 0;
                text-align: left;
            }}
            .info-label {{
                font-size: 12px;
                color: #6b6b6b;
                display: block;
                margin-bottom: 4px;
            }}
            .info-value {{
                font-size: 14px;
                font-weight: 600;
                color: #1a1a1a;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #FF6B00;
                color: #ffffff;
                text-decoration: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                margin: 20px 0;
            }}
            .cta-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .footer-text {{
                font-size: 12px;
                color: #6b6b6b;
                margin: 6px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <img src="{logo_url}" alt="{settings.company_name}" class="logo">
                <h1 class="header-title">{settings.company_name}</h1>
            </div>

            <div class="content">
                <h2 class="greeting">Action Required</h2>

                <div class="status-box">
                    <div class="status-icon">👀</div>
                    <div class="status-title">Contractor Pending Review</div>
                    <div class="contractor-name">{contractor_name}</div>
                </div>

                <div class="info-row">
                    <span class="info-label">Submitted by:</span>
                    <span class="info-value">{consultant_name}</span>
                </div>

                <p class="intro-text">
                    A new contractor has completed the document upload and costing sheet. Please review the submitted information and documents to proceed with the approval.
                </p>

                <p class="intro-text">
                    <strong>Review Checklist:</strong>
                </p>
                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    • Verify all uploaded documents are clear and valid<br>
                    • Review costing sheet and placement details<br>
                    • Confirm contractor information is accurate<br>
                    • Approve or request corrections
                </p>

                <div class="cta-container">
                    <a href="{contractor_link}" class="cta-button">Review Contractor</a>
                </div>

                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    Once approved, the system will automatically generate and send the employment contract to the contractor for signature.
                </p>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated notification from {settings.company_name}.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": admin_emails,
            "subject": f"Contractor Pending Review - {contractor_name}",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Review notification sent to admins: {email}")
        return True
    except Exception as e:
        print(f"Failed to send review notification: {str(e)}")
        return False
