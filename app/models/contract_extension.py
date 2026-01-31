"""
Contract Extension Model.

Manages contract extension requests and approvals for contractors.
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Integer, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DECIMAL
from app.database import Base
import enum


class ExtensionStatus(str, enum.Enum):
    """Status of a contract extension request."""
    DRAFT = "draft"                         # Extension request created
    PENDING_APPROVAL = "pending_approval"   # Awaiting admin approval
    APPROVED = "approved"                   # Approved, pending signature
    PENDING_SIGNATURE = "pending_signature" # Sent for contractor signature
    SIGNED = "signed"                       # Contractor signed, pending counter-sign
    COMPLETED = "completed"                 # Extension completed and applied
    REJECTED = "rejected"                   # Extension rejected


class ContractExtension(Base):
    """
    Contract extension record.

    Tracks extension requests including new terms, approval workflow,
    and signature process.
    """
    __tablename__ = "contract_extensions"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Contractor reference
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False, index=True)

    # Extension details
    original_end_date = Column(Date, nullable=False)
    new_end_date = Column(Date, nullable=False)
    extension_months = Column(Integer, nullable=False)

    # Optional rate changes
    new_monthly_rate = Column(DECIMAL(15, 2), nullable=True)
    new_day_rate = Column(DECIMAL(15, 2), nullable=True)
    rate_change_reason = Column(Text, nullable=True)

    # Status & Workflow
    status = Column(
        SQLEnum(ExtensionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ExtensionStatus.DRAFT
    )

    # Request tracking
    requested_by = Column(String, ForeignKey("users.id"), nullable=False)
    requested_date = Column(DateTime(timezone=True), server_default=func.now())

    # Approval tracking
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    rejected_by = Column(String, ForeignKey("users.id"), nullable=True)
    rejected_date = Column(DateTime(timezone=True), nullable=True)

    # Extension document
    extension_document_url = Column(String, nullable=True)

    # Signature workflow - Contractor
    signature_token = Column(String, unique=True, nullable=True, index=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    contractor_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    contractor_signature_data = Column(Text, nullable=True)
    contractor_signed_date = Column(DateTime(timezone=True), nullable=True)

    # Signature workflow - Aventus counter-signature
    aventus_signature_type = Column(String, nullable=True)
    aventus_signature_data = Column(Text, nullable=True)
    aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)
    aventus_signed_date = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contractor = relationship("Contractor", back_populates="contract_extensions")
