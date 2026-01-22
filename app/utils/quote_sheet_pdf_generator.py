from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import base64
import os


def format_currency(value, default="-"):
    """Format a number as currency with comma separators"""
    if value is None or value == "":
        return default
    try:
        num = float(value)
        if num == 0:
            return "-"
        return f"{num:,.2f}"
    except (ValueError, TypeError):
        return default


def generate_quote_sheet_pdf(quote_sheet_data: dict) -> BytesIO:
    """
    Generate Quote Sheet PDF matching the new A-H section structure.
    Uses dark red (#9B1B1B) as the primary color like FNRCO branding.
    Includes 15% VAT on Medical Insurance and Service Charge only.

    Args:
        quote_sheet_data: Dictionary containing all quote sheet form data

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=8*mm,
        bottomMargin=8*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Get primary color from data or use default dark red
    primary_color_hex = quote_sheet_data.get('primary_color', '#9B1B1B')
    try:
        primary_color = colors.HexColor(primary_color_hex)
    except:
        primary_color = colors.HexColor('#9B1B1B')

    # Colors
    light_gray = colors.HexColor('#f3f4f6')
    highlight_bg = colors.HexColor('#f5e6e6')  # Light red background for totals
    dark_gray = colors.HexColor('#1f2937')
    border_gray = colors.HexColor('#d1d5db')

    # Helper to get value
    def get_val(key, default=""):
        val = quote_sheet_data.get(key)
        if val is None:
            return default
        return str(val) if not isinstance(val, (int, float)) else val

    def get_num(key, default=None):
        val = quote_sheet_data.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    # Styles
    title_style = ParagraphStyle(
        'Title',
        fontSize=14,
        textColor=primary_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2*mm,
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontSize=8,
        textColor=colors.white,
        fontName='Helvetica-Bold',
    )

    cell_style = ParagraphStyle(
        'Cell',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=9,
    )

    cell_bold_style = ParagraphStyle(
        'CellBold',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=9,
    )

    cell_right_style = ParagraphStyle(
        'CellRight',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=9,
        alignment=TA_RIGHT,
    )

    cell_right_bold_style = ParagraphStyle(
        'CellRightBold',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=9,
        alignment=TA_RIGHT,
    )

    header_cell_style = ParagraphStyle(
        'HeaderCell',
        fontSize=7,
        textColor=colors.HexColor('#374151'),
        fontName='Helvetica-Bold',
        leading=9,
    )

    label_style = ParagraphStyle(
        'Label',
        fontSize=7,
        textColor=colors.HexColor('#374151'),
        fontName='Helvetica-Bold',
        leading=9,
    )

    value_style = ParagraphStyle(
        'Value',
        fontSize=7,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=9,
    )

    # ============== HEADER WITH LOGOS ==============
    # Try to load FNRCO logo
    fnrco_logo_element = None
    logo_url = get_val('logo_url', '')

    if logo_url:
        try:
            if logo_url.startswith('data:image'):
                import re
                match = re.match(r'data:image/(\w+);base64,(.+)', logo_url)
                if match:
                    img_data = base64.b64decode(match.group(2))
                    img_buffer = BytesIO(img_data)
                    fnrco_logo_element = Image(img_buffer, width=22*mm, height=12*mm)
            elif logo_url.startswith('http'):
                import urllib.request
                with urllib.request.urlopen(logo_url, timeout=5) as response:
                    img_data = response.read()
                    img_buffer = BytesIO(img_data)
                    fnrco_logo_element = Image(img_buffer, width=22*mm, height=12*mm)
            else:
                if os.path.exists(logo_url):
                    fnrco_logo_element = Image(logo_url, width=22*mm, height=12*mm)
        except Exception as e:
            print(f"Error loading logo: {e}")

    # Try default FNRCO logo paths
    if fnrco_logo_element is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)

        default_logo_paths = [
            os.path.join(app_dir, 'static', 'fnrco-logo.png'),
            os.path.join(current_dir, 'static', 'fnrco-logo.png'),
            '/app/static/fnrco-logo.png',
            'static/fnrco-logo.png',
            'app/static/fnrco-logo.png',
        ]
        for path in default_logo_paths:
            if os.path.exists(path):
                try:
                    fnrco_logo_element = Image(path, width=22*mm, height=12*mm)
                    break
                except:
                    pass

    # Load Aventus logo for right side
    aventus_logo_element = None
    aventus_logo_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'av-logo.png'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'av-logo.png'),
        '/app/static/av-logo.png',
        'static/av-logo.png',
        'app/static/av-logo.png',
    ]

    for path in aventus_logo_paths:
        if os.path.exists(path):
            try:
                aventus_logo_element = Image(path, width=22*mm, height=12*mm)
                break
            except:
                pass

    # If no local file, try to fetch from Supabase
    if aventus_logo_element is None:
        try:
            import urllib.request
            aventus_url = "https://mhrmbwsjjivckttokdiz.supabase.co/storage/v1/object/public/assets/logos/av-logo.png"
            with urllib.request.urlopen(aventus_url, timeout=5) as response:
                img_data = response.read()
                img_buffer = BytesIO(img_data)
                aventus_logo_element = Image(img_buffer, width=22*mm, height=12*mm)
        except Exception as e:
            print(f"Error loading Aventus logo: {e}")

    # Build header with logos on both sides and centered title
    left_element = fnrco_logo_element if fnrco_logo_element else Paragraph("", cell_style)
    right_element = aventus_logo_element if aventus_logo_element else Paragraph("", cell_style)

    # Center element with company name and title
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=cell_style,
        fontSize=12,
        textColor=primary_color,
        alignment=1,  # Center
        fontName='Helvetica-Bold',
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=cell_style,
        fontSize=10,
        textColor=primary_color,
        alignment=1,  # Center
        fontName='Helvetica',
    )
    center_element = Table([
        [Paragraph("FIRST NATIONAL HUMAN RESOURCES COMPANY", company_name_style)],
        [Paragraph("Cost Estimation Sheet", subtitle_style)],
    ], colWidths=[80*mm])
    center_element.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    header_data = [[left_element, center_element, right_element]]

    header_table = Table(header_data, colWidths=[50*mm, 90*mm, 50*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, primary_color),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3*mm))

    # ============== SECTIONS A & B SIDE BY SIDE ==============
    def create_section_header_cell(title, width):
        return Table(
            [[Paragraph(title, section_header_style)]],
            colWidths=[width]
        )

    # Section A - Client Information
    section_a_header = create_section_header_cell("A. CLIENT INFORMATION", 93*mm)
    section_a_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    section_a_data = [
        [Paragraph("<b>Name</b>", label_style), Paragraph(get_val('client_name', 'Aventus Talent Consultancy LLC'), value_style)],
        [Paragraph("<b>Department</b>", label_style), Paragraph(get_val('client_department', ''), value_style)],
        [Paragraph("<b>Email Address</b>", label_style), Paragraph(get_val('client_email', ''), value_style)],
        [Paragraph("<b>Mobile No</b>", label_style), Paragraph(get_val('client_mobile', ''), value_style)],
        [Paragraph("<b>Contact Person</b>", label_style), Paragraph(get_val('client_contact_person', ''), value_style)],
    ]

    section_a_table = Table(section_a_data, colWidths=[28*mm, 65*mm])
    section_a_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    # Section B - Costing Information
    section_b_header = create_section_header_cell("B. COSTING INFORMATION", 93*mm)
    section_b_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    section_b_data = [
        [Paragraph("<b>Costing Type</b>", label_style), Paragraph(get_val('costing_type', 'Cost Plus'), value_style)],
        [Paragraph("<b>Duration</b>", label_style), Paragraph(get_val('duration', '12 Months'), value_style)],
        [Paragraph("<b>Recruitment Type</b>", label_style), Paragraph(get_val('recruitment_type', 'Local'), value_style)],
        [Paragraph("<b>Issued Date</b>", label_style), Paragraph(get_val('issued_date', ''), value_style)],
        [Paragraph("<b>Working Hours</b>", label_style), Paragraph(get_val('working_hours', '48 Hours Per Week'), value_style)],
    ]

    section_b_table = Table(section_b_data, colWidths=[28*mm, 65*mm])
    section_b_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    # Combine A and B side by side
    ab_combined = Table([
        [section_a_header, section_b_header],
        [section_a_table, section_b_table],
    ], colWidths=[93*mm, 93*mm], hAlign='CENTER')
    ab_combined.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(ab_combined)
    elements.append(Spacer(1, 2*mm))

    # ============== SECTIONS C & D SIDE BY SIDE ==============
    # Section C - Candidate / Employee Information
    section_c_header = create_section_header_cell("C. CANDIDATE / EMPLOYEE INFORMATION", 93*mm)
    section_c_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    section_c_data = [
        [Paragraph("<b>Name</b>", label_style), Paragraph(get_val('employee_name', ''), value_style)],
        [Paragraph("<b>Position</b>", label_style), Paragraph(get_val('position', ''), value_style)],
        [Paragraph("<b>Nationality</b>", label_style), Paragraph(get_val('nationality', ''), value_style)],
        [Paragraph("<b>Profession</b>", label_style), Paragraph(get_val('profession', ''), value_style)],
        [Paragraph("<b>Status</b>", label_style), Paragraph(get_val('family_status', ''), value_style)],
        [Paragraph("<b>No. of Dependents</b>", label_style), Paragraph(get_val('num_dependents', '0'), value_style)],
        [Paragraph("<b>Vacation</b>", label_style), Paragraph(get_val('vacation_days', '30 calendar days every year'), value_style)],
        [Paragraph("<b>Medical Insurance</b>", label_style), Paragraph(get_val('medical_insurance_class', 'A1 Class Medical Insurance'), value_style)],
    ]

    section_c_table = Table(section_c_data, colWidths=[28*mm, 65*mm])
    section_c_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    # Section D - Salary Details
    section_d_header = create_section_header_cell("D. SALARY DETAILS", 93*mm)
    section_d_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    # Calculate total salary
    basic_salary = get_num('basic_salary', 0) or 0
    housing_allowance = get_num('housing_allowance', 0) or 0
    transportation_allowance = get_num('transportation_allowance', 0) or 0
    food_allowance = get_num('food_allowance', 0) or 0
    mobile_allowance = get_num('mobile_allowance', 0) or 0
    fixed_ot = get_num('fixed_ot', 0) or 0
    other_allowance = get_num('other_allowance', 0) or 0
    total_salary = basic_salary + housing_allowance + transportation_allowance + food_allowance + mobile_allowance + fixed_ot + other_allowance

    section_d_data = [
        [Paragraph("<b>Basic Salary</b>", label_style), Paragraph(f"SAR {format_currency(get_num('basic_salary'))}", cell_right_style)],
        [Paragraph("<b>Housing Allowance</b>", label_style), Paragraph(f"SAR {format_currency(get_num('housing_allowance'))}", cell_right_style)],
        [Paragraph("<b>Transportation Allowance</b>", label_style), Paragraph(f"SAR {format_currency(get_num('transportation_allowance'))}", cell_right_style)],
        [Paragraph("<b>Food Allowance</b>", label_style), Paragraph(f"SAR {format_currency(get_num('food_allowance'))}", cell_right_style)],
        [Paragraph("<b>Mobile Allowance</b>", label_style), Paragraph(f"SAR {format_currency(get_num('mobile_allowance'))}", cell_right_style)],
        [Paragraph("<b>Fixed OT</b>", label_style), Paragraph(f"SAR {format_currency(get_num('fixed_ot'))}", cell_right_style)],
        [Paragraph("<b>Other Allowance</b>", label_style), Paragraph(f"SAR {format_currency(get_num('other_allowance'))}", cell_right_style)],
        [Paragraph("<b>TOTAL SALARY</b>", cell_bold_style), Paragraph(f"<b>SAR {format_currency(total_salary)}</b>", cell_right_bold_style)],
    ]

    section_d_table = Table(section_d_data, colWidths=[40*mm, 53*mm])
    section_d_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), highlight_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    # Combine C and D side by side
    cd_combined = Table([
        [section_c_header, section_d_header],
        [section_c_table, section_d_table],
    ], colWidths=[93*mm, 93*mm], hAlign='CENTER')
    cd_combined.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(cd_combined)
    elements.append(Spacer(1, 2*mm))

    # ============== COST TABLES HELPER ==============
    def create_cost_section(title, rows_config, totals_label):
        """Create a cost section with one-time, annual, monthly columns"""
        # Section header
        header = Table(
            [[Paragraph(title, section_header_style)]],
            colWidths=[190*mm]
        )
        header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        # Column headers
        cost_header = [
            Paragraph("<b>DESCRIPTION</b>", header_cell_style),
            Paragraph("<b>ONE TIME</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>ANNUAL</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>MONTHLY</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>REMARKS / CLARIFICATION</b>", header_cell_style),
        ]

        cost_data = [cost_header]

        total_one_time = 0
        total_annual = 0
        total_monthly = 0

        for prefix, label in rows_config:
            one_time = get_num(f'{prefix}_one_time')
            annual = get_num(f'{prefix}_annual')
            monthly = get_num(f'{prefix}_monthly')
            remarks = get_val(f'{prefix}_remarks', '')

            total_one_time += one_time or 0
            total_annual += annual or 0
            total_monthly += monthly or 0

            cost_data.append([
                Paragraph(label, cell_style),
                Paragraph(format_currency(one_time), cell_right_style),
                Paragraph(format_currency(annual), cell_right_style),
                Paragraph(format_currency(monthly), cell_right_style),
                Paragraph(remarks, cell_style),
            ])

        # Total row
        cost_data.append([
            Paragraph(f"<b>{totals_label}</b>", cell_bold_style),
            Paragraph(f"<b>{format_currency(total_one_time if total_one_time > 0 else None)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_annual if total_annual > 0 else None)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_monthly if total_monthly > 0 else None)}</b>", cell_right_bold_style),
            Paragraph("", cell_style),
        ])

        cost_table = Table(cost_data, colWidths=[50*mm, 26*mm, 26*mm, 26*mm, 62*mm])
        cost_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
            ('BACKGROUND', (0, 0), (-1, 0), light_gray),
            ('BACKGROUND', (0, -1), (-1, -1), highlight_bg),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        return header, cost_table, total_one_time, total_annual, total_monthly

    # ============== E. EMPLOYEE COST ==============
    section_e_rows = [
        ('employee_vacation', 'Employee Vacation Cost'),
        ('eosb', 'EOSB - End of Service Benefits'),
        ('gosi', 'GOSI - General Organization for Social Insurance'),
        ('employee_medical', 'Medical Insurance Cost'),
        ('exit_reentry', 'Exit Re-Entry Cost'),
        ('salary_transfer', 'Salary Transfer Cost'),
        ('public_holiday', 'Public Holiday Cost'),
        ('sick_leave', 'Sick Leave Cost'),
    ]
    e_header, e_table, e_one_time, e_annual, e_monthly = create_cost_section(
        "E. EMPLOYEE COST", section_e_rows, "Total of Employee Cost"
    )
    elements.append(e_header)
    elements.append(e_table)
    elements.append(Spacer(1, 2*mm))

    # ============== F. FAMILY COST ==============
    section_f_rows = [
        ('family_medical', 'Medical Insurance Cost'),
        ('family_vacation', 'Vacation Ticket Cost'),
        ('family_exit_reentry', 'Exit Re-Entry Cost'),
        ('family_joining', 'Joining Ticket Cost'),
        ('family_visa', 'Visa Cost'),
        ('family_levy', 'Levy Cost'),
    ]
    f_header, f_table, f_one_time, f_annual, f_monthly = create_cost_section(
        "F. FAMILY COST", section_f_rows, "Total of Family Cost"
    )
    elements.append(f_header)
    elements.append(f_table)
    elements.append(Spacer(1, 2*mm))

    # ============== G. GOVERNMENT COST ==============
    section_g_rows = [
        ('sce', 'SCE - Saudi Council of Engineering Cost'),
        ('socpa', 'SOCPA - Saudi Org. for Chartered & Prof. Accnts'),
        ('medical_test', 'Medical Test for Iqama Cost'),
        ('ewakala_chamber', 'E-Wakala and Chamber & Mofa Cost'),
        ('govt_visa', 'Visa Cost'),
        ('iqama_transfer', 'Iqama Transfer Cost'),
        ('iqama', 'Iqama Cost'),
        ('saudi_admin', 'Saudi Admin Cost'),
        ('ajeer', 'Ajeer Cost'),
    ]
    g_header, g_table, g_one_time, g_annual, g_monthly = create_cost_section(
        "G. GOVERNMENT COST", section_g_rows, "Total of Government Related Charges"
    )
    elements.append(g_header)
    elements.append(g_table)
    elements.append(Spacer(1, 2*mm))

    # ============== H. MOBILIZATION COST ==============
    section_h_rows = [
        ('visa_processing', 'Visa Processing Cost'),
        ('recruitment_fee', 'Recruitment Fee Cost'),
        ('philippines_fee', 'Philippines Placement Fee Cost'),
        ('joining_ticket', 'Joining Ticket Cost'),
        ('egypt_govt_fee', 'Egypt Government Fee Cost'),
        ('relocation', 'Relocation Cost'),
        ('other_expenses', 'Other Expenses Cost (If Any)'),
    ]
    h_header, h_table, h_one_time, h_annual, h_monthly = create_cost_section(
        "H. MOBILIZATION COST", section_h_rows, "Total of Mobilization Cost"
    )
    elements.append(h_header)
    elements.append(h_table)
    elements.append(Spacer(1, 2*mm))

    # ============== SUMMARY & INVOICE ==============
    # Calculate grand totals
    total_one_time = e_one_time + f_one_time + g_one_time + h_one_time
    total_annual = e_annual + f_annual + g_annual + h_annual
    total_monthly = e_monthly + f_monthly + g_monthly + h_monthly + total_salary

    # Use provided totals if available
    total_one_time = get_num('totalOneTime') or total_one_time
    total_annual = get_num('totalAnnual') or total_annual
    total_monthly = get_num('totalMonthly') or total_monthly

    # Service charge
    service_charge = get_num('fnrco_service_charge', 1250.00) or 1250.00

    # 15% VAT calculation (on Medical Insurance + Service Charge only)
    employee_medical_annual = get_num('employee_medical_annual', 0) or 0
    family_medical_annual = get_num('family_medical_annual', 0) or 0
    total_medical_insurance = employee_medical_annual + family_medical_annual
    vat_on_annual = total_medical_insurance * 0.15
    vat_on_monthly = service_charge * 0.15

    # Total invoice amount
    total_invoice = total_monthly + service_charge + vat_on_monthly

    # Summary table
    summary_data = [
        [
            Paragraph("<b>Total Cost</b>", cell_bold_style),
            Paragraph(f"<b>{format_currency(total_one_time)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_annual)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_monthly)}</b>", cell_right_bold_style),
            Paragraph("Payroll Benefits + Monthly Cost", cell_style),
        ],
        [
            Paragraph("<b>FNRCO SERVICE CHARGE</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>{format_currency(service_charge)}</b>", cell_right_bold_style),
            Paragraph("Per Person Per Month", cell_style),
        ],
        [
            Paragraph("<b>15% VAT - Applicable on Medical Insurance and Service Charge Only</b>", cell_bold_style),
            Paragraph("", cell_style),
            Paragraph(f"{format_currency(vat_on_annual)}", cell_right_style),
            Paragraph(f"{format_currency(vat_on_monthly)}", cell_right_style),
            Paragraph("15% Vat", cell_style),
        ],
        [
            Paragraph("<b>TOTAL INVOICED AMOUNT INCLUDING 15% VAT</b>", ParagraphStyle('White', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph(f"<b>{format_currency(total_invoice)}</b>", ParagraphStyle('WhiteRB', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT)),
            Paragraph("Regular Monthly", ParagraphStyle('WhiteS', fontSize=7, fontName='Helvetica', textColor=colors.white)),
        ],
    ]

    summary_table = Table(summary_data, colWidths=[50*mm, 26*mm, 26*mm, 26*mm, 62*mm])
    summary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5e6e6')),  # Light red for total cost row
        ('BACKGROUND', (0, -1), (-1, -1), primary_color),  # Dark red for final row
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -2), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -2), 2),
        ('TOPPADDING', (0, -1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 4),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 3*mm))

    # ============== FOOTER ==============
    employee_name = get_val('employee_name', '')
    footer_text = f"{employee_name} - Cost Estimation Sheet" if employee_name else "Cost Estimation Sheet"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=7, textColor=colors.HexColor('#9ca3af'))))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
