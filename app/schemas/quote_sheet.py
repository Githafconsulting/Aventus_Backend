from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.quote_sheet import QuoteSheetStatus


class QuoteSheetBase(BaseModel):
    contractor_id: str
    third_party_id: Optional[str] = None
    contractor_name: Optional[str] = None
    third_party_company_name: Optional[str] = None
    proposed_rate: Optional[float] = None
    currency: Optional[str] = "AED"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class QuoteSheetCreate(QuoteSheetBase):
    pass


class QuoteSheetUpload(BaseModel):
    document_url: str
    document_filename: str
    proposed_rate: Optional[float] = None
    currency: Optional[str] = "AED"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class QuoteSheetUpdate(BaseModel):
    proposed_rate: Optional[float] = None
    currency: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    consultant_notes: Optional[str] = None
    status: Optional[QuoteSheetStatus] = None


class QuoteSheetResponse(QuoteSheetBase):
    id: str
    consultant_id: str
    upload_token: str
    token_expiry: datetime
    document_url: Optional[str] = None
    document_filename: Optional[str] = None
    additional_documents: Optional[List[Dict[str, Any]]] = []
    status: QuoteSheetStatus
    consultant_notes: Optional[str] = None
    created_at: datetime
    uploaded_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
