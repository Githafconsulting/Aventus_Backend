"""
Seed COHF and Quote Sheet HTML templates into the database.
Run: python seed_cohf_quotesheet_templates.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.template import Template, TemplateType

COHF_TEMPLATE = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #111;">

  <!-- Header -->
  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
    <div>
      <p style="font-size: 14px; font-weight: bold; color: #333;">{{to_company_name}}</p>
      <p style="font-size: 11px; color: #666;">{{to_company_address}}</p>
      <p style="font-size: 11px; color: #666;">{{to_company_city}}, {{to_company_country}}</p>
      <p style="font-size: 11px; color: #666;">{{to_company_website}}</p>
    </div>
    <div style="text-align: right;">
      <h1 style="font-size: 24px; color: #00A99D; margin: 0;">Confirmation of Hire Form</h1>
      <p style="font-size: 11px; color: #666; margin-top: 4px;">COHF</p>
    </div>
  </div>

  <hr style="border: none; border-top: 2px solid #00A99D; margin: 12px 0;" />

  <!-- Reference -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: #00A99D; font-weight: bold; margin-bottom: 8px;">1. Reference</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Reference No.</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{reference_no}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Requested By</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{requested_by}}</td>
      </tr>
    </table>
    <p style="font-size: 9px; color: #999; margin-top: 6px; font-style: italic;">
      {{reference_note}}
    </p>
  </div>

  <!-- Employee Candidate Information -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: #00A99D; font-weight: bold; margin-bottom: 8px;">2. Employee / Candidate Information</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Title</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{title}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Full Name (as per passport)</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{full_name}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Nationality</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{nationality}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Date of Birth</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{date_of_birth}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Marital Status</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{marital_status}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Mobile</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{mobile}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Email</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{email}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Current Location</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{current_location}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Visa Status</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{visa_status}}</td>
      </tr>
    </table>
  </div>

  <!-- Remuneration Information -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: #00A99D; font-weight: bold; margin-bottom: 8px;">3. Remuneration Information</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Gross Salary (AED/month)</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{gross_salary}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Basic Salary</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{basic_salary}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Housing Allowance</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{housing_allowance}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Transport Allowance</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{transport_allowance}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Leave Allowance</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{leave_allowance}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Family Status</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{family_status}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Medical Insurance Category</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{medical_insurance_category}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">EOSB</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{eosb}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Management Fee</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{management_fee}}</td>
      </tr>
    </table>
  </div>

  <!-- Deployment Particulars -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: #00A99D; font-weight: bold; margin-bottom: 8px;">4. Deployment Particulars</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Visa Type</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{visa_type}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Job Title</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{job_title}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Company Name</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{company_name}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Work Location</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{work_location}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Expected Start Date</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{expected_start_date}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Expected Tenure</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{expected_tenure}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Probation Period</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{probation_period}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Notice Period</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{notice_period}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Annual Leave Days</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{annual_leave_days}} ({{annual_leave_type}})</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Weekly Working Days</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{weekly_working_days}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Chargeable Rate</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{chargeable_rate}}</td>
      </tr>
    </table>
  </div>

  <!-- Signatures -->
  <div style="display: flex; justify-content: space-between; margin-top: 32px;">
    <div style="width: 45%;">
      <p style="font-size: 12px; color: #00A99D; font-weight: bold; margin-bottom: 4px;">Third Party Signatory</p>
      <p style="font-size: 11px; color: #666; margin-bottom: 40px;">{{signatory_name}}</p>
      <div style="border-top: 1px solid #333; padding-top: 4px;">
        <p style="font-size: 10px; color: #666;">Signature & Date</p>
      </div>
    </div>
    <div style="width: 45%; text-align: right;">
      <p style="font-size: 12px; color: #00A99D; font-weight: bold; margin-bottom: 4px;">Aventus Signatory</p>
      <p style="font-size: 11px; color: #666; margin-bottom: 40px;">{{signatory_name_aventus}}</p>
      <div style="border-top: 1px solid #333; padding-top: 4px;">
        <p style="font-size: 10px; color: #666;">Counter-Signature & Date</p>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div style="margin-top: 24px; padding-top: 12px; border-top: 1px solid #ddd;">
    <p style="font-size: 9px; color: #999; text-align: center;">
      {{disclaimer_text}}
    </p>
  </div>
</div>
"""

QUOTE_SHEET_TEMPLATE = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #111;">

  <!-- Header -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
    <div>
      <p style="font-size: 16px; font-weight: bold; color: #9B1B1B;">FIRST NATIONAL HUMAN RESOURCES COMPANY</p>
      <p style="font-size: 11px; color: #666;">FNRCO</p>
    </div>
    <div style="text-align: right;">
      <h1 style="font-size: 22px; color: #9B1B1B; margin: 0;">Cost Estimation Sheet</h1>
    </div>
  </div>

  <hr style="border: none; border-top: 2px solid #9B1B1B; margin: 12px 0;" />

  <!-- Section A: Client Information -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Section A: Client Information</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Client Name</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{client_name}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Department</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{client_department}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Contact Person</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{client_contact_person}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Email</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{client_email}}</td>
      </tr>
    </table>
  </div>

  <!-- Section B: Costing Information -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Section B: Costing Information</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Costing Type</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{costing_type}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Duration</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{duration}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Recruitment Type</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{recruitment_type}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Working Hours</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{working_hours}}</td>
      </tr>
    </table>
  </div>

  <!-- Section C: Candidate Information -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Section C: Candidate / Employee Information</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; width: 35%; border: 1px solid #ddd;">Employee Name</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{employee_name}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Position</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{position}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Nationality</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{nationality}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Family Status</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{family_status}}</td>
      </tr>
      <tr>
        <td style="padding: 6px 10px; font-size: 11px; background: #f8f8f8; font-weight: bold; border: 1px solid #ddd;">Medical Insurance Class</td>
        <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">{{medical_insurance_class}}</td>
      </tr>
    </table>
  </div>

  <!-- Section D: Salary Details -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Section D: Salary Details (SAR)</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead>
        <tr style="background: #f5e6e6;">
          <th style="padding: 6px 10px; font-size: 11px; text-align: left; border: 1px solid #ddd;">Component</th>
          <th style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">Amount (SAR)</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Basic Salary</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{basic_salary}}</td></tr>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Housing Allowance</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{housing_allowance}}</td></tr>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Transportation Allowance</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{transportation_allowance}}</td></tr>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Food Allowance</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{food_allowance}}</td></tr>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Mobile Allowance</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{mobile_allowance}}</td></tr>
        <tr><td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">Other Allowance</td><td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{other_allowance}}</td></tr>
        <tr style="background: #f5e6e6; font-weight: bold;">
          <td style="padding: 6px 10px; font-size: 11px; border: 1px solid #ddd;">TOTAL SALARY</td>
          <td style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{total_salary}}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Section E: Employee Cost -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Section E: Employee Cost (SAR)</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead>
        <tr style="background: #f5e6e6;">
          <th style="padding: 6px 10px; font-size: 11px; text-align: left; border: 1px solid #ddd;">Item</th>
          <th style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">One-Time</th>
          <th style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">Annual</th>
          <th style="padding: 6px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">Monthly</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">Vacation</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_vacation_onetime}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_vacation_annual}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_vacation_monthly}}</td></tr>
        <tr><td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">EOSB</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{eosb_onetime}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{eosb_annual}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{eosb_monthly}}</td></tr>
        <tr><td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">GOSI</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{gosi_onetime}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{gosi_annual}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{gosi_monthly}}</td></tr>
        <tr><td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">Medical Insurance</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_medical_onetime}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_medical_annual}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_medical_monthly}}</td></tr>
        <tr><td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">Salary Transfer</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{salary_transfer_onetime}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{salary_transfer_annual}}</td><td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{salary_transfer_monthly}}</td></tr>
        <tr style="background: #f5e6e6; font-weight: bold;">
          <td style="padding: 5px 10px; font-size: 11px; border: 1px solid #ddd;">Total Employee Cost</td>
          <td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_cost_onetime}}</td>
          <td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_cost_annual}}</td>
          <td style="padding: 5px 10px; font-size: 11px; text-align: right; border: 1px solid #ddd;">{{employee_cost_monthly}}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Summary & Invoice -->
  <div style="margin-bottom: 16px;">
    <h3 style="font-size: 13px; color: white; background: #9B1B1B; padding: 6px 10px; margin-bottom: 0;">Summary & Invoice</h3>
    <table style="width: 60%; margin-left: auto; border-collapse: collapse; border: 1px solid #ddd;">
      <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 6px 10px; font-size: 11px; font-weight: bold;">Total Monthly Cost</td>
        <td style="padding: 6px 10px; font-size: 11px; text-align: right;">SAR {{totalMonthly}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 6px 10px; font-size: 11px; font-weight: bold;">FNRCO Service Charge</td>
        <td style="padding: 6px 10px; font-size: 11px; text-align: right;">SAR {{fnrco_service_charge}}</td>
      </tr>
      <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 6px 10px; font-size: 11px; font-weight: bold;">15% VAT</td>
        <td style="padding: 6px 10px; font-size: 11px; text-align: right;">SAR {{vat_amount}}</td>
      </tr>
      <tr style="background: #9B1B1B; color: white; font-weight: bold;">
        <td style="padding: 8px 10px; font-size: 12px;">TOTAL INVOICED AMOUNT (incl. 15% VAT)</td>
        <td style="padding: 8px 10px; font-size: 12px; text-align: right;">SAR {{total_invoiced}}</td>
      </tr>
    </table>
  </div>

  <!-- Footer -->
  <div style="margin-top: 24px; padding-top: 12px; border-top: 1px solid #ddd; text-align: center;">
    <p style="font-size: 10px; color: #666;">{{employee_name}} - Cost Estimation Sheet</p>
    <p style="font-size: 9px; color: #999;">This is a computer-generated document.</p>
  </div>
</div>
"""


def seed():
    db = SessionLocal()
    try:
        existing_cohf = db.query(Template).filter(
            Template.template_type == TemplateType.COHF.value
        ).first()
        existing_qs = db.query(Template).filter(
            Template.template_type == TemplateType.QUOTE_SHEET.value
        ).first()

        created = []

        if not existing_cohf:
            cohf = Template(
                name="Standard COHF (UAE)",
                template_type=TemplateType.COHF.value,
                description="Confirmation of Hire Form for UAE route with candidate info, remuneration, deployment details and dual signatures.",
                content=COHF_TEMPLATE.strip(),
                country="UAE",
                is_active=True,
            )
            db.add(cohf)
            created.append("COHF")
            print("Created: Standard COHF template")
        else:
            print("Skipped: COHF template already exists")

        if not existing_qs:
            qs = Template(
                name="Standard Quote Sheet (Saudi)",
                template_type=TemplateType.QUOTE_SHEET.value,
                description="FNRCO Cost Estimation Sheet for Saudi route with salary details, employee costs, government charges and invoice summary.",
                content=QUOTE_SHEET_TEMPLATE.strip(),
                country="Saudi Arabia",
                is_active=True,
            )
            db.add(qs)
            created.append("Quote Sheet")
            print("Created: Standard Quote Sheet template")
        else:
            print("Skipped: Quote Sheet template already exists")

        if created:
            db.commit()
            print(f"\nDone! Created {len(created)} template(s): {', '.join(created)}")
        else:
            print("\nNo new templates needed.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
