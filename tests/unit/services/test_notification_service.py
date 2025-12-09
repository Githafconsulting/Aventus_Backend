"""
Unit tests for NotificationService.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

from app.services.notification_service import NotificationService
from app.adapters.email.resend_adapter import MockEmailSender
from app.adapters.email.interface import EmailResult


class TestNotificationServiceSetup:
    """Tests for NotificationService initialization."""

    def test_service_initialization(self, mock_email_sender, mock_template_engine):
        """Test service initializes with dependencies."""
        service = NotificationService(mock_email_sender, mock_template_engine)
        assert service.email == mock_email_sender
        assert service.templates == mock_template_engine


class TestDocumentUploadEmail:
    """Tests for send_document_upload_email."""

    @pytest.mark.asyncio
    async def test_send_document_upload_email_success(self, notification_service, mock_email_sender):
        """Test sending document upload email."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_document_upload_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            upload_token="test-token",
            expiry_date=datetime.utcnow() + timedelta(days=7),
        )

        assert result is True
        mock_email_sender.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_document_upload_email_failure(self, notification_service, mock_email_sender):
        """Test document upload email failure."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=False, error="Failed"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_document_upload_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            upload_token="test-token",
            expiry_date=datetime.utcnow() + timedelta(days=7),
        )

        assert result is False


class TestContractSigningEmail:
    """Tests for send_contract_signing_email."""

    @pytest.mark.asyncio
    async def test_send_contract_signing_email_success(self, notification_service, mock_email_sender):
        """Test sending contract signing email."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_contract_signing_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            contract_token="contract-token",
            expiry_date=datetime.utcnow() + timedelta(hours=48),
        )

        assert result is True


class TestActivationEmail:
    """Tests for send_activation_email."""

    @pytest.mark.asyncio
    async def test_send_activation_email_success(self, notification_service, mock_email_sender):
        """Test sending activation email."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_activation_email(
            contractor_email="test@example.com",
            contractor_name="John Doe",
            temporary_password="TempPass123!",
        )

        assert result is True


class TestDocumentsUploadedNotification:
    """Tests for send_documents_uploaded_notification."""

    @pytest.mark.asyncio
    async def test_send_documents_uploaded_notification(self, notification_service, mock_email_sender):
        """Test sending documents uploaded notification."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_documents_uploaded_notification(
            admin_email="admin@example.com",
            contractor_name="John Doe",
            contractor_id=1,
        )

        assert result is True


class TestCOHFSignatureRequest:
    """Tests for send_cohf_signature_request."""

    @pytest.mark.asyncio
    async def test_send_cohf_signature_request(self, notification_service, mock_email_sender):
        """Test sending COHF signature request."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_cohf_signature_request(
            third_party_email="thirdparty@example.com",
            third_party_name="Third Party Co",
            contractor_name="John Doe",
            cohf_token="cohf-token",
            expiry_date=datetime.utcnow() + timedelta(hours=72),
        )

        assert result is True


class TestQuoteSheetRequest:
    """Tests for send_quote_sheet_request."""

    @pytest.mark.asyncio
    async def test_send_quote_sheet_request(self, notification_service, mock_email_sender):
        """Test sending quote sheet request."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_quote_sheet_request(
            third_party_email="thirdparty@example.com",
            third_party_name="Third Party Co",
            contractor_name="John Doe",
            quote_token="quote-token",
            expiry_date=datetime.utcnow() + timedelta(hours=72),
        )

        assert result is True


class TestWorkOrderEmail:
    """Tests for send_work_order_email."""

    @pytest.mark.asyncio
    async def test_send_work_order_email(self, notification_service, mock_email_sender):
        """Test sending work order email."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_work_order_email(
            client_email="client@example.com",
            client_name="Acme Corp",
            contractor_name="John Doe",
            work_order_token="wo-token",
            expiry_date=datetime.utcnow() + timedelta(hours=48),
        )

        assert result is True


class TestPasswordResetEmail:
    """Tests for send_password_reset_email."""

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, notification_service, mock_email_sender):
        """Test sending password reset email."""
        mock_email_sender.send = AsyncMock(return_value=EmailResult(success=True, message_id="123"))
        notification_service.email = mock_email_sender

        result = await notification_service.send_password_reset_email(
            email="test@example.com",
            name="John Doe",
            reset_token="reset-token",
            expiry_date=datetime.utcnow() + timedelta(hours=1),
        )

        assert result is True
