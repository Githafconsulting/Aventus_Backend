from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


class ContractorUpdate(BaseModel):
    """Schema for updating contractor"""
    first_name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Cost of Hire fields
    recruitment_cost: Optional[str] = None
    onboarding_cost: Optional[str] = None
    equipment_cost: Optional[str] = None
    administrative_cost: Optional[str] = None
    relocation_cost: Optional[str] = None
    total_cost_of_hire: Optional[str] = None
    cost_of_hire_notes: Optional[str] = None
    cost_breakdown: Optional[Dict[str, Any]] = None

    # Add other fields as needed


class SignatureSubmission(BaseModel):
    """Schema for contractor signature submission"""
    signature_type: str  # "typed" or "drawn"
    signature_data: str  # Name or base64 image


class ContractorInitialCreate(BaseModel):
    """Schema for consultant's initial contractor creation (Step 1)"""
    first_name: str
    surname: str
    email: EmailStr
    phone: str


class CostingSheetData(BaseModel):
    """Schema for costing sheet submission by consultant"""
    # Personal Details (if not already filled)
    gender: Optional[str] = None
    nationality: Optional[str] = None
    home_address: Optional[str] = None
    dob: Optional[str] = None

    # Placement Details
    client_name: str
    role: str
    start_date: str
    end_date: str
    location: str
    duration: Optional[str] = None
    currency: str = "SAR"

    # Rates & Costs
    client_charge_rate: str
    candidate_pay_rate: str
    candidate_pay_rate_period: Optional[str] = None
    candidate_basic_salary: Optional[str] = None
    contractor_costs: Optional[str] = None

    # Monthly Costs
    management_company_charges: Optional[str] = None
    taxes: Optional[str] = None
    bank_fees: Optional[str] = None
    fx: Optional[str] = None
    nationalisation: Optional[str] = None

    # Provisions
    eosb: Optional[str] = None
    vacation_days: Optional[str] = None
    vacation_pay: Optional[str] = None
    sick_leave: Optional[str] = None
    other_provision: Optional[str] = None

    # One Time Costs
    flights: Optional[str] = None
    visa: Optional[str] = None
    medical_insurance: Optional[str] = None
    family_costs: Optional[str] = None
    other_one_time_costs: Optional[str] = None

    # Additional Info
    upfront_invoices: Optional[str] = None
    security_deposit: Optional[str] = None
    laptop_provider: Optional[str] = None
    other_notes: Optional[str] = None

    # Management Company
    business_type: Optional[str] = None  # "3RD Party", "Freelancer", "Aventus"
    third_party_id: Optional[str] = None  # ID of third party company if business_type is "3RD Party"
    umbrella_company_name: Optional[str] = None
    registered_address: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    company_reg_no: Optional[str] = None

    # Client Details
    client_office_address: Optional[str] = None
    client_address_line2: Optional[str] = None
    client_address_line3: Optional[str] = None
    client_po_box: Optional[str] = None
    po_required: Optional[str] = None
    po_number: Optional[str] = None
    client_tax_number: Optional[str] = None
    contractor_pay_frequency: Optional[str] = None
    client_invoice_frequency: Optional[str] = None
    client_payment_terms: Optional[str] = None
    invoicing_preferences: Optional[str] = None
    invoice_instructions: Optional[str] = None
    supporting_docs_required: Optional[str] = None

    # Payment Details
    umbrella_or_direct: Optional[str] = None
    candidate_bank_name: Optional[str] = None
    candidate_bank_details: Optional[str] = None
    candidate_account_number: Optional[str] = None
    candidate_mobile: Optional[str] = None
    current_location: Optional[str] = None


class DocumentUploadData(BaseModel):
    """Schema for document uploads and personal information by contractor"""
    # Personal Information
    first_name: str
    surname: str
    email: EmailStr
    gender: str
    dob: str
    nationality: str
    country: Optional[str] = None
    current_location: Optional[str] = None
    marital_status: Optional[str] = None
    number_of_children: Optional[str] = None
    phone: str
    home_address: str
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    address_line4: Optional[str] = None
    candidate_bank_name: Optional[str] = None
    candidate_bank_details: Optional[str] = None
    candidate_iban: Optional[str] = None

    # Documents (handled as file uploads in the route)
    passport_document: Optional[str] = None  # base64 or file path
    photo_document: Optional[str] = None
    visa_page_document: Optional[str] = None
    id_front_document: Optional[str] = None
    id_back_document: Optional[str] = None
    emirates_id_document: Optional[str] = None
    degree_document: Optional[str] = None
    other_documents: Optional[List[Dict[str, str]]] = None  # [{"name": "...", "data": "..."}]


class SuperadminSignatureData(BaseModel):
    """Schema for superadmin signature"""
    signature_type: str  # "typed" or "drawn"
    signature_data: str  # Name or base64 image


class ContractorApproval(BaseModel):
    """Schema for admin/superadmin approval"""
    approved: bool
    notes: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document information"""
    document_name: str
    document_type: str  # "passport", "photo", "visa", "emirates_id", "degree", "contract", "other"
    document_url: Optional[str] = None
    uploaded_date: Optional[datetime] = None


class ContractorResponse(BaseModel):
    """Schema for contractor response"""
    id: str
    status: str
    first_name: str
    surname: str
    email: str
    phone: str
    nationality: Optional[str] = None
    role: Optional[str] = None
    client_name: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    contract_token: Optional[str] = None
    document_upload_token: Optional[str] = None
    consultant_name: Optional[str] = None
    sent_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None
    activated_date: Optional[datetime] = None
    documents_uploaded_date: Optional[datetime] = None
    reviewed_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Document fields for counting uploaded documents
    passport_document: Optional[str] = None
    photo_document: Optional[str] = None
    visa_page_document: Optional[str] = None
    id_front_document: Optional[str] = None
    id_back_document: Optional[str] = None
    emirates_id_document: Optional[str] = None
    degree_document: Optional[str] = None
    third_party_document: Optional[str] = None
    other_documents: Optional[Dict[str, Any]] = None

    # Costing sheet data for checking if CDS is completed
    costing_sheet_data: Optional[Dict[str, Any]] = None

    # Onboarding route
    onboarding_route: Optional[str] = None

    class Config:
        from_attributes = True


class RouteSelection(BaseModel):
    """Schema for selecting onboarding route"""
    route: str  # "wps", "freelancer", "uae", "saudi", "offshore"
    sub_route: Optional[str] = "direct"  # "direct" or "third_party" (for UAE and SAUDI)


class ThirdPartyRequest(BaseModel):
    """Schema for sending third party request"""
    third_party_id: str
    email_subject: str
    email_body: str


class QuoteSheetRequest(BaseModel):
    """Schema for sending quote sheet request with direct email (for SAUDI route)"""
    third_party_id: Optional[str] = None  # Optional third party ID if selecting from dropdown
    third_party_email: str
    email_cc: Optional[str] = None  # Optional CC email
    email_subject: str
    email_message: str


class ContractorDetailResponse(BaseModel):
    """Schema for detailed contractor response"""
    id: str
    status: str

    # All fields from the model
    first_name: str
    surname: str
    gender: Optional[str] = None
    nationality: Optional[str] = None
    country: Optional[str] = None
    current_location: Optional[str] = None
    marital_status: Optional[str] = None
    number_of_children: Optional[str] = None
    home_address: Optional[str] = None
    address_line2: Optional[str] = None
    address_line3: Optional[str] = None
    address_line4: Optional[str] = None
    phone: str
    email: str
    dob: Optional[str] = None
    candidate_bank_name: Optional[str] = None
    candidate_bank_details: Optional[str] = None
    candidate_iban: Optional[str] = None

    # Optional fields
    client_name: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    currency: str = "SAR"

    # Contract details
    contract_token: Optional[str] = None
    signature_type: Optional[str] = None
    signature_data: Optional[str] = None
    generated_contract: Optional[str] = None

    # Document upload
    document_upload_token: Optional[str] = None
    passport_document: Optional[str] = None
    photo_document: Optional[str] = None
    visa_page_document: Optional[str] = None
    id_front_document: Optional[str] = None
    id_back_document: Optional[str] = None
    emirates_id_document: Optional[str] = None
    degree_document: Optional[str] = None
    third_party_document: Optional[str] = None
    other_documents: Optional[Dict[str, Any]] = None

    # Superadmin signature
    superadmin_signature_type: Optional[str] = None
    superadmin_signature_data: Optional[str] = None

    # Consultant info
    consultant_id: Optional[str] = None
    consultant_name: Optional[str] = None

    # Cost of Hire
    recruitment_cost: Optional[str] = None
    onboarding_cost: Optional[str] = None
    equipment_cost: Optional[str] = None
    administrative_cost: Optional[str] = None
    relocation_cost: Optional[str] = None
    total_cost_of_hire: Optional[str] = None
    cost_of_hire_notes: Optional[str] = None
    cost_breakdown: Optional[Dict[str, Any]] = None

    # Dates
    sent_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None
    activated_date: Optional[datetime] = None
    documents_uploaded_date: Optional[datetime] = None
    reviewed_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Onboarding route
    onboarding_route: Optional[str] = None

    # CDS form data (Step 2)
    cds_form_data: Optional[Dict[str, Any]] = None

    # Costing sheet data
    costing_sheet_data: Optional[Dict[str, Any]] = None

    # Management Company fields
    business_type: Optional[str] = None
    third_party_id: Optional[str] = None
    umbrella_company_name: Optional[str] = None
    registered_address: Optional[str] = None
    management_address_line2: Optional[str] = None
    management_address_line3: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    company_reg_no: Optional[str] = None

    # Placement Details
    client_id: Optional[str] = None
    project_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    client_charge_rate: Optional[str] = None
    candidate_pay_rate: Optional[str] = None
    candidate_pay_rate_period: Optional[str] = None
    candidate_basic_salary: Optional[str] = None
    contractor_costs: Optional[str] = None

    # Monthly Costs
    management_company_charges: Optional[str] = None
    taxes: Optional[str] = None
    bank_fees: Optional[str] = None
    fx: Optional[str] = None
    nationalisation: Optional[str] = None

    # Provisions
    eosb: Optional[str] = None
    vacation_days: Optional[str] = None
    vacation_pay: Optional[str] = None
    sick_leave: Optional[str] = None
    other_provision: Optional[str] = None

    # One Time Costs
    flights: Optional[str] = None
    visa: Optional[str] = None
    medical_insurance: Optional[str] = None
    family_costs: Optional[str] = None
    other_one_time_costs: Optional[str] = None

    # Additional Info
    laptop_provided_by: Optional[str] = None
    any_notes: Optional[str] = None
    upfront_invoices: Optional[str] = None
    security_deposit: Optional[str] = None
    laptop_provider: Optional[str] = None
    other_notes: Optional[str] = None

    # Summary Calculations
    total_monthly_costs: Optional[str] = None
    total_contractor_fixed_costs: Optional[str] = None
    monthly_contractor_fixed_costs: Optional[str] = None
    total_contractor_monthly_cost: Optional[str] = None
    estimated_monthly_gp: Optional[str] = None
    contractor_total_fixed_costs: Optional[str] = None

    # Aventus Deal
    consultant: Optional[str] = None
    any_splits: Optional[str] = None
    resourcer: Optional[str] = None

    # Invoice Details
    timesheet_required: Optional[str] = None
    timesheet_approver_name: Optional[str] = None
    invoice_email: Optional[str] = None
    client_contact: Optional[str] = None
    invoice_address_line1: Optional[str] = None
    invoice_address_line2: Optional[str] = None
    invoice_address_line3: Optional[str] = None
    invoice_address_line4: Optional[str] = None
    invoice_po_box: Optional[str] = None
    invoice_country: Optional[str] = None
    invoice_tax_number: Optional[str] = None
    contractor_pay_frequency: Optional[str] = None
    client_invoice_frequency: Optional[str] = None
    client_payment_terms: Optional[str] = None
    invoicing_preferences: Optional[str] = None
    invoice_instructions: Optional[str] = None
    supporting_docs_required: Optional[str] = None
    po_required: Optional[str] = None
    po_number: Optional[str] = None

    # Pay Details
    umbrella_or_direct: Optional[str] = None

    class Config:
        from_attributes = True
