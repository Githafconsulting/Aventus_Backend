"""
Payslip repository implementation.

SQLAlchemy-based implementation of payslip data access.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.repositories.implementations.base import BaseRepository
from app.repositories.interfaces.payslip_repo import IPayslipRepository
from app.models.payslip import Payslip, PayslipStatus
from app.models.contractor import Contractor


class PayslipRepository(BaseRepository[Payslip], IPayslipRepository):
    """
    SQLAlchemy implementation of payslip repository.
    """

    def __init__(self, db: Session):
        super().__init__(Payslip, db)

    async def get_by_payroll_id(self, payroll_id: int) -> Optional[Payslip]:
        """Find payslip by payroll ID."""
        return self.db.query(Payslip).filter(
            Payslip.payroll_id == payroll_id
        ).first()

    async def get_by_contractor_id(
        self,
        contractor_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payslip]:
        """Get all payslips for a contractor."""
        return self.db.query(Payslip).filter(
            Payslip.contractor_id == contractor_id
        ).order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()

    async def get_by_status(self, status: PayslipStatus) -> List[Payslip]:
        """Get all payslips with a specific status."""
        return self.db.query(Payslip).filter(
            Payslip.status == status
        ).order_by(Payslip.created_at.desc()).all()

    async def get_by_access_token(self, token: str) -> Optional[Payslip]:
        """Find payslip by portal access token."""
        return self.db.query(Payslip).filter(
            Payslip.access_token == token
        ).first()

    async def get_next_document_number(self, year: int) -> str:
        """Generate next sequential document number for the year."""
        prefix = f"PS-{year}-"

        # Find the highest number for this year
        last = self.db.query(Payslip).filter(
            Payslip.document_number.like(f"{prefix}%")
        ).order_by(Payslip.document_number.desc()).with_for_update().first()

        if last:
            # Extract number and increment
            last_num = int(last.document_number.split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:06d}"

    async def count_by_status(self) -> dict:
        """Count payslips by status."""
        counts = self.db.query(
            Payslip.status,
            func.count(Payslip.id)
        ).group_by(Payslip.status).all()

        return {status.value: count for status, count in counts}

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[PayslipStatus] = None,
        period: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Payslip], int]:
        """Search payslips with filters."""
        q = self.db.query(Payslip).join(Contractor)

        if query:
            search_filter = f"%{query}%"
            q = q.filter(or_(
                Contractor.first_name.ilike(search_filter),
                Contractor.surname.ilike(search_filter),
                Contractor.email.ilike(search_filter),
                Payslip.document_number.ilike(search_filter),
            ))

        if status:
            q = q.filter(Payslip.status == status)

        if period:
            q = q.filter(Payslip.period == period)

        total = q.count()
        results = q.order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()

        return results, total
