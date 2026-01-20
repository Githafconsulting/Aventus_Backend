from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.payslip import PayslipStatus


class PayslipBase(BaseModel):
    period: str
    document_number: Optional[str] = None


class PayslipCreate(BaseModel):
    payroll_id: int


class PayslipBulkCreate(BaseModel):
    payroll_ids: List[int]


class PayslipBulkSend(BaseModel):
    payslip_ids: List[int]


class PayslipResponse(BaseModel):
    id: int
    payroll_id: int
    contractor_id: str
    document_number: str
    period: str
    pdf_url: Optional[str] = None
    status: PayslipStatus
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Nested info
    contractor_name: Optional[str] = None
    contractor_email: Optional[str] = None
    client_name: Optional[str] = None
    net_salary: Optional[float] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


class PayslipListResponse(BaseModel):
    id: int
    payroll_id: int
    contractor_id: str
    contractor_name: str
    contractor_email: Optional[str] = None
    client_name: Optional[str] = None
    document_number: str
    period: str
    net_salary: Optional[float] = None
    currency: Optional[str] = None
    status: PayslipStatus
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PayslipPortalResponse(BaseModel):
    """Response for contractor portal access"""
    id: int
    document_number: str
    period: str
    pdf_url: Optional[str] = None
    status: PayslipStatus
    contractor_name: str
    net_salary: Optional[float] = None
    currency: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PayslipStatsResponse(BaseModel):
    total: int
    generated: int
    sent: int
    viewed: int
    acknowledged: int
