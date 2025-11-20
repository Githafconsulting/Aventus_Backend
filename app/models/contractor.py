from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
#  Updated contractor statuses


class ContractorStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_DOCUMENTS = "pending_documents"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    PENDING_THIRD_PARTY_RESPONSE = "pending_third_party_response"
    PENDING_CDS_CS = "pending_cds_cs"
    CDS_CS_COMPLETED = "cds_cs_completed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PENDING_CLIENT_WO_SIGNATURE = "pending_client_wo_signature"
    WORK_ORDER_COMPLETED = "work_order_completed"
    PENDING_CONTRACT_UPLOAD = "pending_contract_upload"
    CONTRACT_UPLOADED = "contract_uploaded"
    CONTRACT_APPROVED = "contract_approved"
    PENDING_SIGNATURE = "pending_signature"
    PENDING_SUPERADMIN_SIGNATURE = "pending_superadmin_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class OnboardingRoute(str, enum.Enum):
    WPS_FREELANCER = "wps_freelancer"
    THIRD_PARTY = "third_party"


class SignatureType(str, enum.Enum):
    TYPED = "typed"
    DRAWN = "drawn"


class Contractor(Base):
    """Contractor model for contractor management"""
    __tablename__ = "contractors"

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Status & Workflow
    status = Column(SQLEnum(ContractorStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ContractorStatus.DRAFT)
    onboarding_route = Column(SQLEnum(OnboardingRoute, values_callable=lambda x: [e.value for e in x]), nullable=True)  # WPS/Freelancer or Third Party
    contract_token = Column(String, unique=True, nullable=True, index=True)
    signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    signature_data = Column(Text, nullable=True)  # Name for typed, base64 for drawn
    sent_date = Column(DateTime(timezone=True), nullable=True)
    signed_date = Column(DateTime(timezone=True), nullable=True)
    activated_date = Column(DateTime(timezone=True), nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)

    # Third Party Route Data
    third_party_company_id = Column(String, nullable=True)  # ID of selected third party
    third_party_email_sent_date = Column(DateTime(timezone=True), nullable=True)
    third_party_response_received_date = Column(DateTime(timezone=True), nullable=True)
    third_party_document = Column(String, nullable=True)  # Path to uploaded 3rd party document

    # Document Upload Workflow
    document_upload_token = Column(String, unique=True, nullable=True, index=True)
    document_token_expiry = Column(DateTime(timezone=True), nullable=True)
    documents_uploaded_date = Column(DateTime(timezone=True), nullable=True)

    # Uploaded Documents (file paths or URLs)
    passport_document = Column(String, nullable=True)
    photo_document = Column(String, nullable=True)
    visa_page_document = Column(String, nullable=True)
    id_front_document = Column(String, nullable=True)
    id_back_document = Column(String, nullable=True)
    emirates_id_document = Column(String, nullable=True)
    degree_document = Column(String, nullable=True)
    other_documents = Column(JSON, nullable=True)  # Array of additional documents

    # Client Contract Upload Workflow
    contract_upload_token = Column(String, unique=True, nullable=True, index=True)
    contract_upload_token_expiry = Column(DateTime(timezone=True), nullable=True)
    client_uploaded_contract = Column(String, nullable=True)  # Path to contract uploaded by client
    contract_uploaded_date = Column(DateTime(timezone=True), nullable=True)
    contract_approved_date = Column(DateTime(timezone=True), nullable=True)
    contract_approved_by = Column(String, nullable=True)  # User ID of superadmin who approved contract

    # Superadmin Signature
    superadmin_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    superadmin_signature_data = Column(Text, nullable=True)  # Name for typed, base64 for drawn

    # Signed Contract (Generated after both parties sign)
    signed_contract_url = Column(String, nullable=True)  # URL to final signed PDF in Supabase

    # Review & Approval Tracking
    reviewed_date = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)  # User ID of admin/superadmin who reviewed
    approved_date = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)  # User ID of admin/superadmin who approved

    # Consultant Tracking
    consultant_id = Column(String, nullable=True)  # User ID of consultant who created
    consultant_name = Column(String, nullable=True)

    # Costing Sheet Data (filled by consultant)
    costing_sheet_data = Column(JSON, nullable=True)

    # Personal Details
    first_name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)  # "Male" or "Female"
    nationality = Column(String, nullable=False)
    country = Column(String, nullable=True)  # Current country
    current_location = Column(String, nullable=True)  # Current city/location
    marital_status = Column(String, nullable=True)  # "Single", "Married", "Divorced", "Widowed"
    number_of_children = Column(String, nullable=True)
    home_address = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    address_line3 = Column(String, nullable=True)
    address_line4 = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    dob = Column(String, nullable=False)

    # Management Company
    business_type = Column(String, nullable=True)  # "3RD Party", "Freelancer", "Aventus"
    third_party_id = Column(String, nullable=True)  # ID of third party company if business_type is "3RD Party"
    umbrella_company_name = Column(String, nullable=True)
    registered_address = Column(String, nullable=True)
    management_address_line2 = Column(String, nullable=True)
    management_address_line3 = Column(String, nullable=True)
    company_vat_no = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    iban_number = Column(String, nullable=True)
    company_reg_no = Column(String, nullable=True)

    # Placement Details
    client_id = Column(String, nullable=True)  # ID of the client company
    client_name = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    currency = Column(String, nullable=False, default="AED")
    client_charge_rate = Column(String, nullable=True)
    candidate_pay_rate = Column(String, nullable=True)
    candidate_basic_salary = Column(String, nullable=True)
    contractor_costs = Column(String, nullable=True)

    # Monthly Costs
    management_company_charges = Column(String, nullable=True)
    taxes = Column(String, nullable=True)
    bank_fees = Column(String, nullable=True)
    fx = Column(String, nullable=True)
    nationalisation = Column(String, nullable=True)

    # Provisions
    eosb = Column(String, nullable=True)
    vacation_pay = Column(String, nullable=True)
    sick_leave = Column(String, nullable=True)
    other_provision = Column(String, nullable=True)

    # One Time Costs
    flights = Column(String, nullable=True)
    visa = Column(String, nullable=True)
    medical_insurance = Column(String, nullable=True)
    family_costs = Column(String, nullable=True)
    other_one_time_costs = Column(String, nullable=True)

    # Additional Info
    upfront_invoices = Column(String, nullable=True)
    security_deposit = Column(String, nullable=True)
    laptop_provider = Column(String, nullable=True)
    other_notes = Column(Text, nullable=True)

    # Summary Calculations
    contractor_total_fixed_costs = Column(String, nullable=True)
    estimated_monthly_gp = Column(String, nullable=True)

    # Aventus Deal
    consultant = Column(String, nullable=True)
    any_splits = Column(String, nullable=True)
    resourcer = Column(String, nullable=True)

    # Invoice Details
    timesheet_required = Column(String, nullable=True)
    timesheet_approver_name = Column(String, nullable=True)
    invoice_email = Column(String, nullable=True)
    client_contact = Column(String, nullable=True)
    invoice_address_line1 = Column(String, nullable=True)
    invoice_address_line2 = Column(String, nullable=True)
    invoice_address_line3 = Column(String, nullable=True)
    invoice_address_line4 = Column(String, nullable=True)
    invoice_po_box = Column(String, nullable=True)
    invoice_tax_number = Column(String, nullable=True)
    contractor_pay_frequency = Column(String, nullable=True)
    client_invoice_frequency = Column(String, nullable=True)
    client_payment_terms = Column(String, nullable=True)
    invoicing_preferences = Column(String, nullable=True)
    invoice_instructions = Column(Text, nullable=True)
    supporting_docs_required = Column(String, nullable=True)
    po_required = Column(String, nullable=True)
    po_number = Column(String, nullable=True)

    # Pay Details
    umbrella_or_direct = Column(String, nullable=True)
    candidate_bank_details = Column(String, nullable=True)
    candidate_iban = Column(String, nullable=True)

    # CDS Form Data (Step 2) - Stored as JSON for flexibility
    cds_form_data = Column(JSON, nullable=True)

    # Generated Contract
    generated_contract = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    timesheets = relationship("Timesheet", back_populates="contractor")
    contracts = relationship("Contract", back_populates="contractor")
