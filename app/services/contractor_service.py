"""
Contractor Service.

Application service for contractor management operations.
Orchestrates domain logic, repositories, and adapters.
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from app.repositories.implementations.contractor_repo import ContractorRepository
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.state_machine import ContractorStateMachine
from app.domain.contractor.exceptions import (
    ContractorNotFoundError,
    InvalidStatusTransitionError,
)
from app.domain.token.token import Token
from app.domain.onboarding.registry import OnboardingRegistry
from app.schemas.contractor import ContractorCreate, ContractorUpdate
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class ContractorService:
    """
    Application service for contractor management.

    Provides use cases for:
    - Creating and updating contractors
    - Managing contractor status transitions
    - Token management (document upload, contract signing)
    - Route selection and onboarding workflow
    """

    def __init__(self, repo: ContractorRepository):
        """
        Initialize contractor service.

        Args:
            repo: Contractor repository instance
        """
        self.repo = repo

    async def create_initial(self, data: ContractorCreate) -> Dict[str, Any]:
        """
        Create initial contractor record.

        Generates document upload token and prepares for onboarding.

        Args:
            data: Contractor creation data

        Returns:
            Dict with contractor, upload_token, and upload_expiry
        """
        # Generate document upload token (7 days validity)
        token = Token.generate(hours=168)

        contractor_data = {
            **data.model_dump(),
            "status": ContractorStatus.PENDING_DOCUMENTS.value,
            "document_upload_token": token.value,
            "document_upload_token_expiry": token.expiry,
        }

        contractor = await self.repo.create(contractor_data)

        logger.info(
            "Contractor created",
            extra={
                "contractor_id": contractor.id,
                "email": contractor.email,
                "status": contractor.status,
            }
        )

        return {
            "contractor": contractor,
            "upload_token": token.value,
            "upload_expiry": token.expiry,
        }

    async def get(self, id: int):
        """
        Get contractor by ID.

        Args:
            id: Contractor ID

        Returns:
            Contractor object

        Raises:
            ContractorNotFoundError: If not found
        """
        contractor = await self.repo.get(id)
        if not contractor:
            raise ContractorNotFoundError(f"Contractor {id} not found")
        return contractor

    async def get_by_token(self, token: str):
        """
        Get contractor by document upload token.

        Args:
            token: Document upload token

        Returns:
            Contractor object

        Raises:
            ContractorNotFoundError: If not found or expired
        """
        contractor = await self.repo.get_by_token(token)
        if not contractor:
            raise ContractorNotFoundError("Invalid or expired token")

        # Validate token hasn't expired
        if contractor.document_upload_token_expiry:
            token_obj = Token(token, contractor.document_upload_token_expiry)
            token_obj.validate()

        return contractor

    async def get_by_contract_token(self, token: str):
        """
        Get contractor by contract signing token.

        Args:
            token: Contract signing token

        Returns:
            Contractor object

        Raises:
            ContractorNotFoundError: If not found or expired
        """
        contractor = await self.repo.get_by_contract_token(token)
        if not contractor:
            raise ContractorNotFoundError("Invalid or expired contract token")

        # Validate token hasn't expired
        if contractor.contract_token_expiry:
            token_obj = Token(token, contractor.contract_token_expiry)
            token_obj.validate()

        return contractor

    async def update(self, id: int, data: ContractorUpdate):
        """
        Update contractor data.

        Args:
            id: Contractor ID
            data: Update data

        Returns:
            Updated contractor

        Raises:
            ContractorNotFoundError: If not found
        """
        contractor = await self.get(id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        updated = await self.repo.update(id, update_data)

        logger.info(
            "Contractor updated",
            extra={
                "contractor_id": id,
                "fields": list(update_data.keys()),
            }
        )

        return updated

    async def update_status(
        self,
        id: int,
        new_status: ContractorStatus,
    ):
        """
        Update contractor status with validation.

        Uses state machine to ensure valid transitions.

        Args:
            id: Contractor ID
            new_status: Target status

        Returns:
            Updated contractor

        Raises:
            InvalidStatusTransitionError: If transition not allowed
        """
        contractor = await self.get(id)
        current_status = ContractorStatus(contractor.status)

        # Validate transition using state machine
        ContractorStateMachine.transition(current_status, new_status)

        # Perform update
        updated = await self.repo.update(id, {
            "status": new_status.value,
            "updated_at": datetime.utcnow(),
        })

        logger.info(
            "Contractor status updated",
            extra={
                "contractor_id": id,
                "from_status": current_status.value,
                "to_status": new_status.value,
            }
        )

        return updated

    async def select_route(
        self,
        id: int,
        route: OnboardingRoute,
    ):
        """
        Select onboarding route for contractor.

        Args:
            id: Contractor ID
            route: Onboarding route to select

        Returns:
            Updated contractor

        Raises:
            InvalidStatusTransitionError: If route selection not allowed
        """
        contractor = await self.get(id)

        # Validate current status allows route selection
        if contractor.status != ContractorStatus.DOCUMENTS_UPLOADED.value:
            raise InvalidStatusTransitionError(
                "Route can only be selected after documents are uploaded"
            )

        # Get strategy to determine next status
        strategy = OnboardingRegistry.get(route.value)
        next_status = strategy.get_next_status(ContractorStatus.DOCUMENTS_UPLOADED)

        updated = await self.repo.update(id, {
            "onboarding_route": route.value,
            "status": next_status.value if next_status else contractor.status,
            "updated_at": datetime.utcnow(),
        })

        logger.info(
            "Onboarding route selected",
            extra={
                "contractor_id": id,
                "route": route.value,
                "next_status": next_status.value if next_status else "unchanged",
            }
        )

        return updated

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        route: Optional[str] = None,
        client_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List, int]:
        """
        Search contractors with pagination.

        Args:
            query: Search term
            status: Filter by status
            route: Filter by route
            client_id: Filter by client
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (contractors list, total count)
        """
        skip = (page - 1) * page_size
        return await self.repo.search(
            query=query,
            status=status,
            route=route,
            client_id=client_id,
            skip=skip,
            limit=page_size,
        )

    async def generate_contract_token(self, id: int) -> Dict[str, Any]:
        """
        Generate contract signing token.

        Args:
            id: Contractor ID

        Returns:
            Dict with token and expiry
        """
        contractor = await self.get(id)

        # Generate token (48 hours validity)
        token = Token.generate(hours=48)

        await self.repo.update(id, {
            "contract_token": token.value,
            "contract_token_expiry": token.expiry,
        })

        logger.info(
            "Contract token generated",
            extra={"contractor_id": id}
        )

        return {
            "token": token.value,
            "expiry": token.expiry,
        }

    async def mark_documents_uploaded(self, id: int):
        """
        Mark that contractor has uploaded their documents.

        Args:
            id: Contractor ID

        Returns:
            Updated contractor
        """
        return await self.update_status(id, ContractorStatus.DOCUMENTS_UPLOADED)

    async def get_pending_review(self) -> List:
        """Get all contractors pending admin review."""
        return await self.repo.get_pending_review()

    async def get_by_client(self, client_id: int) -> List:
        """Get all contractors for a client."""
        return await self.repo.get_by_client(client_id)

    async def get_statistics(self) -> dict:
        """Get contractor statistics."""
        return await self.repo.get_statistics()
