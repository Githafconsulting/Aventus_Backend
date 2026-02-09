"""
Payslip Service - Business logic for payslip management.

Handles payslip generation, PDF creation, storage, and email delivery.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.models.payslip import Payslip, PayslipStatus
from app.models.payroll import Payroll, PayrollStatus
from app.models.contractor import Contractor
from app.repositories.implementations.payslip_repo import PayslipRepository
from app.utils.payroll_pdf import generate_payslip_pdf
from app.utils.storage import upload_file
from app.utils.email import _invoke_email_lambda
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class PayslipService:
    """
    Payslip business logic service.

    Orchestrates payslip generation, PDF creation, storage, and delivery.
    """

    def __init__(
        self,
        payslip_repo: PayslipRepository,
        db: Session,
        email_sender=None,
        template_engine=None,
    ):
        self.repo = payslip_repo
        self.db = db

    async def generate_payslip(self, payroll_id: int) -> Payslip:
        """
        Generate a payslip for an approved/paid payroll.

        Args:
            payroll_id: ID of the payroll record

        Returns:
            Created Payslip record

        Raises:
            ValueError: If payroll not found or already has payslip
        """
        # Get payroll
        payroll = self.db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not payroll:
            raise ValueError(f"Payroll {payroll_id} not found")

        # Check if payslip already exists
        existing = await self.repo.get_by_payroll_id(payroll_id)
        if existing:
            raise ValueError(f"Payslip already exists for payroll {payroll_id}")

        # Check payroll status
        if payroll.status not in [PayrollStatus.APPROVED, PayrollStatus.PAID]:
            raise ValueError(f"Payroll must be approved or paid to generate payslip")

        # Get contractor
        contractor = self.db.query(Contractor).filter(
            Contractor.id == payroll.contractor_id
        ).first()
        if not contractor:
            raise ValueError("Contractor not found")

        # Generate document number
        year = datetime.now().year
        document_number = await self.repo.get_next_document_number(year)

        # Generate PDF
        pdf_buffer = generate_payslip_pdf(payroll, contractor)

        # Upload to storage
        filename = f"{document_number}.pdf"
        folder = f"payslips/{contractor.id}"
        pdf_url = upload_file(pdf_buffer, filename, folder)

        # Generate access token
        access_token = secrets.token_urlsafe(32)
        token_expiry = datetime.utcnow() + timedelta(days=30)

        # Create payslip record
        payslip_data = {
            "payroll_id": payroll_id,
            "contractor_id": contractor.id,
            "document_number": document_number,
            "period": payroll.period or datetime.now().strftime("%B %Y"),
            "pdf_storage_key": f"{folder}/{filename}",
            "pdf_url": pdf_url,
            "status": PayslipStatus.GENERATED,
            "access_token": access_token,
            "token_expiry": token_expiry,
        }

        payslip = await self.repo.create(payslip_data)

        logger.info(
            "Payslip generated",
            extra={
                "payslip_id": payslip.id,
                "document_number": document_number,
                "contractor_id": contractor.id,
            }
        )

        return payslip

    async def generate_bulk(self, payroll_ids: List[int]) -> Dict[str, List]:
        """
        Bulk generate payslips for multiple payrolls.

        Args:
            payroll_ids: List of payroll IDs

        Returns:
            Dict with 'success' and 'failed' lists
        """
        results = {"success": [], "failed": []}

        for payroll_id in payroll_ids:
            try:
                payslip = await self.generate_payslip(payroll_id)
                results["success"].append({
                    "payroll_id": payroll_id,
                    "payslip_id": payslip.id,
                    "document_number": payslip.document_number,
                })
            except Exception as e:
                results["failed"].append({
                    "payroll_id": payroll_id,
                    "error": str(e),
                })

        return results

    async def send_payslip(self, payslip_id: int) -> bool:
        """
        Send payslip email to contractor via Lambda.

        Args:
            payslip_id: ID of the payslip

        Returns:
            True if sent successfully
        """
        payslip = await self.repo.get(payslip_id)
        if not payslip:
            raise ValueError(f"Payslip {payslip_id} not found")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == payslip.contractor_id
        ).first()
        if not contractor:
            raise ValueError("Contractor not found")

        payroll = self.db.query(Payroll).filter(
            Payroll.id == payslip.payroll_id
        ).first()

        portal_link = f"{settings.frontend_url}/payslip/{payslip.access_token}"
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        success = _invoke_email_lambda("payslip", contractor.email, {
            "contractor_name": contractor_name,
            "document_number": payslip.document_number,
            "period": payslip.period,
            "net_salary": str(payroll.net_salary) if payroll and payroll.net_salary else "0",
            "currency": payroll.currency if payroll else "AED",
            "portal_link": portal_link,
        })

        if success:
            payslip.status = PayslipStatus.SENT
            payslip.sent_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                "Payslip sent",
                extra={
                    "payslip_id": payslip_id,
                    "to": contractor.email,
                }
            )

        return success

    async def send_bulk(self, payslip_ids: List[int]) -> Dict[str, List]:
        """
        Bulk send payslips.

        Args:
            payslip_ids: List of payslip IDs

        Returns:
            Dict with 'success' and 'failed' lists
        """
        results = {"success": [], "failed": []}

        for payslip_id in payslip_ids:
            try:
                success = await self.send_payslip(payslip_id)
                if success:
                    results["success"].append(payslip_id)
                else:
                    results["failed"].append({
                        "payslip_id": payslip_id,
                        "error": "Failed to send",
                    })
            except Exception as e:
                results["failed"].append({
                    "payslip_id": payslip_id,
                    "error": str(e),
                })

        return results

    async def mark_viewed(self, payslip_id: int) -> Payslip:
        """Mark payslip as viewed (from portal access)."""
        payslip = await self.repo.get(payslip_id)
        if not payslip:
            raise ValueError(f"Payslip {payslip_id} not found")

        if payslip.status == PayslipStatus.SENT:
            payslip.status = PayslipStatus.VIEWED
            payslip.viewed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(payslip)

        return payslip

    async def acknowledge(self, payslip_id: int) -> Payslip:
        """Contractor acknowledges receipt of payslip."""
        payslip = await self.repo.get(payslip_id)
        if not payslip:
            raise ValueError(f"Payslip {payslip_id} not found")

        if payslip.status in [PayslipStatus.SENT, PayslipStatus.VIEWED]:
            payslip.status = PayslipStatus.ACKNOWLEDGED
            payslip.acknowledged_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(payslip)

        return payslip

    async def get_by_access_token(self, token: str) -> Optional[Payslip]:
        """Get payslip by portal access token."""
        payslip = await self.repo.get_by_access_token(token)

        if payslip and payslip.token_expiry:
            if datetime.utcnow() > payslip.token_expiry:
                return None  # Token expired

        return payslip

    async def get_stats(self) -> Dict:
        """Get payslip statistics."""
        counts = await self.repo.count_by_status()

        total = sum(counts.values())

        return {
            "total": total,
            "generated": counts.get("generated", 0),
            "sent": counts.get("sent", 0),
            "viewed": counts.get("viewed", 0),
            "acknowledged": counts.get("acknowledged", 0),
        }

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[PayslipStatus] = None,
        period: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Payslip], int]:
        """Search payslips with filters."""
        return await self.repo.search(
            query=query,
            status=status,
            period=period,
            skip=skip,
            limit=limit,
        )

    async def regenerate_pdf(self, payslip_id: int) -> Payslip:
        """Regenerate PDF for an existing payslip."""
        payslip = await self.repo.get(payslip_id)
        if not payslip:
            raise ValueError(f"Payslip {payslip_id} not found")

        payroll = self.db.query(Payroll).filter(
            Payroll.id == payslip.payroll_id
        ).first()
        contractor = self.db.query(Contractor).filter(
            Contractor.id == payslip.contractor_id
        ).first()

        if not payroll or not contractor:
            raise ValueError("Related records not found")

        # Generate new PDF
        pdf_buffer = generate_payslip_pdf(payroll, contractor)

        # Upload to storage (overwrite)
        filename = f"{payslip.document_number}.pdf"
        folder = f"payslips/{contractor.id}"
        pdf_url = upload_file(pdf_buffer, filename, folder)

        # Update URL
        payslip.pdf_url = pdf_url
        payslip.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payslip)

        return payslip
