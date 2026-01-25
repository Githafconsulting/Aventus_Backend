from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


def generate_timesheet_pdf(timesheet_data: dict) -> BytesIO:
    """
    Generate a professional timesheet PDF with Aventus branding

    Args:
        timesheet_data: Dictionary containing timesheet information

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document
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

    # Define colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')
    light_gray = colors.HexColor('#F3F4F6')
    green = colors.HexColor('#10B981')
    red = colors.HexColor('#EF4444')
    blue = colors.HexColor('#3B82F6')
    purple = colors.HexColor('#8B5CF6')

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=dark_gray,
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

    # Extract data
    contractor_name = timesheet_data.get('contractor_name', '[Contractor Name]')
    client_name = timesheet_data.get('client_name', '[Client Name]')
    project_name = timesheet_data.get('project_name', '[Project Name]')
    location = timesheet_data.get('location', '[Location]')
    month = timesheet_data.get('month', '[Month Year]')
    manager_name = timesheet_data.get('manager_name', '[Manager Name]')
    manager_email = timesheet_data.get('manager_email', '[Manager Email]')

    # Summary data
    work_days = timesheet_data.get('work_days', 0)
    sick_days = timesheet_data.get('sick_days', 0)
    vacation_days = timesheet_data.get('vacation_days', 0)
    holiday_days = timesheet_data.get('holiday_days', 0)
    unpaid_days = timesheet_data.get('unpaid_days', 0)
    # Calculate total days as sum of work, sick, vacation, and holiday
    total_days = (work_days or 0) + (sick_days or 0) + (vacation_days or 0) + (holiday_days or 0)

    submitted_date = timesheet_data.get('submitted_date', '')
    status = timesheet_data.get('status', 'pending')
    notes = timesheet_data.get('notes', '')

    # Add logo if available
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=12*mm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 3*mm))

    # Title
    elements.append(Paragraph("TIMESHEET", title_style))
    elements.append(Paragraph(month, ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica'
    )))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[170*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, orange),
    ])))
    elements.append(Spacer(1, 4*mm))

    # Contractor Information Table
    info_data = [
        ['Contractor:', contractor_name, 'Client:', client_name],
        ['Project:', project_name, 'Location:', location],
        ['Manager:', manager_name, 'Email:', manager_email],
    ]

    info_table = Table(info_data, colWidths=[25*mm, 55*mm, 25*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), dark_gray),
        ('TEXTCOLOR', (2, 0), (2, -1), dark_gray),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5*mm))

    # Summary Section
    elements.append(Paragraph("<b>Summary</b>", section_style))

    # Summary table with colored indicators - Total Days at bottom as sum
    summary_data = [
        ['Category', 'Days', 'Category', 'Days'],
        ['Work Days', str(work_days), 'Sick Days', str(sick_days)],
        ['Vacation Days', str(vacation_days), 'Public Holidays', str(holiday_days)],
        ['Unpaid Leave', str(unpaid_days), '', ''],
        ['', '', 'TOTAL DAYS', str(total_days)],
    ]

    summary_table = Table(summary_data, colWidths=[45*mm, 35*mm, 45*mm, 35*mm])
    summary_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        # Data rows
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, 3), light_gray),
        # Total row styling - make it stand out
        ('BACKGROUND', (2, 4), (3, 4), orange),
        ('TEXTCOLOR', (2, 4), (3, 4), colors.white),
        ('FONTNAME', (2, 4), (3, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 4), (3, 4), 11),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 5*mm))

    # Status Section
    status_color = green if status == 'approved' else (red if status == 'declined' else colors.HexColor('#F59E0B'))
    status_text = status.upper()

    status_table = Table(
        [['Status:', status_text, 'Submitted:', submitted_date]],
        colWidths=[20*mm, 60*mm, 25*mm, 55*mm]
    )
    status_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), status_color),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 5*mm))

    # Notes Section (if any)
    if notes:
        elements.append(Paragraph("<b>Notes</b>", section_style))
        notes_table = Table([[notes]], colWidths=[160*mm])
        notes_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(notes_table)
        elements.append(Spacer(1, 5*mm))

    # Horizontal rule before signatures
    elements.append(Table([['', '']], colWidths=[160*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ])))
    elements.append(Spacer(1, 5*mm))

    # Signature Section - Manager Only
    sig_header_style = ParagraphStyle(
        'SigHeader',
        parent=body_style,
        fontSize=10,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    # Single manager signature (contractor does not sign)
    manager_sig_col = [
        Paragraph("<b>MANAGER APPROVAL:</b>", sig_header_style),
        Spacer(1, 3*mm),
        Paragraph("Signature: _____________________________", body_style),
        Spacer(1, 2*mm),
        Paragraph(f"Name: {manager_name}", body_style),
        Spacer(1, 2*mm),
        Paragraph("Date: _____________________________", body_style),
    ]

    signature_table = Table([[manager_sig_col]], colWidths=[160*mm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(signature_table)
    elements.append(Spacer(1, 5*mm))

    # Footer
    elements.append(Table([['', '']], colWidths=[160*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
    ])))
    elements.append(Spacer(1, 2*mm))

    footer_style = ParagraphStyle(
        'Footer',
        parent=small_style,
        alignment=TA_CENTER,
        fontSize=8,
        textColor=colors.grey
    )
    footer_text = f"""
    <b>AVENTUS CONTRACTOR MANAGEMENT</b><br/>
    Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
    <i>This timesheet requires manager approval.</i>
    """
    elements.append(Paragraph(footer_text, footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer
