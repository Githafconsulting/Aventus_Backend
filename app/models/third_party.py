from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
from datetime import datetime


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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    third_party_documents = relationship("ThirdPartyDocument", back_populates="third_party", cascade="all, delete-orphan")

    @property
    def documents(self):
        """Backward-compat property: serialize child docs as list of dicts."""
        return [
            {
                "type": d.document_type,
                "filename": d.filename,
                "url": d.url,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in (self.third_party_documents or [])
        ]


class ThirdPartyDocument(Base):
    __tablename__ = "third_party_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    third_party_id = Column(String, ForeignKey("third_parties.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    third_party = relationship("ThirdParty", back_populates="third_party_documents")
