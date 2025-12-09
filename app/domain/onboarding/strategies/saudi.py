"""
Saudi Arabia (3rd Party) Onboarding Strategy.

Workflow: Documents → Route → Quote Sheet → CDS → Review → Work Order → Contract → Activate

Key characteristics:
- Requires Quote Sheet from Saudi 3rd party before CDS
- Uses Aventus contract (not 3rd party contract)
- Comprehensive costing with SAR currency
"""
from typing import List, Optional, Dict, Any
from app.domain.onboarding.strategies.base import (
    OnboardingStrategy,
    OnboardingResult,
    WorkflowStep,
)
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute


class SaudiOnboardingStrategy(OnboardingStrategy):
    """
    Saudi Arabia (3rd Party) onboarding strategy implementation.

    This route is for contractors placed through a Saudi-based third party.
    Key difference from other routes:
    - Quote sheet from 3rd party required before CDS
    - Comprehensive costing breakdown (employee, family, government costs)
    """

    @property
    def route_name(self) -> str:
        return OnboardingRoute.SAUDI.value

    @property
    def display_name(self) -> str:
        return "3rd Party Saudi Arabia"

    def get_required_documents(self) -> List[str]:
        """Saudi route required documents."""
        return [
            "passport",
            "photo",
            "degree",
            "iqama",  # Saudi residence permit
        ]

    def get_workflow_steps(self) -> List[WorkflowStep]:
        """Saudi onboarding workflow steps."""
        return [
            WorkflowStep(
                id="documents",
                name="Document Upload",
                description="Upload required documents (passport, photo, degree, iqama)",
                order=1,
            ),
            WorkflowStep(
                id="route_selection",
                name="Route Selection",
                description="Select onboarding route and third party",
                order=2,
            ),
            WorkflowStep(
                id="quote_sheet",
                name="Quote Sheet",
                description="Request and receive costing quote from 3rd party",
                order=3,
            ),
            WorkflowStep(
                id="cds_costing",
                name="CDS & Costing Sheet",
                description="Complete contractor data sheet and costing information",
                order=4,
            ),
            WorkflowStep(
                id="admin_review",
                name="Admin Review",
                description="Admin reviews and approves contractor details",
                order=5,
            ),
            WorkflowStep(
                id="work_order",
                name="Work Order",
                description="Generate and send work order to client for signature",
                order=6,
            ),
            WorkflowStep(
                id="contract",
                name="Employment Contract",
                description="Generate and send Aventus employment contract",
                order=7,
            ),
            WorkflowStep(
                id="activation",
                name="Activation",
                description="Activate contractor account with login credentials",
                order=8,
            ),
        ]

    def get_next_status(self, current_status: ContractorStatus) -> Optional[ContractorStatus]:
        """Get next status for Saudi route."""
        transitions = {
            ContractorStatus.DOCUMENTS_UPLOADED: ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE: ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.PENDING_CDS_CS: ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CDS_CS_COMPLETED: ContractorStatus.PENDING_REVIEW,
            ContractorStatus.APPROVED: ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: ContractorStatus.WORK_ORDER_COMPLETED,
            ContractorStatus.WORK_ORDER_COMPLETED: ContractorStatus.PENDING_SIGNATURE,
            ContractorStatus.PENDING_SIGNATURE: ContractorStatus.SIGNED,
            ContractorStatus.SIGNED: ContractorStatus.ACTIVE,
        }
        return transitions.get(current_status)

    async def execute_step(
        self,
        contractor_id: int,
        step: str,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute Saudi-specific step logic."""

        if step == "quote_sheet_request":
            return await self._execute_quote_sheet_request(contractor_id, data)

        if step == "quote_sheet_received":
            return await self._execute_quote_sheet_received(contractor_id, data)

        # Default: proceed to next status
        current_status = ContractorStatus(data.get("current_status"))
        next_status = self.get_next_status(current_status)

        if next_status:
            return OnboardingResult(
                next_status=next_status,
                message=f"Step '{step}' completed successfully",
            )

        return OnboardingResult(
            next_status=current_status,
            message=f"No automatic transition for step '{step}'",
        )

    async def _execute_quote_sheet_request(
        self,
        contractor_id: int,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute quote sheet request step."""
        return OnboardingResult(
            next_status=ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
            message="Quote sheet request sent to 3rd party.",
            requires_external_action=True,
            external_action_type="quote_sheet_email",
            data={
                "action": "send_quote_sheet_request",
                "contractor_id": contractor_id,
                "third_party_id": data.get("third_party_id"),
            }
        )

    async def _execute_quote_sheet_received(
        self,
        contractor_id: int,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute quote sheet received step."""
        return OnboardingResult(
            next_status=ContractorStatus.PENDING_CDS_CS,
            message="Quote sheet received. Proceeding to CDS.",
            data={
                "quote_sheet_id": data.get("quote_sheet_id"),
                "total_cost": data.get("total_cost"),
            }
        )

    def _get_status_to_step_mapping(self) -> Dict[ContractorStatus, str]:
        """Map statuses to workflow step IDs."""
        return {
            ContractorStatus.PENDING_DOCUMENTS: "documents",
            ContractorStatus.DOCUMENTS_UPLOADED: "route_selection",
            ContractorStatus.PENDING_THIRD_PARTY_QUOTE: "quote_sheet",
            ContractorStatus.PENDING_CDS_CS: "cds_costing",
            ContractorStatus.CDS_CS_COMPLETED: "admin_review",
            ContractorStatus.PENDING_REVIEW: "admin_review",
            ContractorStatus.APPROVED: "work_order",
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: "work_order",
            ContractorStatus.WORK_ORDER_COMPLETED: "contract",
            ContractorStatus.PENDING_SIGNATURE: "contract",
            ContractorStatus.SIGNED: "activation",
        }

    def validate_step_data(self, step: str, data: Dict[str, Any]) -> List[str]:
        """Validate Saudi-specific step data."""
        errors = []

        if step == "quote_sheet_request":
            if not data.get("third_party_id"):
                errors.append("Third party ID is required")
            if not data.get("contractor_name"):
                errors.append("Contractor name is required")

        if step == "quote_sheet_received":
            if not data.get("quote_sheet_id"):
                errors.append("Quote sheet ID is required")

        return errors
