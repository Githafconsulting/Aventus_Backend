"""
Invoice repository interface.

Defines invoice-specific data access operations.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple
from datetime import date
from app.repositories.interfaces.base import IRepository
from app.models.invoice import Invoice, InvoiceStatus, InvoicePayment


class IInvoiceRepository(IRepository[Invoice]):
    """
    Invoice repository interface.

    Extends base repository with invoice-specific queries.
    """

    @abstractmethod
    async def get_by_payroll_id(self, payroll_id: int) -> Optional[Invoice]:
        """Find invoice by payroll ID."""
        pass

    @abstractmethod
    async def get_by_client_id(
        self,
        client_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a client."""
        pass

    @abstractmethod
    async def get_by_contractor_id(
        self,
        contractor_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a contractor."""
        pass

    @abstractmethod
    async def get_by_status(self, status: InvoiceStatus) -> List[Invoice]:
        """Get all invoices with a specific status."""
        pass

    @abstractmethod
    async def get_overdue(self) -> List[Invoice]:
        """Get all overdue invoices."""
        pass

    @abstractmethod
    async def get_by_access_token(self, token: str) -> Optional[Invoice]:
        """Find invoice by portal access token."""
        pass

    @abstractmethod
    async def get_next_invoice_number(self, client_id: str, year: int) -> str:
        """Generate next sequential invoice number for client and year."""
        pass

    @abstractmethod
    async def count_by_status(self) -> dict:
        """Count invoices by status."""
        pass

    @abstractmethod
    async def get_outstanding_totals(self) -> dict:
        """Get total outstanding and overdue amounts."""
        pass

    @abstractmethod
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
        pass


class IInvoicePaymentRepository(IRepository[InvoicePayment]):
    """
    Invoice payment repository interface.
    """

    @abstractmethod
    async def get_by_invoice_id(self, invoice_id: int) -> List[InvoicePayment]:
        """Get all payments for an invoice."""
        pass

    @abstractmethod
    async def get_total_paid(self, invoice_id: int) -> float:
        """Get total amount paid for an invoice."""
        pass
