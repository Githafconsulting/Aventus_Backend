"""
Client Invoice PDF generator - Consolidated invoices (one per client per period).
Professional design matching existing payroll invoice style.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


# Brand colors
ORANGE = colors.HexColor('#FF6B00')
BLACK = colors.HexColor('#111111')
DARK_TEXT = colors.HexColor('#333333')
LIGHT_TEXT = colors.HexColor('#666666')
BORDER_COLOR = colors.HexColor('#DDDDDD')
BG_LIGHT = colors.HexColor('#F8F8F8')
WHITE = colors.white


def _add_logo(elements):
    """Add Aventus logo to PDF."""
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=40*mm, height=10*mm, kind='proportional')
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 5*mm))


def _fmt(amount, currency="AED"):
    """Format a number as currency."""
    if amount is None:
        return "0.00"
    return f"{currency} {amount:,.2f}"


def generate_client_invoice_pdf(invoice, client, line_items) -> BytesIO:
    """
    Generate a consolidated client invoice PDF.

    Args:
        invoice: ClientInvoice model instance
        client: Client model instance
        line_items: list of ClientInvoiceLineItem instances

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'],
        fontSize=22, textColor=ORANGE, spaceAfter=2*mm,
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle', parent=styles['Normal'],
        fontSize=10, textColor=LIGHT_TEXT, spaceAfter=5*mm,
    )
    header_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        fontSize=12, textColor=DARK_TEXT, spaceBefore=5*mm, spaceAfter=3*mm,
    )
    normal_style = ParagraphStyle(
        'InvoiceNormal', parent=styles['Normal'],
        fontSize=9, textColor=DARK_TEXT,
    )
    right_style = ParagraphStyle(
        'InvoiceRight', parent=styles['Normal'],
        fontSize=9, textColor=DARK_TEXT, alignment=TA_RIGHT,
    )
    bold_style = ParagraphStyle(
        'InvoiceBold', parent=styles['Normal'],
        fontSize=9, textColor=BLACK, fontName='Helvetica-Bold',
    )

    # Logo
    _add_logo(elements)

    # Title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Paragraph(f"Invoice No: {invoice.invoice_number}", subtitle_style))

    # Invoice details + Client info (side by side)
    invoice_date = invoice.invoice_date.strftime("%B %d, %Y") if invoice.invoice_date else "N/A"
    due_date = invoice.due_date.strftime("%B %d, %Y") if invoice.due_date else "N/A"

    client_name = client.company_name if client else "N/A"
    client_address = ""
    if client:
        addr_parts = [client.address_line1, client.address_line2, client.address_line3, client.address_line4]
        client_address = "<br/>".join(p for p in addr_parts if p)

    left_info = [
        [Paragraph("<b>From:</b>", normal_style)],
        [Paragraph("Aventus Global Solutions", bold_style)],
        [Paragraph("", normal_style)],
        [Paragraph(f"<b>Invoice Date:</b> {invoice_date}", normal_style)],
        [Paragraph(f"<b>Due Date:</b> {due_date}", normal_style)],
        [Paragraph(f"<b>Payment Terms:</b> {invoice.payment_terms or 'Net 30'}", normal_style)],
        [Paragraph(f"<b>Period:</b> {invoice.period}", normal_style)],
    ]
    right_info = [
        [Paragraph("<b>Bill To:</b>", normal_style)],
        [Paragraph(client_name, bold_style)],
        [Paragraph(client_address, normal_style)] if client_address else [Paragraph("", normal_style)],
        [Paragraph("", normal_style)],
        [Paragraph("", normal_style)],
        [Paragraph("", normal_style)],
        [Paragraph("", normal_style)],
    ]

    info_table = Table(
        [[left_info[i][0], right_info[i][0]] for i in range(len(left_info))],
        colWidths=[85*mm, 85*mm],
    )
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # Line items table
    elements.append(Paragraph("Line Items", header_style))

    currency = invoice.currency or "AED"
    header_row = [
        Paragraph("<b>#</b>", normal_style),
        Paragraph("<b>Contractor</b>", normal_style),
        Paragraph("<b>Description</b>", normal_style),
        Paragraph("<b>Subtotal</b>", right_style),
        Paragraph("<b>VAT</b>", right_style),
        Paragraph("<b>Total</b>", right_style),
    ]
    table_data = [header_row]

    for i, item in enumerate(line_items, 1):
        table_data.append([
            Paragraph(str(i), normal_style),
            Paragraph(item.contractor_name or "N/A", normal_style),
            Paragraph(item.description or "", normal_style),
            Paragraph(_fmt(item.subtotal, currency), right_style),
            Paragraph(_fmt(item.vat_amount, currency), right_style),
            Paragraph(_fmt(item.total, currency), right_style),
        ])

    col_widths = [10*mm, 40*mm, 45*mm, 28*mm, 25*mm, 28*mm]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        # Rows
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))

    # Totals
    totals_data = [
        [Paragraph("<b>Subtotal:</b>", right_style), Paragraph(_fmt(invoice.subtotal, currency), right_style)],
        [Paragraph(f"<b>VAT ({invoice.vat_rate * 100:.0f}%):</b>", right_style), Paragraph(_fmt(invoice.vat_amount, currency), right_style)],
        [Paragraph("<b>Total Amount:</b>", right_style), Paragraph(f"<b>{_fmt(invoice.total_amount, currency)}</b>", right_style)],
    ]

    if invoice.amount_paid and invoice.amount_paid > 0:
        totals_data.append([
            Paragraph("<b>Amount Paid:</b>", right_style),
            Paragraph(_fmt(invoice.amount_paid, currency), right_style),
        ])
        totals_data.append([
            Paragraph("<b>Balance Due:</b>", right_style),
            Paragraph(f"<b>{_fmt(invoice.balance, currency)}</b>", right_style),
        ])

    totals_table = Table(totals_data, colWidths=[130*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEABOVE', (0, -1), (-1, -1), 1, ORANGE),
    ]))
    elements.append(totals_table)

    # Notes
    if invoice.notes:
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("Notes", header_style))
        elements.append(Paragraph(invoice.notes, normal_style))

    # Footer
    elements.append(Spacer(1, 15*mm))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=LIGHT_TEXT, alignment=TA_CENTER,
    )
    elements.append(Paragraph("Thank you for your business.", footer_style))
    elements.append(Paragraph("Aventus Global Solutions", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
