"""
UAE (3rd Party) Onboarding Strategy.

Workflow: Documents → Route → COHF → CDS → Review → Work Order → 3rd Party Contract → Activate

Key characteristics:
- Requires COHF (Cost of Hire Form) before CDS
- 3rd party uploads their contract (not Aventus contract)
- DocuSign integration for COHF signatures
"""
from typing import List, Optional, Dict, Any
from app.domain.onboarding.strategies.base import (
    OnboardingStrategy,
    OnboardingResult,
    WorkflowStep,
)
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute


class UAEOnboardingStrategy(OnboardingStrategy):
    """
    UAE (3rd Party) onboarding strategy implementation.

    This route is for contractors placed through a UAE-based third party.
    Key difference from other routes:
    - COHF form required before CDS
    - 3rd party provides the contract
    """

    @property
    def route_name(self) -> str:
        return OnboardingRoute.UAE.value

    @property
    def display_name(self) -> str:
        return "3rd Party UAE"

    def get_required_documents(self) -> List[str]:
        """UAE route required documents."""
        return [
            "passport",
            "photo",
            "emirates_id",
            "visa",
            "degree",
        ]

    def get_workflow_steps(self) -> List[WorkflowStep]:
        """UAE onboarding workflow steps."""
        return [
            WorkflowStep(
                id="documents",
                name="Document Upload",
                description="Upload required documents (passport, photo, Emirates ID, visa)",
                order=1,
            ),
            WorkflowStep(
                id="route_selection",
                name="Route Selection",
                description="Select onboarding route and third party",
                order=2,
            ),
            WorkflowStep(
                id="cohf",
                name="Cost of Hire Form",
                description="Complete and submit COHF for 3rd party signature",
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
                id="third_party_contract",
                name="3rd Party Contract",
                description="3rd party uploads their employment contract",
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
        """Get next status for UAE route."""
        transitions = {
            ContractorStatus.DOCUMENTS_UPLOADED: ContractorStatus.PENDING_COHF,
            ContractorStatus.PENDING_COHF: ContractorStatus.AWAITING_COHF_SIGNATURE,
            ContractorStatus.AWAITING_COHF_SIGNATURE: ContractorStatus.COHF_COMPLETED,
            ContractorStatus.COHF_COMPLETED: ContractorStatus.PENDING_CDS_CS,
            ContractorStatus.PENDING_CDS_CS: ContractorStatus.CDS_CS_COMPLETED,
            ContractorStatus.CDS_CS_COMPLETED: ContractorStatus.PENDING_REVIEW,
            ContractorStatus.APPROVED: ContractorStatus.PENDING_CLIENT_WO_SIGNATURE,
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: ContractorStatus.WORK_ORDER_COMPLETED,
            ContractorStatus.WORK_ORDER_COMPLETED: ContractorStatus.PENDING_3RD_PARTY_CONTRACT,
            ContractorStatus.PENDING_3RD_PARTY_CONTRACT: ContractorStatus.CONTRACT_APPROVED,
            ContractorStatus.CONTRACT_APPROVED: ContractorStatus.PENDING_SIGNATURE,
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
        """Execute UAE-specific step logic."""

        if step == "cohf":
            return await self._execute_cohf_step(contractor_id, data)

        if step == "cohf_signature":
            return await self._execute_cohf_signature_step(contractor_id, data)

        if step == "third_party_contract":
            return await self._execute_third_party_contract_step(contractor_id, data)

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

    async def _execute_cohf_step(
        self,
        contractor_id: int,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute COHF form submission step."""
        return OnboardingResult(
            next_status=ContractorStatus.AWAITING_COHF_SIGNATURE,
            message="COHF form submitted. Awaiting 3rd party signature.",
            requires_external_action=True,
            external_action_type="cohf_signature",
            data={
                "action": "send_cohf_to_third_party",
                "contractor_id": contractor_id,
            }
        )

    async def _execute_cohf_signature_step(
        self,
        contractor_id: int,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute COHF signature completion step."""
        return OnboardingResult(
            next_status=ContractorStatus.COHF_COMPLETED,
            message="COHF signed by all parties. Proceeding to CDS.",
            data={
                "signed_cohf_url": data.get("signed_document_url"),
            }
        )

    async def _execute_third_party_contract_step(
        self,
        contractor_id: int,
        data: Dict[str, Any],
    ) -> OnboardingResult:
        """Execute 3rd party contract upload step."""
        return OnboardingResult(
            next_status=ContractorStatus.CONTRACT_APPROVED,
            message="3rd party contract uploaded and approved.",
            data={
                "contract_url": data.get("contract_url"),
            }
        )

    def _get_status_to_step_mapping(self) -> Dict[ContractorStatus, str]:
        """Map statuses to workflow step IDs."""
        return {
            ContractorStatus.PENDING_DOCUMENTS: "documents",
            ContractorStatus.DOCUMENTS_UPLOADED: "route_selection",
            ContractorStatus.PENDING_COHF: "cohf",
            ContractorStatus.AWAITING_COHF_SIGNATURE: "cohf",
            ContractorStatus.COHF_COMPLETED: "cds_costing",
            ContractorStatus.PENDING_CDS_CS: "cds_costing",
            ContractorStatus.CDS_CS_COMPLETED: "admin_review",
            ContractorStatus.PENDING_REVIEW: "admin_review",
            ContractorStatus.APPROVED: "work_order",
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: "work_order",
            ContractorStatus.WORK_ORDER_COMPLETED: "third_party_contract",
            ContractorStatus.PENDING_3RD_PARTY_CONTRACT: "third_party_contract",
            ContractorStatus.CONTRACT_APPROVED: "activation",
            ContractorStatus.SIGNED: "activation",
        }

    def validate_step_data(self, step: str, data: Dict[str, Any]) -> List[str]:
        """Validate UAE-specific step data."""
        errors = []

        if step == "cohf":
            required_fields = ["employee_name", "remuneration", "third_party_id"]
            for field in required_fields:
                if not data.get(field):
                    errors.append(f"Missing required field: {field}")

        if step == "third_party_contract":
            if not data.get("contract_url"):
                errors.append("Contract document URL is required")

        return errors
