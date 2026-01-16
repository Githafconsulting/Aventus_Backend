"""
Payroll calculation strategies.

Each strategy encapsulates a different way to calculate payroll based on rate type.
Follows the Strategy Pattern and Open/Closed Principle.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from calendar import monthrange
from datetime import datetime

from app.domain.payroll.value_objects import (
    RateType,
    Money,
    PayrollCalculation,
    LeaveAdjustment,
    AccrualBreakdown,
    ContractorPayInfo,
)
from app.domain.payroll.exceptions import InvalidRateConfigurationError


class IPayrollCalculator(ABC):
    """
    Interface for payroll calculation strategies.

    Different calculators handle monthly vs daily rates.
    """

    @abstractmethod
    def calculate(
        self,
        contractor_info: ContractorPayInfo,
        days_worked: float,
        period: str,
        leave_adjustment: LeaveAdjustment,
        manual_accruals: dict,
        expenses_reimbursement: float = 0,
    ) -> PayrollCalculation:
        """
        Calculate payroll based on the strategy.

        Args:
            contractor_info: Contractor pay configuration
            days_worked: Number of days worked in period
            period: Pay period (e.g., "January 2025")
            leave_adjustment: Leave balance and deductions
            manual_accruals: Manually entered accruals (GOSI, etc.)
            expenses_reimbursement: Expense reimbursements

        Returns:
            Complete payroll calculation

        Raises:
            InvalidRateConfigurationError: If required rates are missing
        """
        pass


class MonthlyRateCalculator(IPayrollCalculator):
    """
    Calculate payroll for monthly-rate contractors.

    Formula:
    - Pro-rata Day Rate = Monthly Rate / Total Calendar Days
    - Gross Pay = Monthly Rate
    - Net Salary = (Gross Pay / Total Calendar Days × Days Worked) - Leave Deductibles + Expenses
    """

    def calculate(
        self,
        contractor_info: ContractorPayInfo,
        days_worked: float,
        period: str,
        leave_adjustment: LeaveAdjustment,
        manual_accruals: dict,
        expenses_reimbursement: float = 0,
    ) -> PayrollCalculation:
        """Calculate payroll for monthly rate."""
        # Validate monthly rate exists
        if not contractor_info.monthly_rate:
            raise InvalidRateConfigurationError(
                "Monthly rate not configured for this contractor"
            )

        # Create Money objects
        currency = contractor_info.currency
        monthly_rate = Money(Decimal(str(contractor_info.monthly_rate)), currency)
        expenses = Money(Decimal(str(expenses_reimbursement)), currency)

        # Calculate calendar days
        total_calendar_days = self._get_calendar_days(period)

        # Pro-rata day rate
        prorata_day_rate = Money(
            monthly_rate.amount / Decimal(str(total_calendar_days)),
            currency
        )

        # Gross pay is the monthly rate
        gross_pay = monthly_rate

        # Net salary calculation for monthly
        # (Gross / Calendar Days × Days Worked) - Leave Deductibles + Expenses
        net_salary = Money(
            (gross_pay.amount / Decimal(str(total_calendar_days))) * Decimal(str(days_worked)),
            currency
        ) - leave_adjustment.leave_deductibles + expenses

        # Build accruals
        accruals = self._build_accruals(contractor_info, manual_accruals, currency)

        # Management fee
        management_fee = Money(Decimal(str(contractor_info.management_fee)), currency)

        # Invoice calculation
        invoice_total = net_salary + accruals.total + management_fee

        # VAT
        vat_rate = self._get_vat_rate(contractor_info.country)
        vat_amount = invoice_total * float(vat_rate)

        # Total payable
        total_payable = invoice_total + vat_amount

        return PayrollCalculation(
            rate_type=RateType.MONTHLY,
            total_calendar_days=total_calendar_days,
            days_worked=days_worked,
            prorata_day_rate=prorata_day_rate,
            gross_pay=gross_pay,
            monthly_rate=monthly_rate,
            day_rate=None,
            leave_adjustment=leave_adjustment,
            expenses_reimbursement=expenses,
            net_salary=net_salary,
            accruals=accruals,
            management_fee=management_fee,
            invoice_total=invoice_total,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total_payable=total_payable,
            period=period,
            client_name=contractor_info.client_name,
            third_party_name=contractor_info.third_party_name,
            country=contractor_info.country,
        )

    def _get_calendar_days(self, period: str) -> int:
        """Get total calendar days in month from period string."""
        try:
            date = datetime.strptime(period, "%B %Y")
            return monthrange(date.year, date.month)[1]
        except:
            return 30  # Default fallback

    def _get_vat_rate(self, country: str) -> Decimal:
        """Get VAT rate based on country."""
        country_lower = (country or "").lower()
        if "saudi" in country_lower or "ksa" in country_lower:
            return Decimal("0.15")  # 15% for Saudi
        elif "uae" in country_lower or "emirates" in country_lower or "dubai" in country_lower:
            return Decimal("0.05")  # 5% for UAE
        return Decimal("0.05")  # Default to UAE

    def _build_accruals(
        self, contractor_info: ContractorPayInfo, manual_accruals: dict, currency: str
    ) -> AccrualBreakdown:
        """Build accrual breakdown from CDS data and manual inputs."""
        return AccrualBreakdown(
            gosi=Money(Decimal(str(manual_accruals.get("accrual_gosi", 0))), currency),
            salary_transfer=Money(Decimal(str(manual_accruals.get("accrual_salary_transfer", 0))), currency),
            admin_costs=Money(Decimal(str(manual_accruals.get("accrual_admin_costs", 0))), currency),
            gratuity=Money(Decimal(str(contractor_info.accrual_gratuity)), currency),
            airfare=Money(Decimal(str(contractor_info.accrual_airfare)), currency),
            annual_leave=Money(Decimal(str(contractor_info.accrual_annual_leave)), currency),
            other=Money(Decimal(str(manual_accruals.get("accrual_other", 0))), currency),
        )


class DailyRateCalculator(IPayrollCalculator):
    """
    Calculate payroll for daily-rate contractors.

    Formula:
    - Gross Pay = Days Worked × Day Rate
    - Net Salary = Gross Pay + Expenses
    """

    def calculate(
        self,
        contractor_info: ContractorPayInfo,
        days_worked: float,
        period: str,
        leave_adjustment: LeaveAdjustment,
        manual_accruals: dict,
        expenses_reimbursement: float = 0,
    ) -> PayrollCalculation:
        """Calculate payroll for daily rate."""
        # Validate day rate exists
        if not contractor_info.day_rate:
            raise InvalidRateConfigurationError(
                "Day rate not configured for this contractor"
            )

        # Create Money objects
        currency = contractor_info.currency
        day_rate = Money(Decimal(str(contractor_info.day_rate)), currency)
        expenses = Money(Decimal(str(expenses_reimbursement)), currency)

        # Calculate calendar days
        total_calendar_days = self._get_calendar_days(period)

        # Gross pay = days worked × day rate
        gross_pay = day_rate * days_worked

        # Pro-rata day rate is just the day rate for daily contractors
        prorata_day_rate = day_rate

        # Net salary for daily = Gross Pay + Expenses (no leave deductions)
        net_salary = gross_pay + expenses

        # Build accruals
        accruals = self._build_accruals(contractor_info, manual_accruals, currency)

        # Management fee
        management_fee = Money(Decimal(str(contractor_info.management_fee)), currency)

        # Invoice calculation
        invoice_total = net_salary + accruals.total + management_fee

        # VAT
        vat_rate = self._get_vat_rate(contractor_info.country)
        vat_amount = invoice_total * float(vat_rate)

        # Total payable
        total_payable = invoice_total + vat_amount

        return PayrollCalculation(
            rate_type=RateType.DAILY,
            total_calendar_days=total_calendar_days,
            days_worked=days_worked,
            prorata_day_rate=prorata_day_rate,
            gross_pay=gross_pay,
            monthly_rate=None,
            day_rate=day_rate,
            leave_adjustment=leave_adjustment,
            expenses_reimbursement=expenses,
            net_salary=net_salary,
            accruals=accruals,
            management_fee=management_fee,
            invoice_total=invoice_total,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total_payable=total_payable,
            period=period,
            client_name=contractor_info.client_name,
            third_party_name=contractor_info.third_party_name,
            country=contractor_info.country,
        )

    def _get_calendar_days(self, period: str) -> int:
        """Get total calendar days in month from period string."""
        try:
            date = datetime.strptime(period, "%B %Y")
            return monthrange(date.year, date.month)[1]
        except:
            return 30  # Default fallback

    def _get_vat_rate(self, country: str) -> Decimal:
        """Get VAT rate based on country."""
        country_lower = (country or "").lower()
        if "saudi" in country_lower or "ksa" in country_lower:
            return Decimal("0.15")  # 15% for Saudi
        elif "uae" in country_lower or "emirates" in country_lower or "dubai" in country_lower:
            return Decimal("0.05")  # 5% for UAE
        return Decimal("0.05")  # Default to UAE

    def _build_accruals(
        self, contractor_info: ContractorPayInfo, manual_accruals: dict, currency: str
    ) -> AccrualBreakdown:
        """Build accrual breakdown from CDS data and manual inputs."""
        return AccrualBreakdown(
            gosi=Money(Decimal(str(manual_accruals.get("accrual_gosi", 0))), currency),
            salary_transfer=Money(Decimal(str(manual_accruals.get("accrual_salary_transfer", 0))), currency),
            admin_costs=Money(Decimal(str(manual_accruals.get("accrual_admin_costs", 0))), currency),
            gratuity=Money(Decimal(str(contractor_info.accrual_gratuity)), currency),
            airfare=Money(Decimal(str(contractor_info.accrual_airfare)), currency),
            annual_leave=Money(Decimal(str(contractor_info.accrual_annual_leave)), currency),
            other=Money(Decimal(str(manual_accruals.get("accrual_other", 0))), currency),
        )


class PayrollCalculatorFactory:
    """
    Factory for creating appropriate payroll calculator based on rate type.

    Follows Factory Pattern.
    """

    @staticmethod
    def create(rate_type: RateType) -> IPayrollCalculator:
        """
        Create calculator for given rate type.

        Args:
            rate_type: Type of rate (monthly or daily)

        Returns:
            Appropriate calculator instance

        Raises:
            ValueError: If rate type is not supported
        """
        if rate_type == RateType.MONTHLY:
            return MonthlyRateCalculator()
        elif rate_type == RateType.DAILY:
            return DailyRateCalculator()
        else:
            raise ValueError(f"Unsupported rate type: {rate_type}")
