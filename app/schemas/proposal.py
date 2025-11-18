from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.proposal import ProposalStatus


class ProposalBase(BaseModel):
    client_id: str
    client_company_name: Optional[str] = None
    project_name: str
    project_description: Optional[str] = None
    scope_of_work: Optional[str] = None
    deliverables: Optional[List[Dict[str, Any]]] = []
    estimated_duration: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    milestones: Optional[List[Dict[str, Any]]] = []
    currency: Optional[str] = "AED"
    total_amount: Optional[float] = None
    payment_schedule: Optional[List[Dict[str, Any]]] = []
    terms_and_conditions: Optional[str] = None
    assumptions: Optional[str] = None
    exclusions: Optional[str] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    client_id: Optional[str] = None
    client_company_name: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    scope_of_work: Optional[str] = None
    deliverables: Optional[List[Dict[str, Any]]] = None
    estimated_duration: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    payment_schedule: Optional[List[Dict[str, Any]]] = None
    terms_and_conditions: Optional[str] = None
    assumptions: Optional[str] = None
    exclusions: Optional[str] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[ProposalStatus] = None


class ProposalResponse(ProposalBase):
    id: str
    proposal_number: str
    consultant_id: str
    proposal_content: Optional[str] = None
    document_url: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    status: ProposalStatus
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
