"""
Unit tests for contractor state machine.
"""
import pytest
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.state_machine import ContractorStateMachine
from app.exceptions.contractor import InvalidStatusTransitionError


class TestContractorStateMachine:
    """Tests for ContractorStateMachine."""

    def test_valid_transition_draft_to_pending_documents(self):
        """Test valid transition from draft to pending_documents."""
        result = ContractorStateMachine.transition(
            ContractorStatus.DRAFT,
            ContractorStatus.PENDING_DOCUMENTS
        )
        assert result == ContractorStatus.PENDING_DOCUMENTS

    def test_valid_transition_pending_documents_to_documents_uploaded(self):
        """Test valid transition from pending_documents to documents_uploaded."""
        result = ContractorStateMachine.transition(
            ContractorStatus.PENDING_DOCUMENTS,
            ContractorStatus.DOCUMENTS_UPLOADED
        )
        assert result == ContractorStatus.DOCUMENTS_UPLOADED

    def test_valid_transition_signed_to_active(self):
        """Test valid transition from signed to active."""
        result = ContractorStateMachine.transition(
            ContractorStatus.SIGNED,
            ContractorStatus.ACTIVE
        )
        assert result == ContractorStatus.ACTIVE

    def test_invalid_transition_raises_error(self):
        """Test that invalid transition raises error."""
        with pytest.raises(InvalidStatusTransitionError):
            ContractorStateMachine.transition(
                ContractorStatus.DRAFT,
                ContractorStatus.ACTIVE  # Can't go directly to active
            )

    def test_invalid_transition_pending_to_active(self):
        """Test that skipping steps raises error."""
        with pytest.raises(InvalidStatusTransitionError):
            ContractorStateMachine.transition(
                ContractorStatus.PENDING_DOCUMENTS,
                ContractorStatus.ACTIVE
            )

    def test_can_transition_returns_true_for_valid(self):
        """Test can_transition returns True for valid transitions."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.DRAFT,
            ContractorStatus.PENDING_DOCUMENTS
        ) is True

    def test_can_transition_returns_false_for_invalid(self):
        """Test can_transition returns False for invalid transitions."""
        assert ContractorStateMachine.can_transition(
            ContractorStatus.DRAFT,
            ContractorStatus.ACTIVE
        ) is False

    def test_get_allowed_transitions(self):
        """Test getting allowed transitions from a status."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.PENDING_DOCUMENTS
        )
        assert ContractorStatus.DOCUMENTS_UPLOADED in allowed
        assert ContractorStatus.ACTIVE not in allowed

    def test_get_allowed_transitions_for_draft(self):
        """Test allowed transitions from draft status."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.DRAFT
        )
        assert ContractorStatus.PENDING_DOCUMENTS in allowed

    def test_get_allowed_transitions_for_active(self):
        """Test allowed transitions from active status."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.ACTIVE
        )
        assert ContractorStatus.SUSPENDED in allowed
        assert ContractorStatus.TERMINATED in allowed

    def test_terminated_has_no_transitions(self):
        """Test that terminated status has no outgoing transitions."""
        allowed = ContractorStateMachine.get_allowed_transitions(
            ContractorStatus.TERMINATED
        )
        assert len(allowed) == 0 or allowed == set()


class TestStateMachineWorkflowProgress:
    """Tests for workflow progress calculation."""

    def test_workflow_progress_draft(self):
        """Test progress at draft status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.DRAFT,
            OnboardingRoute.UAE
        )
        assert "current_step" in progress
        assert "percentage" in progress
        assert progress["percentage"] >= 0

    def test_workflow_progress_active(self):
        """Test progress at active status (should be 100%)."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.ACTIVE,
            OnboardingRoute.UAE
        )
        assert progress["percentage"] == 100

    def test_workflow_progress_midway(self):
        """Test progress at midway status."""
        progress = ContractorStateMachine.get_workflow_progress(
            ContractorStatus.DOCUMENTS_UPLOADED,
            OnboardingRoute.UAE
        )
        assert 0 < progress["percentage"] < 100
