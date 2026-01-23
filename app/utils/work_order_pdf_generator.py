from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os
import base64


def generate_work_order_pdf(work_order_data: dict) -> BytesIO:
    """
    Generate a professional work order PDF with Aventus branding

    Args:
        work_order_data: Dictionary containing work order information

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document with compact margins to fit on one A4 page
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Define colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')
    light_gray = colors.HexColor('#F3F4F6')

    # Custom styles - compact for single page
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=orange,
        spaceAfter=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=10,
        textColor=dark_gray,
        spaceAfter=3,
        spaceBefore=6,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=2,
        leading=11,
        fontName='Helvetica'
    )

    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=8,
        leading=10,
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

    # Add logo if available - smaller for compact layout
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=50*mm, height=12*mm)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 2*mm))

    # Add title - Appendix 1
    appendix_style = ParagraphStyle(
        'Appendix',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica'
    )
    elements.append(Paragraph("Appendix \"1\"", appendix_style))

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        textColor=orange
    )
    elements.append(Paragraph("CONTRACTOR WORK ORDER", title_style))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
    ])))
    elements.append(Spacer(1, 2*mm))

    # Details and Definitions header
    elements.append(Paragraph("<b>Details and Definitions</b>", section_style))
    elements.append(Spacer(1, 1*mm))

    # Main details
    elements.append(Paragraph(f"<b>Contractor:</b> {contractor_name}", body_style))
    elements.append(Paragraph(f"<b>Location:</b> {location}, or such other site as may be agreed from time to time by parties", body_style))
    elements.append(Spacer(1, 1*mm))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.lightgrey),
    ])))
    elements.append(Spacer(1, 1*mm))

    # Assignment Term section
    elements.append(Paragraph(f"<b>Assignment Term:</b> From {start_date} to {end_date} ({duration})", body_style))
    elements.append(Paragraph(f"<b>Position:</b> {role}", body_style))
    elements.append(Spacer(1, 1*mm))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.lightgrey),
    ])))
    elements.append(Spacer(1, 1*mm))

    # Assignment details
    elements.append(Paragraph("<b>Assignment details:</b>", body_style))
    if project_name:
        elements.append(Paragraph(f"{project_name}", body_style))
    elements.append(Paragraph("<i>(Include the type of work to be carried out)</i>", small_style))
    elements.append(Spacer(1, 1*mm))

    # Horizontal rule
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.lightgrey),
    ])))
    elements.append(Spacer(1, 1*mm))

    # Financial and other details - more compact
    elements.append(Paragraph(f"<b>Overtime:</b> N/A &nbsp;&nbsp;&nbsp;&nbsp; <b>Charge Rate:</b> {charge_rate} {currency} per professional month worked &nbsp;&nbsp;&nbsp;&nbsp; <b>Currency:</b> {currency}", body_style))
    elements.append(Paragraph("<b>Termination Notice Period:</b> TBC &nbsp;&nbsp;&nbsp;&nbsp; <b>Payment terms:</b> As per agreement, from date of invoice", body_style))
    elements.append(Paragraph("<b>Expenses:</b> All expenses approved in writing by the Client either to the Contractor or to Aventus", body_style))
    elements.append(Spacer(1, 2*mm))

    # Horizontal rule before signatures
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
    ])))
    elements.append(Spacer(1, 2*mm))

    # Signature Section - compact
    sig_header_style = ParagraphStyle(
        'SigHeader',
        parent=body_style,
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceAfter=2
    )

    signature_style = ParagraphStyle(
        'Signature',
        parent=body_style,
        fontSize=12,
        fontName='Helvetica-Oblique',
        textColor=colors.blue,
        alignment=TA_LEFT
    )

    # Get signature data
    client_signature_type = work_order_data.get('client_signature_type')
    client_signature_data = work_order_data.get('client_signature_data')
    client_signed_date = work_order_data.get('client_signed_date')

    aventus_signature_type = work_order_data.get('aventus_signature_type')
    aventus_signature_data = work_order_data.get('aventus_signature_data')
    aventus_signed_date = work_order_data.get('aventus_signed_date')

    # Two-column signature layout - compact
    # Left column - Client
    client_col = [Paragraph(f"<b>FOR {client_name.upper()}:</b>", sig_header_style)]

    if client_signature_data:
        if client_signature_type == "drawn":
            try:
                if client_signature_data.startswith('data:image'):
                    client_signature_data = client_signature_data.split(',')[1]
                sig_image_data = base64.b64decode(client_signature_data)
                sig_buffer = BytesIO(sig_image_data)
                sig_image = Image(sig_buffer, width=40*mm, height=12*mm)
                client_col.append(sig_image)
            except Exception as e:
                client_col.append(Paragraph(f"<i>[Signature]</i>", signature_style))
        else:
            client_col.append(Paragraph(f"<i>{client_signature_data}</i>", signature_style))
        client_col.append(Paragraph(f"Date: {client_signed_date[:10] if client_signed_date else 'N/A'}", body_style))
    else:
        client_col.extend([
            Paragraph("Signed: ________________________", body_style),
            Paragraph("Name: ________________________", body_style),
            Paragraph("Date: ________________________", body_style),
        ])

    # Right column - Aventus
    aventus_col = [Paragraph("<b>FOR AVENTUS:</b>", sig_header_style)]

    if aventus_signature_data:
        if aventus_signature_type == "drawn":
            try:
                if aventus_signature_data.startswith('data:image'):
                    aventus_signature_data = aventus_signature_data.split(',')[1]
                sig_image_data = base64.b64decode(aventus_signature_data)
                sig_buffer = BytesIO(sig_image_data)
                sig_image = Image(sig_buffer, width=40*mm, height=12*mm)
                aventus_col.append(sig_image)
            except Exception as e:
                aventus_col.append(Paragraph(f"<i>[Signature]</i>", signature_style))
        else:
            aventus_col.append(Paragraph(f"<i>{aventus_signature_data}</i>", signature_style))
        aventus_col.append(Paragraph(f"Date: {aventus_signed_date[:10] if aventus_signed_date else 'N/A'}", body_style))
    else:
        aventus_col.extend([
            Paragraph("Signed: ________________________", body_style),
            Paragraph("Name: ________________________", body_style),
            Paragraph("Date: ________________________", body_style),
        ])

    # Create side-by-side table
    signature_table = Table([[client_col, aventus_col]], colWidths=[90*mm, 90*mm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(signature_table)
    elements.append(Spacer(1, 2*mm))

    # Horizontal rule before footer
    elements.append(Table([['', '']], colWidths=[180*mm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.lightgrey),
    ])))
    elements.append(Spacer(1, 1*mm))

    # Footer - compact
    footer_style = ParagraphStyle(
        'Footer',
        parent=small_style,
        alignment=TA_CENTER,
        fontSize=7,
        textColor=colors.grey
    )
    footer_text = "<b>AVENTUS CONTRACTOR MANAGEMENT</b> | Email: contact@aventus.com | <i>This is a legally binding agreement.</i>"
    elements.append(Paragraph(footer_text, footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer
