"""
Freelancer Onboarding Strategy.

Workflow: Documents → Route → CDS → Review → Work Order → Contract → Activate

Key characteristics:
- Independent contractors/freelancers
- Simplified document requirements
- Direct contract with Aventus
- No visa/residence requirements
"""
from typing import List, Optional, Dict, Any
from app.domain.onboarding.strategies.base import (
    OnboardingStrategy,
    OnboardingResult,
    WorkflowStep,
)
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute


class FreelancerOnboardingStrategy(OnboardingStrategy):
    """
    Freelancer onboarding strategy implementation.

    For independent contractors who work as freelancers.
    Simplified workflow with minimal document requirements.
    """

    @property
    def route_name(self) -> str:
        return OnboardingRoute.FREELANCER.value

    @property
    def display_name(self) -> str:
        return "Freelancer"

    def get_required_documents(self) -> List[str]:
        """Freelancer route required documents - minimal requirements."""
        return [
            "passport",
            "photo",
        ]

    def get_optional_documents(self) -> List[str]:
        """Optional documents for freelancers."""
        return [
            "degree",
            "portfolio",
            "certifications",
        ]

    def get_workflow_steps(self) -> List[WorkflowStep]:
        """Freelancer onboarding workflow steps."""
        return [
            WorkflowStep(
                id="documents",
                name="Document Upload",
                description="Upload required documents (passport, photo)",
                order=1,
            ),
            WorkflowStep(
                id="route_selection",
                name="Route Selection",
                description="Select onboarding route",
                order=2,
            ),
            WorkflowStep(
                id="cds_costing",
                name="CDS & Costing Sheet",
                description="Complete contractor data sheet and costing information",
                order=3,
            ),
            WorkflowStep(
                id="admin_review",
                name="Admin Review",
                description="Admin reviews and approves contractor details",
                order=4,
            ),
            WorkflowStep(
                id="work_order",
                name="Work Order",
                description="Generate and send work order to client for signature",
                order=5,
            ),
            WorkflowStep(
                id="contract",
                name="Freelancer Agreement",
                description="Generate and send freelancer agreement",
                order=6,
            ),
            WorkflowStep(
                id="activation",
                name="Activation",
                description="Activate contractor account with login credentials",
                order=7,
            ),
        ]

    def get_next_status(self, current_status: ContractorStatus) -> Optional[ContractorStatus]:
        """Get next status for Freelancer route."""
        transitions = {
            ContractorStatus.DOCUMENTS_UPLOADED: ContractorStatus.PENDING_CDS_CS,
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
        """Execute Freelancer-specific step logic."""
        current_status = ContractorStatus(data.get("current_status"))
        next_status = self.get_next_status(current_status)

        if step == "contract":
            # Freelancers get a specific agreement type
            return OnboardingResult(
                next_status=ContractorStatus.PENDING_SIGNATURE,
                message="Freelancer agreement generated and sent for signature",
                requires_external_action=True,
                external_action_type="contract_signature",
                data={"contract_type": "freelancer_agreement"},
            )

        if next_status:
            return OnboardingResult(
                next_status=next_status,
                message=f"Step '{step}' completed successfully",
            )

        return OnboardingResult(
            next_status=current_status,
            message=f"No automatic transition for step '{step}'",
        )

    def validate_step_data(self, step: str, data: Dict[str, Any]) -> List[str]:
        """Validate freelancer-specific step data."""
        errors = []

        if step == "cds_costing":
            # Freelancers must have payment method specified
            if not data.get("payment_method"):
                errors.append("Payment method is required for freelancers")

        return errors

    def _get_status_to_step_mapping(self) -> Dict[ContractorStatus, str]:
        """Map statuses to workflow step IDs."""
        return {
            ContractorStatus.PENDING_DOCUMENTS: "documents",
            ContractorStatus.DOCUMENTS_UPLOADED: "route_selection",
            ContractorStatus.PENDING_CDS_CS: "cds_costing",
            ContractorStatus.CDS_CS_COMPLETED: "admin_review",
            ContractorStatus.PENDING_REVIEW: "admin_review",
            ContractorStatus.APPROVED: "work_order",
            ContractorStatus.PENDING_CLIENT_WO_SIGNATURE: "work_order",
            ContractorStatus.WORK_ORDER_COMPLETED: "contract",
            ContractorStatus.PENDING_SIGNATURE: "contract",
            ContractorStatus.SIGNED: "activation",
        }
