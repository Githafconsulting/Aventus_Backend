"""
Invoice Service - Business logic for invoice management.

Handles invoice generation, payment tracking, and email delivery.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, date
import secrets

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus, InvoicePayment
from app.models.payroll import Payroll, PayrollStatus
from app.models.contractor import Contractor
from app.models.client import Client
from app.repositories.implementations.invoice_repo import InvoiceRepository, InvoicePaymentRepository
from app.utils.payroll_pdf import generate_invoice_pdf
from app.utils.storage import upload_file
from app.utils.email import _invoke_email_lambda
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class InvoiceService:
    """
    Invoice business logic service.

    Orchestrates invoice generation, payment tracking, and delivery.
    """

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        payment_repo: InvoicePaymentRepository,
        db: Session,
        email_sender=None,
        template_engine=None,
    ):
        self.repo = invoice_repo
        self.payment_repo = payment_repo
        self.db = db

    async def generate_invoice(
        self,
        payroll_id: int,
        payment_terms: str = "Net 30",
        notes: Optional[str] = None,
    ) -> Invoice:
        """
        Generate an invoice for a payroll.

        Args:
            payroll_id: ID of the payroll record
            payment_terms: Payment terms (Net 30, Net 60, etc.)
            notes: Optional notes

        Returns:
            Created Invoice record
        """
        # Get payroll
        payroll = self.db.query(Payroll).filter(Payroll.id == payroll_id).first()
        if not payroll:
            raise ValueError(f"Payroll {payroll_id} not found")

        # Check if invoice already exists
        existing = await self.repo.get_by_payroll_id(payroll_id)
        if existing:
            raise ValueError(f"Invoice already exists for payroll {payroll_id}")

        # Check payroll status
        if payroll.status not in [PayrollStatus.APPROVED, PayrollStatus.PAID]:
            raise ValueError("Payroll must be approved or paid to generate invoice")

        # Get contractor
        contractor = self.db.query(Contractor).filter(
            Contractor.id == payroll.contractor_id
        ).first()
        if not contractor:
            raise ValueError("Contractor not found")

        # Get or find client
        client_id = contractor.client_id
        client = None
        if client_id:
            client = self.db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise ValueError("Client not found for contractor")

        # Generate invoice number
        year = datetime.now().year
        invoice_number = await self.repo.get_next_invoice_number(client.id, year)

        # Calculate amounts
        subtotal = payroll.invoice_total or payroll.total_payable or 0
        vat_rate = payroll.vat_rate or 0.05
        vat_amount = subtotal * vat_rate
        total_amount = subtotal + vat_amount

        # Calculate due date
        days_terms = self._parse_payment_terms(payment_terms)
        invoice_date = date.today()
        due_date = invoice_date + timedelta(days=days_terms)

        # Generate PDF
        pdf_buffer = generate_invoice_pdf(payroll, contractor)

        # Upload to storage
        filename = f"{invoice_number}.pdf"
        folder = f"invoices/{client.id}"
        pdf_url = upload_file(pdf_buffer, filename, folder)

        # Generate access token
        access_token = secrets.token_urlsafe(32)
        token_expiry = datetime.utcnow() + timedelta(days=90)

        # Create invoice record
        invoice_data = {
            "payroll_id": payroll_id,
            "client_id": client.id,
            "contractor_id": contractor.id,
            "invoice_number": invoice_number,
            "subtotal": subtotal,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "amount_paid": 0,
            "balance": total_amount,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "payment_terms": payment_terms,
            "pdf_storage_key": f"{folder}/{filename}",
            "pdf_url": pdf_url,
            "status": InvoiceStatus.DRAFT,
            "access_token": access_token,
            "token_expiry": token_expiry,
            "notes": notes,
        }

        invoice = await self.repo.create(invoice_data)

        logger.info(
            "Invoice generated",
            extra={
                "invoice_id": invoice.id,
                "invoice_number": invoice_number,
                "client_id": client.id,
            }
        )

        return invoice

    def _parse_payment_terms(self, terms: str) -> int:
        """Parse payment terms to get number of days."""
        terms = terms.lower()
        if "60" in terms:
            return 60
        elif "45" in terms:
            return 45
        elif "15" in terms:
            return 15
        elif "7" in terms:
            return 7
        return 30  # Default to Net 30

    async def send_invoice(self, invoice_id: int) -> bool:
        """
        Send invoice email to client via Lambda.

        Args:
            invoice_id: ID of the invoice

        Returns:
            True if sent successfully
        """
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.OVERDUE]:
            raise ValueError("Invoice can only be sent from draft or overdue status")

        client = self.db.query(Client).filter(Client.id == invoice.client_id).first()
        contractor = self.db.query(Contractor).filter(
            Contractor.id == invoice.contractor_id
        ).first()

        if not client or not contractor:
            raise ValueError("Related records not found")

        client_email = client.contact_person_email
        if not client_email:
            raise ValueError("Client does not have a contact email")

        payroll = self.db.query(Payroll).filter(
            Payroll.id == invoice.payroll_id
        ).first()

        portal_link = f"{settings.frontend_url}/invoice/{invoice.access_token}"
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        success = _invoke_email_lambda("invoice", client_email, {
            "client_name": client.company_name,
            "invoice_number": invoice.invoice_number,
            "contractor_name": contractor_name,
            "period": payroll.period if payroll else "",
            "total_amount": invoice.total_amount,
            "currency": payroll.currency if payroll else "AED",
            "due_date": invoice.due_date.strftime("%B %d, %Y"),
            "portal_link": portal_link,
        })

        if success:
            invoice.status = InvoiceStatus.SENT
            invoice.sent_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                "Invoice sent",
                extra={
                    "invoice_id": invoice_id,
                    "to": client_email,
                }
            )

        return success

    async def send_bulk(self, invoice_ids: List[int]) -> Dict[str, List]:
        """Bulk send invoices."""
        results = {"success": [], "failed": []}

        for invoice_id in invoice_ids:
            try:
                success = await self.send_invoice(invoice_id)
                if success:
                    results["success"].append(invoice_id)
                else:
                    results["failed"].append({
                        "invoice_id": invoice_id,
                        "error": "Failed to send",
                    })
            except Exception as e:
                results["failed"].append({
                    "invoice_id": invoice_id,
                    "error": str(e),
                })

        return results

    async def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: date,
        payment_method: Optional[str] = None,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> InvoicePayment:
        """
        Record a payment against an invoice.

        Args:
            invoice_id: ID of the invoice
            amount: Payment amount
            payment_date: Date of payment
            payment_method: Payment method
            reference_number: Transaction reference
            notes: Optional notes

        Returns:
            Created InvoicePayment record
        """
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        if amount > invoice.balance:
            raise ValueError(f"Payment amount exceeds balance of {invoice.balance}")

        # Create payment record
        payment_data = {
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_date": payment_date,
            "payment_method": payment_method,
            "reference_number": reference_number,
            "notes": notes,
        }

        payment = await self.payment_repo.create(payment_data)

        # Update invoice
        invoice.amount_paid += amount
        invoice.balance = invoice.total_amount - invoice.amount_paid

        if invoice.balance <= 0:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.utcnow()
        elif invoice.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        self.db.commit()

        logger.info(
            "Payment recorded",
            extra={
                "invoice_id": invoice_id,
                "amount": amount,
                "new_balance": invoice.balance,
            }
        )

        return payment

    async def check_and_mark_overdue(self) -> List[Invoice]:
        """Check for overdue invoices and update their status."""
        overdue = await self.repo.get_overdue()

        for invoice in overdue:
            invoice.status = InvoiceStatus.OVERDUE
            self.db.commit()

        return overdue

    async def send_overdue_reminder(self, invoice_id: int) -> bool:
        """Send overdue reminder email via Lambda."""
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status != InvoiceStatus.OVERDUE:
            raise ValueError("Invoice is not overdue")

        client = self.db.query(Client).filter(Client.id == invoice.client_id).first()
        contractor = self.db.query(Contractor).filter(
            Contractor.id == invoice.contractor_id
        ).first()

        if not client or not contractor:
            raise ValueError("Related records not found")

        client_email = client.contact_person_email
        if not client_email:
            raise ValueError("Client does not have a contact email")

        payroll = self.db.query(Payroll).filter(
            Payroll.id == invoice.payroll_id
        ).first()

        days_overdue = (date.today() - invoice.due_date).days
        portal_link = f"{settings.frontend_url}/invoice/{invoice.access_token}"
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        return _invoke_email_lambda("invoice_overdue", client_email, {
            "client_name": client.company_name,
            "invoice_number": invoice.invoice_number,
            "contractor_name": contractor_name,
            "balance": invoice.balance,
            "currency": payroll.currency if payroll else "AED",
            "due_date": invoice.due_date.strftime("%B %d, %Y"),
            "days_overdue": days_overdue,
            "portal_link": portal_link,
        })

    async def mark_viewed(self, invoice_id: int) -> Invoice:
        """Mark invoice as viewed (from portal access)."""
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status == InvoiceStatus.SENT:
            invoice.status = InvoiceStatus.VIEWED
            invoice.viewed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(invoice)

        return invoice

    async def get_by_access_token(self, token: str) -> Optional[Invoice]:
        """Get invoice by portal access token."""
        invoice = await self.repo.get_by_access_token(token)

        if invoice and invoice.token_expiry:
            if datetime.utcnow() > invoice.token_expiry:
                return None

        return invoice

    async def update_invoice(
        self,
        invoice_id: int,
        payment_terms: Optional[str] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Invoice:
        """Update a draft invoice."""
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Only draft invoices can be updated")

        if payment_terms:
            invoice.payment_terms = payment_terms
        if due_date:
            invoice.due_date = due_date
        if notes is not None:
            invoice.notes = notes

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    async def delete_invoice(self, invoice_id: int) -> bool:
        """Delete a draft invoice."""
        invoice = await self.repo.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Only draft invoices can be deleted")

        return await self.repo.delete(invoice_id)

    async def get_stats(self) -> Dict:
        """Get invoice statistics."""
        counts = await self.repo.count_by_status()
        totals = await self.repo.get_outstanding_totals()

        total = sum(counts.values())

        return {
            "total": total,
            "draft": counts.get("draft", 0),
            "sent": counts.get("sent", 0),
            "partially_paid": counts.get("partially_paid", 0),
            "paid": counts.get("paid", 0),
            "overdue": counts.get("overdue", 0),
            "total_outstanding": totals["total_outstanding"],
            "total_overdue": totals["total_overdue"],
        }

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        client_id: Optional[str] = None,
        due_before: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Invoice], int]:
        """Search invoices with filters."""
        return await self.repo.search(
            query=query,
            status=status,
            client_id=client_id,
            due_before=due_before,
            skip=skip,
            limit=limit,
        )
