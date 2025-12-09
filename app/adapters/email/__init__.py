# Email adapter
from app.adapters.email.interface import (
    IEmailSender,
    EmailMessage,
    EmailResult,
    EmailAttachment,
)
from app.adapters.email.resend_adapter import ResendEmailSender, MockEmailSender
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
    "ResendEmailSender",
    "MockEmailSender",
    # Template engine
    "EmailTemplateEngine",
    "get_email_template_engine",
    "email_template_engine",
]
