"""
Base exception classes for the application.
All custom exceptions should inherit from BaseAppException.
"""
from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """
    Base exception class for all application exceptions.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code to return
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        result = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class NotFoundError(BaseAppException):
    """Base class for not found errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details,
        )


class ConflictError(BaseAppException):
    """Base class for conflict errors (duplicate resources, etc.)."""

    def __init__(
        self,
        message: str,
        error_code: str = "conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409,
            details=details,
        )


class BadRequestError(BaseAppException):
    """Base class for bad request errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "bad_request",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
        )
