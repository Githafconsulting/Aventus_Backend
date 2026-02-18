from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ClientInvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"


class ClientInvoice(Base):
    __tablename__ = "client_invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    period = Column(String, nullable=False)  # e.g. "January 2026"

    # Document Identification
    invoice_number = Column(String, unique=True, nullable=False, index=True)  # CINV-2026-0001

    # Financial Details
    subtotal = Column(Float, default=0)
    vat_rate = Column(Float, default=0.05)
    vat_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)

    # Payment Tracking
    amount_paid = Column(Float, default=0)
    balance = Column(Float, default=0)
    currency = Column(String(10), default="AED")

    # Dates
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    payment_terms = Column(String, nullable=True)  # "Net 30", "Net 60"

    # PDF Storage
    pdf_storage_key = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)

    # Status Workflow
    status = Column(SQLEnum(ClientInvoiceStatus), default=ClientInvoiceStatus.DRAFT)
    sent_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    # Portal Access
    access_token = Column(String, unique=True, nullable=True, index=True)
    token_expiry = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", foreign_keys=[client_id])
    line_items = relationship("ClientInvoiceLineItem", back_populates="client_invoice", cascade="all, delete-orphan")
    payments = relationship("ClientInvoicePayment", back_populates="client_invoice", cascade="all, delete-orphan")


class ClientInvoiceLineItem(Base):
    __tablename__ = "client_invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    client_invoice_id = Column(Integer, ForeignKey("client_invoices.id"), nullable=False)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), nullable=True)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=True)

    # Display info
    description = Column(String, nullable=True)

    # Financials
    subtotal = Column(Float, default=0)
    vat_amount = Column(Float, default=0)
    total = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

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

    # Relationships
    client_invoice = relationship("ClientInvoice", back_populates="line_items")
    payroll = relationship("Payroll", foreign_keys=[payroll_id])
    contractor = relationship("Contractor", foreign_keys=[contractor_id])


class ClientInvoicePayment(Base):
    __tablename__ = "client_invoice_payments"

    id = Column(Integer, primary_key=True, index=True)
    client_invoice_id = Column(Integer, ForeignKey("client_invoices.id"), nullable=False)

    # Payment Details
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client_invoice = relationship("ClientInvoice", back_populates="payments")
