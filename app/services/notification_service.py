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

    # ============ Offboarding Notifications ============

    async def send_offboarding_initiated_email(
        self,
        contractor_email: str,
        contractor_name: str,
        reason: str,
        notice_start_date: str,
        last_working_date: str,
        notice_period_days: int,
    ) -> bool:
        """
        Send offboarding initiated notification to contractor.

        Args:
            contractor_email: Recipient email
            contractor_name: Contractor's name
            reason: Offboarding reason
            notice_start_date: Notice period start
            last_working_date: Last working date
            notice_period_days: Notice period duration

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "offboarding_initiated",
            contractor_name=contractor_name,
            reason=reason,
            notice_start_date=notice_start_date,
            last_working_date=last_working_date,
            notice_period_days=notice_period_days,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Offboarding Notice - {settings.company_name}",
            html=html,
        )

        logger.info(
            "Offboarding initiated email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    async def send_offboarding_settlement_email(
        self,
        contractor_email: str,
        contractor_name: str,
        currency: str,
        total_settlement: str,
        pro_rata_salary: str = None,
        days_worked: int = 0,
        unused_leave_payout: str = None,
        leave_days_remaining: str = None,
        gratuity_eosb: str = None,
        pending_reimbursements: str = None,
        deductions: str = None,
    ) -> bool:
        """
        Send settlement details to contractor.

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "offboarding_settlement",
            contractor_name=contractor_name,
            currency=currency,
            total_settlement=total_settlement,
            pro_rata_salary=pro_rata_salary,
            days_worked=days_worked,
            unused_leave_payout=unused_leave_payout,
            leave_days_remaining=leave_days_remaining,
            gratuity_eosb=gratuity_eosb,
            pending_reimbursements=pending_reimbursements,
            deductions=deductions,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Final Settlement Details - {settings.company_name}",
            html=html,
        )

        return result.success

    async def send_offboarding_completed_email(
        self,
        contractor_email: str,
        contractor_name: str,
        effective_date: str,
        currency: str,
        total_settlement: str,
        termination_letter_url: str = None,
        experience_letter_url: str = None,
        clearance_certificate_url: str = None,
        final_payslip_url: str = None,
    ) -> bool:
        """
        Send offboarding completed notification with document links.

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "offboarding_completed",
            contractor_name=contractor_name,
            effective_date=effective_date,
            currency=currency,
            total_settlement=total_settlement,
            termination_letter_url=termination_letter_url,
            experience_letter_url=experience_letter_url,
            clearance_certificate_url=clearance_certificate_url,
            final_payslip_url=final_payslip_url,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Offboarding Complete - {settings.company_name}",
            html=html,
        )

        logger.info(
            "Offboarding completed email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    # ============ Extension Notifications ============

    async def send_extension_request_email(
        self,
        admin_email: str,
        contractor_name: str,
        original_end_date: str,
        new_end_date: str,
        extension_months: int,
        requested_by: str,
        review_link: str,
        currency: str = None,
        new_rate: str = None,
        rate_change_reason: str = None,
    ) -> bool:
        """
        Send extension request notification to admin.

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "extension_request",
            contractor_name=contractor_name,
            original_end_date=original_end_date,
            new_end_date=new_end_date,
            extension_months=extension_months,
            requested_by=requested_by,
            review_link=review_link,
            currency=currency,
            new_rate=new_rate,
            rate_change_reason=rate_change_reason,
        )

        result = await self.email.send(
            to=admin_email,
            subject=f"Extension Request - {contractor_name}",
            html=html,
        )

        return result.success

    async def send_extension_approved_email(
        self,
        contractor_email: str,
        contractor_name: str,
        original_end_date: str,
        new_end_date: str,
        extension_months: int,
        approved_by: str,
        approved_date: str,
        currency: str = None,
        new_rate: str = None,
    ) -> bool:
        """
        Send extension approved notification to contractor.

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "extension_approved",
            contractor_name=contractor_name,
            original_end_date=original_end_date,
            new_end_date=new_end_date,
            extension_months=extension_months,
            approved_by=approved_by,
            approved_date=approved_date,
            currency=currency,
            new_rate=new_rate,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Contract Extension Approved - {settings.company_name}",
            html=html,
        )

        logger.info(
            "Extension approved email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success

    async def send_extension_signature_request_email(
        self,
        contractor_email: str,
        contractor_name: str,
        original_end_date: str,
        new_end_date: str,
        extension_months: int,
        signing_link: str,
        expiry_date: str,
        currency: str = None,
        new_rate: str = None,
    ) -> bool:
        """
        Send extension signature request to contractor.

        Returns:
            True if sent successfully
        """
        html = self.templates.render(
            "extension_signature_request",
            contractor_name=contractor_name,
            original_end_date=original_end_date,
            new_end_date=new_end_date,
            extension_months=extension_months,
            signing_link=signing_link,
            expiry_date=expiry_date,
            currency=currency,
            new_rate=new_rate,
        )

        result = await self.email.send(
            to=contractor_email,
            subject=f"Sign Your Contract Extension - {settings.company_name}",
            html=html,
        )

        logger.info(
            "Extension signature request email sent",
            extra={
                "to": contractor_email,
                "success": result.success,
            }
        )

        return result.success
