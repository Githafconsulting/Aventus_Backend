"""
Onboarding Service.

Application service for managing contractor onboarding workflows.
Orchestrates the onboarding process using strategies.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.repositories.implementations.contractor_repo import ContractorRepository
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute
from app.domain.contractor.exceptions import ContractorNotFoundError
from app.domain.onboarding.registry import OnboardingRegistry
from app.domain.onboarding.strategies.base import OnboardingResult, WorkflowStep
from app.services.notification_service import NotificationService
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class OnboardingService:
    """
    Application service for contractor onboarding.

    Manages the onboarding workflow by:
    - Determining current step based on status
    - Executing steps using route-specific strategies
    - Sending notifications at appropriate points
    - Tracking progress and transitions
    """

    def __init__(
        self,
        contractor_repo: ContractorRepository,
        notification_service: Optional[NotificationService] = None,
    ):
        """
        Initialize onboarding service.

        Args:
            contractor_repo: Contractor repository
            notification_service: Notification service (optional)
        """
        self.contractor_repo = contractor_repo
        self.notifications = notification_service

    async def get_workflow_status(self, contractor_id: int) -> Dict[str, Any]:
        """
        Get the current workflow status for a contractor.

        Args:
            contractor_id: Contractor ID

        Returns:
            Dict with workflow information
        """
        contractor = await self.contractor_repo.get(contractor_id)
        if not contractor:
            raise ContractorNotFoundError(f"Contractor {contractor_id} not found")

        route = contractor.onboarding_route
        status = ContractorStatus(contractor.status)

        result = {
            "contractor_id": contractor_id,
            "current_status": status.value,
            "route": route,
            "workflow_steps": [],
            "current_step": None,
            "completed_steps": [],
            "pending_steps": [],
        }

        if not route:
            result["message"] = "Onboarding route not yet selected"
            return result

        # Get strategy for the route
        strategy = OnboardingRegistry.get(route)

        # Get all workflow steps
        steps = strategy.get_workflow_steps()
        result["workflow_steps"] = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "order": s.order,
            }
            for s in steps
        ]

        # Determine current step
        current_step = strategy.get_current_step(status)
        if current_step:
            result["current_step"] = current_step.id

        # Categorize steps
        if current_step:
            for step in steps:
                if step.order < current_step.order:
                    result["completed_steps"].append(step.id)
                elif step.order > current_step.order:
                    result["pending_steps"].append(step.id)

        return result

    async def execute_step(
        self,
        contractor_id: int,
        step_id: str,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """
        Execute an onboarding step.

        Args:
            contractor_id: Contractor ID
            step_id: Step identifier
            data: Step-specific data

        Returns:
            OnboardingResult with next status and actions
        """
        contractor = await self.contractor_repo.get(contractor_id)
        if not contractor:
            raise ContractorNotFoundError(f"Contractor {contractor_id} not found")

        route = contractor.onboarding_route
        if not route:
            raise ValueError("Cannot execute step: onboarding route not selected")

        # Get strategy
        strategy = OnboardingRegistry.get(route)

        # Validate step data
        errors = strategy.validate_step_data(step_id, data)
        if errors:
            return OnboardingResult(
                next_status=ContractorStatus(contractor.status),
                message=f"Validation failed: {', '.join(errors)}",
            )

        # Add current status to data
        data["current_status"] = contractor.status

        # Execute step
        result = await strategy.execute_step(contractor_id, step_id, data)

        # Update contractor status if changed
        if result.next_status.value != contractor.status:
            await self.contractor_repo.update(contractor_id, {
                "status": result.next_status.value,
                "updated_at": datetime.utcnow(),
            })

        logger.info(
            "Onboarding step executed",
            extra={
                "contractor_id": contractor_id,
                "step": step_id,
                "route": route,
                "next_status": result.next_status.value,
                "requires_external_action": result.requires_external_action,
            }
        )

        # Handle external actions (send notifications, etc.)
        if result.requires_external_action and self.notifications:
            await self._handle_external_action(
                contractor,
                result.external_action_type,
                data,
            )

        return result

    async def _handle_external_action(
        self,
        contractor,
        action_type: str,
        data: Dict[str, Any],
    ):
        """Handle external actions like sending notifications."""
        if not self.notifications:
            return

        contractor_name = f"{contractor.first_name} {contractor.surname}"

        if action_type == "document_upload":
            await self.notifications.send_document_upload_email(
                contractor_email=contractor.email,
                contractor_name=contractor_name,
                upload_token=contractor.document_upload_token,
                expiry_date=contractor.document_upload_token_expiry,
            )

        elif action_type == "contract_signature":
            await self.notifications.send_contract_signing_email(
                contractor_email=contractor.email,
                contractor_name=contractor_name,
                contract_token=contractor.contract_token,
                expiry_date=contractor.contract_token_expiry,
            )

        elif action_type == "cohf_signature":
            # Get third party info from data
            third_party = data.get("third_party", {})
            await self.notifications.send_cohf_signature_request(
                third_party_email=third_party.get("email"),
                third_party_name=third_party.get("name"),
                contractor_name=contractor_name,
                cohf_token=data.get("cohf_token"),
                expiry_date=data.get("expiry_date"),
            )

        elif action_type == "quote_sheet_submission":
            third_party = data.get("third_party", {})
            await self.notifications.send_quote_sheet_request(
                third_party_email=third_party.get("email"),
                third_party_name=third_party.get("name"),
                contractor_name=contractor_name,
                quote_token=data.get("quote_token"),
                expiry_date=data.get("expiry_date"),
            )

    async def get_available_routes(self) -> List[Dict[str, Any]]:
        """
        Get list of available onboarding routes.

        Returns:
            List of route info dicts
        """
        return OnboardingRegistry.get_route_info()

    async def get_required_documents(
        self,
        route: str,
    ) -> List[str]:
        """
        Get required documents for a route.

        Args:
            route: Route identifier

        Returns:
            List of required document field names
        """
        strategy = OnboardingRegistry.get(route)
        return strategy.get_required_documents()

    async def get_next_action(self, contractor_id: int) -> Dict[str, Any]:
        """
        Get the next required action for a contractor.

        Args:
            contractor_id: Contractor ID

        Returns:
            Dict describing the next action needed
        """
        contractor = await self.contractor_repo.get(contractor_id)
        if not contractor:
            raise ContractorNotFoundError(f"Contractor {contractor_id} not found")

        status = ContractorStatus(contractor.status)
        route = contractor.onboarding_route

        # Determine next action based on status
        if status == ContractorStatus.PENDING_DOCUMENTS:
            return {
                "action": "upload_documents",
                "description": "Contractor needs to upload required documents",
                "actor": "contractor",
            }

        if status == ContractorStatus.DOCUMENTS_UPLOADED and not route:
            return {
                "action": "select_route",
                "description": "Admin needs to select onboarding route",
                "actor": "admin",
            }

        if route:
            strategy = OnboardingRegistry.get(route)
            current_step = strategy.get_current_step(status)
            if current_step:
                return {
                    "action": current_step.id,
                    "description": current_step.description,
                    "actor": self._determine_actor(current_step.id),
                }

        return {
            "action": "none",
            "description": "No pending actions",
            "actor": None,
        }

    def _determine_actor(self, step_id: str) -> str:
        """Determine who needs to act on a step."""
        contractor_steps = {"documents", "contract"}
        admin_steps = {"route_selection", "cds_costing", "admin_review", "activation"}
        client_steps = {"work_order"}
        third_party_steps = {"cohf", "quote_sheet", "third_party_contract"}

        if step_id in contractor_steps:
            return "contractor"
        elif step_id in admin_steps:
            return "admin"
        elif step_id in client_steps:
            return "client"
        elif step_id in third_party_steps:
            return "third_party"
        else:
            return "admin"  # Default to admin
