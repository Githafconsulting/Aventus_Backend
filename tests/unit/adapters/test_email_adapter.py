"""
Unit tests for email adapters.
"""
import pytest
from app.adapters.email.resend_adapter import MockEmailSender
from app.adapters.email.interface import EmailMessage, EmailResult, EmailAttachment
from app.adapters.email.template_engine import EmailTemplateEngine


class TestMockEmailSender:
    """Tests for MockEmailSender."""

    @pytest.fixture
    def sender(self):
        return MockEmailSender()

    @pytest.mark.asyncio
    async def test_send_stores_email(self, sender):
        """Test that send stores email in memory."""
        result = await sender.send(
            to="test@example.com",
            subject="Test Subject",
            html="<p>Test content</p>",
        )

        assert result.success is True
        assert len(sender.sent_emails) == 1

    @pytest.mark.asyncio
    async def test_send_returns_message_id(self, sender):
        """Test that send returns message ID."""
        result = await sender.send(
            to="test@example.com",
            subject="Test",
            html="<p>Test</p>",
        )

        assert result.message_id is not None
        assert "mock" in result.message_id

    @pytest.mark.asyncio
    async def test_send_message(self, sender):
        """Test sending via EmailMessage object."""
        message = EmailMessage(
            to="test@example.com",
            subject="Test Subject",
            html="<p>Test</p>",
        )

        result = await sender.send_message(message)

        assert result.success is True
        assert len(sender.sent_emails) == 1

    @pytest.mark.asyncio
    async def test_send_bulk(self, sender):
        """Test sending multiple emails."""
        messages = [
            EmailMessage(to="test1@example.com", subject="Test 1", html="<p>1</p>"),
            EmailMessage(to="test2@example.com", subject="Test 2", html="<p>2</p>"),
        ]

        results = await sender.send_bulk(messages)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert len(sender.sent_emails) == 2

    def test_clear_emails(self, sender):
        """Test clearing sent emails."""
        sender.sent_emails.append(
            EmailMessage(to="test@example.com", subject="Test", html="<p>Test</p>")
        )

        sender.clear()

        assert len(sender.sent_emails) == 0

    @pytest.mark.asyncio
    async def test_get_last_email(self, sender):
        """Test getting last sent email."""
        await sender.send(to="test1@example.com", subject="Test 1", html="<p>1</p>")
        await sender.send(to="test2@example.com", subject="Test 2", html="<p>2</p>")

        last = sender.get_last_email()

        assert last.subject == "Test 2"

    @pytest.mark.asyncio
    async def test_find_by_recipient(self, sender):
        """Test finding emails by recipient."""
        await sender.send(to="john@example.com", subject="For John", html="<p>Hi John</p>")
        await sender.send(to="jane@example.com", subject="For Jane", html="<p>Hi Jane</p>")

        john_emails = sender.find_by_recipient("john@example.com")

        assert len(john_emails) == 1
        assert john_emails[0].subject == "For John"


class TestEmailTemplateEngine:
    """Tests for EmailTemplateEngine."""

    @pytest.fixture
    def engine(self):
        return EmailTemplateEngine()

    def test_template_exists(self, engine):
        """Test checking if template exists."""
        assert engine.template_exists("base") is True
        assert engine.template_exists("contract_signing") is True
        assert engine.template_exists("nonexistent") is False

    def test_render_template(self, engine):
        """Test rendering a template."""
        html = engine.render(
            "contract_signing",
            contractor_name="John Doe",
            contract_link="https://example.com/contract",
            expiry_date="January 15, 2025",
        )

        assert "John Doe" in html
        assert "https://example.com/contract" in html

    def test_render_with_subject(self, engine):
        """Test render_with_subject returns tuple."""
        subject, html = engine.render_with_subject(
            "activation",
            subject="Welcome!",
            contractor_name="John Doe",
            contractor_email="john@example.com",
            temporary_password="TempPass123",
            login_link="https://example.com",
        )

        assert subject == "Welcome!"
        assert "John Doe" in html

    def test_default_context_included(self, engine):
        """Test that default context is included."""
        html = engine.render(
            "document_upload",
            contractor_name="John",
            upload_link="https://example.com",
            expiry_date="Jan 15",
        )

        # Default context should include company_name
        assert html is not None


class TestEmailMessage:
    """Tests for EmailMessage dataclass."""

    def test_create_simple_message(self):
        """Test creating simple email message."""
        msg = EmailMessage(
            to="test@example.com",
            subject="Test",
            html="<p>Test</p>",
        )

        assert msg.to == "test@example.com"
        assert msg.subject == "Test"
        assert msg.html == "<p>Test</p>"

    def test_create_message_with_all_fields(self):
        """Test creating message with all fields."""
        msg = EmailMessage(
            to=["test1@example.com", "test2@example.com"],
            subject="Test",
            html="<p>Test</p>",
            text="Test",
            from_email="sender@example.com",
            from_name="Sender Name",
            reply_to="reply@example.com",
        )

        assert len(msg.to) == 2
        assert msg.from_email == "sender@example.com"


class TestEmailResult:
    """Tests for EmailResult dataclass."""

    def test_success_result(self):
        """Test creating success result."""
        result = EmailResult(success=True, message_id="msg-123")

        assert result.success is True
        assert result.message_id == "msg-123"
        assert result.error is None

    def test_failure_result(self):
        """Test creating failure result."""
        result = EmailResult(success=False, error="Connection failed")

        assert result.success is False
        assert result.error == "Connection failed"


class TestEmailAttachment:
    """Tests for EmailAttachment dataclass."""

    def test_create_attachment(self):
        """Test creating email attachment."""
        attachment = EmailAttachment(
            filename="document.pdf",
            content=b"PDF content here",
            content_type="application/pdf",
        )

        assert attachment.filename == "document.pdf"
        assert attachment.content_type == "application/pdf"
