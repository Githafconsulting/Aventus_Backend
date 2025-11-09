from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ThirdParty(Base):
    __tablename__ = "third_parties"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False)
    registered_address = Column(String)
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
