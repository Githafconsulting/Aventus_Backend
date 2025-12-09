"""
Token value object for secure token generation and validation.
Used for document uploads, contract signing, password reset, etc.
"""
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
from app.exceptions.auth import TokenExpiredError


class TokenType(Enum):
    """
    Token types with their default expiry hours.
    """
    CONTRACT = ("contract_token", 72)           # 3 days
    DOCUMENT_UPLOAD = ("upload_token", 168)     # 7 days
    COHF = ("cohf_token", 72)                   # 3 days
    WORK_ORDER = ("work_order_token", 168)      # 7 days
    TIMESHEET = ("timesheet_token", 168)        # 7 days
    PASSWORD_RESET = ("reset_token", 24)        # 1 day
    QUOTE_SHEET = ("quote_sheet_token", 168)    # 7 days

    def __init__(self, field_name: str, default_hours: int):
        self.field_name = field_name
        self.default_hours = default_hours


@dataclass(frozen=True)
class Token:
    """
    Immutable token value object.

    Encapsulates token generation, validation, and expiry logic.
    Use Token.generate() to create new tokens.

    Attributes:
        value: The token string (URL-safe, 32 characters)
        expiry: When the token expires
        token_type: Optional type for context
    """
    value: str
    expiry: datetime
    token_type: Optional[TokenType] = None

    @classmethod
    def generate(
        cls,
        hours: Optional[int] = None,
        token_type: Optional[TokenType] = None,
    ) -> "Token":
        """
        Generate a new secure token.

        Args:
            hours: Hours until expiry (uses token_type default if not provided)
            token_type: Type of token being generated

        Returns:
            New Token instance

        Example:
            token = Token.generate(token_type=TokenType.CONTRACT)
            token = Token.generate(hours=24)
        """
        if hours is None and token_type:
            hours = token_type.default_hours
        elif hours is None:
            hours = 72  # Default 3 days

        value = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=hours)

        return cls(value=value, expiry=expiry, token_type=token_type)

    @classmethod
    def from_existing(
        cls,
        value: str,
        expiry: datetime,
        token_type: Optional[TokenType] = None,
    ) -> "Token":
        """
        Create a Token instance from existing values.
        Used when loading from database.

        Args:
            value: Existing token string
            expiry: Existing expiry datetime
            token_type: Optional token type

        Returns:
            Token instance
        """
        return cls(value=value, expiry=expiry, token_type=token_type)

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid (not expired)."""
        return datetime.utcnow() < self.expiry

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return not self.is_valid

    @property
    def hours_remaining(self) -> float:
        """Get hours remaining until expiry."""
        if self.is_expired:
            return 0.0
        delta = self.expiry - datetime.utcnow()
        return max(0.0, delta.total_seconds() / 3600)

    @property
    def expiry_formatted(self) -> str:
        """Get formatted expiry date string."""
        return self.expiry.strftime("%B %d, %Y at %I:%M %p")

    def validate(self) -> None:
        """
        Validate the token is not expired.

        Raises:
            TokenExpiredError: If token has expired
        """
        if self.is_expired:
            token_name = self.token_type.field_name if self.token_type else "Token"
            raise TokenExpiredError(
                message=f"{token_name} has expired",
                token_type=self.token_type.field_name if self.token_type else "unknown",
            )

    def __str__(self) -> str:
        """String representation (masked for security)."""
        return f"{self.value[:8]}...{self.value[-4:]}"


def generate_token_pair(
    token_type: TokenType,
    hours: Optional[int] = None,
) -> Tuple[str, datetime]:
    """
    Convenience function to generate token value and expiry.
    Returns tuple for easy database assignment.

    Args:
        token_type: Type of token
        hours: Custom expiry hours (optional)

    Returns:
        Tuple of (token_value, expiry_datetime)

    Example:
        token, expiry = generate_token_pair(TokenType.CONTRACT)
        contractor.contract_token = token
        contractor.contract_token_expiry = expiry
    """
    token = Token.generate(hours=hours, token_type=token_type)
    return token.value, token.expiry
