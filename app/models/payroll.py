from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class PayrollStatus(str, enum.Enum):
    PENDING = "pending"
    CALCULATED = "calculated"
    APPROVED = "approved"
    APPROVED_ADJUSTED = "approved_adjusted"
    MISMATCH_3RD_PARTY = "mismatch_3rd_party"
    PAID = "paid"


class RateType(str, enum.Enum):
    MONTHLY = "monthly"
    DAILY = "daily"


class Payroll(Base):
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"), unique=True, nullable=False)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Basic Info
    period = Column(String, nullable=True)  # e.g., "November 2024"
    currency = Column(String(10), default="AED")
    rate_type = Column(SQLEnum(RateType), default=RateType.MONTHLY)

    # Basic Calculation - Monthly Rate
    monthly_rate = Column(Float, nullable=True)  # From CDS
    total_calendar_days = Column(Integer, nullable=True)  # Total days in month
    days_worked = Column(Float, nullable=True)  # From timesheet or default to calendar days
    prorata_day_rate = Column(Float, nullable=True)  # Monthly rate / total calendar days
    gross_pay = Column(Float, nullable=True)  # Monthly rate or (days worked x day rate)

    # Basic Calculation - Day Rate
    day_rate = Column(Float, nullable=True)  # From CDS

    # Leave Adjustments
    leave_allowance = Column(Float, default=0)  # From CDS (annual leave days)
    carry_over_leave = Column(Float, default=0)  # From previous year (max 5)
    total_leave_allowance = Column(Float, default=0)  # leave_allowance + carry_over
    total_leave_taken = Column(Float, default=0)  # Sum from timesheets this year
    leave_balance = Column(Float, default=0)  # total_leave_allowance - total_leave_taken
    previous_month_days_worked = Column(Float, nullable=True)  # For reference
    leave_deductibles = Column(Float, default=0)  # Deduction if negative leave balance

    # Expenses
    expenses_reimbursement = Column(Float, default=0)  # From expenses form

    # Net Salary
    net_salary = Column(Float, nullable=True)  # Final net salary calculation

    # 3rd Party Accruals
    total_accruals = Column(Float, default=0)  # Sum of all accruals

    # Individual accrual fields (for common ones)
    accrual_gosi = Column(Float, default=0)
    accrual_salary_transfer = Column(Float, default=0)
    accrual_admin_costs = Column(Float, default=0)
    accrual_gratuity = Column(Float, default=0)
    accrual_airfare = Column(Float, default=0)
    accrual_annual_leave = Column(Float, default=0)
    accrual_other = Column(Float, default=0)

    # Management Fee
    management_fee = Column(Float, default=0)  # From CDS - Management company charges

    # Invoice Calculation
    invoice_total = Column(Float, nullable=True)  # Net salary + accruals + management fee
    vat_rate = Column(Float, default=0.05)  # 5% UAE, 15% Saudi
    vat_amount = Column(Float, default=0)  # Invoice total x VAT rate
    total_payable = Column(Float, nullable=True)  # Invoice total + VAT

    # Legacy fields for backward compatibility
    deductions = Column(Float, default=0)
    net_amount = Column(Float, nullable=True)
    charge_rate_day = Column(Float, nullable=True)
    invoice_amount = Column(Float, nullable=True)

    # Batch reference (nullable for backward compatibility)
    batch_id = Column(Integer, ForeignKey("payroll_batches.id"), nullable=True)

    # 3rd party reconciliation
    tp_draft_amount = Column(Float, nullable=True)
    reconciliation_notes = Column(Text, nullable=True)
    adjusted_by = Column(String, ForeignKey("users.id"), nullable=True)
    adjusted_at = Column(DateTime, nullable=True)

    # Status workflow: PENDING -> CALCULATED -> APPROVED -> PAID
    status = Column(SQLEnum(PayrollStatus), default=PayrollStatus.CALCULATED)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Properties — resolved from FK relationships (Phase 6)
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
    def third_party_name(self):
        try:
            c = self.contractor
            return c.third_party.company_name if c and c.third_party else None
        except Exception:
            return None

    @third_party_name.setter
    def third_party_name(self, value):
        pass

    @property
    def country(self):
        try:
            return self.contractor.onboarding_route if self.contractor else None
        except Exception:
            return None

    @country.setter
    def country(self, value):
        pass

    # Relationships
    timesheet = relationship("Timesheet", back_populates="payroll")
    contractor = relationship("Contractor", back_populates="payrolls")
    approver = relationship("User", foreign_keys=[approved_by])
    adjuster = relationship("User", foreign_keys=[adjusted_by])
    payslip = relationship("Payslip", back_populates="payroll", uselist=False)
    invoice = relationship("Invoice", back_populates="payroll", uselist=False)
    batch = relationship("PayrollBatch", back_populates="payrolls")
