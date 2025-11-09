from datetime import datetime
from typing import Dict, Any


EMPLOYMENT_CONTRACT_TEMPLATE = """
# EMPLOYMENT AGREEMENT

**This Employment Agreement** ("Agreement") is entered into as of **{{START_DATE}}** between:

**AVENTUS CONTRACTOR MANAGEMENT** ("Company")
- Address: [Company Address]
- Email: contact@aventus.com

AND

**{{CONTRACTOR_NAME}}** ("Contractor")
- Email: {{CONTRACTOR_EMAIL}}
- Date of Birth: {{DOB}}
- Nationality: {{NATIONALITY}}

---

## 1. POSITION AND DUTIES

1.1 The Company hereby engages the Contractor to perform services as **{{ROLE}}** for the client **{{CLIENT_NAME}}**.

1.2 The Contractor shall perform the duties and responsibilities as outlined in the job description and as may be assigned by the Company from time to time.

1.3 The Contractor shall devote their full business time and attention to the performance of their duties under this Agreement.

---

## 2. TERM OF EMPLOYMENT

2.1 This Agreement shall commence on **{{START_DATE}}** and shall continue until **{{END_DATE}}**, unless terminated earlier in accordance with the provisions of this Agreement.

2.2 The employment period is **{{DURATION}}**.

2.3 The Contractor will be based at **{{LOCATION}}**.

---

## 3. COMPENSATION

3.1 The Contractor shall receive compensation as follows:

- **Pay Rate:** {{CURRENCY}} {{PAY_RATE}} per month
- **Payment Frequency:** Monthly
- **Payment Method:** Bank transfer to designated account

3.2 All compensation is subject to applicable tax deductions and withholdings as required by law.

3.3 The Contractor acknowledges that the client charge rate is {{CURRENCY}} {{CHARGE_RATE}} per month.

---

## 4. BENEFITS AND ENTITLEMENTS

4.1 The Contractor shall be entitled to the following benefits:

- Annual leave in accordance with local labor law
- Sick leave as per company policy
- End of Service Benefits (EOSB) as required by law
- Medical insurance coverage (if applicable)

4.2 Specific benefit details will be provided separately.

---

## 5. WORKING HOURS

5.1 The normal working hours shall be as determined by the client and in accordance with local labor regulations.

5.2 The Contractor may be required to work additional hours as reasonably necessary to fulfill their duties.

---

## 6. CONFIDENTIALITY

6.1 The Contractor acknowledges that during the course of employment, they may have access to confidential information belonging to the Company and/or the client.

6.2 The Contractor agrees to maintain the confidentiality of all such information both during and after the term of employment.

6.3 This obligation shall survive the termination of this Agreement.

---

## 7. INTELLECTUAL PROPERTY

7.1 All intellectual property, inventions, discoveries, and works created by the Contractor in the course of employment shall be the sole property of the Company and/or the client.

7.2 The Contractor agrees to execute any documents necessary to perfect the Company's or client's rights in such intellectual property.

---

## 8. TERMINATION

8.1 This Agreement may be terminated:
   a) By mutual written agreement of both parties
   b) By either party giving 30 days' written notice
   c) Immediately for cause, including but not limited to misconduct, breach of contract, or poor performance

8.2 Upon termination, the Contractor shall:
   a) Return all Company and client property
   b) Complete all pending assignments as directed
   c) Receive final settlement in accordance with this Agreement

---

## 9. NON-COMPETE AND NON-SOLICITATION

9.1 During the term of this Agreement and for a period of 6 months thereafter, the Contractor shall not:
   a) Engage in any business that competes with the Company or the client
   b) Solicit or attempt to solicit any clients or customers of the Company
   c) Solicit or attempt to recruit any employees of the Company or the client

---

## 10. GOVERNING LAW

10.1 This Agreement shall be governed by and construed in accordance with the laws of **{{JURISDICTION}}**.

10.2 Any disputes arising from this Agreement shall be subject to the exclusive jurisdiction of the courts of **{{JURISDICTION}}**.

---

## 11. ENTIRE AGREEMENT

11.1 This Agreement constitutes the entire agreement between the parties and supersedes all prior agreements, understandings, and arrangements.

11.2 Any amendments to this Agreement must be made in writing and signed by both parties.

---

## 12. ACCEPTANCE

By signing below, both parties acknowledge that they have read, understood, and agree to be bound by the terms and conditions of this Employment Agreement.

---

**FOR THE COMPANY:**

AVENTUS CONTRACTOR MANAGEMENT

Authorized Signatory: ___________________________

Date: ___________________________

---

**CONTRACTOR ACKNOWLEDGMENT:**

I, **{{CONTRACTOR_NAME}}**, hereby acknowledge that I have read and understood the terms and conditions of this Employment Agreement, and I voluntarily agree to be bound by them.

**Electronic Signature:**

Signature: ___________________________ [TO BE SIGNED ELECTRONICALLY]

Date: {{SIGNATURE_DATE}}

---

*This is a legally binding agreement. Please read carefully before signing. If you have any questions or concerns, please contact the Company before signing.*
"""


def populate_contract_template(contractor_data: Dict[str, Any]) -> str:
    """
    Populate the contract template with contractor data

    Args:
        contractor_data: Dictionary containing contractor information

    Returns:
        Populated contract as string
    """
    contract = EMPLOYMENT_CONTRACT_TEMPLATE

    # Helper function to safely get value with default
    def get_value(key: str, default: str = "[Not Provided]") -> str:
        value = contractor_data.get(key)
        return str(value) if value else default

    # Build contractor name
    contractor_name = f"{get_value('first_name', '')} {get_value('surname', '')}".strip()
    if not contractor_name:
        contractor_name = "[Contractor Name]"

    # Replace all placeholders
    replacements = {
        "{{CONTRACTOR_NAME}}": contractor_name,
        "{{CONTRACTOR_EMAIL}}": get_value("email", "[Email]"),
        "{{DOB}}": get_value("dob", "[Date of Birth]"),
        "{{NATIONALITY}}": get_value("nationality", "[Nationality]"),
        "{{ROLE}}": get_value("role", "[Role/Position]"),
        "{{CLIENT_NAME}}": get_value("client_name", "[Client Name]"),
        "{{START_DATE}}": get_value("start_date", "[Start Date]"),
        "{{END_DATE}}": get_value("end_date", "[End Date]"),
        "{{DURATION}}": get_value("duration", "[Duration]"),
        "{{LOCATION}}": get_value("location", "[Location]"),
        "{{CURRENCY}}": get_value("currency", "SAR"),
        "{{PAY_RATE}}": get_value("candidate_pay_rate", "[Pay Rate]"),
        "{{CHARGE_RATE}}": get_value("client_charge_rate", "[Charge Rate]"),
        "{{JURISDICTION}}": "Kingdom of Saudi Arabia",
        "{{SIGNATURE_DATE}}": datetime.now().strftime("%B %d, %Y"),
    }

    for placeholder, value in replacements.items():
        contract = contract.replace(placeholder, value)

    return contract
