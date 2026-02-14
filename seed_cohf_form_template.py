"""
Seed the COHF (Confirmation of Hire Form) template for the admin Templates section.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.template import Template, TemplateType

COHF_FORM_HTML = """
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #333; font-size: 11px;">

  <!-- Letterhead -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding-bottom: 6px;">
    <div style="width: 100px; height: 40px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 9px; color: #00A99D; font-weight: bold;">auxilium</div>
    <div style="text-align: right; font-size: 10px;">
      <p style="margin: 0; font-weight: bold;">{{to_company_name}}</p>
      <p style="margin: 2px 0 0 0; color: #666;">{{to_company_address}}</p>
      <p style="margin: 0; color: #666;">{{to_company_city}}, {{to_company_country}}</p>
      <p style="margin: 0; color: #00A99D;">{{to_company_website}}</p>
    </div>
  </div>
  <hr style="border: none; border-top: 2px solid #00A99D; margin: 0 0 8px 0;" />

  <!-- Title -->
  <h1 style="text-align: center; font-size: 16px; color: #00A99D; margin: 8px 0;">Confirmation of Hire Form - UAE</h1>

  <!-- From / To -->
  <div style="display: flex; gap: 20px; margin-bottom: 10px; font-size: 10px;">
    <div style="flex: 1;"><strong>From:</strong><br/>{{from_company}}</div>
    <div style="flex: 1;"><strong>To:</strong><br/>{{to_company_name}}<br/>{{to_company_address}}<br/>{{to_company_city}}, {{to_company_country}}</div>
  </div>

  <!-- Reference -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Reference</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 4px;">
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600; width: 160px;">Document Reference</td><td style="padding: 4px 8px;">Service Agreement dated and associated General Terms (the "Agreement")</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Confirmation of Hire No</td><td style="padding: 4px 8px;">{{reference_no}}</td></tr>
    <tr><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Requested by</td><td style="padding: 4px 8px;">{{requested_by}}</td></tr>
  </table>
  <p style="font-size: 9px; color: #888; font-style: italic; margin: 2px 0 6px 0;">Capitalised terms used in this form, but not defined in it shall have the meaning given to them in the Agreement.</p>
  <p style="font-size: 10px; margin: 0 0 8px 0;">Please fill the below form for the candidate to initiate your request:</p>

  <!-- Employee Candidate Information -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Employee Candidate Information</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 8px;">
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600; width: 160px;">Title</td><td style="padding: 4px 8px;">{{title}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Full Name - per passport</td><td style="padding: 4px 8px;">{{full_name}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Nationality</td><td style="padding: 4px 8px;">{{nationality}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Date of Birth</td><td style="padding: 4px 8px;">{{date_of_birth}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Marital Status</td><td style="padding: 4px 8px;">{{marital_status}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Mobile No.</td><td style="padding: 4px 8px;">{{mobile}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Email Address</td><td style="padding: 4px 8px;">{{email}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">UAE Address or Address in Home Country (if outside UAE)</td><td style="padding: 4px 8px;">{{address}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Current Location</td><td style="padding: 4px 8px;">{{current_location}}</td></tr>
    <tr><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Current Visa Status</td><td style="padding: 4px 8px;">{{visa_status}}</td></tr>
  </table>

  <!-- Remuneration Information -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Remuneration Information</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 8px;">
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600; width: 160px;">Gross Salary</td><td style="padding: 4px 8px;">{{gross_salary}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Basic Salary</td><td style="padding: 4px 8px;">{{basic_salary}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Housing Allowance</td><td style="padding: 4px 8px;">{{housing_allowance}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Transport Allowance</td><td style="padding: 4px 8px;">{{transport_allowance}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Leave Allowance</td><td style="padding: 4px 8px;">{{leave_allowance}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Family Status</td><td style="padding: 4px 8px;">{{family_status}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Medical Insurance Category</td><td style="padding: 4px 8px;">{{medical_insurance_category}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Flight Entitlement</td><td style="padding: 4px 8px;">{{flight_entitlement}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Medical Insurance</td><td style="padding: 4px 8px;">{{medical_insurance_cost}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Visa / Labour Card</td><td style="padding: 4px 8px;">{{visa_labour_card}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">EOSB</td><td style="padding: 4px 8px;">{{eosb}}</td></tr>
    <tr><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Service Charge</td><td style="padding: 4px 8px;">{{management_fee}}</td></tr>
  </table>

  <!-- Additional Payments -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Additional Payments</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 4px;">
    <thead>
      <tr style="background: #f5f5f5;">
        <th style="padding: 4px 6px; text-align: left; border: 1px solid #ddd; width: 90px;">Payment Type</th>
        <th style="padding: 4px 6px; text-align: left; border: 1px solid #ddd;">Criteria for Payment</th>
        <th style="padding: 4px 6px; text-align: left; border: 1px solid #ddd; width: 70px;">Cap</th>
        <th style="padding: 4px 6px; text-align: left; border: 1px solid #ddd; width: 90px;">Payment Frequency</th>
        <th style="padding: 4px 6px; text-align: left; border: 1px solid #ddd;">Notes</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #e5e7eb;">
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">Commission</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{commission_criteria}}</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{commission_cap}}</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{commission_frequency}}</td>
        <td style="padding: 3px 6px;">{{commission_notes}}</td>
      </tr>
      <tr>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">Bonus</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{bonus_criteria}}</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{bonus_cap}}</td>
        <td style="padding: 3px 6px; border-right: 1px solid #ddd;">{{bonus_frequency}}</td>
        <td style="padding: 3px 6px;">{{bonus_notes}}</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size: 10px; margin: 4px 0 2px 0;"><strong>Client Declaration:</strong></p>
  <p style="font-size: 9px; margin: 2px 0; color: #555;">&#9744; I confirm that the above commission and/or bonus payments comply with UAE AML regulations and are not linked to any high-risk activities.</p>
  <p style="font-size: 9px; margin: 2px 0 8px 0; color: #555;">&#9744; I acknowledge that if the payments are uncapped, additional due diligence may be required by the Service Provider.</p>

  <!-- Deployment Particulars -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Deployment Particulars</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 8px;">
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600; width: 160px;">Visa Type</td><td style="padding: 4px 8px;">{{visa_type}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Job Title</td><td style="padding: 4px 8px;">{{job_title}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Company Name</td><td style="padding: 4px 8px;">{{company_name}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Employee Work Location</td><td style="padding: 4px 8px;">{{work_location}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Expected Start Date</td><td style="padding: 4px 8px;">{{expected_start_date}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Expected Tenure</td><td style="padding: 4px 8px;">{{expected_tenure}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Probation Period (Months)</td><td style="padding: 4px 8px;">{{probation_period}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Notice Period (Months)</td><td style="padding: 4px 8px;">{{notice_period}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Annual Leave Type (Calendar/Working Days)</td><td style="padding: 4px 8px;">{{annual_leave_type}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Annual Leave Days</td><td style="padding: 4px 8px;">{{annual_leave_days}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Weekly Working Days</td><td style="padding: 4px 8px;">{{weekly_working_days}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Weekend Days</td><td style="padding: 4px 8px;">{{weekend_days}}</td></tr>
    <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Chargeable Rate</td><td style="padding: 4px 8px;">{{chargeable_rate}}</td></tr>
    <tr><td style="padding: 4px 8px; background: #f5f5f5; font-weight: 600;">Additional Terms &amp; Conditions</td><td style="padding: 4px 8px;">{{additional_terms}}</td></tr>
  </table>

  <!-- Documents Required -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Documents Required</div>
  <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 4px;">
    <tr style="border-bottom: 1px solid #e5e7eb;">
      <td style="padding: 5px 8px; border-right: 1px solid #ddd;">&#9744; Passport Copy (in colour)</td>
      <td style="padding: 5px 8px; border-right: 1px solid #ddd;">&#9744; Current Visa Copy</td>
      <td style="padding: 5px 8px;">&#9744; Passport Size Photograph</td>
    </tr>
    <tr>
      <td style="padding: 5px 8px; border-right: 1px solid #ddd;">&#9744; Attested University Degree</td>
      <td style="padding: 5px 8px; border-right: 1px solid #ddd;">&#9744; Visa Cancellation (if any)</td>
      <td style="padding: 5px 8px;">&#9744; Emirates ID Copy (if any)</td>
    </tr>
  </table>
  <p style="font-size: 9px; color: #888; font-style: italic; margin: 2px 0 10px 0;">Note: The Employment Visa application process for the Candidate is subject to government approvals and Auxilium will not be held responsible for any rejections by the relevant authorities.</p>

  <!-- Signatures -->
  <div style="background: #00A99D; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">Signatures &amp; Company Stamp</div>
  <div style="display: flex; gap: 12px; margin-top: 4px;">
    <div style="flex: 1; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
      <p style="font-size: 10px; margin: 0 0 4px 0;">{{signatory_name}}</p>
      <p style="font-size: 10px; font-weight: bold; margin: 0 0 20px 0;">{{to_company_name}}</p>
      <p style="margin: 0; border-top: 1px solid #999; padding-top: 4px; font-size: 9px; color: #666;">[Authorised Signatory]</p>
    </div>
    <div style="flex: 1; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
      <p style="font-size: 10px; margin: 0 0 4px 0;">{{signatory_name_aventus}}</p>
      <p style="font-size: 10px; font-weight: bold; margin: 0 0 20px 0;">Aventus Talent Consultancy</p>
      <p style="margin: 0; border-top: 1px solid #999; padding-top: 4px; font-size: 9px; color: #666;">[Authorised Signatory]</p>
    </div>
  </div>

  <p style="text-align: center; color: #999; font-size: 9px; margin-top: 12px;">Note: Please sign and stamp above and submit this form for further process.</p>
</div>
"""

if __name__ == "__main__":
    db = SessionLocal()

    existing = db.query(Template).filter(Template.template_type == TemplateType.COHF).first()
    if existing:
        print(f"COHF template already exists: {existing.name}")
    else:
        template = Template(
            name="Confirmation of Hire Form (COHF)",
            template_type=TemplateType.COHF,
            description="UAE route Confirmation of Hire Form sent to third party (Auxilium). Sections: Reference, Employee Candidate Info, Remuneration, Additional Payments (Commission/Bonus), Deployment Particulars, Documents Required, and dual Signatures.",
            content=COHF_FORM_HTML,
            country="UAE",
            is_active=True,
        )
        db.add(template)
        db.commit()
        print(f"Created: Confirmation of Hire Form (COHF)")

    db.close()
