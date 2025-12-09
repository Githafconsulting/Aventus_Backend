"""
Contractor repository implementation.

SQLAlchemy implementation of the contractor repository interface.
"""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.repositories.implementations.base import BaseRepository
from app.repositories.interfaces.contractor_repo import IContractorRepository
from app.models.contractor import Contractor
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute


class ContractorRepository(BaseRepository[Contractor], IContractorRepository):
    """
    Contractor repository implementation.

    Provides all contractor-specific data access operations.
    """

    def __init__(self, db: Session):
        """Initialize with Contractor model."""
        super().__init__(Contractor, db)

    async def get_by_email(self, email: str) -> Optional[Contractor]:
        """Find contractor by email."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.email == email)
            .first()
        )

    async def get_by_token(self, token: str) -> Optional[Contractor]:
        """Find contractor by document upload token."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.document_upload_token == token)
            .first()
        )

    async def get_by_contract_token(self, token: str) -> Optional[Contractor]:
        """Find contractor by contract signing token."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.contract_token == token)
            .first()
        )

    async def get_by_cohf_token(self, token: str) -> Optional[Contractor]:
        """Find contractor by COHF token."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.cohf_token == token)
            .first()
        )

    async def get_by_status(self, status: ContractorStatus) -> List[Contractor]:
        """Get all contractors with a specific status."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.status == status.value)
            .all()
        )

    async def get_by_route(self, route: OnboardingRoute) -> List[Contractor]:
        """Get all contractors on a specific onboarding route."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.onboarding_route == route.value)
            .all()
        )

    async def get_active(self) -> List[Contractor]:
        """Get all active contractors."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.status == ContractorStatus.ACTIVE.value)
            .all()
        )

    async def get_pending_review(self) -> List[Contractor]:
        """Get contractors pending admin review."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.status == ContractorStatus.PENDING_REVIEW.value)
            .order_by(Contractor.updated_at.asc())
            .all()
        )

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        route: Optional[str] = None,
        client_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Contractor], int]:
        """Search contractors with filters."""
        q = self.db.query(Contractor)

        # Apply search query (name or email)
        if query:
            search_filter = f"%{query}%"
            q = q.filter(
                or_(
                    Contractor.first_name.ilike(search_filter),
                    Contractor.surname.ilike(search_filter),
                    Contractor.email.ilike(search_filter),
                    Contractor.phone.ilike(search_filter),
                )
            )

        # Apply status filter
        if status:
            q = q.filter(Contractor.status == status)

        # Apply route filter
        if route:
            q = q.filter(Contractor.onboarding_route == route)

        # Apply client filter
        if client_id:
            q = q.filter(Contractor.client_id == client_id)

        # Get total count before pagination
        total = q.count()

        # Apply pagination and ordering
        contractors = (
            q.order_by(Contractor.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return contractors, total

    async def get_by_client(self, client_id: int) -> List[Contractor]:
        """Get all contractors for a specific client."""
        return (
            self.db.query(Contractor)
            .filter(Contractor.client_id == client_id)
            .order_by(Contractor.created_at.desc())
            .all()
        )

    async def get_expiring_tokens(self, hours: int = 24) -> List[Contractor]:
        """Get contractors with tokens expiring within specified hours."""
        expiry_threshold = datetime.utcnow() + timedelta(hours=hours)
        now = datetime.utcnow()

        return (
            self.db.query(Contractor)
            .filter(
                or_(
                    and_(
                        Contractor.document_upload_token.isnot(None),
                        Contractor.document_upload_token_expiry.between(now, expiry_threshold),
                    ),
                    and_(
                        Contractor.contract_token.isnot(None),
                        Contractor.contract_token_expiry.between(now, expiry_threshold),
                    ),
                )
            )
            .all()
        )

    async def get_by_statuses(self, statuses: List[ContractorStatus]) -> List[Contractor]:
        """
        Get contractors with any of the specified statuses.

        Args:
            statuses: List of statuses to filter by

        Returns:
            List of contractors matching any status
        """
        status_values = [s.value for s in statuses]
        return (
            self.db.query(Contractor)
            .filter(Contractor.status.in_(status_values))
            .all()
        )

    async def update_status(
        self,
        id: int,
        new_status: ContractorStatus,
    ) -> Optional[Contractor]:
        """
        Update contractor status.

        Args:
            id: Contractor ID
            new_status: New status

        Returns:
            Updated contractor or None
        """
        contractor = await self.get(id)
        if contractor:
            contractor.status = new_status.value
            contractor.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(contractor)
        return contractor

    async def get_statistics(self) -> dict:
        """
        Get contractor statistics.

        Returns:
            Dict with various counts and metrics
        """
        total = self.db.query(Contractor).count()
        active = (
            self.db.query(Contractor)
            .filter(Contractor.status == ContractorStatus.ACTIVE.value)
            .count()
        )
        pending_review = (
            self.db.query(Contractor)
            .filter(Contractor.status == ContractorStatus.PENDING_REVIEW.value)
            .count()
        )

        # Count by route
        routes = {}
        for route in OnboardingRoute:
            count = (
                self.db.query(Contractor)
                .filter(Contractor.onboarding_route == route.value)
                .count()
            )
            routes[route.value] = count

        return {
            "total": total,
            "active": active,
            "pending_review": pending_review,
            "by_route": routes,
        }
