"""
Payroll PDF generators for payslips and invoices.
Clean, professional design with single color scheme.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from calendar import monthrange
import os


# Brand color
ORANGE = colors.HexColor('#FF6B00')
BLACK = colors.HexColor('#111111')
DARK_TEXT = colors.HexColor('#333333')
LIGHT_TEXT = colors.HexColor('#666666')
BORDER_COLOR = colors.HexColor('#DDDDDD')
BG_LIGHT = colors.HexColor('#F8F8F8')
WHITE = colors.white


def _add_logo(elements):
    """Add Aventus logo to PDF with proper sizing."""
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        # Proper aspect ratio for logo
        logo = Image(logo_path, width=40*mm, height=10*mm, kind='proportional')
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 5*mm))


def _number_to_words(amount: float, currency: str = "AED") -> str:
    """Convert a number to words for payslip display."""
    ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
            'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
            'seventeen', 'eighteen', 'nineteen']
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

    def convert_hundreds(n):
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (('-' + ones[n % 10]) if n % 10 else '')
        else:
            return ones[n // 100] + ' hundred' + ((' and ' + convert_hundreds(n % 100)) if n % 100 else '')

    def convert(n):
        if n < 1000:
            return convert_hundreds(n)
        elif n < 1000000:
            return convert(n // 1000) + ' thousand' + ((' ' + convert_hundreds(n % 1000)) if n % 1000 else '')
        elif n < 1000000000:
            return convert(n // 1000000) + ' million' + ((' ' + convert(n % 1000000)) if n % 1000000 else '')
        else:
            return convert(n // 1000000000) + ' billion' + ((' ' + convert(n % 1000000000)) if n % 1000000000 else '')

    whole = int(amount)
    if whole == 0:
        words = "zero"
    else:
        words = convert(whole)

    words = words.capitalize()

    currency_names = {
        'AED': 'dirhams',
        'SAR': 'riyals',
        'USD': 'dollars',
        'GBP': 'pounds',
        'EUR': 'euros',
    }
    currency_word = currency_names.get(currency.upper(), currency.lower())

    return f"{words} {currency_word}"


def _get_pay_period_string(period: str) -> str:
    """Convert 'November 2024' to 'November 01 - November 30, 2024'."""
    try:
        date = datetime.strptime(period, "%B %Y")
        last_day = monthrange(date.year, date.month)[1]
        return f"{date.strftime('%B')} 01 - {date.strftime('%B')} {last_day}, {date.year}"
    except (ValueError, AttributeError):
        return period or "Current Period"


def generate_payslip_pdf(payroll, contractor) -> BytesIO:
    """
    Generate a clean, professional payslip PDF.
    Single color scheme with bold/light text variations.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    elements = []

    # Safe value extraction
    currency = payroll.currency or "AED"
    gross_pay = payroll.gross_pay or 0
    net_salary = payroll.net_salary or 0
    monthly_rate = payroll.monthly_rate or 0
    day_rate = payroll.day_rate or 0
    days_worked = payroll.days_worked or 0
    deductions = payroll.leave_deductibles or payroll.deductions or 0
    contractor_name = f"{contractor.first_name} {contractor.surname}"

    # =========================================================================
    # HEADER
    # =========================================================================

    # Reference info styles
    ref_style = ParagraphStyle(
        'RefStyle',
        fontSize=10,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        spaceAfter=1,
    )

    title_style = ParagraphStyle(
        'Title',
        fontSize=22,
        textColor=ORANGE,
        fontName='Helvetica-Bold',
        spaceAfter=0,
        alignment=TA_RIGHT,
    )

    payslip_ref = f"PS-{payroll.id}"
    pay_date = datetime.now().strftime('%d/%m/%Y')
    pay_period = _get_pay_period_string(payroll.period)

    # Left column: reference info
    left_col = [
        Paragraph(f"{payslip_ref}", ref_style),
        Paragraph(f"Pay Date: {pay_date}", ref_style),
        Paragraph(f"Pay Period: {pay_period}", ref_style),
    ]

    # Right column: logo + "Payslip" title
    right_col = []
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=40*mm, height=10*mm, kind='proportional')
        logo.hAlign = 'RIGHT'
        right_col.append(logo)
    right_col.append(Paragraph("Payslip", title_style))

    header_table = Table(
        [[left_col, right_col]],
        colWidths=[95*mm, 75*mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))

    # =========================================================================
    # EMPLOYEE & EMPLOYER DETAILS
    # =========================================================================

    # Section header style
    section_header = ParagraphStyle(
        'SectionHeader',
        fontSize=9,
        textColor=ORANGE,
        fontName='Helvetica-Bold',
        spaceAfter=3,
    )

    # Bold text style
    bold_style = ParagraphStyle(
        'BoldText',
        fontSize=10,
        textColor=BLACK,
        fontName='Helvetica-Bold',
        spaceAfter=1,
    )

    # Light text style
    light_style = ParagraphStyle(
        'LightText',
        fontSize=9,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        spaceAfter=1,
    )

    # Two column layout
    employee_col = [
        Paragraph("Employee Details", section_header),
        Paragraph(contractor_name, bold_style),
        Paragraph(contractor.client_name or '', light_style),
    ]
    if contractor.role:
        employee_col.append(Paragraph(contractor.role, light_style))

    employer_col = [
        Paragraph("Employer Details", section_header),
        Paragraph("Aventus Talent Consultancy LLC", bold_style),
        Paragraph("Office 14, Golden Mile 4,", light_style),
        Paragraph("Palm Jumeirah, Dubai, UAE", light_style),
    ]

    details_table = Table(
        [[employee_col, employer_col]],
        colWidths=[85*mm, 85*mm]
    )
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 8*mm))

    # =========================================================================
    # EARNINGS
    # =========================================================================

    # Section title row with orange background
    earnings_title = Table(
        [['Earnings', 'Amount']],
        colWidths=[130*mm, 40*mm]
    )
    earnings_title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(earnings_title)

    # Build earnings rows
    if monthly_rate and monthly_rate > 0:
        # Monthly breakdown
        basic_pay = round(monthly_rate * 0.50, 2)
        housing = round(monthly_rate * 0.25, 2)
        transport = round(monthly_rate * 0.1667, 2)
        leave_allow = round(monthly_rate - basic_pay - housing - transport, 2)

        earnings_data = [
            ['Basic Pay', f"{currency} {basic_pay:,.2f}"],
            ['Housing Allowance', f"{currency} {housing:,.2f}"],
            ['Transport Allowance', f"{currency} {transport:,.2f}"],
            ['Leave Allowance', f"{currency} {leave_allow:,.2f}"],
        ]
    elif day_rate and days_worked:
        total = day_rate * days_worked
        earnings_data = [
            ['Day Rate', f"{currency} {day_rate:,.2f}"],
            ['Days Worked', f"{days_worked}"],
            ['Gross Earnings', f"{currency} {total:,.2f}"],
        ]
    else:
        earnings_data = [
            ['Gross Salary', f"{currency} {gross_pay:,.2f}"],
        ]

    earnings_table = Table(earnings_data, colWidths=[130*mm, 40*mm])
    earnings_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK_TEXT),
        ('TEXTCOLOR', (1, 0), (1, -1), BLACK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
        ('RIGHTPADDING', (1, 0), (1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 6*mm))

    # =========================================================================
    # DEDUCTIONS
    # =========================================================================

    deductions_title = Table(
        [['Deductions', 'Amount']],
        colWidths=[130*mm, 40*mm]
    )
    deductions_title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(deductions_title)

    # Build deductions rows
    deductions_data = []
    expenses = payroll.expenses_reimbursement or 0

    if expenses > 0:
        deductions_data.append(['Expenses Reimbursement', f"+{currency} {expenses:,.2f}"])

    if deductions > 0:
        deductions_data.append(['Leave Deductions', f"-{currency} {deductions:,.2f}"])

    # Pro-rata for partial month
    if monthly_rate and days_worked and payroll.total_calendar_days:
        total_days = payroll.total_calendar_days
        if days_worked < total_days:
            prorata = monthly_rate - (monthly_rate / total_days * days_worked)
            if prorata > 0:
                deductions_data.append([f'Pro-rata ({days_worked}/{total_days} days)', f"-{currency} {prorata:,.2f}"])

    if not deductions_data:
        deductions_data.append(['No deductions', f"{currency} 0.00"])

    deductions_table = Table(deductions_data, colWidths=[130*mm, 40*mm])
    deductions_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK_TEXT),
        ('TEXTCOLOR', (1, 0), (1, -1), BLACK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
        ('RIGHTPADDING', (1, 0), (1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
    ]))
    elements.append(deductions_table)
    elements.append(Spacer(1, 6*mm))

    # =========================================================================
    # TOTAL PAY
    # =========================================================================

    total_table = Table(
        [['Total Pay', f"{currency} {net_salary:,.2f}"]],
        colWidths=[130*mm, 40*mm]
    )
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(total_table)

    # Amount in words
    amount_words = _number_to_words(net_salary, currency)
    words_table = Table(
        [['Total Pay in Words:', amount_words]],
        colWidths=[45*mm, 125*mm]
    )
    words_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Oblique'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_TEXT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(words_table)
    elements.append(Spacer(1, 10*mm))

    # =========================================================================
    # PAYMENT DETAILS
    # =========================================================================

    elements.append(Paragraph("Payment Details", section_header))
    elements.append(Paragraph("Payment made to employee's bank account.", light_style))

    if contractor.contractor_bank_name or contractor.contractor_iban:
        bank_info = []
        if contractor.contractor_bank_name:
            bank_info.append(f"Bank: {contractor.contractor_bank_name}")
        if contractor.contractor_iban:
            iban = contractor.contractor_iban
            masked = iban[:4] + '*' * (len(iban) - 8) + iban[-4:] if len(iban) > 8 else iban
            bank_info.append(f"IBAN: {masked}")
        elements.append(Paragraph(" | ".join(bank_info), light_style))

    elements.append(Spacer(1, 12*mm))

    # =========================================================================
    # SIGNATURES
    # =========================================================================

    sig_table = Table(
        [
            ['Employee Signature', '', 'Employer Signature'],
            ['', '', ''],
            ['', '', ''],
            ['_________________________', '', '_________________________'],
            [contractor_name, '', 'Aventus Talent Consultancy LLC'],
        ],
        colWidths=[60*mm, 50*mm, 60*mm]
    )
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), DARK_TEXT),
        ('FONTSIZE', (0, 3), (-1, -1), 8),
        ('TEXTCOLOR', (0, 4), (-1, 4), LIGHT_TEXT),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 12*mm))

    # =========================================================================
    # FOOTER
    # =========================================================================

    # Line
    elements.append(Table([['']], colWidths=[170*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, BORDER_COLOR),
    ])))
    elements.append(Spacer(1, 3*mm))

    footer_style = ParagraphStyle(
        'Footer',
        fontSize=7,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        alignment=TA_CENTER,
        leading=10,
    )

    footer = """This is a system-generated payslip, therefore signature is not mandatory.
The information contained herein is confidential and intended only for the use of the named person.
Aventus Talent Consultancy LLC | Dubai, UAE"""

    elements.append(Paragraph(footer, footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(payroll, contractor) -> BytesIO:
    """
    Generate a clean, professional invoice PDF.
    Single color scheme with bold/light text variations.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    elements = []

    # Safe values
    currency = payroll.currency or "AED"
    invoice_total = payroll.invoice_total or payroll.net_salary or 0
    vat_rate = payroll.vat_rate or 0
    vat_amount = payroll.vat_amount or 0
    total_payable = payroll.total_payable or invoice_total
    net_salary = payroll.net_salary or 0
    total_accruals = payroll.total_accruals or 0
    management_fee = payroll.management_fee or 0
    contractor_name = f"{contractor.first_name} {contractor.surname}"

    # =========================================================================
    # HEADER
    # =========================================================================

    _add_logo(elements)

    title_style = ParagraphStyle(
        'Title',
        fontSize=22,
        textColor=ORANGE,
        fontName='Helvetica-Bold',
        spaceAfter=2,
    )
    elements.append(Paragraph("Invoice", title_style))

    ref_style = ParagraphStyle(
        'RefStyle',
        fontSize=10,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        spaceAfter=1,
    )

    invoice_number = f"INV-{payroll.id:06d}"
    invoice_date = datetime.now().strftime('%d/%m/%Y')

    elements.append(Paragraph(f"{invoice_number}", ref_style))
    elements.append(Paragraph(f"Date: {invoice_date}", ref_style))
    elements.append(Paragraph(f"Period: {payroll.period or 'N/A'}", ref_style))
    elements.append(Spacer(1, 8*mm))

    # =========================================================================
    # FROM / TO
    # =========================================================================

    section_header = ParagraphStyle(
        'SectionHeader',
        fontSize=9,
        textColor=ORANGE,
        fontName='Helvetica-Bold',
        spaceAfter=3,
    )

    bold_style = ParagraphStyle(
        'BoldText',
        fontSize=10,
        textColor=BLACK,
        fontName='Helvetica-Bold',
        spaceAfter=1,
    )

    light_style = ParagraphStyle(
        'LightText',
        fontSize=9,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        spaceAfter=1,
    )

    from_col = [
        Paragraph("From", section_header),
        Paragraph("Aventus Talent Consultancy LLC", bold_style),
        Paragraph("Office 14, Golden Mile 4,", light_style),
        Paragraph("Palm Jumeirah, Dubai, UAE", light_style),
    ]

    to_col = [
        Paragraph("Bill To", section_header),
        Paragraph(contractor.client_name or "Client Company", bold_style),
    ]
    if contractor.invoice_address_line1:
        to_col.append(Paragraph(contractor.invoice_address_line1, light_style))
    if contractor.invoice_address_line2:
        to_col.append(Paragraph(contractor.invoice_address_line2, light_style))
    if contractor.invoice_country:
        to_col.append(Paragraph(contractor.invoice_country, light_style))

    address_table = Table([[from_col, to_col]], colWidths=[85*mm, 85*mm])
    address_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 8*mm))

    # =========================================================================
    # SERVICE DETAILS
    # =========================================================================

    service_title = Table(
        [['Description', 'Amount']],
        colWidths=[130*mm, 40*mm]
    )
    service_title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(service_title)

    service_data = [
        [f"Contractor Services - {contractor_name}", f"{currency} {net_salary:,.2f}"],
    ]
    if total_accruals > 0:
        service_data.append(['Third Party Accruals', f"{currency} {total_accruals:,.2f}"])
    if management_fee > 0:
        service_data.append(['Management Fee', f"{currency} {management_fee:,.2f}"])

    service_table = Table(service_data, colWidths=[130*mm, 40*mm])
    service_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK_TEXT),
        ('TEXTCOLOR', (1, 0), (1, -1), BLACK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
        ('RIGHTPADDING', (1, 0), (1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
    ]))
    elements.append(service_table)
    elements.append(Spacer(1, 4*mm))

    # =========================================================================
    # TOTALS
    # =========================================================================

    vat_percent = int(vat_rate * 100) if vat_rate else 0

    totals_data = [
        ['Subtotal:', f"{currency} {invoice_total:,.2f}"],
        [f'VAT ({vat_percent}%):', f"{currency} {vat_amount:,.2f}"],
    ]

    totals_table = Table(totals_data, colWidths=[130*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_TEXT),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (1, 0), (1, -1), 8),
    ]))
    elements.append(totals_table)

    # Total Due
    total_due = Table(
        [['Total Due:', f"{currency} {total_payable:,.2f}"]],
        colWidths=[130*mm, 40*mm]
    )
    total_due.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('RIGHTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(total_due)
    elements.append(Spacer(1, 10*mm))

    # =========================================================================
    # PAYMENT TERMS & BANK
    # =========================================================================

    elements.append(Paragraph("Payment Terms", section_header))
    terms = contractor.client_payment_terms or "Net 30 days"
    elements.append(Paragraph(f"Payment is due within {terms} from the invoice date.", light_style))
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Bank Details for Payment", section_header))

    bank_data = [
        ['Bank Name:', 'Emirates NBD'],
        ['Account Name:', 'Aventus Talent Consultancy LLC'],
        ['IBAN:', 'AE12 3456 7890 1234 5678 901'],
        ['SWIFT/BIC:', 'EBILORAE'],
    ]

    bank_table = Table(bank_data, colWidths=[35*mm, 135*mm])
    bank_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_TEXT),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(bank_table)
    elements.append(Spacer(1, 12*mm))

    # =========================================================================
    # FOOTER
    # =========================================================================

    elements.append(Table([['']], colWidths=[170*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, BORDER_COLOR),
    ])))
    elements.append(Spacer(1, 3*mm))

    footer_style = ParagraphStyle(
        'Footer',
        fontSize=7,
        textColor=LIGHT_TEXT,
        fontName='Helvetica',
        alignment=TA_CENTER,
        leading=10,
    )

    elements.append(Paragraph("Thank you for your business.", footer_style))
    elements.append(Paragraph("Aventus Talent Consultancy LLC | Dubai, UAE", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
