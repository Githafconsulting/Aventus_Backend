"""
Offboarding Schemas.

Pydantic models for offboarding requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from app.models.offboarding import OffboardingReason, OffboardingStatus


class SettlementBreakdown(BaseModel):
    """Detailed breakdown of final settlement."""
    pro_rata_salary: Decimal = Field(default=Decimal("0"), description="Days worked in final month")
    unused_leave_payout: Decimal = Field(default=Decimal("0"), description="Accrued but unused leave")
    gratuity_eosb: Decimal = Field(default=Decimal("0"), description="End of service benefit")
    pending_reimbursements: Decimal = Field(default=Decimal("0"), description="Pending expense reimbursements")
    pending_expenses: Decimal = Field(default=Decimal("0"), description="Other pending expenses")
    deductions: Decimal = Field(default=Decimal("0"), description="Any amounts owed to company")
    total_settlement: Decimal = Field(default=Decimal("0"), description="Final settlement amount")
    currency: str = Field(default="USD", description="Currency for settlement amounts")

    # Additional details
    days_worked_final_month: int = 0
    total_leave_days_accrued: Decimal = Field(default=Decimal("0"))
    leave_days_used: Decimal = Field(default=Decimal("0"))
    leave_days_remaining: Decimal = Field(default=Decimal("0"))
    years_of_service: Decimal = Field(default=Decimal("0"))
    gratuity_rate: Decimal = Field(default=Decimal("0"), description="Days per year of service")

    class Config:
        from_attributes = True


class InitiateOffboardingRequest(BaseModel):
    """Request to initiate offboarding process."""
    reason: OffboardingReason
    last_working_date: date
    notice_period_days: int = Field(default=30, ge=0, le=180)
    notes: Optional[str] = None

    # Transfer specific fields (required if reason = TRANSFER)
    transfer_to_employer: Optional[str] = None
    transfer_effective_date: Optional[date] = None


class ApproveSettlementRequest(BaseModel):
    """Request to approve settlement calculation."""
    approved: bool = True
    adjustments: Optional[dict] = None  # Optional manual adjustments
    notes: Optional[str] = None


class CancelOffboardingRequest(BaseModel):
    """Request to cancel an offboarding process."""
    reason: str = Field(..., min_length=10, description="Reason for cancellation")


class CompleteOffboardingRequest(BaseModel):
    """Request to complete offboarding."""
    notes: Optional[str] = None


class OffboardingResponse(BaseModel):
    """Response for offboarding record."""
    id: str
    contractor_id: str
    reason: OffboardingReason
    status: OffboardingStatus

    # Dates
    initiated_date: datetime
    initiated_by: str
    notice_period_days: int
    notice_start_date: Optional[date] = None
    last_working_date: date
    effective_termination_date: Optional[date] = None
    completed_date: Optional[datetime] = None

    # Settlement
    final_settlement_amount: Optional[Decimal] = None
    settlement_breakdown: Optional[dict] = None
    settlement_approved_by: Optional[str] = None
    settlement_approved_date: Optional[datetime] = None

    # Documents
    termination_letter_url: Optional[str] = None
    experience_letter_url: Optional[str] = None
    clearance_certificate_url: Optional[str] = None
    final_payslip_url: Optional[str] = None

    # Transfer
    transfer_to_employer: Optional[str] = None
    transfer_effective_date: Optional[date] = None

    # Notes
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OffboardingListResponse(BaseModel):
    """List response for offboarding records."""
    id: str
    contractor_id: str
    contractor_name: Optional[str] = None
    reason: OffboardingReason
    status: OffboardingStatus
    initiated_date: datetime
    last_working_date: date
    final_settlement_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class OffboardingStatusResponse(BaseModel):
    """Status response for contractor offboarding."""
    contractor_id: str
    is_offboarding: bool = False
    current_status: Optional[OffboardingStatus] = None
    offboarding_id: Optional[str] = None
    reason: Optional[OffboardingReason] = None
    notice_start_date: Optional[date] = None
    last_working_date: Optional[date] = None
    days_remaining: Optional[int] = None
    settlement_approved: bool = False
    documents_generated: bool = False

    class Config:
        from_attributes = True


class OffboardingDocumentsResponse(BaseModel):
    """Response for offboarding documents."""
    offboarding_id: str
    termination_letter_url: Optional[str] = None
    experience_letter_url: Optional[str] = None
    clearance_certificate_url: Optional[str] = None
    final_payslip_url: Optional[str] = None
    all_documents_generated: bool = False

    class Config:
        from_attributes = True
