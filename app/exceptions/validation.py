"""
Validation exceptions.
"""
from typing import Optional, Dict, Any, List
from app.exceptions.base import BaseAppException


class ValidationError(BaseAppException):
    """
    Raised when input validation fails.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "validation_error",
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[Dict[str, str]]] = None,
    ):
        if field_errors:
            details = details or {}
            details["field_errors"] = field_errors

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
        )


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field_name: str):
        super().__init__(
            message=f"Missing required field: {field_name}",
            error_code="missing_field",
            details={"field": field_name},
        )


class InvalidFieldError(ValidationError):
    """Raised when a field value is invalid."""

    def __init__(self, field_name: str, reason: str):
        super().__init__(
            message=f"Invalid value for field '{field_name}': {reason}",
            error_code="invalid_field",
            details={"field": field_name, "reason": reason},
        )
