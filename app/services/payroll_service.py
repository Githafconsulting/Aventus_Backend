"""
Payroll service - Business logic orchestration.

Handles payroll calculation, approval workflow, and data coordination.
Follows Single Responsibility and Dependency Inversion principles.
"""
from decimal import Decimal
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.payroll import (
    PayrollCalculation,
    PayrollCalculatorFactory,
    LeaveAdjustment,
    Money,
    RateType,
    PayrollStatus,
)
from app.domain.payroll.exceptions import (
    TimesheetNotApprovedException,
    PayrollAlreadyExistsError,
    InvalidStatusTransitionError,
    InvalidRateConfigurationError,
)
from app.models.payroll import Payroll
from app.models.timesheet import Timesheet, TimesheetStatus
from app.models.contractor import Contractor
from app.repositories.interfaces.payroll_repo import IPayrollRepository
from app.utils.contractor_data_extractor import ContractorDataExtractor
from app.services.expense_service import get_approved_expenses_total


class PayrollService:
    """
    Payroll business logic service.

    Orchestrates payroll calculations, status transitions, and data access.
    """

    def __init__(
        self,
        payroll_repo: IPayrollRepository,
        db: Session,  # TODO: Replace with repository pattern for Timesheet/Contractor
    ):
        """
        Initialize service with dependencies.

        Args:
            payroll_repo: Payroll repository for data access
            db: Database session (temporary until we have repos for all models)
        """
        self.payroll_repo = payroll_repo
        self.db = db

    async def get_timesheets_ready_for_payroll(self) -> List[dict]:
        """
        Get approved timesheets that don't have payroll records yet.

        Returns:
            List of timesheet data ready for payroll calculation
        """
        # Get approved timesheets without payroll
        timesheets = (
            self.db.query(Timesheet)
            .outerjoin(Payroll, Timesheet.id == Payroll.timesheet_id)
            .filter(Timesheet.status == TimesheetStatus.APPROVED)
            .filter(Payroll.id == None)
            .order_by(Timesheet.approved_date.desc())
            .all()
        )

        result = []
        for ts in timesheets:
            contractor = self.db.query(Contractor).filter(
                Contractor.id == ts.contractor_id
            ).first()

            if not contractor:
                continue

            # Extract contractor info
            extractor = ContractorDataExtractor(contractor)
            pay_info = extractor.extract_pay_info()

            contractor_name = f"{contractor.first_name} {contractor.surname}"

            # Calculate estimated gross based on rate type
            estimated_gross = None
            if pay_info.rate_type == RateType.DAILY and pay_info.day_rate:
                estimated_gross = pay_info.day_rate * (ts.work_days or 0)
            elif pay_info.rate_type == RateType.MONTHLY and pay_info.monthly_rate:
                estimated_gross = pay_info.monthly_rate

            result.append({
                "id": ts.id,
                "contractor_id": ts.contractor_id,
                "contractor_name": contractor_name,
                "contractor_email": contractor.email,
                "client_name": pay_info.client_name,
                "third_party_name": pay_info.third_party_name,
                "period": ts.month,
                "work_days": ts.work_days,
                "total_days": ts.total_days,
                "rate_type": pay_info.rate_type.value,
                "monthly_rate": pay_info.monthly_rate,
                "day_rate": pay_info.day_rate,
                "currency": pay_info.currency,
                "estimated_gross": estimated_gross,
                "submitted_date": ts.submitted_date,
                "approved_date": ts.approved_date,
            })

        return result

    async def calculate_payroll(
        self,
        timesheet_id: int,
        manual_accruals: Dict[str, float],
        expenses_reimbursement: float = 0,
    ) -> Payroll:
        """
        Calculate payroll for a timesheet.

        Args:
            timesheet_id: ID of the timesheet
            manual_accruals: Manually entered accruals (GOSI, salary transfer, etc.)
            expenses_reimbursement: Expense reimbursements

        Returns:
            Created Payroll record

        Raises:
            TimesheetNotApprovedException: If timesheet is not approved
            PayrollAlreadyExistsError: If payroll already exists for this timesheet
            InvalidRateConfigurationError: If contractor rates are not configured
        """
        # Check if timesheet exists and is approved
        timesheet = self.db.query(Timesheet).filter(
            Timesheet.id == timesheet_id
        ).first()

        if not timesheet:
            raise ValueError("Timesheet not found")

        if timesheet.status != TimesheetStatus.APPROVED:
            raise TimesheetNotApprovedException(
                f"Timesheet {timesheet_id} must be approved before payroll calculation"
            )

        # Check if payroll already exists
        if await self.payroll_repo.exists_for_timesheet(timesheet_id):
            raise PayrollAlreadyExistsError(
                f"Payroll already calculated for timesheet {timesheet_id}"
            )

        # Get contractor
        contractor = self.db.query(Contractor).filter(
            Contractor.id == timesheet.contractor_id
        ).first()

        if not contractor:
            raise ValueError("Contractor not found")

        # Extract contractor pay info
        extractor = ContractorDataExtractor(contractor)
        contractor_info = extractor.extract_pay_info()

        # Validate rates are configured
        contractor_info.validate()

        # Calculate leave adjustment
        leave_adjustment = await self._calculate_leave_adjustment(
            contractor=contractor,
            contractor_info=contractor_info,
            period=timesheet.month,
            timesheet_id=timesheet_id,
        )

        # Auto-sum approved expenses if not manually provided
        if expenses_reimbursement == 0:
            try:
                period_date = datetime.strptime(timesheet.month, "%B %Y")
                expenses_reimbursement = get_approved_expenses_total(
                    self.db, contractor.id, period_date.month, period_date.year
                )
            except Exception:
                pass

        # Get appropriate calculator
        calculator = PayrollCalculatorFactory.create(contractor_info.rate_type)

        # Calculate payroll
        calculation = calculator.calculate(
            contractor_info=contractor_info,
            days_worked=timesheet.work_days or 0,
            period=timesheet.month,
            leave_adjustment=leave_adjustment,
            manual_accruals=manual_accruals,
            expenses_reimbursement=expenses_reimbursement,
        )

        # Create payroll record
        payroll = await self._create_payroll_record(
            timesheet_id=timesheet_id,
            contractor_id=contractor.id,
            calculation=calculation,
        )

        return payroll

    async def get_payroll_by_id(self, payroll_id: int) -> Optional[Payroll]:
        """Get payroll record by ID."""
        return await self.payroll_repo.get(payroll_id)

    async def get_all_payroll_records(
        self, status_filter: Optional[str] = None
    ) -> List[Payroll]:
        """
        Get all payroll records with optional status filter.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of payroll records
        """
        if status_filter and status_filter != "all":
            try:
                status_enum = PayrollStatus(status_filter)
                return await self.payroll_repo.get_by_status(status_enum)
            except ValueError:
                pass  # Invalid status, return all

        # Return all records
        return self.db.query(Payroll).order_by(Payroll.created_at.desc()).all()

    async def get_payroll_stats(self) -> dict:
        """
        Get payroll statistics.

        Returns:
            Dictionary with counts by status
        """
        # Count ready timesheets
        ready_count = (
            self.db.query(Timesheet)
            .outerjoin(Payroll, Timesheet.id == Payroll.timesheet_id)
            .filter(Timesheet.status == TimesheetStatus.APPROVED)
            .filter(Payroll.id == None)
            .count()
        )

        # Count by status
        status_counts = await self.payroll_repo.count_by_status()

        return {
            "ready": ready_count,
            "calculated": status_counts.get("calculated", 0),
            "approved": status_counts.get("approved", 0),
            "paid": status_counts.get("paid", 0),
        }

    async def approve_payroll(self, payroll_id: int, approved_by: Optional[str] = None) -> Payroll:
        """
        Approve a payroll record.

        Args:
            payroll_id: ID of the payroll record
            approved_by: ID of user approving

        Returns:
            Updated Payroll record

        Raises:
            InvalidStatusTransitionError: If payroll is not in CALCULATED status
        """
        payroll = await self.payroll_repo.get(payroll_id)
        if not payroll:
            raise ValueError("Payroll record not found")

        if payroll.status != PayrollStatus.CALCULATED:
            raise InvalidStatusTransitionError(payroll.status.value, "approved")

        # Update directly in database
        payroll.status = PayrollStatus.APPROVED
        payroll.approved_at = datetime.utcnow()
        if approved_by:
            payroll.approved_by = approved_by

        self.db.commit()
        self.db.refresh(payroll)
        return payroll

    async def mark_paid(self, payroll_id: int) -> Payroll:
        """
        Mark a payroll record as paid.

        Args:
            payroll_id: ID of the payroll record

        Returns:
            Updated Payroll record

        Raises:
            InvalidStatusTransitionError: If payroll is not in APPROVED status
        """
        payroll = await self.payroll_repo.get(payroll_id)
        if not payroll:
            raise ValueError("Payroll record not found")

        if payroll.status != PayrollStatus.APPROVED:
            raise InvalidStatusTransitionError(payroll.status.value, "paid")

        # Update directly in database
        payroll.status = PayrollStatus.PAID
        payroll.paid_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(payroll)
        return payroll

    # Private helper methods

    async def _calculate_leave_adjustment(
        self,
        contractor: Contractor,
        contractor_info,
        period: str,
        timesheet_id: int,
    ) -> LeaveAdjustment:
        """Calculate leave balance and deductibles."""
        # Get current year from period
        try:
            period_date = datetime.strptime(period, "%B %Y")
            current_year = period_date.year
        except:
            current_year = datetime.now().year

        # Calculate total leave taken this year
        total_leave_taken = await self._get_total_leave_taken_this_year(
            contractor.id, current_year
        )

        # Get previous month data
        prev_timesheet = await self._get_previous_month_timesheet(
            contractor.id, period
        )
        previous_month_days_worked = prev_timesheet.work_days if prev_timesheet else None

        # Leave allowance and balance
        leave_allowance = contractor_info.leave_allowance
        carry_over_leave = 0  # TODO: Calculate from previous year (max 5 days)
        total_leave_allowance = leave_allowance + carry_over_leave
        leave_balance = total_leave_allowance - total_leave_taken

        # Calculate leave deductibles (only for monthly rate with negative balance)
        leave_deductibles = Money(Decimal("0"), contractor_info.currency)
        if leave_balance < 0 and contractor_info.rate_type == RateType.MONTHLY:
            # Deduct based on prorata day rate
            if contractor_info.monthly_rate:
                from calendar import monthrange
                period_date = datetime.strptime(period, "%B %Y")
                calendar_days = monthrange(period_date.year, period_date.month)[1]
                prorata_day_rate = contractor_info.monthly_rate / calendar_days
                leave_deductibles = Money(
                    Decimal(str(prorata_day_rate * abs(leave_balance))),
                    contractor_info.currency
                )

        return LeaveAdjustment(
            leave_allowance=leave_allowance,
            carry_over_leave=carry_over_leave,
            total_leave_allowance=total_leave_allowance,
            total_leave_taken=total_leave_taken,
            leave_balance=leave_balance,
            leave_deductibles=leave_deductibles,
            previous_month_days_worked=previous_month_days_worked,
        )

    async def _get_total_leave_taken_this_year(
        self, contractor_id: str, year: int
    ) -> float:
        """Calculate total vacation days taken this year from all timesheets."""
        timesheets = self.db.query(Timesheet).filter(
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

    async def _get_previous_month_timesheet(
        self, contractor_id: str, current_period: str
    ) -> Optional[Timesheet]:
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

            return self.db.query(Timesheet).filter(
                Timesheet.contractor_id == contractor_id,
                Timesheet.month == prev_period,
                Timesheet.status == TimesheetStatus.APPROVED
            ).first()
        except:
            return None

    async def _create_payroll_record(
        self,
        timesheet_id: int,
        contractor_id: str,
        calculation: PayrollCalculation,
    ) -> Payroll:
        """Create payroll database record from calculation."""
        payroll = Payroll(
            timesheet_id=timesheet_id,
            contractor_id=contractor_id,
            # Basic Info
            period=calculation.period,
            client_name=calculation.client_name,
            third_party_name=calculation.third_party_name,
            currency=calculation.gross_pay.currency,
            rate_type=calculation.rate_type,
            country=calculation.country,
            # Basic Calculation
            monthly_rate=calculation.monthly_rate.to_float() if calculation.monthly_rate else None,
            total_calendar_days=calculation.total_calendar_days,
            days_worked=calculation.days_worked,
            prorata_day_rate=calculation.prorata_day_rate.to_float() if calculation.prorata_day_rate else None,
            gross_pay=calculation.gross_pay.to_float(),
            day_rate=calculation.day_rate.to_float() if calculation.day_rate else None,
            # Leave Adjustments
            leave_allowance=calculation.leave_adjustment.leave_allowance if calculation.leave_adjustment else 30,
            carry_over_leave=calculation.leave_adjustment.carry_over_leave if calculation.leave_adjustment else 0,
            total_leave_allowance=calculation.leave_adjustment.total_leave_allowance if calculation.leave_adjustment else 30,
            total_leave_taken=calculation.leave_adjustment.total_leave_taken if calculation.leave_adjustment else 0,
            leave_balance=calculation.leave_adjustment.leave_balance if calculation.leave_adjustment else 30,
            previous_month_days_worked=calculation.leave_adjustment.previous_month_days_worked if calculation.leave_adjustment else None,
            leave_deductibles=calculation.leave_adjustment.leave_deductibles.to_float() if calculation.leave_adjustment else 0,
            # Expenses
            expenses_reimbursement=calculation.expenses_reimbursement.to_float() if calculation.expenses_reimbursement else 0,
            # Net Salary
            net_salary=calculation.net_salary.to_float() if calculation.net_salary else 0,
            # Accruals
            accrual_gosi=calculation.accruals.gosi.to_float() if calculation.accruals else 0,
            accrual_salary_transfer=calculation.accruals.salary_transfer.to_float() if calculation.accruals else 0,
            accrual_admin_costs=calculation.accruals.admin_costs.to_float() if calculation.accruals else 0,
            accrual_gratuity=calculation.accruals.gratuity.to_float() if calculation.accruals else 0,
            accrual_airfare=calculation.accruals.airfare.to_float() if calculation.accruals else 0,
            accrual_annual_leave=calculation.accruals.annual_leave.to_float() if calculation.accruals else 0,
            accrual_other=calculation.accruals.other.to_float() if calculation.accruals else 0,
            total_accruals=calculation.accruals.total.to_float() if calculation.accruals else 0,
            # Management Fee
            management_fee=calculation.management_fee.to_float() if calculation.management_fee else 0,
            # Invoice
            invoice_total=calculation.invoice_total.to_float() if calculation.invoice_total else 0,
            vat_rate=float(calculation.vat_rate),
            vat_amount=calculation.vat_amount.to_float() if calculation.vat_amount else 0,
            total_payable=calculation.total_payable.to_float() if calculation.total_payable else 0,
            # Legacy fields (for backward compatibility)
            deductions=calculation.leave_adjustment.leave_deductibles.to_float() if calculation.leave_adjustment else 0,
            net_amount=calculation.net_salary.to_float() if calculation.net_salary else 0,
            invoice_amount=calculation.invoice_total.to_float() if calculation.invoice_total else 0,
            # Status
            status=PayrollStatus.CALCULATED,
            calculated_at=datetime.utcnow(),
        )

        self.db.add(payroll)
        self.db.commit()
        self.db.refresh(payroll)

        return payroll
