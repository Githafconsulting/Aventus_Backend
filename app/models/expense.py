from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseCategory(str, enum.Enum):
    TRAVEL = "travel"
    MEALS = "meals"
    ACCOMMODATION = "accommodation"
    SUPPLIES = "supplies"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Expense details
    date = Column(Date, nullable=False)
    month = Column(String, nullable=False)  # e.g. "February 2026" (for payroll linkage)
    year = Column(Integer, nullable=False)
    month_number = Column(Integer, nullable=False)
    category = Column(SQLEnum(ExpenseCategory, values_callable=lambda x: [e.value for e in x]), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="AED")
    receipt_url = Column(String, nullable=True)

    # Status workflow
    status = Column(SQLEnum(ExpenseStatus, values_callable=lambda x: [e.value for e in x]), default=ExpenseStatus.PENDING)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contractor = relationship("Contractor", back_populates="expenses")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
