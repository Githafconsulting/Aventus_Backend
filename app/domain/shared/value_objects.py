"""
Shared value objects used across domain modules.
Value objects are immutable and compared by value, not identity.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    CONSULTANT = "consultant"
    CLIENT = "client"
    CONTRACTOR = "contractor"


@dataclass(frozen=True)
class Email:
    """
    Email address value object with validation.
    """
    value: str

    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError(f"Invalid email address: {self.value}")

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        """Get the domain part of the email."""
        return self.value.split("@")[1]


@dataclass(frozen=True)
class PhoneNumber:
    """
    Phone number value object.
    """
    value: str

    def __str__(self) -> str:
        return self.value

    @property
    def is_international(self) -> bool:
        """Check if phone number has international prefix."""
        return self.value.startswith("+")


@dataclass(frozen=True)
class Address:
    """
    Address value object.
    """
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if address has all required fields."""
        return all([self.street, self.city, self.country])

    def to_string(self) -> str:
        """Format address as single line string."""
        parts = [p for p in [self.street, self.city, self.state, self.postal_code, self.country] if p]
        return ", ".join(parts)


@dataclass(frozen=True)
class Money:
    """
    Money value object with currency.
    """
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)


@dataclass(frozen=True)
class DateRange:
    """
    Date range value object.
    """
    start_date: datetime
    end_date: Optional[datetime] = None

    def __post_init__(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")

    @property
    def is_ongoing(self) -> bool:
        """Check if date range has no end date."""
        return self.end_date is None

    @property
    def duration_days(self) -> Optional[int]:
        """Get duration in days (None if ongoing)."""
        if self.end_date is None:
            return None
        return (self.end_date - self.start_date).days

    def contains(self, date: datetime) -> bool:
        """Check if a date falls within this range."""
        if date < self.start_date:
            return False
        if self.end_date and date > self.end_date:
            return False
        return True
