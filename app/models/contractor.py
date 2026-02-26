from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


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
    onboarding_route = Column(SQLEnum(OnboardingRoute, values_callable=lambda x: [e.value for e in x]), nullable=True)
    sent_date = Column(DateTime(timezone=True), nullable=True)
    activated_date = Column(DateTime(timezone=True), nullable=True)

    # Third Party Route Data (Saudi Quote Sheet)
    third_party_company_id = Column(String, nullable=True)
    third_party_email_sent_date = Column(DateTime(timezone=True), nullable=True)
    third_party_response_received_date = Column(DateTime(timezone=True), nullable=True)
    third_party_document = Column(String, nullable=True)

    # Quote Sheet Data (Saudi Route)
    quote_sheet_data = Column(JSON, nullable=True)
    quote_sheet_status = Column(String, nullable=True)

    # UAE 3rd Party Contract Upload
    third_party_contract_url = Column(String, nullable=True)
    third_party_contract_uploaded_date = Column(DateTime(timezone=True), nullable=True)

    # Document Upload Workflow
    documents_uploaded_date = Column(DateTime(timezone=True), nullable=True)

    # Uploaded Documents (Phase 8 deferred)
    passport_document = Column(String, nullable=True)
    photo_document = Column(String, nullable=True)
    visa_page_document = Column(String, nullable=True)
    id_front_document = Column(String, nullable=True)
    id_back_document = Column(String, nullable=True)
    emirates_id_document = Column(String, nullable=True)
    degree_document = Column(String, nullable=True)

    # Client Contract Upload Workflow
    client_uploaded_contract = Column(String, nullable=True)
    contract_uploaded_date = Column(DateTime(timezone=True), nullable=True)
    contract_approved_date = Column(DateTime(timezone=True), nullable=True)
    contract_approved_by = Column(String, nullable=True)

    # Signed Contract
    signed_contract_url = Column(String, nullable=True)

    # Review & Approval Tracking
    reviewed_date = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)

    # Consultant Tracking
    consultant_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Costing Sheet Data (filled by consultant)
    costing_sheet_data = Column(JSON, nullable=True)

    # Personal Details
    first_name = Column(String, nullable=False)
    middle_names = Column(String, nullable=True)
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    country = Column(String, nullable=True)
    country_of_residence = Column(String, nullable=True)
    current_location = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    number_of_children = Column(String, nullable=True)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    address_line3 = Column(String, nullable=True)
    address_line4 = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    mobile_no = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    dob = Column(String, nullable=False)

    # Management Company (structural FKs stay)
    business_type = Column(String, nullable=True)
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)

    # Placement Details
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    project_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    currency = Column(String, nullable=False, default="AED")

    # CDS Form Data (Step 2)
    cds_form_data = Column(JSON, nullable=True)

    # Generated Contract
    generated_contract = Column(Text, nullable=True)

    # Offboarding fields
    offboarding_status = Column(String, nullable=True)
    offboarded_date = Column(DateTime(timezone=True), nullable=True)
    offboarding_reason = Column(String, nullable=True)
    is_offboarded = Column(String, nullable=True, default="false")

    # Extension tracking
    current_extension_id = Column(String, nullable=True)
    total_extensions = Column(String, nullable=True, default="0")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==========================================
    # CHILD TABLE RELATIONSHIPS (1:1, eager-loaded)
    # ==========================================
    mgmt_company = relationship("ContractorMgmtCompany", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    banking = relationship("ContractorBanking", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    invoicing = relationship("ContractorInvoicing", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    deal_terms = relationship("ContractorDealTerms", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    tokens = relationship("ContractorTokens", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    signatures = relationship("ContractorSignatures", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")
    cohf_record = relationship("ContractorCohf", uselist=False, back_populates="contractor", cascade="all, delete-orphan", lazy="joined")

    # FK-referenced relationships (for name resolution)
    client = relationship("Client", foreign_keys=[client_id], lazy="select")
    consultant_user = relationship("User", foreign_keys=[consultant_id], lazy="select")
    third_party = relationship("ThirdParty", foreign_keys=[third_party_id], lazy="select")

    # Existing relationships (cascade delete)
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

    # ==========================================
    # ENSURE HELPERS — create child row on first write
    # ==========================================
    def _ensure_mgmt_company(self):
        if self.mgmt_company is None:
            self.mgmt_company = ContractorMgmtCompany()
        return self.mgmt_company

    def _ensure_banking(self):
        if self.banking is None:
            self.banking = ContractorBanking()
        return self.banking

    def _ensure_invoicing(self):
        if self.invoicing is None:
            self.invoicing = ContractorInvoicing()
        return self.invoicing

    def _ensure_deal_terms(self):
        if self.deal_terms is None:
            self.deal_terms = ContractorDealTerms()
        return self.deal_terms

    def _ensure_tokens(self):
        if self.tokens is None:
            self.tokens = ContractorTokens()
        return self.tokens

    def _ensure_signatures(self):
        if self.signatures is None:
            self.signatures = ContractorSignatures()
        return self.signatures

    def _ensure_cohf(self):
        if self.cohf_record is None:
            self.cohf_record = ContractorCohf()
        return self.cohf_record

    # ==========================================
    # PROPERTIES — Phase 1: Management Company (14 cols)
    # ==========================================
    @property
    def umbrella_company_name(self):
        return self.mgmt_company.umbrella_company_name if self.mgmt_company else None

    @umbrella_company_name.setter
    def umbrella_company_name(self, value):
        self._ensure_mgmt_company().umbrella_company_name = value

    @property
    def company_vat_no(self):
        return self.mgmt_company.company_vat_no if self.mgmt_company else None

    @company_vat_no.setter
    def company_vat_no(self, value):
        self._ensure_mgmt_company().company_vat_no = value

    @property
    def company_name(self):
        return self.mgmt_company.company_name if self.mgmt_company else None

    @company_name.setter
    def company_name(self, value):
        self._ensure_mgmt_company().company_name = value

    @property
    def company_reg_no(self):
        return self.mgmt_company.company_reg_no if self.mgmt_company else None

    @company_reg_no.setter
    def company_reg_no(self, value):
        self._ensure_mgmt_company().company_reg_no = value

    @property
    def mgmt_address_line1(self):
        return self.mgmt_company.mgmt_address_line1 if self.mgmt_company else None

    @mgmt_address_line1.setter
    def mgmt_address_line1(self, value):
        self._ensure_mgmt_company().mgmt_address_line1 = value

    @property
    def mgmt_address_line2(self):
        return self.mgmt_company.mgmt_address_line2 if self.mgmt_company else None

    @mgmt_address_line2.setter
    def mgmt_address_line2(self, value):
        self._ensure_mgmt_company().mgmt_address_line2 = value

    @property
    def mgmt_address_line3(self):
        return self.mgmt_company.mgmt_address_line3 if self.mgmt_company else None

    @mgmt_address_line3.setter
    def mgmt_address_line3(self, value):
        self._ensure_mgmt_company().mgmt_address_line3 = value

    @property
    def mgmt_address_line4(self):
        return self.mgmt_company.mgmt_address_line4 if self.mgmt_company else None

    @mgmt_address_line4.setter
    def mgmt_address_line4(self, value):
        self._ensure_mgmt_company().mgmt_address_line4 = value

    @property
    def mgmt_country(self):
        return self.mgmt_company.mgmt_country if self.mgmt_company else None

    @mgmt_country.setter
    def mgmt_country(self, value):
        self._ensure_mgmt_company().mgmt_country = value

    @property
    def mgmt_bank_name(self):
        return self.mgmt_company.mgmt_bank_name if self.mgmt_company else None

    @mgmt_bank_name.setter
    def mgmt_bank_name(self, value):
        self._ensure_mgmt_company().mgmt_bank_name = value

    @property
    def mgmt_account_name(self):
        return self.mgmt_company.mgmt_account_name if self.mgmt_company else None

    @mgmt_account_name.setter
    def mgmt_account_name(self, value):
        self._ensure_mgmt_company().mgmt_account_name = value

    @property
    def mgmt_account_number(self):
        return self.mgmt_company.mgmt_account_number if self.mgmt_company else None

    @mgmt_account_number.setter
    def mgmt_account_number(self, value):
        self._ensure_mgmt_company().mgmt_account_number = value

    @property
    def mgmt_iban_number(self):
        return self.mgmt_company.mgmt_iban_number if self.mgmt_company else None

    @mgmt_iban_number.setter
    def mgmt_iban_number(self, value):
        self._ensure_mgmt_company().mgmt_iban_number = value

    @property
    def mgmt_swift_bic(self):
        return self.mgmt_company.mgmt_swift_bic if self.mgmt_company else None

    @mgmt_swift_bic.setter
    def mgmt_swift_bic(self, value):
        self._ensure_mgmt_company().mgmt_swift_bic = value

    # ==========================================
    # PROPERTIES — Phase 2: Banking (9 cols)
    # ==========================================
    @property
    def contractor_bank_name(self):
        return self.banking.contractor_bank_name if self.banking else None

    @contractor_bank_name.setter
    def contractor_bank_name(self, value):
        self._ensure_banking().contractor_bank_name = value

    @property
    def contractor_account_name(self):
        return self.banking.contractor_account_name if self.banking else None

    @contractor_account_name.setter
    def contractor_account_name(self, value):
        self._ensure_banking().contractor_account_name = value

    @property
    def contractor_account_no(self):
        return self.banking.contractor_account_no if self.banking else None

    @contractor_account_no.setter
    def contractor_account_no(self, value):
        self._ensure_banking().contractor_account_no = value

    @property
    def contractor_iban(self):
        return self.banking.contractor_iban if self.banking else None

    @contractor_iban.setter
    def contractor_iban(self, value):
        self._ensure_banking().contractor_iban = value

    @property
    def contractor_swift_bic(self):
        return self.banking.contractor_swift_bic if self.banking else None

    @contractor_swift_bic.setter
    def contractor_swift_bic(self, value):
        self._ensure_banking().contractor_swift_bic = value

    @property
    def candidate_bank_name(self):
        return self.banking.candidate_bank_name if self.banking else None

    @candidate_bank_name.setter
    def candidate_bank_name(self, value):
        self._ensure_banking().candidate_bank_name = value

    @property
    def candidate_bank_details(self):
        return self.banking.candidate_bank_details if self.banking else None

    @candidate_bank_details.setter
    def candidate_bank_details(self, value):
        self._ensure_banking().candidate_bank_details = value

    @property
    def candidate_iban(self):
        return self.banking.candidate_iban if self.banking else None

    @candidate_iban.setter
    def candidate_iban(self, value):
        self._ensure_banking().candidate_iban = value

    @property
    def umbrella_or_direct(self):
        return self.banking.umbrella_or_direct if self.banking else None

    @umbrella_or_direct.setter
    def umbrella_or_direct(self, value):
        self._ensure_banking().umbrella_or_direct = value

    # ==========================================
    # PROPERTIES — Phase 3: Invoicing (22 cols)
    # ==========================================
    @property
    def timesheet_required(self):
        return self.invoicing.timesheet_required if self.invoicing else None

    @timesheet_required.setter
    def timesheet_required(self, value):
        self._ensure_invoicing().timesheet_required = value

    @property
    def timesheet_approver_name(self):
        return self.invoicing.timesheet_approver_name if self.invoicing else None

    @timesheet_approver_name.setter
    def timesheet_approver_name(self, value):
        self._ensure_invoicing().timesheet_approver_name = value

    @property
    def invoice_email1(self):
        return self.invoicing.invoice_email1 if self.invoicing else None

    @invoice_email1.setter
    def invoice_email1(self, value):
        self._ensure_invoicing().invoice_email1 = value

    @property
    def invoice_email2(self):
        return self.invoicing.invoice_email2 if self.invoicing else None

    @invoice_email2.setter
    def invoice_email2(self, value):
        self._ensure_invoicing().invoice_email2 = value

    @property
    def client_contact1(self):
        return self.invoicing.client_contact1 if self.invoicing else None

    @client_contact1.setter
    def client_contact1(self, value):
        self._ensure_invoicing().client_contact1 = value

    @property
    def client_contact2(self):
        return self.invoicing.client_contact2 if self.invoicing else None

    @client_contact2.setter
    def client_contact2(self, value):
        self._ensure_invoicing().client_contact2 = value

    @property
    def invoice_address_line1(self):
        return self.invoicing.invoice_address_line1 if self.invoicing else None

    @invoice_address_line1.setter
    def invoice_address_line1(self, value):
        self._ensure_invoicing().invoice_address_line1 = value

    @property
    def invoice_address_line2(self):
        return self.invoicing.invoice_address_line2 if self.invoicing else None

    @invoice_address_line2.setter
    def invoice_address_line2(self, value):
        self._ensure_invoicing().invoice_address_line2 = value

    @property
    def invoice_address_line3(self):
        return self.invoicing.invoice_address_line3 if self.invoicing else None

    @invoice_address_line3.setter
    def invoice_address_line3(self, value):
        self._ensure_invoicing().invoice_address_line3 = value

    @property
    def invoice_address_line4(self):
        return self.invoicing.invoice_address_line4 if self.invoicing else None

    @invoice_address_line4.setter
    def invoice_address_line4(self, value):
        self._ensure_invoicing().invoice_address_line4 = value

    @property
    def invoice_po_box(self):
        return self.invoicing.invoice_po_box if self.invoicing else None

    @invoice_po_box.setter
    def invoice_po_box(self, value):
        self._ensure_invoicing().invoice_po_box = value

    @property
    def invoice_country(self):
        return self.invoicing.invoice_country if self.invoicing else None

    @invoice_country.setter
    def invoice_country(self, value):
        self._ensure_invoicing().invoice_country = value

    @property
    def invoice_tax_number(self):
        return self.invoicing.invoice_tax_number if self.invoicing else None

    @invoice_tax_number.setter
    def invoice_tax_number(self, value):
        self._ensure_invoicing().invoice_tax_number = value

    @property
    def tax_number(self):
        return self.invoicing.tax_number if self.invoicing else None

    @tax_number.setter
    def tax_number(self, value):
        self._ensure_invoicing().tax_number = value

    @property
    def contractor_pay_frequency(self):
        return self.invoicing.contractor_pay_frequency if self.invoicing else None

    @contractor_pay_frequency.setter
    def contractor_pay_frequency(self, value):
        self._ensure_invoicing().contractor_pay_frequency = value

    @property
    def client_invoice_frequency(self):
        return self.invoicing.client_invoice_frequency if self.invoicing else None

    @client_invoice_frequency.setter
    def client_invoice_frequency(self, value):
        self._ensure_invoicing().client_invoice_frequency = value

    @property
    def client_payment_terms(self):
        return self.invoicing.client_payment_terms if self.invoicing else None

    @client_payment_terms.setter
    def client_payment_terms(self, value):
        self._ensure_invoicing().client_payment_terms = value

    @property
    def invoicing_preferences(self):
        return self.invoicing.invoicing_preferences if self.invoicing else None

    @invoicing_preferences.setter
    def invoicing_preferences(self, value):
        self._ensure_invoicing().invoicing_preferences = value

    @property
    def invoice_instructions(self):
        return self.invoicing.invoice_instructions if self.invoicing else None

    @invoice_instructions.setter
    def invoice_instructions(self, value):
        self._ensure_invoicing().invoice_instructions = value

    @property
    def supporting_docs_required(self):
        return self.invoicing.supporting_docs_required if self.invoicing else None

    @supporting_docs_required.setter
    def supporting_docs_required(self, value):
        self._ensure_invoicing().supporting_docs_required = value

    @property
    def po_required(self):
        return self.invoicing.po_required if self.invoicing else None

    @po_required.setter
    def po_required(self, value):
        self._ensure_invoicing().po_required = value

    @property
    def po_number(self):
        return self.invoicing.po_number if self.invoicing else None

    @po_number.setter
    def po_number(self, value):
        self._ensure_invoicing().po_number = value

    # ==========================================
    # PROPERTIES — Phase 4: Deal Terms (35 cols)
    # ==========================================
    @property
    def rate_type(self):
        return self.deal_terms.rate_type if self.deal_terms else None

    @rate_type.setter
    def rate_type(self, value):
        self._ensure_deal_terms().rate_type = value

    @property
    def charge_rate_month(self):
        return self.deal_terms.charge_rate_month if self.deal_terms else None

    @charge_rate_month.setter
    def charge_rate_month(self, value):
        self._ensure_deal_terms().charge_rate_month = value

    @property
    def gross_salary(self):
        return self.deal_terms.gross_salary if self.deal_terms else None

    @gross_salary.setter
    def gross_salary(self, value):
        self._ensure_deal_terms().gross_salary = value

    @property
    def charge_rate_day(self):
        return self.deal_terms.charge_rate_day if self.deal_terms else None

    @charge_rate_day.setter
    def charge_rate_day(self, value):
        self._ensure_deal_terms().charge_rate_day = value

    @property
    def day_rate(self):
        return self.deal_terms.day_rate if self.deal_terms else None

    @day_rate.setter
    def day_rate(self, value):
        self._ensure_deal_terms().day_rate = value

    @property
    def candidate_pay_rate_period(self):
        return self.deal_terms.candidate_pay_rate_period if self.deal_terms else None

    @candidate_pay_rate_period.setter
    def candidate_pay_rate_period(self, value):
        self._ensure_deal_terms().candidate_pay_rate_period = value

    @property
    def management_company_charges(self):
        return self.deal_terms.management_company_charges if self.deal_terms else None

    @management_company_charges.setter
    def management_company_charges(self, value):
        self._ensure_deal_terms().management_company_charges = value

    @property
    def taxes(self):
        return self.deal_terms.taxes if self.deal_terms else None

    @taxes.setter
    def taxes(self, value):
        self._ensure_deal_terms().taxes = value

    @property
    def bank_fees(self):
        return self.deal_terms.bank_fees if self.deal_terms else None

    @bank_fees.setter
    def bank_fees(self, value):
        self._ensure_deal_terms().bank_fees = value

    @property
    def fx(self):
        return self.deal_terms.fx if self.deal_terms else None

    @fx.setter
    def fx(self, value):
        self._ensure_deal_terms().fx = value

    @property
    def nationalisation(self):
        return self.deal_terms.nationalisation if self.deal_terms else None

    @nationalisation.setter
    def nationalisation(self, value):
        self._ensure_deal_terms().nationalisation = value

    @property
    def leave_allowance(self):
        return self.deal_terms.leave_allowance if self.deal_terms else None

    @leave_allowance.setter
    def leave_allowance(self, value):
        self._ensure_deal_terms().leave_allowance = value

    @property
    def eosb(self):
        return self.deal_terms.eosb if self.deal_terms else None

    @eosb.setter
    def eosb(self, value):
        self._ensure_deal_terms().eosb = value

    @property
    def vacation_days(self):
        return self.deal_terms.vacation_days if self.deal_terms else None

    @vacation_days.setter
    def vacation_days(self, value):
        self._ensure_deal_terms().vacation_days = value

    @property
    def vacation_pay(self):
        return self.deal_terms.vacation_pay if self.deal_terms else None

    @vacation_pay.setter
    def vacation_pay(self, value):
        self._ensure_deal_terms().vacation_pay = value

    @property
    def sick_leave(self):
        return self.deal_terms.sick_leave if self.deal_terms else None

    @sick_leave.setter
    def sick_leave(self, value):
        self._ensure_deal_terms().sick_leave = value

    @property
    def other_provision(self):
        return self.deal_terms.other_provision if self.deal_terms else None

    @other_provision.setter
    def other_provision(self, value):
        self._ensure_deal_terms().other_provision = value

    @property
    def flights(self):
        return self.deal_terms.flights if self.deal_terms else None

    @flights.setter
    def flights(self, value):
        self._ensure_deal_terms().flights = value

    @property
    def visa(self):
        return self.deal_terms.visa if self.deal_terms else None

    @visa.setter
    def visa(self, value):
        self._ensure_deal_terms().visa = value

    @property
    def medical_insurance(self):
        return self.deal_terms.medical_insurance if self.deal_terms else None

    @medical_insurance.setter
    def medical_insurance(self, value):
        self._ensure_deal_terms().medical_insurance = value

    @property
    def family_costs(self):
        return self.deal_terms.family_costs if self.deal_terms else None

    @family_costs.setter
    def family_costs(self, value):
        self._ensure_deal_terms().family_costs = value

    @property
    def other_one_time_costs(self):
        return self.deal_terms.other_one_time_costs if self.deal_terms else None

    @other_one_time_costs.setter
    def other_one_time_costs(self, value):
        self._ensure_deal_terms().other_one_time_costs = value

    @property
    def laptop_provided_by(self):
        return self.deal_terms.laptop_provided_by if self.deal_terms else None

    @laptop_provided_by.setter
    def laptop_provided_by(self, value):
        self._ensure_deal_terms().laptop_provided_by = value

    @property
    def any_notes(self):
        return self.deal_terms.any_notes if self.deal_terms else None

    @any_notes.setter
    def any_notes(self, value):
        self._ensure_deal_terms().any_notes = value

    @property
    def upfront_invoices(self):
        return self.deal_terms.upfront_invoices if self.deal_terms else None

    @upfront_invoices.setter
    def upfront_invoices(self, value):
        self._ensure_deal_terms().upfront_invoices = value

    @property
    def security_deposit(self):
        return self.deal_terms.security_deposit if self.deal_terms else None

    @security_deposit.setter
    def security_deposit(self, value):
        self._ensure_deal_terms().security_deposit = value

    @property
    def total_monthly_costs(self):
        return self.deal_terms.total_monthly_costs if self.deal_terms else None

    @total_monthly_costs.setter
    def total_monthly_costs(self, value):
        self._ensure_deal_terms().total_monthly_costs = value

    @property
    def total_contractor_fixed_costs(self):
        return self.deal_terms.total_contractor_fixed_costs if self.deal_terms else None

    @total_contractor_fixed_costs.setter
    def total_contractor_fixed_costs(self, value):
        self._ensure_deal_terms().total_contractor_fixed_costs = value

    @property
    def monthly_contractor_fixed_costs(self):
        return self.deal_terms.monthly_contractor_fixed_costs if self.deal_terms else None

    @monthly_contractor_fixed_costs.setter
    def monthly_contractor_fixed_costs(self, value):
        self._ensure_deal_terms().monthly_contractor_fixed_costs = value

    @property
    def total_contractor_monthly_cost(self):
        return self.deal_terms.total_contractor_monthly_cost if self.deal_terms else None

    @total_contractor_monthly_cost.setter
    def total_contractor_monthly_cost(self, value):
        self._ensure_deal_terms().total_contractor_monthly_cost = value

    @property
    def estimated_monthly_gp(self):
        return self.deal_terms.estimated_monthly_gp if self.deal_terms else None

    @estimated_monthly_gp.setter
    def estimated_monthly_gp(self, value):
        self._ensure_deal_terms().estimated_monthly_gp = value

    @property
    def consultant(self):
        return self.deal_terms.consultant if self.deal_terms else None

    @consultant.setter
    def consultant(self, value):
        self._ensure_deal_terms().consultant = value

    @property
    def resourcer(self):
        return self.deal_terms.resourcer if self.deal_terms else None

    @resourcer.setter
    def resourcer(self, value):
        self._ensure_deal_terms().resourcer = value

    @property
    def aventus_split(self):
        return self.deal_terms.aventus_split if self.deal_terms else None

    @aventus_split.setter
    def aventus_split(self, value):
        self._ensure_deal_terms().aventus_split = value

    @property
    def resourcer_split(self):
        return self.deal_terms.resourcer_split if self.deal_terms else None

    @resourcer_split.setter
    def resourcer_split(self, value):
        self._ensure_deal_terms().resourcer_split = value

    # ==========================================
    # PROPERTIES — Phase 5: Tokens (12 cols)
    # ==========================================
    @property
    def contract_token(self):
        return self.tokens.contract_token if self.tokens else None

    @contract_token.setter
    def contract_token(self, value):
        self._ensure_tokens().contract_token = value

    @property
    def token_expiry(self):
        return self.tokens.token_expiry if self.tokens else None

    @token_expiry.setter
    def token_expiry(self, value):
        self._ensure_tokens().token_expiry = value

    @property
    def document_upload_token(self):
        return self.tokens.document_upload_token if self.tokens else None

    @document_upload_token.setter
    def document_upload_token(self, value):
        self._ensure_tokens().document_upload_token = value

    @property
    def document_token_expiry(self):
        return self.tokens.document_token_expiry if self.tokens else None

    @document_token_expiry.setter
    def document_token_expiry(self, value):
        self._ensure_tokens().document_token_expiry = value

    @property
    def contract_upload_token(self):
        return self.tokens.contract_upload_token if self.tokens else None

    @contract_upload_token.setter
    def contract_upload_token(self, value):
        self._ensure_tokens().contract_upload_token = value

    @property
    def contract_upload_token_expiry(self):
        return self.tokens.contract_upload_token_expiry if self.tokens else None

    @contract_upload_token_expiry.setter
    def contract_upload_token_expiry(self, value):
        self._ensure_tokens().contract_upload_token_expiry = value

    @property
    def quote_sheet_token(self):
        return self.tokens.quote_sheet_token if self.tokens else None

    @quote_sheet_token.setter
    def quote_sheet_token(self, value):
        self._ensure_tokens().quote_sheet_token = value

    @property
    def quote_sheet_token_expiry(self):
        return self.tokens.quote_sheet_token_expiry if self.tokens else None

    @quote_sheet_token_expiry.setter
    def quote_sheet_token_expiry(self, value):
        self._ensure_tokens().quote_sheet_token_expiry = value

    @property
    def cohf_token(self):
        return self.tokens.cohf_token if self.tokens else None

    @cohf_token.setter
    def cohf_token(self, value):
        self._ensure_tokens().cohf_token = value

    @property
    def cohf_token_expiry(self):
        return self.tokens.cohf_token_expiry if self.tokens else None

    @cohf_token_expiry.setter
    def cohf_token_expiry(self, value):
        self._ensure_tokens().cohf_token_expiry = value

    @property
    def third_party_contract_upload_token(self):
        return self.tokens.third_party_contract_upload_token if self.tokens else None

    @third_party_contract_upload_token.setter
    def third_party_contract_upload_token(self, value):
        self._ensure_tokens().third_party_contract_upload_token = value

    @property
    def third_party_contract_token_expiry(self):
        return self.tokens.third_party_contract_token_expiry if self.tokens else None

    @third_party_contract_token_expiry.setter
    def third_party_contract_token_expiry(self, value):
        self._ensure_tokens().third_party_contract_token_expiry = value

    # ==========================================
    # PROPERTIES — Phase 6: Signatures (18 cols)
    # ==========================================
    @property
    def signature_type(self):
        return self.signatures.signature_type if self.signatures else None

    @signature_type.setter
    def signature_type(self, value):
        self._ensure_signatures().signature_type = value

    @property
    def signature_data(self):
        return self.signatures.signature_data if self.signatures else None

    @signature_data.setter
    def signature_data(self, value):
        self._ensure_signatures().signature_data = value

    @property
    def signed_date(self):
        return self.signatures.signed_date if self.signatures else None

    @signed_date.setter
    def signed_date(self, value):
        self._ensure_signatures().signed_date = value

    @property
    def superadmin_signature_type(self):
        return self.signatures.superadmin_signature_type if self.signatures else None

    @superadmin_signature_type.setter
    def superadmin_signature_type(self, value):
        self._ensure_signatures().superadmin_signature_type = value

    @property
    def superadmin_signature_data(self):
        return self.signatures.superadmin_signature_data if self.signatures else None

    @superadmin_signature_data.setter
    def superadmin_signature_data(self, value):
        self._ensure_signatures().superadmin_signature_data = value

    @property
    def cohf_third_party_signature(self):
        return self.signatures.cohf_third_party_signature if self.signatures else None

    @cohf_third_party_signature.setter
    def cohf_third_party_signature(self, value):
        self._ensure_signatures().cohf_third_party_signature = value

    @property
    def cohf_third_party_name(self):
        return self.signatures.cohf_third_party_name if self.signatures else None

    @cohf_third_party_name.setter
    def cohf_third_party_name(self, value):
        self._ensure_signatures().cohf_third_party_name = value

    @property
    def cohf_aventus_signature_type(self):
        return self.signatures.cohf_aventus_signature_type if self.signatures else None

    @cohf_aventus_signature_type.setter
    def cohf_aventus_signature_type(self, value):
        self._ensure_signatures().cohf_aventus_signature_type = value

    @property
    def cohf_aventus_signature_data(self):
        return self.signatures.cohf_aventus_signature_data if self.signatures else None

    @cohf_aventus_signature_data.setter
    def cohf_aventus_signature_data(self, value):
        self._ensure_signatures().cohf_aventus_signature_data = value

    @property
    def cohf_aventus_signed_date(self):
        return self.signatures.cohf_aventus_signed_date if self.signatures else None

    @cohf_aventus_signed_date.setter
    def cohf_aventus_signed_date(self, value):
        self._ensure_signatures().cohf_aventus_signed_date = value

    @property
    def cohf_aventus_signed_by(self):
        return self.signatures.cohf_aventus_signed_by if self.signatures else None

    @cohf_aventus_signed_by.setter
    def cohf_aventus_signed_by(self, value):
        self._ensure_signatures().cohf_aventus_signed_by = value

    @property
    def quote_sheet_third_party_signature(self):
        return self.signatures.quote_sheet_third_party_signature if self.signatures else None

    @quote_sheet_third_party_signature.setter
    def quote_sheet_third_party_signature(self, value):
        self._ensure_signatures().quote_sheet_third_party_signature = value

    @property
    def quote_sheet_third_party_name(self):
        return self.signatures.quote_sheet_third_party_name if self.signatures else None

    @quote_sheet_third_party_name.setter
    def quote_sheet_third_party_name(self, value):
        self._ensure_signatures().quote_sheet_third_party_name = value

    @property
    def quote_sheet_third_party_signed_date(self):
        return self.signatures.quote_sheet_third_party_signed_date if self.signatures else None

    @quote_sheet_third_party_signed_date.setter
    def quote_sheet_third_party_signed_date(self, value):
        self._ensure_signatures().quote_sheet_third_party_signed_date = value

    @property
    def quote_sheet_aventus_signature_type(self):
        return self.signatures.quote_sheet_aventus_signature_type if self.signatures else None

    @quote_sheet_aventus_signature_type.setter
    def quote_sheet_aventus_signature_type(self, value):
        self._ensure_signatures().quote_sheet_aventus_signature_type = value

    @property
    def quote_sheet_aventus_signature_data(self):
        return self.signatures.quote_sheet_aventus_signature_data if self.signatures else None

    @quote_sheet_aventus_signature_data.setter
    def quote_sheet_aventus_signature_data(self, value):
        self._ensure_signatures().quote_sheet_aventus_signature_data = value

    @property
    def quote_sheet_aventus_signed_date(self):
        return self.signatures.quote_sheet_aventus_signed_date if self.signatures else None

    @quote_sheet_aventus_signed_date.setter
    def quote_sheet_aventus_signed_date(self, value):
        self._ensure_signatures().quote_sheet_aventus_signed_date = value

    @property
    def quote_sheet_aventus_signed_by(self):
        return self.signatures.quote_sheet_aventus_signed_by if self.signatures else None

    @quote_sheet_aventus_signed_by.setter
    def quote_sheet_aventus_signed_by(self, value):
        self._ensure_signatures().quote_sheet_aventus_signed_by = value

    # ==========================================
    # PROPERTIES — Phase 7: COHF (7 cols)
    # ==========================================
    @property
    def cohf_data(self):
        return self.cohf_record.cohf_data if self.cohf_record else None

    @cohf_data.setter
    def cohf_data(self, value):
        self._ensure_cohf().cohf_data = value

    @property
    def cohf_status(self):
        return self.cohf_record.cohf_status if self.cohf_record else None

    @cohf_status.setter
    def cohf_status(self, value):
        self._ensure_cohf().cohf_status = value

    @property
    def cohf_submitted_date(self):
        return self.cohf_record.cohf_submitted_date if self.cohf_record else None

    @cohf_submitted_date.setter
    def cohf_submitted_date(self, value):
        self._ensure_cohf().cohf_submitted_date = value

    @property
    def cohf_sent_to_3rd_party_date(self):
        return self.cohf_record.cohf_sent_to_3rd_party_date if self.cohf_record else None

    @cohf_sent_to_3rd_party_date.setter
    def cohf_sent_to_3rd_party_date(self, value):
        self._ensure_cohf().cohf_sent_to_3rd_party_date = value

    @property
    def cohf_docusign_received_date(self):
        return self.cohf_record.cohf_docusign_received_date if self.cohf_record else None

    @cohf_docusign_received_date.setter
    def cohf_docusign_received_date(self, value):
        self._ensure_cohf().cohf_docusign_received_date = value

    @property
    def cohf_completed_date(self):
        return self.cohf_record.cohf_completed_date if self.cohf_record else None

    @cohf_completed_date.setter
    def cohf_completed_date(self, value):
        self._ensure_cohf().cohf_completed_date = value

    @property
    def cohf_signed_document(self):
        return self.cohf_record.cohf_signed_document if self.cohf_record else None

    @cohf_signed_document.setter
    def cohf_signed_document(self, value):
        self._ensure_cohf().cohf_signed_document = value

    # ==========================================
    # BACKWARD-COMPAT ALIASES
    # ==========================================
    @hybrid_property
    def home_address(self):
        return self.address_line1

    @home_address.setter
    def home_address(self, value):
        self.address_line1 = value

    @property
    def registered_address(self):
        return self.mgmt_address_line1

    @registered_address.setter
    def registered_address(self, value):
        self.mgmt_address_line1 = value

    @property
    def management_address_line2(self):
        return self.mgmt_address_line2

    @management_address_line2.setter
    def management_address_line2(self, value):
        self.mgmt_address_line2 = value

    @property
    def management_address_line3(self):
        return self.mgmt_address_line3

    @management_address_line3.setter
    def management_address_line3(self, value):
        self.mgmt_address_line3 = value

    @property
    def bank_name(self):
        return self.mgmt_bank_name

    @bank_name.setter
    def bank_name(self, value):
        self.mgmt_bank_name = value

    @property
    def account_number(self):
        return self.mgmt_account_number

    @account_number.setter
    def account_number(self, value):
        self.mgmt_account_number = value

    @property
    def iban_number(self):
        return self.mgmt_iban_number

    @iban_number.setter
    def iban_number(self, value):
        self.mgmt_iban_number = value

    @property
    def invoice_email(self):
        return self.invoice_email1

    @invoice_email.setter
    def invoice_email(self, value):
        self.invoice_email1 = value

    @property
    def client_contact(self):
        return self.client_contact1

    @client_contact.setter
    def client_contact(self, value):
        self.client_contact1 = value

    @property
    def client_charge_rate(self):
        return self.charge_rate_month

    @client_charge_rate.setter
    def client_charge_rate(self, value):
        self.charge_rate_month = value

    @property
    def candidate_pay_rate(self):
        return self.gross_salary

    @candidate_pay_rate.setter
    def candidate_pay_rate(self, value):
        self.gross_salary = value

    @property
    def candidate_basic_salary(self):
        return self.gross_salary

    @candidate_basic_salary.setter
    def candidate_basic_salary(self, value):
        self.gross_salary = value

    @property
    def contractor_costs(self):
        return None  # Derivable, no canonical column

    @property
    def contractor_total_fixed_costs(self):
        return self.total_contractor_fixed_costs

    @contractor_total_fixed_costs.setter
    def contractor_total_fixed_costs(self, value):
        self.total_contractor_fixed_costs = value

    @property
    def laptop_provider(self):
        return self.laptop_provided_by

    @laptop_provider.setter
    def laptop_provider(self, value):
        self.laptop_provided_by = value

    @property
    def other_notes(self):
        return self.any_notes

    @other_notes.setter
    def other_notes(self, value):
        self.any_notes = value

    # Token expiry aliases (code uses these names but canonical names differ)
    @property
    def contract_token_expiry(self):
        return self.token_expiry

    @contract_token_expiry.setter
    def contract_token_expiry(self, value):
        self.token_expiry = value

    @property
    def document_upload_token_expiry(self):
        return self.document_token_expiry

    @document_upload_token_expiry.setter
    def document_upload_token_expiry(self, value):
        self.document_token_expiry = value

    # ==========================================
    # FK-RESOLVED PROPERTIES
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


# ==========================================
# CHILD TABLES (1:1 decomposition from contractors)
# ==========================================

class ContractorMgmtCompany(Base):
    """Management company details for a contractor."""
    __tablename__ = "contractor_mgmt_company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    umbrella_company_name = Column(String, nullable=True)
    company_vat_no = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    company_reg_no = Column(String, nullable=True)
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

    contractor = relationship("Contractor", back_populates="mgmt_company")


class ContractorBanking(Base):
    """Banking details for a contractor."""
    __tablename__ = "contractor_banking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    contractor_bank_name = Column(String, nullable=True)
    contractor_account_name = Column(String, nullable=True)
    contractor_account_no = Column(String, nullable=True)
    contractor_iban = Column(String, nullable=True)
    contractor_swift_bic = Column(String, nullable=True)
    candidate_bank_name = Column(String, nullable=True)
    candidate_bank_details = Column(String, nullable=True)
    candidate_iban = Column(String, nullable=True)
    umbrella_or_direct = Column(String, nullable=True)

    contractor = relationship("Contractor", back_populates="banking")


class ContractorInvoicing(Base):
    """Invoicing details for a contractor."""
    __tablename__ = "contractor_invoicing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    timesheet_required = Column(String, nullable=True)
    timesheet_approver_name = Column(String, nullable=True)
    invoice_email1 = Column(String, nullable=True)
    invoice_email2 = Column(String, nullable=True)
    client_contact1 = Column(String, nullable=True)
    client_contact2 = Column(String, nullable=True)
    invoice_address_line1 = Column(String, nullable=True)
    invoice_address_line2 = Column(String, nullable=True)
    invoice_address_line3 = Column(String, nullable=True)
    invoice_address_line4 = Column(String, nullable=True)
    invoice_po_box = Column(String, nullable=True)
    invoice_country = Column(String, nullable=True)
    invoice_tax_number = Column(String, nullable=True)
    tax_number = Column(String, nullable=True)
    contractor_pay_frequency = Column(String, nullable=True)
    client_invoice_frequency = Column(String, nullable=True)
    client_payment_terms = Column(String, nullable=True)
    invoicing_preferences = Column(String, nullable=True)
    invoice_instructions = Column(Text, nullable=True)
    supporting_docs_required = Column(String, nullable=True)
    po_required = Column(String, nullable=True)
    po_number = Column(String, nullable=True)

    contractor = relationship("Contractor", back_populates="invoicing")


class ContractorDealTerms(Base):
    """Deal terms and costing for a contractor."""
    __tablename__ = "contractor_deal_terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    rate_type = Column(String, nullable=True, default="monthly")
    charge_rate_month = Column(String, nullable=True)
    gross_salary = Column(String, nullable=True)
    charge_rate_day = Column(String, nullable=True)
    day_rate = Column(String, nullable=True)
    candidate_pay_rate_period = Column(String, nullable=True)
    management_company_charges = Column(String, nullable=True)
    taxes = Column(String, nullable=True)
    bank_fees = Column(String, nullable=True)
    fx = Column(String, nullable=True)
    nationalisation = Column(String, nullable=True)
    leave_allowance = Column(String, nullable=True)
    eosb = Column(String, nullable=True)
    vacation_days = Column(String, nullable=True)
    vacation_pay = Column(String, nullable=True)
    sick_leave = Column(String, nullable=True)
    other_provision = Column(String, nullable=True)
    flights = Column(String, nullable=True)
    visa = Column(String, nullable=True)
    medical_insurance = Column(String, nullable=True)
    family_costs = Column(String, nullable=True)
    other_one_time_costs = Column(String, nullable=True)
    laptop_provided_by = Column(String, nullable=True)
    any_notes = Column(Text, nullable=True)
    upfront_invoices = Column(String, nullable=True)
    security_deposit = Column(String, nullable=True)
    total_monthly_costs = Column(String, nullable=True)
    total_contractor_fixed_costs = Column(String, nullable=True)
    monthly_contractor_fixed_costs = Column(String, nullable=True)
    total_contractor_monthly_cost = Column(String, nullable=True)
    estimated_monthly_gp = Column(String, nullable=True)
    consultant = Column(String, nullable=True)
    resourcer = Column(String, nullable=True)
    aventus_split = Column(String, nullable=True)
    resourcer_split = Column(String, nullable=True)

    contractor = relationship("Contractor", back_populates="deal_terms")


class ContractorTokens(Base):
    """Access tokens for a contractor."""
    __tablename__ = "contractor_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    contract_token = Column(String, unique=True, nullable=True, index=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    document_upload_token = Column(String, unique=True, nullable=True, index=True)
    document_token_expiry = Column(DateTime(timezone=True), nullable=True)
    contract_upload_token = Column(String, unique=True, nullable=True, index=True)
    contract_upload_token_expiry = Column(DateTime(timezone=True), nullable=True)
    quote_sheet_token = Column(String, unique=True, nullable=True, index=True)
    quote_sheet_token_expiry = Column(DateTime(timezone=True), nullable=True)
    cohf_token = Column(String, unique=True, nullable=True, index=True)
    cohf_token_expiry = Column(DateTime(timezone=True), nullable=True)
    third_party_contract_upload_token = Column(String, unique=True, nullable=True, index=True)
    third_party_contract_token_expiry = Column(DateTime(timezone=True), nullable=True)

    contractor = relationship("Contractor", back_populates="tokens")


class ContractorSignatures(Base):
    """Signature data for a contractor."""
    __tablename__ = "contractor_signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    signature_type = Column(String, nullable=True)
    signature_data = Column(Text, nullable=True)
    signed_date = Column(DateTime(timezone=True), nullable=True)
    superadmin_signature_type = Column(String, nullable=True)
    superadmin_signature_data = Column(Text, nullable=True)
    cohf_third_party_signature = Column(Text, nullable=True)
    cohf_third_party_name = Column(String, nullable=True)
    cohf_aventus_signature_type = Column(String, nullable=True)
    cohf_aventus_signature_data = Column(Text, nullable=True)
    cohf_aventus_signed_date = Column(DateTime(timezone=True), nullable=True)
    cohf_aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)
    quote_sheet_third_party_signature = Column(Text, nullable=True)
    quote_sheet_third_party_name = Column(String, nullable=True)
    quote_sheet_third_party_signed_date = Column(DateTime(timezone=True), nullable=True)
    quote_sheet_aventus_signature_type = Column(String, nullable=True)
    quote_sheet_aventus_signature_data = Column(Text, nullable=True)
    quote_sheet_aventus_signed_date = Column(DateTime(timezone=True), nullable=True)
    quote_sheet_aventus_signed_by = Column(String, ForeignKey("users.id"), nullable=True)

    contractor = relationship("Contractor", back_populates="signatures")


class ContractorCohf(Base):
    """COHF (Cost of Hire Form) data for a contractor."""
    __tablename__ = "contractor_cohf"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    cohf_data = Column(JSON, nullable=True)
    cohf_status = Column(String, nullable=True)
    cohf_submitted_date = Column(DateTime(timezone=True), nullable=True)
    cohf_sent_to_3rd_party_date = Column(DateTime(timezone=True), nullable=True)
    cohf_docusign_received_date = Column(DateTime(timezone=True), nullable=True)
    cohf_completed_date = Column(DateTime(timezone=True), nullable=True)
    cohf_signed_document = Column(String, nullable=True)

    contractor = relationship("Contractor", back_populates="cohf_record")


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
