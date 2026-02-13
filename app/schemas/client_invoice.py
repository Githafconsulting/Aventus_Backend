from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from app.models.client_invoice import ClientInvoiceStatus


class ClientInvoiceLineItemResponse(BaseModel):
    id: int
    payroll_id: Optional[int] = None
    contractor_id: Optional[str] = None
    contractor_name: Optional[str] = None
    description: Optional[str] = None
    subtotal: float = 0
    vat_amount: float = 0
    total: float = 0

    class Config:
        from_attributes = True


class ClientInvoicePaymentResponse(BaseModel):
    id: int
    amount: float
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientInvoiceListResponse(BaseModel):
    id: int
    client_id: str
    period: str
    invoice_number: str
    subtotal: float = 0
    vat_rate: float = 0.05
    vat_amount: float = 0
    total_amount: float = 0
    amount_paid: float = 0
    balance: float = 0
    currency: str = "AED"
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: ClientInvoiceStatus
    client_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClientInvoiceDetailResponse(ClientInvoiceListResponse):
    payment_terms: Optional[str] = None
    pdf_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    line_items: List[ClientInvoiceLineItemResponse] = []
    payments: List[ClientInvoicePaymentResponse] = []

    class Config:
        from_attributes = True


class ClientInvoiceStatsResponse(BaseModel):
    total: int = 0
    draft: int = 0
    sent: int = 0
    partially_paid: int = 0
    paid: int = 0
    overdue: int = 0
    total_outstanding: float = 0


class GenerateClientInvoiceRequest(BaseModel):
    client_id: str
    period: str
    payment_terms: Optional[str] = "Net 30"
    notes: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    amount: float
    payment_date: date
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
