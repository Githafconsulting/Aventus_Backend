from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class CustomField(BaseModel):
    field_name: str
    value_type: Literal["text", "radio"]
    value: Optional[str] = None
    options: Optional[List[str]] = None  # For radio buttons


class WorkflowConfig(BaseModel):
    # Document Applicability
    quote_sheet_applicable: Optional[bool] = False
    cds_applicable: Optional[bool] = False  # Contract Deal Sheet
    cost_sheet_applicable: Optional[bool] = False
    work_order_applicable: Optional[bool] = False
    proposal_applicable: Optional[bool] = False
    cohf_applicable: Optional[bool] = False  # Cost of Hire Form
    contractor_contract_applicable: Optional[bool] = False

    # Contractor Contract Configuration
    contractor_contract_provider: Optional[Literal["Aventus", "Third Party"]] = None

    # Schedule Form (only if contractor_contract_applicable is False)
    schedule_form_applicable: Optional[bool] = False

    # Custom Fields
    custom_fields: Optional[List[CustomField]] = []


class ThirdPartyBase(BaseModel):
    # Country & Workflow Configuration
    country: Optional[str] = None
    company_type: Optional[str] = None
    workflow_config: Optional[WorkflowConfig] = None

    # Company Details
    company_name: str
    registered_address: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_reg_no: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True
    documents: Optional[List[Dict[str, Any]]] = []


class ThirdPartyCreate(ThirdPartyBase):
    pass


class ThirdPartyUpdate(BaseModel):
    # Country & Workflow Configuration
    country: Optional[str] = None
    company_type: Optional[str] = None
    workflow_config: Optional[WorkflowConfig] = None

    # Company Details
    company_name: Optional[str] = None
    registered_address: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_reg_no: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    documents: Optional[List[Dict[str, Any]]] = None


class ThirdPartyResponse(ThirdPartyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
