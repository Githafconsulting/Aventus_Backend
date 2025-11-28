from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os
import base64


def generate_cohf_pdf(contractor_data: dict, cohf_data: dict = None) -> BytesIO:
    """
    Generate a professional Confirmation of Hire Form (COHF) PDF with Auxilium branding

    Args:
        contractor_data: Dictionary containing contractor information
        cohf_data: Dictionary containing COHF form field values

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document with proper margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Define Auxilium colors (teal from logo)
    teal = colors.HexColor('#00A99D')
    dark_gray = colors.HexColor('#333333')
    light_gray = colors.HexColor('#F5F5F5')
    white = colors.white

    # Merge cohf_data into contractor_data for easier access
    data = {**contractor_data}
    if cohf_data:
        data.update(cohf_data)

    # ============== STYLES ==============
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=teal,
        spaceAfter=6*mm,
        spaceBefore=4*mm,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=white,
        spaceBefore=0,
        spaceAfter=0,
        fontName='Helvetica-Bold',
        leftIndent=0,
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=12,
    )

    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=12,
    )

    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=12,
    )

    italic_style = ParagraphStyle(
        'ItalicText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        fontName='Helvetica-Oblique',
        leading=10,
        spaceBefore=3*mm,
        spaceAfter=3*mm,
    )

    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceBefore=4*mm,
    )

    # Helper function to get value or empty string
    def get_val(key, default=''):
        return str(data.get(key, default) or default)

    # Helper function to create section header
    def create_section_header(title):
        header_table = Table(
            [[Paragraph(title, section_header_style)]],
            colWidths=[170*mm]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), teal),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return header_table

    # ============== PROFESSIONAL LETTERHEAD ==============
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'auxilium-logo.png')

    # Company name style
    company_name_style = ParagraphStyle(
        'CompanyName',
        fontSize=11,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        leading=14,
    )

    address_style = ParagraphStyle(
        'Address',
        fontSize=9,
        textColor=dark_gray,
        fontName='Helvetica',
        alignment=TA_RIGHT,
        leading=12,
    )

    # Build letterhead
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=45*mm, height=18*mm)
            logo.hAlign = 'LEFT'
        except:
            logo = Paragraph("<font color='#00A99D' size='20'><b>auxilium</b></font>",
                           ParagraphStyle('LogoText', fontSize=20, textColor=teal, fontName='Helvetica-Bold'))
    else:
        logo = Paragraph("<font color='#00A99D' size='20'><b>auxilium</b></font>",
                        ParagraphStyle('LogoText', fontSize=20, textColor=teal, fontName='Helvetica-Bold'))

    # Address block
    address_block = Paragraph(
        "<b>Auxilium Management Group FZE</b><br/>"
        "PO Box 333625<br/>"
        "Dubai, United Arab Emirates<br/>"
        "www.auxilium.ae",
        address_style
    )

    # Letterhead table
    letterhead_data = [[logo, address_block]]
    letterhead_table = Table(letterhead_data, colWidths=[85*mm, 85*mm])
    letterhead_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
    ]))
    elements.append(letterhead_table)

    # Teal divider line
    elements.append(HRFlowable(width="100%", thickness=2, color=teal, spaceBefore=2*mm, spaceAfter=2*mm))

    # ============== TITLE ==============
    elements.append(Paragraph("Confirmation of Hire Form - UAE", title_style))

    # ============== FROM/TO SECTION ==============
    from_label_style = ParagraphStyle('FromLabel', fontSize=10, textColor=dark_gray, fontName='Helvetica-Bold')
    from_value_style = ParagraphStyle('FromValue', fontSize=9, textColor=dark_gray, fontName='Helvetica', leading=12)

    from_to_data = [
        [
            Paragraph("<b>From:</b>", from_label_style),
            Paragraph("<b>To:</b>", from_label_style)
        ],
        [
            Paragraph(get_val('from_company', '_______________________'), from_value_style),
            Paragraph("Auxilium Management Group FZE<br/>PO Box 333625<br/>Dubai, UAE", from_value_style)
        ]
    ]
    from_to_table = Table(from_to_data, colWidths=[85*mm, 85*mm])
    from_to_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(from_to_table)
    elements.append(Spacer(1, 4*mm))

    # ============== REFERENCE SECTION ==============
    elements.append(create_section_header("Reference"))

    ref_data = [
        [Paragraph("<b>Document Reference:</b>", label_style),
         Paragraph('Commercial Terms dated and associated General Terms (the "Agreement")', value_style)],
        [Paragraph("<b>Confirmation of Hire No:</b>", label_style),
         Paragraph(get_val('reference_no', 'COHF-00'), value_style)],
        [Paragraph("<b>Requested by:</b>", label_style),
         Paragraph(get_val('requested_by', ''), value_style)],
    ]
    ref_table = Table(ref_data, colWidths=[55*mm, 115*mm])
    ref_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(ref_table)

    elements.append(Paragraph(
        "Capitalised terms used in this form, but not defined in it shall have the meaning given to them in the Agreement.",
        italic_style
    ))
    elements.append(Paragraph(
        "Please fill the below form for the candidate in order to initiate your request:",
        normal_style
    ))
    elements.append(Spacer(1, 3*mm))

    # ============== EMPLOYEE CANDIDATE INFORMATION ==============
    elements.append(create_section_header("Employee Candidate Information"))

    # Build full name
    full_name = get_val('full_name')
    if not full_name:
        first_name = get_val('first_name', '')
        surname = get_val('surname', '')
        full_name = f"{first_name} {surname}".strip()

    emp_data = [
        [Paragraph("<b>Title</b>", label_style), Paragraph(get_val('title', ''), value_style)],
        [Paragraph("<b>Full Name (inc. Middle Names)</b>", label_style), Paragraph(full_name, value_style)],
        [Paragraph("<b>Nationality</b>", label_style), Paragraph(get_val('nationality', ''), value_style)],
        [Paragraph("<b>Date of Birth</b>", label_style), Paragraph(get_val('date_of_birth', get_val('dob', '')), value_style)],
        [Paragraph("<b>Marital Status</b>", label_style), Paragraph(get_val('marital_status', 'Married / Single'), value_style)],
        [Paragraph("<b>Mobile No.</b>", label_style), Paragraph(get_val('mobile', get_val('phone', '')), value_style)],
        [Paragraph("<b>Email Address</b>", label_style), Paragraph(get_val('email', ''), value_style)],
        [Paragraph("<b>UAE Address or Address in Home Country<br/>(if outside UAE)</b>", label_style),
         Paragraph(get_val('address', get_val('home_address', '')), value_style)],
        [Paragraph("<b>Current Location</b>", label_style),
         Paragraph(get_val('current_location', '☐ Outside UAE       ☐ Inside UAE'), value_style)],
        [Paragraph("<b>Current Visa Status</b>", label_style),
         Paragraph(get_val('visa_status', '☐ Existing Residence Visa<br/>☐ Tourist Visa<br/>☐ Spouse or Parent Sponsored'), value_style)],
    ]
    emp_table = Table(emp_data, colWidths=[55*mm, 115*mm])
    emp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4*mm))

    # ============== REMUNERATION INFORMATION ==============
    elements.append(create_section_header("Remuneration Information"))

    rem_data = [
        [Paragraph("<b>Gross Salary</b>", label_style), Paragraph(get_val('gross_salary', ''), value_style)],
        [Paragraph("<b>Basic Salary</b>", label_style), Paragraph(get_val('basic_salary', get_val('basic_salary_monthly', '')), value_style)],
        [Paragraph("<b>General Allowance</b>", label_style), Paragraph(get_val('general_allowance', ''), value_style)],
        [Paragraph("<b>Transport Allowance</b>", label_style), Paragraph(get_val('transport_allowance', get_val('transport_monthly', '')), value_style)],
        [Paragraph("<b>Other Allowances</b>", label_style), Paragraph(get_val('other_allowances', get_val('other_monthly', '')), value_style)],
        [Paragraph("<b>Family Status</b>", label_style),
         Paragraph(get_val('family_status', "Yes / No – if yes please confirm what's included in the Family Status"), value_style)],
        [Paragraph("<b>Medical Insurance</b>", label_style), Paragraph(get_val('medical_insurance', get_val('medical', '')), value_style)],
        [Paragraph("<b>Flight Entitlement</b>", label_style), Paragraph(get_val('flight_entitlement', ''), value_style)],
    ]
    rem_table = Table(rem_data, colWidths=[55*mm, 115*mm])
    rem_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(rem_table)
    elements.append(Spacer(1, 4*mm))

    # ============== DEPLOYMENT PARTICULARS ==============
    elements.append(create_section_header("Deployment Particulars"))

    dep_data = [
        [Paragraph("<b>Visa Type</b>", label_style),
         Paragraph(get_val('visa_type', '☐ 2YR Visa - ☐ Urgent<br/>☐ Work Permit (only)<br/>☐ Labour Card (only)<br/>☐ Mission Visa'), value_style)],
        [Paragraph("<b>Job Title</b>", label_style), Paragraph(get_val('job_title', get_val('role', '')), value_style)],
        [Paragraph("<b>Company Name</b>", label_style),
         Paragraph(get_val('company_name', get_val('client_name', 'Name of the company the candidate will be working for')), value_style)],
        [Paragraph("<b>Expected Start Date</b>", label_style), Paragraph(get_val('expected_start_date', get_val('start_date', '')), value_style)],
        [Paragraph("<b>Expected Tenure</b>", label_style), Paragraph(get_val('expected_tenure', get_val('duration', '')), value_style)],
    ]
    dep_table = Table(dep_data, colWidths=[55*mm, 115*mm])
    dep_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(dep_table)

    # Disclaimer
    elements.append(Paragraph(
        "The Candidate is subject to government approvals and Auxilium will not be held responsible for any rejections by the relevant authorities.",
        italic_style
    ))
    elements.append(Spacer(1, 6*mm))

    # ============== SIGNATURES SECTION ==============
    elements.append(create_section_header("Signatures & Company Stamp"))
    elements.append(Spacer(1, 4*mm))

    sig_text_style = ParagraphStyle('SigText', fontSize=9, textColor=dark_gray, fontName='Helvetica', leading=12)

    # Check if third party has signed
    third_party_signer = get_val('third_party_signer_name', '')
    third_party_signature = get_val('third_party_signature', '')
    signature_date = get_val('signature_date', '')
    signature_type = get_val('third_party_signature_type', 'typed')

    # Build the third party signature block
    third_party_sig_elements = []

    if third_party_signer and third_party_signature:
        # If typed signature, display the name in a cursive-like style
        if signature_type == 'typed':
            third_party_sig_block = Paragraph(
                f"<br/><br/><i><font size='14'>{third_party_signature}</font></i><br/>"
                f"______________________________<br/>"
                f"[Signed by: {third_party_signer}]<br/>"
                f"<font size='7'>{signature_date}</font>",
                sig_text_style
            )
        else:
            # For drawn signatures, decode base64 and create image
            try:
                # The signature is base64 data URL like "data:image/png;base64,..."
                if third_party_signature.startswith('data:'):
                    # Extract the base64 part
                    base64_data = third_party_signature.split(',')[1]
                else:
                    base64_data = third_party_signature

                # Decode base64 to bytes
                sig_bytes = base64.b64decode(base64_data)
                sig_buffer = BytesIO(sig_bytes)

                # Create image from the signature
                sig_image = Image(sig_buffer, width=60*mm, height=20*mm)
                sig_image.hAlign = 'LEFT'

                # Create a mini table for the signature block with image
                sig_block_data = [
                    [sig_image],
                    [Paragraph("______________________________", sig_text_style)],
                    [Paragraph(f"[Signed by: {third_party_signer}]", sig_text_style)],
                    [Paragraph(f"<font size='7'>{signature_date}</font>", sig_text_style)]
                ]
                third_party_sig_block = Table(sig_block_data, colWidths=[80*mm])
                third_party_sig_block.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ]))
            except Exception as e:
                # Fallback if image fails
                print(f"Error creating signature image: {e}")
                third_party_sig_block = Paragraph(
                    f"<br/><br/><i>[Digitally Signed]</i><br/>"
                    f"______________________________<br/>"
                    f"[Signed by: {third_party_signer}]<br/>"
                    f"<font size='7'>{signature_date}</font>",
                    sig_text_style
                )
    else:
        third_party_sig_block = Paragraph(
            "<br/><br/><br/>______________________________<br/>[Authorised Signatory]",
            sig_text_style
        )

    sig_data = [
        [
            Paragraph("Signed by Lawrence Coward duly authorised<br/>for and on behalf of<br/><b>Auxilium Management Group FZE</b>", sig_text_style),
            Paragraph(f"Signed by duly authorised<br/>for and on behalf of<br/><b>{get_val('company_name', get_val('client_name', 'XXXX'))}</b>", sig_text_style)
        ],
        [
            Paragraph("<br/><br/><br/>______________________________<br/>[Authorised Signatory]", sig_text_style),
            third_party_sig_block
        ]
    ]
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 6*mm))

    # Footer note
    elements.append(Paragraph(
        "Note: Please sign and stamp above and submit this form for further process.",
        small_style
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
