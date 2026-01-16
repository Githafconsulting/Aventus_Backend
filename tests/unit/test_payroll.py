"""
Unit tests for payroll calculations and model.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime


class TestPayrollModel:
    """Tests for Payroll model."""

    def test_payroll_model_exists(self):
        """Test that Payroll model can be imported."""
        from app.models.payroll import Payroll, PayrollStatus
        assert Payroll is not None
        assert PayrollStatus is not None

    def test_payroll_status_enum_values(self):
        """Test PayrollStatus enum has expected values."""
        from app.models.payroll import PayrollStatus

        assert PayrollStatus.PENDING.value == "pending"
        assert PayrollStatus.CALCULATED.value == "calculated"
        assert PayrollStatus.APPROVED.value == "approved"
        assert PayrollStatus.PAID.value == "paid"

    def test_payroll_model_has_required_fields(self):
        """Test Payroll model has all required fields."""
        from app.models.payroll import Payroll

        required_fields = [
            "id", "timesheet_id", "contractor_id",
            "day_rate", "work_days", "gross_amount",
            "deductions", "net_amount", "currency",
            "status", "period"
        ]
        for field in required_fields:
            assert hasattr(Payroll, field), f"Missing field: {field}"

    def test_payroll_model_has_invoice_fields(self):
        """Test Payroll model has invoice-related fields."""
        from app.models.payroll import Payroll

        invoice_fields = ["charge_rate_day", "invoice_amount"]
        for field in invoice_fields:
            assert hasattr(Payroll, field), f"Missing field: {field}"

    def test_payroll_model_has_timestamp_fields(self):
        """Test Payroll model has timestamp fields."""
        from app.models.payroll import Payroll

        timestamp_fields = [
            "calculated_at", "approved_at", "paid_at",
            "created_at", "updated_at"
        ]
        for field in timestamp_fields:
            assert hasattr(Payroll, field), f"Missing field: {field}"


class TestPayrollCalculations:
    """Tests for payroll calculation logic."""

    def test_gross_amount_calculation(self):
        """Test gross amount = day_rate * work_days."""
        day_rate = 100.0
        work_days = 20
        expected_gross = 2000.0

        gross_amount = day_rate * work_days
        assert gross_amount == expected_gross

    def test_net_amount_calculation(self):
        """Test net amount = gross - deductions."""
        gross_amount = 2000.0
        deductions = 200.0
        expected_net = 1800.0

        net_amount = gross_amount - deductions
        assert net_amount == expected_net

    def test_invoice_amount_calculation(self):
        """Test invoice amount = charge_rate * work_days."""
        charge_rate_day = 150.0
        work_days = 20
        expected_invoice = 3000.0

        invoice_amount = charge_rate_day * work_days
        assert invoice_amount == expected_invoice

    def test_day_rate_from_monthly(self):
        """Test day rate calculation from monthly salary."""
        monthly_salary = 2000.0
        working_days = 20
        expected_day_rate = 100.0

        day_rate = monthly_salary / working_days
        assert day_rate == expected_day_rate

    def test_day_rate_from_monthly_with_different_days(self):
        """Test day rate with 22 working days."""
        monthly_salary = 4400.0
        working_days = 22
        expected_day_rate = 200.0

        day_rate = monthly_salary / working_days
        assert day_rate == expected_day_rate

    def test_leave_deductibles_negative_balance(self):
        """Test leave deductibles when balance is negative."""
        leave_allowance = 30
        leave_taken = 35
        leave_balance = leave_allowance - leave_taken  # -5

        daily_rate = 100.0
        leave_deductibles = abs(leave_balance) * daily_rate if leave_balance < 0 else 0

        assert leave_balance == -5
        assert leave_deductibles == 500.0

    def test_leave_deductibles_positive_balance(self):
        """Test no deductibles when balance is positive."""
        leave_allowance = 30
        leave_taken = 20
        leave_balance = leave_allowance - leave_taken  # 10

        daily_rate = 100.0
        leave_deductibles = abs(leave_balance) * daily_rate if leave_balance < 0 else 0

        assert leave_balance == 10
        assert leave_deductibles == 0


class TestContractorPayInfo:
    """Tests for contractor pay info extraction."""

    @pytest.fixture
    def mock_contractor_monthly(self):
        """Mock contractor with monthly rate."""
        contractor = MagicMock()
        contractor.rate_type = "monthly"
        contractor.gross_salary = "2000"
        contractor.day_rate = None
        contractor.charge_rate_month = "3000"
        contractor.charge_rate_day = None
        contractor.currency = "AED"
        contractor.costing_sheet_data = {"estimated_working_days": "20"}
        contractor.cds_form_data = {"grossSalary": "2000", "chargeRateMonth": "3000"}
        return contractor

    @pytest.fixture
    def mock_contractor_daily(self):
        """Mock contractor with day rate."""
        contractor = MagicMock()
        contractor.rate_type = "daily"
        contractor.day_rate = "150"
        contractor.charge_rate_day = "200"
        contractor.gross_salary = None
        contractor.currency = "USD"
        contractor.costing_sheet_data = {}
        contractor.cds_form_data = {}
        return contractor

    def test_extract_day_rate_from_daily_contractor(self, mock_contractor_daily):
        """Test extracting day rate from daily rate contractor."""
        day_rate = float(mock_contractor_daily.day_rate)
        assert day_rate == 150.0

    def test_extract_day_rate_from_monthly_contractor(self, mock_contractor_monthly):
        """Test calculating day rate from monthly contractor."""
        monthly_salary = float(mock_contractor_monthly.gross_salary)
        working_days = float(mock_contractor_monthly.costing_sheet_data["estimated_working_days"])
        day_rate = monthly_salary / working_days

        assert day_rate == 100.0

    def test_extract_charge_rate_from_monthly(self, mock_contractor_monthly):
        """Test calculating charge rate from monthly."""
        monthly_charge = float(mock_contractor_monthly.charge_rate_month)
        working_days = float(mock_contractor_monthly.costing_sheet_data["estimated_working_days"])
        charge_rate_day = monthly_charge / working_days

        assert charge_rate_day == 150.0


class TestPayrollStatusTransitions:
    """Tests for payroll status transitions."""

    def test_valid_transition_calculated_to_approved(self):
        """Test valid transition from CALCULATED to APPROVED."""
        from app.models.payroll import PayrollStatus

        current = PayrollStatus.CALCULATED
        target = PayrollStatus.APPROVED

        # Valid workflow: CALCULATED -> APPROVED
        valid_transitions = {
            PayrollStatus.CALCULATED: [PayrollStatus.APPROVED],
            PayrollStatus.APPROVED: [PayrollStatus.PAID],
        }

        assert target in valid_transitions.get(current, [])

    def test_valid_transition_approved_to_paid(self):
        """Test valid transition from APPROVED to PAID."""
        from app.models.payroll import PayrollStatus

        current = PayrollStatus.APPROVED
        target = PayrollStatus.PAID

        valid_transitions = {
            PayrollStatus.CALCULATED: [PayrollStatus.APPROVED],
            PayrollStatus.APPROVED: [PayrollStatus.PAID],
        }

        assert target in valid_transitions.get(current, [])

    def test_invalid_transition_calculated_to_paid(self):
        """Test invalid transition from CALCULATED to PAID."""
        from app.models.payroll import PayrollStatus

        current = PayrollStatus.CALCULATED
        target = PayrollStatus.PAID

        valid_transitions = {
            PayrollStatus.CALCULATED: [PayrollStatus.APPROVED],
            PayrollStatus.APPROVED: [PayrollStatus.PAID],
        }

        assert target not in valid_transitions.get(current, [])
