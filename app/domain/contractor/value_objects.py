"""
Contractor domain value objects.
Immutable objects that represent contractor-related concepts.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


class ContractorStatus(str, Enum):
    """
    All possible contractor statuses throughout the onboarding lifecycle.
    """
    # Initial stages
    DRAFT = "draft"
    PENDING_DOCUMENTS = "pending_documents"
    DOCUMENTS_UPLOADED = "documents_uploaded"

    # UAE Route specific (COHF)
    PENDING_COHF = "pending_cohf"
    AWAITING_COHF_SIGNATURE = "awaiting_cohf_signature"
    COHF_COMPLETED = "cohf_completed"

    # Saudi Route specific (Quote Sheet)
    PENDING_THIRD_PARTY_QUOTE = "pending_third_party_quote"

    # CDS and Costing
    PENDING_CDS_CS = "pending_cds_cs"
    CDS_CS_COMPLETED = "cds_cs_completed"

    # Admin Review
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"

    # Work Order
    PENDING_CLIENT_WO_SIGNATURE = "pending_client_wo_signature"
    WORK_ORDER_COMPLETED = "work_order_completed"

    # Contract stages
    PENDING_3RD_PARTY_CONTRACT = "pending_3rd_party_contract"
    PENDING_CONTRACT_UPLOAD = "pending_contract_upload"
    CONTRACT_APPROVED = "contract_approved"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"

    # Final states
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"

    # Offboarding statuses
    NOTICE_PERIOD = "notice_period"          # In notice period before offboarding
    OFFBOARDING = "offboarding"              # Offboarding in progress
    OFFBOARDED = "offboarded"                # Successfully offboarded (terminal but rehirable)

    # Extension status
    EXTENSION_PENDING = "extension_pending"  # Contract extension in progress

    @classmethod
    def initial_statuses(cls) -> List["ContractorStatus"]:
        """Statuses at the beginning of onboarding."""
        return [cls.DRAFT, cls.PENDING_DOCUMENTS, cls.DOCUMENTS_UPLOADED]

    @classmethod
    def active_statuses(cls) -> List["ContractorStatus"]:
        """Statuses for active contractors."""
        return [cls.ACTIVE, cls.EXTENSION_PENDING]

    @classmethod
    def terminal_statuses(cls) -> List["ContractorStatus"]:
        """Final statuses (no further transitions)."""
        return [cls.CANCELLED, cls.TERMINATED, cls.OFFBOARDED]

    @classmethod
    def offboarding_statuses(cls) -> List["ContractorStatus"]:
        """Statuses during offboarding process."""
        return [cls.NOTICE_PERIOD, cls.OFFBOARDING]

    @classmethod
    def rehirable_statuses(cls) -> List["ContractorStatus"]:
        """Statuses that allow rehiring."""
        return [cls.OFFBOARDED]


class OnboardingRoute(str, Enum):
    """
    Available onboarding routes based on contractor location/type.
    Each route has different workflow steps and requirements.
    """
    WPS = "wps"                    # Work Permit System
    FREELANCER = "freelancer"      # Freelancer arrangement
    UAE = "uae"                    # 3rd Party UAE
    SAUDI = "saudi"                # 3rd Party Saudi Arabia
    OFFSHORE = "offshore"          # International/Offshore

    @property
    def display_name(self) -> str:
        """Human-readable name for the route."""
        names = {
            "wps": "WPS (Work Permit System)",
            "freelancer": "Freelancer",
            "uae": "3rd Party UAE",
            "saudi": "3rd Party Saudi Arabia",
            "offshore": "Offshore/International",
        }
        return names.get(self.value, self.value)

    @property
    def requires_third_party(self) -> bool:
        """Check if route requires third party involvement."""
        return self in (OnboardingRoute.UAE, OnboardingRoute.SAUDI)

    @property
    def requires_cohf(self) -> bool:
        """Check if route requires COHF form."""
        return self == OnboardingRoute.UAE

    @property
    def requires_quote_sheet(self) -> bool:
        """Check if route requires quote sheet."""
        return self == OnboardingRoute.SAUDI


@dataclass(frozen=True)
class PersonalInfo:
    """
    Value object for contractor personal information.
    """
    first_name: str
    surname: str
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    marital_status: Optional[str] = None
    children_count: Optional[int] = None

    @property
    def full_name(self) -> str:
        """Get full name with middle name if present."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.surname)
        return " ".join(parts)

    @property
    def age(self) -> Optional[int]:
        """Calculate age from date of birth."""
        if not self.date_of_birth:
            return None
        today = datetime.now()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age


@dataclass(frozen=True)
class ContactInfo:
    """
    Value object for contractor contact information.
    """
    email: str
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if contact info has all required fields."""
        return bool(self.email and self.phone)


@dataclass(frozen=True)
class BankingInfo:
    """
    Value object for contractor banking information.
    """
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    swift_code: Optional[str] = None
    currency: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Check if banking info is complete for payments."""
        return bool(self.account_number or self.iban)


@dataclass(frozen=True)
class PlacementInfo:
    """
    Value object for contractor placement/assignment information.
    """
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    monthly_rate: Optional[float] = None
    day_rate: Optional[float] = None
    currency: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if placement is currently active."""
        now = datetime.now()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True

    @property
    def rate_display(self) -> str:
        """Get formatted rate for display."""
        if self.monthly_rate:
            return f"{self.currency or 'USD'} {self.monthly_rate:,.2f}/month"
        if self.day_rate:
            return f"{self.currency or 'USD'} {self.day_rate:,.2f}/day"
        return "Rate not set"


@dataclass(frozen=True)
class DocumentSet:
    """
    Value object representing required documents for a contractor.
    """
    passport_url: Optional[str] = None
    photo_url: Optional[str] = None
    visa_url: Optional[str] = None
    emirates_id_url: Optional[str] = None
    degree_url: Optional[str] = None
    other_documents: Optional[List[str]] = None

    @property
    def required_documents(self) -> List[str]:
        """List of required document fields."""
        return ["passport_url", "photo_url"]

    @property
    def is_complete(self) -> bool:
        """Check if all required documents are uploaded."""
        return bool(self.passport_url and self.photo_url)

    @property
    def uploaded_count(self) -> int:
        """Count of uploaded documents."""
        count = 0
        for field in ["passport_url", "photo_url", "visa_url", "emirates_id_url", "degree_url"]:
            if getattr(self, field):
                count += 1
        if self.other_documents:
            count += len(self.other_documents)
        return count
