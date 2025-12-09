"""
Base PDF generator.

Provides common PDF generation functionality using ReportLab.
All document-specific generators inherit from this class.
"""
from abc import abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.adapters.pdf.interface import IPDFGenerator, PDFResult
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class BasePDFGenerator(IPDFGenerator):
    """
    Base PDF generator with shared functionality.

    Provides:
    - Common styles and formatting
    - Header/footer generation
    - Table creation utilities
    - Signature embedding
    - Error handling

    Subclasses implement build_content() for document-specific content.
    """

    # Page settings
    PAGE_SIZE = A4
    MARGIN_LEFT = 0.75 * inch
    MARGIN_RIGHT = 0.75 * inch
    MARGIN_TOP = 0.75 * inch
    MARGIN_BOTTOM = 0.75 * inch

    # Colors
    PRIMARY_COLOR = colors.HexColor("#FF6B00")  # Aventus orange
    SECONDARY_COLOR = colors.HexColor("#1a1a1a")
    LIGHT_GRAY = colors.HexColor("#f5f5f5")
    BORDER_COLOR = colors.HexColor("#e0e0e0")

    def __init__(self):
        """Initialize base generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name="DocumentTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=20,
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=12,
            textColor=self.SECONDARY_COLOR,
            spaceBefore=15,
            spaceAfter=10,
            fontName="Helvetica-Bold",
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name="BodyText",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
        ))

        # Small text
        self.styles.add(ParagraphStyle(
            name="SmallText",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=colors.gray,
        ))

        # Field label
        self.styles.add(ParagraphStyle(
            name="FieldLabel",
            parent=self.styles["Normal"],
            fontSize=9,
            textColor=colors.gray,
        ))

        # Field value
        self.styles.add(ParagraphStyle(
            name="FieldValue",
            parent=self.styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
        ))

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        """Generate PDF document."""
        try:
            # Validate data
            missing = self.validate_data(data)
            if missing:
                return PDFResult(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}",
                )

            # Create PDF buffer
            buffer = BytesIO()

            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.PAGE_SIZE,
                leftMargin=self.MARGIN_LEFT,
                rightMargin=self.MARGIN_RIGHT,
                topMargin=self.MARGIN_TOP,
                bottomMargin=self.MARGIN_BOTTOM,
            )

            # Build content
            elements = []
            elements.extend(self.build_header(data))
            elements.extend(self.build_content(data))
            elements.extend(self.build_footer(data))

            # Generate PDF
            doc.build(elements)

            # Get content
            pdf_content = buffer.getvalue()
            buffer.close()

            # Generate filename
            filename = self.generate_filename(data)

            logger.info(
                f"PDF generated successfully",
                extra={
                    "document_type": self.document_type,
                    "size": len(pdf_content),
                }
            )

            return PDFResult(
                success=True,
                content=pdf_content,
                filename=filename,
            )

        except Exception as e:
            logger.error(
                f"PDF generation failed",
                extra={
                    "document_type": self.document_type,
                    "error": str(e),
                }
            )
            return PDFResult(
                success=False,
                error=str(e),
            )

    def generate_with_signature(
        self,
        data: Dict[str, Any],
        signature: bytes,
        signature_position: Optional[Dict[str, int]] = None,
    ) -> PDFResult:
        """Generate PDF with embedded signature."""
        # Add signature to data for content building
        data["_signature"] = signature
        data["_signature_position"] = signature_position or {
            "x": 100,
            "y": 150,
            "width": 150,
            "height": 50,
        }

        return self.generate(data)

    def build_header(self, data: Dict[str, Any]) -> List:
        """
        Build document header.

        Override in subclasses for custom headers.
        """
        elements = []

        # Add logo if available
        logo_path = data.get("logo_path") or settings.logo_path
        if logo_path:
            try:
                logo = Image(logo_path, width=1.5 * inch, height=0.5 * inch)
                elements.append(logo)
            except Exception:
                pass

        elements.append(Spacer(1, 10))
        return elements

    @abstractmethod
    def build_content(self, data: Dict[str, Any]) -> List:
        """
        Build document-specific content.

        Must be implemented by subclasses.
        """
        pass

    def build_footer(self, data: Dict[str, Any]) -> List:
        """
        Build document footer.

        Override in subclasses for custom footers.
        """
        elements = []
        elements.append(Spacer(1, 30))

        # Footer text
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        elements.append(Paragraph(footer_text, self.styles["SmallText"]))

        return elements

    def generate_filename(self, data: Dict[str, Any]) -> str:
        """Generate suggested filename for the PDF."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.document_type}_{timestamp}.pdf"

    # Utility methods for building content

    def create_field_row(
        self,
        label: str,
        value: Any,
        label_width: float = 2 * inch,
    ) -> Table:
        """Create a label-value row."""
        data = [[
            Paragraph(label, self.styles["FieldLabel"]),
            Paragraph(str(value or "N/A"), self.styles["FieldValue"]),
        ]]

        table = Table(data, colWidths=[label_width, None])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        return table

    def create_section_table(
        self,
        title: str,
        fields: List[Tuple[str, Any]],
        columns: int = 2,
    ) -> List:
        """Create a section with multiple fields in a grid."""
        elements = []

        # Section title
        elements.append(Paragraph(title, self.styles["SectionHeader"]))

        # Build rows
        rows = []
        current_row = []

        for label, value in fields:
            current_row.append(Paragraph(label, self.styles["FieldLabel"]))
            current_row.append(Paragraph(str(value or "N/A"), self.styles["FieldValue"]))

            if len(current_row) >= columns * 2:
                rows.append(current_row)
                current_row = []

        # Add remaining fields
        if current_row:
            # Pad with empty cells
            while len(current_row) < columns * 2:
                current_row.append("")
            rows.append(current_row)

        if rows:
            col_width = (self.PAGE_SIZE[0] - self.MARGIN_LEFT - self.MARGIN_RIGHT) / (columns * 2)
            table = Table(rows, colWidths=[col_width] * (columns * 2))
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(table)

        elements.append(Spacer(1, 10))
        return elements

    def create_signature_block(
        self,
        title: str,
        signature: Optional[bytes] = None,
        date: Optional[str] = None,
    ) -> List:
        """Create a signature block."""
        elements = []

        elements.append(Spacer(1, 20))
        elements.append(Paragraph(title, self.styles["SectionHeader"]))

        # Signature line
        sig_data = [["Signature:", "_" * 40, "Date:", date or "_" * 20]]

        if signature:
            try:
                sig_buffer = BytesIO(signature)
                sig_image = Image(sig_buffer, width=2 * inch, height=0.75 * inch)
                sig_data = [["Signature:", sig_image, "Date:", date or "_" * 20]]
            except Exception:
                pass

        table = Table(sig_data, colWidths=[1 * inch, 2.5 * inch, 0.75 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)

        return elements

    def create_info_box(
        self,
        content: str,
        bg_color: Optional[colors.Color] = None,
    ) -> Table:
        """Create an info/notice box."""
        bg = bg_color or self.LIGHT_GRAY

        data = [[Paragraph(content, self.styles["BodyText"])]]
        table = Table(data, colWidths=[None])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 15),
            ("RIGHTPADDING", (0, 0), (-1, -1), 15),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))

        return table
