from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os
import base64


def generate_work_order_pdf(work_order_data: dict) -> BytesIO:
    """
    Generate a professional work order PDF with clean table-based design
    """
    buffer = BytesIO()

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
    light_orange = colors.HexColor('#FFF7ED')
    light_gray = colors.HexColor('#F9FAFB')
    border_gray = colors.HexColor('#E5E7EB')

    # Custom styles
    appendix_style = ParagraphStyle(
        'Appendix',
        fontSize=9,
        alignment=TA_CENTER,
        fontName='Helvetica',
        textColor=dark_gray,
        spaceAfter=2
    )

    title_style = ParagraphStyle(
        'Title',
        fontSize=16,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        textColor=orange,
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=9,
        alignment=TA_CENTER,
        fontName='Helvetica',
        textColor=dark_gray
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    label_style = ParagraphStyle(
        'Label',
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=dark_gray
    )

    value_style = ParagraphStyle(
        'Value',
        fontSize=9,
        fontName='Helvetica',
        textColor=dark_gray
    )

    small_style = ParagraphStyle(
        'Small',
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.gray
    )

    italic_style = ParagraphStyle(
        'Italic',
        fontSize=8,
        fontName='Helvetica-Oblique',
        textColor=colors.gray
    )

    signature_text_style = ParagraphStyle(
        'SignatureText',
        fontSize=11,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#1E40AF')
    )

    # Extract data
    contractor_name = work_order_data.get('contractor_name', '[Contractor Name]')
    client_name = work_order_data.get('client_name', '[Client Name]')
    role = work_order_data.get('role', '[Role]')
    location = work_order_data.get('location', '[Location]')
    start_date = work_order_data.get('start_date', '[Start Date]')
    end_date = work_order_data.get('end_date', '[End Date]')
    duration = work_order_data.get('duration', '[Duration]')
    charge_rate = work_order_data.get('charge_rate', '[Charge Rate]')
    currency = work_order_data.get('currency', 'AED')
    work_order_number = work_order_data.get('work_order_number', '[WO-NUMBER]')
    project_name = work_order_data.get('project_name', '')
    rate_type = work_order_data.get('rate_type', 'monthly')  # monthly or daily

    # Logo - proper aspect ratio
    logo_path = os.path.join("app", "static", "av-logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60*mm, height=18*mm, kind='proportional')
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 4*mm))

    # Appendix
    elements.append(Paragraph('Appendix "1"', appendix_style))

    # Title
    elements.append(Paragraph("CONTRACTOR WORK ORDER", title_style))
    elements.append(Paragraph(f"Reference: {work_order_number}", subtitle_style))
    elements.append(Spacer(1, 5*mm))

    # Details and Definitions Section
    details_data = [
        [Paragraph("<b>DETAILS AND DEFINITIONS</b>", section_header_style), '', '', ''],
        [
            Paragraph("Contractor", label_style),
            Paragraph(contractor_name, value_style),
            Paragraph("Client", label_style),
            Paragraph(client_name, value_style)
        ],
        [
            Paragraph("Location", label_style),
            Paragraph(f"{location}, or such other site as may be agreed from time to time by parties", value_style),
            '', ''
        ],
        [
            Paragraph("Position", label_style),
            Paragraph(role, value_style),
            '', ''
        ],
    ]

    details_table = Table(details_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    details_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('SPAN', (0, 0), (-1, 0)),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        # Data rows
        ('BACKGROUND', (0, 1), (0, -1), light_gray),
        ('BACKGROUND', (2, 1), (2, 1), light_gray),
        ('GRID', (0, 1), (-1, -1), 0.5, border_gray),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Span for location and position rows
        ('SPAN', (1, 2), (3, 2)),
        ('SPAN', (1, 3), (3, 3)),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 4*mm))

    # Assignment Term Section
    term_data = [
        [Paragraph("<b>ASSIGNMENT TERM</b>", section_header_style), '', '', ''],
        [
            Paragraph("Start Date", label_style),
            Paragraph(start_date, value_style),
            Paragraph("End Date", label_style),
            Paragraph(end_date, value_style)
        ],
        [
            Paragraph("Duration", label_style),
            Paragraph(str(duration), value_style),
            '', ''
        ],
    ]

    term_table = Table(term_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    term_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('SPAN', (0, 0), (-1, 0)),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (0, -1), light_gray),
        ('BACKGROUND', (2, 1), (2, 1), light_gray),
        ('GRID', (0, 1), (-1, -1), 0.5, border_gray),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 2), (3, 2)),
    ]))
    elements.append(term_table)
    elements.append(Spacer(1, 4*mm))

    # Assignment Details Section
    assignment_content = project_name if project_name else ""
    assignment_data = [
        [Paragraph("<b>ASSIGNMENT DETAILS</b>", section_header_style)],
        [Paragraph(assignment_content, value_style)],
        [Paragraph("<i>(Include the type of work to be carried out)</i>", italic_style)],
    ]
    assignment_table = Table(assignment_data, colWidths=[180*mm])
    assignment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('BOX', (0, 1), (-1, -1), 0.5, border_gray),
        ('TOPPADDING', (0, 1), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 2),
        ('TOPPADDING', (0, 2), (-1, 2), 0),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 6),
        ('LEFTPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(assignment_table)
    elements.append(Spacer(1, 4*mm))

    # Financial Details Section - Display rate per month or per day based on rate_type
    rate_period = "per professional month worked" if rate_type == "monthly" else "per day worked"
    financial_data = [
        [Paragraph("<b>FINANCIAL & OTHER DETAILS</b>", section_header_style), '', '', ''],
        [
            Paragraph("Overtime", label_style),
            Paragraph("N/A", value_style),
            Paragraph("Charge Rate", label_style),
            Paragraph(f"{charge_rate} {currency} {rate_period}", value_style)
        ],
        [
            Paragraph("Currency", label_style),
            Paragraph(currency, value_style),
            Paragraph("Termination Notice", label_style),
            Paragraph("TBC", value_style)
        ],
        [
            Paragraph("Payment Terms", label_style),
            Paragraph("As per agreement, from date of invoice", value_style),
            '', ''
        ],
        [
            Paragraph("Expenses", label_style),
            Paragraph("All expenses approved in writing by the Client either to the Contractor or to Aventus", value_style),
            '', ''
        ],
    ]

    financial_table = Table(financial_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('SPAN', (0, 0), (-1, 0)),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (0, -1), light_gray),
        ('BACKGROUND', (2, 1), (2, 2), light_gray),
        ('GRID', (0, 1), (-1, -1), 0.5, border_gray),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 4), (3, 4)),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 6*mm))

    # Signatures Section
    client_signature_type = work_order_data.get('client_signature_type')
    client_signature_data = work_order_data.get('client_signature_data')
    client_signed_date = work_order_data.get('client_signed_date', '')
    client_signer_name = work_order_data.get('client_signer_name', '')

    aventus_signature_type = work_order_data.get('aventus_signature_type')
    aventus_signature_data = work_order_data.get('aventus_signature_data')
    aventus_signed_date = work_order_data.get('aventus_signed_date', '')
    aventus_signer_name = work_order_data.get('aventus_signer_name', '')

    def build_signature_content(sig_type, sig_data, signed_date, party_name, signer_name='', company_name=''):
        content = []
        content.append(Paragraph(f"<b>FOR {party_name}:</b>", label_style))
        if company_name:
            content.append(Paragraph(f"Company: {company_name}", small_style))
        content.append(Spacer(1, 3*mm))

        if sig_data:
            if sig_type == "drawn":
                try:
                    if sig_data.startswith('data:image'):
                        sig_data = sig_data.split(',')[1]
                    sig_image_data = base64.b64decode(sig_data)
                    sig_buffer = BytesIO(sig_image_data)
                    sig_image = Image(sig_buffer, width=45*mm, height=15*mm)
                    content.append(sig_image)
                except:
                    content.append(Paragraph("[Signature]", signature_text_style))
            else:
                content.append(Paragraph(f"<i>{sig_data}</i>", signature_text_style))
            content.append(Spacer(1, 2*mm))
            if signer_name:
                content.append(Paragraph(f"Name: {signer_name}", small_style))
            date_display = signed_date if signed_date else 'N/A'
            content.append(Paragraph(f"Date: {date_display}", small_style))
        else:
            content.append(Spacer(1, 10*mm))
            content.append(Paragraph("Signed: ________________________", value_style))
            content.append(Spacer(1, 2*mm))
            content.append(Paragraph("Name: ________________________", value_style))
            content.append(Spacer(1, 2*mm))
            content.append(Paragraph("Date: ________________________", value_style))

        return content

    client_content = build_signature_content(
        client_signature_type, client_signature_data, client_signed_date,
        "THE CLIENT", client_signer_name, client_name
    )
    aventus_content = build_signature_content(
        aventus_signature_type, aventus_signature_data, aventus_signed_date,
        "AVENTUS", aventus_signer_name, "Aventus Contractor Management"
    )

    sig_data = [
        [Paragraph("<b>SIGNATURES</b>", section_header_style), ''],
        [client_content, aventus_content]
    ]

    sig_table = Table(sig_data, colWidths=[90*mm, 90*mm])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('SPAN', (0, 0), (-1, 0)),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), light_orange),
        ('BOX', (0, 1), (-1, -1), 0.5, border_gray),
        ('LINEBEFORE', (1, 1), (1, 1), 0.5, border_gray),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 6*mm))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph(
        "<b>AVENTUS CONTRACTOR MANAGEMENT</b> | Email: contact@aventus.com | <i>This is a legally binding agreement.</i>",
        footer_style
    ))

    doc.build(elements)
    buffer.seek(0)

    return buffer
