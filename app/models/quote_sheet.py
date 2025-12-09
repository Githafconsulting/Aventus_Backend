from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum


class QuoteSheetStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"  # For legacy file upload flow
    SUBMITTED = "submitted"  # For new form submission flow
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class QuoteSheet(Base):
    __tablename__ = "quote_sheets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Relationships
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)
    consultant_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Upload token for secure access
    upload_token = Column(String, unique=True, nullable=False, index=True)
    token_expiry = Column(DateTime, nullable=False)

    # Basic Quote Sheet Details
    contractor_name = Column(String, nullable=True)
    third_party_company_name = Column(String, nullable=True)
    issued_date = Column(String, nullable=True)

    # ===== (A) Employee Contract Information =====
    employee_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    date_of_hiring = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    family_status = Column(String, nullable=True)  # Single or Family
    num_children = Column(String, nullable=True)

    # ===== (B) Employee Cash Benefits (SAR) =====
    basic_salary = Column(Float, nullable=True)
    transport_allowance = Column(Float, nullable=True)
    housing_allowance = Column(Float, nullable=True)
    rate_per_day = Column(Float, nullable=True)
    working_days_month = Column(Float, nullable=True)
    aed_to_sar = Column(Float, nullable=True)
    gross_salary = Column(Float, nullable=True)

    # ===== (C) Employee Cost (One Time / Annual / Monthly) =====
    # Vacation
    vacation_one_time = Column(Float, nullable=True)
    vacation_annual = Column(Float, nullable=True)
    vacation_monthly = Column(Float, nullable=True)
    # Flight
    flight_one_time = Column(Float, nullable=True)
    flight_annual = Column(Float, nullable=True)
    flight_monthly = Column(Float, nullable=True)
    # EOSB
    eosb_one_time = Column(Float, nullable=True)
    eosb_annual = Column(Float, nullable=True)
    eosb_monthly = Column(Float, nullable=True)
    # GOSI
    gosi_one_time = Column(Float, nullable=True)
    gosi_annual = Column(Float, nullable=True)
    gosi_monthly = Column(Float, nullable=True)
    # Medical
    medical_one_time = Column(Float, nullable=True)
    medical_annual = Column(Float, nullable=True)
    medical_monthly = Column(Float, nullable=True)
    # Exit Re-Entry
    exit_reentry_one_time = Column(Float, nullable=True)
    exit_reentry_annual = Column(Float, nullable=True)
    exit_reentry_monthly = Column(Float, nullable=True)
    # Salary Transfer
    salary_transfer_one_time = Column(Float, nullable=True)
    salary_transfer_annual = Column(Float, nullable=True)
    salary_transfer_monthly = Column(Float, nullable=True)
    # Sick Leave
    sick_leave_one_time = Column(Float, nullable=True)
    sick_leave_annual = Column(Float, nullable=True)
    sick_leave_monthly = Column(Float, nullable=True)
    # Employee Cost Totals
    employee_cost_one_time_total = Column(Float, nullable=True)
    employee_cost_annual_total = Column(Float, nullable=True)
    employee_cost_monthly_total = Column(Float, nullable=True)

    # ===== (D) Family Cost =====
    family_medical_one_time = Column(Float, nullable=True)
    family_medical_annual = Column(Float, nullable=True)
    family_medical_monthly = Column(Float, nullable=True)
    family_flight_one_time = Column(Float, nullable=True)
    family_flight_annual = Column(Float, nullable=True)
    family_flight_monthly = Column(Float, nullable=True)
    family_exit_one_time = Column(Float, nullable=True)
    family_exit_annual = Column(Float, nullable=True)
    family_exit_monthly = Column(Float, nullable=True)
    family_joining_one_time = Column(Float, nullable=True)
    family_joining_annual = Column(Float, nullable=True)
    family_joining_monthly = Column(Float, nullable=True)
    family_visa_one_time = Column(Float, nullable=True)
    family_visa_annual = Column(Float, nullable=True)
    family_visa_monthly = Column(Float, nullable=True)
    family_levy_one_time = Column(Float, nullable=True)
    family_levy_annual = Column(Float, nullable=True)
    family_levy_monthly = Column(Float, nullable=True)
    # Family Cost Totals
    family_cost_one_time_total = Column(Float, nullable=True)
    family_cost_annual_total = Column(Float, nullable=True)
    family_cost_monthly_total = Column(Float, nullable=True)

    # ===== (E) Government Related Charges =====
    sce_one_time = Column(Float, nullable=True)
    sce_annual = Column(Float, nullable=True)
    sce_monthly = Column(Float, nullable=True)
    medical_test_one_time = Column(Float, nullable=True)
    medical_test_annual = Column(Float, nullable=True)
    medical_test_monthly = Column(Float, nullable=True)
    visa_cost_one_time = Column(Float, nullable=True)
    visa_cost_annual = Column(Float, nullable=True)
    visa_cost_monthly = Column(Float, nullable=True)
    ewakala_one_time = Column(Float, nullable=True)
    ewakala_annual = Column(Float, nullable=True)
    ewakala_monthly = Column(Float, nullable=True)
    chamber_mofa_one_time = Column(Float, nullable=True)
    chamber_mofa_annual = Column(Float, nullable=True)
    chamber_mofa_monthly = Column(Float, nullable=True)
    iqama_one_time = Column(Float, nullable=True)
    iqama_annual = Column(Float, nullable=True)
    iqama_monthly = Column(Float, nullable=True)
    saudi_admin_one_time = Column(Float, nullable=True)
    saudi_admin_annual = Column(Float, nullable=True)
    saudi_admin_monthly = Column(Float, nullable=True)
    ajeer_one_time = Column(Float, nullable=True)
    ajeer_annual = Column(Float, nullable=True)
    ajeer_monthly = Column(Float, nullable=True)
    # Government Cost Totals
    govt_cost_one_time_total = Column(Float, nullable=True)
    govt_cost_annual_total = Column(Float, nullable=True)
    govt_cost_monthly_total = Column(Float, nullable=True)

    # ===== (F) Mobilization Cost =====
    visa_processing_one_time = Column(Float, nullable=True)
    visa_processing_annual = Column(Float, nullable=True)
    visa_processing_monthly = Column(Float, nullable=True)
    recruitment_one_time = Column(Float, nullable=True)
    recruitment_annual = Column(Float, nullable=True)
    recruitment_monthly = Column(Float, nullable=True)
    joining_ticket_one_time = Column(Float, nullable=True)
    joining_ticket_annual = Column(Float, nullable=True)
    joining_ticket_monthly = Column(Float, nullable=True)
    relocation_one_time = Column(Float, nullable=True)
    relocation_annual = Column(Float, nullable=True)
    relocation_monthly = Column(Float, nullable=True)
    other_cost_one_time = Column(Float, nullable=True)
    other_cost_annual = Column(Float, nullable=True)
    other_cost_monthly = Column(Float, nullable=True)
    # Mobilization Cost Totals
    mobilization_one_time_total = Column(Float, nullable=True)
    mobilization_annual_total = Column(Float, nullable=True)
    mobilization_monthly_total = Column(Float, nullable=True)

    # ===== Grand Totals =====
    total_one_time = Column(Float, nullable=True)
    total_annual = Column(Float, nullable=True)
    total_monthly = Column(Float, nullable=True)
    fnrco_service_charge = Column(Float, nullable=True)
    total_invoice_amount = Column(Float, nullable=True)

    # Remarks fields for flexibility
    remarks_data = Column(JSON, default=dict)  # Store any remarks/notes for each field

    # Documents
    document_url = Column(String, nullable=True)  # Generated PDF URL
    document_filename = Column(String, nullable=True)
    additional_documents = Column(JSON, default=list)

    # Status
    status = Column(SQLEnum(QuoteSheetStatus), default=QuoteSheetStatus.PENDING, nullable=False)

    # Notes and Details
    notes = Column(Text, nullable=True)
    consultant_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contractor = relationship("Contractor", backref="quote_sheets")
    third_party = relationship("ThirdParty", backref="quote_sheets")
    consultant = relationship("User", backref="quote_sheets")
