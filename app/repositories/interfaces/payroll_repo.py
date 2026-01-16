"""
Payroll repository interface.

Defines payroll-specific data access operations.
"""
from abc import abstractmethod
from typing import List, Optional
from app.repositories.interfaces.base import IRepository
from app.models.payroll import Payroll, PayrollStatus


class IPayrollRepository(IRepository[Payroll]):
    """
    Payroll repository interface.

    Extends base repository with payroll-specific queries.
    """

    @abstractmethod
    async def get_by_timesheet_id(self, timesheet_id: int) -> Optional[Payroll]:
        """
        Find payroll by timesheet ID.

        Args:
            timesheet_id: ID of the timesheet

        Returns:
            Payroll if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_contractor_id(self, contractor_id: str) -> List[Payroll]:
        """
        Get all payroll records for a contractor.

        Args:
            contractor_id: Contractor ID

        Returns:
            List of payroll records
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: PayrollStatus) -> List[Payroll]:
        """
        Get all payroll records with a specific status.

        Args:
            status: Payroll status to filter by

        Returns:
            List of payroll records
        """
        pass

    @abstractmethod
    async def get_by_period(self, period: str) -> List[Payroll]:
        """
        Get all payroll records for a specific period.

        Args:
            period: Period string (e.g., "January 2025")

        Returns:
            List of payroll records
        """
        pass

    @abstractmethod
    async def count_by_status(self) -> dict:
        """
        Count payroll records by status.

        Returns:
            Dictionary with status counts (e.g., {"calculated": 5, "approved": 3})
        """
        pass

    @abstractmethod
    async def exists_for_timesheet(self, timesheet_id: int) -> bool:
        """
        Check if payroll already exists for a timesheet.

        Args:
            timesheet_id: ID of the timesheet

        Returns:
            True if payroll exists, False otherwise
        """
        pass
