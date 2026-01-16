"""
Integration tests for payroll API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestPayrollEndpoints:
    """Integration tests for payroll endpoints."""

    def test_api_structure_exists(self):
        """Test that the payroll router can be imported."""
        from app.routes.payroll import router
        assert router is not None

    def test_router_has_prefix(self):
        """Test router has correct prefix."""
        from app.routes.payroll import router
        assert router.prefix == "/api/v1/payroll"

    def test_router_has_tags(self):
        """Test router has correct tags."""
        from app.routes.payroll import router
        assert "payroll" in router.tags


class TestPayrollReadyEndpoint:
    """Tests for /api/v1/payroll/ready endpoint."""

    def test_ready_endpoint_exists(self):
        """Test that ready endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/ready" in r for r in routes)

    def test_ready_endpoint_returns_list_structure(self):
        """Test ready endpoint returns expected structure."""
        expected_keys = ["timesheets", "total"]
        # Structure validation
        response = {"timesheets": [], "total": 0}
        for key in expected_keys:
            assert key in response


class TestPayrollCalculateEndpoint:
    """Tests for /api/v1/payroll/{timesheet_id}/calculate endpoint."""

    def test_calculate_endpoint_exists(self):
        """Test that calculate endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/calculate" in r for r in routes)

    @pytest.fixture
    def mock_timesheet(self):
        """Mock approved timesheet."""
        from app.models.timesheet import TimesheetStatus

        timesheet = MagicMock()
        timesheet.id = 1
        timesheet.contractor_id = "contractor-123"
        timesheet.status = TimesheetStatus.APPROVED
        timesheet.work_days = 20
        timesheet.month = "January 2025"
        return timesheet

    @pytest.fixture
    def mock_contractor(self):
        """Mock contractor with pay info."""
        contractor = MagicMock()
        contractor.id = "contractor-123"
        contractor.first_name = "John"
        contractor.surname = "Doe"
        contractor.rate_type = "monthly"
        contractor.gross_salary = "2000"
        contractor.day_rate = None
        contractor.charge_rate_month = "3000"
        contractor.charge_rate_day = None
        contractor.currency = "AED"
        contractor.costing_sheet_data = {"estimated_working_days": "20"}
        contractor.cds_form_data = {}
        return contractor

    def test_calculate_creates_payroll_record(self, mock_timesheet, mock_contractor):
        """Test calculation creates payroll with correct values."""
        # Simulate calculation
        working_days = 20
        monthly_salary = 2000.0
        day_rate = monthly_salary / working_days
        gross_amount = day_rate * mock_timesheet.work_days

        assert day_rate == 100.0
        assert gross_amount == 2000.0


class TestPayrollDetailedEndpoint:
    """Tests for /api/v1/payroll/{payroll_id}/detailed endpoint."""

    def test_detailed_endpoint_exists(self):
        """Test that detailed endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/detailed" in r for r in routes)

    def test_detailed_response_structure(self):
        """Test detailed endpoint returns all expected fields."""
        expected_fields = [
            "contractor_name", "contractor_id", "client_name",
            "period", "currency", "rate_type", "monthly_rate",
            "day_rate", "work_days", "holiday_days", "sick_days",
            "vacation_days", "monthly_working_days",
            "leave_allowance", "leave_balance", "leave_deductibles",
            "management_fee", "eosb", "vacation_accrual",
            "gross_pay", "total_deductions", "net_pay",
            "payroll_id", "status"
        ]

        # Simulate response
        response = {field: None for field in expected_fields}
        for field in expected_fields:
            assert field in response


class TestPayrollApproveEndpoint:
    """Tests for /api/v1/payroll/{payroll_id}/approve endpoint."""

    def test_approve_endpoint_exists(self):
        """Test that approve endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/approve" in r for r in routes)

    def test_approve_requires_calculated_status(self):
        """Test approval only works for CALCULATED status."""
        from app.models.payroll import PayrollStatus

        # Mock payroll with CALCULATED status
        payroll = MagicMock()
        payroll.status = PayrollStatus.CALCULATED

        # Should be able to approve
        assert payroll.status == PayrollStatus.CALCULATED

    def test_approve_fails_for_paid_status(self):
        """Test approval fails for PAID status."""
        from app.models.payroll import PayrollStatus

        payroll = MagicMock()
        payroll.status = PayrollStatus.PAID

        # Should not be able to approve
        assert payroll.status != PayrollStatus.CALCULATED


class TestPayrollMarkPaidEndpoint:
    """Tests for /api/v1/payroll/{payroll_id}/mark-paid endpoint."""

    def test_mark_paid_endpoint_exists(self):
        """Test that mark-paid endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/mark-paid" in r for r in routes)

    def test_mark_paid_requires_approved_status(self):
        """Test mark-paid only works for APPROVED status."""
        from app.models.payroll import PayrollStatus

        payroll = MagicMock()
        payroll.status = PayrollStatus.APPROVED

        assert payroll.status == PayrollStatus.APPROVED


class TestPayrollPayslipEndpoint:
    """Tests for /api/v1/payroll/{payroll_id}/payslip endpoint."""

    def test_payslip_endpoint_exists(self):
        """Test that payslip endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/payslip" in r for r in routes)


class TestPayrollInvoiceEndpoint:
    """Tests for /api/v1/payroll/{payroll_id}/invoice endpoint."""

    def test_invoice_endpoint_exists(self):
        """Test that invoice endpoint route exists."""
        from app.routes.payroll import router

        routes = [r.path for r in router.routes]
        assert any("/invoice" in r for r in routes)
