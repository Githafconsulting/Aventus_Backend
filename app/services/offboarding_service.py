"""
Offboarding Service.

Application service for managing contractor offboarding process.
Handles settlement calculations, document generation, and workflow management.
"""
from typing import Optional
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session

from app.models.contractor import Contractor, ContractorStatus
from app.models.offboarding import OffboardingRecord, OffboardingReason, OffboardingStatus
from app.schemas.offboarding import (
    SettlementBreakdown,
    InitiateOffboardingRequest,
    OffboardingStatusResponse,
)
from app.domain.contractor.state_machine import ContractorStateMachine
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class OffboardingService:
    """
    Service for managing contractor offboarding.

    Handles the full offboarding workflow including:
    - Initiating offboarding
    - Settlement calculation
    - Document generation
    - Workflow completion
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    async def initiate_offboarding(
        self,
        contractor_id: str,
        request: InitiateOffboardingRequest,
        initiated_by: str,
    ) -> OffboardingRecord:
        """
        Initiate offboarding process for a contractor.

        Args:
            contractor_id: Contractor to offboard
            request: Offboarding request details
            initiated_by: User ID initiating the offboarding

        Returns:
            Created offboarding record

        Raises:
            ValueError: If contractor not found or invalid state
        """
        contractor = self.db.query(Contractor).filter(Contractor.id == contractor_id).first()
        if not contractor:
            raise ValueError(f"Contractor not found: {contractor_id}")

        # Check if already in offboarding
        existing = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.contractor_id == contractor_id,
            OffboardingRecord.status.notin_([OffboardingStatus.COMPLETED, OffboardingStatus.CANCELLED])
        ).first()
        if existing:
            raise ValueError(f"Contractor already has active offboarding: {existing.id}")

        # Validate contractor can be offboarded
        if contractor.status not in [ContractorStatus.ACTIVE, ContractorStatus.SUSPENDED]:
            raise ValueError(f"Cannot offboard contractor in status: {contractor.status}")

        # Determine initial status and dates
        notice_start = date.today()
        if request.notice_period_days > 0:
            initial_status = OffboardingStatus.NOTICE_PERIOD
            contractor_status = ContractorStatus.NOTICE_PERIOD
        else:
            initial_status = OffboardingStatus.PENDING_SETTLEMENT
            contractor_status = ContractorStatus.OFFBOARDING

        # Create offboarding record
        offboarding = OffboardingRecord(
            id=str(uuid.uuid4()),
            contractor_id=contractor_id,
            reason=request.reason,
            status=initial_status,
            initiated_by=initiated_by,
            notice_period_days=request.notice_period_days,
            notice_start_date=notice_start,
            last_working_date=request.last_working_date,
            effective_termination_date=request.last_working_date,
            notes=request.notes,
            transfer_to_employer=request.transfer_to_employer,
            transfer_effective_date=request.transfer_effective_date,
        )

        self.db.add(offboarding)

        # Update contractor status
        contractor.status = contractor_status
        contractor.offboarding_status = initial_status.value
        contractor.offboarding_reason = request.reason.value

        self.db.commit()
        self.db.refresh(offboarding)

        logger.info(
            "Offboarding initiated",
            extra={
                "contractor_id": contractor_id,
                "offboarding_id": offboarding.id,
                "reason": request.reason.value,
                "initiated_by": initiated_by,
            }
        )

        return offboarding

    async def calculate_final_settlement(
        self,
        contractor_id: str,
        preview_date: Optional[date] = None,
    ) -> SettlementBreakdown:
        """
        Calculate final settlement for a contractor.

        Includes:
        - Pro-rata salary for final month
        - Unused leave payout
        - Gratuity/EOSB
        - Pending reimbursements
        - Deductions

        Args:
            contractor_id: Contractor to calculate settlement for
            preview_date: Optional date for preview calculation (used when no offboarding exists)

        Returns:
            Settlement breakdown
        """
        contractor = self.db.query(Contractor).filter(Contractor.id == contractor_id).first()
        if not contractor:
            raise ValueError(f"Contractor not found: {contractor_id}")

        # Get the active offboarding record (if exists)
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.contractor_id == contractor_id,
            OffboardingRecord.status.notin_([OffboardingStatus.COMPLETED, OffboardingStatus.CANCELLED])
        ).first()

        # Determine last working date
        if offboarding:
            last_working_date = offboarding.last_working_date
        elif preview_date:
            last_working_date = preview_date
        elif contractor.end_date:
            # Use contractor's contract end date for preview
            try:
                last_working_date = datetime.strptime(contractor.end_date, "%Y-%m-%d").date() if isinstance(contractor.end_date, str) else contractor.end_date
            except (ValueError, TypeError):
                last_working_date = date.today()
        else:
            # Default to today if no date available
            last_working_date = date.today()

        # Calculate pro-rata salary
        month_start = date(last_working_date.year, last_working_date.month, 1)
        days_in_month = (date(last_working_date.year, last_working_date.month + 1, 1) - timedelta(days=1)).day if last_working_date.month < 12 else 31
        days_worked = (last_working_date - month_start).days + 1

        # Get salary rate
        monthly_rate = Decimal(contractor.gross_salary or contractor.charge_rate_month or "0")
        daily_rate = monthly_rate / Decimal(str(days_in_month)) if days_in_month > 0 else Decimal("0")
        pro_rata_salary = daily_rate * Decimal(str(days_worked))

        # Calculate leave payout
        total_leave_accrued = Decimal(contractor.leave_allowance or "0")
        leave_used = Decimal("0")  # Would need to fetch from leave records
        leave_remaining = total_leave_accrued - leave_used
        unused_leave_payout = daily_rate * leave_remaining

        # Calculate gratuity/EOSB
        start_date_str = contractor.start_date
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        except (ValueError, TypeError):
            start_date = None

        years_of_service = Decimal("0")
        if start_date:
            service_days = (last_working_date - start_date).days
            years_of_service = Decimal(str(service_days)) / Decimal("365")

        # Standard gratuity calculation (21 days per year for first 5 years, 30 days after)
        if years_of_service > 5:
            gratuity_days = (Decimal("5") * Decimal("21")) + ((years_of_service - Decimal("5")) * Decimal("30"))
        else:
            gratuity_days = years_of_service * Decimal("21")

        gratuity_eosb = daily_rate * gratuity_days

        # Pending reimbursements (would fetch from expense system)
        pending_reimbursements = Decimal("0")
        pending_expenses = Decimal("0")

        # Deductions (would fetch from deduction records)
        deductions = Decimal("0")

        # Calculate total
        total_settlement = (
            pro_rata_salary +
            unused_leave_payout +
            gratuity_eosb +
            pending_reimbursements +
            pending_expenses -
            deductions
        )

        breakdown = SettlementBreakdown(
            pro_rata_salary=pro_rata_salary.quantize(Decimal("0.01")),
            unused_leave_payout=unused_leave_payout.quantize(Decimal("0.01")),
            gratuity_eosb=gratuity_eosb.quantize(Decimal("0.01")),
            pending_reimbursements=pending_reimbursements.quantize(Decimal("0.01")),
            pending_expenses=pending_expenses.quantize(Decimal("0.01")),
            deductions=deductions.quantize(Decimal("0.01")),
            total_settlement=total_settlement.quantize(Decimal("0.01")),
            currency=contractor.currency or "USD",
            days_worked_final_month=days_worked,
            total_leave_days_accrued=total_leave_accrued,
            leave_days_used=leave_used,
            leave_days_remaining=leave_remaining,
            years_of_service=years_of_service.quantize(Decimal("0.01")),
            gratuity_rate=gratuity_days.quantize(Decimal("0.01")),
        )

        # Store breakdown in offboarding record (only if one exists)
        if offboarding:
            offboarding.settlement_breakdown = breakdown.model_dump(mode='json')
            offboarding.final_settlement_amount = total_settlement
            self.db.commit()

            logger.info(
                "Settlement calculated",
                extra={
                    "contractor_id": contractor_id,
                    "offboarding_id": offboarding.id,
                    "total_settlement": str(total_settlement),
                }
            )
        else:
            logger.info(
                "Settlement preview calculated (no offboarding record)",
                extra={
                    "contractor_id": contractor_id,
                    "total_settlement": str(total_settlement),
                }
            )

        return breakdown

    async def approve_settlement(
        self,
        offboarding_id: str,
        approved_by: str,
        adjustments: Optional[dict] = None,
    ) -> OffboardingRecord:
        """
        Approve settlement calculation.

        Args:
            offboarding_id: Offboarding record ID
            approved_by: User ID approving
            adjustments: Optional manual adjustments

        Returns:
            Updated offboarding record
        """
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.id == offboarding_id
        ).first()

        if not offboarding:
            raise ValueError(f"Offboarding not found: {offboarding_id}")

        if offboarding.status not in [OffboardingStatus.NOTICE_PERIOD, OffboardingStatus.PENDING_SETTLEMENT]:
            raise ValueError(f"Cannot approve settlement in status: {offboarding.status}")

        # Apply adjustments if any
        if adjustments and offboarding.settlement_breakdown:
            breakdown = offboarding.settlement_breakdown.copy()
            for key, value in adjustments.items():
                if key in breakdown:
                    breakdown[key] = str(value)
            # Recalculate total
            total = sum(
                Decimal(str(breakdown.get(k, "0")))
                for k in ["pro_rata_salary", "unused_leave_payout", "gratuity_eosb",
                         "pending_reimbursements", "pending_expenses"]
            ) - Decimal(str(breakdown.get("deductions", "0")))
            breakdown["total_settlement"] = str(total)
            offboarding.settlement_breakdown = breakdown
            offboarding.final_settlement_amount = total

        offboarding.settlement_approved_by = approved_by
        offboarding.settlement_approved_date = datetime.now(timezone.utc)
        offboarding.status = OffboardingStatus.PENDING_DOCUMENTS

        self.db.commit()
        self.db.refresh(offboarding)

        logger.info(
            "Settlement approved",
            extra={
                "offboarding_id": offboarding_id,
                "approved_by": approved_by,
            }
        )

        return offboarding

    async def generate_offboarding_documents(
        self,
        offboarding_id: str,
    ) -> dict:
        """
        Generate offboarding documents.

        Creates:
        - Termination letter
        - Experience letter
        - Clearance certificate

        Args:
            offboarding_id: Offboarding record ID

        Returns:
            Dict with document URLs
        """
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.id == offboarding_id
        ).first()

        if not offboarding:
            raise ValueError(f"Offboarding not found: {offboarding_id}")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == offboarding.contractor_id
        ).first()

        if not contractor:
            raise ValueError(f"Contractor not found: {offboarding.contractor_id}")

        # Document generation would go here
        # For now, we'll set placeholder URLs
        # In production, use PDF generators and upload to storage

        documents = {
            "termination_letter_url": None,
            "experience_letter_url": None,
            "clearance_certificate_url": None,
        }

        # Update offboarding record with document URLs
        offboarding.termination_letter_url = documents.get("termination_letter_url")
        offboarding.experience_letter_url = documents.get("experience_letter_url")
        offboarding.clearance_certificate_url = documents.get("clearance_certificate_url")
        offboarding.status = OffboardingStatus.PENDING_APPROVAL

        self.db.commit()

        logger.info(
            "Offboarding documents generated",
            extra={
                "offboarding_id": offboarding_id,
                "contractor_id": contractor.id,
            }
        )

        return documents

    async def complete_offboarding(
        self,
        offboarding_id: str,
        completed_by: str,
    ) -> OffboardingRecord:
        """
        Complete the offboarding process.

        Args:
            offboarding_id: Offboarding record ID
            completed_by: User ID completing

        Returns:
            Completed offboarding record
        """
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.id == offboarding_id
        ).first()

        if not offboarding:
            raise ValueError(f"Offboarding not found: {offboarding_id}")

        if offboarding.status not in [OffboardingStatus.PENDING_APPROVAL, OffboardingStatus.PENDING_DOCUMENTS]:
            raise ValueError(f"Cannot complete offboarding in status: {offboarding.status}")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == offboarding.contractor_id
        ).first()

        if not contractor:
            raise ValueError(f"Contractor not found: {offboarding.contractor_id}")

        # Update offboarding record
        offboarding.status = OffboardingStatus.COMPLETED
        offboarding.completed_date = datetime.now(timezone.utc)

        # Update contractor
        contractor.status = ContractorStatus.OFFBOARDED
        contractor.offboarding_status = OffboardingStatus.COMPLETED.value
        contractor.offboarded_date = datetime.now(timezone.utc)
        contractor.is_offboarded = "true"

        self.db.commit()
        self.db.refresh(offboarding)

        logger.info(
            "Offboarding completed",
            extra={
                "offboarding_id": offboarding_id,
                "contractor_id": contractor.id,
                "completed_by": completed_by,
            }
        )

        return offboarding

    async def cancel_offboarding(
        self,
        offboarding_id: str,
        cancelled_by: str,
        reason: str,
    ) -> OffboardingRecord:
        """
        Cancel an offboarding process.

        Args:
            offboarding_id: Offboarding record ID
            cancelled_by: User ID cancelling
            reason: Cancellation reason

        Returns:
            Cancelled offboarding record
        """
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.id == offboarding_id
        ).first()

        if not offboarding:
            raise ValueError(f"Offboarding not found: {offboarding_id}")

        if offboarding.status == OffboardingStatus.COMPLETED:
            raise ValueError("Cannot cancel completed offboarding")

        if offboarding.status == OffboardingStatus.CANCELLED:
            raise ValueError("Offboarding already cancelled")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == offboarding.contractor_id
        ).first()

        if not contractor:
            raise ValueError(f"Contractor not found: {offboarding.contractor_id}")

        # Update offboarding record
        offboarding.status = OffboardingStatus.CANCELLED
        offboarding.cancelled_by = cancelled_by
        offboarding.cancelled_date = datetime.now(timezone.utc)
        offboarding.cancellation_reason = reason

        # Restore contractor to active
        contractor.status = ContractorStatus.ACTIVE
        contractor.offboarding_status = None
        contractor.offboarding_reason = None

        self.db.commit()
        self.db.refresh(offboarding)

        logger.info(
            "Offboarding cancelled",
            extra={
                "offboarding_id": offboarding_id,
                "contractor_id": contractor.id,
                "cancelled_by": cancelled_by,
                "reason": reason,
            }
        )

        return offboarding

    async def get_offboarding_status(
        self,
        contractor_id: str,
    ) -> OffboardingStatusResponse:
        """
        Get offboarding status for a contractor.

        Args:
            contractor_id: Contractor ID

        Returns:
            Offboarding status response
        """
        contractor = self.db.query(Contractor).filter(Contractor.id == contractor_id).first()
        if not contractor:
            raise ValueError(f"Contractor not found: {contractor_id}")

        # Find active offboarding
        offboarding = self.db.query(OffboardingRecord).filter(
            OffboardingRecord.contractor_id == contractor_id,
            OffboardingRecord.status.notin_([OffboardingStatus.COMPLETED, OffboardingStatus.CANCELLED])
        ).first()

        if not offboarding:
            return OffboardingStatusResponse(
                contractor_id=contractor_id,
                is_offboarding=False,
            )

        # Calculate days remaining
        days_remaining = None
        if offboarding.last_working_date:
            delta = offboarding.last_working_date - date.today()
            days_remaining = max(0, delta.days)

        return OffboardingStatusResponse(
            contractor_id=contractor_id,
            is_offboarding=True,
            current_status=offboarding.status,
            offboarding_id=offboarding.id,
            reason=offboarding.reason,
            notice_start_date=offboarding.notice_start_date,
            last_working_date=offboarding.last_working_date,
            days_remaining=days_remaining,
            settlement_approved=offboarding.settlement_approved_by is not None,
            documents_generated=offboarding.termination_letter_url is not None,
        )

    async def get_offboarding_by_id(
        self,
        offboarding_id: str,
    ) -> Optional[OffboardingRecord]:
        """Get offboarding record by ID."""
        return self.db.query(OffboardingRecord).filter(
            OffboardingRecord.id == offboarding_id
        ).first()

    async def list_offboardings(
        self,
        status: Optional[OffboardingStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list:
        """List offboarding records with optional filtering."""
        query = self.db.query(OffboardingRecord)

        if status:
            query = query.filter(OffboardingRecord.status == status)

        return query.order_by(OffboardingRecord.initiated_date.desc()).offset(skip).limit(limit).all()
