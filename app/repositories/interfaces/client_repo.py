"""
Client repository interface.

Defines client-specific data access operations.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple
from app.repositories.interfaces.base import IRepository
from app.models.client import Client


class IClientRepository(IRepository[Client]):
    """
    Client repository interface.

    Extends base repository with client-specific queries.
    """

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Client]:
        """
        Find client by name.

        Args:
            name: Client name

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Client]:
        """
        Find client by email.

        Args:
            email: Client email

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Client], int]:
        """
        Search clients with filters.

        Args:
            query: Search term (name or email)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (clients list, total count)
        """
        pass

    @abstractmethod
    async def get_active(self) -> List[Client]:
        """
        Get all active clients.

        Returns:
            List of active clients
        """
        pass

    @abstractmethod
    async def get_with_contractor_count(self) -> List[dict]:
        """
        Get clients with their contractor counts.

        Returns:
            List of dicts with client info and contractor_count
        """
        pass
