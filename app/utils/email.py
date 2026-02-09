"""
Email sending utilities.

All emails are sent via AWS Lambda (which uses SES templates),
except send_quote_sheet_pdf_email which sends directly via SES with a PDF attachment.
"""
import json
import boto3
from datetime import datetime
from typing import Optional

from app.config import settings

# Module-level cached boto3 clients (created once, reused)
_lambda_client = None
_ses_client = None


def _get_lambda_client():
    """Get or create cached Lambda client."""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client(
            "lambda",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _lambda_client


def _get_ses_client():
    """Get or create cached SES client."""
    global _ses_client
    if _ses_client is None:
        _ses_client = boto3.client(
            "ses",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _ses_client


def _invoke_email_lambda(email_type: str, recipient: str, data: dict, cc: Optional[str] = None) -> bool:
    """
    Invoke the AWS Lambda function to send an email.

    Args:
        email_type: The template type (e.g. "activation", "contract_signing")
        recipient: Recipient email address
        data: Template data dict
        cc: Optional CC email address

    Returns:
        True if invocation succeeded, False otherwise
    """
    if not settings.email_lambda_function_name:
        print("[EMAIL] ERROR: EMAIL_LAMBDA_FUNCTION_NAME not set")
        return False

    try:
        payload = {
            "email_type": email_type,
            "recipient": recipient,
            "data": data,
        }
        if cc:
            payload["cc"] = cc

        client = _get_lambda_client()
        client.invoke(
            FunctionName=settings.email_lambda_function_name,
            InvocationType="Event",  # Async fire-and-forget
            Payload=json.dumps(payload).encode("utf-8"),
        )
        print(f"[EMAIL] Lambda invoked: {email_type} -> {recipient}")
        return True
    except Exception as e:
        print(f"[EMAIL] ERROR invoking Lambda ({email_type}): {e}")
        return False


# =============================================================================
# Contract & Onboarding Emails
# =============================================================================

def send_contract_email(
    contractor_email: str,
    contractor_name: str,
    contract_token: str,
    expiry_date: datetime
) -> bool:
    """Send contract signing email to contractor."""
    return _invoke_email_lambda("contract_signing", contractor_email, {
        "contractor_name": contractor_name,
        "contract_link": f"{settings.contract_signing_url}?token={contract_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    })


def send_activation_email(
    contractor_email: str,
    contractor_name: str,
    temporary_password: str
) -> bool:
    """Send account activation email with login credentials."""
    return _invoke_email_lambda("activation", contractor_email, {
        "contractor_name": contractor_name,
        "contractor_email": contractor_email,
        "temporary_password": temporary_password,
        "login_link": settings.frontend_url,
    })


def send_signed_contract_email(
    contractor_email: str,
    contractor_name: str,
    pdf_url: str
) -> bool:
    """Send signed contract copy to contractor."""
    return _invoke_email_lambda("signed_contract", contractor_email, {
        "contractor_name": contractor_name,
        "pdf_url": pdf_url,
        "login_link": settings.frontend_url,
    })


def send_document_upload_email(
    contractor_email: str,
    contractor_name: str,
    upload_token: str,
    expiry_date: datetime
) -> bool:
    """Send document upload request email."""
    return _invoke_email_lambda("document_upload", contractor_email, {
        "contractor_name": contractor_name,
        "upload_link": f"{settings.frontend_url}/documents/upload/{upload_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    })


def send_documents_uploaded_notification(
    admin_email: str,
    contractor_name: str,
    contractor_id: int
) -> bool:
    """Notify admin that contractor has uploaded documents."""
    return _invoke_email_lambda("documents_uploaded", admin_email, {
        "contractor_name": contractor_name,
        "review_link": f"{settings.frontend_url}/admin/contractors/{contractor_id}",
    })


# =============================================================================
# Password & Authentication
# =============================================================================

def send_password_reset_email(
    email: str,
    name: str,
    reset_token: str,
    expiry_date: datetime
) -> bool:
    """Send password reset email."""
    return _invoke_email_lambda("password_reset", email, {
        "name": name,
        "reset_link": f"{settings.password_reset_url}?token={reset_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    })


# =============================================================================
# Review & Notification
# =============================================================================

def send_review_notification(
    admin_email: str,
    contractor_name: str,
    contractor_id: int,
    notification_type: str = "Review"
) -> bool:
    """Send review notification to admin."""
    return _invoke_email_lambda("review_notification", admin_email, {
        "contractor_name": contractor_name,
        "notification_type": notification_type,
        "review_link": f"{settings.frontend_url}/admin/contractors/{contractor_id}",
    })


# =============================================================================
# Quote Sheet & COHF
# =============================================================================

def send_quote_sheet_request_email(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    quote_token: str,
    expiry_date: datetime,
    cc_email: Optional[str] = None,
    custom_subject: Optional[str] = None,
    custom_message: Optional[str] = None
) -> bool:
    """Send quote sheet request to third party."""
    data = {
        "third_party_name": third_party_name,
        "contractor_name": contractor_name,
        "quote_link": f"{settings.frontend_url}/quote-sheet/{quote_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if custom_message:
        data["custom_message"] = custom_message
    if custom_subject:
        data["subject"] = custom_subject
    return _invoke_email_lambda("quote_sheet_request", third_party_email, data, cc=cc_email)


def send_cohf_email(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    cohf_token: str,
    expiry_date: datetime,
    custom_message: Optional[str] = None
) -> bool:
    """Send COHF signature request to third party."""
    data = {
        "third_party_name": third_party_name,
        "contractor_name": contractor_name,
        "signing_link": f"{settings.frontend_url}/cohf/sign/{cohf_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if custom_message:
        data["custom_message"] = custom_message
    return _invoke_email_lambda("cohf", third_party_email, data)


# =============================================================================
# Work Orders
# =============================================================================

def send_work_order_email(
    recipient_email: str,
    recipient_name: str,
    contractor_name: str,
    work_order_token: str,
    expiry_date: datetime,
    client_name: Optional[str] = None
) -> bool:
    """Send work order notification."""
    data = {
        "recipient_name": recipient_name,
        "contractor_name": contractor_name,
        "work_order_link": f"{settings.frontend_url}/work-order/{work_order_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if client_name:
        data["client_name"] = client_name
    return _invoke_email_lambda("work_order", recipient_email, data)


def send_work_order_to_client(
    client_email: str,
    client_name: str,
    contractor_name: str,
    work_order_token: str,
    expiry_date: datetime
) -> bool:
    """Send work order signing request to client."""
    return _invoke_email_lambda("work_order_client", client_email, {
        "client_name": client_name,
        "contractor_name": contractor_name,
        "signing_link": f"{settings.frontend_url}/sign-work-order/{work_order_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    })


# =============================================================================
# Proposals
# =============================================================================

def send_proposal_email(
    recipient_email: str,
    recipient_name: str,
    proposal_title: str,
    proposal_token: str,
    expiry_date: datetime,
    contractor_name: Optional[str] = None
) -> bool:
    """Send proposal email."""
    data = {
        "recipient_name": recipient_name,
        "proposal_title": proposal_title,
        "proposal_link": f"{settings.frontend_url}/proposal/{proposal_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if contractor_name:
        data["contractor_name"] = contractor_name
    return _invoke_email_lambda("proposal", recipient_email, data)


# =============================================================================
# Third Party
# =============================================================================

def send_third_party_contractor_request(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    action_token: str,
    expiry_date: datetime,
    role: Optional[str] = None,
    client_name: Optional[str] = None,
    custom_message: Optional[str] = None
) -> bool:
    """Send contractor request to third party."""
    data = {
        "third_party_name": third_party_name,
        "contractor_name": contractor_name,
        "action_link": f"{settings.frontend_url}/third-party/request/{action_token}",
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if role:
        data["role"] = role
    if client_name:
        data["client_name"] = client_name
    if custom_message:
        data["custom_message"] = custom_message
    return _invoke_email_lambda("third_party_request", third_party_email, data)


# =============================================================================
# Timesheets
# =============================================================================

def send_timesheet_to_manager(
    manager_email: str,
    manager_name: str,
    contractor_name: str,
    timesheet_month: str,
    review_link: str,
    total_days: float = 0,
    work_days: int = 0,
    sick_days: int = 0,
    vacation_days: int = 0,
    pdf_content: Optional[bytes] = None,
    client_name: Optional[str] = None
) -> bool:
    """Send timesheet notification to manager for approval."""
    data = {
        "manager_name": manager_name,
        "contractor_name": contractor_name,
        "timesheet_link": review_link,
        "period": timesheet_month,
        "total_days": total_days,
        "work_days": work_days,
        "sick_days": sick_days,
        "vacation_days": vacation_days,
    }
    if client_name:
        data["client_name"] = client_name
    return _invoke_email_lambda("timesheet", manager_email, data)


def send_uploaded_timesheet_to_manager(
    manager_email: str,
    manager_name: str,
    contractor_name: str,
    review_link: str,
    filename: Optional[str] = None,
    period: Optional[str] = None,
    client_name: Optional[str] = None
) -> bool:
    """Send notification when timesheet document is uploaded."""
    data = {
        "manager_name": manager_name,
        "contractor_name": contractor_name,
        "review_link": review_link,
    }
    if filename:
        data["filename"] = filename
    if period:
        data["period"] = period
    if client_name:
        data["client_name"] = client_name
    return _invoke_email_lambda("timesheet_uploaded", manager_email, data)


# =============================================================================
# Quote Sheet (Saudi Route)
# =============================================================================

def send_quote_sheet_request(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    upload_url: str,
    expiry_date: datetime,
    email_subject: Optional[str] = None,
    email_cc: Optional[str] = None
) -> bool:
    """Send quote sheet request to third party for Saudi route."""
    data = {
        "third_party_name": third_party_name,
        "contractor_name": contractor_name,
        "quote_link": upload_url,
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if email_subject:
        data["subject"] = email_subject
    return _invoke_email_lambda("quote_sheet_request", third_party_email, data, cc=email_cc)


def send_quote_sheet_form_link(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    form_link: str,
    expiry_date: datetime,
    role: Optional[str] = None,
    location: Optional[str] = None,
    client_name: Optional[str] = None
) -> bool:
    """Send quote sheet form link to third party to fill and submit."""
    data = {
        "third_party_name": third_party_name,
        "contractor_name": contractor_name,
        "form_link": form_link,
        "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    }
    if role:
        data["role"] = role
    if location:
        data["location"] = location
    if client_name:
        data["client_name"] = client_name
    return _invoke_email_lambda("quote_sheet_form_link", third_party_email, data)


def send_quote_sheet_pdf_email(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    pdf_content: bytes,
    pdf_filename: str,
    company_name: str = "Aventus"
) -> bool:
    """
    Send quote sheet PDF to third party via email.

    This is the special case: no Lambda template exists for this email.
    Sends directly via SES with a MIME attachment.
    """
    import base64
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"Cost Estimation Sheet - {contractor_name}"
        msg["From"] = settings.from_email
        msg["To"] = third_party_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #9B1B1B;">Cost Estimation Sheet</h2>
                <p>Dear {third_party_name or 'Team'},</p>
                <p>Please find attached the Cost Estimation Sheet for <strong>{contractor_name}</strong>.</p>
                <p>This document contains the detailed cost breakdown for your review.</p>
                <p>If you have any questions or require clarification, please don't hesitate to contact us.</p>
                <br/>
                <p>Best regards,</p>
                <p><strong>{company_name} Team</strong></p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"/>
                <p style="font-size: 12px; color: #666;">This is an automated email. Please do not reply directly to this message.</p>
            </div>
        </body>
        </html>
        """

        body_part = MIMEText(html, "html")
        msg.attach(body_part)

        att = MIMEApplication(pdf_content)
        att.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(att)

        client = _get_ses_client()
        client.send_raw_email(
            Source=settings.from_email,
            Destinations=[third_party_email],
            RawMessage={"Data": msg.as_string()},
        )
        print(f"[EMAIL] SES raw email sent: quote_sheet_pdf -> {third_party_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] ERROR sending quote sheet PDF via SES: {e}")
        return False
