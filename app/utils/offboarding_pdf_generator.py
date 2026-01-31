"""
Offboarding PDF Generators.

Generates PDF documents for offboarding:
- Termination Letter
- Experience Letter
- Clearance Certificate
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


def generate_termination_letter_pdf(
    contractor_data: dict,
    offboarding_data: dict,
) -> BytesIO:
    """
    Generate a professional termination letter PDF.

    Args:
        contractor_data: Dictionary containing contractor information
        offboarding_data: Dictionary containing offboarding details

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

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

    # Colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')

    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16,
        fontName='Helvetica'
    )

    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=dark_gray,
        fontName='Helvetica'
    )

    # Extract data
    contractor_name = f"{contractor_data.get('first_name', '')} {contractor_data.get('surname', '')}"
    contractor_address = contractor_data.get('home_address', '')
    reason = offboarding_data.get('reason', 'Contract End')
    last_working_date = offboarding_data.get('last_working_date', '')
    effective_date = offboarding_data.get('effective_termination_date', last_working_date)

    today = datetime.now().strftime('%B %d, %Y')

    # Header with logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'av-logo.png')
    try:
        logo = Image(logo_path, width=40*mm, height=12*mm)
        company_details = Paragraph("""
            <font size=8>
            Office 14, Golden Mile 4<br/>
            Palm Jumeirah<br/>
            Dubai, United Arab Emirates
            </font>
        """, address_style)

        header_data = [[logo, company_details]]
        header_table = Table(header_data, colWidths=[80*mm, 85*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, orange),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(header_table)
    except Exception:
        pass

    elements.append(Spacer(1, 20))

    # Title
    elements.append(Paragraph("TERMINATION LETTER", header_style))
    elements.append(Spacer(1, 20))

    # Date
    elements.append(Paragraph(f"Date: {today}", body_style))
    elements.append(Spacer(1, 10))

    # Recipient
    elements.append(Paragraph(f"<b>To:</b> {contractor_name}", body_style))
    if contractor_address:
        elements.append(Paragraph(f"{contractor_address}", body_style))
    elements.append(Spacer(1, 20))

    # Subject
    elements.append(Paragraph("<b>Subject: Termination of Contract</b>", body_style))
    elements.append(Spacer(1, 15))

    # Body
    reason_text = _get_reason_text(reason)

    body_text = f"""
    Dear {contractor_name},<br/><br/>

    We are writing to formally notify you that your contract with Aventus Talent Consultant
    will be terminated effective <b>{effective_date}</b>.<br/><br/>

    {reason_text}<br/><br/>

    Your last working day will be <b>{last_working_date}</b>. Please ensure that all company
    property, including but not limited to laptops, access cards, and confidential documents,
    are returned before your departure.<br/><br/>

    Your final settlement, including any outstanding salary, unused leave encashment, and
    end of service benefits, will be processed in accordance with your contract terms and
    applicable labor laws.<br/><br/>

    We appreciate your contributions during your time with us and wish you all the best in
    your future endeavors.<br/><br/>

    If you have any questions regarding this termination or the settlement process, please
    do not hesitate to contact our HR department.
    """

    elements.append(Paragraph(body_text, body_style))
    elements.append(Spacer(1, 30))

    # Signature
    elements.append(Paragraph("Sincerely,", body_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_______________________", body_style))
    elements.append(Paragraph("<b>Aventus Talent Consultant</b>", body_style))
    elements.append(Paragraph("Human Resources Department", body_style))

    # Footer
    elements.append(Spacer(1, 40))
    footer_text = """<font size=8 color='gray'>
    This document is confidential and intended for the named recipient only.
    </font>"""
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_experience_letter_pdf(
    contractor_data: dict,
    offboarding_data: dict,
) -> BytesIO:
    """
    Generate a professional experience letter PDF.

    Args:
        contractor_data: Dictionary containing contractor information
        offboarding_data: Dictionary containing offboarding details

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

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

    # Colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')

    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16,
        fontName='Helvetica'
    )

    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=dark_gray,
        fontName='Helvetica'
    )

    # Extract data
    contractor_name = f"{contractor_data.get('first_name', '')} {contractor_data.get('surname', '')}"
    role = contractor_data.get('role', 'Consultant')
    client_name = contractor_data.get('client_name', '')
    start_date = contractor_data.get('start_date', '')
    last_working_date = offboarding_data.get('last_working_date', '')

    today = datetime.now().strftime('%B %d, %Y')

    # Header with logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'av-logo.png')
    try:
        logo = Image(logo_path, width=40*mm, height=12*mm)
        company_details = Paragraph("""
            <font size=8>
            Office 14, Golden Mile 4<br/>
            Palm Jumeirah<br/>
            Dubai, United Arab Emirates
            </font>
        """, address_style)

        header_data = [[logo, company_details]]
        header_table = Table(header_data, colWidths=[80*mm, 85*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, orange),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(header_table)
    except Exception:
        pass

    elements.append(Spacer(1, 20))

    # Title
    elements.append(Paragraph("EXPERIENCE LETTER", header_style))
    elements.append(Spacer(1, 20))

    # Date
    elements.append(Paragraph(f"Date: {today}", body_style))
    elements.append(Spacer(1, 20))

    # Subject
    elements.append(Paragraph("<b>TO WHOM IT MAY CONCERN</b>", body_style))
    elements.append(Spacer(1, 20))

    # Body
    body_text = f"""
    This is to certify that <b>{contractor_name}</b> was employed with Aventus Talent Consultant
    as a <b>{role}</b> from <b>{start_date}</b> to <b>{last_working_date}</b>.<br/><br/>

    {"During this period, " + contractor_name + " was assigned to work with " + client_name + "." if client_name else ""}<br/><br/>

    {contractor_name} has demonstrated professionalism, dedication, and competence throughout
    their tenure with us. Their contributions have been valuable to our organization and
    our clients.<br/><br/>

    During their employment, {contractor_name} fulfilled their responsibilities satisfactorily
    and maintained good working relationships with colleagues and clients alike.<br/><br/>

    We confirm that {contractor_name} is leaving the organization on good terms, and we
    wish them continued success in their future endeavors.<br/><br/>

    This letter is issued upon request for employment verification purposes.
    """

    elements.append(Paragraph(body_text, body_style))
    elements.append(Spacer(1, 40))

    # Signature
    elements.append(Paragraph("Best regards,", body_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_______________________", body_style))
    elements.append(Paragraph("<b>Aventus Talent Consultant</b>", body_style))
    elements.append(Paragraph("Human Resources Department", body_style))

    # Footer
    elements.append(Spacer(1, 40))
    footer_text = """<font size=8 color='gray'>
    This document is issued without prejudice. For verification, please contact HR at hr@aventus.ae
    </font>"""
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_clearance_certificate_pdf(
    contractor_data: dict,
    offboarding_data: dict,
) -> BytesIO:
    """
    Generate a clearance certificate PDF.

    Args:
        contractor_data: Dictionary containing contractor information
        offboarding_data: Dictionary containing offboarding details

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

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

    # Colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')
    light_gray = colors.HexColor('#F3F4F6')

    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16,
        fontName='Helvetica'
    )

    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=dark_gray,
        fontName='Helvetica'
    )

    # Extract data
    contractor_name = f"{contractor_data.get('first_name', '')} {contractor_data.get('surname', '')}"
    contractor_id = contractor_data.get('id', '')
    last_working_date = offboarding_data.get('last_working_date', '')

    today = datetime.now().strftime('%B %d, %Y')

    # Header with logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'av-logo.png')
    try:
        logo = Image(logo_path, width=40*mm, height=12*mm)
        company_details = Paragraph("""
            <font size=8>
            Office 14, Golden Mile 4<br/>
            Palm Jumeirah<br/>
            Dubai, United Arab Emirates
            </font>
        """, address_style)

        header_data = [[logo, company_details]]
        header_table = Table(header_data, colWidths=[80*mm, 85*mm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, orange),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(header_table)
    except Exception:
        pass

    elements.append(Spacer(1, 20))

    # Title
    elements.append(Paragraph("CLEARANCE CERTIFICATE", header_style))
    elements.append(Spacer(1, 20))

    # Date and Reference
    elements.append(Paragraph(f"Date: {today}", body_style))
    elements.append(Paragraph(f"Reference: CLR-{contractor_id[:8] if contractor_id else 'XXXX'}", body_style))
    elements.append(Spacer(1, 20))

    # Body
    body_text = f"""
    This is to certify that <b>{contractor_name}</b> has completed all necessary
    clearance procedures following the termination of their contract with
    Aventus Talent Consultant, effective <b>{last_working_date}</b>.<br/><br/>

    The following items have been verified and cleared:
    """
    elements.append(Paragraph(body_text, body_style))

    # Clearance checklist
    checklist_items = [
        ["IT Equipment", "Cleared"],
        ["Access Cards / Keys", "Cleared"],
        ["Company Documents", "Cleared"],
        ["Financial Obligations", "Cleared"],
        ["Knowledge Transfer", "Completed"],
        ["Exit Interview", "Completed"],
    ]

    checklist_table = Table(
        [["Department", "Status"]] + checklist_items,
        colWidths=[100*mm, 50*mm]
    )
    checklist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), light_gray),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_gray]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(checklist_table)
    elements.append(Spacer(1, 20))

    # Final statement
    final_text = f"""
    {contractor_name} has no outstanding obligations or liabilities towards
    Aventus Talent Consultant. This clearance certificate is issued to confirm
    the satisfactory completion of all offboarding procedures.
    """
    elements.append(Paragraph(final_text, body_style))
    elements.append(Spacer(1, 30))

    # Signature
    elements.append(Paragraph("Authorized Signatory,", body_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_______________________", body_style))
    elements.append(Paragraph("<b>Aventus Talent Consultant</b>", body_style))
    elements.append(Paragraph("Human Resources Department", body_style))

    # Footer
    elements.append(Spacer(1, 30))
    footer_text = """<font size=8 color='gray'>
    This certificate is valid only with authorized signature. For verification, contact hr@aventus.ae
    </font>"""
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _get_reason_text(reason: str) -> str:
    """Get human-readable reason text."""
    reason_texts = {
        "contract_end": "This termination is due to the natural expiry of your contract term.",
        "resignation": "This termination is in acknowledgment of your resignation letter.",
        "termination": "This termination has been initiated by the company in accordance with your contract terms.",
        "transfer": "This termination is effective as you are being transferred to another employer.",
        "mutual_agreement": "This termination has been mutually agreed upon by both parties.",
    }
    return reason_texts.get(reason, "This termination is effective as per the agreed terms.")
