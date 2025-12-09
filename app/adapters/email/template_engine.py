"""
Email template engine.

Jinja2-based template rendering for emails.
"""
from pathlib import Path
from typing import Any, Tuple, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class EmailTemplateEngine:
    """
    Jinja2-based email template rendering engine.

    Features:
    - Template inheritance (base + specific templates)
    - Component reuse (header, footer, buttons)
    - Auto-escaping for security
    - Default context (company name, logo)

    Usage:
        engine = EmailTemplateEngine()
        html = engine.render("contract_signing", contractor_name="John")
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template engine.

        Args:
            template_dir: Path to templates directory (optional)
        """
        if template_dir is None:
            # Default to app/templates
            template_dir = Path(__file__).parent.parent.parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters["currency"] = self._currency_filter
        self.env.filters["date_format"] = self._date_format_filter

    @staticmethod
    def _currency_filter(value: float, currency: str = "USD") -> str:
        """Format number as currency."""
        symbols = {"USD": "$", "AED": "AED ", "SAR": "SAR ", "EUR": "€", "GBP": "£"}
        symbol = symbols.get(currency, currency + " ")
        return f"{symbol}{value:,.2f}"

    @staticmethod
    def _date_format_filter(value, format: str = "%B %d, %Y") -> str:
        """Format datetime object."""
        if hasattr(value, "strftime"):
            return value.strftime(format)
        return str(value)

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render an email template.

        Args:
            template_name: Template name (without path/extension)
            **context: Variables to pass to template

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(f"email/{template_name}.html")
        except TemplateNotFound:
            logger.error(f"Email template not found: {template_name}")
            raise

        # Merge with default context
        full_context = self._get_default_context()
        full_context.update(context)

        return template.render(**full_context)

    def render_with_subject(
        self,
        template_name: str,
        subject: str,
        **context: Any
    ) -> Tuple[str, str]:
        """
        Render template and return subject + HTML.

        Args:
            template_name: Template name
            subject: Email subject
            **context: Template variables

        Returns:
            Tuple of (subject, html_content)
        """
        html = self.render(template_name, subject=subject, **context)
        return subject, html

    def _get_default_context(self) -> dict:
        """Get default context for all templates."""
        return {
            "company_name": settings.company_name,
            "logo_url": settings.logo_url,
            "frontend_url": settings.frontend_url,
            "support_email": settings.support_email,
            "current_year": 2025,
        }

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            self.env.get_template(f"email/{template_name}.html")
            return True
        except TemplateNotFound:
            return False


# Singleton instance for reuse
_email_template_engine: Optional[EmailTemplateEngine] = None


def get_email_template_engine() -> EmailTemplateEngine:
    """Get or create the email template engine singleton."""
    global _email_template_engine
    if _email_template_engine is None:
        _email_template_engine = EmailTemplateEngine()
    return _email_template_engine


# Convenience alias
email_template_engine = get_email_template_engine()
