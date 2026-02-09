"""
Notification Service.

Application service for sending notifications via AWS Lambda/SES.
"""
from typing import Optional
from datetime import datetime

from app.utils.email import _invoke_email_lambda
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Application service for sending notifications.

    All methods invoke the AWS Lambda email function directly.
    Constructor params are kept optional for DI compatibility.
    """

    def __init__(
        self,
        email_sender=None,
        template_engine=None,
    ):
        pass

    async def send_document_upload_email(
        self,
        contractor_email: str,
        contractor_name: str,
        upload_token: str,
        expiry_date: datetime,
    ) -> bool:
        upload_link = f"{settings.frontend_url}/documents/upload/{upload_token}"
        result = _invoke_email_lambda("document_upload", contractor_email, {
            "contractor_name": contractor_name,
            "upload_link": upload_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })
        logger.info("Document upload email sent", extra={"to": contractor_email, "success": result})
        return result

    async def send_contract_signing_email(
        self,
        contractor_email: str,
        contractor_name: str,
        contract_token: str,
        expiry_date: datetime,
    ) -> bool:
        contract_link = f"{settings.contract_signing_url}?token={contract_token}"
        result = _invoke_email_lambda("contract_signing", contractor_email, {
            "contractor_name": contractor_name,
            "contract_link": contract_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })
        logger.info("Contract signing email sent", extra={"to": contractor_email, "success": result})
        return result

    async def send_activation_email(
        self,
        contractor_email: str,
        contractor_name: str,
        temporary_password: str,
    ) -> bool:
        result = _invoke_email_lambda("activation", contractor_email, {
            "contractor_name": contractor_name,
            "contractor_email": contractor_email,
            "temporary_password": temporary_password,
            "login_link": settings.frontend_url,
        })
        logger.info("Activation email sent", extra={"to": contractor_email, "success": result})
        return result

    async def send_documents_uploaded_notification(
        self,
        admin_email: str,
        contractor_name: str,
        contractor_id: int,
    ) -> bool:
        review_link = f"{settings.frontend_url}/admin/contractors/{contractor_id}"
        return _invoke_email_lambda("documents_uploaded", admin_email, {
            "contractor_name": contractor_name,
            "review_link": review_link,
        })

    async def send_cohf_signature_request(
        self,
        third_party_email: str,
        third_party_name: str,
        contractor_name: str,
        cohf_token: str,
        expiry_date: datetime,
    ) -> bool:
        signing_link = f"{settings.frontend_url}/cohf/sign/{cohf_token}"
        result = _invoke_email_lambda("cohf", third_party_email, {
            "third_party_name": third_party_name,
            "contractor_name": contractor_name,
            "signing_link": signing_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })
        logger.info("COHF signature email sent", extra={
            "to": third_party_email, "contractor": contractor_name, "success": result,
        })
        return result

    async def send_quote_sheet_request(
        self,
        third_party_email: str,
        third_party_name: str,
        contractor_name: str,
        quote_token: str,
        expiry_date: datetime,
    ) -> bool:
        quote_link = f"{settings.frontend_url}/quote-sheet/{quote_token}"
        return _invoke_email_lambda("quote_sheet_request", third_party_email, {
            "third_party_name": third_party_name,
            "contractor_name": contractor_name,
            "quote_link": quote_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })

    async def send_work_order_email(
        self,
        client_email: str,
        client_name: str,
        contractor_name: str,
        work_order_token: str,
        expiry_date: datetime,
    ) -> bool:
        signing_link = f"{settings.frontend_url}/work-order/sign/{work_order_token}"
        result = _invoke_email_lambda("work_order_client", client_email, {
            "client_name": client_name,
            "contractor_name": contractor_name,
            "signing_link": signing_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })
        logger.info("Work order email sent", extra={
            "to": client_email, "contractor": contractor_name, "success": result,
        })
        return result

    async def send_review_notification(
        self,
        admin_email: str,
        contractor_name: str,
        contractor_id: int,
        notification_type: str,
    ) -> bool:
        review_link = f"{settings.frontend_url}/admin/contractors/{contractor_id}"
        return _invoke_email_lambda("review_notification", admin_email, {
            "contractor_name": contractor_name,
            "notification_type": notification_type,
            "review_link": review_link,
        })

    async def send_password_reset_email(
        self,
        email: str,
        name: str,
        reset_token: str,
        expiry_date: datetime,
    ) -> bool:
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
        return _invoke_email_lambda("password_reset", email, {
            "name": name,
            "reset_link": reset_link,
            "expiry_date": expiry_date.strftime("%B %d, %Y at %I:%M %p"),
        })

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
        result = _invoke_email_lambda("offboarding_initiated", contractor_email, {
            "contractor_name": contractor_name,
            "reason": reason,
            "notice_start_date": notice_start_date,
            "last_working_date": last_working_date,
            "notice_period_days": str(notice_period_days),
        })
        logger.info("Offboarding initiated email sent", extra={"to": contractor_email, "success": result})
        return result

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
        return _invoke_email_lambda("offboarding_settlement", contractor_email, {
            "contractor_name": contractor_name,
            "currency": currency,
            "total_settlement": total_settlement,
            "pro_rata_salary": pro_rata_salary,
            "days_worked": str(days_worked),
            "unused_leave_payout": unused_leave_payout,
            "leave_days_remaining": leave_days_remaining,
            "gratuity_eosb": gratuity_eosb,
            "pending_reimbursements": pending_reimbursements,
            "deductions": deductions,
        })

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
        result = _invoke_email_lambda("offboarding_completed", contractor_email, {
            "contractor_name": contractor_name,
            "effective_date": effective_date,
            "currency": currency,
            "total_settlement": total_settlement,
            "termination_letter_url": termination_letter_url,
            "experience_letter_url": experience_letter_url,
            "clearance_certificate_url": clearance_certificate_url,
            "final_payslip_url": final_payslip_url,
        })
        logger.info("Offboarding completed email sent", extra={"to": contractor_email, "success": result})
        return result

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
        return _invoke_email_lambda("extension_request", admin_email, {
            "contractor_name": contractor_name,
            "original_end_date": original_end_date,
            "new_end_date": new_end_date,
            "extension_months": str(extension_months),
            "requested_by": requested_by,
            "review_link": review_link,
            "currency": currency,
            "new_rate": new_rate,
            "rate_change_reason": rate_change_reason,
        })

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
        result = _invoke_email_lambda("extension_approved", contractor_email, {
            "contractor_name": contractor_name,
            "original_end_date": original_end_date,
            "new_end_date": new_end_date,
            "extension_months": str(extension_months),
            "approved_by": approved_by,
            "approved_date": approved_date,
            "currency": currency,
            "new_rate": new_rate,
        })
        logger.info("Extension approved email sent", extra={"to": contractor_email, "success": result})
        return result

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
        result = _invoke_email_lambda("extension_signature_request", contractor_email, {
            "contractor_name": contractor_name,
            "original_end_date": original_end_date,
            "new_end_date": new_end_date,
            "extension_months": str(extension_months),
            "signing_link": signing_link,
            "expiry_date": expiry_date,
            "currency": currency,
            "new_rate": new_rate,
        })
        logger.info("Extension signature request email sent", extra={"to": contractor_email, "success": result})
        return result
