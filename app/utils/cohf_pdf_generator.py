from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os
import base64


def generate_cohf_pdf(contractor_data: dict, cohf_data: dict = None) -> BytesIO:
    """
    Generate a professional Confirmation of Hire Form (COHF) PDF - Version 2
    Matching the new Auxilium COHF template with all sections:
    - Reference
    - Employee Candidate Information
    - Remuneration Information
    - Additional Payments (Commission/Bonus table with Client Declaration)
    - Deployment Particulars
    - Documents Required
    - Signatures (4 signature blocks)

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

    # Get primary color from cohf_data or use default teal
    primary_color_hex = '#00A99D'
    if cohf_data and cohf_data.get('primary_color'):
        primary_color_hex = cohf_data.get('primary_color')

    # Define colors
    teal = colors.HexColor(primary_color_hex)
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
        fontSize=16,
        textColor=teal,
        spaceAfter=4*mm,
        spaceBefore=3*mm,
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
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=11,
    )

    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=11,
    )

    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=11,
    )

    italic_style = ParagraphStyle(
        'ItalicText',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        fontName='Helvetica-Oblique',
        leading=9,
        spaceBefore=2*mm,
        spaceAfter=2*mm,
    )

    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceBefore=3*mm,
    )

    checkbox_style = ParagraphStyle(
        'Checkbox',
        parent=styles['Normal'],
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=11,
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
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return header_table

    # Helper function for checkbox display
    def checkbox(checked=False):
        return "☑" if checked else "☐"

    # ============== PROFESSIONAL LETTERHEAD ==============
    # Try to use custom logo from cohf_data, otherwise use default
    logo_url = get_val('logo_url', '')
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'auxilium-logo.png')

    # Company name style
    company_name_style = ParagraphStyle(
        'CompanyName',
        fontSize=10,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        leading=13,
    )

    address_style = ParagraphStyle(
        'Address',
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica',
        alignment=TA_RIGHT,
        leading=11,
    )

    # Build letterhead
    logo = None
    if logo_url and logo_url.startswith('data:'):
        # Custom logo from base64
        try:
            base64_data = logo_url.split(',')[1]
            logo_bytes = base64.b64decode(base64_data)
            logo_buffer = BytesIO(logo_bytes)
            logo = Image(logo_buffer, width=40*mm, height=16*mm)
            logo.hAlign = 'LEFT'
        except Exception as e:
            print(f"Error loading custom logo: {e}")
            logo = None

    if logo is None and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=40*mm, height=16*mm)
            logo.hAlign = 'LEFT'
        except:
            logo = Paragraph("<font color='#00A99D' size='18'><b>auxilium</b></font>",
                           ParagraphStyle('LogoText', fontSize=18, textColor=teal, fontName='Helvetica-Bold'))
    elif logo is None:
        logo = Paragraph("<font color='#00A99D' size='18'><b>auxilium</b></font>",
                        ParagraphStyle('LogoText', fontSize=18, textColor=teal, fontName='Helvetica-Bold'))

    # Address block - get from cohf_data or use defaults
    to_company_name = get_val('to_company_name', 'Auxilium Management Group FZE')
    to_company_address = get_val('to_company_address', 'PO Box 333625')
    to_company_city = get_val('to_company_city', 'Dubai')
    to_company_country = get_val('to_company_country', 'UAE')
    to_company_website = get_val('to_company_website', 'www.auxilium.ae')

    address_block = Paragraph(
        f"<b>{to_company_name}</b><br/>"
        f"{to_company_address}<br/>"
        f"{to_company_city}<br/>"
        f"{to_company_country}<br/>"
        f"<font color='{primary_color_hex}'>{to_company_website}</font>",
        address_style
    )

    # Letterhead table
    letterhead_data = [[logo, address_block]]
    letterhead_table = Table(letterhead_data, colWidths=[85*mm, 85*mm])
    letterhead_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(letterhead_table)

    # Teal divider line
    elements.append(HRFlowable(width="100%", thickness=2, color=teal, spaceBefore=1*mm, spaceAfter=1*mm))

    # ============== TITLE ==============
    document_title = get_val('document_title', 'Confirmation of Hire Form - UAE')
    elements.append(Paragraph(document_title, title_style))

    # ============== FROM/TO SECTION ==============
    from_label_style = ParagraphStyle('FromLabel', fontSize=9, textColor=dark_gray, fontName='Helvetica-Bold')
    from_value_style = ParagraphStyle('FromValue', fontSize=8, textColor=dark_gray, fontName='Helvetica', leading=11)

    from_to_data = [
        [
            Paragraph("<b>From:</b>", from_label_style),
            Paragraph("<b>To:</b>", from_label_style)
        ],
        [
            Paragraph(get_val('from_company', '_______________________'), from_value_style),
            Paragraph(f"{to_company_name}<br/>{to_company_address}<br/>{to_company_city}<br/>{to_company_country}", from_value_style)
        ]
    ]
    from_to_table = Table(from_to_data, colWidths=[85*mm, 85*mm])
    from_to_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
    ]))
    elements.append(from_to_table)
    elements.append(Spacer(1, 3*mm))

    # ============== REFERENCE SECTION ==============
    section_title = get_val('section_reference', 'Reference')
    elements.append(create_section_header(section_title))

    document_reference = get_val('document_reference', 'Service Agreement dated and associated General Terms (the "Agreement")')

    ref_data = [
        [Paragraph("<b>Document Reference:</b>", label_style),
         Paragraph(document_reference, value_style)],
        [Paragraph("<b>Confirmation of Hire No:</b>", label_style),
         Paragraph(get_val('reference_no', 'COHF-00'), value_style)],
        [Paragraph("<b>Requested by:</b>", label_style),
         Paragraph(get_val('requested_by', ''), value_style)],
    ]
    ref_table = Table(ref_data, colWidths=[50*mm, 120*mm])
    ref_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(ref_table)

    reference_note = get_val('reference_note', 'Capitalised terms used in this form, but not defined in it shall have the meaning given to them in the Agreement.')
    reference_instruction = get_val('reference_instruction', 'Please fill the below form for the candidate to initiate your request:')

    elements.append(Paragraph(reference_note, italic_style))
    elements.append(Paragraph(reference_instruction, normal_style))
    elements.append(Spacer(1, 2*mm))

    # ============== EMPLOYEE CANDIDATE INFORMATION ==============
    section_title = get_val('section_employee_info', 'Employee Candidate Information')
    elements.append(create_section_header(section_title))

    # Build full name
    full_name = get_val('full_name')
    if not full_name:
        first_name = get_val('first_name', '')
        surname = get_val('surname', '')
        full_name = f"{first_name} {surname}".strip()

    emp_data = [
        [Paragraph("<b>Title</b>", label_style), Paragraph(get_val('title', ''), value_style)],
        [Paragraph("<b>Full Name - per passport</b>", label_style), Paragraph(full_name, value_style)],
        [Paragraph("<b>Nationality</b>", label_style), Paragraph(get_val('nationality', ''), value_style)],
        [Paragraph("<b>Date of Birth</b>", label_style), Paragraph(get_val('date_of_birth', get_val('dob', '')), value_style)],
        [Paragraph("<b>Marital Status</b>", label_style), Paragraph(get_val('marital_status', ''), value_style)],
        [Paragraph("<b>Mobile No.</b>", label_style), Paragraph(get_val('mobile', get_val('phone', '')), value_style)],
        [Paragraph("<b>Email Address</b>", label_style), Paragraph(get_val('email', ''), value_style)],
        [Paragraph("<b>UAE Address or Address in Home Country<br/>(if outside UAE)</b>", label_style),
         Paragraph(get_val('address', get_val('home_address', '')), value_style)],
        [Paragraph("<b>Current Location</b>", label_style),
         Paragraph(get_val('current_location', ''), value_style)],
        [Paragraph("<b>Current Visa Status</b>", label_style),
         Paragraph(get_val('visa_status', ''), value_style)],
    ]
    emp_table = Table(emp_data, colWidths=[50*mm, 120*mm])
    emp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 3*mm))

    # ============== REMUNERATION INFORMATION ==============
    section_title = get_val('section_remuneration', 'Remuneration Information')
    elements.append(create_section_header(section_title))

    rem_data = [
        [Paragraph("<b>Gross Salary</b>", label_style), Paragraph(get_val('gross_salary', ''), value_style)],
        [Paragraph("<b>Basic Salary</b>", label_style), Paragraph(get_val('basic_salary', get_val('basic_salary_monthly', '')), value_style)],
        [Paragraph("<b>Housing Allowance</b>", label_style), Paragraph(get_val('housing_allowance', get_val('housing_monthly', '')), value_style)],
        [Paragraph("<b>Transport Allowance</b>", label_style), Paragraph(get_val('transport_allowance', get_val('transport_monthly', '')), value_style)],
        [Paragraph("<b>Leave Allowance</b>", label_style), Paragraph(get_val('leave_allowance', ''), value_style)],
        [Paragraph("<b>Family Status</b>", label_style), Paragraph(get_val('family_status', ''), value_style)],
        [Paragraph("<b>Medical Insurance Category</b>", label_style), Paragraph(get_val('medical_insurance_category', ''), value_style)],
        [Paragraph("<b>Flight Entitlement</b>", label_style), Paragraph(get_val('flight_entitlement', ''), value_style)],
        [Paragraph("<b>Medical Insurance</b>", label_style), Paragraph(get_val('medical_insurance_cost', get_val('medical', '')), value_style)],
        [Paragraph("<b>Visa / Labour Card</b>", label_style), Paragraph(get_val('visa_labour_card', ''), value_style)],
        [Paragraph("<b>EOSB</b>", label_style), Paragraph(get_val('eosb', ''), value_style)],
        [Paragraph("<b>Management Fee</b>", label_style), Paragraph(get_val('management_fee', ''), value_style)],
    ]
    rem_table = Table(rem_data, colWidths=[50*mm, 120*mm])
    rem_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(rem_table)
    elements.append(Spacer(1, 3*mm))

    # ============== ADDITIONAL PAYMENTS ==============
    section_title = get_val('section_additional_payments', 'Additional Payments')
    elements.append(create_section_header(section_title))

    # Table header style
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=10,
    )

    # Additional Payments table
    add_pay_header = [
        Paragraph("<b>Payment Type</b>", table_header_style),
        Paragraph("<b>Criteria for Payment</b>", table_header_style),
        Paragraph("<b>Cap</b>", table_header_style),
        Paragraph("<b>Payment Frequency</b>", table_header_style),
        Paragraph("<b>Notes</b>", table_header_style),
    ]

    add_pay_data = [
        add_pay_header,
        [
            Paragraph("Commission", value_style),
            Paragraph(get_val('commission_criteria', ''), value_style),
            Paragraph(get_val('commission_cap', ''), value_style),
            Paragraph(get_val('commission_frequency', ''), value_style),
            Paragraph(get_val('commission_notes', ''), value_style),
        ],
        [
            Paragraph("Bonus", value_style),
            Paragraph(get_val('bonus_criteria', ''), value_style),
            Paragraph(get_val('bonus_cap', ''), value_style),
            Paragraph(get_val('bonus_frequency', ''), value_style),
            Paragraph(get_val('bonus_notes', ''), value_style),
        ],
    ]

    add_pay_table = Table(add_pay_data, colWidths=[28*mm, 45*mm, 25*mm, 32*mm, 40*mm])
    add_pay_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(add_pay_table)
    elements.append(Spacer(1, 2*mm))

    # Client Declaration
    declaration_style = ParagraphStyle(
        'Declaration',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=10,
    )

    elements.append(Paragraph("<b>Client Declaration:</b>", label_style))

    decl_1_checked = data.get('client_declaration_1_checked', False)
    decl_2_checked = data.get('client_declaration_2_checked', False)
    decl_1_text = get_val('client_declaration_1', 'I confirm that the above commission and/or bonus payments comply with UAE AML regulations and are not linked to any high-risk activities.')
    decl_2_text = get_val('client_declaration_2', 'I acknowledge that if the payments are uncapped, additional due diligence may be required by the Service Provider.')

    elements.append(Paragraph(f"{checkbox(decl_1_checked)} {decl_1_text}", declaration_style))
    elements.append(Paragraph(f"{checkbox(decl_2_checked)} {decl_2_text}", declaration_style))
    elements.append(Spacer(1, 3*mm))

    # ============== DEPLOYMENT PARTICULARS ==============
    section_title = get_val('section_deployment', 'Deployment Particulars')
    elements.append(create_section_header(section_title))

    dep_data = [
        [Paragraph("<b>Visa Type</b>", label_style), Paragraph(get_val('visa_type', ''), value_style)],
        [Paragraph("<b>Job Title</b>", label_style), Paragraph(get_val('job_title', get_val('role', '')), value_style)],
        [Paragraph("<b>Company Name</b>", label_style),
         Paragraph(get_val('company_name', get_val('client_name', '')), value_style)],
        [Paragraph("<b>Employee Work Location</b>", label_style), Paragraph(get_val('work_location', ''), value_style)],
        [Paragraph("<b>Expected Start Date</b>", label_style), Paragraph(get_val('expected_start_date', get_val('start_date', '')), value_style)],
        [Paragraph("<b>Expected Tenure</b>", label_style), Paragraph(get_val('expected_tenure', get_val('duration', '')), value_style)],
        [Paragraph("<b>Probation Period (Months)</b>", label_style), Paragraph(get_val('probation_period', ''), value_style)],
        [Paragraph("<b>Notice Period (Months)</b>", label_style), Paragraph(get_val('notice_period', ''), value_style)],
        [Paragraph("<b>Annual Leave Type<br/>(Calendar/Working Days)</b>", label_style), Paragraph(get_val('annual_leave_type', ''), value_style)],
        [Paragraph("<b>Annual Leave Days</b>", label_style), Paragraph(get_val('annual_leave_days', ''), value_style)],
        [Paragraph("<b>Weekly Working Days</b>", label_style), Paragraph(get_val('weekly_working_days', ''), value_style)],
        [Paragraph("<b>Weekend Days</b>", label_style), Paragraph(get_val('weekend_days', ''), value_style)],
        [Paragraph("<b>Chargeable Rate</b>", label_style), Paragraph(get_val('chargeable_rate', ''), value_style)],
        [Paragraph("<b>Additional Terms &amp; Conditions</b>", label_style), Paragraph(get_val('additional_terms', ''), value_style)],
    ]
    dep_table = Table(dep_data, colWidths=[50*mm, 120*mm])
    dep_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(dep_table)
    elements.append(Spacer(1, 3*mm))

    # ============== DOCUMENTS REQUIRED ==============
    section_title = get_val('section_documents_required', 'Documents Required')
    elements.append(create_section_header(section_title))

    doc_passport = checkbox(data.get('doc_passport_copy', False))
    doc_visa = checkbox(data.get('doc_current_visa', False))
    doc_photo = checkbox(data.get('doc_passport_photo', False))
    doc_degree = checkbox(data.get('doc_attested_degree', False))
    doc_cancellation = checkbox(data.get('doc_visa_cancellation', False))
    doc_emirates_id = checkbox(data.get('doc_emirates_id', False))

    docs_data = [
        [
            Paragraph(f"{doc_passport} Passport Copy (in colour)", checkbox_style),
            Paragraph(f"{doc_visa} Current Visa Copy", checkbox_style),
            Paragraph(f"{doc_photo} Passport Size Photograph", checkbox_style),
        ],
        [
            Paragraph(f"{doc_degree} Attested University Degree", checkbox_style),
            Paragraph(f"{doc_cancellation} Visa Cancellation (if any)", checkbox_style),
            Paragraph(f"{doc_emirates_id} Emirates ID Copy (if any)", checkbox_style),
        ],
    ]
    docs_table = Table(docs_data, colWidths=[56*mm, 56*mm, 58*mm])
    docs_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(docs_table)

    # Disclaimer
    disclaimer_text = get_val('disclaimer_text', 'Note: The Employment Visa application process for the Candidate is subject to government approvals and Auxilium will not be held responsible for any rejections by the relevant authorities.')
    elements.append(Paragraph(disclaimer_text, italic_style))
    elements.append(Spacer(1, 4*mm))

    # ============== SIGNATURES SECTION (4 Signature Blocks) ==============
    section_title = get_val('section_signatures', 'Signatures & Company Stamp')
    elements.append(create_section_header(section_title))
    elements.append(Spacer(1, 3*mm))

    sig_text_style = ParagraphStyle('SigText', fontSize=8, textColor=dark_gray, fontName='Helvetica', leading=11)
    sig_text_bold = ParagraphStyle('SigTextBold', fontSize=8, textColor=dark_gray, fontName='Helvetica-Bold', leading=11)

    # Get signatory names from cohf_data
    signatory_name = get_val('signatory_name', 'Lawrence Coward')
    signatory_name_aventus = get_val('signatory_name_aventus', 'Richard White')

    # Check if third party has signed
    third_party_signer = get_val('third_party_signer_name', '')
    third_party_signature = get_val('third_party_signature', '')
    signature_date = get_val('signature_date', '')
    signature_type = get_val('third_party_signature_type', 'typed')

    # Build third party signature block
    def build_signature_block(sig_data=None, sig_name='', sig_date='', sig_type='typed'):
        if sig_name and sig_data:
            if sig_type == 'typed':
                return Paragraph(
                    f"<br/><i><font size='12'>{sig_data}</font></i><br/>"
                    f"______________________________<br/>"
                    f"[Signed by: {sig_name}]<br/>"
                    f"<font size='6'>{sig_date}</font>",
                    sig_text_style
                )
            else:
                try:
                    if sig_data.startswith('data:'):
                        base64_data = sig_data.split(',')[1]
                    else:
                        base64_data = sig_data
                    sig_bytes = base64.b64decode(base64_data)
                    sig_buffer = BytesIO(sig_bytes)
                    sig_image = Image(sig_buffer, width=50*mm, height=18*mm)
                    sig_image.hAlign = 'LEFT'

                    sig_block_data = [
                        [sig_image],
                        [Paragraph("______________________________", sig_text_style)],
                        [Paragraph(f"[Signed by: {sig_name}]", sig_text_style)],
                        [Paragraph(f"<font size='6'>{sig_date}</font>", sig_text_style)]
                    ]
                    sig_block = Table(sig_block_data, colWidths=[75*mm])
                    sig_block.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ]))
                    return sig_block
                except Exception as e:
                    print(f"Error creating signature image: {e}")
                    return Paragraph(
                        f"<br/><i>[Digitally Signed]</i><br/>"
                        f"______________________________<br/>"
                        f"[Signed by: {sig_name}]<br/>"
                        f"<font size='6'>{sig_date}</font>",
                        sig_text_style
                    )
        else:
            return Paragraph(
                "<br/><br/>______________________________<br/>[Authorised Signatory]",
                sig_text_style
            )

    # 4 Signature blocks as per template v2: 2 for Auxilium, 2 for Aventus
    sig_row_1 = [
        # Auxilium Signatory 1
        [
            Paragraph(f"Signed by {signatory_name} duly authorised", sig_text_style),
            Paragraph("for and on behalf of", sig_text_style),
            Paragraph(f"<b>{to_company_name}</b>", sig_text_bold),
            Paragraph("<br/><br/>______________________________<br/>[Authorised Signatory]", sig_text_style),
        ],
        # Auxilium Signatory 2
        [
            Paragraph(f"Signed by {signatory_name} duly authorised", sig_text_style),
            Paragraph("for and on behalf of", sig_text_style),
            Paragraph(f"<b>{to_company_name}</b>", sig_text_bold),
            Paragraph("<br/><br/>______________________________<br/>[Authorised Signatory]", sig_text_style),
        ],
    ]

    # Build client signature with potential signature
    client_company_name = get_val('company_name', get_val('client_name', 'Client Company'))

    sig_row_2 = [
        # Aventus Signatory 1
        [
            Paragraph(f"Signed by {signatory_name_aventus} duly authorised", sig_text_style),
            Paragraph("for and on behalf of", sig_text_style),
            Paragraph("<b>Aventus Talent Consultancy</b>", sig_text_bold),
            Paragraph("<br/><br/>______________________________<br/>[Authorised Signatory]", sig_text_style),
        ],
        # Aventus Signatory 2 / Client Signatory
        [
            Paragraph(f"Signed by {signatory_name_aventus} duly authorised", sig_text_style),
            Paragraph("for and on behalf of", sig_text_style),
            Paragraph("<b>Aventus Talent Consultancy</b>", sig_text_bold),
            build_signature_block(third_party_signature, third_party_signer, signature_date, signature_type),
        ],
    ]

    # Create signature tables
    def create_sig_box(content_list):
        inner_table = Table([[item] for item in content_list], colWidths=[80*mm])
        inner_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return inner_table

    sig_table_1 = Table([
        [create_sig_box(sig_row_1[0]), create_sig_box(sig_row_1[1])]
    ], colWidths=[85*mm, 85*mm])
    sig_table_1.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (0, 0), 0.5, colors.lightgrey),
        ('BOX', (1, 0), (1, 0), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(sig_table_1)
    elements.append(Spacer(1, 2*mm))

    sig_table_2 = Table([
        [create_sig_box(sig_row_2[0]), create_sig_box(sig_row_2[1])]
    ], colWidths=[85*mm, 85*mm])
    sig_table_2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (0, 0), 0.5, colors.lightgrey),
        ('BOX', (1, 0), (1, 0), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(sig_table_2)
    elements.append(Spacer(1, 4*mm))

    # Footer note
    footer_note = get_val('footer_note', 'Note: Please sign and stamp above and submit this form for further process.')
    elements.append(Paragraph(footer_note, small_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
