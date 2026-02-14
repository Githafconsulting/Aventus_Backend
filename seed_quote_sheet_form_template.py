"""
Seed the FNRCO Cost Estimation Sheet (Quote Sheet) form template.
This is the visual template shown in the admin Templates section.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.template import Template, TemplateType

QUOTE_SHEET_FORM_HTML = """
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #111; font-size: 11px;">

  <!-- Letterhead -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 2px solid #9B1B1B;">
    <div style="width: 80px; height: 40px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 9px; color: #666;">FNRCO Logo</div>
    <div style="text-align: center;">
      <h1 style="font-size: 14px; color: #9B1B1B; margin: 0;">FIRST NATIONAL HUMAN RESOURCES COMPANY</h1>
      <p style="font-size: 11px; color: #9B1B1B; margin: 2px 0 0 0;">Cost Estimation Sheet</p>
    </div>
    <div style="width: 80px; height: 40px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 9px; color: #666;">Aventus Logo</div>
  </div>

  <!-- Sections A & B Side by Side -->
  <div style="display: flex; gap: 12px; margin-bottom: 10px;">
    <div style="flex: 1;">
      <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">A. CLIENT INFORMATION</div>
      <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600; width: 110px;">Name</td><td style="padding: 4px 8px;">{{client_name}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Department</td><td style="padding: 4px 8px;">{{client_department}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Email Address</td><td style="padding: 4px 8px;">{{client_email}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Mobile No</td><td style="padding: 4px 8px;">{{client_mobile}}</td></tr>
        <tr><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Contact Person</td><td style="padding: 4px 8px;">{{client_contact_person}}</td></tr>
      </table>
    </div>
    <div style="flex: 1;">
      <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">B. COSTING INFORMATION</div>
      <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600; width: 110px;">Costing Type</td><td style="padding: 4px 8px;">Cost Plus</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Duration</td><td style="padding: 4px 8px;">12 months</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Recruitment Type</td><td style="padding: 4px 8px;">Local</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Issued Date</td><td style="padding: 4px 8px;">{{issued_date}}</td></tr>
        <tr><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Working Hours</td><td style="padding: 4px 8px;">{{working_hours}}</td></tr>
      </table>
    </div>
  </div>

  <!-- Sections C & D Side by Side -->
  <div style="display: flex; gap: 12px; margin-bottom: 10px;">
    <div style="flex: 1;">
      <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">C. CANDIDATE / EMPLOYEE INFORMATION</div>
      <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600; width: 110px;">Name</td><td style="padding: 4px 8px;">{{employee_name}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Position</td><td style="padding: 4px 8px;">{{position}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Nationality</td><td style="padding: 4px 8px;">{{nationality}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Profession</td><td style="padding: 4px 8px;">{{profession}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Status</td><td style="padding: 4px 8px;">{{family_status}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">No. of Dependents</td><td style="padding: 4px 8px;">{{num_dependents}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Vacation</td><td style="padding: 4px 8px;">{{vacation_days}}</td></tr>
        <tr><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Medical Insurance</td><td style="padding: 4px 8px;">{{medical_insurance_class}}</td></tr>
      </table>
    </div>
    <div style="flex: 1;">
      <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">D. SALARY DETAILS (SAR)</div>
      <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600; width: 110px;">Basic Salary</td><td style="padding: 4px 8px; text-align: right;">{{basic_salary}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Housing</td><td style="padding: 4px 8px; text-align: right;">{{housing_allowance}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Transportation</td><td style="padding: 4px 8px; text-align: right;">{{transportation_allowance}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Food</td><td style="padding: 4px 8px; text-align: right;">{{food_allowance}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Mobile</td><td style="padding: 4px 8px; text-align: right;">{{mobile_allowance}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Fixed OT</td><td style="padding: 4px 8px; text-align: right;">{{fixed_ot}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 4px 8px; background: #f9fafb; font-weight: 600;">Other</td><td style="padding: 4px 8px; text-align: right;">{{other_allowance}}</td></tr>
        <tr style="background: #9b1b1b10; font-weight: bold;"><td style="padding: 4px 8px;">TOTAL SALARY</td><td style="padding: 4px 8px; text-align: right;">{{total_salary}}</td></tr>
      </table>
    </div>
  </div>

  <!-- E. EMPLOYEE COST -->
  <div style="margin-bottom: 10px;">
    <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">E. EMPLOYEE COST (SAR)</div>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead><tr style="background: #f3f4f6;">
        <th style="padding: 4px 8px; text-align: left; border-right: 1px solid #ddd; width: 180px;">DESCRIPTION</th>
        <th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ONE TIME</th>
        <th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ANNUAL</th>
        <th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">MONTHLY</th>
        <th style="padding: 4px 8px; text-align: left;">REMARKS</th>
      </tr></thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Employee Vacation Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">EOSB - End of Service Benefits</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">GOSI</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Medical Insurance Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Exit Re-Entry Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Salary Transfer Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Public Holiday Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Sick Leave Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="background: #9b1b1b10; font-weight: bold;"><td style="padding: 4px 8px; border-right: 1px solid #ddd;">Total of Employee Cost</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px;"></td></tr>
      </tbody>
    </table>
  </div>

  <!-- F. FAMILY COST -->
  <div style="margin-bottom: 10px;">
    <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">F. FAMILY COST (SAR)</div>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead><tr style="background: #f3f4f6;"><th style="padding: 4px 8px; text-align: left; border-right: 1px solid #ddd; width: 180px;">DESCRIPTION</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ONE TIME</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ANNUAL</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">MONTHLY</th><th style="padding: 4px 8px; text-align: left;">REMARKS</th></tr></thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Medical Insurance Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Vacation Ticket Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Exit Re-Entry Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Joining Ticket Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Visa Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Levy Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="background: #9b1b1b10; font-weight: bold;"><td style="padding: 4px 8px; border-right: 1px solid #ddd;">Total of Family Cost</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px;"></td></tr>
      </tbody>
    </table>
  </div>

  <!-- G. GOVERNMENT COST -->
  <div style="margin-bottom: 10px;">
    <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">G. GOVERNMENT COST (SAR)</div>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead><tr style="background: #f3f4f6;"><th style="padding: 4px 8px; text-align: left; border-right: 1px solid #ddd; width: 180px;">DESCRIPTION</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ONE TIME</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ANNUAL</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">MONTHLY</th><th style="padding: 4px 8px; text-align: left;">REMARKS</th></tr></thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">SCE - Saudi Council of Engineering</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">SOCPA</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Medical Test for Iqama</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">E-Wakala and Chamber &amp; Mofa</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Visa Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Iqama Transfer Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Iqama Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Saudi Admin Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Ajeer Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="background: #9b1b1b10; font-weight: bold;"><td style="padding: 4px 8px; border-right: 1px solid #ddd;">Total of Government Charges</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px;"></td></tr>
      </tbody>
    </table>
  </div>

  <!-- H. MOBILIZATION COST -->
  <div style="margin-bottom: 10px;">
    <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">H. MOBILIZATION COST (SAR)</div>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead><tr style="background: #f3f4f6;"><th style="padding: 4px 8px; text-align: left; border-right: 1px solid #ddd; width: 180px;">DESCRIPTION</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ONE TIME</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ANNUAL</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">MONTHLY</th><th style="padding: 4px 8px; text-align: left;">REMARKS</th></tr></thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Visa Processing Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Recruitment Fee Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Philippines Placement Fee</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Joining Ticket Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Egypt Government Fee</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Relocation Cost</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Other Expenses</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px;"></td></tr>
        <tr style="background: #9b1b1b10; font-weight: bold;"><td style="padding: 4px 8px; border-right: 1px solid #ddd;">Total of Mobilization Cost</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px;"></td></tr>
      </tbody>
    </table>
  </div>

  <!-- SUMMARY -->
  <div style="margin-bottom: 10px;">
    <div style="background: #9B1B1B; color: white; font-weight: bold; padding: 4px 8px; font-size: 10px; border-radius: 3px 3px 0 0;">SUMMARY</div>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
      <thead><tr style="background: #f3f4f6;"><th style="padding: 4px 8px; text-align: left; border-right: 1px solid #ddd;">DESCRIPTION</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ONE TIME</th><th style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd; width: 90px;">ANNUAL</th><th style="padding: 4px 8px; text-align: right; width: 90px;">MONTHLY</th></tr></thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Total Salary (D)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right;">{{total_salary}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Employee Cost (E)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right;">0.00</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Family Cost (F)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right;">0.00</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Government Cost (G)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right;">0.00</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">Mobilization Cost (H)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 3px 8px; text-align: right;">0.00</td></tr>
        <tr style="background: #9b1b1b20; font-weight: bold; border-bottom: 1px solid #ddd;"><td style="padding: 4px 8px; border-right: 1px solid #ddd;">GRAND TOTAL</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right; border-right: 1px solid #ddd;">0.00</td><td style="padding: 4px 8px; text-align: right;">0.00</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">FNRCO Service Charge</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right;">{{service_charge}}</td></tr>
        <tr style="border-bottom: 1px solid #e5e7eb;"><td style="padding: 3px 8px; border-right: 1px solid #ddd;">15% VAT (on Medical Insurance + Service Charge)</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">-</td><td style="padding: 3px 8px; text-align: right; border-right: 1px solid #ddd;">{{vat_annual}}</td><td style="padding: 3px 8px; text-align: right;">{{vat_monthly}}</td></tr>
        <tr style="background: #9B1B1B; color: white; font-weight: bold;"><td style="padding: 6px 8px; border-right: 1px solid #7a1515;">TOTAL INVOICE AMOUNT</td><td style="padding: 6px 8px; text-align: right; border-right: 1px solid #7a1515;">-</td><td style="padding: 6px 8px; text-align: right; border-right: 1px solid #7a1515;">-</td><td style="padding: 6px 8px; text-align: right;">{{total_invoice}}</td></tr>
      </tbody>
    </table>
  </div>

  <p style="text-align: center; color: #999; font-size: 9px; margin-top: 12px;">FNRCO Cost Estimation Sheet - Saudi Arabia Route</p>
</div>
"""

if __name__ == "__main__":
    db = SessionLocal()

    existing = db.query(Template).filter(Template.template_type == TemplateType.QUOTE_SHEET).first()
    if existing:
        print(f"Quote Sheet template already exists: {existing.name}")
    else:
        template = Template(
            name="FNRCO Cost Estimation Sheet (Quote Sheet)",
            template_type=TemplateType.QUOTE_SHEET,
            description="Saudi Arabia route cost estimation form sent to FNRCO third party. Sections A-H covering client info, costing, employee details, salary, employee costs, family costs, government costs, and mobilization costs with 15% VAT calculation.",
            content=QUOTE_SHEET_FORM_HTML,
            country="Saudi Arabia",
            is_active=True,
        )
        db.add(template)
        db.commit()
        print(f"Created: FNRCO Cost Estimation Sheet (Quote Sheet)")

    db.close()
