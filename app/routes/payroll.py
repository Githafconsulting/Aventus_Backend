from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import Optional
from datetime import datetime
from calendar import monthrange
from io import BytesIO

from app.database import get_db
from app.models.payroll import Payroll, PayrollStatus, RateType
from app.models.timesheet import Timesheet, TimesheetStatus
from app.models.contractor import Contractor

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])


def _get_calendar_days_in_month(period: str) -> int:
    """Get total calendar days in a month from period string like 'November 2024'."""
    try:
        date = datetime.strptime(period, "%B %Y")
        return monthrange(date.year, date.month)[1]
    except:
        return 30  # Default fallback


def _get_vat_rate(country: str) -> float:
    """Get VAT rate based on country."""
    country_lower = (country or "").lower()
    if "saudi" in country_lower or "ksa" in country_lower:
        return 0.15  # 15% for Saudi
    elif "uae" in country_lower or "emirates" in country_lower or "dubai" in country_lower:
        return 0.05  # 5% for UAE
    return 0.05  # Default to UAE


def _get_contractor_full_info(contractor: Contractor, db: Session) -> dict:
    """Extract all pay-related information from contractor."""
    # Basic rate info
    rate_type = (contractor.rate_type or "monthly").lower()
    currency = contractor.currency or "AED"

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

    # Get day rate
    day_rate = None
    if contractor.day_rate:
        try:
            day_rate = float(contractor.day_rate)
        except (ValueError, TypeError):
            pass
    if day_rate is None and contractor.cds_form_data:
        cds = contractor.cds_form_data
        if cds.get("dayRate"):
            try:
                day_rate = float(cds["dayRate"])
            except (ValueError, TypeError):
                pass

    # Get charge rates for invoicing
    charge_rate_month = 0
    if contractor.charge_rate_month:
        try:
            charge_rate_month = float(contractor.charge_rate_month)
        except (ValueError, TypeError):
            pass
    if charge_rate_month == 0 and contractor.cds_form_data:
        cds = contractor.cds_form_data
        if cds.get("chargeRateMonth"):
            try:
                charge_rate_month = float(cds["chargeRateMonth"])
            except (ValueError, TypeError):
                pass

    charge_rate_day = None
    if contractor.charge_rate_day:
        try:
            charge_rate_day = float(contractor.charge_rate_day)
        except (ValueError, TypeError):
            pass
    if charge_rate_day is None and contractor.cds_form_data:
        cds = contractor.cds_form_data
        if cds.get("chargeRateDay"):
            try:
                charge_rate_day = float(cds["chargeRateDay"])
            except (ValueError, TypeError):
                pass

    # Leave allowance from CDS (annual leave days)
    leave_allowance = 30  # Default
    # First check the new leave_allowance field
    if contractor.leave_allowance:
        try:
            leave_allowance = float(contractor.leave_allowance)
        except (ValueError, TypeError):
            pass
    # Check CDS form data for leaveAllowance
    if contractor.cds_form_data and contractor.cds_form_data.get("leaveAllowance"):
        try:
            leave_allowance = float(contractor.cds_form_data["leaveAllowance"])
        except (ValueError, TypeError):
            pass
    # Fallback to old vacation_days field
    elif contractor.vacation_days:
        try:
            leave_allowance = float(contractor.vacation_days)
        except (ValueError, TypeError):
            pass

    # Third party / Management company info
    third_party_name = contractor.company_name or ""

    # Management fee from costing sheet
    management_fee = 0
    if contractor.costing_sheet_data:
        costing = contractor.costing_sheet_data
        for key in ["management_company_charges", "managementFee", "management_fee", "serviceCharge"]:
            if costing.get(key):
                try:
                    management_fee = float(costing[key])
                    break
                except (ValueError, TypeError):
                    pass

    # Accruals from costing sheet
    accrual_gratuity = 0
    accrual_airfare = 0
    accrual_annual_leave = 0
    if contractor.costing_sheet_data:
        costing = contractor.costing_sheet_data
        if costing.get("eosb") or costing.get("gratuity"):
            try:
                accrual_gratuity = float(costing.get("eosb") or costing.get("gratuity") or 0)
            except (ValueError, TypeError):
                pass
        if costing.get("airfare"):
            try:
                accrual_airfare = float(costing["airfare"])
            except (ValueError, TypeError):
                pass
        if costing.get("leave") or costing.get("annualLeave"):
            try:
                accrual_annual_leave = float(costing.get("leave") or costing.get("annualLeave") or 0)
            except (ValueError, TypeError):
                pass

    # Country for VAT
    country = contractor.onboarding_route or "UAE"

    return {
        "rate_type": rate_type,
        "currency": currency,
        "monthly_rate": monthly_rate,
        "day_rate": day_rate,
        "charge_rate_month": charge_rate_month,
        "charge_rate_day": charge_rate_day,
        "leave_allowance": leave_allowance,
        "third_party_name": third_party_name,
        "management_fee": management_fee,
        "accrual_gratuity": accrual_gratuity,
        "accrual_airfare": accrual_airfare,
        "accrual_annual_leave": accrual_annual_leave,
        "country": country,
        "client_name": contractor.client_name or "",
    }


def _get_total_leave_taken_this_year(contractor_id: str, year: int, db: Session) -> float:
    """Calculate total vacation days taken this year from all timesheets."""
    timesheets = db.query(Timesheet).filter(
        Timesheet.contractor_id == contractor_id,
        Timesheet.status == TimesheetStatus.APPROVED
    ).all()

    total_leave = 0
    for ts in timesheets:
        # Parse month to check if it's the same year
        try:
            ts_date = datetime.strptime(ts.month, "%B %Y")
            if ts_date.year == year:
                total_leave += ts.vacation_days or 0
        except:
            pass

    return total_leave


def _get_previous_month_timesheet(contractor_id: str, current_period: str, db: Session) -> Optional[Timesheet]:
    """Get the previous month's timesheet."""
    try:
        current_date = datetime.strptime(current_period, "%B %Y")
        if current_date.month == 1:
            prev_month = 12
            prev_year = current_date.year - 1
        else:
            prev_month = current_date.month - 1
            prev_year = current_date.year

        prev_period = datetime(prev_year, prev_month, 1).strftime("%B %Y")

        return db.query(Timesheet).filter(
            Timesheet.contractor_id == contractor_id,
            Timesheet.month == prev_period,
            Timesheet.status == TimesheetStatus.APPROVED
        ).first()
    except:
        return None


@router.get("/ready")
def get_timesheets_ready_for_payroll(
    db: Session = Depends(get_db)
):
    """Get approved timesheets that don't have payroll records yet."""
    timesheets = (
        db.query(Timesheet)
        .outerjoin(Payroll, Timesheet.id == Payroll.timesheet_id)
        .filter(Timesheet.status == TimesheetStatus.APPROVED)
        .filter(Payroll.id == None)
        .order_by(Timesheet.approved_date.desc())
        .all()
    )

    result = []
    for ts in timesheets:
        contractor = db.query(Contractor).filter(Contractor.id == ts.contractor_id).first()
        if not contractor:
            continue

        info = _get_contractor_full_info(contractor, db)
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        # Calculate estimated gross based on rate type
        estimated_gross = None
        if info["rate_type"] == "daily" and info["day_rate"]:
            estimated_gross = info["day_rate"] * (ts.work_days or 0)
        elif info["rate_type"] == "monthly" and info["monthly_rate"]:
            estimated_gross = info["monthly_rate"]

        result.append({
            "id": ts.id,
            "contractor_id": ts.contractor_id,
            "contractor_name": contractor_name,
            "contractor_email": contractor.email,
            "client_name": info["client_name"],
            "third_party_name": info["third_party_name"],
            "period": ts.month,
            "work_days": ts.work_days,
            "total_days": ts.total_days,
            "rate_type": info["rate_type"],
            "monthly_rate": info["monthly_rate"],
            "day_rate": info["day_rate"],
            "currency": info["currency"],
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
            "third_party_name": p.third_party_name,
            "period": p.period,
            "rate_type": p.rate_type.value if p.rate_type else "monthly",
            "days_worked": p.days_worked,
            "gross_pay": p.gross_pay,
            "net_salary": p.net_salary,
            "total_accruals": p.total_accruals,
            "management_fee": p.management_fee,
            "invoice_total": p.invoice_total,
            "vat_amount": p.vat_amount,
            "total_payable": p.total_payable,
            "currency": p.currency,
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
    expenses_reimbursement: float = 0,
    accrual_gosi: float = 0,
    accrual_salary_transfer: float = 0,
    accrual_admin_costs: float = 0,
    accrual_other: float = 0,
    db: Session = Depends(get_db)
):
    """
    Calculate payroll for a specific timesheet using the detailed formula.

    For Monthly Rate:
    - Prorata Day Rate = Monthly Rate / Total Calendar Days
    - Gross Pay = Monthly Rate
    - Net Salary = (Gross Pay / Total Calendar Days × Days Worked) - Leave Deductibles + Expenses

    For Daily Rate:
    - Gross Pay = Days Worked × Day Rate
    - Net Salary = Gross Pay + Expenses

    Invoice Total = Net Salary + Total Accruals + Management Fee
    VAT = Invoice Total × VAT Rate (15% Saudi, 5% UAE)
    Total Payable = Invoice Total + VAT
    """
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

    # Get all contractor info
    info = _get_contractor_full_info(contractor, db)

    # Determine rate type
    rate_type = RateType.MONTHLY if info["rate_type"] == "monthly" else RateType.DAILY

    # Get period info
    period = timesheet.month
    total_calendar_days = _get_calendar_days_in_month(period)

    # Days worked from timesheet
    days_worked = timesheet.work_days or 0

    # Get previous month data
    prev_timesheet = _get_previous_month_timesheet(contractor.id, period, db)
    previous_month_days_worked = prev_timesheet.work_days if prev_timesheet else 0

    # Parse year from period for leave calculations
    try:
        period_date = datetime.strptime(period, "%B %Y")
        current_year = period_date.year
    except:
        current_year = datetime.now().year

    # ========== BASIC CALCULATION ==========
    monthly_rate = info["monthly_rate"]
    day_rate = info["day_rate"]

    if rate_type == RateType.MONTHLY:
        if not monthly_rate:
            raise HTTPException(status_code=400, detail="Monthly rate not configured for this contractor")
        prorata_day_rate = monthly_rate / total_calendar_days if total_calendar_days > 0 else 0
        gross_pay = monthly_rate
    else:
        if not day_rate:
            raise HTTPException(status_code=400, detail="Day rate not configured for this contractor")
        prorata_day_rate = day_rate
        gross_pay = days_worked * day_rate

    # ========== LEAVE ADJUSTMENTS ==========
    leave_allowance = info["leave_allowance"]
    carry_over_leave = 0  # TODO: Calculate from previous year (max 5 days)
    total_leave_allowance = leave_allowance + carry_over_leave
    total_leave_taken = _get_total_leave_taken_this_year(contractor.id, current_year, db)
    leave_balance = total_leave_allowance - total_leave_taken

    # Leave deductibles only apply if balance is negative
    leave_deductibles = 0
    if leave_balance < 0 and rate_type == RateType.MONTHLY:
        leave_deductibles = prorata_day_rate * abs(leave_balance)

    # ========== NET SALARY CALCULATION ==========
    if rate_type == RateType.MONTHLY:
        # Net salary for monthly = (Gross pay / Total calendar days × Days worked) - leave deductibles + expenses
        net_salary = (gross_pay / total_calendar_days * days_worked) - leave_deductibles + expenses_reimbursement
    else:
        # Net salary for daily = Gross pay + Expenses
        net_salary = gross_pay + expenses_reimbursement

    # ========== 3RD PARTY ACCRUALS ==========
    # Some from CDS, some manually entered
    accrual_gratuity = info["accrual_gratuity"]
    accrual_airfare = info["accrual_airfare"]
    accrual_annual_leave = info["accrual_annual_leave"]

    total_accruals = (
        accrual_gosi +
        accrual_salary_transfer +
        accrual_admin_costs +
        accrual_gratuity +
        accrual_airfare +
        accrual_annual_leave +
        accrual_other
    )

    # ========== MANAGEMENT FEE ==========
    management_fee = info["management_fee"]

    # ========== INVOICE CALCULATION ==========
    invoice_total = net_salary + total_accruals + management_fee

    # VAT based on country
    vat_rate = _get_vat_rate(info["country"])
    vat_amount = invoice_total * vat_rate
    total_payable = invoice_total + vat_amount

    # ========== CREATE PAYROLL RECORD ==========
    payroll = Payroll(
        timesheet_id=timesheet_id,
        contractor_id=contractor.id,

        # Basic Info
        period=period,
        client_name=info["client_name"],
        third_party_name=info["third_party_name"],
        currency=info["currency"],
        rate_type=rate_type,
        country=info["country"],

        # Basic Calculation
        monthly_rate=monthly_rate,
        total_calendar_days=total_calendar_days,
        days_worked=days_worked,
        prorata_day_rate=prorata_day_rate,
        gross_pay=gross_pay,
        day_rate=day_rate,

        # Leave Adjustments
        leave_allowance=leave_allowance,
        carry_over_leave=carry_over_leave,
        total_leave_allowance=total_leave_allowance,
        total_leave_taken=total_leave_taken,
        leave_balance=leave_balance,
        previous_month_days_worked=previous_month_days_worked,
        leave_deductibles=leave_deductibles,

        # Expenses
        expenses_reimbursement=expenses_reimbursement,

        # Net Salary
        net_salary=net_salary,

        # Accruals
        accrual_gosi=accrual_gosi,
        accrual_salary_transfer=accrual_salary_transfer,
        accrual_admin_costs=accrual_admin_costs,
        accrual_gratuity=accrual_gratuity,
        accrual_airfare=accrual_airfare,
        accrual_annual_leave=accrual_annual_leave,
        accrual_other=accrual_other,
        total_accruals=total_accruals,

        # Management Fee
        management_fee=management_fee,

        # Invoice
        invoice_total=invoice_total,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total_payable=total_payable,

        # Legacy fields
        deductions=leave_deductibles,
        net_amount=net_salary,
        charge_rate_day=info["charge_rate_day"],
        invoice_amount=invoice_total,

        # Status
        status=PayrollStatus.CALCULATED,
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

        # Basic Info
        "period": payroll.period,
        "client_name": payroll.client_name,
        "third_party_name": payroll.third_party_name,
        "currency": payroll.currency,
        "rate_type": payroll.rate_type.value,
        "country": payroll.country,

        # Basic Calculation
        "monthly_rate": payroll.monthly_rate,
        "total_calendar_days": payroll.total_calendar_days,
        "days_worked": payroll.days_worked,
        "prorata_day_rate": round(payroll.prorata_day_rate, 2) if payroll.prorata_day_rate else None,
        "gross_pay": round(payroll.gross_pay, 2) if payroll.gross_pay else None,
        "day_rate": payroll.day_rate,

        # Leave
        "leave_allowance": payroll.leave_allowance,
        "carry_over_leave": payroll.carry_over_leave,
        "total_leave_allowance": payroll.total_leave_allowance,
        "total_leave_taken": payroll.total_leave_taken,
        "leave_balance": payroll.leave_balance,
        "leave_deductibles": round(payroll.leave_deductibles, 2),

        # Expenses
        "expenses_reimbursement": payroll.expenses_reimbursement,

        # Net Salary
        "net_salary": round(payroll.net_salary, 2) if payroll.net_salary else None,

        # Accruals
        "accrual_gosi": payroll.accrual_gosi,
        "accrual_salary_transfer": payroll.accrual_salary_transfer,
        "accrual_admin_costs": payroll.accrual_admin_costs,
        "accrual_gratuity": payroll.accrual_gratuity,
        "accrual_airfare": payroll.accrual_airfare,
        "accrual_annual_leave": payroll.accrual_annual_leave,
        "accrual_other": payroll.accrual_other,
        "total_accruals": round(payroll.total_accruals, 2),

        # Management Fee
        "management_fee": payroll.management_fee,

        # Invoice
        "invoice_total": round(payroll.invoice_total, 2) if payroll.invoice_total else None,
        "vat_rate": payroll.vat_rate,
        "vat_amount": round(payroll.vat_amount, 2),
        "total_payable": round(payroll.total_payable, 2) if payroll.total_payable else None,

        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
    }


@router.get("/{payroll_id}")
def get_payroll(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Get a single payroll record with all details."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    contractor_name = "Unknown"
    contractor_email = None

    if contractor:
        contractor_name = f"{contractor.first_name} {contractor.surname}"
        contractor_email = contractor.email

    return {
        "id": payroll.id,
        "timesheet_id": payroll.timesheet_id,
        "contractor_id": payroll.contractor_id,
        "contractor_name": contractor_name,
        "contractor_email": contractor_email,

        # Basic Info
        "period": payroll.period,
        "client_name": payroll.client_name,
        "third_party_name": payroll.third_party_name,
        "currency": payroll.currency,
        "rate_type": payroll.rate_type.value if payroll.rate_type else "monthly",
        "country": payroll.country,

        # Basic Calculation
        "monthly_rate": payroll.monthly_rate,
        "total_calendar_days": payroll.total_calendar_days,
        "days_worked": payroll.days_worked,
        "prorata_day_rate": payroll.prorata_day_rate,
        "gross_pay": payroll.gross_pay,
        "day_rate": payroll.day_rate,

        # Leave
        "leave_allowance": payroll.leave_allowance,
        "carry_over_leave": payroll.carry_over_leave,
        "total_leave_allowance": payroll.total_leave_allowance,
        "total_leave_taken": payroll.total_leave_taken,
        "leave_balance": payroll.leave_balance,
        "previous_month_days_worked": payroll.previous_month_days_worked,
        "leave_deductibles": payroll.leave_deductibles,

        # Expenses
        "expenses_reimbursement": payroll.expenses_reimbursement,

        # Net Salary
        "net_salary": payroll.net_salary,

        # Accruals
        "accrual_gosi": payroll.accrual_gosi,
        "accrual_salary_transfer": payroll.accrual_salary_transfer,
        "accrual_admin_costs": payroll.accrual_admin_costs,
        "accrual_gratuity": payroll.accrual_gratuity,
        "accrual_airfare": payroll.accrual_airfare,
        "accrual_annual_leave": payroll.accrual_annual_leave,
        "accrual_other": payroll.accrual_other,
        "total_accruals": payroll.total_accruals,

        # Management Fee
        "management_fee": payroll.management_fee,

        # Invoice
        "invoice_total": payroll.invoice_total,
        "vat_rate": payroll.vat_rate,
        "vat_amount": payroll.vat_amount,
        "total_payable": payroll.total_payable,

        # Status
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
    """Get detailed payroll calculation data formatted for display."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    contractor_name = f"{contractor.first_name} {contractor.surname}"

    return {
        # Header Info
        "period": payroll.period,
        "contractor_name": contractor_name,
        "client_name": payroll.client_name,
        "third_party_name": payroll.third_party_name,
        "currency": payroll.currency,
        "rate_type": payroll.rate_type.value if payroll.rate_type else "monthly",

        # Basic Calculation - Monthly
        "basic_monthly": {
            "monthly_rate": payroll.monthly_rate,
            "total_calendar_days": payroll.total_calendar_days,
            "days_worked": payroll.days_worked,
            "prorata_day_rate": payroll.prorata_day_rate,
            "gross_pay": payroll.gross_pay,
        },

        # Basic Calculation - Daily (if applicable)
        "basic_daily": {
            "day_rate": payroll.day_rate,
            "total_calendar_days": payroll.total_calendar_days,
            "days_worked": payroll.days_worked,
            "gross_pay": payroll.gross_pay if payroll.rate_type == RateType.DAILY else None,
        },

        # Adjustments
        "adjustments": {
            "leave_allowance": payroll.leave_allowance,
            "carry_over_leave": payroll.carry_over_leave,
            "total_leave_allowance": payroll.total_leave_allowance,
            "total_leave_taken": payroll.total_leave_taken,
            "leave_balance": payroll.leave_balance,
            "previous_month_days_worked": payroll.previous_month_days_worked,
            "leave_deductibles": payroll.leave_deductibles,
        },

        # Expenses
        "expenses": {
            "reimbursement": payroll.expenses_reimbursement,
        },

        # Net Salary
        "net_salary": {
            "monthly_formula": "(Gross Pay / Total Calendar Days × Days Worked) - Leave Deductibles + Expenses",
            "daily_formula": "Gross Pay + Expenses",
            "value": payroll.net_salary,
        },

        # 3rd Party Accruals
        "accruals": {
            "gosi": payroll.accrual_gosi,
            "salary_transfer": payroll.accrual_salary_transfer,
            "admin_costs": payroll.accrual_admin_costs,
            "gratuity": payroll.accrual_gratuity,
            "airfare": payroll.accrual_airfare,
            "annual_leave": payroll.accrual_annual_leave,
            "other": payroll.accrual_other,
            "total": payroll.total_accruals,
        },

        # Management Fee
        "management_fee": {
            "third_party": payroll.third_party_name,
            "value": payroll.management_fee,
        },

        # Invoice Total
        "invoice": {
            "invoice_total": payroll.invoice_total,
            "vat_rate": payroll.vat_rate,
            "vat_rate_percent": f"{int(payroll.vat_rate * 100)}%",
            "vat_amount": payroll.vat_amount,
            "total_payable": payroll.total_payable,
        },

        # Status
        "payroll_id": payroll.id,
        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
        "approved_at": payroll.approved_at,
        "paid_at": payroll.paid_at,
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
