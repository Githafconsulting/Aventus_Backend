"""
Contractor State Machine.
Defines and enforces valid status transitions for contractors.
"""
from typing import Dict, Set, List, Optional, Any
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.exceptions.contractor import InvalidStatusTransitionError


class ContractorStateMachine:
    """
    State machine for contractor status transitions.

    Enforces business rules around what status changes are allowed.
    Prevents invalid transitions that would break the onboarding workflow.

    Usage:
        # Check if transition is valid
        if ContractorStateMachine.can_transition(current, new):
            ...

        # Perform transition (raises if invalid)
        new_status = ContractorStateMachine.transition(current, new)

        # Get allowed next statuses
        allowed = ContractorStateMachine.get_allowed_transitions(current)
    """

    # Define all valid transitions: from_status -> {valid_to_statuses}
    TRANSITIONS: Dict[ContractorStatus, Set[ContractorStatus]] = {
        # Initial stages
        ContractorStatus.DRAFT: {
            ContractorStatus.PENDING_DOCUMENTS,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.PENDING_DOCUMENTS: {
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.DOCUMENTS_UPLOADED: {
            # Route selection determines next status
            ContractorStatus.PENDING_COHF,              # UAE route
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE, # Saudi route
            ContractorStatus.PENDING_CDS_CS,            # Other routes
            ContractorStatus.CANCELLED,
        },

        # UAE COHF workflow
        ContractorStatus.PENDING_COHF: {
            ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.AWAITING_COHF_SIGNATURE: {
            ContractorStatus.COHF_COMPLETED,
            ContractorStatus.PENDING_COHF,  # Can go back for edits
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.COHF_COMPLETED: {
            ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.CANCELLED,
        },

        # Saudi Quote Sheet workflow
        ContractorStatus.PENDING_THIRD_PARTY_QUOTE: {
            ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.CANCELLED,
        },

        # CDS and Costing
        ContractorStatus.PENDING_CDS_CS: {
            ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.CDS_CS_COMPLETED: {
            ContractorStatus.PENDING_REVIEW,
            ContractorStatus.CANCELLED,
        },

        # Admin Review
        ContractorStatus.PENDING_REVIEW: {
            ContractorStatus.APPROVED,
            ContractorStatus.REJECTED,
            ContractorStatus.PENDING_CDS_CS,  # Recall for edits
        },

        ContractorStatus.APPROVED: {
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.REJECTED: {
            ContractorStatus.DRAFT,  # Can start over
            ContractorStatus.CANCELLED,
        },

        # Work Order
        ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: {
            ContractorStatus.WORK_ORDER_COMPLETED,
            ContractorStatus.APPROVED,  # Can go back
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.WORK_ORDER_COMPLETED: {
            ContractorStatus.PENDING_3RD_PARTY_CONTRACT,  # UAE route
            ContractorStatus.PENDING_SIGNATURE,           # Other routes
            ContractorStatus.CANCELLED,
        },

        # Contract stages
        ContractorStatus.PENDING_3RD_PARTY_CONTRACT: {
            ContractorStatus.CONTRACT_APPROVED,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.PENDING_CONTRACT_UPLOAD: {
            ContractorStatus.CONTRACT_APPROVED,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.CONTRACT_APPROVED: {
            ContractorStatus.PENDING_SIGNATURE,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.PENDING_SIGNATURE: {
            ContractorStatus.SIGNED,
            ContractorStatus.CANCELLED,
        },

        ContractorStatus.SIGNED: {
            ContractorStatus.ACTIVE,
        },

        # Active contractor states
        ContractorStatus.ACTIVE: {
            ContractorStatus.SUSPENDED,
            ContractorStatus.TERMINATED,
        },

        ContractorStatus.SUSPENDED: {
            ContractorStatus.ACTIVE,      # Can be reactivated
            ContractorStatus.TERMINATED,
        },

        # Terminal states - no transitions out
        ContractorStatus.CANCELLED: set(),
        ContractorStatus.TERMINATED: set(),
    }

    @classmethod
    def can_transition(
        cls,
        from_status: ContractorStatus,
        to_status: ContractorStatus,
    ) -> bool:
        """
        Check if a status transition is valid.

        Args:
            from_status: Current status
            to_status: Desired new status

        Returns:
            True if transition is allowed, False otherwise
        """
        allowed = cls.TRANSITIONS.get(from_status, set())
        return to_status in allowed

    @classmethod
    def transition(
        cls,
        from_status: ContractorStatus,
        to_status: ContractorStatus,
    ) -> ContractorStatus:
        """
        Perform a status transition.

        Args:
            from_status: Current status
            to_status: Desired new status

        Returns:
            The new status if transition is valid

        Raises:
            InvalidStatusTransitionError: If transition is not allowed
        """
        if not cls.can_transition(from_status, to_status):
            raise InvalidStatusTransitionError(
                message=f"Cannot transition from '{from_status.value}' to '{to_status.value}'",
                from_status=from_status.value,
                to_status=to_status.value,
            )
        return to_status

    @classmethod
    def get_allowed_transitions(
        cls,
        from_status: ContractorStatus,
    ) -> Set[ContractorStatus]:
        """
        Get all allowed transitions from a status.

        Args:
            from_status: Current status

        Returns:
            Set of valid target statuses
        """
        return cls.TRANSITIONS.get(from_status, set()).copy()

    @classmethod
    def get_next_status_for_route(
        cls,
        current_status: ContractorStatus,
        route: OnboardingRoute,
    ) -> Optional[ContractorStatus]:
        """
        Get the next status based on onboarding route.

        This is used for automatic workflow progression where the
        next status depends on the selected route.

        Args:
            current_status: Current contractor status
            route: The onboarding route

        Returns:
            The next status, or None if no automatic transition
        """
        # After document upload, route determines next step
        if current_status == ContractorStatus.DOCUMENTS_UPLOADED:
            if route == OnboardingRoute.UAE:
                return ContractorStatus.PENDING_COHF
            elif route == OnboardingRoute.SAUDI:
                return ContractorStatus.PENDING_THIRD_PARTY_QUOTE
            else:
                return ContractorStatus.PENDING_CDS_CS

        # After work order, UAE goes to 3rd party contract
        if current_status == ContractorStatus.WORK_ORDER_COMPLETED:
            if route == OnboardingRoute.UAE:
                return ContractorStatus.PENDING_3RD_PARTY_CONTRACT
            else:
                return ContractorStatus.PENDING_SIGNATURE

        return None

    @classmethod
    def is_terminal(cls, status: ContractorStatus) -> bool:
        """Check if a status is terminal (no further transitions)."""
        return len(cls.TRANSITIONS.get(status, set())) == 0

    @classmethod
    def get_workflow_progress(
        cls,
        status: ContractorStatus,
        route: OnboardingRoute,
    ) -> Dict[str, Any]:
        """
        Calculate workflow progress for a contractor.

        Args:
            status: Current status
            route: Onboarding route

        Returns:
            Dict with progress info (step, total_steps, percentage)
        """
        # Define steps for each route
        route_steps = {
            OnboardingRoute.UAE: [
                ContractorStatus.DRAFT,
                ContractorStatus.PENDING_DOCUMENTS,
                ContractorStatus.DOCUMENTS_UPLOADED,
                ContractorStatus.PENDING_COHF,
                ContractorStatus.COHF_COMPLETED,
                ContractorStatus.PENDING_CDS_CS,
                ContractorStatus.CDS_CS_COMPLETED,
                ContractorStatus.PENDING_REVIEW,
                ContractorStatus.APPROVED,
                ContractorStatus.WORK_ORDER_COMPLETED,
                ContractorStatus.PENDING_3RD_PARTY_CONTRACT,
                ContractorStatus.CONTRACT_APPROVED,
                ContractorStatus.SIGNED,
                ContractorStatus.ACTIVE,
            ],
            OnboardingRoute.SAUDI: [
                ContractorStatus.DRAFT,
                ContractorStatus.PENDING_DOCUMENTS,
                ContractorStatus.DOCUMENTS_UPLOADED,
                ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
                ContractorStatus.PENDING_CDS_CS,
                ContractorStatus.CDS_CS_COMPLETED,
                ContractorStatus.PENDING_REVIEW,
                ContractorStatus.APPROVED,
                ContractorStatus.WORK_ORDER_COMPLETED,
                ContractorStatus.SIGNED,
                ContractorStatus.ACTIVE,
            ],
        }

        # Default route steps
        default_steps = [
            ContractorStatus.DRAFT,
            ContractorStatus.PENDING_DOCUMENTS,
            ContractorStatus.DOCUMENTS_UPLOADED,
            ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.PENDING_REVIEW,
            ContractorStatus.APPROVED,
            ContractorStatus.WORK_ORDER_COMPLETED,
            ContractorStatus.SIGNED,
            ContractorStatus.ACTIVE,
        ]

        steps = route_steps.get(route, default_steps)
        total_steps = len(steps)

        try:
            current_step = steps.index(status) + 1
        except ValueError:
            current_step = 0

        return {
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": round((current_step / total_steps) * 100) if total_steps > 0 else 0,
            "status": status.value,
            "is_complete": status == ContractorStatus.ACTIVE,
        }
