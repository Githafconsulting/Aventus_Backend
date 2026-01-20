from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), unique=True, nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    contractor_id = Column(String, ForeignKey("contractors.id"), nullable=False)

    # Document Identification
    invoice_number = Column(String, unique=True, nullable=False, index=True)  # INV-2025-0001

    # Financial Details
    subtotal = Column(Float, nullable=False)
    vat_rate = Column(Float, default=0.05)  # 5% UAE, 15% Saudi
    vat_amount = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)

    # Payment Tracking
    amount_paid = Column(Float, default=0)
    balance = Column(Float, nullable=False)

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_terms = Column(String, nullable=True)  # "Net 30", "Net 60"

    # PDF Storage
    pdf_storage_key = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)

    # Status Workflow
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)
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
    payroll = relationship("Payroll", back_populates="invoice")
    client = relationship("Client", back_populates="invoices")
    contractor = relationship("Contractor", back_populates="invoices")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    # Payment Details
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=True)  # Bank Transfer, Check, etc.
    reference_number = Column(String, nullable=True)  # Transaction reference

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
