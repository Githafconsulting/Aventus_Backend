"""
Payroll domain value objects.

Immutable objects representing payroll concepts.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

# Import enums from model to avoid duplication
from app.models.payroll import PayrollStatus, RateType


# Helper functions for enum behavior
def can_approve_payroll(status: PayrollStatus) -> bool:
    """Check if a payroll status can transition to approved."""
    return status == PayrollStatus.CALCULATED


def can_mark_paid(status: PayrollStatus) -> bool:
    """Check if a payroll status can transition to paid."""
    return status == PayrollStatus.APPROVED


def normalize_rate_type(value: str) -> RateType:
    """
    Normalize rate type string to enum value.

    Handles "day" -> "daily" normalization.
    """
    value_lower = value.lower().strip()

    # Handle "day" -> "daily" normalization
    if value_lower == "day":
        return RateType.DAILY

    if value_lower == "monthly":
        return RateType.MONTHLY
    elif value_lower == "daily":
        return RateType.DAILY
    else:
        raise ValueError(f"Invalid rate type: {value}")


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts."""
    amount: Decimal
    currency: str

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter code (e.g., AED, USD)")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: float) -> "Money":
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def to_float(self) -> float:
        """Convert to float for database storage."""
        return float(self.amount)


@dataclass(frozen=True)
class LeaveAdjustment:
    """Leave balance and deductions calculation."""
    leave_allowance: float
    carry_over_leave: float
    total_leave_allowance: float
    total_leave_taken: float
    leave_balance: float
    leave_deductibles: Money
    previous_month_days_worked: Optional[float] = None

    @property
    def has_negative_balance(self) -> bool:
        """Check if contractor has taken more leave than allowed."""
        return self.leave_balance < 0


@dataclass(frozen=True)
class AccrualBreakdown:
    """Third-party accruals breakdown."""
    gosi: Money
    salary_transfer: Money
    admin_costs: Money
    gratuity: Money
    airfare: Money
    annual_leave: Money
    other: Money

    @property
    def total(self) -> Money:
        """Calculate total accruals."""
        return (
            self.gosi +
            self.salary_transfer +
            self.admin_costs +
            self.gratuity +
            self.airfare +
            self.annual_leave +
            self.other
        )


@dataclass(frozen=True)
class PayrollCalculation:
    """
    Complete payroll calculation result.

    This is the output of a calculation strategy.
    """
    # Basic calculation
    rate_type: RateType
    total_calendar_days: int
    days_worked: float
    prorata_day_rate: Optional[Money]
    gross_pay: Money

    # Monthly-specific
    monthly_rate: Optional[Money] = None

    # Daily-specific
    day_rate: Optional[Money] = None

    # Leave adjustments
    leave_adjustment: Optional[LeaveAdjustment] = None

    # Expenses
    expenses_reimbursement: Money = None

    # Net salary
    net_salary: Money = None

    # Accruals
    accruals: Optional[AccrualBreakdown] = None

    # Management fee
    management_fee: Money = None

    # Invoice
    invoice_total: Money = None
    vat_rate: Decimal = Decimal("0.05")
    vat_amount: Money = None
    total_payable: Money = None

    # Metadata
    period: str = ""
    client_name: str = ""
    third_party_name: Optional[str] = None
    country: str = "UAE"

    def __post_init__(self):
        """Validate calculation consistency."""
        # Ensure we have the right rate based on rate_type
        if self.rate_type == RateType.MONTHLY and self.monthly_rate is None:
            raise ValueError("Monthly rate required for MONTHLY rate type")
        if self.rate_type == RateType.DAILY and self.day_rate is None:
            raise ValueError("Day rate required for DAILY rate type")


@dataclass(frozen=True)
class ContractorPayInfo:
    """
    Contractor pay-related information extracted from various sources.

    This consolidates data from CDS form, contractor fields, and costing sheet.
    """
    # Rate information
    rate_type: RateType
    currency: str
    monthly_rate: Optional[float]
    day_rate: Optional[float]

    # Charge rates for invoicing
    charge_rate_month: Optional[float]
    charge_rate_day: Optional[float]

    # Leave information
    leave_allowance: float

    # Third party information
    third_party_name: str
    management_fee: float

    # Accruals from costing sheet
    accrual_gratuity: float
    accrual_airfare: float
    accrual_annual_leave: float

    # Country for VAT
    country: str
    client_name: str

    def validate(self) -> None:
        """Validate that required rates are configured."""
        if self.rate_type == RateType.MONTHLY and not self.monthly_rate:
            raise ValueError("Monthly rate not configured for MONTHLY rate type")
        if self.rate_type == RateType.DAILY and not self.day_rate:
            raise ValueError("Day rate not configured for DAILY rate type")
