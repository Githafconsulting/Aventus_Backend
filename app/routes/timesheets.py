from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
from app.database import get_db
from app.models.timesheet import Timesheet, TimesheetStatus
from app.models.contractor import Contractor
from app.utils.email import send_timesheet_to_manager
from app.utils.timesheet_pdf_generator import generate_timesheet_pdf
from app.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


# Get all timesheets (admin view)
@router.get("/")
def get_all_timesheets(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all timesheets for admin view"""
    query = db.query(Timesheet)

    if status:
        query = query.filter(Timesheet.status == status)

    timesheets = query.order_by(Timesheet.created_at.desc()).all()

    result = []
    for ts in timesheets:
        # Get contractor info
        contractor = db.query(Contractor).filter(Contractor.id == ts.contractor_id).first()
        contractor_name = f"{contractor.first_name} {contractor.surname}" if contractor and contractor.first_name and contractor.surname else "Unknown"

        result.append({
            "id": ts.id,
            "contractor_id": ts.contractor_id,
            "contractor_name": contractor_name,
            "client_name": contractor.client_name if contractor else "N/A",
            "project_name": contractor.project_name if contractor else "N/A",
            "month": ts.month,
            "year": ts.year,
            "month_number": ts.month_number,
            "total_days": ts.total_days,
            "work_days": ts.work_days,
            "sick_days": ts.sick_days,
            "vacation_days": ts.vacation_days,
            "holiday_days": ts.holiday_days,
            "unpaid_days": ts.unpaid_days,
            "status": ts.status,
            "submitted_date": ts.submitted_date.isoformat() if ts.submitted_date else None,
            "approved_date": ts.approved_date.isoformat() if ts.approved_date else None,
            "declined_date": ts.declined_date.isoformat() if ts.declined_date else None,
            "manager_name": ts.manager_name,
            "manager_email": ts.manager_email,
            "notes": ts.notes,
            "decline_reason": ts.decline_reason,
            "timesheet_data": ts.timesheet_data,
            "timesheet_file_url": ts.timesheet_file_url,
            "is_uploaded": ts.timesheet_file_url is not None,
        })

    return {
        "timesheets": result,
        "total": len(result),
        "pending": len([ts for ts in timesheets if ts.status == TimesheetStatus.PENDING]),
        "approved": len([ts for ts in timesheets if ts.status == TimesheetStatus.APPROVED]),
        "declined": len([ts for ts in timesheets if ts.status == TimesheetStatus.DECLINED]),
    }


# Pydantic models
class TimesheetCreate(BaseModel):
    contractor_id: str
    month: str
    year: int
    month_number: int
    timesheet_data: dict
    total_days: float
    work_days: int
    sick_days: int
    vacation_days: int
    holiday_days: int
    unpaid_days: int
    notes: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None


class TimesheetUpdate(BaseModel):
    timesheet_data: Optional[dict] = None
    total_days: Optional[float] = None
    work_days: Optional[int] = None
    sick_days: Optional[int] = None
    vacation_days: Optional[int] = None
    holiday_days: Optional[int] = None
    unpaid_days: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[TimesheetStatus] = None
    decline_reason: Optional[str] = None


class TimesheetUpload(BaseModel):
    contractor_id: str
    month: str
    year: int
    month_number: int
    notes: Optional[str] = None


# Get all timesheets for a contractor
@router.get("/contractor/{contractor_id}")
def get_contractor_timesheets(
    contractor_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all timesheets for a specific contractor"""
    query = db.query(Timesheet).filter(Timesheet.contractor_id == contractor_id)

    if status:
        query = query.filter(Timesheet.status == status)

    timesheets = query.order_by(Timesheet.created_at.desc()).all()

    return {
        "timesheets": [
            {
                "id": ts.id,
                "month": ts.month,
                "year": ts.year,
                "month_number": ts.month_number,
                "total_days": ts.total_days,
                "work_days": ts.work_days,
                "sick_days": ts.sick_days,
                "vacation_days": ts.vacation_days,
                "holiday_days": ts.holiday_days,
                "unpaid_days": ts.unpaid_days,
                "status": ts.status,
                "submitted_date": ts.submitted_date.isoformat() if ts.submitted_date else None,
                "approved_date": ts.approved_date.isoformat() if ts.approved_date else None,
                "declined_date": ts.declined_date.isoformat() if ts.declined_date else None,
                "manager_name": ts.manager_name,
                "manager_email": ts.manager_email,
                "notes": ts.notes,
                "decline_reason": ts.decline_reason,
                "timesheet_file_url": ts.timesheet_file_url,
                "approval_file_url": ts.approval_file_url,
            }
            for ts in timesheets
        ],
        "total": len(timesheets),
        "pending": len([ts for ts in timesheets if ts.status == TimesheetStatus.PENDING]),
        "approved": len([ts for ts in timesheets if ts.status == TimesheetStatus.APPROVED]),
        "declined": len([ts for ts in timesheets if ts.status == TimesheetStatus.DECLINED]),
    }


# Get contractor info for timesheet
@router.get("/contractor/{contractor_id}/info")
def get_contractor_info(contractor_id: str, db: Session = Depends(get_db)):
    """Get contractor information for filling timesheet"""
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Get placement details from contractor fields (set by CDS form)
    return {
        "id": contractor.id,
        "name": f"{contractor.first_name} {contractor.surname}" if contractor.first_name and contractor.surname else "N/A",
        "client_name": contractor.client_name or "N/A",
        "project_name": contractor.project_name or "N/A",
        "location": contractor.location or "N/A",
    }


# Create a new timesheet (fill timesheet)
@router.post("/")
def create_timesheet(timesheet: TimesheetCreate, db: Session = Depends(get_db)):
    """Create a new timesheet"""
    # Check if contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == timesheet.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Check if timesheet already exists for this month
    existing = db.query(Timesheet).filter(
        Timesheet.contractor_id == timesheet.contractor_id,
        Timesheet.year == timesheet.year,
        Timesheet.month_number == timesheet.month_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Timesheet already exists for this month. Please update the existing one."
        )

    # Generate review token for manager
    review_token = secrets.token_urlsafe(32)
    review_token_expiry = datetime.utcnow() + timedelta(days=7)  # 7 days to review

    # Create new timesheet
    new_timesheet = Timesheet(
        contractor_id=timesheet.contractor_id,
        month=timesheet.month,
        year=timesheet.year,
        month_number=timesheet.month_number,
        timesheet_data=timesheet.timesheet_data,
        total_days=timesheet.total_days,
        work_days=timesheet.work_days,
        sick_days=timesheet.sick_days,
        vacation_days=timesheet.vacation_days,
        holiday_days=timesheet.holiday_days,
        unpaid_days=timesheet.unpaid_days,
        notes=timesheet.notes,
        manager_name=timesheet.manager_name,
        manager_email=timesheet.manager_email,
        status=TimesheetStatus.PENDING,
        submitted_date=datetime.utcnow(),
        review_token=review_token,
        review_token_expiry=review_token_expiry
    )

    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)

    # Get contractor name for email
    contractor_name = f"{contractor.first_name} {contractor.surname}" if contractor.first_name and contractor.surname else "Contractor"

    # Generate PDF
    pdf_data = {
        "contractor_name": contractor_name,
        "client_name": contractor.client_name or "N/A",
        "project_name": contractor.project_name or "N/A",
        "location": contractor.location or "N/A",
        "month": timesheet.month,
        "manager_name": timesheet.manager_name,
        "manager_email": timesheet.manager_email,
        "total_days": timesheet.total_days,
        "work_days": timesheet.work_days,
        "sick_days": timesheet.sick_days,
        "vacation_days": timesheet.vacation_days,
        "holiday_days": timesheet.holiday_days,
        "unpaid_days": timesheet.unpaid_days,
        "submitted_date": datetime.utcnow().strftime("%B %d, %Y"),
        "status": "pending",
        "notes": timesheet.notes or ""
    }

    pdf_buffer = generate_timesheet_pdf(pdf_data)
    pdf_content = pdf_buffer.read()

    # Send email to manager with PDF attachment
    review_link = f"{settings.frontend_url}/timesheet/review/{review_token}"

    email_sent = send_timesheet_to_manager(
        manager_email=timesheet.manager_email,
        manager_name=timesheet.manager_name,
        contractor_name=contractor_name,
        timesheet_month=timesheet.month,
        review_link=review_link,
        total_days=timesheet.total_days,
        work_days=timesheet.work_days,
        sick_days=timesheet.sick_days,
        vacation_days=timesheet.vacation_days,
        pdf_content=pdf_content
    )

    return {
        "message": "Timesheet created successfully" + (" and sent to manager for approval" if email_sent else ""),
        "timesheet_id": new_timesheet.id,
        "email_sent": email_sent
    }


# Upload timesheet files
@router.post("/upload")
async def upload_timesheet(
    contractor_id: str = Form(...),
    month: str = Form(...),
    year: str = Form(...),
    month_number: str = Form(...),
    manager_name: str = Form(...),
    manager_email: str = Form(...),
    notes: Optional[str] = Form(None),
    timesheet_file: UploadFile = File(...),
    approval_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Upload timesheet document with files"""
    try:
        from app.utils.storage import upload_file
        from io import BytesIO
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage initialization error: {str(e)}")

    # Convert string inputs to proper types
    year_int = int(year)
    month_number_int = int(month_number)

    # Check if contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Check if timesheet already exists
    existing = db.query(Timesheet).filter(
        Timesheet.contractor_id == contractor_id,
        Timesheet.year == year_int,
        Timesheet.month_number == month_number_int
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Timesheet already exists for this month"
        )

    # Upload timesheet file
    timesheet_file_content = await timesheet_file.read()
    timesheet_file_url = upload_file(
        BytesIO(timesheet_file_content),
        f"{year_int}_{month_number_int}_timesheet_{timesheet_file.filename}",
        f"timesheets/{contractor_id}"
    )

    # Upload approval file if provided
    approval_file_url = None
    if approval_file:
        approval_file_content = await approval_file.read()
        approval_file_url = upload_file(
            BytesIO(approval_file_content),
            f"{year_int}_{month_number_int}_approval_{approval_file.filename}",
            f"timesheets/{contractor_id}"
        )

    # Generate review token
    review_token = secrets.token_urlsafe(32)
    review_token_expiry = datetime.utcnow() + timedelta(days=7)

    # Create timesheet with file URLs
    new_timesheet = Timesheet(
        contractor_id=contractor_id,
        month=month,
        year=year_int,
        month_number=month_number_int,
        notes=notes,
        manager_name=manager_name,
        manager_email=manager_email,
        status=TimesheetStatus.PENDING,
        submitted_date=datetime.utcnow(),
        timesheet_file_url=timesheet_file_url,
        approval_file_url=approval_file_url,
        review_token=review_token,
        review_token_expiry=review_token_expiry
    )

    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)

    # Send email to manager
    contractor_name = f"{contractor.first_name} {contractor.surname}" if contractor.first_name and contractor.surname else "Contractor"
    review_link = f"{settings.frontend_url}/timesheet/review/{review_token}"

    from app.utils.email import send_uploaded_timesheet_to_manager

    email_sent = send_uploaded_timesheet_to_manager(
        manager_email=manager_email,
        manager_name=manager_name,
        contractor_name=contractor_name,
        timesheet_month=month,
        review_link=review_link,
        file_content=timesheet_file_content,
        filename=timesheet_file.filename
    )

    return {
        "message": "Timesheet uploaded successfully" + (" and sent to manager for approval" if email_sent else ""),
        "timesheet_id": new_timesheet.id,
        "email_sent": email_sent
    }


# Get timesheet by ID
@router.get("/{timesheet_id}")
def get_timesheet(timesheet_id: int, db: Session = Depends(get_db)):
    """Get a specific timesheet by ID"""
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    return {
        "id": timesheet.id,
        "contractor_id": timesheet.contractor_id,
        "month": timesheet.month,
        "year": timesheet.year,
        "month_number": timesheet.month_number,
        "timesheet_data": timesheet.timesheet_data,
        "total_days": timesheet.total_days,
        "work_days": timesheet.work_days,
        "sick_days": timesheet.sick_days,
        "vacation_days": timesheet.vacation_days,
        "holiday_days": timesheet.holiday_days,
        "unpaid_days": timesheet.unpaid_days,
        "status": timesheet.status,
        "submitted_date": timesheet.submitted_date.isoformat() if timesheet.submitted_date else None,
        "approved_date": timesheet.approved_date.isoformat() if timesheet.approved_date else None,
        "declined_date": timesheet.declined_date.isoformat() if timesheet.declined_date else None,
        "manager_name": timesheet.manager_name,
        "manager_email": timesheet.manager_email,
        "notes": timesheet.notes,
        "decline_reason": timesheet.decline_reason,
        "timesheet_file_url": timesheet.timesheet_file_url,
        "approval_file_url": timesheet.approval_file_url,
    }


# Update timesheet
@router.put("/{timesheet_id}")
def update_timesheet(
    timesheet_id: int,
    updates: TimesheetUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing timesheet"""
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    # Update fields
    if updates.timesheet_data is not None:
        timesheet.timesheet_data = updates.timesheet_data
    if updates.total_days is not None:
        timesheet.total_days = updates.total_days
    if updates.work_days is not None:
        timesheet.work_days = updates.work_days
    if updates.sick_days is not None:
        timesheet.sick_days = updates.sick_days
    if updates.vacation_days is not None:
        timesheet.vacation_days = updates.vacation_days
    if updates.holiday_days is not None:
        timesheet.holiday_days = updates.holiday_days
    if updates.unpaid_days is not None:
        timesheet.unpaid_days = updates.unpaid_days
    if updates.notes is not None:
        timesheet.notes = updates.notes
    if updates.status is not None:
        timesheet.status = updates.status
        if updates.status == TimesheetStatus.APPROVED:
            timesheet.approved_date = datetime.utcnow()
        elif updates.status == TimesheetStatus.DECLINED:
            timesheet.declined_date = datetime.utcnow()
    if updates.decline_reason is not None:
        timesheet.decline_reason = updates.decline_reason

    db.commit()
    db.refresh(timesheet)

    return {"message": "Timesheet updated successfully"}


# Delete timesheet
@router.delete("/{timesheet_id}")
def delete_timesheet(timesheet_id: int, db: Session = Depends(get_db)):
    """Delete a timesheet"""
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    db.delete(timesheet)
    db.commit()

    return {"message": "Timesheet deleted successfully"}


# ============== PUBLIC ENDPOINTS FOR MANAGER REVIEW ==============

# Get timesheet by review token (public - no auth required)
@router.get("/review/{token}")
def get_timesheet_by_token(token: str, db: Session = Depends(get_db)):
    """Get timesheet details by review token for manager review"""
    timesheet = db.query(Timesheet).filter(Timesheet.review_token == token).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found or invalid token")

    # Check if token is expired
    if timesheet.review_token_expiry and timesheet.review_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Review link has expired")

    # Get contractor info
    contractor = db.query(Contractor).filter(Contractor.id == timesheet.contractor_id).first()
    contractor_name = f"{contractor.first_name} {contractor.surname}" if contractor and contractor.first_name and contractor.surname else "Contractor"

    return {
        "id": timesheet.id,
        "contractor_name": contractor_name,
        "client_name": contractor.client_name if contractor else "N/A",
        "project_name": contractor.project_name if contractor else "N/A",
        "location": contractor.location if contractor else "N/A",
        "month": timesheet.month,
        "year": timesheet.year,
        "timesheet_data": timesheet.timesheet_data,
        "total_days": timesheet.total_days,
        "work_days": timesheet.work_days,
        "sick_days": timesheet.sick_days,
        "vacation_days": timesheet.vacation_days,
        "holiday_days": timesheet.holiday_days,
        "unpaid_days": timesheet.unpaid_days,
        "status": timesheet.status,
        "submitted_date": timesheet.submitted_date.isoformat() if timesheet.submitted_date else None,
        "manager_name": timesheet.manager_name,
        "manager_email": timesheet.manager_email,
        "notes": timesheet.notes,
        "timesheet_file_url": timesheet.timesheet_file_url,
        "is_uploaded": timesheet.timesheet_file_url is not None,
    }


# Approve timesheet (public - via token)
@router.post("/review/{token}/approve")
def approve_timesheet_by_token(token: str, db: Session = Depends(get_db)):
    """Approve timesheet via review token"""
    timesheet = db.query(Timesheet).filter(Timesheet.review_token == token).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found or invalid token")

    # Check if token is expired
    if timesheet.review_token_expiry and timesheet.review_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Review link has expired")

    # Check if already processed
    if timesheet.status != TimesheetStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Timesheet has already been {timesheet.status.value}"
        )

    # Update status to approved
    timesheet.status = TimesheetStatus.APPROVED
    timesheet.approved_date = datetime.utcnow()

    db.commit()
    db.refresh(timesheet)

    return {
        "message": "Timesheet approved successfully",
        "status": timesheet.status.value,
        "approved_date": timesheet.approved_date.isoformat()
    }


# Decline timesheet (public - via token)
class DeclineRequest(BaseModel):
    reason: str

@router.post("/review/{token}/decline")
def decline_timesheet_by_token(token: str, request: DeclineRequest, db: Session = Depends(get_db)):
    """Decline timesheet via review token with reason"""
    timesheet = db.query(Timesheet).filter(Timesheet.review_token == token).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found or invalid token")

    # Check if token is expired
    if timesheet.review_token_expiry and timesheet.review_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Review link has expired")

    # Check if already processed
    if timesheet.status != TimesheetStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Timesheet has already been {timesheet.status.value}"
        )

    # Update status to declined
    timesheet.status = TimesheetStatus.DECLINED
    timesheet.declined_date = datetime.utcnow()
    timesheet.decline_reason = request.reason

    db.commit()
    db.refresh(timesheet)

    return {
        "message": "Timesheet declined",
        "status": timesheet.status.value,
        "declined_date": timesheet.declined_date.isoformat(),
        "decline_reason": timesheet.decline_reason
    }


# Get timesheet PDF by token (public)
@router.get("/review/{token}/pdf")
def get_timesheet_pdf_by_token(token: str, db: Session = Depends(get_db)):
    """Get timesheet PDF by review token"""
    from fastapi.responses import StreamingResponse

    timesheet = db.query(Timesheet).filter(Timesheet.review_token == token).first()

    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found or invalid token")

    # Get contractor info
    contractor = db.query(Contractor).filter(Contractor.id == timesheet.contractor_id).first()
    contractor_name = f"{contractor.first_name} {contractor.surname}" if contractor and contractor.first_name and contractor.surname else "Contractor"

    # Generate PDF
    pdf_data = {
        "contractor_name": contractor_name,
        "client_name": contractor.client_name if contractor else "N/A",
        "project_name": contractor.project_name if contractor else "N/A",
        "location": contractor.location if contractor else "N/A",
        "month": timesheet.month,
        "manager_name": timesheet.manager_name,
        "manager_email": timesheet.manager_email,
        "total_days": timesheet.total_days,
        "work_days": timesheet.work_days,
        "sick_days": timesheet.sick_days,
        "vacation_days": timesheet.vacation_days,
        "holiday_days": timesheet.holiday_days,
        "unpaid_days": timesheet.unpaid_days,
        "submitted_date": timesheet.submitted_date.strftime("%B %d, %Y") if timesheet.submitted_date else "N/A",
        "status": timesheet.status.value,
        "notes": timesheet.notes or ""
    }

    pdf_buffer = generate_timesheet_pdf(pdf_data)

    filename = f"Timesheet_{contractor_name.replace(' ', '_')}_{timesheet.month.replace(' ', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
