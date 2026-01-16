"""
Contractor data extraction utility.

Consolidates logic for extracting pay-related information from contractors.
Eliminates repetitive CDS/field fallback patterns.
"""
from typing import Any, Optional
from app.domain.payroll.value_objects import normalize_rate_type, ContractorPayInfo
from app.models.payroll import RateType


class ContractorDataExtractor:
    """
    Extract and consolidate contractor pay information.

    Follows Single Responsibility Principle - only handles data extraction.
    """

    def __init__(self, contractor: Any):
        """
        Initialize extractor with contractor model.

        Args:
            contractor: Contractor SQLAlchemy model instance
        """
        self.contractor = contractor
        self.cds = contractor.cds_form_data or {}
        self.costing = contractor.costing_sheet_data or {}

    def extract_pay_info(self) -> ContractorPayInfo:
        """
        Extract all pay-related information from contractor.

        Returns:
            ContractorPayInfo with consolidated data

        Raises:
            ValueError: If rate type cannot be determined
        """
        return ContractorPayInfo(
            rate_type=self._extract_rate_type(),
            currency=self._extract_currency(),
            monthly_rate=self._extract_monthly_rate(),
            day_rate=self._extract_day_rate(),
            charge_rate_month=self._extract_charge_rate_month(),
            charge_rate_day=self._extract_charge_rate_day(),
            leave_allowance=self._extract_leave_allowance(),
            third_party_name=self._extract_third_party_name(),
            management_fee=self._extract_management_fee(),
            accrual_gratuity=self._extract_accrual_gratuity(),
            accrual_airfare=self._extract_accrual_airfare(),
            accrual_annual_leave=self._extract_accrual_annual_leave(),
            country=self._extract_country(),
            client_name=self._extract_client_name(),
        )

    def _get_field(
        self,
        cds_key: Optional[str] = None,
        direct_field: Optional[str] = None,
        costing_keys: Optional[list] = None,
        default: Any = None,
        converter: Optional[callable] = None,
    ) -> Any:
        """
        Generic field extractor with fallback logic.

        Priority: CDS form data → Direct field → Costing sheet → Default

        Args:
            cds_key: Key in CDS form data
            direct_field: Direct attribute on contractor model
            costing_keys: List of keys to try in costing sheet data
            default: Default value if not found
            converter: Optional function to convert value (e.g., float, str.lower)

        Returns:
            Extracted and optionally converted value
        """
        # Try CDS form data first
        if cds_key and cds_key in self.cds:
            value = self.cds[cds_key]
            if value is not None:
                return converter(value) if converter else value

        # Try direct field
        if direct_field and hasattr(self.contractor, direct_field):
            value = getattr(self.contractor, direct_field)
            if value is not None:
                return converter(value) if converter else value

        # Try costing sheet keys
        if costing_keys:
            for key in costing_keys:
                if key in self.costing:
                    value = self.costing[key]
                    if value is not None:
                        return converter(value) if converter else value

        return default

    def _extract_rate_type(self) -> RateType:
        """Extract and normalize rate type."""
        rate_type_str = self._get_field(
            cds_key="rateType",
            direct_field="rate_type",
            default="monthly",
            converter=str.lower
        )
        return normalize_rate_type(rate_type_str)

    def _extract_currency(self) -> str:
        """Extract currency code."""
        return self._get_field(
            cds_key="currency",
            direct_field="currency",
            default="AED"
        )

    def _extract_monthly_rate(self) -> Optional[float]:
        """Extract monthly salary rate."""
        return self._get_field(
            cds_key="grossSalary",
            direct_field="gross_salary",
            converter=float
        )

    def _extract_day_rate(self) -> Optional[float]:
        """Extract daily rate."""
        return self._get_field(
            cds_key="dayRate",
            direct_field="day_rate",
            converter=float
        )

    def _extract_charge_rate_month(self) -> Optional[float]:
        """Extract monthly charge rate for invoicing."""
        return self._get_field(
            cds_key="chargeRateMonth",
            direct_field="charge_rate_month",
            converter=float
        )

    def _extract_charge_rate_day(self) -> Optional[float]:
        """Extract daily charge rate for invoicing."""
        return self._get_field(
            cds_key="chargeRateDay",
            direct_field="charge_rate_day",
            converter=float
        )

    def _extract_leave_allowance(self) -> float:
        """Extract annual leave allowance in days."""
        # Priority: leave_allowance field → CDS leaveAllowance → vacation_days → 30 default
        return self._get_field(
            cds_key="leaveAllowance",
            direct_field="leave_allowance",
            default=30.0,
            converter=float
        ) or self._get_field(
            direct_field="vacation_days",
            default=30.0,
            converter=float
        )

    def _extract_third_party_name(self) -> str:
        """Extract third party/management company name."""
        return self._get_field(
            direct_field="company_name",
            default=""
        )

    def _extract_management_fee(self) -> float:
        """Extract management company charges."""
        return self._get_field(
            costing_keys=[
                "management_company_charges",
                "managementFee",
                "management_fee",
                "serviceCharge"
            ],
            default=0.0,
            converter=float
        )

    def _extract_accrual_gratuity(self) -> float:
        """Extract gratuity accrual."""
        return self._get_field(
            costing_keys=["eosb", "gratuity"],
            default=0.0,
            converter=float
        )

    def _extract_accrual_airfare(self) -> float:
        """Extract airfare accrual."""
        return self._get_field(
            costing_keys=["airfare"],
            default=0.0,
            converter=float
        )

    def _extract_accrual_annual_leave(self) -> float:
        """Extract annual leave accrual."""
        return self._get_field(
            costing_keys=["leave", "annualLeave"],
            default=0.0,
            converter=float
        )

    def _extract_country(self) -> str:
        """Extract country for VAT calculation."""
        return self._get_field(
            direct_field="onboarding_route",
            default="UAE"
        )

    def _extract_client_name(self) -> str:
        """Extract client name."""
        return self._get_field(
            direct_field="client_name",
            default=""
        )
