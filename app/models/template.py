from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class TemplateType(str, enum.Enum):
    CONTRACT = "contract"
    CDS = "cds"
    COSTING_SHEET = "costing_sheet"
    WORK_ORDER = "work_order"
    PROPOSAL = "proposal"
    COHF = "cohf"
    SCHEDULE_FORM = "schedule_form"
    QUOTE_SHEET = "quote_sheet"
    PAYSLIP = "payslip"
    INVOICE = "invoice"


class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Template Information
    name = Column(String, nullable=False)
    template_type = Column(String, nullable=False)  # Store as string, validate in Pydantic
    description = Column(Text)

    # Template Content (HTML with placeholders like {{contractor_name}})
    content = Column(Text, nullable=False)

    # Optional: Country-specific templates
    country = Column(String)  # Saudi Arabia, UAE, Qatar, or null for all

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
