"""
Payroll PDF generators for payslips and invoices.
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


# Define colors
ORANGE = colors.HexColor('#FF6B00')
DARK_GRAY = colors.HexColor('#1F2937')
LIGHT_GRAY = colors.HexColor('#F3F4F6')
GREEN = colors.HexColor('#10B981')


def _add_logo(elements):
    """Add Aventus logo to PDF."""
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=12*mm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 3*mm))


def _get_styles():
    """Get common styles for PDF generation."""
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=ORANGE,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=DARK_GRAY,
        spaceAfter=4,
        spaceBefore=8,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=12,
        fontName='Helvetica'
    )

    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=8,
        leading=10,
    )

    return {
        'title': title_style,
        'section': section_style,
        'body': body_style,
        'small': small_style,
        'base': styles,
    }


def generate_payslip_pdf(payroll, contractor) -> BytesIO:
    """
    Generate a payslip PDF for a contractor.

    Args:
        payroll: Payroll model instance
        contractor: Contractor model instance

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    elements = []
    styles = _get_styles()

    # Add logo
    _add_logo(elements)

    # Title
    elements.append(Paragraph("PAYSLIP", styles['title']))
    elements.append(Paragraph(payroll.period or "Current Period", ParagraphStyle(
        'Subtitle',
        parent=styles['base']['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica'
    )))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[170*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, ORANGE),
    ])))
    elements.append(Spacer(1, 4*mm))

    # Employee Information
    contractor_name = f"{contractor.first_name} {contractor.surname}"
    info_data = [
        ['Employee:', contractor_name, 'Employee ID:', str(contractor.id)[:8]],
        ['Client:', contractor.client_name or 'N/A', 'Period:', payroll.period or 'N/A'],
        ['Currency:', payroll.currency, 'Pay Date:', datetime.now().strftime('%B %d, %Y')],
    ]

    info_table = Table(info_data, colWidths=[25*mm, 55*mm, 25*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK_GRAY),
        ('TEXTCOLOR', (2, 0), (2, -1), DARK_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Earnings Section
    elements.append(Paragraph("<b>Earnings</b>", styles['section']))

    earnings_data = [
        ['Description', 'Rate', 'Quantity', 'Amount'],
        ['Day Rate', f"{payroll.currency} {payroll.day_rate:,.2f}", f"{payroll.work_days} days", f"{payroll.currency} {payroll.gross_amount:,.2f}"],
    ]

    earnings_table = Table(earnings_data, colWidths=[60*mm, 40*mm, 30*mm, 40*mm])
    earnings_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        # Data
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 4*mm))

    # Deductions Section (if any)
    if payroll.deductions > 0:
        elements.append(Paragraph("<b>Deductions</b>", styles['section']))

        deductions_data = [
            ['Description', 'Amount'],
            ['Deductions', f"{payroll.currency} {payroll.deductions:,.2f}"],
        ]

        deductions_table = Table(deductions_data, colWidths=[130*mm, 40*mm])
        deductions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(deductions_table)
        elements.append(Spacer(1, 4*mm))

    # Net Pay Summary
    elements.append(Paragraph("<b>Payment Summary</b>", styles['section']))

    summary_data = [
        ['Gross Pay', f"{payroll.currency} {payroll.gross_amount:,.2f}"],
        ['Deductions', f"-{payroll.currency} {payroll.deductions:,.2f}"],
        ['Net Pay', f"{payroll.currency} {payroll.net_amount:,.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[130*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 1), LIGHT_GRAY),
        ('BACKGROUND', (0, 2), (-1, 2), GREEN),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, 2), (-1, 2), 1, DARK_GRAY),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6*mm))

    # Banking Details (if available)
    if contractor.contractor_bank_name or contractor.contractor_iban:
        elements.append(Paragraph("<b>Payment Details</b>", styles['section']))

        bank_info = []
        if contractor.contractor_bank_name:
            bank_info.append(['Bank Name:', contractor.contractor_bank_name])
        if contractor.contractor_account_name:
            bank_info.append(['Account Name:', contractor.contractor_account_name])
        if contractor.contractor_account_no:
            bank_info.append(['Account Number:', contractor.contractor_account_no])
        if contractor.contractor_iban:
            bank_info.append(['IBAN:', contractor.contractor_iban])

        if bank_info:
            bank_table = Table(bank_info, colWidths=[40*mm, 130*mm])
            bank_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(bank_table)
            elements.append(Spacer(1, 4*mm))

    # Footer
    elements.append(Table([['', '']], colWidths=[160*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ])))
    elements.append(Spacer(1, 2*mm))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['small'],
        alignment=TA_CENTER,
        fontSize=8,
        textColor=colors.grey
    )
    footer_text = f"""
    <b>AVENTUS CONTRACTOR MANAGEMENT</b><br/>
    Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
    <i>This is a computer-generated payslip.</i>
    """
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)
    buffer.seek(0)

    return buffer


def generate_invoice_pdf(payroll, contractor) -> BytesIO:
    """
    Generate an invoice PDF for client billing.

    Args:
        payroll: Payroll model instance
        contractor: Contractor model instance

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    elements = []
    styles = _get_styles()

    # Add logo
    _add_logo(elements)

    # Title
    elements.append(Paragraph("INVOICE", styles['title']))

    # Invoice number and date
    invoice_number = f"INV-{payroll.id:06d}"
    invoice_date = datetime.now().strftime('%B %d, %Y')

    elements.append(Paragraph(f"Invoice #: {invoice_number}", ParagraphStyle(
        'InvoiceNum',
        parent=styles['base']['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )))
    elements.append(Paragraph(f"Date: {invoice_date}", ParagraphStyle(
        'InvoiceDate',
        parent=styles['base']['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica'
    )))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[170*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, ORANGE),
    ])))
    elements.append(Spacer(1, 4*mm))

    # Bill To / From section
    contractor_name = f"{contractor.first_name} {contractor.surname}"

    bill_from = [
        Paragraph("<b>FROM:</b>", styles['body']),
        Paragraph("Aventus HR Solutions", styles['body']),
        Paragraph("Dubai, UAE", styles['body']),
    ]

    bill_to = [
        Paragraph("<b>BILL TO:</b>", styles['body']),
        Paragraph(contractor.client_name or "Client Company", styles['body']),
    ]

    # Add invoice address if available
    if contractor.invoice_address_line1:
        bill_to.append(Paragraph(contractor.invoice_address_line1, styles['body']))
    if contractor.invoice_address_line2:
        bill_to.append(Paragraph(contractor.invoice_address_line2, styles['body']))
    if contractor.invoice_country:
        bill_to.append(Paragraph(contractor.invoice_country, styles['body']))

    address_table = Table([[bill_from, bill_to]], colWidths=[85*mm, 85*mm])
    address_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 6*mm))

    # Invoice Details
    elements.append(Paragraph("<b>Service Details</b>", styles['section']))

    details_data = [
        ['Description', 'Period', 'Rate', 'Qty', 'Amount'],
        [
            f"Contractor Services - {contractor_name}",
            payroll.period or "N/A",
            f"{payroll.currency} {payroll.charge_rate_day:,.2f}/day",
            f"{payroll.work_days}",
            f"{payroll.currency} {payroll.invoice_amount:,.2f}"
        ],
    ]

    details_table = Table(details_data, colWidths=[55*mm, 30*mm, 35*mm, 15*mm, 35*mm])
    details_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        # Data
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 4*mm))

    # Total Section
    total_data = [
        ['Subtotal:', f"{payroll.currency} {payroll.invoice_amount:,.2f}"],
        ['VAT (0%):', f"{payroll.currency} 0.00"],
        ['Total Due:', f"{payroll.currency} {payroll.invoice_amount:,.2f}"],
    ]

    total_table = Table(total_data, colWidths=[130*mm, 40*mm])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 1), LIGHT_GRAY),
        ('BACKGROUND', (0, 2), (-1, 2), ORANGE),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEABOVE', (0, 2), (-1, 2), 1, DARK_GRAY),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 6*mm))

    # Payment Terms
    elements.append(Paragraph("<b>Payment Terms</b>", styles['section']))

    terms = contractor.client_payment_terms or "Net 30 days"
    terms_text = f"Payment is due within {terms} from the invoice date."

    terms_table = Table([[terms_text]], colWidths=[170*mm])
    terms_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(terms_table)
    elements.append(Spacer(1, 4*mm))

    # Bank Details for Payment
    elements.append(Paragraph("<b>Bank Details for Payment</b>", styles['section']))

    bank_data = [
        ['Bank Name:', 'Aventus HR Solutions Bank'],
        ['Account Name:', 'Aventus HR Solutions LLC'],
        ['IBAN:', 'AE12 3456 7890 1234 5678 901'],
        ['SWIFT/BIC:', 'AVENTUAE'],
    ]

    bank_table = Table(bank_data, colWidths=[40*mm, 130*mm])
    bank_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(bank_table)
    elements.append(Spacer(1, 6*mm))

    # Footer
    elements.append(Table([['', '']], colWidths=[160*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ])))
    elements.append(Spacer(1, 2*mm))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['small'],
        alignment=TA_CENTER,
        fontSize=8,
        textColor=colors.grey
    )
    footer_text = f"""
    <b>AVENTUS CONTRACTOR MANAGEMENT</b><br/>
    Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
    <i>Thank you for your business.</i>
    """
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)
    buffer.seek(0)

    return buffer
