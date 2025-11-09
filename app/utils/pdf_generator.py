from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import base64


def generate_contract_pdf(contractor_data: dict, include_signature: bool = False) -> BytesIO:
    """
    Generate a professional single-page employment contract PDF matching frontend design

    Args:
        contractor_data: Dictionary containing contractor information
        include_signature: Whether to include the signature (for signed contracts)

    Returns:
        BytesIO: PDF file in memory
    """
    # Create a BytesIO buffer
    buffer = BytesIO()

    # Create the PDF document with tighter margins for single-page layout
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Orange color from frontend
    orange = colors.HexColor('#FF6B00')
    blue = colors.HexColor('#1E40AF')
    light_gray = colors.HexColor('#F3F4F6')
    dark_gray = colors.HexColor('#1F2937')

    # Custom compact styles
    header_style = ParagraphStyle(
        'CompactHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=orange,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    title_style = ParagraphStyle(
        'CompactTitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading3'],
        fontSize=9,
        textColor=dark_gray,
        spaceAfter=4,
        spaceBefore=6,
        fontName='Helvetica-Bold',
        leftIndent=6,
    )

    body_style = ParagraphStyle(
        'CompactBody',
        parent=styles['BodyText'],
        fontSize=8,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
        leading=10,
    )

    small_text_style = ParagraphStyle(
        'SmallText',
        parent=body_style,
        fontSize=7,
        leading=9,
    )

    # Extract contractor data
    first_name = contractor_data.get('first_name', '')
    surname = contractor_data.get('surname', '')
    email = contractor_data.get('email', '')
    dob = contractor_data.get('dob', '')
    nationality = contractor_data.get('nationality', '')
    role = contractor_data.get('role', '')
    client_name = contractor_data.get('client_name', '')
    start_date = contractor_data.get('start_date', '')
    end_date = contractor_data.get('end_date', 'Ongoing')
    duration = contractor_data.get('duration', '')
    location = contractor_data.get('location', '')
    currency = contractor_data.get('currency', 'SAR')
    pay_rate = contractor_data.get('pay_rate', '')
    charge_rate = contractor_data.get('charge_rate', '')

    contractor_full_name = f"{first_name} {surname}"
    today = datetime.now().strftime('%d %B %Y')

    # Format dates
    def format_date(date_str):
        if not date_str or date_str == 'Ongoing':
            return date_str
        try:
            date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
            return date_obj.strftime('%d %B %Y')
        except:
            return date_str

    # Header with orange line
    header_data = [
        [Paragraph("<b>AVENTUS</b>", header_style)],
        [Paragraph("Global Workforce Solutions", small_text_style)],
    ]
    header_table = Table(header_data, colWidths=[180*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEBELOW', (0, -1), (-1, -1), 2, orange),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
    ]))
    elements.append(header_table)

    # Contract metadata (contract number and date)
    meta_data = [
        [f"Contract No: AV-{datetime.now().year}-______", f"Date: {today}"]
    ]
    meta_table = Table(meta_data, colWidths=[90*mm, 90*mm])
    meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6))

    # Title
    elements.append(Paragraph("<b>PROFESSIONAL SERVICES AGREEMENT</b>", title_style))
    elements.append(Spacer(1, 4))

    # Agreement introduction
    intro_text = f"THIS AGREEMENT made and entered into this <b>{today}</b> by and between <b>AVENTUS GLOBAL WORKFORCE SOLUTIONS</b>, " \
                 f"Palm Jumeirah, Dubai, UAE (hereinafter called <b>\"COMPANY\"</b>), and <b><font color='#FF6B00'>{contractor_full_name}</font></b> " \
                 f"(hereinafter called <b>\"CONTRACTOR\"</b>)."
    elements.append(Paragraph(intro_text, body_style))
    elements.append(Spacer(1, 6))

    # Section 1: Contractor Information
    section1_header = Table([[Paragraph("<b>1. CONTRACTOR INFORMATION & DUTIES</b>", section_heading_style)]], colWidths=[180*mm])
    section1_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(section1_header)

    # Contractor details grid
    contractor_details = [
        [
            Paragraph(f"<font size=6 color='gray'>FULL NAME</font><br/><b>{contractor_full_name}</b>", body_style),
            Paragraph(f"<font size=6 color='gray'>EMAIL</font><br/><b>{email}</b>", body_style),
            Paragraph(f"<font size=6 color='gray'>DOB</font><br/><b>{format_date(dob)}</b>", body_style),
            Paragraph(f"<font size=6 color='gray'>NATIONALITY</font><br/><b>{nationality}</b>", body_style),
        ]
    ]
    details_table = Table(contractor_details, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
    details_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(details_table)

    position_text = f"<b>Position:</b> {role} | <b>Client:</b> {client_name} | <b>Location:</b> {location}<br/>" \
                   f"<b>Duties:</b> CONTRACTOR agrees to provide professional services as specified in the role description and client requirements, exercising appropriate skill and diligence."
    elements.append(Paragraph(position_text, body_style))
    elements.append(Spacer(1, 6))

    # Section 2: Contract Period
    section2_header = Table([[Paragraph("<b>2. CONTRACT PERIOD</b>", section_heading_style)]], colWidths=[180*mm])
    section2_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(section2_header)

    period_details = [
        [
            Paragraph(f"<font size=6 color='gray'>START DATE</font><br/><b><font color='#1E40AF'>{format_date(start_date)}</font></b>", body_style),
            Paragraph(f"<font size=6 color='gray'>END DATE</font><br/><b><font color='#1E40AF'>{format_date(end_date)}</font></b>", body_style),
            Paragraph(f"<font size=6 color='gray'>DURATION</font><br/><b><font color='#1E40AF'>{duration} Months</font></b>", body_style),
        ]
    ]
    period_table = Table(period_details, colWidths=[60*mm, 60*mm, 60*mm])
    period_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 6))

    # Section 3: Compensation
    section3_header = Table([[Paragraph("<b>3. COMPENSATION</b>", section_heading_style)]], colWidths=[180*mm])
    section3_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(section3_header)

    elements.append(Paragraph("In consideration for services rendered, COMPANY agrees to pay CONTRACTOR as follows:", body_style))

    comp_details = [
        [
            Paragraph(f"<font size=6 color='gray'>MONTHLY PAY RATE</font><br/><b><font size=11 color='#FF6B00'>{currency} {pay_rate}</font></b>", body_style),
            Paragraph(f"<font size=6 color='gray'>BASIC SALARY (EOSB)</font><br/><b>{currency} [Amount]</b>", body_style),
            Paragraph(f"<font size=6 color='gray'>CLIENT CHARGE RATE</font><br/><b>{currency} {charge_rate}</b>", body_style),
        ]
    ]
    comp_table = Table(comp_details, colWidths=[60*mm, 60*mm, 60*mm])
    comp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('GRID', (0, 0), (0, -1), 2, orange),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF7ED')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(comp_table)
    elements.append(Paragraph("<font size=7>Payment will be processed monthly in arrears upon submission of approved timesheets and invoices.</font>", small_text_style))
    elements.append(Spacer(1, 6))

    # Section 4: Terms & Conditions
    section4_header = Table([[Paragraph("<b>4. TERMS & CONDITIONS</b>", section_heading_style)]], colWidths=[180*mm])
    section4_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(section4_header)

    terms_text = """
    <b>4.1 Compliance:</b> CONTRACTOR shall comply with all UAE labor laws, client policies, and industry regulations.<br/>
    <b>4.2 Confidentiality:</b> CONTRACTOR agrees to maintain confidentiality of all proprietary information and execute required NDAs.<br/>
    <b>4.3 Termination:</b> Either party may terminate with 30 days written notice. COMPANY may terminate immediately for cause.<br/>
    <b>4.4 Documentation:</b> This agreement is subject to completion of Contractor Detail Sheet (CDS) and credential verification.<br/>
    <b>4.5 Independent Contractor:</b> CONTRACTOR is an independent contractor, not an employee of COMPANY.
    """
    elements.append(Paragraph(terms_text, small_text_style))
    elements.append(Spacer(1, 8))

    # Signatures section
    sig_intro = Paragraph("<b>Each party represents and warrants they are duly authorized to execute this Agreement:</b>", body_style)
    elements.append(sig_intro)
    elements.append(Spacer(1, 4))

    # Get contractor signature info if included
    contractor_signature_data_text = contractor_data.get('signature_data', '')
    contractor_signature_type = contractor_data.get('signature_type', '')
    signed_date = contractor_data.get('signed_date', '')

    # Get superadmin signature info
    superadmin_signature_data_text = contractor_data.get('superadmin_signature_data', '')
    superadmin_signature_type = contractor_data.get('superadmin_signature_type', '')

    # Prepare contractor signature cell content
    contractor_sig_content = None
    superadmin_sig_content = None

    if include_signature and signed_date:
        # Format signed date
        try:
            if isinstance(signed_date, str):
                signed_date_obj = datetime.fromisoformat(signed_date.replace('Z', '+00:00'))
            else:
                signed_date_obj = signed_date
            formatted_signed_date = signed_date_obj.strftime('%d %B %Y')
        except:
            formatted_signed_date = str(signed_date)

        if contractor_signature_type == 'drawn':
            # Handle drawn signature (base64 image)
            try:
                # Extract base64 data from data URL
                if contractor_signature_data_text.startswith('data:image'):
                    base64_data = contractor_signature_data_text.split(',')[1]
                else:
                    base64_data = contractor_signature_data_text

                # Decode base64 to image
                image_data = base64.b64decode(base64_data)
                image_buffer = BytesIO(image_data)

                # Create image for PDF (max width 60mm, height auto)
                sig_image = Image(image_buffer, width=50*mm, height=15*mm)

                # Create a table with the image and text info
                drawn_sig_data = [
                    [sig_image],
                    [Paragraph(f"<font size=7><b>{contractor_full_name}</b><br/>Signed Electronically<br/>Email: {email}<br/>Date: {formatted_signed_date}</font>", small_text_style)]
                ]
                drawn_sig_table = Table(drawn_sig_data, colWidths=[90*mm])
                drawn_sig_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))
                contractor_sig_content = drawn_sig_table
            except Exception as e:
                print(f"[ERROR] Failed to decode contractor drawn signature: {str(e)}")
                # Fallback to text if image fails
                contractor_sig_content = Paragraph(f"<font size=7><b>{contractor_full_name}</b><br/>Signed Electronically (Image Error)<br/>Email: {email}<br/>Date: {formatted_signed_date}</font>", small_text_style)
        else:
            # Handle typed signature (text)
            contractor_sig_text = f"<font color='#FF6B00' size=12><i>{contractor_signature_data_text}</i></font><br/><font size=7><b>{contractor_full_name}</b><br/>Signed Electronically<br/>Email: {email}<br/>Date: {formatted_signed_date}</font>"
            contractor_sig_content = Paragraph(contractor_sig_text, small_text_style)

        # Handle superadmin signature
        if superadmin_signature_data_text:
            if superadmin_signature_type == 'drawn':
                # Handle drawn signature (base64 image)
                try:
                    # Extract base64 data from data URL
                    if superadmin_signature_data_text.startswith('data:image'):
                        base64_data = superadmin_signature_data_text.split(',')[1]
                    else:
                        base64_data = superadmin_signature_data_text

                    # Decode base64 to image
                    image_data = base64.b64decode(base64_data)
                    image_buffer = BytesIO(image_data)

                    # Create image for PDF (max width 60mm, height auto)
                    sig_image = Image(image_buffer, width=50*mm, height=15*mm)

                    # Create a table with the image and text info
                    drawn_sig_data = [
                        [sig_image],
                        [Paragraph(f"<font size=7><b>Authorized Signatory</b><br/>AVENTUS Global Workforce Solutions<br/>Title: HR Director<br/>Date: {formatted_signed_date}</font>", small_text_style)]
                    ]
                    drawn_sig_table = Table(drawn_sig_data, colWidths=[90*mm])
                    drawn_sig_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ]))
                    superadmin_sig_content = drawn_sig_table
                except Exception as e:
                    print(f"[ERROR] Failed to decode superadmin drawn signature: {str(e)}")
                    # Fallback to text if image fails
                    superadmin_sig_content = Paragraph(f"<font size=7><b>Authorized Signatory</b><br/>AVENTUS Global Workforce Solutions<br/>Title: HR Director<br/>Date: {formatted_signed_date}</font>", small_text_style)
            else:
                # Handle typed signature (text)
                superadmin_sig_text = f"<font color='#1E40AF' size=12><i>{superadmin_signature_data_text}</i></font><br/><font size=7><b>Authorized Signatory</b><br/>AVENTUS Global Workforce Solutions<br/>Title: HR Director<br/>Date: {formatted_signed_date}</font>"
                superadmin_sig_content = Paragraph(superadmin_sig_text, small_text_style)
        else:
            # No superadmin signature yet
            superadmin_sig_content = Paragraph("_______________________<br/><font size=7>Authorized Signatory<br/>AVENTUS Global Workforce Solutions<br/>Title: HR Director<br/>Date: _______________</font>", small_text_style)
    else:
        # No signature yet
        contractor_sig_text = f"_______________________<br/><font size=7><b>{contractor_full_name}</b><br/>Signature<br/>Email: {email}<br/>Date: _______________</font>"
        contractor_sig_content = Paragraph(contractor_sig_text, small_text_style)
        superadmin_sig_content = Paragraph("_______________________<br/><font size=7>Authorized Signatory<br/>AVENTUS Global Workforce Solutions<br/>Title: HR Director<br/>Date: _______________</font>", small_text_style)

    signature_data = [
        [
            Paragraph("<b>COMPANY: AVENTUS</b>", body_style),
            Paragraph("<b>CONTRACTOR:</b>", body_style),
        ],
        [
            superadmin_sig_content,
            contractor_sig_content,
        ]
    ]
    sig_table = Table(signature_data, colWidths=[90*mm, 90*mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(sig_table)

    # Footer
    elements.append(Spacer(1, 8))
    footer_line = Table([['']], colWidths=[180*mm])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(footer_line)

    footer_text = """<font size=6 color='gray'>AVENTUS Global Workforce Solutions • Palm Jumeirah, Dubai, UAE • info@aventus.com • +971 4 XXX XXXX<br/>
    This document is confidential and proprietary. Unauthorized distribution is prohibited.</font>"""
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=small_text_style, alignment=TA_CENTER)))

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer
    buffer.seek(0)
    return buffer
