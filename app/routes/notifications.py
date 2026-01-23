"""
Notification API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.notification import Notification, NotificationType
from app.models.user import User

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    action_url: Optional[str]
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


# ============== API ENDPOINTS ==============

@router.get("/")
def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()

    # Count unread
    unread_count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

    return {
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": unread_count,
        "total": len(notifications)
    }


@router.get("/unread-count")
def get_unread_count(user_id: str, db: Session = Depends(get_db)):
    """Get unread notification count for a user"""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

    return {"unread_count": count}


@router.post("/mark-read")
def mark_notifications_read(request: MarkReadRequest, db: Session = Depends(get_db)):
    """Mark specific notifications as read"""
    db.query(Notification).filter(
        Notification.id.in_(request.notification_ids)
    ).update({
        Notification.is_read: True,
        Notification.read_at: datetime.utcnow()
    }, synchronize_session=False)

    db.commit()

    return {"message": "Notifications marked as read", "count": len(request.notification_ids)}


@router.post("/mark-all-read")
def mark_all_read(user_id: str, db: Session = Depends(get_db)):
    """Mark all notifications as read for a user"""
    updated = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({
        Notification.is_read: True,
        Notification.read_at: datetime.utcnow()
    }, synchronize_session=False)

    db.commit()

    return {"message": "All notifications marked as read", "count": updated}


@router.delete("/{notification_id}")
def delete_notification(notification_id: str, db: Session = Depends(get_db)):
    """Delete a notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted"}


@router.delete("/clear-all")
def clear_all_notifications(user_id: str, db: Session = Depends(get_db)):
    """Clear all notifications for a user"""
    deleted = db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.commit()

    return {"message": "All notifications cleared", "count": deleted}


# ============== HELPER FUNCTIONS FOR CREATING NOTIFICATIONS ==============

def create_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    reference_type: str = None,
    reference_id: str = None,
    action_url: str = None
) -> Notification:
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
        action_url=action_url
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_contractor_timesheet_approved(db: Session, contractor_user_id: str, timesheet_month: str):
    """Notify contractor that their timesheet was approved"""
    return create_notification(
        db=db,
        user_id=contractor_user_id,
        notification_type=NotificationType.TIMESHEET_APPROVED.value,
        title="Timesheet Approved",
        message=f"Your timesheet for {timesheet_month} has been approved.",
        reference_type="timesheet",
        action_url="/dashboard/timesheet"
    )


def notify_contractor_timesheet_declined(db: Session, contractor_user_id: str, timesheet_month: str, reason: str = None):
    """Notify contractor that their timesheet was declined"""
    msg = f"Your timesheet for {timesheet_month} has been declined."
    if reason:
        msg += f" Reason: {reason}"
    return create_notification(
        db=db,
        user_id=contractor_user_id,
        notification_type=NotificationType.TIMESHEET_DECLINED.value,
        title="Timesheet Declined",
        message=msg,
        reference_type="timesheet",
        action_url="/dashboard/timesheet"
    )


def notify_contractor_contract_ready(db: Session, contractor_user_id: str, contractor_id: str):
    """Notify contractor that contract is ready to sign"""
    return create_notification(
        db=db,
        user_id=contractor_user_id,
        notification_type=NotificationType.CONTRACT_READY.value,
        title="Contract Ready to Sign",
        message="Your contract is ready for review and signature.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url="/dashboard"
    )


def notify_contractor_work_order_ready(db: Session, contractor_user_id: str, contractor_id: str):
    """Notify contractor that work order is ready"""
    return create_notification(
        db=db,
        user_id=contractor_user_id,
        notification_type=NotificationType.WORK_ORDER_READY.value,
        title="Work Order Ready",
        message="Your work order is ready for review.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url="/dashboard"
    )


def notify_contractor_activated(db: Session, contractor_user_id: str):
    """Notify contractor that their account has been activated"""
    return create_notification(
        db=db,
        user_id=contractor_user_id,
        notification_type=NotificationType.ACCOUNT_ACTIVATED.value,
        title="Account Activated",
        message="Congratulations! Your account has been activated. You can now access all features.",
        action_url="/dashboard"
    )


def notify_admin_new_contractor(db: Session, admin_user_id: str, contractor_name: str, contractor_id: str):
    """Notify admin of new contractor submission"""
    return create_notification(
        db=db,
        user_id=admin_user_id,
        notification_type=NotificationType.NEW_CONTRACTOR.value,
        title="New Contractor Submission",
        message=f"New contractor {contractor_name} has been submitted for review.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url=f"/dashboard/contractors/{contractor_id}"
    )


def notify_admin_contractor_pending(db: Session, admin_user_id: str, contractor_name: str, contractor_id: str):
    """Notify admin of contractor pending review"""
    return create_notification(
        db=db,
        user_id=admin_user_id,
        notification_type=NotificationType.CONTRACTOR_PENDING_REVIEW.value,
        title="Contractor Pending Review",
        message=f"Contractor {contractor_name} is waiting for your review.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url=f"/dashboard/contractors/{contractor_id}"
    )


def notify_admin_cohf_signed(db: Session, admin_user_id: str, contractor_name: str, contractor_id: str):
    """Notify admin that COHF has been signed by 3rd party"""
    return create_notification(
        db=db,
        user_id=admin_user_id,
        notification_type=NotificationType.COHF_SIGNED.value,
        title="COHF Signed",
        message=f"The Confirmation of Hire Form for {contractor_name} has been signed by the 3rd party.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url=f"/dashboard/contractors/{contractor_id}"
    )


def notify_admin_quote_sheet_signed(db: Session, admin_user_id: str, contractor_name: str, contractor_id: str):
    """Notify admin that quote sheet has been signed"""
    return create_notification(
        db=db,
        user_id=admin_user_id,
        notification_type=NotificationType.QUOTE_SHEET_SIGNED.value,
        title="Quote Sheet Signed",
        message=f"The Quote Sheet for {contractor_name} has been signed.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url=f"/dashboard/contractors/{contractor_id}"
    )


def notify_admin_documents_uploaded(db: Session, admin_user_id: str, contractor_name: str, contractor_id: str):
    """Notify admin that contractor documents have been uploaded"""
    return create_notification(
        db=db,
        user_id=admin_user_id,
        notification_type=NotificationType.DOCUMENTS_UPLOADED.value,
        title="Documents Uploaded",
        message=f"Documents for {contractor_name} have been uploaded and are ready for review.",
        reference_type="contractor",
        reference_id=contractor_id,
        action_url=f"/dashboard/contractors/{contractor_id}"
    )


def notify_manager_timesheet_submitted(db: Session, manager_email: str, contractor_name: str, timesheet_month: str, review_link: str):
    """Notify manager that a timesheet has been submitted for approval"""
    # For managers, we use email as user_id since they might not have accounts
    return create_notification(
        db=db,
        user_id=manager_email,  # Using email as identifier for external managers
        notification_type=NotificationType.TIMESHEET_SUBMITTED.value,
        title="Timesheet Submitted",
        message=f"{contractor_name} has submitted their timesheet for {timesheet_month}.",
        reference_type="timesheet",
        action_url=review_link
    )


def notify_users_by_role(db: Session, role: str, notification_type: str, title: str, message: str, reference_type: str = None, reference_id: str = None, action_url: str = None):
    """Notify all users with a specific role"""
    users = db.query(User).filter(User.role == role).all()
    notifications = []
    for user in users:
        notification = create_notification(
            db=db,
            user_id=user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
            action_url=action_url
        )
        notifications.append(notification)
    return notifications
