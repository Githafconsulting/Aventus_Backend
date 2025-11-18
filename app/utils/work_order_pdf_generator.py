from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


def generate_work_order_pdf(work_order_data: dict) -> BytesIO:
    """
    Generate a professional work order PDF with Aventus branding

    Args:
        work_order_data: Dictionary containing work order information

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Define colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')
    light_gray = colors.HexColor('#F3F4F6')

    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=dark_gray,
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=6,
        leading=14,
        fontName='Helvetica'
    )

    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=9,
        leading=12,
    )

    # Extract data
    contractor_name = work_order_data.get('contractor_name', '[Contractor Name]')
    client_name = work_order_data.get('client_name', '[Client Name]')
    role = work_order_data.get('role', '[Role]')
    location = work_order_data.get('location', '[Location]')
    start_date = work_order_data.get('start_date', '[Start Date]')
    end_date = work_order_data.get('end_date', '[End Date]')
    duration = work_order_data.get('duration', '[Duration]')
    pay_rate = work_order_data.get('pay_rate', '[Pay Rate]')
    charge_rate = work_order_data.get('charge_rate', '[Charge Rate]')
    currency = work_order_data.get('currency', 'AED')
    work_order_number = work_order_data.get('work_order_number', '[WO-NUMBER]')
    business_type = work_order_data.get('business_type', '[Business Type]')
    umbrella_company = work_order_data.get('umbrella_company_name', '[Company Name]')
    project_name = work_order_data.get('project_name', '')

    # Add logo if available
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60*mm, height=15*mm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 10*mm))

    # Add title
    elements.append(Paragraph("WORK ORDER", header_style))
    elements.append(Paragraph(f"Work Order Number: {work_order_number}", title_style))
    elements.append(Spacer(1, 5*mm))

    # Work Order Date
    current_date = datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph(f"<b>Date:</b> {current_date}", body_style))
    elements.append(Spacer(1, 8*mm))

    # Contractor Details Section
    elements.append(Paragraph("CONTRACTOR DETAILS", section_style))
    contractor_table_data = [
        [Paragraph("<b>Contractor Name:</b>", body_style), Paragraph(contractor_name, body_style)],
        [Paragraph("<b>Business Type:</b>", body_style), Paragraph(business_type, body_style)],
    ]
    if business_type and business_type.lower() in ['3rd party', 'umbrella company']:
        contractor_table_data.append(
            [Paragraph("<b>Company Name:</b>", body_style), Paragraph(umbrella_company, body_style)]
        )

    contractor_table = Table(contractor_table_data, colWidths=[60*mm, 100*mm])
    contractor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(contractor_table)
    elements.append(Spacer(1, 6*mm))

    # Assignment Details Section
    elements.append(Paragraph("ASSIGNMENT DETAILS", section_style))
    assignment_table_data = [
        [Paragraph("<b>Client:</b>", body_style), Paragraph(client_name, body_style)],
        [Paragraph("<b>Job Title/Role:</b>", body_style), Paragraph(role, body_style)],
    ]
    if project_name:
        assignment_table_data.append(
            [Paragraph("<b>Project Name:</b>", body_style), Paragraph(project_name, body_style)]
        )
    assignment_table_data.extend([
        [Paragraph("<b>Location:</b>", body_style), Paragraph(location, body_style)],
        [Paragraph("<b>Start Date:</b>", body_style), Paragraph(start_date, body_style)],
        [Paragraph("<b>End Date:</b>", body_style), Paragraph(end_date, body_style)],
        [Paragraph("<b>Duration:</b>", body_style), Paragraph(duration, body_style)],
    ])

    assignment_table = Table(assignment_table_data, colWidths=[60*mm, 100*mm])
    assignment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(assignment_table)
    elements.append(Spacer(1, 6*mm))

    # Financial Details Section
    elements.append(Paragraph("FINANCIAL DETAILS", section_style))
    financial_table_data = [
        [Paragraph("<b>Currency:</b>", body_style), Paragraph(currency, body_style)],
        [Paragraph("<b>Pay Rate:</b>", body_style), Paragraph(f"{pay_rate} {currency}", body_style)],
        [Paragraph("<b>Charge Rate:</b>", body_style), Paragraph(f"{charge_rate} {currency}", body_style)],
    ]

    financial_table = Table(financial_table_data, colWidths=[60*mm, 100*mm])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 10*mm))

    # Terms and Conditions
    elements.append(Paragraph("TERMS AND CONDITIONS", section_style))
    terms_text = """
    <b>1. Scope of Work:</b> The contractor agrees to perform the services as described in this work order
    for the specified client and project.<br/><br/>

    <b>2. Payment Terms:</b> Payment will be made according to the agreed pay rate and frequency as per
    the main consultant agreement.<br/><br/>

    <b>3. Duration:</b> This work order is valid for the specified duration unless terminated earlier by
    either party with appropriate notice.<br/><br/>

    <b>4. Confidentiality:</b> The contractor must maintain confidentiality of all client and project information
    as per the main consultant agreement.<br/><br/>

    <b>5. Compliance:</b> The contractor must comply with all client policies and procedures during the assignment.
    """
    elements.append(Paragraph(terms_text, small_style))
    elements.append(Spacer(1, 10*mm))

    # Signature Section
    elements.append(Paragraph("SIGNATURES", section_style))
    elements.append(Spacer(1, 5*mm))

    signature_table_data = [
        [
            Paragraph("<b>Aventus Resources</b><br/>_____________________<br/>Authorized Signature<br/><br/>Date: _____________", body_style),
            Paragraph(f"<b>{contractor_name}</b><br/>_____________________<br/>Contractor Signature<br/><br/>Date: _____________", body_style)
        ]
    ]

    signature_table = Table(signature_table_data, colWidths=[80*mm, 80*mm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(signature_table)
    elements.append(Spacer(1, 10*mm))

    # Footer
    footer_text = """
    <b>Aventus Resources</b><br/>
    Email: info@aventusresources.com | Phone: +971 XXX XXXX<br/>
    This is a computer-generated document and does not require a physical signature unless specified.
    """
    elements.append(Paragraph(footer_text, small_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer
