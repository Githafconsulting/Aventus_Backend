from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ThirdParty(Base):
    __tablename__ = "third_parties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Country & Workflow Configuration
    country = Column(String)  # Saudi Arabia, UAE, Qatar
    company_type = Column(String)  # 3rd Party, 3rd Party Payroll
    feature_config = Column(JSON, default=dict)  # Feature configuration (legacy)
    workflow_config = Column(JSON, default=dict)  # Workflow item configuration

    # Company Details
    company_name = Column(String, nullable=False)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    address_line3 = Column(String, nullable=True)
    address_line4 = Column(String, nullable=True)
    company_vat_no = Column(String)
    company_reg_no = Column(String)
    contact_person_name = Column(String)
    contact_person_email = Column(String)
    contact_person_phone = Column(String)
    bank_name = Column(String)
    account_number = Column(String)
    iban_number = Column(String)
    swift_code = Column(String)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    documents = Column(JSON, default=list)  # Store uploaded document URLs

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
