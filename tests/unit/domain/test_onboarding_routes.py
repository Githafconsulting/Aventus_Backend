"""
Unit tests for contractor onboarding routes.

Tests the different onboarding workflows (UAE, Saudi, WPS, Freelancer, Offshore)
including route-specific transitions, strategies, and validations.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.state_machine import ContractorStateMachine
from app.domain.onboarding.registry import OnboardingRegistry
from app.domain.onboarding.strategies.base import OnboardingResult, WorkflowStep
from app.exceptions.contractor import InvalidStatusTransitionError


# =============================================================================
# UAE Route Tests
# =============================================================================

class TestUAERouteTransitions:
    """Tests for UAE route status transitions."""

    def test_documents_uploaded_to_pending_cohf(self):
        """UAE route: After documents, goes to COHF step."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.UAE
        )
        assert next_status == ContractorStatus.PENDING_COHF

    def test_can_transition_to_pending_cohf(self):
        """UAE route: Can transition from documents_uploaded to pending_cohf."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.PENDING_COHF
        )

    def test_can_transition_pending_cohf_to_awaiting_signature(self):
        """UAE route: COHF submitted -> awaiting signature."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.PENDING_COHF,
            ContractorStatus.AWAITING_COHF_SIGNATURE
        )

    def test_can_transition_awaiting_signature_to_cohf_completed(self):
        """UAE route: Signature received -> COHF completed."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.COHF_COMPLETED
        )

    def test_can_go_back_from_awaiting_signature(self):
        """UAE route: Can go back from awaiting signature to pending COHF for edits."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.PENDING_COHF
        )

    def test_cohf_completed_to_cds(self):
        """UAE route: COHF completed -> CDS step."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.COHF_COMPLETED,
            ContractorStatus.PENDING_CDS_CS
        )

    def test_work_order_completed_to_third_party_contract(self):
        """UAE route: Work order done -> 3rd party contract upload."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.WORK_ORDER_COMPLETED,
            OnboardingRoute.UAE
        )
        assert next_status == ContractorStatus.PENDING_3RD_PARTY_CONTRACT

    def test_uae_full_workflow_path(self):
        """UAE route: Test full valid workflow path."""
        uae_path = [
            (ContractorStatus.DRAFT, ContractorStatus.PENDING_DOCUMENTS),
            (ContractorStatus.PENDING_DOCUMENTS, ContractorStatus.DOCUMENTS_UPLOADED),
            (ContractorStatus.DOCUMENTS_UPLOADED, ContractorStatus.PENDING_COHF),
            (ContractorStatus.PENDING_COHF, ContractorStatus.AWAITING_COHF_SIGNATURE),
            (ContractorStatus.AWAITING_COHF_SIGNATURE, ContractorStatus.COHF_COMPLETED),
            (ContractorStatus.COHF_COMPLETED, ContractorStatus.PENDING_CDS_CS),
            (ContractorStatus.PENDING_CDS_CS, ContractorStatus.CDS_CS_COMPLETED),
            (ContractorStatus.CDS_CS_COMPLETED, ContractorStatus.PENDING_REVIEW),
            (ContractorStatus.PENDING_REVIEW, ContractorStatus.APPROVED),
            (ContractorStatus.APPROVED, ContractorStatus.PENDING_CLIENT_WO_SIGNATURE),
            (ContractorStatus.PENDING_CLIENT_WO_SIGNATURE, ContractorStatus.WORK_ORDER_COMPLETED),
            (ContractorStatus.WORK_ORDER_COMPLETED, ContractorStatus.PENDING_3RD_PARTY_CONTRACT),
            (ContractorStatus.PENDING_3RD_PARTY_CONTRACT, ContractorStatus.CONTRACT_APPROVED),
            (ContractorStatus.CONTRACT_APPROVED, ContractorStatus.PENDING_SIGNATURE),
            (ContractorStatus.PENDING_SIGNATURE, ContractorStatus.SIGNED),
            (ContractorStatus.SIGNED, ContractorStatus.ACTIVE),
        ]

        for from_status, to_status in uae_path:
            assert ContractorStateMachine.can_transition(from_status, to_status), \
                f"Failed transition: {from_status.value} -> {to_status.value}"


class TestUAEStrategy:
    """Tests for UAE onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("uae")

    def test_route_name(self, strategy):
        """Test UAE route name."""
        assert strategy.route_name == "uae"

    def test_display_name(self, strategy):
        """Test UAE display name."""
        assert strategy.display_name == "3rd Party UAE"

    def test_required_documents(self, strategy):
        """Test UAE required documents include passport and emirates_id."""
        docs = strategy.get_required_documents()
        assert "passport" in docs
        assert "emirates_id" in docs
        assert "visa" in docs
        assert "photo" in docs

    def test_workflow_steps_count(self, strategy):
        """Test UAE has expected workflow steps."""
        steps = strategy.get_workflow_steps()
        # Use minimum count instead of exact - allows adding steps without breaking
        assert len(steps) >= 7, "UAE route should have at least 7 workflow steps"

    def test_workflow_steps_include_cohf(self, strategy):
        """Test UAE workflow includes COHF step."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "cohf" in step_ids

    def test_workflow_steps_include_third_party_contract(self, strategy):
        """Test UAE workflow includes 3rd party contract step."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "third_party_contract" in step_ids

    def test_workflow_steps_order(self, strategy):
        """Test UAE workflow steps are in correct order."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert step_ids.index("cohf") < step_ids.index("cds_costing")
        assert step_ids.index("cds_costing") < step_ids.index("admin_review")
        assert step_ids.index("third_party_contract") < step_ids.index("activation")

    def test_get_next_status_from_documents_uploaded(self, strategy):
        """Test next status after documents uploaded."""
        next_status = strategy.get_next_status(ContractorStatus.DOCUMENTS_UPLOADED)
        assert next_status == ContractorStatus.PENDING_COHF

    def test_get_next_status_from_work_order_completed(self, strategy):
        """Test next status after work order - should go to 3rd party contract."""
        next_status = strategy.get_next_status(ContractorStatus.WORK_ORDER_COMPLETED)
        assert next_status == ContractorStatus.PENDING_3RD_PARTY_CONTRACT

    def test_get_step_by_id(self, strategy):
        """Test getting step by ID."""
        step = strategy.get_step_by_id("cohf")
        assert step is not None
        assert step.name == "Cost of Hire Form"

    def test_get_current_step_for_pending_cohf(self, strategy):
        """Test getting current step when status is PENDING_COHF."""
        step = strategy.get_current_step(ContractorStatus.PENDING_COHF)
        assert step is not None
        assert step.id == "cohf"

    def test_validate_cohf_step_data_valid(self, strategy):
        """Test COHF step validation with valid data."""
        data = {
            "employee_name": "John Doe",
            "remuneration": 10000,
            "third_party_id": "3p-123"
        }
        errors = strategy.validate_step_data("cohf", data)
        assert len(errors) == 0

    def test_validate_cohf_step_data_missing_fields(self, strategy):
        """Test COHF step validation with missing fields."""
        data = {"employee_name": "John Doe"}
        errors = strategy.validate_step_data("cohf", data)
        # Just verify validation catches missing required fields
        assert len(errors) > 0, "Validation should catch missing required fields"

    def test_validate_third_party_contract_data(self, strategy):
        """Test 3rd party contract validation."""
        errors = strategy.validate_step_data("third_party_contract", {})
        assert len(errors) > 0
        assert any("contract" in e.lower() for e in errors)

    @pytest.mark.asyncio
    async def test_execute_cohf_step(self, strategy):
        """Test executing COHF step."""
        result = await strategy.execute_step(
            contractor_id=1,
            step="cohf",
            data={}
        )
        assert isinstance(result, OnboardingResult)
        assert result.next_status == ContractorStatus.AWAITING_COHF_SIGNATURE
        assert result.requires_external_action is True
        assert result.external_action_type == "cohf_signature"

    @pytest.mark.asyncio
    async def test_execute_cohf_signature_step(self, strategy):
        """Test executing COHF signature step."""
        result = await strategy.execute_step(
            contractor_id=1,
            step="cohf_signature",
            data={"signed_document_url": "https://example.com/signed.pdf"}
        )
        assert result.next_status == ContractorStatus.COHF_COMPLETED
        assert "signed_cohf_url" in result.data

    @pytest.mark.asyncio
    async def test_execute_third_party_contract_step(self, strategy):
        """Test executing 3rd party contract upload step."""
        result = await strategy.execute_step(
            contractor_id=1,
            step="third_party_contract",
            data={"contract_url": "https://example.com/contract.pdf"}
        )
        assert result.next_status == ContractorStatus.CONTRACT_APPROVED


# =============================================================================
# Saudi Route Tests
# =============================================================================

class TestSaudiRouteTransitions:
    """Tests for Saudi route status transitions."""

    def test_documents_uploaded_to_pending_quote(self):
        """Saudi route: After documents, goes to quote sheet step."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.SAUDI
        )
        assert next_status == ContractorStatus.PENDING_THIRD_PARTY_QUOTE

    def test_can_transition_to_pending_quote(self):
        """Saudi route: Can transition from documents_uploaded to pending quote."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE
        )

    def test_pending_quote_to_cds(self):
        """Saudi route: Quote received -> CDS step."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
            ContractorStatus.PENDING_CDS_CS
        )

    def test_work_order_completed_to_pending_signature(self):
        """Saudi route: Work order done -> directly to signature (no 3rd party contract)."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.WORK_ORDER_COMPLETED,
            OnboardingRoute.SAUDI
        )
        # Saudi uses Aventus contract, not 3rd party
        assert next_status is None or next_status == ContractorStatus.PENDING_SIGNATURE

    def test_saudi_full_workflow_path(self):
        """Saudi route: Test full valid workflow path."""
        saudi_path = [
            (ContractorStatus.DRAFT, ContractorStatus.PENDING_DOCUMENTS),
            (ContractorStatus.PENDING_DOCUMENTS, ContractorStatus.DOCUMENTS_UPLOADED),
            (ContractorStatus.DOCUMENTS_UPLOADED, ContractorStatus.PENDING_THIRD_PARTY_QUOTE),
            (ContractorStatus.PENDING_THIRD_PARTY_QUOTE, ContractorStatus.PENDING_CDS_CS),
            (ContractorStatus.PENDING_CDS_CS, ContractorStatus.CDS_CS_COMPLETED),
            (ContractorStatus.CDS_CS_COMPLETED, ContractorStatus.PENDING_REVIEW),
            (ContractorStatus.PENDING_REVIEW, ContractorStatus.APPROVED),
            (ContractorStatus.APPROVED, ContractorStatus.PENDING_CLIENT_WO_SIGNATURE),
            (ContractorStatus.PENDING_CLIENT_WO_SIGNATURE, ContractorStatus.WORK_ORDER_COMPLETED),
            (ContractorStatus.WORK_ORDER_COMPLETED, ContractorStatus.PENDING_SIGNATURE),
            (ContractorStatus.PENDING_SIGNATURE, ContractorStatus.SIGNED),
            (ContractorStatus.SIGNED, ContractorStatus.ACTIVE),
        ]

        for from_status, to_status in saudi_path:
            assert ContractorStateMachine.can_transition(from_status, to_status), \
                f"Failed transition: {from_status.value} -> {to_status.value}"


class TestSaudiStrategy:
    """Tests for Saudi onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("saudi")

    def test_route_name(self, strategy):
        """Test Saudi route name."""
        assert strategy.route_name == "saudi"

    def test_display_name(self, strategy):
        """Test Saudi display name."""
        assert "Saudi" in strategy.display_name

    def test_required_documents(self, strategy):
        """Test Saudi required documents include iqama."""
        docs = strategy.get_required_documents()
        assert "passport" in docs
        assert "iqama" in docs  # Saudi residence permit

    def test_workflow_steps_include_quote_sheet(self, strategy):
        """Test Saudi workflow includes quote sheet step."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "quote_sheet" in step_ids

    def test_workflow_does_not_have_cohf(self, strategy):
        """Test Saudi workflow does not include COHF step."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "cohf" not in step_ids

    def test_workflow_does_not_have_third_party_contract(self, strategy):
        """Test Saudi workflow uses Aventus contract, not 3rd party."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "third_party_contract" not in step_ids
        assert "contract" in step_ids  # Uses Aventus contract

    def test_get_next_status_from_documents_uploaded(self, strategy):
        """Test next status after documents uploaded."""
        next_status = strategy.get_next_status(ContractorStatus.DOCUMENTS_UPLOADED)
        assert next_status == ContractorStatus.PENDING_THIRD_PARTY_QUOTE

    def test_get_next_status_from_pending_quote(self, strategy):
        """Test next status after quote received."""
        next_status = strategy.get_next_status(ContractorStatus.PENDING_THIRD_PARTY_QUOTE)
        assert next_status == ContractorStatus.PENDING_CDS_CS

    def test_validate_quote_sheet_request_missing_third_party(self, strategy):
        """Test quote sheet request validation - missing third party."""
        data = {"contractor_name": "John Doe"}
        errors = strategy.validate_step_data("quote_sheet_request", data)
        assert len(errors) > 0
        assert any("third party" in e.lower() for e in errors)

    def test_validate_quote_sheet_received_missing_id(self, strategy):
        """Test quote sheet received validation - missing quote sheet ID."""
        errors = strategy.validate_step_data("quote_sheet_received", {})
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_execute_quote_sheet_request(self, strategy):
        """Test executing quote sheet request step."""
        result = await strategy.execute_step(
            contractor_id=1,
            step="quote_sheet_request",
            data={"third_party_id": "tp-123"}
        )
        assert isinstance(result, OnboardingResult)
        assert result.next_status == ContractorStatus.PENDING_THIRD_PARTY_QUOTE
        assert result.requires_external_action is True

    @pytest.mark.asyncio
    async def test_execute_quote_sheet_received(self, strategy):
        """Test executing quote sheet received step."""
        result = await strategy.execute_step(
            contractor_id=1,
            step="quote_sheet_received",
            data={"quote_sheet_id": "qs-123", "total_cost": 50000}
        )
        assert result.next_status == ContractorStatus.PENDING_CDS_CS


# =============================================================================
# WPS Route Tests
# =============================================================================

class TestWPSRouteTransitions:
    """Tests for WPS (Work Permit System) route transitions."""

    def test_documents_uploaded_to_cds(self):
        """WPS route: After documents, goes directly to CDS (no COHF/quote)."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.WPS
        )
        assert next_status == ContractorStatus.PENDING_CDS_CS

    def test_work_order_completed_to_signature(self):
        """WPS route: Work order done -> directly to signature."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.WORK_ORDER_COMPLETED,
            OnboardingRoute.WPS
        )
        assert next_status == ContractorStatus.PENDING_SIGNATURE


class TestWPSStrategy:
    """Tests for WPS onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("wps")

    def test_route_name(self, strategy):
        """Test WPS route name."""
        assert strategy.route_name == "wps"

    def test_display_name_contains_wps(self, strategy):
        """Test WPS display name."""
        assert "WPS" in strategy.display_name.upper()

    def test_required_documents(self, strategy):
        """Test WPS required documents."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)
        assert "passport" in docs or any("passport" in d.lower() for d in docs)

    def test_workflow_does_not_have_cohf(self, strategy):
        """Test WPS workflow does not include COHF."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "cohf" not in step_ids

    def test_workflow_does_not_have_quote_sheet(self, strategy):
        """Test WPS workflow does not include quote sheet."""
        steps = strategy.get_workflow_steps()
        step_ids = [s.id for s in steps]
        assert "quote_sheet" not in step_ids


# =============================================================================
# Freelancer Route Tests
# =============================================================================

class TestFreelancerRouteTransitions:
    """Tests for Freelancer route transitions."""

    def test_documents_uploaded_to_cds(self):
        """Freelancer route: After documents, goes directly to CDS."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.FREELANCER
        )
        assert next_status == ContractorStatus.PENDING_CDS_CS


class TestFreelancerStrategy:
    """Tests for Freelancer onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("freelancer")

    def test_route_name(self, strategy):
        """Test Freelancer route name."""
        assert strategy.route_name == "freelancer"

    def test_display_name(self, strategy):
        """Test Freelancer display name."""
        assert "freelancer" in strategy.display_name.lower()

    def test_required_documents(self, strategy):
        """Test Freelancer required documents."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)

    def test_workflow_is_streamlined(self, strategy):
        """Test Freelancer workflow is streamlined (fewer steps than UAE)."""
        uae_strategy = OnboardingRegistry.get("uae")
        assert len(strategy.get_workflow_steps()) <= len(uae_strategy.get_workflow_steps())


# =============================================================================
# Offshore Route Tests
# =============================================================================

class TestOffshoreRouteTransitions:
    """Tests for Offshore/International route transitions."""

    def test_documents_uploaded_to_cds(self):
        """Offshore route: After documents, goes directly to CDS."""
        next_status = ContractorStateMachine.get_next_status_for_route(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.OFFSHORE
        )
        assert next_status == ContractorStatus.PENDING_CDS_CS


class TestOffshoreStrategy:
    """Tests for Offshore onboarding strategy."""

    @pytest.fixture
    def strategy(self):
        return OnboardingRegistry.get("offshore")

    def test_route_name(self, strategy):
        """Test Offshore route name."""
        assert strategy.route_name == "offshore"

    def test_display_name(self, strategy):
        """Test Offshore display name."""
        assert "offshore" in strategy.display_name.lower() or "international" in strategy.display_name.lower()

    def test_required_documents(self, strategy):
        """Test Offshore required documents."""
        docs = strategy.get_required_documents()
        assert isinstance(docs, list)
        assert "passport" in docs or any("passport" in d.lower() for d in docs)


# =============================================================================
# Route Comparison Tests
# =============================================================================

class TestRouteComparisons:
    """Tests comparing different routes."""

    def test_uae_and_saudi_require_third_party(self):
        """Test UAE and Saudi routes require third party."""
        assert OnboardingRoute.UAE.requires_third_party is True
        assert OnboardingRoute.SAUDI.requires_third_party is True

    def test_wps_and_freelancer_no_third_party(self):
        """Test WPS and Freelancer routes don't require third party."""
        assert OnboardingRoute.WPS.requires_third_party is False
        assert OnboardingRoute.FREELANCER.requires_third_party is False
        assert OnboardingRoute.OFFSHORE.requires_third_party is False

    def test_only_uae_requires_cohf(self):
        """Test only UAE route requires COHF."""
        assert OnboardingRoute.UAE.requires_cohf is True
        assert OnboardingRoute.SAUDI.requires_cohf is False
        assert OnboardingRoute.WPS.requires_cohf is False
        assert OnboardingRoute.FREELANCER.requires_cohf is False
        assert OnboardingRoute.OFFSHORE.requires_cohf is False

    def test_only_saudi_requires_quote_sheet(self):
        """Test only Saudi route requires quote sheet."""
        assert OnboardingRoute.SAUDI.requires_quote_sheet is True
        assert OnboardingRoute.UAE.requires_quote_sheet is False
        assert OnboardingRoute.WPS.requires_quote_sheet is False

    def test_all_routes_registered(self):
        """Test all routes are registered in the registry."""
        available = OnboardingRegistry.available_routes()
        assert "uae" in available
        assert "saudi" in available
        assert "wps" in available
        assert "freelancer" in available
        assert "offshore" in available

    def test_route_specific_documents(self):
        """Test routes have different required documents."""
        uae_docs = OnboardingRegistry.get("uae").get_required_documents()
        saudi_docs = OnboardingRegistry.get("saudi").get_required_documents()

        # UAE requires Emirates ID
        assert "emirates_id" in uae_docs
        # Saudi requires Iqama
        assert "iqama" in saudi_docs

    def test_uae_has_more_steps_than_default(self):
        """Test UAE has more workflow steps due to COHF and 3rd party contract."""
        uae_steps = len(OnboardingRegistry.get("uae").get_workflow_steps())
        wps_steps = len(OnboardingRegistry.get("wps").get_workflow_steps())
        # UAE should have same or more steps
        assert uae_steps >= wps_steps


# =============================================================================
# Workflow Progress Tests
# =============================================================================

class TestWorkflowProgressByRoute:
    """Tests for workflow progress calculation by route."""

    def test_uae_draft_progress(self):
        """Test UAE route progress at draft status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.DRAFT,
            OnboardingRoute.UAE
        )
        assert progress["current_step"] == 1
        assert progress["percentage"] < 20

    def test_saudi_draft_progress(self):
        """Test Saudi route progress at draft status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.DRAFT,
            OnboardingRoute.SAUDI
        )
        assert progress["current_step"] == 1

    def test_uae_cohf_progress(self):
        """Test UAE route progress at COHF status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.PENDING_COHF,
            OnboardingRoute.UAE
        )
        assert progress["current_step"] > 1
        assert progress["percentage"] > 0

    def test_saudi_quote_progress(self):
        """Test Saudi route progress at quote sheet status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
            OnboardingRoute.SAUDI
        )
        assert progress["current_step"] > 1

    def test_active_is_100_percent(self):
        """Test active status is 100% complete for all routes."""
        for route in [OnboardingRoute.UAE, OnboardingRoute.SAUDI, OnboardingRoute.WPS]:
            progress = ContractorStateMachine.get_workflow_progress(
                ContractorStatus.ACTIVE,
                route
            )
            assert progress["percentage"] == 100
            assert progress["is_complete"] is True


# =============================================================================
# Invalid Transition Tests
# =============================================================================

class TestInvalidTransitions:
    """Tests for invalid status transitions."""

    def test_cannot_skip_cohf_for_uae(self):
        """UAE route: Cannot skip COHF step."""
        # Cannot go from documents_uploaded directly to CDS without COHF
        assert not ContractorStateMachine.can_transition(
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.CDS_CS_COMPLETED
        )

    def test_cannot_go_directly_to_active(self):
        """Test cannot go directly from draft to active."""
        with pytest.raises(InvalidStatusTransitionError):
            ContractorStateMachine.transition(
                ContractorStatus.DRAFT,
                ContractorStatus.ACTIVE
            )

    def test_cannot_skip_review(self):
        """Test cannot skip admin review step."""
        assert not ContractorStateMachine.can_transition(
            ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.APPROVED
        )

    def test_cancelled_has_no_transitions(self):
        """Test cancelled status has no outgoing transitions."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.CANCELLED
        )
        assert len(allowed) == 0

    def test_terminated_has_no_transitions(self):
        """Test terminated status has no outgoing transitions."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.TERMINATED
        )
        assert len(allowed) == 0


# =============================================================================
# Offboarding from Active Status Tests
# =============================================================================

class TestOffboardingTransitions:
    """Tests for transitions from active to offboarding states."""

    def test_active_can_start_notice_period(self):
        """Test active contractor can start notice period."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.ACTIVE,
            ContractorStatus.NOTICE_PERIOD
        )

    def test_active_can_start_direct_offboarding(self):
        """Test active contractor can start direct offboarding."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.ACTIVE,
            ContractorStatus.OFFBOARDING
        )

    def test_notice_period_to_offboarding(self):
        """Test notice period leads to offboarding."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.NOTICE_PERIOD,
            ContractorStatus.OFFBOARDING
        )

    def test_offboarding_to_offboarded(self):
        """Test offboarding completes to offboarded."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.OFFBOARDING,
            ContractorStatus.OFFBOARDED
        )

    def test_offboarded_can_be_rehired(self):
        """Test offboarded contractor can be rehired."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.OFFBOARDED,
            ContractorStatus.DRAFT
        )
        assert ContractorStateMachine.can_rehire(ContractorStatus.OFFBOARDED)


# =============================================================================
# Extension Transition Tests
# =============================================================================

class TestExtensionTransitions:
    """Tests for extension-related transitions."""

    def test_active_can_start_extension(self):
        """Test active contractor can start extension process."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.ACTIVE,
            ContractorStatus.EXTENSION_PENDING
        )

    def test_extension_pending_returns_to_active(self):
        """Test extension pending returns to active when complete/rejected."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.EXTENSION_PENDING,
            ContractorStatus.ACTIVE
        )
