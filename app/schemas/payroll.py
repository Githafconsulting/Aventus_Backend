from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.payroll import PayrollStatus


class PayrollBase(BaseModel):
    day_rate: float
    work_days: float
    gross_amount: float
    deductions: float = 0
    net_amount: float
    currency: str = "USD"
    charge_rate_day: Optional[float] = None
    invoice_amount: Optional[float] = None


class PayrollCreate(BaseModel):
    timesheet_id: int
    deductions: float = 0


class PayrollUpdate(BaseModel):
    deductions: Optional[float] = None
    status: Optional[PayrollStatus] = None


class PayrollResponse(PayrollBase):
    id: int
    timesheet_id: int
    contractor_id: int
    status: PayrollStatus
    period: Optional[str] = None
    calculated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Nested contractor info
    contractor_name: Optional[str] = None
    contractor_email: Optional[str] = None
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class PayrollListResponse(BaseModel):
    id: int
    timesheet_id: int
    contractor_id: int
    contractor_name: str
    contractor_email: Optional[str] = None
    client_name: Optional[str] = None
    period: Optional[str] = None
    work_days: float
    day_rate: float
    gross_amount: float
    net_amount: float
    currency: str
    status: PayrollStatus
    charge_rate_day: Optional[float] = None
    invoice_amount: Optional[float] = None
    calculated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimesheetReadyForPayroll(BaseModel):
    """Timesheet that is approved and ready for payroll calculation"""
    id: int
    contractor_id: str
    contractor_name: str
    contractor_email: Optional[str] = None
    client_name: Optional[str] = None
    period: str
    work_days: int
    total_days: float
    day_rate: Optional[float] = None
    charge_rate_day: Optional[float] = None
    currency: str
    estimated_gross: Optional[float] = None
    submitted_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None

    class Config:
        from_attributes = True
