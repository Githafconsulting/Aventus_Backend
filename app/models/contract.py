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
    PENDING_AVENTUS_SIGNATURE = "pending_aventus_signature"  # Contractor signed, awaiting Aventus counter-sign
    SIGNED = "signed"  # Both parties signed
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

    # Aventus counter-signature
    aventus_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    aventus_signature_data = Column(Text, nullable=True)
    aventus_signer_name = Column(String, nullable=True)  # Name of person who counter-signed (e.g., Richard)
    aventus_signed_date = Column(DateTime(timezone=True), nullable=True)
    aventus_signed_by = Column(String, nullable=True)  # User ID who counter-signed

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

    # Properties — resolved from FK relationships (Phase 6)
    @property
    def consultant_name(self):
        try:
            c = self.contractor
            return f"{c.first_name} {c.surname}" if c else None
        except Exception:
            return None

    @consultant_name.setter
    def consultant_name(self, value):
        pass

    @property
    def client_name(self):
        try:
            c = self.contractor
            return c.client.company_name if c and c.client else None
        except Exception:
            return None

    @client_name.setter
    def client_name(self, value):
        pass

    @property
    def client_address(self):
        try:
            c = self.contractor
            if c and c.client:
                client = c.client
                parts = [p for p in [client.address_line1, client.address_line2, client.address_line3, client.address_line4, client.country] if p]
                return ", ".join(parts) if parts else None
        except Exception:
            pass
        return None

    @client_address.setter
    def client_address(self, value):
        pass

    @property
    def job_title(self):
        try:
            return self.contractor.role if self.contractor else None
        except Exception:
            return None

    @job_title.setter
    def job_title(self, value):
        pass

    # Relationships
    contractor = relationship("Contractor", back_populates="contracts")
    template = relationship("ContractTemplate", back_populates="contracts")
