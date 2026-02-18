import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, JSON, Enum as SQLEnum, Text, UniqueConstraint
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
    third_party_company_name = Column(String, nullable=True)  # Kept: can be set from email-domain when no third_party_id
    issued_date = Column(String, nullable=True)

    # ===== (A) Employee Contract Information =====
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

    # ===== Section Cost Totals (cached) =====
    employee_cost_one_time_total = Column(Float, nullable=True)
    employee_cost_annual_total = Column(Float, nullable=True)
    employee_cost_monthly_total = Column(Float, nullable=True)
    family_cost_one_time_total = Column(Float, nullable=True)
    family_cost_annual_total = Column(Float, nullable=True)
    family_cost_monthly_total = Column(Float, nullable=True)
    govt_cost_one_time_total = Column(Float, nullable=True)
    govt_cost_annual_total = Column(Float, nullable=True)
    govt_cost_monthly_total = Column(Float, nullable=True)
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
    # Documents

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

    # Properties — resolved from FK relationships (Phase 6)
    @property
    def contractor_name(self):
        try:
            c = self.contractor
            return f"{c.first_name} {c.surname}" if c else None
        except Exception:
            return None

    @contractor_name.setter
    def contractor_name(self, value):
        pass

    @property
    def employee_name(self):
        try:
            c = self.contractor
            return f"{c.first_name} {c.surname}" if c else None
        except Exception:
            return None

    @employee_name.setter
    def employee_name(self, value):
        pass

    # Relationships
    contractor = relationship("Contractor", back_populates="quote_sheets")
    third_party = relationship("ThirdParty", backref="quote_sheets")
    consultant = relationship("User", backref="quote_sheets")
    cost_lines = relationship("QuoteSheetCostLine", back_populates="quote_sheet", cascade="all, delete-orphan")
    quote_sheet_documents = relationship("QuoteSheetDocument", back_populates="quote_sheet", cascade="all, delete-orphan")

    @property
    def additional_documents(self):
        """Backward-compat property: serialize child docs as list of dicts."""
        return [
            {
                "filename": d.filename,
                "url": d.url,
                "type": d.document_type,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in (self.quote_sheet_documents or [])
        ]


class QuoteSheetDocument(Base):
    __tablename__ = "quote_sheet_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_sheet_id = Column(String, ForeignKey("quote_sheets.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=True)
    url = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    quote_sheet = relationship("QuoteSheet", back_populates="quote_sheet_documents")


class QuoteSheetCostLine(Base):
    __tablename__ = "quote_sheet_cost_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_sheet_id = Column(String, ForeignKey("quote_sheets.id", ondelete="CASCADE"), nullable=False, index=True)
    section = Column(String, nullable=False)      # employee, family, government, mobilization
    category = Column(String, nullable=False)      # vacation, eosb, gosi, etc.
    label = Column(String, nullable=False)         # Human-readable label
    one_time = Column(Float, default=0)
    annual = Column(Float, default=0)
    monthly = Column(Float, default=0)
    sort_order = Column(Integer, nullable=False, default=0)

    quote_sheet = relationship("QuoteSheet", back_populates="cost_lines")

    __table_args__ = (
        sa.UniqueConstraint("quote_sheet_id", "category", name="uq_qs_cost_line_category"),
    )
