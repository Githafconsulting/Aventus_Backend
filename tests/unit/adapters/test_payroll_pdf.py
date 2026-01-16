"""
Unit tests for payroll PDF generation.
"""
import pytest
from unittest.mock import MagicMock
from io import BytesIO


class TestPayslipPDFGeneration:
    """Tests for payslip PDF generation."""

    @pytest.fixture
    def mock_payroll(self):
        """Mock payroll record."""
        payroll = MagicMock()
        payroll.id = 1
        payroll.contractor_id = "contractor-123"
        payroll.day_rate = 100.0
        payroll.work_days = 20
        payroll.gross_amount = 2000.0
        payroll.deductions = 0
        payroll.net_amount = 2000.0
        payroll.currency = "AED"
        payroll.period = "January 2025"
        payroll.charge_rate_day = 150.0
        payroll.invoice_amount = 3000.0
        return payroll

    @pytest.fixture
    def mock_contractor(self):
        """Mock contractor."""
        contractor = MagicMock()
        contractor.id = "contractor-123"
        contractor.first_name = "John"
        contractor.surname = "Doe"
        contractor.email = "john.doe@example.com"
        contractor.client_name = "Acme Corp"
        return contractor

    def test_payslip_pdf_generator_exists(self):
        """Test that payslip PDF generator can be imported."""
        from app.utils.payroll_pdf import generate_payslip_pdf
        assert generate_payslip_pdf is not None

    def test_payslip_returns_bytesio(self, mock_payroll, mock_contractor):
        """Test payslip generator returns BytesIO object."""
        from app.utils.payroll_pdf import generate_payslip_pdf

        result = generate_payslip_pdf(mock_payroll, mock_contractor)
        assert isinstance(result, BytesIO)

    def test_payslip_has_content(self, mock_payroll, mock_contractor):
        """Test payslip PDF has content."""
        from app.utils.payroll_pdf import generate_payslip_pdf

        result = generate_payslip_pdf(mock_payroll, mock_contractor)
        content = result.getvalue()
        assert len(content) > 0

    def test_payslip_is_valid_pdf(self, mock_payroll, mock_contractor):
        """Test payslip output starts with PDF header."""
        from app.utils.payroll_pdf import generate_payslip_pdf

        result = generate_payslip_pdf(mock_payroll, mock_contractor)
        content = result.getvalue()
        # PDF files start with %PDF
        assert content[:4] == b'%PDF'


class TestInvoicePDFGeneration:
    """Tests for invoice PDF generation."""

    @pytest.fixture
    def mock_payroll_with_invoice(self):
        """Mock payroll with invoice data."""
        payroll = MagicMock()
        payroll.id = 1
        payroll.contractor_id = "contractor-123"
        payroll.day_rate = 100.0
        payroll.work_days = 20
        payroll.gross_amount = 2000.0
        payroll.deductions = 0
        payroll.net_amount = 2000.0
        payroll.currency = "AED"
        payroll.period = "January 2025"
        payroll.charge_rate_day = 150.0
        payroll.invoice_amount = 3000.0
        return payroll

    @pytest.fixture
    def mock_contractor(self):
        """Mock contractor."""
        contractor = MagicMock()
        contractor.id = "contractor-123"
        contractor.first_name = "John"
        contractor.surname = "Doe"
        contractor.email = "john.doe@example.com"
        contractor.client_name = "Acme Corp"
        return contractor

    def test_invoice_pdf_generator_exists(self):
        """Test that invoice PDF generator can be imported."""
        from app.utils.payroll_pdf import generate_invoice_pdf
        assert generate_invoice_pdf is not None

    def test_invoice_returns_bytesio(self, mock_payroll_with_invoice, mock_contractor):
        """Test invoice generator returns BytesIO object."""
        from app.utils.payroll_pdf import generate_invoice_pdf

        result = generate_invoice_pdf(mock_payroll_with_invoice, mock_contractor)
        assert isinstance(result, BytesIO)

    def test_invoice_has_content(self, mock_payroll_with_invoice, mock_contractor):
        """Test invoice PDF has content."""
        from app.utils.payroll_pdf import generate_invoice_pdf

        result = generate_invoice_pdf(mock_payroll_with_invoice, mock_contractor)
        content = result.getvalue()
        assert len(content) > 0

    def test_invoice_is_valid_pdf(self, mock_payroll_with_invoice, mock_contractor):
        """Test invoice output starts with PDF header."""
        from app.utils.payroll_pdf import generate_invoice_pdf

        result = generate_invoice_pdf(mock_payroll_with_invoice, mock_contractor)
        content = result.getvalue()
        assert content[:4] == b'%PDF'


class TestPDFContent:
    """Tests for PDF content validation."""

    @pytest.fixture
    def mock_payroll(self):
        """Mock payroll record."""
        payroll = MagicMock()
        payroll.id = 1
        payroll.contractor_id = "contractor-123"
        payroll.day_rate = 100.0
        payroll.work_days = 20
        payroll.gross_amount = 2000.0
        payroll.deductions = 0
        payroll.net_amount = 2000.0
        payroll.currency = "AED"
        payroll.period = "January 2025"
        payroll.charge_rate_day = 150.0
        payroll.invoice_amount = 3000.0
        return payroll

    @pytest.fixture
    def mock_contractor(self):
        """Mock contractor."""
        contractor = MagicMock()
        contractor.id = "contractor-123"
        contractor.first_name = "John"
        contractor.surname = "Doe"
        contractor.email = "john.doe@example.com"
        contractor.client_name = "Acme Corp"
        return contractor

    def test_payslip_size_reasonable(self, mock_payroll, mock_contractor):
        """Test payslip PDF is reasonable size (not empty, not too large)."""
        from app.utils.payroll_pdf import generate_payslip_pdf

        result = generate_payslip_pdf(mock_payroll, mock_contractor)
        content = result.getvalue()

        # Should be at least 1KB for a valid PDF with content
        assert len(content) > 1000
        # Should be less than 1MB for a simple payslip
        assert len(content) < 1000000

    def test_invoice_size_reasonable(self, mock_payroll, mock_contractor):
        """Test invoice PDF is reasonable size."""
        from app.utils.payroll_pdf import generate_invoice_pdf

        result = generate_invoice_pdf(mock_payroll, mock_contractor)
        content = result.getvalue()

        assert len(content) > 1000
        assert len(content) < 1000000
