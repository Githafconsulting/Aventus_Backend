from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    payroll_id: int
    payment_terms: Optional[str] = "Net 30"
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceBulkSend(BaseModel):
    invoice_ids: List[int]


class InvoicePaymentCreate(BaseModel):
    amount: float
    payment_date: date
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class InvoicePaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    payment_date: date
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: int
    payroll_id: int
    client_id: str
    contractor_id: str
    invoice_number: str
    subtotal: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    amount_paid: float
    balance: float
    invoice_date: date
    due_date: date
    payment_terms: Optional[str] = None
    pdf_url: Optional[str] = None
    status: InvoiceStatus
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Nested info
    client_name: Optional[str] = None
    contractor_name: Optional[str] = None
    period: Optional[str] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceDetailResponse(InvoiceResponse):
    """Extended invoice with payments"""
    payments: List[InvoicePaymentResponse] = []

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    id: int
    payroll_id: int
    client_id: str
    client_name: Optional[str] = None
    contractor_id: str
    contractor_name: Optional[str] = None
    invoice_number: str
    total_amount: float
    amount_paid: float
    balance: float
    currency: Optional[str] = None
    invoice_date: date
    due_date: date
    status: InvoiceStatus
    period: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoicePortalResponse(BaseModel):
    """Response for client portal access"""
    id: int
    invoice_number: str
    client_name: Optional[str] = None
    contractor_name: Optional[str] = None
    period: Optional[str] = None
    subtotal: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    amount_paid: float
    balance: float
    currency: Optional[str] = None
    invoice_date: date
    due_date: date
    payment_terms: Optional[str] = None
    pdf_url: Optional[str] = None
    status: InvoiceStatus
    payments: List[InvoicePaymentResponse] = []

    class Config:
        from_attributes = True


class InvoiceStatsResponse(BaseModel):
    total: int
    draft: int
    sent: int
    partially_paid: int
    paid: int
    overdue: int
    total_outstanding: float
    total_overdue: float
