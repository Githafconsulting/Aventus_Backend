from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
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
    # Offboarding statuses
    NOTICE_PERIOD = "notice_period"          # In notice period before offboarding
    OFFBOARDING = "offboarding"              # Offboarding in progress
    OFFBOARDED = "offboarded"                # Successfully offboarded (terminal but rehirable)
    # Extension status
    EXTENSION_PENDING = "extension_pending"  # Contract extension in progress
    # Terminal status
    TERMINATED = "terminated"                # Contractor terminated (legacy, use OFFBOARDED)


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
    quote_sheet_token = Column(String, unique=True, nullable=True, index=True)  # Token for 3rd party to access
    quote_sheet_token_expiry = Column(DateTime(timezone=True), nullable=True)

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
    consultant_id = Column(String, ForeignKey("users.id"), nullable=True)  # User ID of consultant who created

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
    address_line1 = Column(String, nullable=True)  # Primary address line
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
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)  # ID of third party company if business_type is "3RD Party"
    umbrella_company_name = Column(String, nullable=True)
    company_vat_no = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
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
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)  # ID of the client company
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
    candidate_pay_rate_period = Column(String, nullable=True)  # "day" or "month"

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

    # Summary Calculations
    total_monthly_costs = Column(String, nullable=True)
    total_contractor_fixed_costs = Column(String, nullable=True)
    monthly_contractor_fixed_costs = Column(String, nullable=True)
    total_contractor_monthly_cost = Column(String, nullable=True)
    estimated_monthly_gp = Column(String, nullable=True)

    # Aventus Deal
    consultant = Column(String, nullable=True)
    resourcer = Column(String, nullable=True)
    aventus_split = Column(String, nullable=True)  # Aventus commission split percentage
    resourcer_split = Column(String, nullable=True)  # Resourcer commission split percentage

    # Invoice Details
    timesheet_required = Column(String, nullable=True)
    timesheet_approver_name = Column(String, nullable=True)
    invoice_email1 = Column(String, nullable=True)  # Primary invoice email
    invoice_email2 = Column(String, nullable=True)  # NEW: Secondary invoice email
    client_contact1 = Column(String, nullable=True)  # Primary client contact
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

    # Offboarding fields
    offboarding_status = Column(String, nullable=True)  # Quick status check
    offboarded_date = Column(DateTime(timezone=True), nullable=True)
    offboarding_reason = Column(String, nullable=True)
    is_offboarded = Column(String, nullable=True, default="false")  # For easy querying

    # Extension tracking
    current_extension_id = Column(String, nullable=True)  # Current active extension
    total_extensions = Column(String, nullable=True, default="0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==========================================
    # HYBRID PROPERTIES — backward-compat aliases for dropped legacy columns
    # ==========================================
    @hybrid_property
    def home_address(self):
        return self.address_line1

    @home_address.setter
    def home_address(self, value):
        self.address_line1 = value

    @hybrid_property
    def registered_address(self):
        return self.mgmt_address_line1

    @registered_address.setter
    def registered_address(self, value):
        self.mgmt_address_line1 = value

    @hybrid_property
    def management_address_line2(self):
        return self.mgmt_address_line2

    @management_address_line2.setter
    def management_address_line2(self, value):
        self.mgmt_address_line2 = value

    @hybrid_property
    def management_address_line3(self):
        return self.mgmt_address_line3

    @management_address_line3.setter
    def management_address_line3(self, value):
        self.mgmt_address_line3 = value

    @hybrid_property
    def bank_name(self):
        return self.mgmt_bank_name

    @bank_name.setter
    def bank_name(self, value):
        self.mgmt_bank_name = value

    @hybrid_property
    def account_number(self):
        return self.mgmt_account_number

    @account_number.setter
    def account_number(self, value):
        self.mgmt_account_number = value

    @hybrid_property
    def iban_number(self):
        return self.mgmt_iban_number

    @iban_number.setter
    def iban_number(self, value):
        self.mgmt_iban_number = value

    @hybrid_property
    def invoice_email(self):
        return self.invoice_email1

    @invoice_email.setter
    def invoice_email(self, value):
        self.invoice_email1 = value

    @hybrid_property
    def client_contact(self):
        return self.client_contact1

    @client_contact.setter
    def client_contact(self, value):
        self.client_contact1 = value

    @hybrid_property
    def client_charge_rate(self):
        return self.charge_rate_month

    @client_charge_rate.setter
    def client_charge_rate(self, value):
        self.charge_rate_month = value

    @hybrid_property
    def candidate_pay_rate(self):
        return self.gross_salary

    @candidate_pay_rate.setter
    def candidate_pay_rate(self, value):
        self.gross_salary = value

    @hybrid_property
    def candidate_basic_salary(self):
        return self.gross_salary

    @candidate_basic_salary.setter
    def candidate_basic_salary(self, value):
        self.gross_salary = value

    @hybrid_property
    def contractor_costs(self):
        return None  # Derivable, no canonical column

    @hybrid_property
    def contractor_total_fixed_costs(self):
        return self.total_contractor_fixed_costs

    @contractor_total_fixed_costs.setter
    def contractor_total_fixed_costs(self, value):
        self.total_contractor_fixed_costs = value

    @hybrid_property
    def laptop_provider(self):
        return self.laptop_provided_by

    @laptop_provider.setter
    def laptop_provider(self, value):
        self.laptop_provided_by = value

    @hybrid_property
    def other_notes(self):
        return self.any_notes

    @other_notes.setter
    def other_notes(self, value):
        self.any_notes = value

    # ==========================================
    # PROPERTIES — resolved from FK relationships (Phase 6)
    # ==========================================
    @property
    def client_name(self):
        try:
            return self.client.company_name if self.client else None
        except Exception:
            return None

    @client_name.setter
    def client_name(self, value):
        pass  # Derived from client relationship

    @property
    def consultant_name(self):
        try:
            return self.consultant_user.name if self.consultant_user else None
        except Exception:
            return None

    @consultant_name.setter
    def consultant_name(self, value):
        pass  # Derived from consultant_user relationship

    # FK-referenced relationships (for name resolution)
    client = relationship("Client", foreign_keys=[client_id], lazy="select")
    consultant_user = relationship("User", foreign_keys=[consultant_id], lazy="select")
    third_party = relationship("ThirdParty", foreign_keys=[third_party_id], lazy="select")

    # Relationships (cascade delete to clean up related records when contractor is deleted)
    timesheets = relationship("Timesheet", back_populates="contractor", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="contractor", cascade="all, delete-orphan")
    payrolls = relationship("Payroll", back_populates="contractor", cascade="all, delete-orphan")
    payslips = relationship("Payslip", back_populates="contractor", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="contractor", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="contractor", cascade="all, delete-orphan")
    quote_sheets = relationship("QuoteSheet", back_populates="contractor", cascade="all, delete-orphan")
    offboarding_records = relationship("OffboardingRecord", back_populates="contractor", cascade="all, delete-orphan")
    contract_extensions = relationship("ContractExtension", back_populates="contractor", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="contractor", cascade="all, delete-orphan")
    contractor_documents = relationship("ContractorDocument", back_populates="contractor", cascade="all, delete-orphan")

    @property
    def other_documents(self):
        """Backward-compat property: serialize child docs as list of dicts."""
        return [
            {
                "type": d.document_type,
                "name": d.name,
                "url": d.url,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                "work_order_id": d.work_order_id,
                "contract_id": d.contract_id,
                "signed_by": d.signed_by,
            }
            for d in (self.contractor_documents or [])
        ]


class ContractorDocument(Base):
    __tablename__ = "contractor_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String, nullable=True)
    name = Column(String, nullable=True)
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    work_order_id = Column(String, nullable=True)
    contract_id = Column(String, nullable=True)
    signed_by = Column(String, nullable=True)

    contractor = relationship("Contractor", back_populates="contractor_documents")
