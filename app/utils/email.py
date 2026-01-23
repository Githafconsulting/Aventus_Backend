"""
Email sending utilities.

All email functions use Jinja2 templates from app/templates/email/.
"""
import resend
from pathlib import Path
from datetime import datetime
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings

# Initialize Jinja2 template engine
_template_dir = Path(__file__).parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _render_template(template_name: str, **context) -> str:
    """Render an email template with context."""
    template = _env.get_template(f"email/{template_name}.html")
    default_context = {
        "company_name": settings.company_name,
        "logo_url": settings.logo_url,
        "frontend_url": settings.frontend_url,
        "support_email": getattr(settings, 'support_email', 'support@aventushr.com'),
        "current_year": datetime.now().year,
    }
    default_context.update(context)
    return template.render(**default_context)


def _send_email(to: str, subject: str, html: str) -> bool:
    """Send email via Resend."""
    import os
    from dotenv import load_dotenv

    # Force reload environment variables
    load_dotenv(override=True)

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")

    if not api_key:
        print("[EMAIL] ERROR: RESEND_API_KEY not set")
        return False

    try:
        resend.api_key = api_key

        params = {
            "from": from_email,
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "html": html,
        }

        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"[EMAIL] ERROR: {str(e)}")
        return False


def _send_email_with_attachment(to: str, subject: str, html: str, attachment_content: bytes, attachment_filename: str) -> bool:
    """Send email via Resend with PDF attachment."""
    import os
    import base64
    from dotenv import load_dotenv

    # Force reload environment variables
    load_dotenv(override=True)

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")

    if not api_key:
        print("[EMAIL] ERROR: RESEND_API_KEY not set")
        return False

    try:
        resend.api_key = api_key

        params = {
            "from": from_email,
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "html": html,
            "attachments": [
                {
                    "filename": attachment_filename,
                    "content": base64.b64encode(attachment_content).decode('utf-8'),
                }
            ]
        }

        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"[EMAIL] ERROR sending with attachment: {str(e)}")
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
    html = _render_template(
        "contract_signing",
        contractor_name=contractor_name,
        contract_link=f"{settings.contract_signing_url}?token={contract_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    )
    return _send_email(contractor_email, "Your Employment Contract - Action Required", html)


def send_activation_email(
    contractor_email: str,
    contractor_name: str,
    temporary_password: str
) -> bool:
    """Send account activation email with login credentials."""
    html = _render_template(
        "activation",
        contractor_name=contractor_name,
        contractor_email=contractor_email,
        temporary_password=temporary_password,
        login_link=settings.frontend_url,
    )
    return _send_email(contractor_email, f"Welcome to {settings.company_name} - Your Account is Ready", html)


def send_document_upload_email(
    contractor_email: str,
    contractor_name: str,
    upload_token: str,
    expiry_date: datetime
) -> bool:
    """Send document upload request email."""
    html = _render_template(
        "document_upload",
        contractor_name=contractor_name,
        upload_link=f"{settings.frontend_url}/documents/upload/{upload_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    )
    return _send_email(contractor_email, "Document Upload Required - Action Needed", html)


def send_documents_uploaded_notification(
    admin_email: str,
    contractor_name: str,
    contractor_id: int
) -> bool:
    """Notify admin that contractor has uploaded documents."""
    html = _render_template(
        "documents_uploaded",
        contractor_name=contractor_name,
        review_link=f"{settings.frontend_url}/admin/contractors/{contractor_id}",
    )
    return _send_email(admin_email, f"Documents Uploaded - {contractor_name}", html)


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
    html = _render_template(
        "password_reset",
        name=name,
        reset_link=f"{settings.password_reset_url}?token={reset_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    )
    return _send_email(email, f"Password Reset Request - {settings.company_name}", html)


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
    html = _render_template(
        "review_notification",
        contractor_name=contractor_name,
        notification_type=notification_type,
        review_link=f"{settings.frontend_url}/admin/contractors/{contractor_id}",
    )
    return _send_email(admin_email, f"Review Required: {notification_type} - {contractor_name}", html)


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
    html = _render_template(
        "quote_sheet_request",
        third_party_name=third_party_name,
        contractor_name=contractor_name,
        quote_link=f"{settings.frontend_url}/quote-sheet/{quote_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        custom_message=custom_message,
    )
    subject = custom_subject or f"Quote Sheet Required - {contractor_name}"
    return _send_email(third_party_email, subject, html)


def send_cohf_email(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    cohf_token: str,
    expiry_date: datetime,
    custom_message: Optional[str] = None
) -> bool:
    """Send COHF signature request to third party."""
    html = _render_template(
        "cohf",
        third_party_name=third_party_name,
        contractor_name=contractor_name,
        signing_link=f"{settings.frontend_url}/cohf/sign/{cohf_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        custom_message=custom_message,
    )
    return _send_email(third_party_email, f"COHF Signature Required - {contractor_name}", html)


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
    html = _render_template(
        "work_order",
        recipient_name=recipient_name,
        contractor_name=contractor_name,
        work_order_link=f"{settings.frontend_url}/work-order/{work_order_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        client_name=client_name,
    )
    return _send_email(recipient_email, f"Work Order - {contractor_name}", html)


def send_work_order_to_client(
    client_email: str,
    client_name: str,
    contractor_name: str,
    work_order_token: str,
    expiry_date: datetime
) -> bool:
    """Send work order signing request to client."""
    html = _render_template(
        "work_order_client",
        client_name=client_name,
        contractor_name=contractor_name,
        signing_link=f"{settings.frontend_url}/sign-work-order/{work_order_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    )
    return _send_email(client_email, f"Work Order Signature Required - {contractor_name}", html)


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
    html = _render_template(
        "proposal",
        recipient_name=recipient_name,
        proposal_title=proposal_title,
        proposal_link=f"{settings.frontend_url}/proposal/{proposal_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        contractor_name=contractor_name,
    )
    return _send_email(recipient_email, f"Proposal: {proposal_title}", html)


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
    html = _render_template(
        "third_party_request",
        third_party_name=third_party_name,
        contractor_name=contractor_name,
        action_link=f"{settings.frontend_url}/third-party/request/{action_token}",
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        role=role,
        client_name=client_name,
        custom_message=custom_message,
    )
    return _send_email(third_party_email, f"New Contractor Request - {contractor_name}", html)


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
    html = _render_template(
        "timesheet",
        manager_name=manager_name,
        contractor_name=contractor_name,
        timesheet_link=review_link,
        period=timesheet_month,
        total_days=total_days,
        work_days=work_days,
        sick_days=sick_days,
        vacation_days=vacation_days,
        client_name=client_name,
    )
    return _send_email(manager_email, f"Timesheet Submitted - {contractor_name} ({timesheet_month})", html)


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
    html = _render_template(
        "timesheet_uploaded",
        manager_name=manager_name,
        contractor_name=contractor_name,
        review_link=review_link,
        filename=filename,
        period=period,
        client_name=client_name,
    )
    return _send_email(manager_email, f"Timesheet Uploaded - {contractor_name}", html)


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
    html = _render_template(
        "quote_sheet_request",
        third_party_name=third_party_name,
        contractor_name=contractor_name,
        quote_link=upload_url,
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
    )
    subject = email_subject or f"Quote Sheet Request - {contractor_name}"

    if email_cc:
        return _send_email_with_cc(third_party_email, email_cc, subject, html)
    return _send_email(third_party_email, subject, html)


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
    html = _render_template(
        "quote_sheet_form_link",
        third_party_name=third_party_name,
        contractor_name=contractor_name,
        form_link=form_link,
        expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        role=role,
        location=location,
        client_name=client_name,
    )
    subject = f"Cost Estimation Sheet - Action Required - {contractor_name}"
    return _send_email(third_party_email, subject, html)


def send_quote_sheet_pdf_email(
    third_party_email: str,
    third_party_name: str,
    contractor_name: str,
    pdf_content: bytes,
    pdf_filename: str,
    company_name: str = "Aventus"
) -> bool:
    """Send quote sheet PDF to third party via email."""
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
    subject = f"Cost Estimation Sheet - {contractor_name}"
    return _send_email_with_attachment(third_party_email, subject, html, pdf_content, pdf_filename)


def _send_email_with_cc(to: str, cc: str, subject: str, html: str) -> bool:
    """Send email via Resend with CC."""
    import os
    from dotenv import load_dotenv

    load_dotenv(override=True)

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")

    if not api_key:
        print("[EMAIL] ERROR: RESEND_API_KEY not set")
        return False

    resend.api_key = api_key

    try:
        resend.Emails.send({
            "from": from_email or "Aventus HR <noreply@aventushr.com>",
            "to": to,
            "cc": cc,
            "subject": subject,
            "html": html,
        })
        print(f"[EMAIL] Sent to {to} (CC: {cc}): {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL] ERROR sending to {to}: {e}")
        return False
