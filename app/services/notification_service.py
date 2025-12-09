"""
Notification Service.

Application service for sending notifications (emails, etc.).
Abstracts email sending behind a clean interface.
"""
from typing import Optional
from datetime import datetime

from app.adapters.email.interface import IEmailSender
from app.adapters.email.template_engine import EmailTemplateEngine
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Application service for sending notifications.

    Provides methods for each type of notification email,
    using templates for consistent formatting.
    """

    def __init__(
        self,
        email_sender: IEmailSender,
        template_engine: EmailTemplateEngine,
    ):
        """
        Initialize notification service.

        Args:
            email_sender: Email sender implementation
            template_engine: Template engine for rendering emails
        """
        self.email = email_sender
        self.templates = template_engine

    async def send_document_upload_email(
        self,
        contractor_email: str,
        contractor_name: str,
        upload_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send document upload request email.

        Args:
            contractor_email: Recipient email
            contractor_name: Contractor's name
            upload_token: Document upload token
            expiry_date: Token expiry date

        Returns:
            True if sent successfully
        """
        upload_link = f"{settings.frontend_url}/documents/upload/{upload_token}"

        html = self.templates.render(
            "document_upload",
            contractor_name=contractor_name,
            upload_link=upload_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=contractor_email,
            subject="Document Upload Required - Action Needed",
            html=html,
        )

        logger.info(
            "Document upload email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    async def send_contract_signing_email(
        self,
        contractor_email: str,
        contractor_name: str,
        contract_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send contract signing invitation email.

        Args:
            contractor_email: Recipient email
            contractor_name: Contractor's name
            contract_token: Contract signing token
            expiry_date: Token expiry date

        Returns:
            True if sent successfully
        """
        contract_link = f"{settings.contract_signing_url}?token={contract_token}"

        html = self.templates.render(
            "contract_signing",
            contractor_name=contractor_name,
            contract_link=contract_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=contractor_email,
            subject="Your Employment Contract - Action Required",
            html=html,
        )

        logger.info(
            "Contract signing email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    async def send_activation_email(
        self,
        contractor_email: str,
        contractor_name: str,
        temporary_password: str,
    ) -> bool:
        """
        Send account activation email with credentials.

        Args:
            contractor_email: Recipient email
            contractor_name: Contractor's name
            temporary_password: Generated temporary password

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "activation",
            contractor_name=contractor_name,
            contractor_email=contractor_email,
            temporary_password=temporary_password,
            login_link=settings.frontend_url,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Welcome to {settings.company_name} - Your Account is Ready",
            html=html,
        )

        logger.info(
            "Activation email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    async def send_documents_uploaded_notification(
        self,
        admin_email: str,
        contractor_name: str,
        contractor_id: int,
    ) -> bool:
        """
        Notify admin that a contractor has uploaded documents.

        Args:
            admin_email: Admin email address
            contractor_name: Contractor's name
            contractor_id: Contractor ID for review link

        Returns:
            True if sent successfully
        """
        review_link = f"{settings.frontend_url}/admin/contractors/{contractor_id}"

        html = self.templates.render(
            "documents_uploaded",
            contractor_name=contractor_name,
            review_link=review_link,
        )

        result = await self.email.send(
            to=admin_email,
            subject=f"Documents Uploaded - {contractor_name}",
            html=html,
        )

        return result.success

    async def send_cohf_signature_request(
        self,
        third_party_email: str,
        third_party_name: str,
        contractor_name: str,
        cohf_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send COHF signature request to third party.

        Args:
            third_party_email: Third party email
            third_party_name: Third party name
            contractor_name: Contractor's name
            cohf_token: COHF signing token
            expiry_date: Token expiry

        Returns:
            True if sent successfully
        """
        signing_link = f"{settings.frontend_url}/cohf/sign/{cohf_token}"

        html = self.templates.render(
            "cohf",
            third_party_name=third_party_name,
            contractor_name=contractor_name,
            signing_link=signing_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=third_party_email,
            subject=f"COHF Signature Required - {contractor_name}",
            html=html,
        )

        logger.info(
            "COHF signature email sent",
            extra={
                "to": third_party_email,
                "contractor": contractor_name,
                "success": result.success,
            }
        )

        return result.success

    async def send_quote_sheet_request(
        self,
        third_party_email: str,
        third_party_name: str,
        contractor_name: str,
        quote_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send quote sheet request to third party.

        Args:
            third_party_email: Third party email
            third_party_name: Third party name
            contractor_name: Contractor's name
            quote_token: Quote sheet token
            expiry_date: Token expiry

        Returns:
            True if sent successfully
        """
        quote_link = f"{settings.frontend_url}/quote-sheet/{quote_token}"

        html = self.templates.render(
            "quote_sheet_request",
            third_party_name=third_party_name,
            contractor_name=contractor_name,
            quote_link=quote_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=third_party_email,
            subject=f"Quote Sheet Required - {contractor_name}",
            html=html,
        )

        return result.success

    async def send_work_order_email(
        self,
        client_email: str,
        client_name: str,
        contractor_name: str,
        work_order_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send work order signing request to client.

        Args:
            client_email: Client email
            client_name: Client name
            contractor_name: Contractor's name
            work_order_token: Work order signing token
            expiry_date: Token expiry

        Returns:
            True if sent successfully
        """
        signing_link = f"{settings.frontend_url}/work-order/sign/{work_order_token}"

        html = self.templates.render(
            "work_order_client",
            client_name=client_name,
            contractor_name=contractor_name,
            signing_link=signing_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=client_email,
            subject=f"Work Order Signature Required - {contractor_name}",
            html=html,
        )

        logger.info(
            "Work order email sent",
            extra={
                "to": client_email,
                "contractor": contractor_name,
                "success": result.success,
            }
        )

        return result.success

    async def send_review_notification(
        self,
        admin_email: str,
        contractor_name: str,
        contractor_id: int,
        notification_type: str,
    ) -> bool:
        """
        Send review notification to admin.

        Args:
            admin_email: Admin email
            contractor_name: Contractor's name
            contractor_id: Contractor ID
            notification_type: Type of review needed

        Returns:
            True if sent successfully
        """
        review_link = f"{settings.frontend_url}/admin/contractors/{contractor_id}"

        html = self.templates.render(
            "review_notification",
            contractor_name=contractor_name,
            notification_type=notification_type,
            review_link=review_link,
        )

        result = await self.email.send(
            to=admin_email,
            subject=f"Review Required: {notification_type} - {contractor_name}",
            html=html,
        )

        return result.success

    async def send_password_reset_email(
        self,
        email: str,
        name: str,
        reset_token: str,
        expiry_date: datetime,
    ) -> bool:
        """
        Send password reset email.

        Args:
            email: User email
            name: User name
            reset_token: Password reset token
            expiry_date: Token expiry

        Returns:
            True if sent successfully
        """
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

        html = self.templates.render(
            "password_reset",
            name=name,
            reset_link=reset_link,
            expiry_date=expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        )

        result = await self.email.send(
            to=email,
            subject=f"Password Reset Request - {settings.company_name}",
            html=html,
        )

        return result.success
