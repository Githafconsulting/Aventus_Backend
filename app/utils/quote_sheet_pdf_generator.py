from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime


def format_currency(value, default=""):
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
    Generate a professional Quote Sheet PDF for Saudi Arabia - White Collar

    Args:
        quote_sheet_data: Dictionary containing all quote sheet form data

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Colors
    header_blue = colors.HexColor('#1a5f7a')
    light_gray = colors.HexColor('#f5f5f5')
    total_yellow = colors.HexColor('#fff3cd')
    total_green = colors.HexColor('#d4edda')
    dark_gray = colors.HexColor('#333333')

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
        textColor=header_blue,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=3*mm,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=9,
        textColor=dark_gray,
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
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica',
        leading=10,
    )

    cell_bold_style = ParagraphStyle(
        'CellBold',
        fontSize=8,
        textColor=dark_gray,
        fontName='Helvetica-Bold',
        leading=10,
    )

    # ============== HEADER ==============
    elements.append(Paragraph("Cost Estimation Sheet - White Collar", title_style))
    elements.append(Paragraph("Minimum Contract Period is 12 Months", subtitle_style))

    issued_date = get_val('issued_date', datetime.now().strftime('%B %d, %Y'))
    elements.append(Paragraph(f"Issued Date: {issued_date}", subtitle_style))
    elements.append(Spacer(1, 5*mm))

    # Helper function to create section header
    def create_section_header(title):
        header_table = Table(
            [[Paragraph(title, section_header_style)]],
            colWidths=[180*mm]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_blue),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return header_table

    # ============== (A) EMPLOYEE CONTRACT INFORMATION ==============
    elements.append(create_section_header("(A). Employee Contract Information"))

    company_name = get_val('third_party_company_name', get_val('company_name', 'Aventus Global'))

    emp_info_data = [
        [Paragraph("<b>Name</b>", cell_bold_style),
         Paragraph(get_val('employee_name', get_val('contractor_name', '')), cell_style),
         Paragraph(company_name, cell_style)],
        [Paragraph("<b>Role</b>", cell_bold_style),
         Paragraph(get_val('role', ''), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>Date of Hiring</b>", cell_bold_style),
         Paragraph(get_val('date_of_hiring', ''), cell_style),
         Paragraph("", cell_style)],
        [Paragraph("<b>Nationality</b>", cell_bold_style),
         Paragraph(get_val('nationality', ''), cell_style),
         Paragraph("", cell_style)],
        [Paragraph("<b>Status Single or Family</b>", cell_bold_style),
         Paragraph(get_val('family_status', 'Single'), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>No. of Children Below 18 Years of Age</b>", cell_bold_style),
         Paragraph(get_val('num_children', '0'), cell_style),
         Paragraph("According to Client Policy", cell_style)],
    ]

    emp_table = Table(emp_info_data, colWidths=[70*mm, 50*mm, 60*mm])
    emp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4*mm))

    # ============== (B) EMPLOYEE CASH BENEFITS ==============
    elements.append(create_section_header("(B). Employee Cash Benefits"))

    cash_header = [
        Paragraph("", cell_bold_style),
        Paragraph("<b>AMOUNT IN SAR</b>", cell_bold_style),
        Paragraph("<b>REMARKS</b>", cell_bold_style),
    ]

    cash_data = [
        cash_header,
        [Paragraph("<b>Basic Salary</b>", cell_bold_style),
         Paragraph(format_currency(get_num('basic_salary')), cell_style),
         Paragraph("Salary is variable as per the categories", cell_style)],
        [Paragraph("<b>Transport Allowance</b>", cell_bold_style),
         Paragraph(format_currency(get_num('transport_allowance')), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>Housing Allowance</b>", cell_bold_style),
         Paragraph(format_currency(get_num('housing_allowance')), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>Rate Per Day</b>", cell_bold_style),
         Paragraph(format_currency(get_num('rate_per_day')), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>Working Days / Month</b>", cell_bold_style),
         Paragraph(get_val('working_days_month', ''), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>AED to SAR</b>", cell_bold_style),
         Paragraph(get_val('aed_to_sar', ''), cell_style),
         Paragraph("According to Client Policy", cell_style)],
        [Paragraph("<b>Employee Monthly Total Cash Benefits</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('gross_salary'))}</b>", cell_bold_style),
         Paragraph("<b>Gross Salary</b>", cell_bold_style)],
    ]

    cash_table = Table(cash_data, colWidths=[70*mm, 50*mm, 60*mm])
    cash_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, 1), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), total_green),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(cash_table)
    elements.append(Spacer(1, 4*mm))

    # ============== (C) EMPLOYEE COST ==============
    elements.append(create_section_header("(C). Employee Cost (Charges in SAR)"))

    cost_header = [
        Paragraph("", cell_bold_style),
        Paragraph("<b>One Time</b>", cell_bold_style),
        Paragraph("<b>Annual</b>", cell_bold_style),
        Paragraph("<b>Monthly</b>", cell_bold_style),
        Paragraph("<b>Remarks</b>", cell_bold_style),
    ]

    employee_cost_data = [
        cost_header,
        [Paragraph("Cost of Annual Vacation 30 Calendar Days for Employee", cell_style),
         Paragraph(format_currency(get_num('vacation_one_time')), cell_style),
         Paragraph(format_currency(get_num('vacation_annual')), cell_style),
         Paragraph(format_currency(get_num('vacation_monthly')), cell_style),
         Paragraph("12 Month Contract", cell_style)],
        [Paragraph("Cost of Annual Flight Tickets for Employee", cell_style),
         Paragraph(format_currency(get_num('flight_one_time')), cell_style),
         Paragraph(format_currency(get_num('flight_annual')), cell_style),
         Paragraph(format_currency(get_num('flight_monthly')), cell_style),
         Paragraph("As Per Actuals / After 1 Year", cell_style)],
        [Paragraph("Monthly Cost of EOSB of Employee", cell_style),
         Paragraph(format_currency(get_num('eosb_one_time')), cell_style),
         Paragraph(format_currency(get_num('eosb_annual')), cell_style),
         Paragraph(format_currency(get_num('eosb_monthly')), cell_style),
         Paragraph("Monthly", cell_style)],
        [Paragraph("Monthly Cost of GOSI of Employee", cell_style),
         Paragraph(format_currency(get_num('gosi_one_time')), cell_style),
         Paragraph(format_currency(get_num('gosi_annual')), cell_style),
         Paragraph(format_currency(get_num('gosi_monthly')), cell_style),
         Paragraph("Monthly", cell_style)],
        [Paragraph("Annual Medical Insurance for Employee (A1 Class)", cell_style),
         Paragraph(format_currency(get_num('medical_one_time')), cell_style),
         Paragraph(format_currency(get_num('medical_annual')), cell_style),
         Paragraph(format_currency(get_num('medical_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("Exit Re-Entry Charges of Employee", cell_style),
         Paragraph(format_currency(get_num('exit_reentry_one_time')), cell_style),
         Paragraph(format_currency(get_num('exit_reentry_annual')), cell_style),
         Paragraph(format_currency(get_num('exit_reentry_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("Salary Transfer (Monthly)", cell_style),
         Paragraph(format_currency(get_num('salary_transfer_one_time')), cell_style),
         Paragraph(format_currency(get_num('salary_transfer_annual')), cell_style),
         Paragraph(format_currency(get_num('salary_transfer_monthly')), cell_style),
         Paragraph("Monthly", cell_style)],
        [Paragraph("Sick Leave and Public Holiday Cost", cell_style),
         Paragraph(format_currency(get_num('sick_leave_one_time')), cell_style),
         Paragraph(format_currency(get_num('sick_leave_annual')), cell_style),
         Paragraph(format_currency(get_num('sick_leave_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("<b>Total of Employee Cost</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('employee_cost_one_time_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('employee_cost_annual_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('employee_cost_monthly_total'))}</b>", cell_bold_style),
         Paragraph("", cell_style)],
    ]

    employee_cost_table = Table(employee_cost_data, colWidths=[60*mm, 25*mm, 25*mm, 25*mm, 45*mm])
    employee_cost_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, 1), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), total_yellow),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(employee_cost_table)
    elements.append(Spacer(1, 4*mm))

    # ============== (D) FAMILY COST ==============
    elements.append(create_section_header("(D). Family Cost (Charges in SAR)"))

    family_status = get_val('family_status', 'Single')
    single_remark = "Single Only" if family_status == "Single" else ""

    family_cost_data = [
        cost_header,
        [Paragraph("Annual Medical Insurance for Family", cell_style),
         Paragraph(format_currency(get_num('family_medical_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_medical_annual')), cell_style),
         Paragraph(format_currency(get_num('family_medical_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("Annual Flight Tickets for Family", cell_style),
         Paragraph(format_currency(get_num('family_flight_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_flight_annual')), cell_style),
         Paragraph(format_currency(get_num('family_flight_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("Exit Re-Entry charges for Family", cell_style),
         Paragraph(format_currency(get_num('family_exit_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_exit_annual')), cell_style),
         Paragraph(format_currency(get_num('family_exit_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("Joining Flight Tickets for Family (One Time)", cell_style),
         Paragraph(format_currency(get_num('family_joining_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_joining_annual')), cell_style),
         Paragraph(format_currency(get_num('family_joining_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("Visa Cost for Family (One Time)", cell_style),
         Paragraph(format_currency(get_num('family_visa_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_visa_annual')), cell_style),
         Paragraph(format_currency(get_num('family_visa_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("Family Levy Cost", cell_style),
         Paragraph(format_currency(get_num('family_levy_one_time')), cell_style),
         Paragraph(format_currency(get_num('family_levy_annual')), cell_style),
         Paragraph(format_currency(get_num('family_levy_monthly')), cell_style),
         Paragraph(single_remark, cell_style)],
        [Paragraph("<b>Total of Family Cost</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('family_cost_one_time_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('family_cost_annual_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('family_cost_monthly_total'))}</b>", cell_bold_style),
         Paragraph("", cell_style)],
    ]

    family_cost_table = Table(family_cost_data, colWidths=[60*mm, 25*mm, 25*mm, 25*mm, 45*mm])
    family_cost_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, 1), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), total_yellow),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(family_cost_table)
    elements.append(Spacer(1, 4*mm))

    # ============== (E) GOVERNMENT RELATED CHARGES ==============
    elements.append(create_section_header("(E). Government Related Charges (In SAR)"))

    govt_cost_data = [
        cost_header,
        [Paragraph("SCE Charges", cell_style),
         Paragraph(format_currency(get_num('sce_one_time')), cell_style),
         Paragraph(format_currency(get_num('sce_annual')), cell_style),
         Paragraph(format_currency(get_num('sce_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("Medical Test (Iqama) (One Time)", cell_style),
         Paragraph(format_currency(get_num('medical_test_one_time')), cell_style),
         Paragraph(format_currency(get_num('medical_test_annual')), cell_style),
         Paragraph(format_currency(get_num('medical_test_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('medical_test', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Cost of Visa (One Time)", cell_style),
         Paragraph(format_currency(get_num('visa_cost_one_time')), cell_style),
         Paragraph(format_currency(get_num('visa_cost_annual')), cell_style),
         Paragraph(format_currency(get_num('visa_cost_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("E-wakala Charge (One Time)", cell_style),
         Paragraph(format_currency(get_num('ewakala_one_time')), cell_style),
         Paragraph(format_currency(get_num('ewakala_annual')), cell_style),
         Paragraph(format_currency(get_num('ewakala_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('ewakala', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Chamber & Mofa (One Time)", cell_style),
         Paragraph(format_currency(get_num('chamber_mofa_one_time')), cell_style),
         Paragraph(format_currency(get_num('chamber_mofa_annual')), cell_style),
         Paragraph(format_currency(get_num('chamber_mofa_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('chamber_mofa', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Yearly Cost of Iqama (Annual)", cell_style),
         Paragraph(format_currency(get_num('iqama_one_time')), cell_style),
         Paragraph(format_currency(get_num('iqama_annual')), cell_style),
         Paragraph(format_currency(get_num('iqama_monthly')), cell_style),
         Paragraph("As per actuals", cell_style)],
        [Paragraph("Saudi Admin Cost", cell_style),
         Paragraph(format_currency(get_num('saudi_admin_one_time')), cell_style),
         Paragraph(format_currency(get_num('saudi_admin_annual')), cell_style),
         Paragraph(format_currency(get_num('saudi_admin_monthly')), cell_style),
         Paragraph("Monthly - Subject to Change", cell_style)],
        [Paragraph("Ajeer Cost", cell_style),
         Paragraph(format_currency(get_num('ajeer_one_time')), cell_style),
         Paragraph(format_currency(get_num('ajeer_annual')), cell_style),
         Paragraph(format_currency(get_num('ajeer_monthly')), cell_style),
         Paragraph("Monthly", cell_style)],
        [Paragraph("<b>Total of Government Related Charges</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('govt_cost_one_time_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('govt_cost_annual_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('govt_cost_monthly_total'))}</b>", cell_bold_style),
         Paragraph("", cell_style)],
    ]

    govt_cost_table = Table(govt_cost_data, colWidths=[60*mm, 25*mm, 25*mm, 25*mm, 45*mm])
    govt_cost_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, 1), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), total_yellow),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(govt_cost_table)
    elements.append(Spacer(1, 4*mm))

    # ============== (F) MOBILIZATION COST ==============
    elements.append(create_section_header("(F). Mobilization Cost (Charges in SAR)"))

    mobilization_cost_data = [
        cost_header,
        [Paragraph("Visa Processing Charges (One Time)", cell_style),
         Paragraph(format_currency(get_num('visa_processing_one_time')), cell_style),
         Paragraph(format_currency(get_num('visa_processing_annual')), cell_style),
         Paragraph(format_currency(get_num('visa_processing_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('visa_processing', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Recruitment Fee (One Time)", cell_style),
         Paragraph(format_currency(get_num('recruitment_one_time')), cell_style),
         Paragraph(format_currency(get_num('recruitment_annual')), cell_style),
         Paragraph(format_currency(get_num('recruitment_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('recruitment', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Joining Ticket (One Time)", cell_style),
         Paragraph(format_currency(get_num('joining_ticket_one_time')), cell_style),
         Paragraph(format_currency(get_num('joining_ticket_annual')), cell_style),
         Paragraph(format_currency(get_num('joining_ticket_monthly')), cell_style),
         Paragraph(get_val('remarks_data', {}).get('joining_ticket', 'Not Applicable') if isinstance(get_val('remarks_data', {}), dict) else 'Not Applicable', cell_style)],
        [Paragraph("Relocation Cost (One Time)", cell_style),
         Paragraph(format_currency(get_num('relocation_one_time')), cell_style),
         Paragraph(format_currency(get_num('relocation_annual')), cell_style),
         Paragraph(format_currency(get_num('relocation_monthly')), cell_style),
         Paragraph("As per Actuals", cell_style)],
        [Paragraph("Other Cost", cell_style),
         Paragraph(format_currency(get_num('other_cost_one_time')), cell_style),
         Paragraph(format_currency(get_num('other_cost_annual')), cell_style),
         Paragraph(format_currency(get_num('other_cost_monthly')), cell_style),
         Paragraph("As per Actuals", cell_style)],
        [Paragraph("<b>Total of Mobilization Cost</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('mobilization_one_time_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('mobilization_annual_total'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('mobilization_monthly_total'))}</b>", cell_bold_style),
         Paragraph("", cell_style)],
    ]

    mobilization_cost_table = Table(mobilization_cost_data, colWidths=[60*mm, 25*mm, 25*mm, 25*mm, 45*mm])
    mobilization_cost_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), light_gray),
        ('BACKGROUND', (0, 1), (0, -2), light_gray),
        ('BACKGROUND', (0, -1), (-1, -1), total_yellow),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(mobilization_cost_table)
    elements.append(Spacer(1, 4*mm))

    # ============== GRAND TOTALS ==============
    grand_total_data = [
        [Paragraph("<b>Total Cost</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('total_one_time'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('total_annual'))}</b>", cell_bold_style),
         Paragraph(f"<b>{format_currency(get_num('total_monthly'))}</b>", cell_bold_style),
         Paragraph("Payroll Benefits + Monthly Cost", cell_style)],
        [Paragraph("<b>FNRCO Service Charge</b>", cell_bold_style),
         Paragraph("", cell_style),
         Paragraph("", cell_style),
         Paragraph(f"<b>{format_currency(get_num('fnrco_service_charge'))}</b>", cell_bold_style),
         Paragraph("Per Person Per Month", cell_style)],
        [Paragraph("<b>Total Invoice Amount</b>", cell_bold_style),
         Paragraph("", cell_style),
         Paragraph("", cell_style),
         Paragraph(f"<b>{format_currency(get_num('total_invoice_amount'))}</b>", cell_bold_style),
         Paragraph("Monthly", cell_style)],
    ]

    grand_total_table = Table(grand_total_data, colWidths=[60*mm, 25*mm, 25*mm, 25*mm, 45*mm])
    grand_total_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), total_green),
        ('BACKGROUND', (0, 1), (0, 1), light_gray),
        ('BACKGROUND', (0, 2), (-1, 2), header_blue),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (3, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(grand_total_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
