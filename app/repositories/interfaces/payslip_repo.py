"""
Payslip repository interface.

Defines payslip-specific data access operations.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple
from app.repositories.interfaces.base import IRepository
from app.models.payslip import Payslip, PayslipStatus


class IPayslipRepository(IRepository[Payslip]):
    """
    Payslip repository interface.

    Extends base repository with payslip-specific queries.
    """

    @abstractmethod
    async def get_by_payroll_id(self, payroll_id: int) -> Optional[Payslip]:
        """Find payslip by payroll ID."""
        pass

    @abstractmethod
    async def get_by_contractor_id(
        self,
        contractor_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payslip]:
        """Get all payslips for a contractor."""
        pass

    @abstractmethod
    async def get_by_status(self, status: PayslipStatus) -> List[Payslip]:
        """Get all payslips with a specific status."""
        pass

    @abstractmethod
    async def get_by_access_token(self, token: str) -> Optional[Payslip]:
        """Find payslip by portal access token."""
        pass

    @abstractmethod
    async def get_next_document_number(self, year: int) -> str:
        """Generate next sequential document number for the year."""
        pass

    @abstractmethod
    async def count_by_status(self) -> dict:
        """Count payslips by status."""
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[PayslipStatus] = None,
        period: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Payslip], int]:
        """Search payslips with filters."""
        pass
