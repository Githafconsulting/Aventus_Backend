"""
Unit tests for PDF adapters.
"""
import pytest
from app.adapters.pdf.registry import PDFGeneratorRegistry
from app.adapters.pdf.interface import IPDFGenerator, PDFResult
# Import generators to ensure they are registered
import app.adapters.pdf.generators  # noqa: F401


class TestPDFGeneratorRegistry:
    """Tests for PDFGeneratorRegistry."""

    def test_available_types(self):
        """Test getting available PDF types."""
        types = PDFGeneratorRegistry.available_types()

        assert isinstance(types, list)
        assert "contract" in types
        assert "work_order" in types
        assert "cohf" in types
        assert "quote_sheet" in types
        assert "timesheet" in types

    def test_is_registered(self):
        """Test checking if type is registered."""
        assert PDFGeneratorRegistry.is_registered("contract") is True
        assert PDFGeneratorRegistry.is_registered("invalid_type") is False

    def test_get_generator(self):
        """Test getting a generator."""
        generator = PDFGeneratorRegistry.get("contract")

        assert generator is not None
        assert isinstance(generator, IPDFGenerator)

    def test_get_invalid_raises(self):
        """Test getting invalid type raises error."""
        with pytest.raises(KeyError):
            PDFGeneratorRegistry.get("invalid_type")

    def test_get_or_none(self):
        """Test get_or_none returns None for invalid."""
        result = PDFGeneratorRegistry.get_or_none("invalid_type")
        assert result is None

        result = PDFGeneratorRegistry.get_or_none("contract")
        assert result is not None

    def test_generators_have_document_type(self):
        """Test all generators have document_type attribute."""
        for doc_type in PDFGeneratorRegistry.available_types():
            generator = PDFGeneratorRegistry.get(doc_type)
            assert hasattr(generator, "document_type")


class TestContractPDFGenerator:
    """Tests for Contract PDF generator."""

    @pytest.fixture
    def generator(self):
        return PDFGeneratorRegistry.get("contract")

    def test_document_type(self, generator):
        """Test document type."""
        assert generator.document_type == "contract"

    def test_validate_data_missing_fields(self, generator):
        """Test validation with missing fields."""
        missing = generator.validate_data({})
        assert len(missing) > 0

    def test_validate_data_with_required(self, generator):
        """Test validation with required fields."""
        missing = generator.validate_data({"contractor_name": "John Doe"})
        assert len(missing) == 0


class TestWorkOrderPDFGenerator:
    """Tests for Work Order PDF generator."""

    @pytest.fixture
    def generator(self):
        return PDFGeneratorRegistry.get("work_order")

    def test_document_type(self, generator):
        """Test document type."""
        assert generator.document_type == "work_order"


class TestCOHFPDFGenerator:
    """Tests for COHF PDF generator."""

    @pytest.fixture
    def generator(self):
        return PDFGeneratorRegistry.get("cohf")

    def test_document_type(self, generator):
        """Test document type."""
        assert generator.document_type == "cohf"


class TestQuoteSheetPDFGenerator:
    """Tests for Quote Sheet PDF generator."""

    @pytest.fixture
    def generator(self):
        return PDFGeneratorRegistry.get("quote_sheet")

    def test_document_type(self, generator):
        """Test document type."""
        assert generator.document_type == "quote_sheet"


class TestTimesheetPDFGenerator:
    """Tests for Timesheet PDF generator."""

    @pytest.fixture
    def generator(self):
        return PDFGeneratorRegistry.get("timesheet")

    def test_document_type(self, generator):
        """Test document type."""
        assert generator.document_type == "timesheet"


class TestPDFResult:
    """Tests for PDFResult dataclass."""

    def test_success_result(self):
        """Test creating success result."""
        result = PDFResult(
            success=True,
            content=b"PDF content",
            filename="document.pdf",
        )

        assert result.success is True
        assert result.content is not None
        assert result.filename == "document.pdf"

    def test_failure_result(self):
        """Test creating failure result."""
        result = PDFResult(
            success=False,
            error="Generation failed",
        )

        assert result.success is False
        assert result.error == "Generation failed"
        assert result.content is None
