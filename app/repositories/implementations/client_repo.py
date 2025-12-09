"""
Client repository implementation.

SQLAlchemy implementation of the client repository interface.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.repositories.implementations.base import BaseRepository
from app.repositories.interfaces.client_repo import IClientRepository
from app.models.client import Client
from app.models.contractor import Contractor


class ClientRepository(BaseRepository[Client], IClientRepository):
    """
    Client repository implementation.

    Provides all client-specific data access operations.
    """

    def __init__(self, db: Session):
        """Initialize with Client model."""
        super().__init__(Client, db)

    async def get_by_name(self, name: str) -> Optional[Client]:
        """Find client by name."""
        return (
            self.db.query(Client)
            .filter(Client.name == name)
            .first()
        )

    async def get_by_email(self, email: str) -> Optional[Client]:
        """Find client by email."""
        return (
            self.db.query(Client)
            .filter(Client.email == email)
            .first()
        )

    async def search(
        self,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Client], int]:
        """Search clients with filters."""
        q = self.db.query(Client)

        if query:
            search_filter = f"%{query}%"
            q = q.filter(
                or_(
                    Client.name.ilike(search_filter),
                    Client.email.ilike(search_filter),
                )
            )

        total = q.count()
        clients = (
            q.order_by(Client.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return clients, total

    async def get_active(self) -> List[Client]:
        """Get all active clients."""
        return (
            self.db.query(Client)
            .filter(Client.is_active == True)
            .order_by(Client.name.asc())
            .all()
        )

    async def get_with_contractor_count(self) -> List[dict]:
        """Get clients with their contractor counts."""
        results = (
            self.db.query(
                Client,
                func.count(Contractor.id).label("contractor_count")
            )
            .outerjoin(Contractor, Client.id == Contractor.client_id)
            .group_by(Client.id)
            .order_by(Client.name.asc())
            .all()
        )

        return [
            {
                "client": client,
                "contractor_count": count,
            }
            for client, count in results
        ]
