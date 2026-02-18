from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Client(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Company Information
    company_name = Column(String, nullable=False, unique=True, index=True)
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=False)
    industry = Column(String, nullable=True)
    company_reg_no = Column(String, nullable=True)
    company_vat_no = Column(String, nullable=True)

    # Contact Information
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    address_line3 = Column(String, nullable=True)
    address_line4 = Column(String, nullable=True)
    country = Column(String, nullable=True)

    # Primary Contact Person
    contact_person_name = Column(String, nullable=True)
    contact_person_email = Column(String, nullable=True)
    contact_person_phone = Column(String, nullable=True)
    contact_person_title = Column(String, nullable=True)

    # Banking Information
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    iban_number = Column(String, nullable=True)
    swift_code = Column(String, nullable=True)

    # Additional Information
    website = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    # Workflow Configuration
    work_order_applicable = Column(Boolean, default=False, nullable=True)
    proposal_applicable = Column(Boolean, default=False, nullable=True)

    # Timesheet Configuration
    timesheet_required = Column(Boolean, default=False, nullable=True)
    timesheet_approver_name = Column(String, nullable=True)

    # Payment Terms
    po_required = Column(Boolean, default=False, nullable=True)
    po_number = Column(String, nullable=True)
    contractor_pay_frequency = Column(String, nullable=True)  # Weekly, Bi-weekly, Monthly
    client_invoice_frequency = Column(String, nullable=True)  # Weekly, Bi-weekly, Monthly
    client_payment_terms = Column(String, nullable=True)  # Net 30, Net 60, etc.
    invoicing_preferences = Column(String, nullable=True)  # Consolidated, Per Worker, Consolidated per Project
    invoice_delivery_method = Column(String, nullable=True)  # Upload, Email
    invoice_instructions = Column(String, nullable=True)

    # Supporting Documents
    supporting_documents_required = Column(JSON, default=lambda: [], nullable=True)  # List of required documents: Invoice, Timesheet, etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoices = relationship("Invoice", back_populates="client")
    client_documents = relationship("ClientDocument", back_populates="client", cascade="all, delete-orphan")
    client_projects = relationship("ClientProject", back_populates="client", cascade="all, delete-orphan")

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
            for d in (self.client_documents or [])
        ]

    @property
    def projects(self):
        """Backward-compat property: serialize child projects as list of dicts."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "third_party_id": p.third_party_id,
                "third_party_name": p.third_party_name,
            }
            for p in (self.client_projects or [])
        ]


class ClientDocument(Base):
    __tablename__ = "client_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="client_documents")


class ClientProject(Base):
    __tablename__ = "client_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="Planning")
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)
    third_party_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="client_projects")
