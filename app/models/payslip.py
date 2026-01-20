from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class PayslipStatus(str, enum.Enum):
    GENERATED = "generated"
    SENT = "sent"
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"


class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), nullable=False)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Document Identification
    document_number = Column(String, unique=True, nullable=False, index=True)  # PS-2025-000001
    period = Column(String, nullable=False)  # "January 2025"

    # PDF Storage
    pdf_storage_key = Column(String, nullable=True)  # Supabase storage key
    pdf_url = Column(String, nullable=True)  # Public/signed URL

    # Status Workflow
    status = Column(SQLEnum(PayslipStatus), default=PayslipStatus.GENERATED)
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Portal Access
    access_token = Column(String, unique=True, nullable=True, index=True)
    token_expiry = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payroll = relationship("Payroll", back_populates="payslip")
    contractor = relationship("Contractor", back_populates="payslips")
