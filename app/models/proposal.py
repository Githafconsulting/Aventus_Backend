from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum


class ProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_number = Column(String, unique=True, nullable=False, index=True)

    # Relationships
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    consultant_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Proposal Details
    client_company_name = Column(String, nullable=True)
    project_name = Column(String, nullable=False)
    project_description = Column(Text, nullable=True)

    # Scope and Deliverables
    scope_of_work = Column(Text, nullable=True)
    deliverables = Column(JSON, default=list)  # List of deliverables

    # Timeline
    estimated_duration = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    milestones = Column(JSON, default=list)

    # Financial
    currency = Column(String, nullable=True, default="AED")
    total_amount = Column(Float, nullable=True)
    payment_schedule = Column(JSON, default=list)

    # Additional Terms
    terms_and_conditions = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)

    # Documents
    proposal_content = Column(Text, nullable=True)  # Generated HTML/PDF content
    document_url = Column(String, nullable=True)
    attachments = Column(JSON, default=list)

    # Status
    status = Column(SQLEnum(ProposalStatus), default=ProposalStatus.DRAFT, nullable=False)

    # Tracking
    valid_until = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="proposals")
    consultant = relationship("User", backref="proposals")
