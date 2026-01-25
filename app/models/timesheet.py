from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class TimesheetStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DECLINED = "declined"

class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Period information
    month = Column(String, nullable=False)  # e.g., "November 2024"
    year = Column(Integer, nullable=False)
    month_number = Column(Integer, nullable=False)  # 1-12

    # Timesheet data
    timesheet_data = Column(JSON, nullable=True)  # Stores the daily entries

    # Summary
    total_days = Column(Float, default=0)
    work_days = Column(Integer, default=0)
    sick_days = Column(Integer, default=0)
    vacation_days = Column(Integer, default=0)
    holiday_days = Column(Integer, default=0)
    unpaid_days = Column(Integer, default=0)

    # Status and approval
    status = Column(SQLEnum(TimesheetStatus), default=TimesheetStatus.PENDING_APPROVAL)
    submitted_date = Column(DateTime, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    declined_date = Column(DateTime, nullable=True)

    # Manager and notes
    manager_name = Column(String, nullable=True)
    manager_email = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    decline_reason = Column(Text, nullable=True)

    # Review token for manager access
    review_token = Column(String, unique=True, nullable=True, index=True)
    review_token_expiry = Column(DateTime, nullable=True)

    # File uploads
    timesheet_file_url = Column(String, nullable=True)
    approval_file_url = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contractor = relationship("Contractor", back_populates="timesheets")
    payroll = relationship("Payroll", back_populates="timesheet", uselist=False)
