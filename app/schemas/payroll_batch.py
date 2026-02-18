from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.payroll_batch import BatchStatus


class PayrollInBatchResponse(BaseModel):
    id: int
    contractor_id: str
    contractor_name: Optional[str] = None
    period: Optional[str] = None
    currency: Optional[str] = None
    gross_pay: Optional[float] = None
    net_salary: Optional[float] = None
    total_accruals: Optional[float] = None
    management_fee: Optional[float] = None
    invoice_total: Optional[float] = None
    vat_amount: Optional[float] = None
    total_payable: Optional[float] = None
    status: str
    tp_draft_amount: Optional[float] = None
    reconciliation_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    adjusted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    id: int
    period: str
    client_id: str
    client_name: Optional[str] = None
    onboarding_route: str
    route_label: Optional[str] = None
    third_party_name: Optional[str] = None
    contractor_count: int = 0
    total_net_salary: float = 0
    total_payable: float = 0
    currency: str = "AED"
    status: BatchStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchDetailResponse(BatchListResponse):
    third_party_id: Optional[str] = None
    tp_invoice_url: Optional[str] = None
    tp_invoice_uploaded_at: Optional[datetime] = None
    invoice_requested_at: Optional[datetime] = None
    invoice_deadline: Optional[datetime] = None
    finance_reviewed_by: Optional[str] = None
    finance_reviewed_at: Optional[datetime] = None
    finance_notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    payrolls: List[PayrollInBatchResponse] = []

    class Config:
        from_attributes = True


class BatchStatsResponse(BaseModel):
    total: int = 0
    awaiting_approval: int = 0
    partially_approved: int = 0
    submit_for_invoice: int = 0
    invoice_requested: int = 0
    invoice_received: int = 0
    ready_for_payment: int = 0
    invoice_update_requested: int = 0
    paid: int = 0
    payslips_generated: int = 0


class AdjustPayrollRequest(BaseModel):
    net_salary: Optional[float] = None
    total_accruals: Optional[float] = None
    management_fee: Optional[float] = None
    notes: str


class FlagMismatchRequest(BaseModel):
    tp_draft_amount: float
    notes: str


class RequestInvoiceRequest(BaseModel):
    deadline_days: int = 7
    message: Optional[str] = None


class FinanceRejectRequest(BaseModel):
    notes: str


class MarkPaidRequest(BaseModel):
    payment_reference: str


class InvoiceUploadRequest(BaseModel):
    invoice_url: str
