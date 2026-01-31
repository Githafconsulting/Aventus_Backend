"""
Offboarding Model.

Manages contractor offboarding process including contract endings,
resignations, terminations, and transfers.
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey, Integer, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL
from app.database import Base
import enum


class OffboardingReason(str, enum.Enum):
    """Reasons for offboarding a contractor."""
    CONTRACT_END = "contract_end"           # Natural contract expiry
    RESIGNATION = "resignation"             # Contractor resigned
    TERMINATION = "termination"             # Company terminated
    TRANSFER = "transfer"                   # Transfer to another employer
    MUTUAL_AGREEMENT = "mutual_agreement"   # Both parties agreed


class OffboardingStatus(str, enum.Enum):
    """Status of the offboarding process."""
    INITIATED = "initiated"                 # Process started
    NOTICE_PERIOD = "notice_period"         # In notice period
    PENDING_SETTLEMENT = "pending_settlement"  # Calculating/reviewing settlement
    PENDING_DOCUMENTS = "pending_documents"    # Generating offboarding documents
    PENDING_APPROVAL = "pending_approval"   # Final approval needed
    COMPLETED = "completed"                 # Successfully offboarded
    CANCELLED = "cancelled"                 # Offboarding cancelled


class OffboardingRecord(Base):
    """
    Offboarding record for tracking contractor exit process.

    Tracks the full offboarding workflow including notice period,
    final settlement, document generation, and completion.
    """
    __tablename__ = "offboarding_records"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Contractor reference
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False, index=True)

    # Offboarding details
    reason = Column(
        SQLEnum(OffboardingReason, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status = Column(
        SQLEnum(OffboardingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=OffboardingStatus.INITIATED
    )

    # Dates
    initiated_date = Column(DateTime(timezone=True), server_default=func.now())
    initiated_by = Column(String, ForeignKey("users.id"), nullable=False)
    notice_period_days = Column(Integer, default=30)
    notice_start_date = Column(Date, nullable=True)
    last_working_date = Column(Date, nullable=False)
    effective_termination_date = Column(Date, nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)

    # Settlement information
    final_settlement_amount = Column(DECIMAL(15, 2), nullable=True)
    settlement_breakdown = Column(JSON, nullable=True)  # Detailed breakdown
    settlement_approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    settlement_approved_date = Column(DateTime(timezone=True), nullable=True)

    # Document URLs (stored in Supabase or similar)
    termination_letter_url = Column(String, nullable=True)
    experience_letter_url = Column(String, nullable=True)
    clearance_certificate_url = Column(String, nullable=True)
    final_payslip_url = Column(String, nullable=True)

    # Transfer specific fields (if reason = TRANSFER)
    transfer_to_employer = Column(String, nullable=True)
    transfer_effective_date = Column(Date, nullable=True)

    # Notes and audit trail
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_by = Column(String, ForeignKey("users.id"), nullable=True)
    cancelled_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contractor = relationship("Contractor", back_populates="offboarding_records")
