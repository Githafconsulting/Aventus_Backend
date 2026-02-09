"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


# =============================================================================
# Contractor Fixtures
# =============================================================================

@pytest.fixture
def sample_contractor_data():
    """Sample contractor data for testing."""
    return {
        "id": 1,
        "first_name": "John",
        "surname": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "status": "pending_documents",
        "nationality": "US",
        "gender": "male",
        "dob": "1990-01-15",
        "home_address": "123 Main St, City",
        "onboarding_route": "uae",
        "document_upload_token": "test-token-123",
        "document_upload_token_expiry": datetime.utcnow() + timedelta(days=7),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_contractor_create():
    """Sample contractor creation data."""
    return {
        "first_name": "Jane",
        "surname": "Smith",
        "email": "jane.smith@example.com",
        "phone": "+0987654321",
    }


@pytest.fixture
def mock_contractor(sample_contractor_data):
    """Mock contractor object."""
    contractor = MagicMock()
    for key, value in sample_contractor_data.items():
        setattr(contractor, key, value)
    return contractor


# =============================================================================
# Client Fixtures
# =============================================================================

@pytest.fixture
def sample_client_data():
    """Sample client data for testing."""
    return {
        "id": 1,
        "name": "Acme Corporation",
        "email": "contact@acme.com",
        "phone": "+1234567890",
        "address": "456 Business Ave",
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_client(sample_client_data):
    """Mock client object."""
    client = MagicMock()
    for key, value in sample_client_data.items():
        setattr(client, key, value)
    return client


# =============================================================================
# Email Fixtures
# =============================================================================

@pytest.fixture
def mock_email_sender():
    """Mock email sender."""
    from app.adapters.email.resend_adapter import MockEmailSender
    return MockEmailSender()


@pytest.fixture
def mock_template_engine():
    """Mock template engine."""
    engine = MagicMock()
    engine.render = MagicMock(return_value="<html>Test Email</html>")
    return engine


# =============================================================================
# Storage Fixtures
# =============================================================================

@pytest.fixture
def mock_storage():
    """Mock storage adapter."""
    from app.adapters.storage.supabase_adapter import InMemoryStorageAdapter
    return InMemoryStorageAdapter()


# =============================================================================
# Repository Fixtures
# =============================================================================

@pytest.fixture
def mock_contractor_repo(mock_db_session, mock_contractor):
    """Mock contractor repository."""
    repo = MagicMock()
    repo.get = AsyncMock(return_value=mock_contractor)
    repo.get_all = AsyncMock(return_value=[mock_contractor])
    repo.create = AsyncMock(return_value=mock_contractor)
    repo.update = AsyncMock(return_value=mock_contractor)
    repo.delete = AsyncMock(return_value=True)
    repo.get_by_token = AsyncMock(return_value=mock_contractor)
    repo.get_by_contract_token = AsyncMock(return_value=mock_contractor)
    repo.search = AsyncMock(return_value=([mock_contractor], 1))
    return repo


@pytest.fixture
def mock_client_repo(mock_db_session, mock_client):
    """Mock client repository."""
    repo = MagicMock()
    repo.get = AsyncMock(return_value=mock_client)
    repo.get_all = AsyncMock(return_value=[mock_client])
    repo.create = AsyncMock(return_value=mock_client)
    repo.update = AsyncMock(return_value=mock_client)
    repo.delete = AsyncMock(return_value=True)
    return repo


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def contractor_service(mock_contractor_repo):
    """Contractor service with mocked repo."""
    from app.services.contractor_service import ContractorService
    return ContractorService(mock_contractor_repo)


@pytest.fixture
def notification_service():
    """Notification service instance."""
    from app.services.notification_service import NotificationService
    return NotificationService()


# =============================================================================
# Token Fixtures
# =============================================================================

@pytest.fixture
def valid_token():
    """Valid token data."""
    return {
        "value": "valid-test-token-12345",
        "expiry": datetime.utcnow() + timedelta(hours=48),
    }


@pytest.fixture
def expired_token():
    """Expired token data."""
    return {
        "value": "expired-test-token-12345",
        "expiry": datetime.utcnow() - timedelta(hours=1),
    }


# =============================================================================
# PDF Fixtures
# =============================================================================

@pytest.fixture
def sample_pdf_data():
    """Sample data for PDF generation."""
    return {
        "contractor_name": "John Doe",
        "client_name": "Acme Corp",
        "role": "Software Engineer",
        "start_date": "2025-01-15",
        "end_date": "2025-12-31",
        "salary": "10000",
        "currency": "USD",
    }
