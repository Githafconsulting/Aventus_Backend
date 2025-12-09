"""
Exceptions for external service failures.
"""
from typing import Optional, Dict, Any
from app.exceptions.base import BaseAppException


class ExternalServiceError(BaseAppException):
    """Base class for external service errors."""

    def __init__(
        self,
        message: str,
        service_name: str,
        error_code: str = "external_service_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service"] = service_name

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=502,
            details=details,
        )


class EmailServiceError(ExternalServiceError):
    """Raised when email sending fails."""

    def __init__(
        self,
        message: str = "Failed to send email",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            service_name="email",
            error_code="email_service_error",
            details=details,
        )


class StorageServiceError(ExternalServiceError):
    """Raised when file storage operations fail."""

    def __init__(
        self,
        message: str = "File storage operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            service_name="storage",
            error_code="storage_service_error",
            details=details,
        )


class PDFGenerationError(BaseAppException):
    """Raised when PDF generation fails."""

    def __init__(
        self,
        message: str = "Failed to generate PDF",
        document_type: Optional[str] = None,
    ):
        details = {}
        if document_type:
            details["document_type"] = document_type

        super().__init__(
            message=message,
            error_code="pdf_generation_error",
            status_code=500,
            details=details if details else None,
        )
