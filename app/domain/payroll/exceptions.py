"""
Payroll domain exceptions.
"""


class PayrollDomainException(Exception):
    """Base exception for payroll domain errors."""
    pass


class PayrollCalculationError(PayrollDomainException):
    """Error during payroll calculation."""
    pass


class InvalidRateConfigurationError(PayrollCalculationError):
    """Contractor rate configuration is invalid or missing."""
    pass


class TimesheetNotApprovedException(PayrollCalculationError):
    """Timesheet must be approved before payroll calculation."""
    pass


class PayrollAlreadyExistsError(PayrollCalculationError):
    """Payroll already calculated for this timesheet."""
    pass


class InvalidStatusTransitionError(PayrollDomainException):
    """Invalid payroll status transition attempted."""

    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current} to {target}. "
            f"Valid workflow: CALCULATED → APPROVED → PAID"
        )


class NegativeLeaveBalanceError(PayrollCalculationError):
    """Contractor has negative leave balance requiring deduction."""

    def __init__(self, balance: float, deduction_amount: float):
        self.balance = balance
        self.deduction_amount = deduction_amount
        super().__init__(
            f"Negative leave balance: {balance} days. "
            f"Deduction of {deduction_amount} will be applied."
        )
