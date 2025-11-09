import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.contractor import Contractor, ContractorStatus, SignatureType


# Create an in-memory SQLite database for testing
@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


class TestContractorStatus:
    """Test ContractorStatus enum"""

    def test_contractor_status_values(self):
        """Test that all contractor status values are correct"""
        assert ContractorStatus.DRAFT == "draft"
        assert ContractorStatus.PENDING_SIGNATURE == "pending_signature"
        assert ContractorStatus.SIGNED == "signed"
        assert ContractorStatus.ACTIVE == "active"
        assert ContractorStatus.SUSPENDED == "suspended"

    def test_contractor_status_is_string_enum(self):
        """Test that ContractorStatus inherits from str"""
        assert isinstance(ContractorStatus.DRAFT, str)
        assert issubclass(ContractorStatus, str)


class TestSignatureType:
    """Test SignatureType enum"""

    def test_signature_type_values(self):
        """Test that all signature type values are correct"""
        assert SignatureType.TYPED == "typed"
        assert SignatureType.DRAWN == "drawn"

    def test_signature_type_is_string_enum(self):
        """Test that SignatureType inherits from str"""
        assert isinstance(SignatureType.TYPED, str)
        assert issubclass(SignatureType, str)


class TestContractorModel:
    """Test Contractor model"""

    def test_create_contractor_minimal(self, test_db):
        """Test creating a contractor with minimal required fields"""
        contractor = Contractor(
            id="test-001",
            first_name="John",
            surname="Doe",
            gender="Male",
            nationality="American",
            home_address="123 Main St",
            phone="+1234567890",
            email="john.doe@example.com",
            dob="1990-01-01",
            currency="SAR"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.id == "test-001"
        assert contractor.first_name == "John"
        assert contractor.surname == "Doe"
        assert contractor.email == "john.doe@example.com"
        assert contractor.status == ContractorStatus.DRAFT
        assert contractor.currency == "SAR"
        assert contractor.created_at is not None

    def test_create_contractor_full(self, test_db):
        """Test creating a contractor with all fields"""
        contractor = Contractor(
            id="test-002",
            status=ContractorStatus.ACTIVE,
            contract_token="token123",
            signature_type="typed",
            signature_data="John Doe",
            first_name="Jane",
            surname="Smith",
            gender="Female",
            nationality="British",
            home_address="456 Oak Ave",
            address_line3="Suite 100",
            address_line4="Building A",
            phone="+4420123456",
            email="jane.smith@example.com",
            dob="1985-05-15",
            umbrella_company_name="Umbrella Corp",
            registered_address="789 Business Rd",
            client_name="ABC Company",
            role="Software Engineer",
            start_date="2024-01-01",
            end_date="2024-12-31",
            location="London",
            duration="12 months",
            currency="GBP",
            client_charge_rate="100",
            candidate_pay_rate="80",
            other_notes="Special requirements"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.id == "test-002"
        assert contractor.status == ContractorStatus.ACTIVE
        assert contractor.first_name == "Jane"
        assert contractor.surname == "Smith"
        assert contractor.email == "jane.smith@example.com"
        assert contractor.contract_token == "token123"
        assert contractor.signature_type == "typed"
        assert contractor.signature_data == "John Doe"
        assert contractor.client_name == "ABC Company"
        assert contractor.role == "Software Engineer"
        assert contractor.currency == "GBP"
        assert contractor.other_notes == "Special requirements"

    def test_contractor_default_status(self, test_db):
        """Test that contractor status defaults to DRAFT"""
        contractor = Contractor(
            id="test-003",
            first_name="Bob",
            surname="Wilson",
            gender="Male",
            nationality="Canadian",
            home_address="789 Maple St",
            phone="+1987654321",
            email="bob.wilson@example.com",
            dob="1992-03-20"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.status == ContractorStatus.DRAFT

    def test_contractor_unique_email(self, test_db):
        """Test that email must be unique"""
        contractor1 = Contractor(
            id="test-004",
            first_name="Alice",
            surname="Johnson",
            gender="Female",
            nationality="Australian",
            home_address="111 Beach Rd",
            phone="+61123456789",
            email="alice@example.com",
            dob="1988-07-10"
        )

        contractor2 = Contractor(
            id="test-005",
            first_name="Bob",
            surname="Smith",
            gender="Male",
            nationality="Australian",
            home_address="222 Beach Rd",
            phone="+61987654321",
            email="alice@example.com",
            dob="1990-08-15"
        )

        test_db.add(contractor1)
        test_db.commit()

        test_db.add(contractor2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

    def test_contractor_unique_contract_token(self, test_db):
        """Test that contract_token must be unique"""
        contractor1 = Contractor(
            id="test-006",
            first_name="Charlie",
            surname="Brown",
            gender="Male",
            nationality="American",
            home_address="333 Park Ave",
            phone="+1111111111",
            email="charlie@example.com",
            dob="1991-04-05",
            contract_token="unique-token-123"
        )

        contractor2 = Contractor(
            id="test-007",
            first_name="Diana",
            surname="Prince",
            gender="Female",
            nationality="American",
            home_address="444 Hero St",
            phone="+1222222222",
            email="diana@example.com",
            dob="1989-06-12",
            contract_token="unique-token-123"
        )

        test_db.add(contractor1)
        test_db.commit()

        test_db.add(contractor2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

    def test_contractor_status_transitions(self, test_db):
        """Test contractor status can be updated"""
        contractor = Contractor(
            id="test-008",
            first_name="Eve",
            surname="Taylor",
            gender="Female",
            nationality="Irish",
            home_address="555 Green St",
            phone="+353123456789",
            email="eve@example.com",
            dob="1993-09-22"
        )

        test_db.add(contractor)
        test_db.commit()

        assert contractor.status == ContractorStatus.DRAFT

        contractor.status = ContractorStatus.PENDING_SIGNATURE
        test_db.commit()
        test_db.refresh(contractor)
        assert contractor.status == ContractorStatus.PENDING_SIGNATURE

        contractor.status = ContractorStatus.SIGNED
        test_db.commit()
        test_db.refresh(contractor)
        assert contractor.status == ContractorStatus.SIGNED

        contractor.status = ContractorStatus.ACTIVE
        test_db.commit()
        test_db.refresh(contractor)
        assert contractor.status == ContractorStatus.ACTIVE

    def test_contractor_timestamps(self, test_db):
        """Test that created_at is automatically set"""
        contractor = Contractor(
            id="test-009",
            first_name="Frank",
            surname="Miller",
            gender="Male",
            nationality="German",
            home_address="666 Berlin St",
            phone="+4912345678",
            email="frank@example.com",
            dob="1987-11-30"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.created_at is not None
        assert isinstance(contractor.created_at, datetime)

    def test_contractor_json_cds_form_data(self, test_db):
        """Test that cds_form_data can store JSON"""
        cds_data = {
            "field1": "value1",
            "field2": "value2",
            "nested": {"key": "value"}
        }

        contractor = Contractor(
            id="test-010",
            first_name="Grace",
            surname="Lee",
            gender="Female",
            nationality="Korean",
            home_address="777 Seoul St",
            phone="+82123456789",
            email="grace@example.com",
            dob="1994-02-14",
            cds_form_data=cds_data
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.cds_form_data == cds_data
        assert contractor.cds_form_data["field1"] == "value1"
        assert contractor.cds_form_data["nested"]["key"] == "value"

    def test_contractor_signature_data(self, test_db):
        """Test contractor signature data storage"""
        contractor = Contractor(
            id="test-011",
            first_name="Henry",
            surname="Ford",
            gender="Male",
            nationality="American",
            home_address="888 Auto Dr",
            phone="+1333333333",
            email="henry@example.com",
            dob="1990-12-25",
            signature_type="drawn",
            signature_data="base64encodedimagedata"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.signature_type == "drawn"
        assert contractor.signature_data == "base64encodedimagedata"

    def test_contractor_optional_dates(self, test_db):
        """Test that date fields can be nullable"""
        contractor = Contractor(
            id="test-012",
            first_name="Ivy",
            surname="Green",
            gender="Female",
            nationality="Canadian",
            home_address="999 Maple Ave",
            phone="+1444444444",
            email="ivy@example.com",
            dob="1995-08-08"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.sent_date is None
        assert contractor.signed_date is None
        assert contractor.activated_date is None
        assert contractor.token_expiry is None

    def test_contractor_currency_default(self, test_db):
        """Test that currency defaults to SAR"""
        contractor = Contractor(
            id="test-013",
            first_name="Jack",
            surname="Black",
            gender="Male",
            nationality="American",
            home_address="100 Rock St",
            phone="+1555555555",
            email="jack@example.com",
            dob="1969-08-28"
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert contractor.currency == "SAR"

    def test_contractor_text_fields(self, test_db):
        """Test Text fields can store long content"""
        long_text = "This is a very long text " * 100

        contractor = Contractor(
            id="test-014",
            first_name="Kate",
            surname="White",
            gender="Female",
            nationality="British",
            home_address="200 Long St",
            phone="+4466666666",
            email="kate@example.com",
            dob="1992-05-17",
            other_notes=long_text,
            generated_contract=long_text,
            invoice_instructions=long_text
        )

        test_db.add(contractor)
        test_db.commit()
        test_db.refresh(contractor)

        assert len(contractor.other_notes) > 1000
        assert contractor.other_notes == long_text
        assert contractor.generated_contract == long_text
        assert contractor.invoice_instructions == long_text
