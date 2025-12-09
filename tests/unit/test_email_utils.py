"""
Unit tests for email utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestEmailUtilFunctions:
    """Tests for email utility functions in app/utils/email.py."""

    @pytest.fixture
    def mock_resend(self):
        """Mock resend module."""
        with patch("app.utils.email.resend") as mock:
            mock.Emails.send = MagicMock(return_value={"id": "msg-123"})
            yield mock

    @pytest.fixture
    def mock_template_env(self):
        """Mock template environment."""
        with patch("app.utils.email._env") as mock:
            template = MagicMock()
            template.render = MagicMock(return_value="<html>Test</html>")
            mock.get_template = MagicMock(return_value=template)
            yield mock

    def test_send_contract_email(self, mock_resend, mock_template_env):
        """Test send_contract_email function."""
        from app.utils.email import send_contract_email

        result = send_contract_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            contract_token="test-token",
            expiry_date=datetime.utcnow() + timedelta(hours=48),
        )

        assert result is True
        mock_resend.Emails.send.assert_called_once()

    def test_send_activation_email(self, mock_resend, mock_template_env):
        """Test send_activation_email function."""
        from app.utils.email import send_activation_email

        result = send_activation_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            temporary_password="TempPass123!",
        )

        assert result is True

    def test_send_document_upload_email(self, mock_resend, mock_template_env):
        """Test send_document_upload_email function."""
        from app.utils.email import send_document_upload_email

        result = send_document_upload_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            upload_token="upload-token",
            expiry_date=datetime.utcnow() + timedelta(days=7),
        )

        assert result is True

    def test_send_password_reset_email(self, mock_resend, mock_template_env):
        """Test send_password_reset_email function."""
        from app.utils.email import send_password_reset_email

        result = send_password_reset_email(
            email="test@example.com",
            name="John Doe",
            reset_token="reset-token",
            expiry_date=datetime.utcnow() + timedelta(hours=1),
        )

        assert result is True

    def test_send_cohf_email(self, mock_resend, mock_template_env):
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

    def test_send_quote_sheet_request_email(self, mock_resend, mock_template_env):
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

    def test_send_work_order_to_client(self, mock_resend, mock_template_env):
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

    def test_send_email_failure(self, mock_template_env):
        """Test email sending failure."""
        with patch("app.utils.email.resend") as mock_resend:
            mock_resend.Emails.send = MagicMock(side_effect=Exception("Connection failed"))

            from app.utils.email import send_contract_email

            result = send_contract_email(
                contractor_email="test@example.com",
                contractor_name="John Doe",
                contract_token="test-token",
                expiry_date=datetime.utcnow() + timedelta(hours=48),
            )

            assert result is False


class TestRenderTemplate:
    """Tests for _render_template function."""

    def test_render_template_includes_defaults(self):
        """Test that render includes default context."""
        from app.utils.email import _render_template

        # This should not raise an error
        html = _render_template(
            "document_upload",
            contractor_name="John",
            upload_link="https://example.com/upload",
            expiry_date="Jan 15, 2025",
        )

        assert html is not None
        assert "John" in html
