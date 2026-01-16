"""
Payroll repository implementation.

SQLAlchemy-based implementation of payroll data access.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.repositories.implementations.base import BaseRepository
from app.repositories.interfaces.payroll_repo import IPayrollRepository
from app.models.payroll import Payroll, PayrollStatus


class PayrollRepository(BaseRepository[Payroll], IPayrollRepository):
    """
    SQLAlchemy implementation of payroll repository.

    Inherits common CRUD operations from BaseRepository.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(Payroll, db)

    async def get_by_timesheet_id(self, timesheet_id: int) -> Optional[Payroll]:
        """Find payroll by timesheet ID."""
        return self.db.query(Payroll).filter(
            Payroll.timesheet_id == timesheet_id
        ).first()

    async def get_by_contractor_id(self, contractor_id: str) -> List[Payroll]:
        """Get all payroll records for a contractor."""
        return self.db.query(Payroll).filter(
            Payroll.contractor_id == contractor_id
        ).order_by(Payroll.created_at.desc()).all()

    async def get_by_status(self, status: PayrollStatus) -> List[Payroll]:
        """Get all payroll records with a specific status."""
        return self.db.query(Payroll).filter(
            Payroll.status == status
        ).order_by(Payroll.created_at.desc()).all()

    async def get_by_period(self, period: str) -> List[Payroll]:
        """Get all payroll records for a specific period."""
        return self.db.query(Payroll).filter(
            Payroll.period == period
        ).order_by(Payroll.contractor_id).all()

    async def count_by_status(self) -> dict:
        """Count payroll records by status."""
        counts = self.db.query(
            Payroll.status,
            func.count(Payroll.id)
        ).group_by(Payroll.status).all()

        return {
            status.value: count for status, count in counts
        }

    async def exists_for_timesheet(self, timesheet_id: int) -> bool:
        """Check if payroll already exists for a timesheet."""
        return self.db.query(Payroll).filter(
            Payroll.timesheet_id == timesheet_id
        ).count() > 0
