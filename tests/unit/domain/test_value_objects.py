"""
Unit tests for domain value objects.
"""
import pytest
from datetime import datetime
from app.domain.contractor.value_objects import (
    ContractorStatus,
    OnboardingRoute,
    PersonalInfo,
    ContactInfo,
    BankingInfo,
    PlacementInfo,
    DocumentSet,
)


class TestContractorStatus:
    """Tests for ContractorStatus enum."""

    def test_initial_statuses_exist(self):
        """Verify initial statuses are defined."""
        assert ContractorStatus.DRAFT.value == "draft"
        assert ContractorStatus.PENDING_DOCUMENTS.value == "pending_documents"
        assert ContractorStatus.DOCUMENTS_UPLOADED.value == "documents_uploaded"

    def test_uae_route_statuses_exist(self):
        """Verify UAE route statuses exist."""
        assert ContractorStatus.PENDING_COHF.value == "pending_cohf"
        assert ContractorStatus.AWAITING_COHF_SIGNATURE.value == "awaiting_cohf_signature"
        assert ContractorStatus.COHF_COMPLETED.value == "cohf_completed"

    def test_final_statuses_exist(self):
        """Verify final statuses exist."""
        assert ContractorStatus.ACTIVE.value == "active"
        assert ContractorStatus.TERMINATED.value == "terminated"
        assert ContractorStatus.CANCELLED.value == "cancelled"

    def test_status_from_string(self):
        """Test creating status from string value."""
        status = ContractorStatus("pending_documents")
        assert status == ContractorStatus.PENDING_DOCUMENTS

    def test_initial_statuses_method(self):
        """Test initial_statuses class method."""
        initial = ContractorStatus.initial_statuses()
        assert ContractorStatus.DRAFT in initial
        assert ContractorStatus.PENDING_DOCUMENTS in initial

    def test_terminal_statuses_method(self):
        """Test terminal_statuses class method."""
        terminal = ContractorStatus.terminal_statuses()
        assert ContractorStatus.TERMINATED in terminal
        assert ContractorStatus.CANCELLED in terminal


class TestOnboardingRoute:
    """Tests for OnboardingRoute enum."""

    def test_all_routes_exist(self):
        """Verify all expected routes are defined."""
        assert OnboardingRoute.WPS.value == "wps"
        assert OnboardingRoute.FREELANCER.value == "freelancer"
        assert OnboardingRoute.UAE.value == "uae"
        assert OnboardingRoute.SAUDI.value == "saudi"
        assert OnboardingRoute.OFFSHORE.value == "offshore"

    def test_route_from_string(self):
        """Test creating route from string value."""
        route = OnboardingRoute("freelancer")
        assert route == OnboardingRoute.FREELANCER

    def test_display_name_property(self):
        """Test display_name property."""
        assert "UAE" in OnboardingRoute.UAE.display_name
        assert "WPS" in OnboardingRoute.WPS.display_name

    def test_requires_third_party(self):
        """Test requires_third_party property."""
        assert OnboardingRoute.UAE.requires_third_party is True
        assert OnboardingRoute.SAUDI.requires_third_party is True
        assert OnboardingRoute.WPS.requires_third_party is False
        assert OnboardingRoute.FREELANCER.requires_third_party is False

    def test_requires_cohf(self):
        """Test requires_cohf property."""
        assert OnboardingRoute.UAE.requires_cohf is True
        assert OnboardingRoute.SAUDI.requires_cohf is False

    def test_requires_quote_sheet(self):
        """Test requires_quote_sheet property."""
        assert OnboardingRoute.SAUDI.requires_quote_sheet is True
        assert OnboardingRoute.UAE.requires_quote_sheet is False


class TestPersonalInfo:
    """Tests for PersonalInfo value object."""

    def test_create_personal_info(self):
        """Test creating personal info."""
        info = PersonalInfo(
            first_name="John",
            surname="Doe",
        )
        assert info.first_name == "John"
        assert info.surname == "Doe"

    def test_create_with_optional_fields(self):
        """Test creating with optional fields."""
        info = PersonalInfo(
            first_name="John",
            surname="Doe",
            gender="male",
            nationality="US",
        )
        assert info.gender == "male"
        assert info.nationality == "US"

    def test_full_name_property(self):
        """Test full_name computed property."""
        info = PersonalInfo(first_name="John", surname="Doe")
        assert info.full_name == "John Doe"

    def test_full_name_with_middle_name(self):
        """Test full_name with middle name."""
        info = PersonalInfo(
            first_name="John",
            surname="Doe",
            middle_name="William"
        )
        assert info.full_name == "John William Doe"

    def test_personal_info_immutable(self):
        """Test that PersonalInfo is immutable (frozen)."""
        info = PersonalInfo(first_name="John", surname="Doe")
        with pytest.raises(AttributeError):
            info.first_name = "Jane"

    def test_age_property(self):
        """Test age calculation."""
        info = PersonalInfo(
            first_name="John",
            surname="Doe",
            date_of_birth=datetime(1990, 1, 15)
        )
        assert info.age is not None
        assert info.age >= 34  # Born in 1990


class TestContactInfo:
    """Tests for ContactInfo value object."""

    def test_create_contact_info(self):
        """Test creating contact info."""
        info = ContactInfo(
            email="john@example.com",
            phone="+1234567890",
        )
        assert info.email == "john@example.com"
        assert info.phone == "+1234567890"

    def test_create_with_address(self):
        """Test creating with address fields."""
        info = ContactInfo(
            email="john@example.com",
            phone="+1234567890",
            address="123 Main St",
            city="New York",
            country="USA",
        )
        assert info.address == "123 Main St"
        assert info.city == "New York"

    def test_contact_info_immutable(self):
        """Test that ContactInfo is immutable."""
        info = ContactInfo(email="john@example.com", phone="+1234567890")
        with pytest.raises(AttributeError):
            info.email = "new@example.com"

    def test_is_complete_property(self):
        """Test is_complete property."""
        info = ContactInfo(email="john@example.com", phone="+1234567890")
        assert info.is_complete is True

        info_incomplete = ContactInfo(email="", phone="")
        assert info_incomplete.is_complete is False


class TestBankingInfo:
    """Tests for BankingInfo value object."""

    def test_create_banking_info(self):
        """Test creating banking info."""
        info = BankingInfo(
            bank_name="Test Bank",
            account_number="1234567890",
            iban="GB82WEST12345698765432",
        )
        assert info.bank_name == "Test Bank"
        assert info.account_number == "1234567890"
        assert info.iban == "GB82WEST12345698765432"

    def test_banking_info_optional_fields(self):
        """Test banking info with optional fields."""
        info = BankingInfo(bank_name="Test Bank")
        assert info.bank_name == "Test Bank"
        assert info.account_number is None

    def test_is_complete_property(self):
        """Test is_complete property."""
        info_with_account = BankingInfo(account_number="123456")
        assert info_with_account.is_complete is True

        info_with_iban = BankingInfo(iban="GB82WEST12345")
        assert info_with_iban.is_complete is True

        info_incomplete = BankingInfo(bank_name="Bank")
        assert info_incomplete.is_complete is False


class TestPlacementInfo:
    """Tests for PlacementInfo value object."""

    def test_create_placement_info(self):
        """Test creating placement info."""
        info = PlacementInfo(
            client_name="Acme Corp",
            role="Developer",
            currency="USD",
        )
        assert info.client_name == "Acme Corp"
        assert info.role == "Developer"
        assert info.currency == "USD"

    def test_rate_display_monthly(self):
        """Test rate_display with monthly rate."""
        info = PlacementInfo(
            monthly_rate=5000.0,
            currency="USD",
        )
        assert "5,000.00" in info.rate_display
        assert "month" in info.rate_display

    def test_rate_display_daily(self):
        """Test rate_display with day rate."""
        info = PlacementInfo(
            day_rate=250.0,
            currency="AED",
        )
        assert "250.00" in info.rate_display
        assert "day" in info.rate_display

    def test_rate_display_not_set(self):
        """Test rate_display when no rate set."""
        info = PlacementInfo(client_name="Acme")
        assert info.rate_display == "Rate not set"


class TestDocumentSet:
    """Tests for DocumentSet value object."""

    def test_create_document_set(self):
        """Test creating document set."""
        docs = DocumentSet(
            passport_url="https://storage.com/passport.pdf",
            photo_url="https://storage.com/photo.jpg",
        )
        assert docs.passport_url is not None
        assert docs.photo_url is not None

    def test_is_complete_with_required_docs(self):
        """Test is_complete when required docs present."""
        docs = DocumentSet(
            passport_url="https://storage.com/passport.pdf",
            photo_url="https://storage.com/photo.jpg",
        )
        assert docs.is_complete is True

    def test_is_complete_missing_docs(self):
        """Test is_complete when docs missing."""
        docs = DocumentSet(passport_url="https://storage.com/passport.pdf")
        assert docs.is_complete is False

    def test_uploaded_count(self):
        """Test uploaded_count property."""
        docs = DocumentSet(
            passport_url="url1",
            photo_url="url2",
            visa_url="url3",
        )
        assert docs.uploaded_count == 3

    def test_uploaded_count_with_other_docs(self):
        """Test uploaded_count with other_documents."""
        docs = DocumentSet(
            passport_url="url1",
            photo_url="url2",
            other_documents=["doc1", "doc2"],
        )
        assert docs.uploaded_count == 4
