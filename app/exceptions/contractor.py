"""
Contractor-specific exceptions.
"""
from typing import Optional, Dict, Any
from app.exceptions.base import NotFoundError, BadRequestError, BaseAppException


class ContractorNotFoundError(NotFoundError):
    """Raised when a contractor is not found."""

    def __init__(
        self,
        message: str = "Contractor not found",
        contractor_id: Optional[int] = None,
    ):
        details = {}
        if contractor_id:
            details["contractor_id"] = contractor_id

        super().__init__(
            message=message,
            error_code="contractor_not_found",
            details=details if details else None,
        )


class InvalidStatusTransitionError(BadRequestError):
    """Raised when an invalid status transition is attempted."""

    def __init__(
        self,
        message: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
    ):
        details = {}
        if from_status:
            details["from_status"] = from_status
        if to_status:
            details["to_status"] = to_status

        super().__init__(
            message=message,
            error_code="invalid_status_transition",
            details=details if details else None,
        )


class ContractorAlreadyExistsError(BaseAppException):
    """Raised when trying to create a contractor that already exists."""

    def __init__(self, email: str):
        super().__init__(
            message=f"Contractor with email '{email}' already exists",
            error_code="contractor_already_exists",
            status_code=409,
            details={"email": email},
        )


class DocumentUploadTokenExpiredError(BadRequestError):
    """Raised when document upload token has expired."""

    def __init__(self):
        super().__init__(
            message="Document upload token has expired",
            error_code="upload_token_expired",
        )


class ContractTokenExpiredError(BadRequestError):
    """Raised when contract signing token has expired."""

    def __init__(self):
        super().__init__(
            message="Contract signing token has expired",
            error_code="contract_token_expired",
        )
