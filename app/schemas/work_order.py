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
    documents: Optional[List[Dict[str, Any]]] = []
    created_by: str
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
