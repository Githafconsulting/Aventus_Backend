from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.timesheet import Timesheet, TimesheetStatus
from app.models.contractor import Contractor
from pydantic import BaseModel

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


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

    # Extract placement details from cds_form_data if available
    cds_data = contractor.cds_form_data or {}

    return {
        "id": contractor.id,
        "name": f"{contractor.first_name} {contractor.last_name}" if contractor.first_name and contractor.last_name else "N/A",
        "client_name": cds_data.get("clientName", "N/A"),
        "project_name": cds_data.get("projectName", "N/A"),
        "location": cds_data.get("location", "N/A"),
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
        status=TimesheetStatus.PENDING,
        submitted_date=datetime.utcnow()
    )

    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)

    return {
        "message": "Timesheet created successfully",
        "timesheet_id": new_timesheet.id
    }


# Upload timesheet files
@router.post("/upload")
def upload_timesheet(
    contractor_id: str,
    month: str,
    year: int,
    month_number: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload timesheet document (placeholder for file handling)"""
    # Check if contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Check if timesheet already exists
    existing = db.query(Timesheet).filter(
        Timesheet.contractor_id == contractor_id,
        Timesheet.year == year,
        Timesheet.month_number == month_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Timesheet already exists for this month"
        )

    # Create timesheet with file upload
    new_timesheet = Timesheet(
        contractor_id=contractor_id,
        month=month,
        year=year,
        month_number=month_number,
        notes=notes,
        status=TimesheetStatus.PENDING,
        submitted_date=datetime.utcnow(),
        # File URLs would be set after actual file upload
        timesheet_file_url="placeholder_file_url",
        approval_file_url="placeholder_approval_url"
    )

    db.add(new_timesheet)
    db.commit()
    db.refresh(new_timesheet)

    return {
        "message": "Timesheet uploaded successfully",
        "timesheet_id": new_timesheet.id
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
