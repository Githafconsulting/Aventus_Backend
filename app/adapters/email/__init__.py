# Email adapter
from app.adapters.email.interface import (
    IEmailSender,
    EmailMessage,
    EmailResult,
    EmailAttachment,
)
from app.adapters.email.resend_adapter import LambdaEmailSender, MockEmailSender
from app.adapters.email.template_engine import (
    EmailTemplateEngine,
    get_email_template_engine,
    email_template_engine,
)

__all__ = [
    # Interface
    "IEmailSender",
    "EmailMessage",
    "EmailResult",
    "EmailAttachment",
    # Implementations
    "LambdaEmailSender",
    "MockEmailSender",
    # Template engine (kept for non-email uses)
    "EmailTemplateEngine",
    "get_email_template_engine",
    "email_template_engine",
]
