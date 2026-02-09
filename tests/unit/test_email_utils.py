"""
Unit tests for email utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestEmailUtilFunctions:
    """Tests for email utility functions in app/utils/email.py."""

    @pytest.fixture
    def mock_lambda_client(self):
        """Mock boto3 Lambda client."""
        with patch("app.utils.email._get_lambda_client") as mock:
            client = MagicMock()
            client.invoke = MagicMock(return_value={"StatusCode": 202})
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Lambda function name."""
        with patch("app.utils.email.settings") as mock:
            mock.email_lambda_function_name = "test-email-lambda"
            mock.frontend_url = "http://localhost:3000"
            mock.contract_signing_url = "http://localhost:3000/contract/sign"
            mock.password_reset_url = "http://localhost:3000/reset-password"
            mock.company_name = "Aventus HR"
            mock.from_email = "noreply@aventushr.com"
            yield mock

    def test_send_contract_email(self, mock_lambda_client, mock_settings):
        """Test send_contract_email function."""
        from app.utils.email import send_contract_email

        result = send_contract_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            contract_token="test-token",
            expiry_date=datetime.utcnow() + timedelta(hours=48),
        )

        assert result is True
        mock_lambda_client.invoke.assert_called_once()

    def test_send_activation_email(self, mock_lambda_client, mock_settings):
        """Test send_activation_email function."""
        from app.utils.email import send_activation_email

        result = send_activation_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            temporary_password="TempPass123!",
        )

        assert result is True

    def test_send_document_upload_email(self, mock_lambda_client, mock_settings):
        """Test send_document_upload_email function."""
        from app.utils.email import send_document_upload_email

        result = send_document_upload_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            upload_token="upload-token",
            expiry_date=datetime.utcnow() + timedelta(days=7),
        )

        assert result is True

    def test_send_password_reset_email(self, mock_lambda_client, mock_settings):
        """Test send_password_reset_email function."""
        from app.utils.email import send_password_reset_email

        result = send_password_reset_email(
            email="test@example.com",
            name="John Doe",
            reset_token="reset-token",
            expiry_date=datetime.utcnow() + timedelta(hours=1),
        )

        assert result is True

    def test_send_cohf_email(self, mock_lambda_client, mock_settings):
        """Test send_cohf_email function."""
        from app.utils.email import send_cohf_email

        result = send_cohf_email(
            third_party_email="thirdparty@example.com",
            third_party_name="Third Party Co",
            contractor_name="John Doe",
            cohf_token="cohf-token",
            expiry_date=datetime.utcnow() + timedelta(hours=72),
        )

        assert result is True

    def test_send_quote_sheet_request_email(self, mock_lambda_client, mock_settings):
        """Test send_quote_sheet_request_email function."""
        from app.utils.email import send_quote_sheet_request_email

        result = send_quote_sheet_request_email(
            third_party_email="thirdparty@example.com",
            third_party_name="Third Party Co",
            contractor_name="John Doe",
            quote_token="quote-token",
            expiry_date=datetime.utcnow() + timedelta(hours=72),
        )

        assert result is True

    def test_send_work_order_to_client(self, mock_lambda_client, mock_settings):
        """Test send_work_order_to_client function."""
        from app.utils.email import send_work_order_to_client

        result = send_work_order_to_client(
            client_email="client@example.com",
            client_name="Acme Corp",
            contractor_name="John Doe",
            work_order_token="wo-token",
            expiry_date=datetime.utcnow() + timedelta(hours=48),
        )

        assert result is True

    def test_send_email_failure(self, mock_settings):
        """Test email sending failure when Lambda invocation fails."""
        with patch("app.utils.email._get_lambda_client") as mock:
            client = MagicMock()
            client.invoke = MagicMock(side_effect=Exception("Connection failed"))
            mock.return_value = client

            from app.utils.email import send_contract_email

            result = send_contract_email(
                contractor_email="test@example.com",
                contractor_name="John Doe",
                contract_token="test-token",
                expiry_date=datetime.utcnow() + timedelta(hours=48),
            )

            assert result is False

    def test_missing_lambda_function_name(self):
        """Test that missing Lambda function name returns False."""
        with patch("app.utils.email.settings") as mock_settings:
            mock_settings.email_lambda_function_name = ""
            mock_settings.frontend_url = "http://localhost:3000"
            mock_settings.contract_signing_url = "http://localhost:3000/contract/sign"

            from app.utils.email import send_contract_email

            result = send_contract_email(
                contractor_email="test@example.com",
                contractor_name="John Doe",
                contract_token="test-token",
                expiry_date=datetime.utcnow() + timedelta(hours=48),
            )

            assert result is False
