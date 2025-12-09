"""
Contractor repository interface.

Defines contractor-specific data access operations.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple
from app.repositories.interfaces.base import IRepository
from app.models.contractor import Contractor
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute


class IContractorRepository(IRepository[Contractor]):
    """
    Contractor repository interface.

    Extends base repository with contractor-specific queries.
    """

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Contractor]:
        """
        Find contractor by email address.

        Args:
            email: Contractor's email

        Returns:
            Contractor if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[Contractor]:
        """
        Find contractor by document upload token.

        Args:
            token: Document upload token

        Returns:
            Contractor if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_contract_token(self, token: str) -> Optional[Contractor]:
        """
        Find contractor by contract signing token.

        Args:
            token: Contract signing token

        Returns:
            Contractor if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_cohf_token(self, token: str) -> Optional[Contractor]:
        """
        Find contractor by COHF token.

        Args:
            token: COHF token

        Returns:
            Contractor if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_status(self, status: ContractorStatus) -> List[Contractor]:
        """
        Get all contractors with a specific status.

        Args:
            status: Contractor status to filter by

        Returns:
            List of contractors with the status
        """
        pass

    @abstractmethod
    async def get_by_route(self, route: OnboardingRoute) -> List[Contractor]:
        """
        Get all contractors on a specific onboarding route.

        Args:
            route: Onboarding route to filter by

        Returns:
            List of contractors on the route
        """
        pass

    @abstractmethod
    async def get_active(self) -> List[Contractor]:
        """
        Get all active contractors.

        Returns:
            List of active contractors
        """
        pass

    @abstractmethod
    async def get_pending_review(self) -> List[Contractor]:
        """
        Get contractors pending admin review.

        Returns:
            List of contractors awaiting review
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        route: Optional[str] = None,
        client_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Contractor], int]:
        """
        Search contractors with filters.

        Args:
            query: Search term (name or email)
            status: Filter by status
            route: Filter by onboarding route
            client_id: Filter by client
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (contractors list, total count)
        """
        pass

    @abstractmethod
    async def get_by_client(self, client_id: int) -> List[Contractor]:
        """
        Get all contractors for a specific client.

        Args:
            client_id: Client ID

        Returns:
            List of contractors assigned to the client
        """
        pass

    @abstractmethod
    async def get_expiring_tokens(self, hours: int = 24) -> List[Contractor]:
        """
        Get contractors with tokens expiring within the specified hours.

        Args:
            hours: Hours until expiry

        Returns:
            List of contractors with expiring tokens
        """
        pass
