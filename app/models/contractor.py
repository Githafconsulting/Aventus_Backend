from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
#  Updated contractor statuses


class ContractorStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_DOCUMENTS = "pending_documents"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    # Route-specific statuses
    PENDING_COHF = "pending_cohf"  # UAE route: Waiting for COHF completion
    AWAITING_COHF_SIGNATURE = "awaiting_cohf_signature"  # UAE route: COHF sent to 3rd party, awaiting signature
    COHF_COMPLETED = "cohf_completed"  # UAE route: COHF done, ready for CDS
    PENDING_THIRD_PARTY_QUOTE = "pending_third_party_quote"  # Saudi route: Waiting for 3rd party quote sheet
    PENDING_THIRD_PARTY_RESPONSE = "pending_third_party_response"
    PENDING_CDS_CS = "pending_cds_cs"
    CDS_CS_COMPLETED = "cds_cs_completed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PENDING_CLIENT_WO_SIGNATURE = "pending_client_wo_signature"
    WORK_ORDER_COMPLETED = "work_order_completed"
    # Contract statuses
    PENDING_CONTRACT_UPLOAD = "pending_contract_upload"
    PENDING_3RD_PARTY_CONTRACT = "pending_3rd_party_contract"  # UAE route: Waiting for 3rd party to send contract
    CONTRACT_UPLOADED = "contract_uploaded"
    CONTRACT_APPROVED = "contract_approved"
    PENDING_SIGNATURE = "pending_signature"
    PENDING_SUPERADMIN_SIGNATURE = "pending_superadmin_signature"
    SIGNED = "signed"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class OnboardingRoute(str, enum.Enum):
    """Onboarding route types - 5 distinct routes"""
    WPS = "wps"
    FREELANCER = "freelancer"
    UAE = "uae"  # UAE 3rd Party
    SAUDI = "saudi"  # Saudi 3rd Party
    OFFSHORE = "offshore"


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

    # Third Party Route Data (Saudi Quote Sheet)
    third_party_company_id = Column(String, nullable=True)  # ID of selected third party
    third_party_email_sent_date = Column(DateTime(timezone=True), nullable=True)
    third_party_response_received_date = Column(DateTime(timezone=True), nullable=True)
    third_party_document = Column(String, nullable=True)  # Path to uploaded 3rd party document

    # Quote Sheet Data (Saudi Route) - similar to COHF for UAE
    quote_sheet_data = Column(JSON, nullable=True)  # Quote Sheet form data
    quote_sheet_status = Column(String, nullable=True)  # draft, sent_to_3rd_party, submitted

    # Third Party Quote Sheet Signatures
    quote_sheet_third_party_signature = Column(Text, nullable=True)  # Third party signature data
    quote_sheet_third_party_name = Column(String, nullable=True)  # Name of third party signer
    quote_sheet_third_party_signed_date = Column(DateTime(timezone=True), nullable=True)

    # Aventus Admin Counter-signature for Quote Sheet
    quote_sheet_aventus_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    quote_sheet_aventus_signature_data = Column(Text, nullable=True)  # Name or base64 image
    quote_sheet_aventus_signed_date = Column(DateTime(timezone=True), nullable=True)
    quote_sheet_aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)  # Admin who signed

    # COHF (Cost of Hire Form) - UAE Route
    cohf_data = Column(JSON, nullable=True)  # COHF form data
    cohf_submitted_date = Column(DateTime(timezone=True), nullable=True)
    cohf_sent_to_3rd_party_date = Column(DateTime(timezone=True), nullable=True)
    cohf_docusign_received_date = Column(DateTime(timezone=True), nullable=True)
    cohf_completed_date = Column(DateTime(timezone=True), nullable=True)
    cohf_status = Column(String, nullable=True)  # draft, sent_to_3rd_party, signed, completed
    cohf_token = Column(String, unique=True, nullable=True, index=True)  # Token for 3rd party to access COHF
    cohf_token_expiry = Column(DateTime(timezone=True), nullable=True)
    cohf_signed_document = Column(String, nullable=True)  # URL to signed COHF PDF
    cohf_third_party_signature = Column(Text, nullable=True)  # Signature data from 3rd party
    cohf_third_party_name = Column(String, nullable=True)  # Name of person who signed

    # Aventus Admin Counter-signature for COHF
    cohf_aventus_signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    cohf_aventus_signature_data = Column(Text, nullable=True)  # Name or base64 image
    cohf_aventus_signed_date = Column(DateTime(timezone=True), nullable=True)
    cohf_aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)  # Admin who signed

    # UAE 3rd Party Contract Upload
    third_party_contract_url = Column(String, nullable=True)  # URL to contract uploaded by 3rd party
    third_party_contract_uploaded_date = Column(DateTime(timezone=True), nullable=True)
    third_party_contract_upload_token = Column(String, unique=True, nullable=True, index=True)
    third_party_contract_token_expiry = Column(DateTime(timezone=True), nullable=True)

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
    middle_names = Column(String, nullable=True)  # NEW: All middle names
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)  # "Male" or "Female"
    nationality = Column(String, nullable=False)
    country = Column(String, nullable=True)  # Current country
    country_of_residence = Column(String, nullable=True)  # NEW: Country of residence
    current_location = Column(String, nullable=True)  # Current city/location
    marital_status = Column(String, nullable=True)  # "Single", "Married", "Divorced", "Widowed"
    number_of_children = Column(String, nullable=True)
    # Address fields (renamed for clarity)
    address_line1 = Column(String, nullable=True)  # NEW: Primary address line
    home_address = Column(String, nullable=False)  # Legacy - keep for backward compatibility
    address_line2 = Column(String, nullable=True)
    address_line3 = Column(String, nullable=True)
    address_line4 = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    mobile_no = Column(String, nullable=True)  # NEW: Mobile number (alias)
    email = Column(String, unique=True, index=True, nullable=False)
    dob = Column(String, nullable=False)
    # Contractor Banking Details (NEW)
    contractor_bank_name = Column(String, nullable=True)
    contractor_account_name = Column(String, nullable=True)
    contractor_account_no = Column(String, nullable=True)
    contractor_iban = Column(String, nullable=True)
    contractor_swift_bic = Column(String, nullable=True)

    # Management Company
    business_type = Column(String, nullable=True)  # "3RD Party", "Freelancer", "Aventus"
    third_party_id = Column(String, nullable=True)  # ID of third party company if business_type is "3RD Party"
    umbrella_company_name = Column(String, nullable=True)
    registered_address = Column(String, nullable=True)
    management_address_line2 = Column(String, nullable=True)
    management_address_line3 = Column(String, nullable=True)
    company_vat_no = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    iban_number = Column(String, nullable=True)
    company_reg_no = Column(String, nullable=True)
    # NEW Management Company Fields
    mgmt_address_line1 = Column(String, nullable=True)
    mgmt_address_line2 = Column(String, nullable=True)
    mgmt_address_line3 = Column(String, nullable=True)
    mgmt_address_line4 = Column(String, nullable=True)
    mgmt_country = Column(String, nullable=True)
    mgmt_bank_name = Column(String, nullable=True)
    mgmt_account_name = Column(String, nullable=True)
    mgmt_account_number = Column(String, nullable=True)
    mgmt_iban_number = Column(String, nullable=True)
    mgmt_swift_bic = Column(String, nullable=True)

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
    # Rate type: "monthly" or "day"
    rate_type = Column(String, nullable=True, default="monthly")
    # Monthly rate fields
    charge_rate_month = Column(String, nullable=True)
    gross_salary = Column(String, nullable=True)
    # Day rate fields
    charge_rate_day = Column(String, nullable=True)
    day_rate = Column(String, nullable=True)
    # Legacy fields (keep for backward compatibility)
    client_charge_rate = Column(String, nullable=True)
    candidate_pay_rate = Column(String, nullable=True)
    candidate_pay_rate_period = Column(String, nullable=True)  # "day" or "month"
    candidate_basic_salary = Column(String, nullable=True)
    contractor_costs = Column(String, nullable=True)

    # Monthly Costs
    management_company_charges = Column(String, nullable=True)
    taxes = Column(String, nullable=True)
    bank_fees = Column(String, nullable=True)
    fx = Column(String, nullable=True)
    nationalisation = Column(String, nullable=True)

    # Provisions & Leave
    leave_allowance = Column(String, nullable=True)  # Annual leave days (e.g., 30)
    eosb = Column(String, nullable=True)
    vacation_days = Column(String, nullable=True)
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
    laptop_provided_by = Column(String, nullable=True)  # "Client", "Aventus", "Contractor"
    any_notes = Column(Text, nullable=True)
    upfront_invoices = Column(String, nullable=True)
    security_deposit = Column(String, nullable=True)
    laptop_provider = Column(String, nullable=True)  # Legacy field
    other_notes = Column(Text, nullable=True)  # Legacy field

    # Summary Calculations
    total_monthly_costs = Column(String, nullable=True)
    total_contractor_fixed_costs = Column(String, nullable=True)
    monthly_contractor_fixed_costs = Column(String, nullable=True)
    total_contractor_monthly_cost = Column(String, nullable=True)
    estimated_monthly_gp = Column(String, nullable=True)
    contractor_total_fixed_costs = Column(String, nullable=True)  # Legacy field

    # Aventus Deal
    consultant = Column(String, nullable=True)
    resourcer = Column(String, nullable=True)
    aventus_split = Column(String, nullable=True)  # Aventus commission split percentage
    resourcer_split = Column(String, nullable=True)  # Resourcer commission split percentage

    # Invoice Details
    timesheet_required = Column(String, nullable=True)
    timesheet_approver_name = Column(String, nullable=True)
    invoice_email = Column(String, nullable=True)  # Legacy
    invoice_email1 = Column(String, nullable=True)  # NEW: Primary invoice email
    invoice_email2 = Column(String, nullable=True)  # NEW: Secondary invoice email
    client_contact = Column(String, nullable=True)  # Legacy
    client_contact1 = Column(String, nullable=True)  # NEW: Primary client contact
    client_contact2 = Column(String, nullable=True)  # NEW: Secondary client contact
    invoice_address_line1 = Column(String, nullable=True)
    invoice_address_line2 = Column(String, nullable=True)
    invoice_address_line3 = Column(String, nullable=True)
    invoice_address_line4 = Column(String, nullable=True)
    invoice_po_box = Column(String, nullable=True)
    invoice_country = Column(String, nullable=True)
    invoice_tax_number = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)  # NEW: Alias for tax number
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
    candidate_bank_name = Column(String, nullable=True)
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
    payrolls = relationship("Payroll", back_populates="contractor")
    payslips = relationship("Payslip", back_populates="contractor")
    invoices = relationship("Invoice", back_populates="contractor")
