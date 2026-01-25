from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.work_order import WorkOrderStatus


class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    contractor_id: str
    third_party_id: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    hourly_rate: Optional[float] = None
    fixed_price: Optional[float] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = 0
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    notes: Optional[str] = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    contractor_id: Optional[str] = None
    third_party_id: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    hourly_rate: Optional[float] = None
    fixed_price: Optional[float] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    status: Optional[WorkOrderStatus] = None
    notes: Optional[str] = None
    approved_by: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    id: str
    work_order_number: str
    client_name: Optional[str] = None
    contractor_name: Optional[str] = None
    project_name: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    currency: Optional[str] = None
    charge_rate: Optional[str] = None
    pay_rate: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = []
    created_by: str
    approved_by: Optional[str] = None
    client_signature_type: Optional[str] = None
    client_signature_data: Optional[str] = None
    client_signer_name: Optional[str] = None
    client_signed_date: Optional[datetime] = None
    aventus_signature_type: Optional[str] = None
    aventus_signature_data: Optional[str] = None
    aventus_signer_name: Optional[str] = None
    aventus_signed_date: Optional[datetime] = None
    aventus_signed_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
