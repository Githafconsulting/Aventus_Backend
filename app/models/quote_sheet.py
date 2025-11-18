from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum


class QuoteSheetStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class QuoteSheet(Base):
    __tablename__ = "quote_sheets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relationships
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=False)
    consultant_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Upload token for secure access
    upload_token = Column(String, unique=True, nullable=False, index=True)
    token_expiry = Column(DateTime, nullable=False)

    # Quote Sheet Details
    contractor_name = Column(String, nullable=True)
    third_party_company_name = Column(String, nullable=True)

    # Financial
    proposed_rate = Column(Float, nullable=True)
    currency = Column(String, nullable=True, default="AED")
    payment_terms = Column(String, nullable=True)

    # Documents
    document_url = Column(String, nullable=True)  # Uploaded quote sheet document
    document_filename = Column(String, nullable=True)
    additional_documents = Column(JSON, default=list)

    # Status
    status = Column(SQLEnum(QuoteSheetStatus), default=QuoteSheetStatus.PENDING, nullable=False)

    # Notes and Details
    notes = Column(String, nullable=True)
    consultant_notes = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contractor = relationship("Contractor", backref="quote_sheets")
    third_party = relationship("ThirdParty", backref="quote_sheets")
    consultant = relationship("User", backref="quote_sheets")
