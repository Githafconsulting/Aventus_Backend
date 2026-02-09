"""
Email sender interface.

Defines the contract for email sending implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class EmailAttachment:
    """
    Email attachment data.

    Attributes:
        filename: Name of the file
        content: File content as bytes
        content_type: MIME type of the file
    """
    filename: str
    content: bytes
    content_type: str


@dataclass
class EmailMessage:
    """
    Email message data.

    Attributes:
        to: Recipient email address(es)
        subject: Email subject
        html: HTML content
        text: Plain text content (optional)
        from_email: Sender email (optional, uses default)
        from_name: Sender name (optional)
        reply_to: Reply-to address (optional)
        attachments: List of attachments (optional)
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
    """
    to: str | List[str]
    subject: str
    html: str
    text: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


@dataclass
class EmailResult:
    """
    Result of an email send operation.

    Attributes:
        success: Whether the email was sent successfully
        message_id: Provider's message ID (if successful)
        error: Error message (if failed)
    """
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class IEmailSender(ABC):
    """
    Abstract interface for email sending.

    Implementations can use different providers (Resend, SES, SMTP, etc.)
    while maintaining the same interface.

    Usage:
        sender = LambdaEmailSender()
        result = await sender.send(
            to="user@example.com",
            subject="Hello",
            html="<h1>Hello World</h1>",
        )
    """

    @abstractmethod
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
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            html: HTML content
            text: Plain text content (optional)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional)
            reply_to: Reply-to address (optional)
            attachments: List of attachments (optional)

        Returns:
            EmailResult with success status and message ID or error
        """
        pass

    @abstractmethod
    async def send_message(self, message: EmailMessage) -> EmailResult:
        """
        Send an email using an EmailMessage object.

        Args:
            message: EmailMessage with all email data

        Returns:
            EmailResult with success status
        """
        pass

    @abstractmethod
    async def send_bulk(
        self,
        messages: List[EmailMessage],
    ) -> List[EmailResult]:
        """
        Send multiple emails.

        Args:
            messages: List of EmailMessage objects

        Returns:
            List of EmailResult objects
        """
        pass
