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
    Generate Quote Sheet PDF matching the frontend edit mode design.
    Uses dark red (#9B1B1B) as the primary color like FNRCO branding.

    Args:
        quote_sheet_data: Dictionary containing all quote sheet form data

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12*mm,
        leftMargin=12*mm,
        topMargin=10*mm,
        bottomMargin=10*mm,
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
    orange_bg = colors.HexColor('#fff7ed')
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

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontSize=9,
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

    # ============== HEADER ==============
    # Company name on right
    company_name = get_val('to_company_name', 'FNRCO')
    company_address = get_val('to_company_address', 'Riyadh, Saudi Arabia')

    header_data = [
        [
            Paragraph("", cell_style),
            Paragraph(f"<b>{company_name}</b><br/>{company_address}", ParagraphStyle('Right', fontSize=8, alignment=TA_RIGHT, textColor=dark_gray))
        ]
    ]
    header_table = Table(header_data, colWidths=[120*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, primary_color),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3*mm))

    # Title
    doc_title = get_val('document_title', 'Cost Estimation Sheet - White Collar')
    elements.append(Paragraph(doc_title, title_style))

    # Subtitle with issued date
    minimum_note = get_val('minimum_contract_note', 'Minimum Contract Period is 12 Months')
    issued_date = get_val('issued_date', 'April 21, 2025')
    elements.append(Paragraph(f"{minimum_note}  |  Issued Date: {issued_date}", subtitle_style))
    elements.append(Spacer(1, 3*mm))

    # Helper function to create section header
    def create_section_header(title):
        header_table = Table(
            [[Paragraph(title, section_header_style)]],
            colWidths=[186*mm]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return header_table

    # ============== (A) EMPLOYEE CONTRACT INFORMATION ==============
    elements.append(create_section_header("(A) Employee Contract Information"))

    emp_info_header = [
        Paragraph("<b>Employee Name</b>", header_cell_style),
        Paragraph("<b>Role / Position</b>", header_cell_style),
        Paragraph("<b>Date of Hiring</b>", header_cell_style),
        Paragraph("<b>Nationality</b>", header_cell_style),
        Paragraph("<b>Status / Children</b>", header_cell_style),
    ]

    family_status = get_val('family_status', '')
    num_children = get_val('num_children', '')
    status_children = f"{family_status}" + (f" / {num_children}" if num_children else "")

    emp_info_data = [
        emp_info_header,
        [
            Paragraph(get_val('employee_name', ''), cell_style),
            Paragraph(get_val('role', ''), cell_style),
            Paragraph(get_val('date_of_hiring', ''), cell_style),
            Paragraph(get_val('nationality', ''), cell_style),
            Paragraph(status_children, cell_style),
        ]
    ]

    emp_table = Table(emp_info_data, colWidths=[37.2*mm, 37.2*mm, 37.2*mm, 37.2*mm, 37.2*mm])
    emp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 3*mm))

    # ============== (B) EMPLOYEE CASH BENEFITS ==============
    elements.append(create_section_header("(B) Employee Cash Benefits (SAR)"))

    cash_header = [
        Paragraph("<b>Basic Salary</b>", header_cell_style),
        Paragraph("<b>Transport</b>", header_cell_style),
        Paragraph("<b>Housing</b>", header_cell_style),
        Paragraph("<b>Rate/Day</b>", header_cell_style),
        Paragraph("<b>Working Days</b>", header_cell_style),
        Paragraph("<b>AED-SAR</b>", header_cell_style),
        Paragraph("<b>Gross Salary</b>", header_cell_style),
    ]

    gross_salary = get_num('gross_salary')
    if gross_salary is None:
        # Calculate if not provided
        basic = get_num('basic_salary', 0) or 0
        transport = get_num('transport_allowance', 0) or 0
        housing = get_num('housing_allowance', 0) or 0
        gross_salary = basic + transport + housing

    cash_data = [
        cash_header,
        [
            Paragraph(format_currency(get_num('basic_salary')), cell_right_style),
            Paragraph(format_currency(get_num('transport_allowance')), cell_right_style),
            Paragraph(format_currency(get_num('housing_allowance')), cell_right_style),
            Paragraph(format_currency(get_num('rate_per_day')), cell_right_style),
            Paragraph(str(get_val('working_days', '')), cell_right_style),
            Paragraph(str(get_val('aed_to_sar_rate', '1.02')), cell_right_style),
            Paragraph(f"<b>{format_currency(gross_salary)}</b>", cell_right_bold_style),
        ]
    ]

    cash_table = Table(cash_data, colWidths=[26.6*mm, 26.6*mm, 26.6*mm, 26.6*mm, 26.6*mm, 26.6*mm, 26.6*mm])
    cash_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (6, 1), (6, 1), orange_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(cash_table)
    elements.append(Spacer(1, 3*mm))

    # Helper for cost tables with 5 columns
    def create_cost_table(section_title, rows_config, totals_key_prefix):
        elements.append(create_section_header(section_title))

        cost_header = [
            Paragraph("<b>Description</b>", header_cell_style),
            Paragraph("<b>One Time</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>Annual</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>Monthly</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph("<b>Remarks / Clarification</b>", header_cell_style),
        ]

        cost_data = [cost_header]

        total_one_time = 0
        total_annual = 0
        total_monthly = 0

        for prefix, default_label in rows_config:
            label = get_val(f'{prefix}_label', default_label)
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
            Paragraph(f"<b>Total {totals_key_prefix}</b>", cell_bold_style),
            Paragraph(f"<b>{format_currency(total_one_time if total_one_time > 0 else None)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_annual if total_annual > 0 else None)}</b>", cell_right_bold_style),
            Paragraph(f"<b>{format_currency(total_monthly if total_monthly > 0 else None)}</b>", cell_right_bold_style),
            Paragraph("", cell_style),
        ])

        cost_table = Table(cost_data, colWidths=[44.6*mm, 28*mm, 28*mm, 28*mm, 57.6*mm])
        cost_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
            ('BACKGROUND', (0, 0), (-1, 0), light_gray),
            ('BACKGROUND', (0, -1), (-1, -1), orange_bg),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(cost_table)
        elements.append(Spacer(1, 3*mm))

        return total_one_time, total_annual, total_monthly

    # ============== (C) EMPLOYEE COST ==============
    section_c_rows = [
        ('vacation', 'Cost of Annual Vacation (30 Days) for Employee'),
        ('flight_tickets', 'Cost of Annual Flight Tickets for Employee'),
        ('eosb', 'Monthly Cost of EOSB of Employee'),
        ('gosi', 'GOSI of Employee'),
        ('medical_insurance', 'Annual Medical Insurance (A1 Class)'),
        ('exit_reentry', 'Exit Re-Entry Charges of Employee'),
        ('salary_transfer', 'Salary Transfer (Monthly)'),
        ('sick_leave', 'Sick Leave and Public Holiday Cost'),
    ]
    c_one_time, c_annual, c_monthly = create_cost_table(
        "(C) Employee Cost (Charges in SAR)",
        section_c_rows,
        "Employee Cost"
    )

    # ============== (D) FAMILY COST ==============
    section_d_rows = [
        ('family_medical', 'Annual Medical Insurance for Family'),
        ('family_flight', 'Annual Flight Tickets for Family'),
        ('family_exit_reentry', 'Exit Re-Entry Charges for Family'),
        ('family_joining', 'Joining Flight Tickets for Family (One Time)'),
        ('family_visa', 'Visa Cost for Family (One Time)'),
        ('family_levy', 'Family Levy Cost'),
    ]
    d_one_time, d_annual, d_monthly = create_cost_table(
        "(D) Family Cost (Charges in SAR)",
        section_d_rows,
        "Family Cost"
    )

    # ============== (E) GOVERNMENT RELATED CHARGES ==============
    section_e_rows = [
        ('sce', 'SCE Charges'),
        ('medical_test', 'Medical Test (Iqama) (One Time)'),
        ('visa', 'Cost of Visa (One Time)'),
        ('e_wakala', 'E-Wakala Charge (One Time)'),
        ('chamber_mofa', 'Chamber & MOFA (One Time)'),
        ('iqama', 'Yearly Cost of Iqama (Annual)'),
        ('saudi_admin', 'Saudi Admin Cost'),
        ('ajeer', 'Ajeer Cost'),
    ]
    e_one_time, e_annual, e_monthly = create_cost_table(
        "(E) Government Related Charges (In SAR)",
        section_e_rows,
        "Government Charges"
    )

    # ============== (F) MOBILIZATION COST & SUMMARY ==============
    elements.append(create_section_header("(F) Mobilization Cost (Charges in SAR) & Summary"))

    mob_header = [
        Paragraph("<b>Description</b>", header_cell_style),
        Paragraph("<b>One Time</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Annual</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Monthly</b>", ParagraphStyle('H', fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Remarks / Clarification</b>", header_cell_style),
    ]

    mob_data = [mob_header]

    # Mobilization rows
    section_f_rows = [
        ('visa_processing', 'Visa Processing Charges (One Time)'),
        ('recruitment', 'Recruitment Fee (One Time)'),
        ('joining_ticket', 'Joining Ticket (One Time)'),
        ('relocation', 'Relocation Cost (One Time)'),
        ('other_mobilization', 'Other Cost'),
    ]

    f_one_time = 0
    f_annual = 0
    f_monthly = 0

    for prefix, default_label in section_f_rows:
        label = get_val(f'{prefix}_label', default_label)
        one_time = get_num(f'{prefix}_one_time')
        annual = get_num(f'{prefix}_annual')
        monthly = get_num(f'{prefix}_monthly')
        remarks = get_val(f'{prefix}_remarks', '')

        f_one_time += one_time or 0
        f_annual += annual or 0
        f_monthly += monthly or 0

        mob_data.append([
            Paragraph(label, cell_style),
            Paragraph(format_currency(one_time), cell_right_style),
            Paragraph(format_currency(annual), cell_right_style),
            Paragraph(format_currency(monthly), cell_right_style),
            Paragraph(remarks, cell_style),
        ])

    # Total Mobilization row
    mob_data.append([
        Paragraph("<b>Total of Mobilization Cost</b>", cell_bold_style),
        Paragraph(f"<b>{format_currency(f_one_time if f_one_time > 0 else None)}</b>", cell_right_bold_style),
        Paragraph(f"<b>{format_currency(f_annual if f_annual > 0 else None)}</b>", cell_right_bold_style),
        Paragraph(f"<b>{format_currency(f_monthly if f_monthly > 0 else None)}</b>", cell_right_bold_style),
        Paragraph("", cell_style),
    ])

    # Grand Total Cost
    total_one_time = c_one_time + d_one_time + e_one_time + f_one_time
    total_annual = c_annual + d_annual + e_annual + f_annual
    total_monthly = c_monthly + d_monthly + e_monthly + f_monthly

    # Use provided totals if available
    total_one_time = get_num('total_one_time') or total_one_time
    total_annual = get_num('total_annual') or total_annual
    total_monthly = get_num('total_monthly') or total_monthly

    mob_data.append([
        Paragraph("<b>Total Cost</b>", cell_bold_style),
        Paragraph(f"<b>{format_currency(total_one_time)}</b>", cell_right_bold_style),
        Paragraph(f"<b>{format_currency(total_annual)}</b>", cell_right_bold_style),
        Paragraph(f"<b>{format_currency(total_monthly)}</b>", cell_right_bold_style),
        Paragraph("", cell_style),
    ])

    # FNRCO Service Charge
    fnrco_charge = get_num('fnrco_service_charge', 1250.00)
    mob_data.append([
        Paragraph("<b>FNRCO Service Charge</b>", cell_bold_style),
        Paragraph("-", cell_right_style),
        Paragraph("-", cell_right_style),
        Paragraph(f"<b>{format_currency(fnrco_charge)}</b>", cell_right_bold_style),
        Paragraph("", cell_style),
    ])

    # Total Invoice Amount
    total_invoice = get_num('total_invoice_amount') or (total_monthly + (fnrco_charge or 0))
    mob_data.append([
        Paragraph("<b>Total Invoice Amount</b>", ParagraphStyle('White', fontSize=8, fontName='Helvetica-Bold', textColor=colors.white)),
        Paragraph("-", ParagraphStyle('WhiteR', fontSize=7, fontName='Helvetica', textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("-", ParagraphStyle('WhiteR', fontSize=7, fontName='Helvetica', textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph(f"<b>{format_currency(total_invoice)}</b>", ParagraphStyle('WhiteRB', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("", cell_style),
    ])

    mob_table = Table(mob_data, colWidths=[44.6*mm, 28*mm, 28*mm, 28*mm, 57.6*mm])
    mob_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, border_gray),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, len(section_f_rows) + 1), (-1, len(section_f_rows) + 1), orange_bg),  # Mobilization total
        ('BACKGROUND', (0, len(section_f_rows) + 2), (-1, len(section_f_rows) + 2), colors.HexColor('#fed7aa')),  # Total Cost
        ('BACKGROUND', (0, -1), (-1, -1), primary_color),  # Total Invoice
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, -1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 5),
    ]))
    elements.append(mob_table)
    elements.append(Spacer(1, 4*mm))

    # ============== FOOTER ==============
    first_name = get_val('first_name', '')
    surname = get_val('surname', '')
    contractor_name = f"{first_name} {surname}".strip() or get_val('employee_name', '')
    footer_text = f"{contractor_name} - Cost Estimation Sheet"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=7, textColor=colors.HexColor('#9ca3af'))))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
