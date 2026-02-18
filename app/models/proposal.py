from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Text, Enum as SQLEnum
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
    project_name = Column(String, nullable=False)
    project_description = Column(Text, nullable=True)

    # Scope and Deliverables
    scope_of_work = Column(Text, nullable=True)

    # Timeline
    estimated_duration = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Financial
    currency = Column(String, nullable=True, default="AED")
    total_amount = Column(Float, nullable=True)

    # Additional Terms
    terms_and_conditions = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)

    # Documents
    proposal_content = Column(Text, nullable=True)  # Generated HTML/PDF content
    document_url = Column(String, nullable=True)

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

    # Properties — resolved from FK relationships (Phase 6)
    @property
    def client_company_name(self):
        try:
            return self.client.company_name if self.client else None
        except Exception:
            return None

    @client_company_name.setter
    def client_company_name(self, value):
        pass

    # Relationships
    client = relationship("Client", backref="proposals")
    consultant = relationship("User", backref="proposals")
    proposal_deliverables = relationship("ProposalDeliverable", back_populates="proposal", cascade="all, delete-orphan")
    proposal_milestones = relationship("ProposalMilestone", back_populates="proposal", cascade="all, delete-orphan")
    proposal_payment_items = relationship("ProposalPaymentItem", back_populates="proposal", cascade="all, delete-orphan")
    proposal_attachments = relationship("ProposalAttachment", back_populates="proposal", cascade="all, delete-orphan")

    @property
    def deliverables(self):
        return [{"title": d.title, "description": d.description} for d in (self.proposal_deliverables or [])]

    @property
    def milestones(self):
        return [
            {"name": m.title, "date": m.due_date.isoformat() if m.due_date else None, "description": m.description}
            for m in (self.proposal_milestones or [])
        ]

    @property
    def payment_schedule(self):
        return [
            {"phase": p.description, "amount": p.amount, "due_date": p.due_date.isoformat() if p.due_date else None, "percentage": p.percentage}
            for p in (self.proposal_payment_items or [])
        ]

    @property
    def attachments(self):
        return [
            {"filename": a.filename, "url": a.url, "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None}
            for a in (self.proposal_attachments or [])
        ]


class ProposalDeliverable(Base):
    __tablename__ = "proposal_deliverables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)

    proposal = relationship("Proposal", back_populates="proposal_deliverables")


class ProposalMilestone(Base):
    __tablename__ = "proposal_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)

    proposal = relationship("Proposal", back_populates="proposal_milestones")


class ProposalPaymentItem(Base):
    __tablename__ = "proposal_payment_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    due_date = Column(DateTime, nullable=True)
    percentage = Column(Float, nullable=True)
    sort_order = Column(Integer, default=0)

    proposal = relationship("Proposal", back_populates="proposal_payment_items")


class ProposalAttachment(Base):
    __tablename__ = "proposal_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String, ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=True)
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    proposal = relationship("Proposal", back_populates="proposal_attachments")
