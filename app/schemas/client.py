from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Project(BaseModel):
    """Project schema for client projects"""
    name: str
    description: Optional[str] = None
    status: Optional[str] = "Planning"
    third_party_id: Optional[str] = None
    third_party_name: Optional[str] = None


class ClientBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    third_party_id: str = Field(..., min_length=1)
    industry: Optional[str] = None
    company_reg_no: Optional[str] = None
    company_vat_no: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    address_line4: Optional[str] = None
    country: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    contact_person_title: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

    # Workflow Configuration
    work_order_applicable: Optional[bool] = False
    proposal_applicable: Optional[bool] = False

    # Timesheet Configuration
    timesheet_required: Optional[bool] = False
    timesheet_approver_name: Optional[str] = None

    # Payment Terms
    po_required: Optional[bool] = False
    po_number: Optional[str] = None
    contractor_pay_frequency: Optional[str] = None
    client_invoice_frequency: Optional[str] = None
    client_payment_terms: Optional[str] = None
    invoicing_preferences: Optional[str] = None
    invoice_delivery_method: Optional[str] = None
    invoice_instructions: Optional[str] = None

    # Supporting Documents
    supporting_documents_required: Optional[List[str]] = []

    # Projects
    projects: Optional[List[Project]] = []

    is_active: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    third_party_id: Optional[str] = None
    industry: Optional[str] = None
    company_reg_no: Optional[str] = None
    company_vat_no: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    address_line4: Optional[str] = None
    country: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    contact_person_title: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

    # Workflow Configuration
    work_order_applicable: Optional[bool] = None
    proposal_applicable: Optional[bool] = None

    # Timesheet Configuration
    timesheet_required: Optional[bool] = None
    timesheet_approver_name: Optional[str] = None

    # Payment Terms
    po_required: Optional[bool] = None
    po_number: Optional[str] = None
    contractor_pay_frequency: Optional[str] = None
    client_invoice_frequency: Optional[str] = None
    client_payment_terms: Optional[str] = None
    invoicing_preferences: Optional[str] = None
    invoice_delivery_method: Optional[str] = None
    invoice_instructions: Optional[str] = None

    # Supporting Documents
    supporting_documents_required: Optional[List[str]] = None

    # Projects
    projects: Optional[List[Project]] = None

    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: str
    third_party_id: Optional[str] = None
    documents: Optional[List[Dict[str, Any]]] = []
    projects: Optional[List[Dict[str, Any]]] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
