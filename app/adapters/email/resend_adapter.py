"""
Lambda/SES email adapter.

Stub implementation for DI compatibility. Actual email sending
is handled by _invoke_email_lambda() in app.utils.email.
"""
from typing import List, Optional
from app.adapters.email.interface import (
    IEmailSender,
    EmailMessage,
    EmailResult,
    EmailAttachment,
)
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class LambdaEmailSender(IEmailSender):
    """
    Stub email sender for DI compatibility.

    Email sending is now done via _invoke_email_lambda() directly.
    This class exists so that services can still accept an IEmailSender
    without breaking, but it should not be used for actual sending.
    """

    async def send(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> EmailResult:
        """Stub - email sending is handled via Lambda invocation."""
        logger.warning("LambdaEmailSender.send() called - use _invoke_email_lambda() instead")
        return EmailResult(success=False, error="Use _invoke_email_lambda() directly")

    async def send_message(self, message: EmailMessage) -> EmailResult:
        """Stub - email sending is handled via Lambda invocation."""
        logger.warning("LambdaEmailSender.send_message() called - use _invoke_email_lambda() instead")
        return EmailResult(success=False, error="Use _invoke_email_lambda() directly")

    async def send_bulk(
        self,
        messages: List[EmailMessage],
    ) -> List[EmailResult]:
        """Stub - email sending is handled via Lambda invocation."""
        return [EmailResult(success=False, error="Use _invoke_email_lambda() directly") for _ in messages]


class MockEmailSender(IEmailSender):
    """
    Mock email sender for testing.

    Stores sent emails in memory for verification.
    """

    def __init__(self):
        self.sent_emails: List[EmailMessage] = []

    async def send(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
    ) -> EmailResult:
        """Store email in memory instead of sending."""
        message = EmailMessage(
            to=to,
            subject=subject,
            html=html,
            text=text,
            from_email=from_email,
            from_name=from_name,
            reply_to=reply_to,
            attachments=attachments,
        )
        self.sent_emails.append(message)

        return EmailResult(
            success=True,
            message_id=f"mock-{len(self.sent_emails)}",
        )

    async def send_message(self, message: EmailMessage) -> EmailResult:
        """Store email message in memory."""
        self.sent_emails.append(message)
        return EmailResult(
            success=True,
            message_id=f"mock-{len(self.sent_emails)}",
        )

    async def send_bulk(
        self,
        messages: List[EmailMessage],
    ) -> List[EmailResult]:
        """Store all emails in memory."""
        results = []
        for message in messages:
            result = await self.send_message(message)
            results.append(result)
        return results

    def clear(self):
        """Clear sent emails."""
        self.sent_emails.clear()

    def get_last_email(self) -> Optional[EmailMessage]:
        """Get the last sent email."""
        return self.sent_emails[-1] if self.sent_emails else None

    def find_by_recipient(self, email: str) -> List[EmailMessage]:
        """Find emails sent to a specific recipient."""
        results = []
        for msg in self.sent_emails:
            recipients = [msg.to] if isinstance(msg.to, str) else msg.to
            if email in recipients:
                results.append(msg)
        return results
