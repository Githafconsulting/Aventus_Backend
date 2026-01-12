from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from io import BytesIO

from app.database import get_db
from app.models.payroll import Payroll, PayrollStatus
from app.models.timesheet import Timesheet, TimesheetStatus
from app.models.contractor import Contractor
from app.schemas.payroll import (
    PayrollCreate,
    PayrollUpdate,
    PayrollResponse,
    PayrollListResponse,
    TimesheetReadyForPayroll,
)

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])


def _get_contractor_pay_info(contractor: Contractor) -> dict:
    """Extract pay information from contractor, supporting both day and monthly rates."""
    day_rate = None
    charge_rate_day = None
    currency = contractor.currency or "USD"
    rate_type = contractor.rate_type or "monthly"

    # Get estimated working days from costing sheet (default 22)
    working_days_per_month = 22
    if contractor.costing_sheet_data and contractor.costing_sheet_data.get("estimated_working_days"):
        try:
            working_days_per_month = float(contractor.costing_sheet_data["estimated_working_days"])
        except (ValueError, TypeError):
            pass

    # Try to get day rate directly first
    if contractor.day_rate:
        try:
            day_rate = float(contractor.day_rate)
        except (ValueError, TypeError):
            pass

    # If no day rate but we have monthly rate, calculate day rate
    if day_rate is None and rate_type == "monthly":
        # Try gross_salary first
        if contractor.gross_salary:
            try:
                monthly_salary = float(contractor.gross_salary)
                day_rate = monthly_salary / working_days_per_month
            except (ValueError, TypeError):
                pass
        # Also check CDS form data
        if day_rate is None and contractor.cds_form_data:
            cds = contractor.cds_form_data
            if cds.get("grossSalary"):
                try:
                    monthly_salary = float(cds["grossSalary"])
                    day_rate = monthly_salary / working_days_per_month
                except (ValueError, TypeError):
                    pass

    # Try charge rate day directly
    if contractor.charge_rate_day:
        try:
            charge_rate_day = float(contractor.charge_rate_day)
        except (ValueError, TypeError):
            pass

    # If no charge rate day but we have monthly charge rate, calculate it
    if charge_rate_day is None and rate_type == "monthly":
        # Try charge_rate_month
        if contractor.charge_rate_month:
            try:
                monthly_charge = float(contractor.charge_rate_month)
                charge_rate_day = monthly_charge / working_days_per_month
            except (ValueError, TypeError):
                pass
        # Also check CDS form data
        if charge_rate_day is None and contractor.cds_form_data:
            cds = contractor.cds_form_data
            if cds.get("chargeRateMonth"):
                try:
                    monthly_charge = float(cds["chargeRateMonth"])
                    charge_rate_day = monthly_charge / working_days_per_month
                except (ValueError, TypeError):
                    pass

    return {
        "day_rate": day_rate,
        "charge_rate_day": charge_rate_day,
        "currency": currency,
        "rate_type": rate_type,
        "working_days_per_month": working_days_per_month,
    }


@router.get("/ready")
def get_timesheets_ready_for_payroll(
    db: Session = Depends(get_db)
):
    """Get approved timesheets that don't have payroll records yet."""
    # Get approved timesheets without payroll records
    timesheets = (
        db.query(Timesheet)
        .outerjoin(Payroll, Timesheet.id == Payroll.timesheet_id)
        .filter(Timesheet.status == TimesheetStatus.APPROVED)
        .filter(Payroll.id == None)  # No payroll record
        .order_by(Timesheet.approved_date.desc())
        .all()
    )

    result = []
    for ts in timesheets:
        contractor = db.query(Contractor).filter(Contractor.id == ts.contractor_id).first()
        if not contractor:
            continue

        pay_info = _get_contractor_pay_info(contractor)
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        # Calculate estimated gross
        estimated_gross = None
        if pay_info["day_rate"] and ts.work_days:
            estimated_gross = pay_info["day_rate"] * ts.work_days

        result.append({
            "id": ts.id,
            "contractor_id": ts.contractor_id,
            "contractor_name": contractor_name,
            "contractor_email": contractor.email,
            "client_name": contractor.client_name,
            "period": ts.month,
            "work_days": ts.work_days,
            "total_days": ts.total_days,
            "day_rate": pay_info["day_rate"],
            "charge_rate_day": pay_info["charge_rate_day"],
            "currency": pay_info["currency"],
            "estimated_gross": estimated_gross,
            "submitted_date": ts.submitted_date,
            "approved_date": ts.approved_date,
        })

    return {"timesheets": result, "total": len(result)}


@router.get("/")
def get_all_payroll_records(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all payroll records with optional status filter."""
    query = db.query(Payroll)

    if status:
        try:
            status_enum = PayrollStatus(status)
            query = query.filter(Payroll.status == status_enum)
        except ValueError:
            pass

    payrolls = query.order_by(Payroll.created_at.desc()).all()

    result = []
    for p in payrolls:
        contractor = db.query(Contractor).filter(Contractor.id == p.contractor_id).first()
        contractor_name = "Unknown"
        contractor_email = None
        client_name = None

        if contractor:
            contractor_name = f"{contractor.first_name} {contractor.surname}"
            contractor_email = contractor.email
            client_name = contractor.client_name

        result.append({
            "id": p.id,
            "timesheet_id": p.timesheet_id,
            "contractor_id": p.contractor_id,
            "contractor_name": contractor_name,
            "contractor_email": contractor_email,
            "client_name": client_name,
            "period": p.period,
            "work_days": p.work_days,
            "day_rate": p.day_rate,
            "gross_amount": p.gross_amount,
            "deductions": p.deductions,
            "net_amount": p.net_amount,
            "currency": p.currency,
            "charge_rate_day": p.charge_rate_day,
            "invoice_amount": p.invoice_amount,
            "status": p.status.value,
            "calculated_at": p.calculated_at,
            "approved_at": p.approved_at,
            "paid_at": p.paid_at,
        })

    # Count by status
    all_payrolls = db.query(Payroll).all()
    status_counts = {
        "calculated": len([p for p in all_payrolls if p.status == PayrollStatus.CALCULATED]),
        "approved": len([p for p in all_payrolls if p.status == PayrollStatus.APPROVED]),
        "paid": len([p for p in all_payrolls if p.status == PayrollStatus.PAID]),
    }

    return {
        "payrolls": result,
        "total": len(result),
        **status_counts,
    }


@router.post("/{timesheet_id}/calculate")
def calculate_payroll(
    timesheet_id: int,
    deductions: float = 0,
    db: Session = Depends(get_db)
):
    """Calculate payroll for a specific timesheet."""
    # Check if timesheet exists
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    # Check if timesheet is approved
    if timesheet.status != TimesheetStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Timesheet must be approved before payroll calculation")

    # Check if payroll already exists
    existing = db.query(Payroll).filter(Payroll.timesheet_id == timesheet_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Payroll already calculated for this timesheet")

    # Get contractor
    contractor = db.query(Contractor).filter(Contractor.id == timesheet.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Get pay info
    pay_info = _get_contractor_pay_info(contractor)

    if not pay_info["day_rate"]:
        raise HTTPException(status_code=400, detail="Contractor does not have a day rate configured")

    # Calculate amounts
    work_days = timesheet.work_days or 0
    day_rate = pay_info["day_rate"]
    gross_amount = day_rate * work_days
    net_amount = gross_amount - deductions

    # Calculate invoice amount if charge rate exists
    charge_rate_day = pay_info["charge_rate_day"]
    invoice_amount = None
    if charge_rate_day:
        invoice_amount = charge_rate_day * work_days

    # Create payroll record
    payroll = Payroll(
        timesheet_id=timesheet_id,
        contractor_id=contractor.id,
        day_rate=day_rate,
        work_days=work_days,
        gross_amount=gross_amount,
        deductions=deductions,
        net_amount=net_amount,
        currency=pay_info["currency"],
        charge_rate_day=charge_rate_day,
        invoice_amount=invoice_amount,
        status=PayrollStatus.CALCULATED,
        period=timesheet.month,
        calculated_at=datetime.utcnow(),
    )

    db.add(payroll)
    db.commit()
    db.refresh(payroll)

    contractor_name = f"{contractor.first_name} {contractor.surname}"

    return {
        "id": payroll.id,
        "timesheet_id": payroll.timesheet_id,
        "contractor_id": payroll.contractor_id,
        "contractor_name": contractor_name,
        "period": payroll.period,
        "work_days": payroll.work_days,
        "day_rate": payroll.day_rate,
        "gross_amount": payroll.gross_amount,
        "deductions": payroll.deductions,
        "net_amount": payroll.net_amount,
        "currency": payroll.currency,
        "charge_rate_day": payroll.charge_rate_day,
        "invoice_amount": payroll.invoice_amount,
        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
    }


@router.get("/{payroll_id}")
def get_payroll(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Get a single payroll record."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    contractor_name = "Unknown"
    contractor_email = None
    client_name = None

    if contractor:
        contractor_name = f"{contractor.first_name} {contractor.surname}"
        contractor_email = contractor.email
        client_name = contractor.client_name

    return {
        "id": payroll.id,
        "timesheet_id": payroll.timesheet_id,
        "contractor_id": payroll.contractor_id,
        "contractor_name": contractor_name,
        "contractor_email": contractor_email,
        "client_name": client_name,
        "period": payroll.period,
        "work_days": payroll.work_days,
        "day_rate": payroll.day_rate,
        "gross_amount": payroll.gross_amount,
        "deductions": payroll.deductions,
        "net_amount": payroll.net_amount,
        "currency": payroll.currency,
        "charge_rate_day": payroll.charge_rate_day,
        "invoice_amount": payroll.invoice_amount,
        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
        "approved_at": payroll.approved_at,
        "paid_at": payroll.paid_at,
    }


@router.get("/{payroll_id}/detailed")
def get_payroll_detailed(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed payroll calculation data for display."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    timesheet = db.query(Timesheet).filter(Timesheet.id == payroll.timesheet_id).first()

    contractor_name = f"{contractor.first_name} {contractor.surname}"

    # Get rate info
    pay_info = _get_contractor_pay_info(contractor)
    rate_type = pay_info.get("rate_type", "monthly")
    working_days_per_month = pay_info.get("working_days_per_month", 22)

    # Get monthly rate from CDS
    monthly_rate = 0
    if contractor.gross_salary:
        try:
            monthly_rate = float(contractor.gross_salary)
        except (ValueError, TypeError):
            pass
    if monthly_rate == 0 and contractor.cds_form_data:
        cds = contractor.cds_form_data
        if cds.get("grossSalary"):
            try:
                monthly_rate = float(cds["grossSalary"])
            except (ValueError, TypeError):
                pass

    # Get timesheet data
    work_days = timesheet.work_days if timesheet else payroll.work_days
    holiday_days = timesheet.holiday_days if timesheet else 0
    sick_days = timesheet.sick_days if timesheet else 0
    vacation_days = timesheet.vacation_days if timesheet else 0
    unpaid_days = timesheet.unpaid_days if timesheet else 0
    total_days = timesheet.total_days if timesheet else payroll.work_days

    # Leave calculations
    leave_allowance = 30  # Default annual leave
    if contractor.vacation_days:
        try:
            leave_allowance = int(contractor.vacation_days)
        except (ValueError, TypeError):
            pass

    carry_over_balance = 0  # This would come from previous year data
    leave_taken = vacation_days
    leave_balance = leave_allowance - leave_taken
    leave_deductibles = 0
    if leave_balance < 0:
        # Deduct for excess leave
        daily_rate = monthly_rate / working_days_per_month if working_days_per_month > 0 else 0
        leave_deductibles = daily_rate * abs(leave_balance)

    # Management fee from costing sheet
    management_fee = 0
    management_company_name = ""
    if contractor.costing_sheet_data:
        costing = contractor.costing_sheet_data
        if costing.get("management_company_charges"):
            try:
                management_fee = float(costing["management_company_charges"])
            except (ValueError, TypeError):
                pass
    if contractor.company_name:
        management_company_name = contractor.company_name

    # Accruals from costing sheet
    eosb = 0
    vacation_accrual = 0
    other_accruals = 0
    if contractor.costing_sheet_data:
        costing = contractor.costing_sheet_data
        if costing.get("eosb"):
            try:
                eosb = float(costing["eosb"])
            except (ValueError, TypeError):
                pass
        if costing.get("leave"):
            try:
                vacation_accrual = float(costing["leave"])
            except (ValueError, TypeError):
                pass

    # Calculate totals
    gross_pay = payroll.gross_amount
    total_deductions = payroll.deductions + management_fee + leave_deductibles
    reimbursements = 0  # Would come from expenses module
    net_pay = gross_pay - total_deductions + reimbursements

    return {
        # Basic Info
        "contractor_name": contractor_name,
        "contractor_id": contractor.id,
        "client_name": contractor.client_name,
        "period": payroll.period,
        "currency": payroll.currency,

        # Rate Info
        "rate_type": rate_type,
        "monthly_rate": monthly_rate,
        "day_rate": payroll.day_rate,

        # Timesheet Data
        "work_days": work_days,
        "holiday_days": holiday_days,
        "sick_days": sick_days,
        "vacation_days": vacation_days,
        "unpaid_days": unpaid_days,
        "total_days": total_days,

        # Working Days Config
        "monthly_working_days": working_days_per_month,

        # Leave Adjustments
        "carry_over_leave_balance": carry_over_balance,
        "leave_allowance": leave_allowance,
        "leave_taken": leave_taken,
        "leave_balance": leave_balance,
        "leave_deductibles": leave_deductibles,

        # Expenses
        "reimbursements": reimbursements,

        # 3rd Party Fees
        "management_fee": management_fee,
        "management_company_name": management_company_name,

        # Accruals
        "eosb": eosb,
        "vacation_accrual": vacation_accrual,
        "other_accruals": other_accruals,

        # Totals
        "gross_pay": gross_pay,
        "total_deductions": total_deductions,
        "net_pay": net_pay,

        # Payroll record info
        "payroll_id": payroll.id,
        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
        "approved_at": payroll.approved_at,
        "paid_at": payroll.paid_at,

        # Invoice
        "charge_rate_day": payroll.charge_rate_day,
        "invoice_amount": payroll.invoice_amount,
    }


@router.put("/{payroll_id}/approve")
def approve_payroll(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Approve a payroll record (mark as ready for payment)."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    if payroll.status != PayrollStatus.CALCULATED:
        raise HTTPException(status_code=400, detail="Payroll must be in CALCULATED status to approve")

    payroll.status = PayrollStatus.APPROVED
    payroll.approved_at = datetime.utcnow()
    db.commit()

    return {"message": "Payroll approved successfully", "status": payroll.status.value}


@router.put("/{payroll_id}/mark-paid")
def mark_payroll_paid(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Mark a payroll record as paid."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    if payroll.status != PayrollStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Payroll must be approved before marking as paid")

    payroll.status = PayrollStatus.PAID
    payroll.paid_at = datetime.utcnow()
    db.commit()

    return {"message": "Payroll marked as paid", "status": payroll.status.value}


@router.get("/{payroll_id}/payslip")
def download_payslip(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Download payslip PDF for a payroll record."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Import PDF generator
    from app.utils.payroll_pdf import generate_payslip_pdf

    contractor_name = f"{contractor.first_name} {contractor.surname}"

    pdf_buffer = generate_payslip_pdf(
        payroll=payroll,
        contractor=contractor,
    )

    filename = f"payslip_{contractor_name.replace(' ', '_')}_{payroll.period.replace(' ', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{payroll_id}/invoice")
def download_invoice(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Download invoice PDF for a payroll record."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    if not payroll.charge_rate_day or not payroll.invoice_amount:
        raise HTTPException(status_code=400, detail="No charge rate configured for invoice generation")

    # Import PDF generator
    from app.utils.payroll_pdf import generate_invoice_pdf

    contractor_name = f"{contractor.first_name} {contractor.surname}"

    pdf_buffer = generate_invoice_pdf(
        payroll=payroll,
        contractor=contractor,
    )

    filename = f"invoice_{contractor_name.replace(' ', '_')}_{payroll.period.replace(' ', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
