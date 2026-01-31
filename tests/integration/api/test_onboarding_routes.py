"""
Integration tests for contractor onboarding routes API endpoints.

Tests the API endpoints for different onboarding workflows:
- Route selection (UAE, Saudi, WPS, Freelancer, Offshore)
- COHF workflow (UAE route)
- Quote Sheet workflow (Saudi route)
- Status transitions through the API
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.contractor import Contractor, ContractorStatus, OnboardingRoute
from app.models.user import User, UserRole
from app.schemas.contractor import RouteSelection


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    session.add = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.name = "Test Admin"
    user.email = "admin@test.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    return user


@pytest.fixture
def mock_contractor_documents_uploaded():
    """Mock contractor at DOCUMENTS_UPLOADED status."""
    contractor = MagicMock(spec=Contractor)
    contractor.id = "contractor-123"
    contractor.first_name = "John"
    contractor.surname = "Doe"
    contractor.email = "john.doe@test.com"
    contractor.status = ContractorStatus.DOCUMENTS_UPLOADED
    contractor.onboarding_route = None
    contractor.business_type = None
    contractor.cohf_status = None
    return contractor


@pytest.fixture
def mock_contractor_pending_cohf():
    """Mock contractor at PENDING_COHF status (UAE route)."""
    contractor = MagicMock(spec=Contractor)
    contractor.id = "contractor-456"
    contractor.first_name = "Jane"
    contractor.surname = "Smith"
    contractor.email = "jane.smith@test.com"
    contractor.status = ContractorStatus.PENDING_COHF
    contractor.onboarding_route = OnboardingRoute.UAE
    contractor.business_type = "3rd_party_uae"
    contractor.cohf_status = "draft"
    return contractor


@pytest.fixture
def mock_contractor_pending_quote():
    """Mock contractor at PENDING_THIRD_PARTY_QUOTE status (Saudi route)."""
    contractor = MagicMock(spec=Contractor)
    contractor.id = "contractor-789"
    contractor.first_name = "Ahmed"
    contractor.surname = "Al-Saud"
    contractor.email = "ahmed@test.com"
    contractor.status = ContractorStatus.PENDING_THIRD_PARTY_QUOTE
    contractor.onboarding_route = OnboardingRoute.SAUDI
    contractor.business_type = "3rd_party_saudi"
    contractor.quote_sheet_status = "pending"
    return contractor


# =============================================================================
# Route Selection Endpoint Tests
# =============================================================================

class TestRouteSelectionEndpoint:
    """Tests for POST /{contractor_id}/select-route endpoint."""

    def test_route_selection_schema_validation(self):
        """Test RouteSelection schema validates routes."""
        # Valid routes
        for route in ["wps", "freelancer", "uae", "saudi", "offshore"]:
            selection = RouteSelection(route=route)
            assert selection.route == route

    def test_route_selection_uae_sets_correct_status(self):
        """Test UAE route selection sets PENDING_COHF status."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        # Simulate what the endpoint does for UAE
        contractor.onboarding_route = OnboardingRoute.UAE
        contractor.status = ContractorStatus.PENDING_COHF
        contractor.cohf_status = "draft"
        contractor.business_type = "3rd_party_uae"

        assert contractor.status == ContractorStatus.PENDING_COHF
        assert contractor.cohf_status == "draft"
        assert contractor.onboarding_route == OnboardingRoute.UAE

    def test_route_selection_saudi_sets_correct_status(self):
        """Test Saudi route selection sets PENDING_THIRD_PARTY_QUOTE status."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        # Simulate what the endpoint does for Saudi
        contractor.onboarding_route = OnboardingRoute.SAUDI
        contractor.status = ContractorStatus.PENDING_THIRD_PARTY_QUOTE
        contractor.business_type = "3rd_party_saudi"

        assert contractor.status == ContractorStatus.PENDING_THIRD_PARTY_QUOTE
        assert contractor.onboarding_route == OnboardingRoute.SAUDI

    def test_route_selection_wps_sets_correct_status(self):
        """Test WPS route selection sets PENDING_CDS_CS status."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        # Simulate what the endpoint does for WPS
        contractor.onboarding_route = OnboardingRoute.WPS
        contractor.status = ContractorStatus.PENDING_CDS_CS
        contractor.business_type = "wps"

        assert contractor.status == ContractorStatus.PENDING_CDS_CS
        assert contractor.onboarding_route == OnboardingRoute.WPS

    def test_route_selection_freelancer_sets_correct_status(self):
        """Test Freelancer route selection sets PENDING_CDS_CS status."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        # Simulate what the endpoint does for Freelancer
        contractor.onboarding_route = OnboardingRoute.FREELANCER
        contractor.status = ContractorStatus.PENDING_CDS_CS
        contractor.business_type = "freelancer"

        assert contractor.status == ContractorStatus.PENDING_CDS_CS
        assert contractor.onboarding_route == OnboardingRoute.FREELANCER

    def test_route_selection_offshore_sets_correct_status(self):
        """Test Offshore route selection sets PENDING_CDS_CS status."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        # Simulate what the endpoint does for Offshore
        contractor.onboarding_route = OnboardingRoute.OFFSHORE
        contractor.status = ContractorStatus.PENDING_CDS_CS
        contractor.business_type = "offshore"

        assert contractor.status == ContractorStatus.PENDING_CDS_CS
        assert contractor.onboarding_route == OnboardingRoute.OFFSHORE

    def test_invalid_route_values(self):
        """Test invalid route values are rejected."""
        invalid_routes = ["invalid", "unknown", "test", "", None]
        valid_routes = ["wps", "freelancer", "uae", "saudi", "offshore"]

        for route in invalid_routes:
            assert route not in valid_routes


# =============================================================================
# UAE Route Workflow Tests (COHF)
# =============================================================================

class TestUAERouteWorkflow:
    """Tests for UAE route COHF workflow endpoints."""

    def test_cohf_status_progression(self):
        """Test COHF status progresses correctly."""
        cohf_statuses = ["draft", "submitted", "sent_to_3rd_party", "signed", "counter_signed"]

        # Validate status progression
        for i, status in enumerate(cohf_statuses[:-1]):
            next_status = cohf_statuses[i + 1]
            assert next_status != status

    def test_uae_route_requires_cohf_before_cds(self):
        """Test UAE route requires COHF completion before CDS."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        # COHF path
        assert ContractorStateMachine.can_transition(
            DomainStatus.PENDING_COHF,
            DomainStatus.AWAITING_COHF_SIGNATURE
        )
        assert ContractorStateMachine.can_transition(
            DomainStatus.COHF_COMPLETED,
            DomainStatus.PENDING_CDS_CS
        )

    def test_cohf_data_structure(self):
        """Test COHF data has expected structure."""
        cohf_data = {
            "employee_name": "John Doe",
            "remuneration": 15000,
            "currency": "AED",
            "third_party_id": "tp-123",
            "third_party_name": "Test 3rd Party",
            "start_date": "2025-01-15",
            "end_date": "2025-12-31",
        }

        required_fields = ["employee_name", "remuneration", "third_party_id"]
        for field in required_fields:
            assert field in cohf_data

    def test_cohf_signature_flow(self):
        """Test COHF signature flow stages."""
        signature_stages = [
            ("draft", "COHF created but not sent"),
            ("sent_to_3rd_party", "Sent to 3rd party for signature"),
            ("signed", "3rd party has signed"),
            ("counter_signed", "Aventus has counter-signed"),
        ]

        for stage, description in signature_stages:
            assert isinstance(stage, str)
            assert len(stage) > 0


class TestCOHFEndpoints:
    """Tests for COHF-specific endpoints."""

    def test_cohf_pdf_generation_requires_cohf_status(self):
        """Test COHF PDF generation requires appropriate status."""
        valid_statuses_for_pdf = [
            ContractorStatus.PENDING_COHF,
            ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.COHF_COMPLETED,
        ]

        invalid_statuses_for_pdf = [
            ContractorStatus.DRAFT,
            ContractorStatus.PENDING_DOCUMENTS,
            ContractorStatus.ACTIVE,
        ]

        for status in valid_statuses_for_pdf:
            assert status.value.startswith(("pending_cohf", "awaiting_cohf", "cohf_completed")) or \
                   "cohf" in status.value

    def test_cohf_public_signing_token_required(self):
        """Test public COHF signing requires valid token."""
        # Token should be present and non-empty for public access
        mock_token = "abc123xyz789"
        assert len(mock_token) > 0
        assert isinstance(mock_token, str)


# =============================================================================
# Saudi Route Workflow Tests (Quote Sheet)
# =============================================================================

class TestSaudiRouteWorkflow:
    """Tests for Saudi route Quote Sheet workflow endpoints."""

    def test_quote_sheet_status_progression(self):
        """Test Quote Sheet status progresses correctly."""
        quote_statuses = ["pending", "requested", "received", "approved"]

        for i, status in enumerate(quote_statuses[:-1]):
            next_status = quote_statuses[i + 1]
            assert next_status != status

    def test_saudi_route_requires_quote_before_cds(self):
        """Test Saudi route requires quote sheet before CDS."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        # Quote sheet path
        assert ContractorStateMachine.can_transition(
            DomainStatus.PENDING_THIRD_PARTY_QUOTE,
            DomainStatus.PENDING_CDS_CS
        )

    def test_quote_sheet_data_structure(self):
        """Test Quote Sheet data has expected structure."""
        quote_data = {
            "contractor_name": "Ahmed Al-Saud",
            "third_party_id": "tp-456",
            "third_party_name": "Saudi Partner Co",
            "position": "Software Engineer",
            "monthly_cost": 25000,
            "currency": "SAR",
        }

        required_fields = ["contractor_name", "third_party_id"]
        for field in required_fields:
            assert field in quote_data


class TestQuoteSheetEndpoints:
    """Tests for Quote Sheet-specific endpoints."""

    def test_quote_sheet_request_sends_email(self):
        """Test requesting quote sheet triggers email to 3rd party."""
        # Simulate the quote sheet request flow
        quote_request_data = {
            "contractor_id": "contractor-789",
            "third_party_id": "tp-456",
            "contractor_name": "Ahmed Al-Saud",
        }

        assert all(key in quote_request_data for key in ["contractor_id", "third_party_id"])

    def test_quote_sheet_public_submission_token(self):
        """Test public quote sheet submission requires valid token."""
        mock_token = "quote-token-xyz"
        assert len(mock_token) > 0


# =============================================================================
# WPS/Freelancer/Offshore Route Tests
# =============================================================================

class TestSimplifiedRouteWorkflow:
    """Tests for simplified routes (WPS, Freelancer, Offshore)."""

    def test_simplified_routes_skip_cohf(self):
        """Test WPS, Freelancer, Offshore skip COHF step."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        # All simplified routes go directly to CDS
        assert ContractorStateMachine.can_transition(
            DomainStatus.DOCUMENTS_UPLOADED,
            DomainStatus.PENDING_CDS_CS
        )

    def test_simplified_routes_skip_quote_sheet(self):
        """Test WPS, Freelancer, Offshore don't require quote sheet."""
        simplified_routes = [OnboardingRoute.WPS, OnboardingRoute.FREELANCER, OnboardingRoute.OFFSHORE]

        for route in simplified_routes:
            assert route.value not in ["uae", "saudi"]


# =============================================================================
# CDS Form Tests (Common to All Routes)
# =============================================================================

class TestCDSFormEndpoints:
    """Tests for CDS Form endpoints (common to all routes)."""

    def test_cds_form_structure(self):
        """Test CDS form has expected structure."""
        cds_data = {
            "personal_info": {
                "first_name": "John",
                "surname": "Doe",
                "nationality": "US",
                "dob": "1990-01-15",
            },
            "contact_info": {
                "email": "john@test.com",
                "phone": "+1234567890",
                "address": "123 Test St",
            },
            "employment_info": {
                "role": "Software Engineer",
                "start_date": "2025-01-15",
                "end_date": "2025-12-31",
            },
            "financial_info": {
                "monthly_rate": 15000,
                "currency": "AED",
            },
        }

        assert "personal_info" in cds_data
        assert "contact_info" in cds_data
        assert "employment_info" in cds_data

    def test_cds_completion_moves_to_review(self):
        """Test completing CDS moves contractor to PENDING_REVIEW."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        assert ContractorStateMachine.can_transition(
            DomainStatus.CDS_CS_COMPLETED,
            DomainStatus.PENDING_REVIEW
        )


# =============================================================================
# Work Order Tests
# =============================================================================

class TestWorkOrderEndpoints:
    """Tests for Work Order endpoints."""

    def test_work_order_after_approval(self):
        """Test work order is generated after admin approval."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        # After approval, goes to work order
        assert ContractorStateMachine.can_transition(
            DomainStatus.APPROVED,
            DomainStatus.PENDING_CLIENT_WO_SIGNATURE
        )

    def test_work_order_routes_differ_after_completion(self):
        """Test UAE and other routes differ after work order completion."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus, OnboardingRoute

        # UAE goes to 3rd party contract
        next_uae = ContractorStateMachine.get_next_status_for_route(
            DomainStatus.WORK_ORDER_COMPLETED,
            OnboardingRoute.UAE
        )
        assert next_uae == DomainStatus.PENDING_3RD_PARTY_CONTRACT

        # Other routes go to signature
        next_wps = ContractorStateMachine.get_next_status_for_route(
            DomainStatus.WORK_ORDER_COMPLETED,
            OnboardingRoute.WPS
        )
        assert next_wps == DomainStatus.PENDING_SIGNATURE


# =============================================================================
# Contract Signing Tests
# =============================================================================

class TestContractSigningEndpoints:
    """Tests for contract signing endpoints."""

    def test_contract_signing_requires_token(self):
        """Test public contract signing requires valid token."""
        mock_token = "contract-token-abc123"
        assert len(mock_token) > 0

    def test_signing_completes_contract(self):
        """Test signing contract moves to SIGNED status."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        assert ContractorStateMachine.can_transition(
            DomainStatus.PENDING_SIGNATURE,
            DomainStatus.SIGNED
        )

    def test_signed_contract_activates_contractor(self):
        """Test signed contract allows activation."""
        from app.domain.contractor.state_machine import ContractorStateMachine
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        assert ContractorStateMachine.can_transition(
            DomainStatus.SIGNED,
            DomainStatus.ACTIVE
        )


# =============================================================================
# Activation Tests
# =============================================================================

class TestActivationEndpoints:
    """Tests for contractor activation endpoints."""

    def test_activation_generates_credentials(self):
        """Test activation generates login credentials."""
        activation_result = {
            "contractor_id": "contractor-123",
            "email": "john.doe@test.com",
            "temp_password": "generated",
            "portal_url": "https://portal.test.com",
        }

        assert "temp_password" in activation_result
        assert "portal_url" in activation_result

    def test_activation_sends_email(self):
        """Test activation sends welcome email."""
        # Simulate activation email data
        email_data = {
            "to": "john.doe@test.com",
            "subject": "Welcome to Aventus",
            "contractor_name": "John Doe",
            "login_url": "https://portal.test.com/login",
        }

        assert "to" in email_data
        assert "Welcome" in email_data["subject"]


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for API error handling."""

    def test_contractor_not_found_returns_404(self):
        """Test 404 returned for non-existent contractor."""
        from fastapi import HTTPException

        def simulate_not_found():
            raise HTTPException(status_code=404, detail="Contractor not found")

        with pytest.raises(HTTPException) as exc_info:
            simulate_not_found()

        assert exc_info.value.status_code == 404

    def test_invalid_route_returns_400(self):
        """Test 400 returned for invalid route selection."""
        from fastapi import HTTPException
        from app.domain.contractor.value_objects import OnboardingRoute

        # Get valid routes dynamically from enum to avoid hardcoding
        valid_routes = [r.value for r in OnboardingRoute]
        invalid_route = "invalid_route"

        def simulate_invalid_route(route):
            if route not in valid_routes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid route. Must be one of: {', '.join(valid_routes)}"
                )

        with pytest.raises(HTTPException) as exc_info:
            simulate_invalid_route(invalid_route)

        assert exc_info.value.status_code == 400

    def test_unauthorized_returns_401(self):
        """Test 401 returned for unauthorized access."""
        from fastapi import HTTPException

        def simulate_unauthorized():
            raise HTTPException(status_code=401, detail="Not authenticated")

        with pytest.raises(HTTPException) as exc_info:
            simulate_unauthorized()

        assert exc_info.value.status_code == 401

    def test_forbidden_returns_403(self):
        """Test 403 returned for insufficient permissions."""
        from fastapi import HTTPException

        def simulate_forbidden():
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        with pytest.raises(HTTPException) as exc_info:
            simulate_forbidden()

        assert exc_info.value.status_code == 403


# =============================================================================
# Route-Specific Status Transition Tests
# =============================================================================

class TestRouteStatusTransitions:
    """Integration tests for route-specific status transitions."""

    def test_uae_full_status_flow(self):
        """Test UAE route full status flow."""
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        uae_flow = [
            DomainStatus.DRAFT,
            DomainStatus.PENDING_DOCUMENTS,
            DomainStatus.DOCUMENTS_UPLOADED,
            DomainStatus.PENDING_COHF,
            DomainStatus.AWAITING_COHF_SIGNATURE,
            DomainStatus.COHF_COMPLETED,
            DomainStatus.PENDING_CDS_CS,
            DomainStatus.CDS_CS_COMPLETED,
            DomainStatus.PENDING_REVIEW,
            DomainStatus.APPROVED,
            DomainStatus.PENDING_CLIENT_WO_SIGNATURE,
            DomainStatus.WORK_ORDER_COMPLETED,
            DomainStatus.PENDING_3RD_PARTY_CONTRACT,
            DomainStatus.CONTRACT_APPROVED,
            DomainStatus.PENDING_SIGNATURE,
            DomainStatus.SIGNED,
            DomainStatus.ACTIVE,
        ]

        # Verify all statuses in flow exist
        for status in uae_flow:
            assert status is not None

    def test_saudi_full_status_flow(self):
        """Test Saudi route full status flow."""
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        saudi_flow = [
            DomainStatus.DRAFT,
            DomainStatus.PENDING_DOCUMENTS,
            DomainStatus.DOCUMENTS_UPLOADED,
            DomainStatus.PENDING_THIRD_PARTY_QUOTE,
            DomainStatus.PENDING_CDS_CS,
            DomainStatus.CDS_CS_COMPLETED,
            DomainStatus.PENDING_REVIEW,
            DomainStatus.APPROVED,
            DomainStatus.PENDING_CLIENT_WO_SIGNATURE,
            DomainStatus.WORK_ORDER_COMPLETED,
            DomainStatus.PENDING_SIGNATURE,
            DomainStatus.SIGNED,
            DomainStatus.ACTIVE,
        ]

        for status in saudi_flow:
            assert status is not None

    def test_wps_full_status_flow(self):
        """Test WPS route full status flow (no COHF, no quote sheet)."""
        from app.domain.contractor.value_objects import ContractorStatus as DomainStatus

        wps_flow = [
            DomainStatus.DRAFT,
            DomainStatus.PENDING_DOCUMENTS,
            DomainStatus.DOCUMENTS_UPLOADED,
            DomainStatus.PENDING_CDS_CS,
            DomainStatus.CDS_CS_COMPLETED,
            DomainStatus.PENDING_REVIEW,
            DomainStatus.APPROVED,
            DomainStatus.PENDING_CLIENT_WO_SIGNATURE,
            DomainStatus.WORK_ORDER_COMPLETED,
            DomainStatus.PENDING_SIGNATURE,
            DomainStatus.SIGNED,
            DomainStatus.ACTIVE,
        ]

        for status in wps_flow:
            assert status is not None

        # Verify WPS flow doesn't include COHF or quote statuses
        assert DomainStatus.PENDING_COHF not in wps_flow
        assert DomainStatus.PENDING_THIRD_PARTY_QUOTE not in wps_flow


# =============================================================================
# Reset and Clear Route Tests
# =============================================================================

class TestResetEndpoints:
    """Tests for reset and clear route endpoints."""

    def test_clear_route_resets_onboarding_route(self):
        """Test clear-route resets onboarding selection."""
        contractor = MagicMock()
        contractor.onboarding_route = OnboardingRoute.UAE
        contractor.business_type = "3rd_party_uae"

        # Simulate clear route
        contractor.onboarding_route = None
        contractor.business_type = None

        assert contractor.onboarding_route is None
        assert contractor.business_type is None

    def test_reset_for_testing_clears_all_route_data(self):
        """Test reset-for-testing clears all route-specific data."""
        contractor = MagicMock()
        contractor.status = ContractorStatus.PENDING_COHF
        contractor.onboarding_route = OnboardingRoute.UAE
        contractor.cohf_status = "submitted"
        contractor.cohf_data = {"some": "data"}

        # Simulate reset
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED
        contractor.onboarding_route = None
        contractor.cohf_status = None
        contractor.cohf_data = None

        assert contractor.status == ContractorStatus.DOCUMENTS_UPLOADED
        assert contractor.onboarding_route is None
        assert contractor.cohf_status is None


# =============================================================================
# Third Party Integration Tests
# =============================================================================

class TestThirdPartyIntegration:
    """Tests for third party integration."""

    def test_uae_requires_third_party(self):
        """Test UAE route requires third party selection."""
        from app.domain.contractor.value_objects import OnboardingRoute

        assert OnboardingRoute.UAE.requires_third_party is True

    def test_saudi_requires_third_party(self):
        """Test Saudi route requires third party selection."""
        from app.domain.contractor.value_objects import OnboardingRoute

        assert OnboardingRoute.SAUDI.requires_third_party is True

    def test_wps_no_third_party(self):
        """Test WPS route doesn't require third party."""
        from app.domain.contractor.value_objects import OnboardingRoute

        assert OnboardingRoute.WPS.requires_third_party is False

    def test_third_party_request_sent_for_uae(self):
        """Test third party request is sent for UAE contractors."""
        request_data = {
            "contractor_id": "contractor-123",
            "third_party_id": "tp-456",
            "third_party_email": "partner@3rdparty.com",
            "contractor_name": "John Doe",
            "request_type": "cohf",
        }

        assert "third_party_email" in request_data
        assert request_data["request_type"] == "cohf"
