"""
Contract Extension Schemas.

Pydantic models for contract extension requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.contract_extension import ExtensionStatus


class RequestExtensionRequest(BaseModel):
    """Request to create a contract extension."""
    new_end_date: date
    extension_months: int = Field(..., ge=1, le=60, description="Extension duration in months")

    # Optional rate changes
    new_monthly_rate: Optional[Decimal] = None
    new_day_rate: Optional[Decimal] = None
    rate_change_reason: Optional[str] = None

    notes: Optional[str] = None


class ApproveExtensionRequest(BaseModel):
    """Request to approve an extension."""
    notes: Optional[str] = None


class RejectExtensionRequest(BaseModel):
    """Request to reject an extension."""
    reason: str = Field(..., min_length=10, description="Reason for rejection")


class ExtensionSignatureRequest(BaseModel):
    """Request to submit signature for extension."""
    signature_type: str = Field(..., pattern="^(typed|drawn)$")
    signature_data: str = Field(..., min_length=1, description="Name for typed, base64 for drawn")


class ContractExtensionResponse(BaseModel):
    """Response for contract extension."""
    id: str
    contractor_id: str
    original_end_date: date
    new_end_date: date
    extension_months: int

    # Rate changes
    new_monthly_rate: Optional[Decimal] = None
    new_day_rate: Optional[Decimal] = None
    rate_change_reason: Optional[str] = None

    # Status & workflow
    status: ExtensionStatus
    requested_by: str
    requested_date: datetime
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_date: Optional[datetime] = None

    # Document
    extension_document_url: Optional[str] = None

    # Contractor signature
    contractor_signed_date: Optional[datetime] = None
    has_contractor_signature: bool = False

    # Aventus counter-signature
    aventus_signed_date: Optional[datetime] = None
    has_aventus_signature: bool = False

    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContractExtensionListResponse(BaseModel):
    """List response for contract extensions."""
    id: str
    contractor_id: str
    contractor_name: Optional[str] = None
    original_end_date: date
    new_end_date: date
    extension_months: int
    status: ExtensionStatus
    requested_date: datetime
    has_rate_change: bool = False

    class Config:
        from_attributes = True


class ExtensionSigningPageResponse(BaseModel):
    """Public signing page response."""
    extension_id: str
    contractor_name: Optional[str] = None
    client_name: Optional[str] = None
    original_end_date: date
    new_end_date: date
    extension_months: int
    new_monthly_rate: Optional[Decimal] = None
    new_day_rate: Optional[Decimal] = None
    rate_change_reason: Optional[str] = None
    extension_document_url: Optional[str] = None
    already_signed: bool = False
    token_expired: bool = False

    class Config:
        from_attributes = True


class ExtensionHistoryResponse(BaseModel):
    """Response for contractor's extension history."""
    contractor_id: str
    total_extensions: int
    extensions: list[ContractExtensionListResponse]

    class Config:
        from_attributes = True
