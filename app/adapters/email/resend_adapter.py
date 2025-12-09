"""
Resend email adapter.

Implementation of email sending using Resend API.
"""
import resend
from typing import List, Optional
from app.adapters.email.interface import (
    IEmailSender,
    EmailMessage,
    EmailResult,
    EmailAttachment,
)
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class ResendEmailSender(IEmailSender):
    """
    Resend API email sender implementation.

    Uses the Resend SDK to send emails.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Resend email sender.

        Args:
            api_key: Resend API key (optional, uses settings if not provided)
        """
        self.api_key = api_key or settings.resend_api_key
        resend.api_key = self.api_key
        self.default_from_email = settings.email_from_address
        self.default_from_name = settings.email_from_name

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
        """Send an email using Resend."""
        try:
            # Format from address
            sender_email = from_email or self.default_from_email
            sender_name = from_name or self.default_from_name
            from_address = f"{sender_name} <{sender_email}>"

            # Prepare params
            params = {
                "from": from_address,
                "to": [to] if isinstance(to, str) else to,
                "subject": subject,
                "html": html,
            }

            if text:
                params["text"] = text

            if reply_to:
                params["reply_to"] = reply_to

            if attachments:
                params["attachments"] = [
                    {
                        "filename": att.filename,
                        "content": att.content,
                        "type": att.content_type,
                    }
                    for att in attachments
                ]

            # Send email
            response = resend.Emails.send(params)

            logger.info(
                "Email sent successfully",
                extra={
                    "to": to,
                    "subject": subject,
                    "message_id": response.get("id"),
                }
            )

            return EmailResult(
                success=True,
                message_id=response.get("id"),
            )

        except Exception as e:
            logger.error(
                "Failed to send email",
                extra={
                    "to": to,
                    "subject": subject,
                    "error": str(e),
                }
            )
            return EmailResult(
                success=False,
                error=str(e),
            )

    async def send_message(self, message: EmailMessage) -> EmailResult:
        """Send an email using EmailMessage object."""
        return await self.send(
            to=message.to,
            subject=message.subject,
            html=message.html,
            text=message.text,
            from_email=message.from_email,
            from_name=message.from_name,
            reply_to=message.reply_to,
            attachments=message.attachments,
        )

    async def send_bulk(
        self,
        messages: List[EmailMessage],
    ) -> List[EmailResult]:
        """Send multiple emails."""
        results = []
        for message in messages:
            result = await self.send_message(message)
            results.append(result)
        return results


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
