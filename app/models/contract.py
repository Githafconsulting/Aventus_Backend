"""
Contract models for managing contract templates and individual contracts
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ContractStatus(str, enum.Enum):
    """Contract status enum"""
    DRAFT = "draft"
    SENT = "sent"
    REVIEWED = "reviewed"
    SIGNED = "signed"
    VALIDATED = "validated"
    ACTIVATED = "activated"
    DECLINED = "declined"


class ContractTemplate(Base):
    """Template for contracts - editable by SuperAdmin"""
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Aventus Contract Template"
    template_content = Column(Text, nullable=False)  # HTML/Text content of the contract
    version = Column(String, nullable=False, default="1.0")
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)  # User ID who created

    # Relationships
    contracts = relationship("Contract", back_populates="template")


class Contract(Base):
    """Individual contracts sent to contractors"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=True)

    # Contract Content
    contract_content = Column(Text, nullable=False)  # Generated contract with auto-filled data

    # Contract Details (auto-filled from CDS)
    contract_date = Column(String, nullable=True)
    consultant_name = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    client_address = Column(Text, nullable=True)
    job_title = Column(String, nullable=True)
    commencement_date = Column(String, nullable=True)
    contract_rate = Column(String, nullable=True)
    working_location = Column(String, nullable=True)
    duration = Column(String, nullable=True)

    # Token for contractor access
    contract_token = Column(String, unique=True, nullable=False, index=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)

    # Status and workflow
    status = Column(SQLEnum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)

    # Email tracking
    sent_date = Column(DateTime(timezone=True), nullable=True)
    sent_by = Column(String, nullable=True)  # User ID who sent

    # Contractor actions
    reviewed_date = Column(DateTime(timezone=True), nullable=True)
    contractor_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    contractor_signature_data = Column(Text, nullable=True)
    contractor_signed_date = Column(DateTime(timezone=True), nullable=True)
    contractor_notes = Column(Text, nullable=True)

    # Aventus auto-signature
    aventus_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    aventus_signature_data = Column(Text, nullable=True)
    aventus_signed_date = Column(DateTime(timezone=True), nullable=True)

    # Admin validation
    validated_date = Column(DateTime(timezone=True), nullable=True)
    validated_by = Column(String, nullable=True)  # User ID who validated

    # Account activation
    activated_date = Column(DateTime(timezone=True), nullable=True)
    activated_by = Column(String, nullable=True)  # User ID who activated
    temporary_password = Column(String, nullable=True)

    # Decline tracking
    declined_date = Column(DateTime(timezone=True), nullable=True)
    decline_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contractor = relationship("Contractor", back_populates="contracts")
    template = relationship("ContractTemplate", back_populates="contracts")
