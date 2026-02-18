from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class BatchStatus(str, enum.Enum):
    AWAITING_APPROVAL = "awaiting_approval"
    PARTIALLY_APPROVED = "partially_approved"
    SUBMIT_FOR_INVOICE = "submit_for_invoice"
    INVOICE_REQUESTED = "invoice_requested"
    INVOICE_RECEIVED = "invoice_received"
    READY_FOR_PAYMENT = "ready_for_payment"
    INVOICE_UPDATE_REQUESTED = "invoice_update_requested"
    PAID = "paid"
    PAYSLIPS_GENERATED = "payslips_generated"


class PayrollBatch(Base):
    __tablename__ = "payroll_batches"

    id = Column(Integer, primary_key=True, index=True)

    # Grouping keys
    period = Column(String, nullable=False)  # e.g. "January 2026"
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    onboarding_route = Column(String, nullable=False)  # OnboardingRoute value
    route_label = Column(String, nullable=True)  # e.g. "UAE - Auxilium"
    third_party_id = Column(String, ForeignKey("third_parties.id"), nullable=True)

    # Aggregates
    contractor_count = Column(Integer, default=0)
    total_net_salary = Column(Float, default=0)
    total_payable = Column(Float, default=0)
    currency = Column(String(10), default="AED")

    # Status
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.AWAITING_APPROVAL, nullable=False)

    # 3rd party invoice tracking
    tp_invoice_url = Column(String, nullable=True)
    tp_invoice_uploaded_at = Column(DateTime, nullable=True)
    tp_invoice_upload_token = Column(String, unique=True, nullable=True, index=True)
    tp_invoice_token_expiry = Column(DateTime, nullable=True)

    # Invoice request tracking
    invoice_requested_at = Column(DateTime, nullable=True)
    invoice_deadline = Column(DateTime, nullable=True)

    # Finance review
    finance_reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    finance_reviewed_at = Column(DateTime, nullable=True)
    finance_notes = Column(Text, nullable=True)

    # Payment
    paid_at = Column(DateTime, nullable=True)
    paid_by = Column(String, ForeignKey("users.id"), nullable=True)
    payment_reference = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Properties — resolved from FK relationships (Phase 6)
    @property
    def client_name(self):
        try:
            return self.client.company_name if self.client else None
        except Exception:
            return None

    @client_name.setter
    def client_name(self, value):
        pass

    @property
    def third_party_name(self):
        try:
            return self.third_party.company_name if self.third_party else None
        except Exception:
            return None

    @third_party_name.setter
    def third_party_name(self, value):
        pass

    # Relationships
    payrolls = relationship("Payroll", back_populates="batch")
    client = relationship("Client", foreign_keys=[client_id])
    third_party = relationship("ThirdParty", foreign_keys=[third_party_id])
    finance_reviewer = relationship("User", foreign_keys=[finance_reviewed_by])
    payer = relationship("User", foreign_keys=[paid_by])
