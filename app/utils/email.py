import resend
from app.config import settings
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, text

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
                <h2 class="greeting">Welcome to {settings.company_name}!</h2>

                <p class="intro-text">
                    We're excited to start your onboarding process. To get started, we need you to provide your personal information and upload the following required documents:
                </p>

                <div class="document-box">
                    <div class="document-icon">📋</div>
                    <div class="document-title">Required Information & Documents</div>
                    <p style="font-size: 13px; color: #6b6b6b; margin-bottom: 10px;">Personal Information:</p>
                    <ul class="document-list">
                        <li>Full name, email, phone, date of birth</li>
                        <li>Gender, nationality, address</li>
                        <li>Bank account details (optional)</li>
                    </ul>
                    <p style="font-size: 13px; color: #6b6b6b; margin-top: 15px; margin-bottom: 10px;">Documents to Upload:</p>
                    <ul class="document-list">
                        <li>Passport</li>
                        <li>ID Front & Back</li>
                        <li>Visa</li>
                        <li>Passport Photo</li>
                        <li>Certificate (degree or diploma)</li>
                    </ul>
                </div>

                <div class="cta-container">
                    <a href="{document_upload_link}" class="cta-button">Complete Onboarding Form</a>
                </div>

                <div class="expiry-notice">
                    <strong>Time-Sensitive Request</strong>
                    <p>This link will expire on <strong>{expiry_str}</strong>. Please complete your information and upload your documents at your earliest convenience to avoid delays in your onboarding.</p>
                </div>

                <div class="divider"></div>

                <p class="intro-text">
                    <strong>Important Notes:</strong>
                </p>
                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    • Fill in all required personal information fields<br>
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
            "subject": f"Complete Your Onboarding - {settings.company_name}",
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
                    The contractor has successfully completed the document upload phase and provided all required personal information.
                </p>

                <p class="intro-text">
                    You can view the contractor details by clicking the button below.
                </p>

                <div class="cta-container">
                    <a href="{contractor_link}" class="cta-button">View Contractor Details</a>
                </div>

                <p class="intro-text" style="font-size: 13px; color: #6b6b6b;">
                    The next step is to complete the Contract Deal Sheet (CDS) to proceed with the onboarding.
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


def send_quote_sheet_request_email(
    third_party_email: str,
    third_party_company_name: str,
    contractor_name: str,
    upload_token: str,
    consultant_name: str
) -> bool:
    """
    Send quote sheet request email to third party with upload link
    """
    upload_link = f"{settings.frontend_url}/quote-sheet/upload?token={upload_token}"
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quote Sheet Request</title>
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
            .contractor-box {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
            }}
            .contractor-title {{
                font-size: 14px;
                color: #6b6b6b;
                margin-bottom: 8px;
            }}
            .contractor-name {{
                font-size: 18px;
                font-weight: 700;
                color: #FF6B00;
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
            .note-box {{
                background-color: #fff9f0;
                border-left: 3px solid #FF6B00;
                padding: 12px 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .note-box p {{
                margin: 0;
                color: #5d4037;
                font-size: 13px;
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
                <h2 class="greeting">Hello {third_party_company_name} Team,</h2>

                <p class="intro-text">
                    We hope this email finds you well. We are reaching out to request a quote sheet for one of our contractors.
                </p>

                <div class="contractor-box">
                    <div class="contractor-title">Contractor Name:</div>
                    <div class="contractor-name">{contractor_name}</div>
                </div>

                <p class="intro-text">
                    Please provide us with a detailed quote sheet including rates, terms, and any applicable fees.
                </p>

                <div class="cta-container">
                    <a href="{upload_link}" class="cta-button">Upload Quote Sheet</a>
                </div>

                <div class="note-box">
                    <p><strong>Note:</strong> You can upload the quote sheet using the link above, or alternatively, you can reply to this email with the quote sheet attached.</p>
                </div>

                <div class="divider"></div>

                <p class="intro-text">
                    If you have any questions or need additional information, please don't hesitate to contact {consultant_name}.
                </p>

                <p class="intro-text" style="margin-top: 16px;">
                    Thank you for your partnership and prompt attention to this request.
                </p>

                <p class="intro-text" style="margin-top: 16px; font-size: 14px;">
                    Best regards,<br>
                    <strong>{consultant_name}</strong><br>
                    {settings.company_name}
                </p>
            </div>

            <div class="footer">
                <p class="footer-text">This is an automated message from {settings.company_name}.</p>
                <p class="footer-text" style="margin-top: 15px; color: #999;">&copy; 2025 {settings.company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [third_party_email],
            "subject": f"Quote Sheet Request for {contractor_name}",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Quote sheet request sent to {third_party_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send quote sheet request: {str(e)}")
        return False


def send_proposal_email(
    client_email: str,
    client_company_name: str,
    proposal_link: str,
    consultant_name: str,
    project_name: str = None
) -> bool:
    """
    Send proposal email to client with preview/download link
    """
    logo_url = settings.logo_url

    subject_line = f"Proposal from {settings.company_name}"
    if project_name:
        subject_line += f" - {project_name}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Proposal from {settings.company_name}</title>
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
                background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header img {{
                max-width: 150px;
                height: auto;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                margin: 0;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #1a1a1a;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 30px;
                line-height: 1.8;
            }}
            .info-box {{
                background-color: #f7fafc;
                border-left: 4px solid #FF6B00;
                padding: 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .info-box p {{
                margin: 8px 0;
                font-size: 15px;
                color: #2d3748;
            }}
            .info-box strong {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .button-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .button {{
                display: inline-block;
                padding: 16px 40px;
                background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                box-shadow: 0 4px 12px rgba(255, 107, 0, 0.3);
                transition: all 0.3s ease;
            }}
            .footer {{
                background-color: #f7fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            .footer p {{
                color: #718096;
                font-size: 14px;
                margin: 5px 0;
            }}
            .footer a {{
                color: #FF6B00;
                text-decoration: none;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #e2e8f0, transparent);
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                {f'<img src="{logo_url}" alt="{settings.company_name} Logo">' if logo_url else ''}
                <h1>New Proposal</h1>
            </div>

            <div class="content">
                <p class="greeting">Dear {client_company_name} Team,</p>

                <p class="message">
                    Thank you for considering {settings.company_name} for your project needs. We are pleased to submit our proposal for your review.
                </p>

                {f'<div class="info-box"><p><strong>Project:</strong> {project_name}</p></div>' if project_name else ''}

                <p class="message">
                    Our proposal includes detailed information about our approach, timeline, deliverables, and pricing structure. We have carefully considered your requirements and believe our solution will meet your expectations.
                </p>

                <div class="button-container">
                    <a href="{proposal_link}" class="button">
                        📄 View Proposal
                    </a>
                </div>

                <div class="divider"></div>

                <p class="message" style="font-size: 14px; color: #718096;">
                    We are excited about the opportunity to work with {client_company_name} and look forward to discussing this proposal with you. If you have any questions or would like to schedule a meeting to review the details, please don't hesitate to reach out.
                </p>

                <p class="message" style="margin-top: 20px;">
                    Best regards,<br>
                    <strong>{consultant_name}</strong><br>
                    {settings.company_name}
                </p>
            </div>

            <div class="footer">
                <p><strong>{settings.company_name}</strong></p>
                <p>Email: <a href="mailto:{settings.from_email}">{settings.from_email}</a></p>
                <p style="margin-top: 15px; font-size: 12px; color: #a0aec0;">
                    This is an automated email. Please do not reply directly to this message.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": [client_email],
            "subject": subject_line,
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Proposal email sent to {client_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send proposal email: {str(e)}")
        return False


def send_work_order_email(
    contractor_email: str,
    contractor_name: str,
    work_order_number: str,
    work_order_id: str
) -> bool:
    """
    Send work order notification email to contractor with preview/download link
    """
    work_order_link = f"{settings.frontend_url}/work-order/{work_order_id}"
    logo_url = settings.logo_url

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Work Order Approved</title>
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
                background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header img {{
                max-width: 150px;
                height: auto;
                margin-bottom: 20px;
            }}
            .header h1 {{
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
                margin: 0;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #1a1a1a;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 30px;
                line-height: 1.8;
            }}
            .info-box {{
                background-color: #f7fafc;
                border-left: 4px solid #FF6B00;
                padding: 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .info-box p {{
                margin: 8px 0;
                font-size: 15px;
                color: #2d3748;
            }}
            .info-box strong {{
                color: #1a1a1a;
                font-weight: 600;
            }}
            .button-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .button {{
                display: inline-block;
                padding: 16px 40px;
                background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%);
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                box-shadow: 0 4px 12px rgba(255, 107, 0, 0.3);
                transition: all 0.3s ease;
            }}
            .button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(255, 107, 0, 0.4);
            }}
            .secondary-button {{
                display: inline-block;
                padding: 12px 30px;
                background: #ffffff;
                color: #FF6B00 !important;
                text-decoration: none;
                border: 2px solid #FF6B00;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                margin-left: 10px;
                transition: all 0.3s ease;
            }}
            .secondary-button:hover {{
                background: #FFF5EB;
            }}
            .footer {{
                background-color: #f7fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            .footer p {{
                color: #718096;
                font-size: 14px;
                margin: 5px 0;
            }}
            .footer a {{
                color: #FF6B00;
                text-decoration: none;
            }}
            .divider {{
                height: 1px;
                background: linear-gradient(to right, transparent, #e2e8f0, transparent);
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                {f'<img src="{logo_url}" alt="Aventus Resources Logo">' if logo_url else ''}
                <h1>Work Order Approved</h1>
            </div>

            <div class="content">
                <p class="greeting">Dear {contractor_name},</p>

                <p class="message">
                    Great news! Your work order has been reviewed and approved. You can now view and download
                    your official work order document.
                </p>

                <div class="info-box">
                    <p><strong>Work Order Number:</strong> {work_order_number}</p>
                    <p><strong>Status:</strong> <span style="color: #10b981; font-weight: 600;">Approved</span></p>
                </div>

                <p class="message">
                    Please review the work order carefully and ensure all details are correct. If you notice
                    any discrepancies, please contact us immediately.
                </p>

                <div class="button-container">
                    <a href="{work_order_link}" class="button">
                        📄 View Work Order
                    </a>
                </div>

                <div class="divider"></div>

                <p class="message" style="font-size: 14px; color: #718096;">
                    <strong>What's Next?</strong><br>
                    After reviewing your work order, you will receive your consultant contract for signature.
                    Once signed, your onboarding process will be complete.
                </p>
            </div>

            <div class="footer">
                <p><strong>Aventus Resources</strong></p>
                <p>Email: <a href="mailto:info@aventusresources.com">info@aventusresources.com</a></p>
                <p style="margin-top: 15px; font-size: 12px; color: #a0aec0;">
                    This is an automated email. Please do not reply directly to this message.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        params = {
            "from": settings.from_email,
            "to": contractor_email,
            "subject": f"Work Order Approved - {work_order_number}",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Work order email sent to {contractor_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send work order email: {str(e)}")
        return False


def send_third_party_contractor_request(
    third_party_email: str,
    third_party_company_name: str,
    email_subject: str,
    email_body: str,
    consultant_name: str,
    upload_url: str
) -> bool:
    """
    Send contractor quote/document request email to third party company with upload link
    Uses template from database for easy editing
    """
    try:
        # Fetch template from database
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT content FROM templates
                WHERE template_type = 'quote_sheet'
                AND name = 'Quote Sheet Request Email'
                AND is_active = true
                LIMIT 1
            """))

            template_row = result.fetchone()

            if not template_row:
                print("Quote Sheet Email template not found in database")
                return False

            html_template = template_row[0]

        # Convert plain text email body to HTML with line breaks
        email_body_html = email_body.replace('\n', '<br>')

        # Replace template placeholders
        html_content = html_template.replace('{{LOGO_URL}}', settings.logo_url)
        html_content = html_content.replace('{{EMAIL_SUBJECT}}', email_subject)
        html_content = html_content.replace('{{THIRD_PARTY_COMPANY_NAME}}', third_party_company_name)
        html_content = html_content.replace('{{EMAIL_BODY}}', email_body_html)
        html_content = html_content.replace('{{UPLOAD_URL}}', upload_url)
        html_content = html_content.replace('{{CONSULTANT_NAME}}', consultant_name)

        # Send email
        params = {
            "from": settings.from_email,
            "to": [third_party_email],
            "subject": email_subject,
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Third party request sent to {third_party_email}: {email}")
        return True
    except Exception as e:
        print(f"Failed to send third party request: {str(e)}")
        return False
