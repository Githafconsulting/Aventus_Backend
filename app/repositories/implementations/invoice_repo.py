"""
Invoice repository implementation.

SQLAlchemy-based implementation of invoice data access.
"""
from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.repositories.implementations.base import BaseRepository
from app.repositories.interfaces.invoice_repo import IInvoiceRepository, IInvoicePaymentRepository
from app.models.invoice import Invoice, InvoiceStatus, InvoicePayment
from app.models.client import Client
from app.models.contractor import Contractor


class InvoiceRepository(BaseRepository[Invoice], IInvoiceRepository):
    """
    SQLAlchemy implementation of invoice repository.
    """

    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    async def get_by_payroll_id(self, payroll_id: int) -> Optional[Invoice]:
        """Find invoice by payroll ID."""
        return self.db.query(Invoice).filter(
            Invoice.payroll_id == payroll_id
        ).first()

    async def get_by_client_id(
        self,
        client_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a client."""
        return self.db.query(Invoice).filter(
            Invoice.client_id == client_id
        ).order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

    async def get_by_contractor_id(
        self,
        contractor_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a contractor."""
        return self.db.query(Invoice).filter(
            Invoice.contractor_id == contractor_id
        ).order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

    async def get_by_status(self, status: InvoiceStatus) -> List[Invoice]:
        """Get all invoices with a specific status."""
        return self.db.query(Invoice).filter(
            Invoice.status == status
        ).order_by(Invoice.created_at.desc()).all()

    async def get_overdue(self) -> List[Invoice]:
        """Get all overdue invoices."""
        today = date.today()
        return self.db.query(Invoice).filter(
            Invoice.due_date < today,
            Invoice.status.notin_([InvoiceStatus.PAID, InvoiceStatus.OVERDUE])
        ).order_by(Invoice.due_date.asc()).all()

    async def get_by_access_token(self, token: str) -> Optional[Invoice]:
        """Find invoice by portal access token."""
        return self.db.query(Invoice).filter(
            Invoice.access_token == token
        ).first()

    async def get_next_invoice_number(self, client_id: str, year: int) -> str:
        """Generate next sequential invoice number for client and year."""
        prefix = f"INV-{year}-"

        # Find the highest number for this year (global, not per-client)
        last = self.db.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.invoice_number.desc()).first()

        if last:
            last_num = int(last.invoice_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    async def count_by_status(self) -> dict:
        """Count invoices by status."""
        counts = self.db.query(
            Invoice.status,
            func.count(Invoice.id)
        ).group_by(Invoice.status).all()

        return {status.value: count for status, count in counts}

    async def get_outstanding_totals(self) -> dict:
        """Get total outstanding and overdue amounts."""
        today = date.today()

        # Total outstanding (not paid)
        outstanding = self.db.query(func.sum(Invoice.balance)).filter(
            Invoice.status.notin_([InvoiceStatus.PAID])
        ).scalar() or 0

        # Total overdue
        overdue = self.db.query(func.sum(Invoice.balance)).filter(
            Invoice.due_date < today,
            Invoice.status.notin_([InvoiceStatus.PAID])
        ).scalar() or 0

        return {
            "total_outstanding": float(outstanding),
            "total_overdue": float(overdue)
        }

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        client_id: Optional[str] = None,
        due_before: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Invoice], int]:
        """Search invoices with filters."""
        q = self.db.query(Invoice).join(Client).join(Contractor)

        if query:
            search_filter = f"%{query}%"
            q = q.filter(or_(
                Client.company_name.ilike(search_filter),
                Contractor.first_name.ilike(search_filter),
                Contractor.surname.ilike(search_filter),
                Invoice.invoice_number.ilike(search_filter),
            ))

        if status:
            q = q.filter(Invoice.status == status)

        if client_id:
            q = q.filter(Invoice.client_id == client_id)

        if due_before:
            q = q.filter(Invoice.due_date <= due_before)

        total = q.count()
        results = q.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

        return results, total


class InvoicePaymentRepository(BaseRepository[InvoicePayment], IInvoicePaymentRepository):
    """
    SQLAlchemy implementation of invoice payment repository.
    """

    def __init__(self, db: Session):
        super().__init__(InvoicePayment, db)

    async def get_by_invoice_id(self, invoice_id: int) -> List[InvoicePayment]:
        """Get all payments for an invoice."""
        return self.db.query(InvoicePayment).filter(
            InvoicePayment.invoice_id == invoice_id
        ).order_by(InvoicePayment.payment_date.desc()).all()

    async def get_total_paid(self, invoice_id: int) -> float:
        """Get total amount paid for an invoice."""
        result = self.db.query(func.sum(InvoicePayment.amount)).filter(
            InvoicePayment.invoice_id == invoice_id
        ).scalar()
        return float(result) if result else 0.0
