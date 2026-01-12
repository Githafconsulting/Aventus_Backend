from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class PayrollStatus(str, enum.Enum):
    PENDING = "pending"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"), unique=True, nullable=False)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Pay calculation
    day_rate = Column(Float, nullable=False)  # Rate per day at calculation time
    work_days = Column(Float, nullable=False)  # Days worked
    gross_amount = Column(Float, nullable=False)  # day_rate * work_days
    deductions = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)  # gross - deductions
    currency = Column(String(10), default="USD")

    # Invoice fields (for client billing)
    charge_rate_day = Column(Float, nullable=True)  # Client charge rate
    invoice_amount = Column(Float, nullable=True)  # charge_rate * work_days

    # Status workflow: PENDING -> CALCULATED -> APPROVED -> PAID
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.CALCULATED)

    # Period info (cached from timesheet)
    period = Column(String, nullable=True)  # e.g., "November 2024"

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    timesheet = relationship("Timesheet", back_populates="payroll")
    contractor = relationship("Contractor", back_populates="payrolls")
    approver = relationship("User", foreign_keys=[approved_by])
