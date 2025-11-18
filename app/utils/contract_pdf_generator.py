from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os


def generate_consultant_contract_pdf(contractor_data: dict) -> BytesIO:
    """
    Generate a professional multi-page consultant contract PDF with Aventus branding

    Args:
        contractor_data: Dictionary containing contractor information

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document
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

    # Define colors
    orange = colors.HexColor('#FF6B00')
    dark_gray = colors.HexColor('#1F2937')
    light_gray = colors.HexColor('#F3F4F6')

    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=orange,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=dark_gray,
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold',
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14,
        fontName='Helvetica'
    )

    small_style = ParagraphStyle(
        'Small',
        parent=body_style,
        fontSize=9,
        leading=12,
    )

    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_RIGHT,
        textColor=dark_gray,
        fontName='Helvetica'
    )

    # Extract data
    contractor_name = f"{contractor_data.get('first_name', '')} {contractor_data.get('surname', '')}"
    client_name = contractor_data.get('client_name', '[Client Name]')
    client_address = contractor_data.get('client_address', '[Client Address]')
    job_title = contractor_data.get('role', '[Job Title]')
    location = contractor_data.get('location', '[Location]')
    duration = contractor_data.get('duration', '6 months')
    start_date = contractor_data.get('start_date', '[Start Date]')
    day_rate = contractor_data.get('candidate_pay_rate', '[Day Rate]')
    currency = contractor_data.get('currency', 'USD')

    today = datetime.now().strftime('%B %d, %Y')

    # HEADER with logo and company details
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'av-logo.png')

    # Logo on the left
    logo = Image(logo_path, width=40*mm, height=12*mm)

    # Company details on the right
    company_details = Paragraph("""
        <font size=8>
        Office 14, Golden Mile 4<br/>
        Palm Jumeirah<br/>
        Dubai, United Arab Emirates
        </font>
    """, address_style)

    # Create header table with logo and details
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
    elements.append(Spacer(1, 12))

    # CONTRACT TITLE
    elements.append(Paragraph(f"This Consultant Contract is made {today}", title_style))
    elements.append(Spacer(1, 12))

    # PARTIES SECTION
    elements.append(Paragraph("<b>BETWEEN:</b>", body_style))
    elements.append(Spacer(1, 6))

    parties_text = f"""
    <b>(1)</b> Aventus Talent Consultant Office 14, Golden Mile 4, Palm Jumeirah, Dubai, United Arab Emirates (the "Principal"); and<br/><br/>
    <b>(2)</b> <u><font color='#FF6B00'><b>{contractor_name}</b></font></u> (the "Consultant")<br/><br/>
    <b>(3)</b> <u>{client_name}</u>, with its principal place of business at <u>{client_address}</u> ("client").
    """
    elements.append(Paragraph(parties_text, body_style))
    elements.append(Spacer(1, 12))

    # SECTION 1: JOB TITLE
    section_header_1 = Table([[Paragraph("<b>1. JOB TITLE</b>", section_style)]], colWidths=[165*mm])
    section_header_1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_1)

    job_title_text = f"""
    <b>1.1</b> The Consultant is engaged as <u><b>{job_title}</b></u> for the Principal. The place of work is <u><b>{location}</b></u>.
    The consultant will be contracted for a duration of <u><b>{duration}</b></u> initially after which there may be extensions.
    """
    elements.append(Paragraph(job_title_text, body_style))
    elements.append(Spacer(1, 8))

    # SECTION 2: DUTIES
    section_header_2 = Table([[Paragraph("<b>2. DUTIES</b>", section_style)]], colWidths=[165*mm])
    section_header_2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_2)

    elements.append(Paragraph("<b>2.1</b> The Consultant shall during the term of this Contract serve the client to the best of their ability in the position stated above.", body_style))
    elements.append(Spacer(1, 8))

    # SECTION 3: REPORTING CHANNEL
    section_header_3 = Table([[Paragraph("<b>3. REPORTING CHANNEL</b>", section_style)]], colWidths=[165*mm])
    section_header_3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_3)

    elements.append(Paragraph("<b>3.1</b> The Consultant shall report directly to selected members of The Client.", body_style))
    elements.append(Spacer(1, 8))

    # SECTION 4: JOINING DATE
    section_header_4 = Table([[Paragraph("<b>4. JOINING DATE</b>", section_style)]], colWidths=[165*mm])
    section_header_4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_4)

    joining_text = f"""
    <b>4.1</b> The engagement of the Consultant will commence on <u><b>{start_date}</b></u> (the "Commencement Date")
    for a duration of <u><b>{duration}</b></u>. There will be a possibility for the contract to extend and this can be
    determined prior to the end date.
    """
    elements.append(Paragraph(joining_text, body_style))
    elements.append(Spacer(1, 8))

    # SECTION 5: PROBATIONARY PERIOD
    section_header_5 = Table([[Paragraph("<b>5. PROBATIONARY PERIOD</b>", section_style)]], colWidths=[165*mm])
    section_header_5.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_5)

    probation_text = """
    <b>5.1</b> The Consultant shall be on probation for the first six (6) months from the joining date. During the
    probation period engagement may be terminated by providing 30 days written notice period. The consultant will
    not be entitled to receive any benefits or compensation whatsoever.
    """
    elements.append(Paragraph(probation_text, body_style))
    elements.append(PageBreak())

    # PAGE 2 - REMUNERATION AND WORKING HOURS
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # SECTION 6: REMUNERATION
    section_header_6 = Table([[Paragraph("<b>6. REMUNERATION</b>", section_style)]], colWidths=[165*mm])
    section_header_6.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_6)

    remuneration_text = f"""
    <b>6.1</b> The Consultant shall be paid the following on a monthly basis in arrears and the Consultant shall keep
    payments confidential and shall not disclose to anyone within or outside the Principal.<br/><br/>
    <b>Contract Rate: <u><font color='#FF6B00'>{day_rate} {currency}</font></u> per Day</b><br/><br/>
    Part month calculation.<br/>
    Payment will be only for the days worked.<br/>
    Laptop will be provided by the consultant.<br/><br/>
    <b>6.2</b> The Consultant acknowledges and agrees that the Principal shall pay monthly salaries based on a client
    approved timesheet. The principal is entitled at any time to make deductions from the Consultant's Remuneration or
    from any other sums due to the Consultant from the Principal in respect of any overpayment of any kind made to the
    Consultant or any outstanding debt or other sums due from the Consultant or unapproved time off requests.<br/><br/>
    <b>6.3</b> The consultant acknowledges that they are based remotely from principal's place of business and as such,
    the payments of remuneration and allowances is inclusive of all individual taxation requirements and the consultant
    is responsible for settling any and all taxes in their home country or country of residence due to be paid arising
    out of this agreement.
    """
    elements.append(Paragraph(remuneration_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 7: WORKING HOURS
    section_header_7 = Table([[Paragraph("<b>7. WORKING HOURS AND PLACE OF WORK</b>", section_style)]], colWidths=[165*mm])
    section_header_7.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_7)

    working_hours_text = """
    <b>7.1</b> The Consultant's hours of work will be in synchronisation with client's working hours. This is usually
    Sunday through Thursday.<br/><br/>
    <b>7.2</b> The Consultant may be required to work additional hours as may be necessary for the proper performance
    of duties, which will be payable based on the approved timesheet.
    """
    elements.append(Paragraph(working_hours_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 8: SICKNESS ABSENCE
    section_header_8 = Table([[Paragraph("<b>8. SICKNESS ABSENCE</b>", section_style)]], colWidths=[165*mm])
    section_header_8.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_8)

    sickness_text = """
    <b>8.1</b> Reasonable sickness absence is expected throughout the year, however as the consultant works on a remote
    base and day rate there is not defined sick leave. Should the consultant deem himself unable to perform their role
    any given day due to illness, they should inform the client and the Principal immediately.
    """
    elements.append(Paragraph(sickness_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 9: DURATION & TERMINATION
    section_header_9 = Table([[Paragraph("<b>9. DURATION & TERMINATION</b>", section_style)]], colWidths=[165*mm])
    section_header_9.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_9)

    termination_text = """
    <b>9.1</b> After confirmation of the Engagement and completion of the Probation Period, either Party may terminate
    this Contract by providing 30 days written notice of intention to terminate the Engagement.<br/><br/>
    <b>9.2</b> The Principal reserves the right to pay the Consultant in lieu of part or all of the notice period or
    require that during the notice period they do not attend the Principal's/Client's premises or/and carry out day to
    day duties (and remain at home on "Garden Leave"). During any Garden Leave period, the Consultant shall be entitled
    to Remuneration and benefits in the usual manner.
    """
    elements.append(Paragraph(termination_text, body_style))
    elements.append(PageBreak())

    # PAGE 3 - POST TERMINATION & CONFIDENTIALITY
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # SECTION 10: POST TERMINATION RESTRICTIONS
    section_header_10 = Table([[Paragraph("<b>10. POST TERMINATION RESTRICTIONS</b>", section_style)]], colWidths=[165*mm])
    section_header_10.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_10)

    post_termination_text = """
    <b>10.1</b> Unless approved by the principal, The Consultant shall not during the Engagement or for a period of
    six (6) months after its termination in the country of the residence:<br/>
    • seek to procure orders from, or deal with in any way, any client(s) or supplier(s) of the Principal with whom
    the Consultant has had regular dealings during the Engagement;<br/>
    • engage the services of, provide services to or become interested in any business activity that is in competition
    with the Principal's business.<br/>
    • Provide the same or similar services to those provided under this agreement whether directly or indirectly to
    the client or any customer of the client for whose benefit the services are to be performed.
    """
    elements.append(Paragraph(post_termination_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 11: CONFIDENTIALITY
    section_header_11 = Table([[Paragraph("<b>11. CONFIDENTIALITY</b>", section_style)]], colWidths=[165*mm])
    section_header_11.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_11)

    confidentiality_text = """
    <b>11.1</b> The Consultant shall not at any time (either during or after the termination of the Engagement)
    disclose or communicate to any person or use any person any confidential information concerning the business
    dealings, affairs or conduct of the Principal, or the client and their staff or business partners or any similar
    matters which may come to the Consultant's knowledge or possession during the term of the Consultant's Engagement.<br/><br/>
    <b>11.2</b> The Consultant hereby irrevocably agrees that during the course of the Engagement, and for an
    indefinite period thereafter, they shall not, other than in the course of fulfilling their obligations as an
    Consultant or as required by law, disclose or divulge any information that might be of a confidential or
    proprietary nature regarding the Principal or the client, (including, in particular, but without limitation,
    information relating to the business of the Principal or The Client or any of its clients or their affairs and
    which includes but is not limited to information relating to the Principal's clients and customers, prospective
    clients and customers, suppliers, agents or distributors of the Principal, commercial, financial or marketing
    information, customer lists, technical information and know-how comprising trade secrets and intellectual property
    belonging to the Principal or The Client, and information regarding the business and financial affairs of the
    Principal), to any person (natural or legal). Further, the Consultant shall not use any confidential or proprietary
    information obtained during the course of Engagement at any time (whether during the term of Engagement or
    subsequently) to compete with or otherwise act to the detriment of the Principal or The Client.<br/><br/>
    <b>11.3</b> Any documents in hard copy or in other electronic form and any equipment, that the Consultant may
    receive or use while performing duties during the tenure of Engagement shall remain the property of the Principal
    or The Client and shall be returned to the Principal at the Principal's request and, in any event, shall be
    delivered to the Principal on the termination of the Engagement. The Consultant shall not make copies of any such
    materials for personal use or advantage, whether they be hard or electronic copy.
    """
    elements.append(Paragraph(confidentiality_text, body_style))
    elements.append(PageBreak())

    # PAGE 4 - GENERAL PROVISIONS
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # SECTION 12: GENERAL PROVISIONS
    section_header_12 = Table([[Paragraph("<b>12. GENERAL PROVISIONS</b>", section_style)]], colWidths=[165*mm])
    section_header_12.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_12)

    general_text = """
    <b>12.1</b> This Contract contains the full agreement between the Principal and the Consultant regarding the
    provisions and conditions of the Engagement relationship. It replaces all previous agreements.<br/><br/>
    <b>12.2</b> On termination of the Consultant's Engagement for whatever reason, consultant will immediately return
    all correspondence, documents, computer discs and software, equipment and any other property of any kind belonging
    to the Principal and which may be in the Consultant's possession or control. For the avoidance of doubt, the
    Consultant shall not be permitted to retain any such information or documents (or copies thereof) after the
    termination of Engagement for any reason.<br/><br/>
    <b>12.3</b> Any amendment to this Agreement must be made in writing and signed by both the Parties in order to be
    legally valid. Each Party declares having received a copy of this Contract duly signed by both Parties.<br/><br/>
    <b>12.4</b> This Agreement may be executed by electronic signature transmission by the parties hereto in to separate
    counterparts, each of which when executed shall be deemed to be an original but all of which taken together shall
    constitute the one and same agreement.<br/><br/>
    <b>12.4</b> In this Agreement words denoting the singular shall include the plural and vice versa. Headings in this
    Agreement are for convenience only and shall not affect its interpretation; and any reference to any legislative
    provision is a reference to that provision as for the time being in any way amended or re-enacted. All references
    to times or dates herein shall be construed with reference to the Gregorian calendar.<br/><br/>
    <b>12.5</b> Notices may be given by either party by letter addressed to the other party at the addresses stated
    above or in the case of the Consultant, the last known address, which shall be deemed to be the address last
    notified by the Consultant to the Principal and any notice given by letter shall be deemed to have been given at
    the time at which the letter would have been delivered in the ordinary course of post or acknowledged as received
    by international courier. Where a notice is delivered by electronic means and the party sending the notice can
    demonstrate via electronic record the sending of the notice, the other party is deemed to have received the notice
    at the same time.
    """
    elements.append(Paragraph(general_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 13: DISPUTE RESOLUTION
    section_header_13 = Table([[Paragraph("<b>13. DISPUTE RESOLUTION</b>", section_style)]], colWidths=[165*mm])
    section_header_13.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_13)

    dispute_text = """
    <b>13.1</b> Each party irrevocably agrees that the courts of the United Arab Emirates shall have exclusive
    jurisdiction to settle any dispute or claim arising out of or in connection with this Agreement or its subject
    matter or formation (including non-contractual disputes or claims).
    """
    elements.append(Paragraph(dispute_text, body_style))
    elements.append(Spacer(1, 10))

    # SECTION 14: GOVERNING LAW
    section_header_14 = Table([[Paragraph("<b>14. GOVERNING LAW</b>", section_style)]], colWidths=[165*mm])
    section_header_14.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('LINEABOVE', (0, 0), (0, 0), 3, orange),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(section_header_14)

    elements.append(Paragraph("<b>14.1</b> This contract shall be governed and be construed in accordance with the Laws of UAE", body_style))
    elements.append(Spacer(1, 15))

    # IN WITNESS WHEREOF
    elements.append(Paragraph("<b>IN WITNESS WHEREOF the Parties have caused this Contract to be executed as of the date written above.</b>", body_style))
    elements.append(Spacer(1, 20))

    # SIGNATURES SECTION
    elements.append(Paragraph("<b>Signed for and on behalf of the Principal.</b>", body_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("_____________________", body_style))
    elements.append(Paragraph("PRINCIPAL<br/>NAME<br/>POSITION", small_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>I, <u>{contractor_name}</u> the undersigned confirm my acceptance of the above terms and conditions.</b>", body_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("__________________________", body_style))
    elements.append(Paragraph("CONSULTANT", small_style))

    # Footer
    elements.append(Spacer(1, 15))
    footer_line = Table([['']], colWidths=[165*mm])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(footer_line)

    footer_text = """<font size=8 color='gray'>
    AVENTUS Talent Consultant • Office 14, Golden Mile 4, Palm Jumeirah, Dubai, UAE<br/>
    This document is confidential and proprietary. Unauthorized distribution is prohibited.
    </font>"""
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
