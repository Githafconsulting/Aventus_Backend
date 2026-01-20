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
from app.adapters.email.interface import IEmailSender, EmailAttachment
from app.adapters.email.template_engine import EmailTemplateEngine
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
        email_sender: Optional[IEmailSender] = None,
        template_engine: Optional[EmailTemplateEngine] = None,
    ):
        self.repo = payslip_repo
        self.db = db
        self.email = email_sender
        self.templates = template_engine

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
        Send payslip email to contractor.

        Args:
            payslip_id: ID of the payslip

        Returns:
            True if sent successfully
        """
        if not self.email or not self.templates:
            raise ValueError("Email sender not configured")

        payslip = await self.repo.get(payslip_id)
        if not payslip:
            raise ValueError(f"Payslip {payslip_id} not found")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == payslip.contractor_id
        ).first()
        if not contractor:
            raise ValueError("Contractor not found")

        # Get PDF content for attachment
        payroll = self.db.query(Payroll).filter(
            Payroll.id == payslip.payroll_id
        ).first()

        pdf_buffer = generate_payslip_pdf(payroll, contractor)
        pdf_content = pdf_buffer.read()

        # Portal link
        portal_link = f"{settings.frontend_url}/payslip/{payslip.access_token}"

        # Render email template
        contractor_name = f"{contractor.first_name} {contractor.surname}"
        html = self.templates.render(
            "payslip",
            contractor_name=contractor_name,
            document_number=payslip.document_number,
            period=payslip.period,
            net_salary=payroll.net_salary if payroll else 0,
            currency=payroll.currency if payroll else "AED",
            portal_link=portal_link,
        )

        # Send with attachment
        attachment = EmailAttachment(
            filename=f"{payslip.document_number}.pdf",
            content=pdf_content,
            content_type="application/pdf",
        )

        result = await self.email.send(
            to=contractor.email,
            subject=f"Your Payslip for {payslip.period} - {payslip.document_number}",
            html=html,
            attachments=[attachment],
        )

        if result.success:
            # Update status
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

        return result.success

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
