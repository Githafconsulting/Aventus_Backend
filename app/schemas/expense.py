from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ExpenseCreate(BaseModel):
    date: date
    category: str
    description: str
    amount: float
    currency: Optional[str] = "AED"


class ExpenseResponse(BaseModel):
    id: int
    contractor_id: str
    contractor_name: Optional[str] = None
    date: date
    month: str
    year: int
    month_number: int
    category: str
    description: str
    amount: float
    currency: str
    receipt_url: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExpenseReviewRequest(BaseModel):
    action: str  # "approve" or "reject"
    rejection_reason: Optional[str] = None


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: int
    total_amount: float
    approved_amount: float
    pending_amount: float
    rejected_amount: float
