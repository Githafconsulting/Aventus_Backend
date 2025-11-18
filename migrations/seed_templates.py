"""
Migration: Seed initial templates from existing codebase
"""
from sqlalchemy import create_engine, text
import logging
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Employment Contract Template (from contract_template.py)
EMPLOYMENT_CONTRACT_TEMPLATE = """
<h1>EMPLOYMENT AGREEMENT</h1>

<p><strong>This Employment Agreement</strong> ("Agreement") is entered into as of <strong>{{START_DATE}}</strong> between:</p>

<p><strong>AVENTUS CONTRACTOR MANAGEMENT</strong> ("Company")<br/>
- Address: [Company Address]<br/>
- Email: contact@aventus.com</p>

<p>AND</p>

<p><strong>{{CONTRACTOR_NAME}}</strong> ("Contractor")<br/>
- Email: {{CONTRACTOR_EMAIL}}<br/>
- Date of Birth: {{DOB}}<br/>
- Nationality: {{NATIONALITY}}</p>

<hr/>

<h2>1. POSITION AND DUTIES</h2>

<p>1.1 The Company hereby engages the Contractor to perform services as <strong>{{ROLE}}</strong> for the client <strong>{{CLIENT_NAME}}</strong>.</p>

<p>1.2 The Contractor shall perform the duties and responsibilities as outlined in the job description and as may be assigned by the Company from time to time.</p>

<p>1.3 The Contractor shall devote their full business time and attention to the performance of their duties under this Agreement.</p>

<hr/>

<h2>2. TERM OF EMPLOYMENT</h2>

<p>2.1 This Agreement shall commence on <strong>{{START_DATE}}</strong> and shall continue until <strong>{{END_DATE}}</strong>, unless terminated earlier in accordance with the provisions of this Agreement.</p>

<p>2.2 The employment period is <strong>{{DURATION}}</strong>.</p>

<p>2.3 The Contractor will be based at <strong>{{LOCATION}}</strong>.</p>

<hr/>

<h2>3. COMPENSATION</h2>

<p>3.1 The Contractor shall receive compensation as follows:</p>

<ul>
<li><strong>Pay Rate:</strong> {{CURRENCY}} {{PAY_RATE}} per month</li>
<li><strong>Payment Frequency:</strong> Monthly</li>
<li><strong>Payment Method:</strong> Bank transfer to designated account</li>
</ul>

<p>3.2 All compensation is subject to applicable tax deductions and withholdings as required by law.</p>

<p>3.3 The Contractor acknowledges that the client charge rate is {{CURRENCY}} {{CHARGE_RATE}} per month.</p>

<hr/>

<h2>4. BENEFITS AND ENTITLEMENTS</h2>

<p>4.1 The Contractor shall be entitled to the following benefits:</p>

<ul>
<li>Annual leave in accordance with local labor law</li>
<li>Sick leave as per company policy</li>
<li>End of Service Benefits (EOSB) as required by law</li>
<li>Medical insurance coverage (if applicable)</li>
</ul>

<p>4.2 Specific benefit details will be provided separately.</p>

<hr/>

<h2>5. WORKING HOURS</h2>

<p>5.1 The normal working hours shall be as determined by the client and in accordance with local labor regulations.</p>

<p>5.2 The Contractor may be required to work additional hours as reasonably necessary to fulfill their duties.</p>

<hr/>

<h2>6. CONFIDENTIALITY</h2>

<p>6.1 The Contractor acknowledges that during the course of employment, they may have access to confidential information belonging to the Company and/or the client.</p>

<p>6.2 The Contractor agrees to maintain the confidentiality of all such information both during and after the term of employment.</p>

<p>6.3 This obligation shall survive the termination of this Agreement.</p>

<hr/>

<h2>7. INTELLECTUAL PROPERTY</h2>

<p>7.1 All intellectual property, inventions, discoveries, and works created by the Contractor in the course of employment shall be the sole property of the Company and/or the client.</p>

<p>7.2 The Contractor agrees to execute any documents necessary to perfect the Company's or client's rights in such intellectual property.</p>

<hr/>

<h2>8. TERMINATION</h2>

<p>8.1 This Agreement may be terminated:</p>
<ul>
<li>a) By mutual written agreement of both parties</li>
<li>b) By either party giving 30 days' written notice</li>
<li>c) Immediately for cause, including but not limited to misconduct, breach of contract, or poor performance</li>
</ul>

<p>8.2 Upon termination, the Contractor shall:</p>
<ul>
<li>a) Return all Company and client property</li>
<li>b) Complete all pending assignments as directed</li>
<li>c) Receive final settlement in accordance with this Agreement</li>
</ul>

<hr/>

<h2>9. NON-COMPETE AND NON-SOLICITATION</h2>

<p>9.1 During the term of this Agreement and for a period of 6 months thereafter, the Contractor shall not:</p>
<ul>
<li>a) Engage in any business that competes with the Company or the client</li>
<li>b) Solicit or attempt to solicit any clients or customers of the Company</li>
<li>c) Solicit or attempt to recruit any employees of the Company or the client</li>
</ul>

<hr/>

<h2>10. GOVERNING LAW</h2>

<p>10.1 This Agreement shall be governed by and construed in accordance with the laws of <strong>{{JURISDICTION}}</strong>.</p>

<p>10.2 Any disputes arising from this Agreement shall be subject to the exclusive jurisdiction of the courts of <strong>{{JURISDICTION}}</strong>.</p>

<hr/>

<h2>11. ENTIRE AGREEMENT</h2>

<p>11.1 This Agreement constitutes the entire agreement between the parties and supersedes all prior agreements, understandings, and arrangements.</p>

<p>11.2 Any amendments to this Agreement must be made in writing and signed by both parties.</p>

<hr/>

<h2>12. ACCEPTANCE</h2>

<p>By signing below, both parties acknowledge that they have read, understood, and agree to be bound by the terms and conditions of this Employment Agreement.</p>

<hr/>

<p><strong>FOR THE COMPANY:</strong></p>

<p>AVENTUS CONTRACTOR MANAGEMENT</p>

<p>Authorized Signatory: ___________________________</p>

<p>Date: ___________________________</p>

<hr/>

<p><strong>CONTRACTOR ACKNOWLEDGMENT:</strong></p>

<p>I, <strong>{{CONTRACTOR_NAME}}</strong>, hereby acknowledge that I have read and understood the terms and conditions of this Employment Agreement, and I voluntarily agree to be bound by them.</p>

<p><strong>Electronic Signature:</strong></p>

<p>Signature: ___________________________ [TO BE SIGNED ELECTRONICALLY]</p>

<p>Date: {{SIGNATURE_DATE}}</p>

<hr/>

<p><em>This is a legally binding agreement. Please read carefully before signing. If you have any questions or concerns, please contact the Company before signing.</em></p>
"""


# Consultant Contract Template (extracted from contract_pdf_generator.py)
CONSULTANT_CONTRACT_TEMPLATE = """
<div style="text-align: center;">
    <h1 style="color: #FF6B00;">CONSULTANT CONTRACT</h1>
    <h2>This Consultant Contract is made {{CURRENT_DATE}}</h2>
</div>

<h3>BETWEEN:</h3>

<p><strong>(1)</strong> Aventus Talent Consultant Office 14, Golden Mile 4, Palm Jumeirah, Dubai, United Arab Emirates (the "Principal"); and</p>

<p><strong>(2)</strong> <u><strong style="color: #FF6B00;">{{CONTRACTOR_NAME}}</strong></u> (the "Consultant")</p>

<p><strong>(3)</strong> <u>{{CLIENT_NAME}}</u>, with its principal place of business at <u>{{CLIENT_ADDRESS}}</u> ("client").</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">1. JOB TITLE</h3>

<p><strong>1.1</strong> The Consultant is engaged as <u><strong>{{ROLE}}</strong></u> for the Principal. The place of work is <u><strong>{{LOCATION}}</strong></u>. The consultant will be contracted for a duration of <u><strong>{{DURATION}}</strong></u> initially after which there may be extensions.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">2. DUTIES</h3>

<p><strong>2.1</strong> The Consultant shall during the term of this Contract serve the client to the best of their ability in the position stated above.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">3. REPORTING CHANNEL</h3>

<p><strong>3.1</strong> The Consultant shall report directly to selected members of The Client.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">4. JOINING DATE</h3>

<p><strong>4.1</strong> The engagement of the Consultant will commence on <u><strong>{{START_DATE}}</strong></u> (the "Commencement Date") for a duration of <u><strong>{{DURATION}}</strong></u>. There will be a possibility for the contract to extend and this can be determined prior to the end date.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">5. PROBATIONARY PERIOD</h3>

<p><strong>5.1</strong> The Consultant shall be on probation for the first six (6) months from the joining date. During the probation period engagement may be terminated by providing 30 days written notice period. The consultant will not be entitled to receive any benefits or compensation whatsoever.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">6. REMUNERATION</h3>

<p><strong>6.1</strong> The Consultant shall be paid the following on a monthly basis in arrears and the Consultant shall keep payments confidential and shall not disclose to anyone within or outside the Principal.</p>

<p><strong>Contract Rate: <u style="color: #FF6B00;">{{PAY_RATE}} {{CURRENCY}}</u> per Day</strong></p>

<p>Part month calculation.<br/>
Payment will be only for the days worked.<br/>
Laptop will be provided by the consultant.</p>

<p><strong>6.2</strong> The Consultant acknowledges and agrees that the Principal shall pay monthly salaries based on a client approved timesheet. The principal is entitled at any time to make deductions from the Consultant's Remuneration or from any other sums due to the Consultant from the Principal in respect of any overpayment of any kind made to the Consultant or any outstanding debt or other sums due from the Consultant or unapproved time off requests.</p>

<p><strong>6.3</strong> The consultant acknowledges that they are based remotely from principal's place of business and as such, the payments of remuneration and allowances is inclusive of all individual taxation requirements and the consultant is responsible for settling any and all taxes in their home country or country of residence due to be paid arising out of this agreement.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">7. WORKING HOURS AND PLACE OF WORK</h3>

<p><strong>7.1</strong> The Consultant's hours of work will be in synchronisation with client's working hours. This is usually Sunday through Thursday.</p>

<p><strong>7.2</strong> The Consultant may be required to work additional hours as may be necessary for the proper performance of duties, which will be payable based on the approved timesheet.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">8. SICKNESS ABSENCE</h3>

<p><strong>8.1</strong> Reasonable sickness absence is expected throughout the year, however as the consultant works on a remote base and day rate there is not defined sick leave. Should the consultant deem himself unable to perform their role any given day due to illness, they should inform the client and the Principal immediately.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">9. DURATION & TERMINATION</h3>

<p><strong>9.1</strong> After confirmation of the Engagement and completion of the Probation Period, either Party may terminate this Contract by providing 30 days written notice of intention to terminate the Engagement.</p>

<p><strong>9.2</strong> The Principal reserves the right to pay the Consultant in lieu of part or all of the notice period or require that during the notice period they do not attend the Principal's/Client's premises or/and carry out day to day duties (and remain at home on "Garden Leave"). During any Garden Leave period, the Consultant shall be entitled to Remuneration and benefits in the usual manner.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">10. POST TERMINATION RESTRICTIONS</h3>

<p><strong>10.1</strong> Unless approved by the principal, The Consultant shall not during the Engagement or for a period of six (6) months after its termination in the country of the residence:</p>
<ul>
<li>seek to procure orders from, or deal with in any way, any client(s) or supplier(s) of the Principal with whom the Consultant has had regular dealings during the Engagement;</li>
<li>engage the services of, provide services to or become interested in any business activity that is in competition with the Principal's business.</li>
<li>Provide the same or similar services to those provided under this agreement whether directly or indirectly to the client or any customer of the client for whose benefit the services are to be performed.</li>
</ul>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">11. CONFIDENTIALITY</h3>

<p><strong>11.1</strong> The Consultant shall not at any time (either during or after the termination of the Engagement) disclose or communicate to any person or use any person any confidential information concerning the business dealings, affairs or conduct of the Principal, or the client and their staff or business partners or any similar matters which may come to the Consultant's knowledge or possession during the term of the Consultant's Engagement.</p>

<p><strong>11.2</strong> The Consultant hereby irrevocably agrees that during the course of the Engagement, and for an indefinite period thereafter, they shall not, other than in the course of fulfilling their obligations as an Consultant or as required by law, disclose or divulge any information that might be of a confidential or proprietary nature regarding the Principal or the client.</p>

<p><strong>11.3</strong> Any documents in hard copy or in other electronic form and any equipment, that the Consultant may receive or use while performing duties during the tenure of Engagement shall remain the property of the Principal or The Client and shall be returned to the Principal at the Principal's request and, in any event, shall be delivered to the Principal on the termination of the Engagement.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">12. GENERAL PROVISIONS</h3>

<p><strong>12.1</strong> This Contract contains the full agreement between the Principal and the Consultant regarding the provisions and conditions of the Engagement relationship. It replaces all previous agreements.</p>

<p><strong>12.2</strong> On termination of the Consultant's Engagement for whatever reason, consultant will immediately return all correspondence, documents, computer discs and software, equipment and any other property of any kind belonging to the Principal and which may be in the Consultant's possession or control.</p>

<p><strong>12.3</strong> Any amendment to this Agreement must be made in writing and signed by both the Parties in order to be legally valid. Each Party declares having received a copy of this Contract duly signed by both Parties.</p>

<p><strong>12.4</strong> This Agreement may be executed by electronic signature transmission by the parties hereto in to separate counterparts, each of which when executed shall be deemed to be an original but all of which taken together shall constitute the one and same agreement.</p>

<p><strong>12.5</strong> Notices may be given by either party by letter addressed to the other party at the addresses stated above or in the case of the Consultant, the last known address.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">13. DISPUTE RESOLUTION</h3>

<p><strong>13.1</strong> Each party irrevocably agrees that the courts of the United Arab Emirates shall have exclusive jurisdiction to settle any dispute or claim arising out of or in connection with this Agreement or its subject matter or formation (including non-contractual disputes or claims).</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">14. GOVERNING LAW</h3>

<p><strong>14.1</strong> This contract shall be governed and be construed in accordance with the Laws of UAE</p>

<hr/>

<p><strong>IN WITNESS WHEREOF the Parties have caused this Contract to be executed as of the date written above.</strong></p>

<p><strong>Signed for and on behalf of the Principal.</strong></p>
<p>_____________________<br/>
PRINCIPAL<br/>
NAME<br/>
POSITION</p>

<p><strong>I, <u>{{CONTRACTOR_NAME}}</u> the undersigned confirm my acceptance of the above terms and conditions.</strong></p>
<p>__________________________<br/>
CONSULTANT</p>
"""


# Work Order Template (extracted from work_order_pdf_generator.py)
WORK_ORDER_TEMPLATE = """
<div style="text-align: center;">
    <h1 style="color: #FF6B00;">WORK ORDER</h1>
    <h2>Work Order Number: {{WORK_ORDER_NUMBER}}</h2>
    <p><strong>Date:</strong> {{CURRENT_DATE}}</p>
</div>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">CONTRACTOR DETAILS</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc; width: 30%;"><strong>Contractor Name:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{CONTRACTOR_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ccc; background-color: #F3F4F6;"><strong>Business Type:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{BUSINESS_TYPE}}</td>
    </tr>
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc;"><strong>Company Name:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{UMBRELLA_COMPANY_NAME}}</td>
    </tr>
</table>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">ASSIGNMENT DETAILS</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc; width: 30%;"><strong>Client:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{CLIENT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ccc; background-color: #F3F4F6;"><strong>Job Title/Role:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{ROLE}}</td>
    </tr>
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc;"><strong>Project Name:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{PROJECT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ccc; background-color: #F3F4F6;"><strong>Location:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{LOCATION}}</td>
    </tr>
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc;"><strong>Start Date:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{START_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ccc; background-color: #F3F4F6;"><strong>End Date:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{END_DATE}}</td>
    </tr>
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc;"><strong>Duration:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{DURATION}}</td>
    </tr>
</table>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">FINANCIAL DETAILS</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc; width: 30%;"><strong>Currency:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{CURRENCY}}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ccc; background-color: #F3F4F6;"><strong>Pay Rate:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{PAY_RATE}} {{CURRENCY}}</td>
    </tr>
    <tr style="background-color: #F3F4F6;">
        <td style="padding: 8px; border: 1px solid #ccc;"><strong>Charge Rate:</strong></td>
        <td style="padding: 8px; border: 1px solid #ccc;">{{CHARGE_RATE}} {{CURRENCY}}</td>
    </tr>
</table>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">TERMS AND CONDITIONS</h3>

<p><strong>1. Scope of Work:</strong> The contractor agrees to perform the services as described in this work order for the specified client and project.</p>

<p><strong>2. Payment Terms:</strong> Payment will be made according to the agreed pay rate and frequency as per the main consultant agreement.</p>

<p><strong>3. Duration:</strong> This work order is valid for the specified duration unless terminated earlier by either party with appropriate notice.</p>

<p><strong>4. Confidentiality:</strong> The contractor must maintain confidentiality of all client and project information as per the main consultant agreement.</p>

<p><strong>5. Compliance:</strong> The contractor must comply with all client policies and procedures during the assignment.</p>

<hr/>

<h3 style="background-color: #F3F4F6; padding: 8px; border-top: 3px solid #FF6B00;">SIGNATURES</h3>

<table style="width: 100%; margin-top: 30px;">
    <tr>
        <td style="width: 50%; vertical-align: top;">
            <p><strong>Aventus Resources</strong></p>
            <p>_____________________<br/>
            Authorized Signature<br/><br/>
            Date: _____________</p>
        </td>
        <td style="width: 50%; vertical-align: top;">
            <p><strong>{{CONTRACTOR_NAME}}</strong></p>
            <p>_____________________<br/>
            Contractor Signature<br/><br/>
            Date: _____________</p>
        </td>
    </tr>
</table>

<hr style="margin-top: 40px;"/>

<p style="text-align: center; font-size: 0.9em; color: #666;">
<strong>Aventus Resources</strong><br/>
Email: info@aventusresources.com | Phone: +971 XXX XXXX<br/>
This is a computer-generated document and does not require a physical signature unless specified.
</p>
"""


def upgrade():
    """Seed initial templates"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Seeding initial templates...")

            # Template 1: Employment Contract
            template_1_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_1_id,
                "name": "Standard Employment Agreement",
                "template_type": "contract",
                "description": "Standard employment contract template for contractors with all standard clauses",
                "content": EMPLOYMENT_CONTRACT_TEMPLATE,
                "country": None,
                "is_active": True
            })
            logger.info(f"✓ Created template: Standard Employment Agreement")

            # Template 2: Consultant Contract (UAE)
            template_2_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_2_id,
                "name": "UAE Consultant Contract",
                "template_type": "contract",
                "description": "Professional consultant contract for UAE-based contractors with Aventus Talent",
                "content": CONSULTANT_CONTRACT_TEMPLATE,
                "country": "UAE",
                "is_active": True
            })
            logger.info(f"✓ Created template: UAE Consultant Contract")

            # Template 3: Work Order
            template_3_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_3_id,
                "name": "Standard Work Order",
                "template_type": "work_order",
                "description": "Standard work order document for contractor assignments",
                "content": WORK_ORDER_TEMPLATE,
                "country": None,
                "is_active": True
            })
            logger.info(f"✓ Created template: Standard Work Order")

            conn.commit()
            logger.info(f"✓ Successfully seeded {3} templates")

        except Exception as e:
            logger.error(f"✗ Error during template seeding: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Seed initial templates")
    upgrade()
    print("Migration completed successfully!")
