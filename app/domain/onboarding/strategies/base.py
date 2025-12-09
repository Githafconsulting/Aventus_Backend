"""
Base onboarding strategy interface.
All route-specific strategies must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from app.domain.contractor.value_objects import ContractorStatus


@dataclass
class OnboardingResult:
    """
    Result of an onboarding step execution.

    Attributes:
        next_status: The status to transition to
        message: Human-readable message about what happened
        requires_external_action: Whether an external action is needed
        external_action_type: Type of external action (email, signature, etc.)
        data: Additional data from the step execution
    """
    next_status: ContractorStatus
    message: str
    requires_external_action: bool = False
    external_action_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowStep:
    """
    Definition of a workflow step.

    Attributes:
        id: Unique step identifier
        name: Human-readable name
        description: Detailed description
        required: Whether this step is mandatory
        order: Sort order in the workflow
    """
    id: str
    name: str
    description: str
    required: bool = True
    order: int = 0


class OnboardingStrategy(ABC):
    """
    Abstract base class for onboarding strategies.

    Each onboarding route (UAE, Saudi, Offshore, etc.) implements this
    interface with its specific workflow logic.

    The Strategy Pattern allows:
    - Adding new routes without modifying existing code
    - Different workflows for different contractor types
    - Easy testing of each route in isolation

    Usage:
        strategy = OnboardingRegistry.get("uae")
        result = await strategy.execute_step(contractor_id, "cohf", data)
    """

    @property
    @abstractmethod
    def route_name(self) -> str:
        """
        Return the route identifier.

        Returns:
            Route identifier string (e.g., "uae", "saudi")
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Return human-readable route name.

        Returns:
            Display name (e.g., "3rd Party UAE")
        """
        pass

    @abstractmethod
    def get_required_documents(self) -> List[str]:
        """
        Return list of required document types for this route.

        Returns:
            List of document field names (e.g., ["passport", "photo", "visa"])
        """
        pass

    @abstractmethod
    def get_workflow_steps(self) -> List[WorkflowStep]:
        """
        Return ordered list of workflow steps for this route.

        Returns:
            List of WorkflowStep objects in execution order
        """
        pass

    @abstractmethod
    def get_next_status(self, current_status: ContractorStatus) -> Optional[ContractorStatus]:
        """
        Determine the next status based on current status.

        Args:
            current_status: The contractor's current status

        Returns:
            The next status to transition to, or None if no automatic transition
        """
        pass

    @abstractmethod
    async def execute_step(
        self,
        contractor_id: int,
        step: str,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """
        Execute a specific onboarding step.

        Args:
            contractor_id: The contractor being onboarded
            step: The step identifier (e.g., "cohf", "cds")
            data: Step-specific data

        Returns:
            OnboardingResult with next status and any required actions
        """
        pass

    def validate_step_data(self, step: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate data for a specific step.

        Override in subclasses to add step-specific validation.

        Args:
            step: The step identifier
            data: Data to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        return []

    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """
        Get a workflow step by its ID.

        Args:
            step_id: Step identifier

        Returns:
            WorkflowStep if found, None otherwise
        """
        for step in self.get_workflow_steps():
            if step.id == step_id:
                return step
        return None

    def get_current_step(self, status: ContractorStatus) -> Optional[WorkflowStep]:
        """
        Get the current workflow step based on contractor status.

        Override in subclasses for custom logic.

        Args:
            status: Current contractor status

        Returns:
            Current WorkflowStep, or None
        """
        # Default: map status to step (override for custom logic)
        status_to_step = self._get_status_to_step_mapping()
        step_id = status_to_step.get(status)
        return self.get_step_by_id(step_id) if step_id else None

    def _get_status_to_step_mapping(self) -> Dict[ContractorStatus, str]:
        """
        Map statuses to step IDs.
        Override in subclasses.
        """
        return {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(route={self.route_name})>"
