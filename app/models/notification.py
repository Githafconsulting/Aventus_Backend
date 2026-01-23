"""
Notification model for storing user notifications
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum
import uuid


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    # Contractor notifications
    TIMESHEET_APPROVED = "timesheet_approved"
    TIMESHEET_DECLINED = "timesheet_declined"
    CONTRACT_READY = "contract_ready"
    CONTRACT_SIGNED = "contract_signed"
    WORK_ORDER_READY = "work_order_ready"
    WORK_ORDER_SIGNED = "work_order_signed"
    DOCUMENT_UPLOADED = "document_uploaded"
    ACCOUNT_ACTIVATED = "account_activated"

    # Admin/Consultant notifications
    NEW_CONTRACTOR = "new_contractor"
    CONTRACTOR_PENDING_REVIEW = "contractor_pending_review"
    CONTRACTOR_APPROVED = "contractor_approved"
    COHF_SIGNED = "cohf_signed"
    QUOTE_SHEET_SIGNED = "quote_sheet_signed"
    DOCUMENTS_UPLOADED = "documents_uploaded"

    # Manager notifications
    TIMESHEET_SUBMITTED = "timesheet_submitted"
    TIMESHEET_UPLOADED = "timesheet_uploaded"

    # General
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)  # The user who receives the notification

    type = Column(String(50), nullable=False)  # NotificationType value
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Optional reference to related entity
    reference_type = Column(String(50), nullable=True)  # e.g., "contractor", "timesheet", "contract"
    reference_id = Column(String(36), nullable=True)  # ID of the related entity

    # Link to navigate to when clicking notification
    action_url = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "action_url": self.action_url,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
