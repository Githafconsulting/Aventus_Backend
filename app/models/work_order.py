from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum


class WorkOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    PENDING_CLIENT_SIGNATURE = "pending_client_signature"
    CLIENT_SIGNED = "client_signed"
    PENDING_AVENTUS_SIGNATURE = "pending_aventus_signature"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DECLINED = "declined"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_order_number = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)

    # Work Order Details
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contractor_name = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    currency = Column(String, nullable=True, default="AED")
    business_type = Column(String, nullable=True)  # "3RD Party", "Freelancer", "Aventus"
    umbrella_company_name = Column(String, nullable=True)

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # Financial
    hourly_rate = Column(Float, nullable=True)
    fixed_price = Column(Float, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True, default=0)
    charge_rate = Column(String, nullable=True)
    pay_rate = Column(String, nullable=True)

    # Generated content
    work_order_content = Column(String, nullable=True)

    # Status
    status = Column(SQLEnum(WorkOrderStatus, values_callable=lambda x: [e.value for e in x]), default=WorkOrderStatus.DRAFT, nullable=False)

    # Additional Info
    notes = Column(String, nullable=True)
    documents = Column(JSON, default=list)  # Store uploaded document URLs and metadata

    # Client Signature
    client_signature_token = Column(String, unique=True, nullable=True, index=True)
    client_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    client_signature_data = Column(String, nullable=True)  # Name or base64 image
    client_signer_name = Column(String, nullable=True)  # Name of person who signed
    client_signed_date = Column(DateTime, nullable=True)

    # Aventus Admin Signature (Counter-signature)
    aventus_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    aventus_signature_data = Column(String, nullable=True)  # Name or base64 image
    aventus_signer_name = Column(String, nullable=True)  # Name of admin who signed
    aventus_signed_date = Column(DateTime, nullable=True)
    aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)  # Admin who signed

    # Audit fields
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    generated_by = Column(String, nullable=True)  # User ID who generated
    generated_date = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_date = Column(DateTime, nullable=True)
    sent_by = Column(String, nullable=True)  # User ID who sent
    sent_date = Column(DateTime, nullable=True)
    declined_by = Column(String, nullable=True)  # User ID who declined
    declined_date = Column(DateTime, nullable=True)
    decline_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contractor = relationship("Contractor", back_populates="work_orders")
    third_party = relationship("ThirdParty", backref="work_orders")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    aventus_signer = relationship("User", foreign_keys=[aventus_signed_by])
