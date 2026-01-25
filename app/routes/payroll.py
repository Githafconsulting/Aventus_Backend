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


# =============================================================================
# HELPER FUNCTIONS - DRY Principle
# =============================================================================

def _get_float_value(primary_value, fallback_dict: Optional[dict], fallback_key: str, default: float = 0) -> Optional[float]:
    """
    Extract a float value from primary source or fallback dictionary.
    Reduces repetitive try/except patterns throughout the codebase.
    """
    # Try primary value first
    if primary_value is not None:
        try:
            return float(primary_value)
        except (ValueError, TypeError):
            pass

    # Try fallback dictionary
    if fallback_dict and fallback_dict.get(fallback_key):
        try:
            return float(fallback_dict[fallback_key])
        except (ValueError, TypeError):
            pass

    return default if default is not None else None


def _get_contractor_name(contractor: Optional[Contractor]) -> str:
    """Get formatted contractor name or 'Unknown' if not available."""
    if contractor:
        return f"{contractor.first_name} {contractor.surname}"
    return "Unknown"


def _calculate_total_accruals(
    gosi: float = 0,
    salary_transfer: float = 0,
    admin_costs: float = 0,
    gratuity: float = 0,
    airfare: float = 0,
    annual_leave: float = 0,
    other: float = 0
) -> float:
    """Calculate total accruals from individual components."""
    return (
        (gosi or 0) +
        (salary_transfer or 0) +
        (admin_costs or 0) +
        (gratuity or 0) +
        (airfare or 0) +
        (annual_leave or 0) +
        (other or 0)
    )


def _format_payroll_response(payroll: Payroll, contractor: Contractor) -> dict:
    """
    Format payroll record for API response.
    Single source of truth for payroll response structure.
    """
    contractor_name = _get_contractor_name(contractor)

    response = {
        "id": payroll.id,
        "timesheet_id": payroll.timesheet_id,
        "contractor_id": payroll.contractor_id,
        "contractor_name": contractor_name,
        "contractor_email": contractor.email if contractor else None,

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
        "prorata_day_rate": round(payroll.prorata_day_rate, 2) if payroll.prorata_day_rate else None,
        "gross_pay": round(payroll.gross_pay, 2) if payroll.gross_pay else None,
        "day_rate": payroll.day_rate,

        # Leave
        "leave_allowance": payroll.leave_allowance,
        "carry_over_leave": payroll.carry_over_leave,
        "total_leave_allowance": payroll.total_leave_allowance,
        "total_leave_taken": payroll.total_leave_taken,
        "leave_balance": payroll.leave_balance,
        "previous_month_days_worked": payroll.previous_month_days_worked,
        "leave_deductibles": round(payroll.leave_deductibles, 2) if payroll.leave_deductibles else 0,

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
        "total_accruals": round(payroll.total_accruals, 2) if payroll.total_accruals else 0,

        # Management Fee
        "management_fee": payroll.management_fee,

        # Invoice
        "invoice_total": round(payroll.invoice_total, 2) if payroll.invoice_total else None,
        "vat_rate": payroll.vat_rate,
        "vat_amount": round(payroll.vat_amount, 2) if payroll.vat_amount else 0,
        "total_payable": round(payroll.total_payable, 2) if payroll.total_payable else None,

        # Status
        "status": payroll.status.value,
        "calculated_at": payroll.calculated_at,
        "approved_at": payroll.approved_at,
        "paid_at": payroll.paid_at,
    }

    return response


def _get_calendar_days_in_month(period: str) -> int:
    """Get total calendar days in a month from period string like 'November 2024'."""
    try:
        date = datetime.strptime(period, "%B %Y")
        return monthrange(date.year, date.month)[1]
    except (ValueError, AttributeError):
        return 30  # Default fallback


def _build_email_table_html(rows: list[tuple[str, str]], highlight_last: bool = True) -> str:
    """
    Build HTML table for email body.
    Each row is a tuple of (label, value).
    """
    html_rows = []
    for i, (label, value) in enumerate(rows):
        is_last = i == len(rows) - 1
        style = 'style="background-color: #f9f9f9;"' if highlight_last and is_last else ''
        value_html = f"<strong>{value}</strong>" if highlight_last and is_last else value
        html_rows.append(f"""
                    <tr {style}>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{label}:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{value_html}</td>
                    </tr>""")
    return "".join(html_rows)


def _send_invoice_to_client(
    contractor: Contractor,
    contractor_name: str,
    payroll: Payroll,
    invoice_bytes: bytes
) -> bool:
    """Send invoice email to client. Returns True if successful."""
    if not contractor.client_email:
        return False

    try:
        from app.utils.email import send_email_with_attachments

        table_rows = [
            ("Contractor", contractor_name),
            ("Period", payroll.period),
            ("Invoice Total", f"{payroll.currency} {payroll.invoice_total:,.2f}"),
            (f"VAT ({int(payroll.vat_rate * 100)}%)", f"{payroll.currency} {payroll.vat_amount:,.2f}"),
            ("Total Payable", f"{payroll.currency} {payroll.total_payable:,.2f}"),
        ]

        client_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #FF6B00;">Invoice for {contractor_name}</h2>
                <p>Dear {contractor.client_name or 'Client'},</p>
                <p>Please find attached the invoice for {contractor_name} for the period of {payroll.period}.</p>
                <table style="margin: 20px 0; border-collapse: collapse;">
                    {_build_email_table_html(table_rows)}
                </table>
                <p>Please review the attached invoice and process payment at your earliest convenience.</p>
                <p>Best regards,<br>Aventus Consultants</p>
            </body>
            </html>
            """

        send_email_with_attachments(
            to_email=contractor.client_email,
            subject=f"Invoice - {contractor_name} - {payroll.period}",
            body=client_body,
            attachments=[{
                "filename": f"Invoice_{contractor_name.replace(' ', '_')}_{payroll.period.replace(' ', '_')}.pdf",
                "content": invoice_bytes,
                "content_type": "application/pdf"
            }]
        )
        print(f"[INFO] Invoice email sent to client: {contractor.client_email}")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to send invoice email to client: {e}")
        return False


def _send_payslip_to_contractor(
    contractor: Contractor,
    contractor_name: str,
    payroll: Payroll,
    payslip_bytes: bytes
) -> bool:
    """Send payslip email to contractor. Returns True if successful."""
    if not contractor.email:
        return False

    try:
        from app.utils.email import send_email_with_attachments

        table_rows = [
            ("Period", payroll.period),
            ("Days Worked", str(payroll.days_worked)),
            ("Gross Pay", f"{payroll.currency} {payroll.gross_pay:,.2f}"),
            ("Net Salary", f"{payroll.currency} {payroll.net_salary:,.2f}"),
        ]

        contractor_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #FF6B00;">Your Payslip for {payroll.period}</h2>
                <p>Dear {contractor.first_name},</p>
                <p>Please find attached your payslip for the period of {payroll.period}.</p>
                <table style="margin: 20px 0; border-collapse: collapse;">
                    {_build_email_table_html(table_rows)}
                </table>
                <p>If you have any questions about your payslip, please contact us.</p>
                <p>Best regards,<br>Aventus Consultants</p>
            </body>
            </html>
            """

        send_email_with_attachments(
            to_email=contractor.email,
            subject=f"Payslip - {payroll.period}",
            body=contractor_body,
            attachments=[{
                "filename": f"Payslip_{contractor_name.replace(' ', '_')}_{payroll.period.replace(' ', '_')}.pdf",
                "content": payslip_bytes,
                "content_type": "application/pdf"
            }]
        )
        print(f"[INFO] Payslip email sent to contractor: {contractor.email}")
        return True
    except Exception as e:
        print(f"[WARNING] Failed to send payslip email to contractor: {e}")
        return False


def _get_vat_rate(country: str) -> float:
    """Get VAT rate based on country."""
    country_lower = (country or "").lower()
    if "saudi" in country_lower or "ksa" in country_lower:
        return 0.15  # 15% for Saudi
    elif "uae" in country_lower or "emirates" in country_lower or "dubai" in country_lower:
        return 0.05  # 5% for UAE
    return 0.05  # Default to UAE


def _get_contractor_full_info(contractor: Contractor, db: Session) -> dict:
    """Extract all pay-related information from contractor using DRY helper functions."""
    cds = contractor.cds_form_data or {}
    costing = contractor.costing_sheet_data or {}

    # Rate type - normalize "day" -> "daily"
    rate_type = (cds.get("rateType") or contractor.rate_type or "monthly").lower()
    if rate_type == "day":
        rate_type = "daily"

    # Currency
    currency = cds.get("currency") or contractor.currency or "AED"

    # Rates - using DRY helper
    monthly_rate = _get_float_value(contractor.gross_salary, cds, "grossSalary", 0)
    day_rate = _get_float_value(contractor.day_rate, cds, "dayRate", None)
    charge_rate_month = _get_float_value(contractor.charge_rate_month, cds, "chargeRateMonth", 0)
    charge_rate_day = _get_float_value(contractor.charge_rate_day, cds, "chargeRateDay", None)

    # Leave allowance - check multiple sources
    leave_allowance = _get_float_value(contractor.leave_allowance, cds, "leaveAllowance", None)
    if leave_allowance is None:
        leave_allowance = _get_float_value(contractor.vacation_days, None, "", 30)

    # Management fee - check multiple keys in costing sheet
    management_fee = 0
    for key in ["management_company_charges", "managementFee", "management_fee", "serviceCharge"]:
        fee = _get_float_value(None, costing, key, None)
        if fee is not None and fee > 0:
            management_fee = fee
            break

    # Accruals from costing sheet - using DRY helper
    accrual_gratuity = _get_float_value(None, costing, "eosb", None) or _get_float_value(None, costing, "gratuity", 0)
    accrual_airfare = _get_float_value(None, costing, "airfare", 0)
    accrual_annual_leave = _get_float_value(None, costing, "leave", None) or _get_float_value(None, costing, "annualLeave", 0)

    return {
        "rate_type": rate_type,
        "currency": currency,
        "monthly_rate": monthly_rate,
        "day_rate": day_rate,
        "charge_rate_month": charge_rate_month,
        "charge_rate_day": charge_rate_day,
        "leave_allowance": leave_allowance,
        "third_party_name": contractor.company_name or "",
        "management_fee": management_fee,
        "accrual_gratuity": accrual_gratuity,
        "accrual_airfare": accrual_airfare,
        "accrual_annual_leave": accrual_annual_leave,
        "country": contractor.onboarding_route or "UAE",
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
        except (ValueError, AttributeError):
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
    except (ValueError, AttributeError):
        return None


def auto_calculate_payroll(timesheet_id: int, db: Session) -> Optional[int]:
    """
    Auto-calculate payroll for a timesheet. Called when timesheet is approved.
    Returns payroll ID if successful, None if failed.
    """
    # Check if timesheet exists
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        return None

    # Check if payroll already exists
    existing = db.query(Payroll).filter(Payroll.timesheet_id == timesheet_id).first()
    if existing:
        return existing.id  # Already calculated

    # Get contractor
    contractor = db.query(Contractor).filter(Contractor.id == timesheet.contractor_id).first()
    if not contractor:
        return None

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
    except (ValueError, AttributeError):
        current_year = datetime.now().year

    # Basic calculation
    monthly_rate = info["monthly_rate"]
    day_rate = info["day_rate"]

    if rate_type == RateType.MONTHLY:
        if not monthly_rate:
            return None
        prorata_day_rate = monthly_rate / total_calendar_days if total_calendar_days > 0 else 0
        gross_pay = monthly_rate
    else:
        if not day_rate:
            return None
        prorata_day_rate = day_rate
        gross_pay = days_worked * day_rate

    # Leave calculations (using defaults - 0 for auto-calculation)
    sick_days_used = timesheet.sick_days or 0
    vacation_days_used = timesheet.vacation_days or 0
    unpaid_leave_days = timesheet.unpaid_days or 0

    # Calculate leave balance (positive means has available leave)
    leave_allowance = info.get("leave_allowance", 0) or 0
    leave_taken = sick_days_used + vacation_days_used
    leave_balance = leave_allowance - leave_taken

    sick_leave_deductible = 0
    vacation_leave_deductible = 0
    # Only deduct unpaid leave for monthly contractors
    unpaid_leave_deductible = unpaid_leave_days * prorata_day_rate if rate_type == RateType.MONTHLY else 0
    total_leave_deductibles = sick_leave_deductible + vacation_leave_deductible + unpaid_leave_deductible

    # Net salary calculation
    expenses_reimbursement = 0  # Default to 0 for auto-calculation
    if rate_type == RateType.MONTHLY:
        # For monthly rate: if leave balance is positive (has available leave), pay full salary
        # Only deduct for unpaid leave days
        net_salary = gross_pay - unpaid_leave_deductible + expenses_reimbursement
    else:
        # For daily rate: pay based on days worked
        net_salary = gross_pay + expenses_reimbursement

    # Accruals (default to 0)
    accrual_gosi = 0
    accrual_salary_transfer = 0
    accrual_admin_costs = 0
    accrual_other = 0
    total_accruals = accrual_gosi + accrual_salary_transfer + accrual_admin_costs + accrual_other

    # Management fee
    management_fee = info["management_fee"]
    invoice_subtotal = net_salary + total_accruals + management_fee

    # VAT calculation
    vat_rate = _get_vat_rate(info["country"])
    vat_amount = invoice_subtotal * vat_rate
    total_invoice = invoice_subtotal + vat_amount

    # Create payroll record
    payroll = Payroll(
        timesheet_id=timesheet_id,
        contractor_id=contractor.id,
        period=period,
        rate_type=rate_type,
        currency=info["currency"],
        monthly_rate=monthly_rate,
        day_rate=day_rate,
        prorata_day_rate=prorata_day_rate,
        total_calendar_days=total_calendar_days,
        days_worked=days_worked,
        previous_month_days_worked=previous_month_days_worked,
        gross_pay=gross_pay,
        sick_days_used=sick_days_used,
        sick_leave_deductible=sick_leave_deductible,
        vacation_days_used=vacation_days_used,
        vacation_leave_deductible=vacation_leave_deductible,
        unpaid_leave_days=unpaid_leave_days,
        unpaid_leave_deductible=unpaid_leave_deductible,
        total_leave_deductibles=total_leave_deductibles,
        expenses_reimbursement=expenses_reimbursement,
        net_salary=net_salary,
        accrual_gosi=accrual_gosi,
        accrual_salary_transfer=accrual_salary_transfer,
        accrual_admin_costs=accrual_admin_costs,
        accrual_other=accrual_other,
        total_accruals=total_accruals,
        management_fee=management_fee,
        invoice_subtotal=invoice_subtotal,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total_invoice=total_invoice,
        status=PayrollStatus.CALCULATED,
        calculated_at=datetime.utcnow(),
    )

    db.add(payroll)
    db.commit()
    db.refresh(payroll)

    return payroll.id


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
        contractor_name = _get_contractor_name(contractor)

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
            contractor_name = _get_contractor_name(contractor)
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
    except (ValueError, AttributeError):
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
        # For monthly rate: if leave balance is positive (has available leave), pay full salary
        # Only deduct for unpaid leave (leave_deductibles calculated above when balance is negative)
        net_salary = gross_pay - leave_deductibles + expenses_reimbursement
    else:
        # Net salary for daily = Gross pay + Expenses
        net_salary = gross_pay + expenses_reimbursement

    # ========== 3RD PARTY ACCRUALS ==========
    # Some from CDS, some manually entered
    accrual_gratuity = info["accrual_gratuity"]
    accrual_airfare = info["accrual_airfare"]
    accrual_annual_leave = info["accrual_annual_leave"]

    total_accruals = _calculate_total_accruals(
        gosi=accrual_gosi,
        salary_transfer=accrual_salary_transfer,
        admin_costs=accrual_admin_costs,
        gratuity=accrual_gratuity,
        airfare=accrual_airfare,
        annual_leave=accrual_annual_leave,
        other=accrual_other
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

    # Use DRY helper for consistent response formatting
    return _format_payroll_response(payroll, contractor)


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

    # Use DRY helper for consistent response formatting
    return _format_payroll_response(payroll, contractor)


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

    contractor_name = _get_contractor_name(contractor)

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


@router.put("/{payroll_id}/update")
def update_payroll(
    payroll_id: int,
    expenses_reimbursement: Optional[float] = None,
    accrual_gosi: Optional[float] = None,
    accrual_salary_transfer: Optional[float] = None,
    accrual_admin_costs: Optional[float] = None,
    accrual_gratuity: Optional[float] = None,
    accrual_airfare: Optional[float] = None,
    accrual_annual_leave: Optional[float] = None,
    accrual_other: Optional[float] = None,
    management_fee: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update editable fields of a payroll record."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    if payroll.status != PayrollStatus.CALCULATED:
        raise HTTPException(status_code=400, detail="Can only edit payroll in CALCULATED status")

    # Update fields if provided
    if expenses_reimbursement is not None:
        payroll.expenses_reimbursement = expenses_reimbursement
    if accrual_gosi is not None:
        payroll.accrual_gosi = accrual_gosi
    if accrual_salary_transfer is not None:
        payroll.accrual_salary_transfer = accrual_salary_transfer
    if accrual_admin_costs is not None:
        payroll.accrual_admin_costs = accrual_admin_costs
    if accrual_gratuity is not None:
        payroll.accrual_gratuity = accrual_gratuity
    if accrual_airfare is not None:
        payroll.accrual_airfare = accrual_airfare
    if accrual_annual_leave is not None:
        payroll.accrual_annual_leave = accrual_annual_leave
    if accrual_other is not None:
        payroll.accrual_other = accrual_other
    if management_fee is not None:
        payroll.management_fee = management_fee

    # Recalculate totals using DRY helper
    payroll.total_accruals = _calculate_total_accruals(
        gosi=payroll.accrual_gosi,
        salary_transfer=payroll.accrual_salary_transfer,
        admin_costs=payroll.accrual_admin_costs,
        gratuity=payroll.accrual_gratuity,
        airfare=payroll.accrual_airfare,
        annual_leave=payroll.accrual_annual_leave,
        other=payroll.accrual_other
    )

    # Recalculate net salary if expenses changed
    rate_type = payroll.rate_type
    if rate_type == RateType.MONTHLY:
        payroll.net_salary = payroll.gross_pay - (payroll.leave_deductibles or 0) + (payroll.expenses_reimbursement or 0)
    else:
        payroll.net_salary = payroll.gross_pay + (payroll.expenses_reimbursement or 0)

    # Recalculate invoice
    payroll.invoice_total = payroll.net_salary + payroll.total_accruals + (payroll.management_fee or 0)
    payroll.vat_amount = payroll.invoice_total * payroll.vat_rate
    payroll.total_payable = payroll.invoice_total + payroll.vat_amount

    db.commit()
    db.refresh(payroll)

    return {"message": "Payroll updated successfully", "id": payroll.id}


@router.put("/{payroll_id}/approve")
def approve_payroll(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """
    Approve a payroll record. This will:
    1. Email the invoice to the client
    2. Generate the contractor payslip
    3. Mark the payroll as approved
    """
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    if payroll.status != PayrollStatus.CALCULATED:
        raise HTTPException(status_code=400, detail="Payroll must be in CALCULATED status to approve")

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    contractor_name = _get_contractor_name(contractor)

    # Generate PDFs
    from app.utils.payroll_pdf import generate_payslip_pdf, generate_invoice_pdf

    payslip_buffer = generate_payslip_pdf(payroll=payroll, contractor=contractor)
    payslip_bytes = payslip_buffer.getvalue()

    invoice_buffer = generate_invoice_pdf(payroll=payroll, contractor=contractor)
    invoice_bytes = invoice_buffer.getvalue()

    # Send emails
    _send_invoice_to_client(contractor, contractor_name, payroll, invoice_bytes)
    _send_payslip_to_contractor(contractor, contractor_name, payroll, payslip_bytes)

    payroll.status = PayrollStatus.APPROVED
    payroll.approved_at = datetime.utcnow()
    db.commit()

    return {"message": "Payroll approved. Invoice sent to client, payslip sent to contractor.", "status": payroll.status.value}


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


@router.delete("/{payroll_id}")
def delete_payroll(
    payroll_id: int,
    db: Session = Depends(get_db)
):
    """Delete a payroll record."""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    db.delete(payroll)
    db.commit()

    return {"message": "Payroll deleted successfully"}


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

    contractor_name = _get_contractor_name(contractor)

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

    contractor_name = _get_contractor_name(contractor)

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
