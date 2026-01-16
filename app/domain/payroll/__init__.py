"""
Payroll domain module.

Contains business logic, value objects, and calculation strategies for payroll.
"""
# Re-export model enums
from app.models.payroll import PayrollStatus, RateType

# Import domain value objects
from app.domain.payroll.value_objects import (
    Money,
    PayrollCalculation,
    LeaveAdjustment,
    AccrualBreakdown,
    ContractorPayInfo,
    can_approve_payroll,
    can_mark_paid,
    normalize_rate_type,
)
from app.domain.payroll.calculations import (
    IPayrollCalculator,
    MonthlyRateCalculator,
    DailyRateCalculator,
    PayrollCalculatorFactory,
)
from app.domain.payroll.exceptions import (
    PayrollCalculationError,
    InvalidRateConfigurationError,
    TimesheetNotApprovedException,
    PayrollAlreadyExistsError,
    InvalidStatusTransitionError,
)

__all__ = [
    # Enums (from model)
    "PayrollStatus",
    "RateType",
    # Value Objects
    "Money",
    "PayrollCalculation",
    "LeaveAdjustment",
    "AccrualBreakdown",
    "ContractorPayInfo",
    # Helper functions
    "can_approve_payroll",
    "can_mark_paid",
    "normalize_rate_type",
    # Calculators
    "IPayrollCalculator",
    "MonthlyRateCalculator",
    "DailyRateCalculator",
    "PayrollCalculatorFactory",
    # Exceptions
    "PayrollCalculationError",
    "InvalidRateConfigurationError",
    "TimesheetNotApprovedException",
    "PayrollAlreadyExistsError",
    "InvalidStatusTransitionError",
]
