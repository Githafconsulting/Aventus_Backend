"""
Authentication and authorization exceptions.
"""
from typing import Optional, Dict, Any
from app.exceptions.base import BaseAppException


class AuthenticationError(BaseAppException):
    """
    Raised when authentication fails.
    Examples: invalid credentials, expired token, missing token.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "authentication_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class AuthorizationError(BaseAppException):
    """
    Raised when user lacks permission for an action.
    Examples: insufficient role, accessing another user's resource.
    """

    def __init__(
        self,
        message: str = "You don't have permission to perform this action",
        error_code: str = "authorization_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        token_type: str = "access",
    ):
        super().__init__(
            message=message,
            error_code="token_expired",
            details={"token_type": token_type},
        )


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid or malformed."""

    def __init__(
        self,
        message: str = "Invalid or malformed token",
    ):
        super().__init__(
            message=message,
            error_code="invalid_token",
        )
