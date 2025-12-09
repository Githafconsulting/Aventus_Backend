"""
Unit tests for ContractorService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from app.services.contractor_service import ContractorService
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.exceptions import ContractorNotFoundError, InvalidStatusTransitionError
from app.schemas.contractor import ContractorCreate, ContractorUpdate


class TestContractorServiceGet:
    """Tests for ContractorService.get()."""

    @pytest.mark.asyncio
    async def test_get_existing_contractor(self, contractor_service, mock_contractor):
        """Test getting an existing contractor."""
        result = await contractor_service.get(1)
        assert result.id == mock_contractor.id
        assert result.email == mock_contractor.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_contractor_raises(self, mock_contractor_repo):
        """Test getting non-existent contractor raises error."""
        mock_contractor_repo.get = AsyncMock(return_value=None)
        service = ContractorService(mock_contractor_repo)

        with pytest.raises(ContractorNotFoundError):
            await service.get(999)


class TestContractorServiceCreate:
    """Tests for ContractorService.create_initial()."""

    @pytest.mark.asyncio
    async def test_create_initial_contractor(self, mock_contractor_repo, sample_contractor_create):
        """Test creating initial contractor."""
        mock_contractor = MagicMock()
        mock_contractor.id = 1
        mock_contractor.email = sample_contractor_create["email"]
        mock_contractor.status = "pending_documents"
        mock_contractor_repo.create = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)
        data = ContractorCreate(**sample_contractor_create)

        result = await service.create_initial(data)

        assert "contractor" in result
        assert "upload_token" in result
        assert "upload_expiry" in result
        assert result["upload_token"] is not None

    @pytest.mark.asyncio
    async def test_create_generates_upload_token(self, mock_contractor_repo, sample_contractor_create):
        """Test that create generates upload token."""
        mock_contractor = MagicMock()
        mock_contractor.id = 1
        mock_contractor_repo.create = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)
        data = ContractorCreate(**sample_contractor_create)

        result = await service.create_initial(data)

        assert len(result["upload_token"]) > 0
        assert result["upload_expiry"] > datetime.utcnow()


class TestContractorServiceUpdate:
    """Tests for ContractorService.update()."""

    @pytest.mark.asyncio
    async def test_update_contractor(self, contractor_service, mock_contractor_repo):
        """Test updating contractor."""
        update_data = ContractorUpdate(first_name="Updated")

        result = await contractor_service.update(1, update_data)

        mock_contractor_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self, mock_contractor_repo):
        """Test updating non-existent contractor raises error."""
        mock_contractor_repo.get = AsyncMock(return_value=None)
        service = ContractorService(mock_contractor_repo)

        with pytest.raises(ContractorNotFoundError):
            await service.update(999, ContractorUpdate(first_name="Test"))


class TestContractorServiceStatus:
    """Tests for ContractorService.update_status()."""

    @pytest.mark.asyncio
    async def test_valid_status_transition(self, mock_contractor_repo, mock_contractor):
        """Test valid status transition."""
        mock_contractor.status = "pending_documents"
        mock_contractor_repo.get = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)

        await service.update_status(1, ContractorStatus.DOCUMENTS_UPLOADED)

        mock_contractor_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_status_transition_raises(self, mock_contractor_repo, mock_contractor):
        """Test invalid status transition raises error."""
        mock_contractor.status = "draft"
        mock_contractor_repo.get = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)

        with pytest.raises(InvalidStatusTransitionError):
            await service.update_status(1, ContractorStatus.ACTIVE)


class TestContractorServiceToken:
    """Tests for token-related methods."""

    @pytest.mark.asyncio
    async def test_get_by_token(self, contractor_service, mock_contractor):
        """Test getting contractor by token."""
        result = await contractor_service.get_by_token("test-token-123")
        assert result.id == mock_contractor.id

    @pytest.mark.asyncio
    async def test_get_by_invalid_token_raises(self, mock_contractor_repo):
        """Test getting by invalid token raises error."""
        mock_contractor_repo.get_by_token = AsyncMock(return_value=None)
        service = ContractorService(mock_contractor_repo)

        with pytest.raises(ContractorNotFoundError):
            await service.get_by_token("invalid-token")

    @pytest.mark.asyncio
    async def test_generate_contract_token(self, contractor_service, mock_contractor_repo):
        """Test generating contract token."""
        result = await contractor_service.generate_contract_token(1)

        assert "token" in result
        assert "expiry" in result
        assert len(result["token"]) > 0
        mock_contractor_repo.update.assert_called()


class TestContractorServiceSearch:
    """Tests for ContractorService.search()."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, contractor_service, mock_contractor):
        """Test search returns results."""
        results, total = await contractor_service.search(query="John")

        assert len(results) > 0
        assert total >= 1

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, contractor_service):
        """Test search with status filter."""
        results, total = await contractor_service.search(status="pending_documents")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_pagination(self, contractor_service):
        """Test search pagination."""
        results, total = await contractor_service.search(page=1, page_size=10)

        assert isinstance(results, list)


class TestContractorServiceRouteSelection:
    """Tests for route selection."""

    @pytest.mark.asyncio
    async def test_select_route(self, mock_contractor_repo, mock_contractor):
        """Test selecting onboarding route."""
        mock_contractor.status = "documents_uploaded"
        mock_contractor_repo.get = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)

        await service.select_route(1, OnboardingRoute.UAE)

        mock_contractor_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_route_wrong_status_raises(self, mock_contractor_repo, mock_contractor):
        """Test selecting route at wrong status raises error."""
        mock_contractor.status = "draft"
        mock_contractor_repo.get = AsyncMock(return_value=mock_contractor)

        service = ContractorService(mock_contractor_repo)

        with pytest.raises(InvalidStatusTransitionError):
            await service.select_route(1, OnboardingRoute.UAE)
