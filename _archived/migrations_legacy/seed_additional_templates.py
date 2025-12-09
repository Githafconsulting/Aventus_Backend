"""
Migration: Seed additional templates (CDS, Costing Sheet, Quote Sheet, COHF)
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


# CDS (Client Deal Sheet) Template
CDS_TEMPLATE = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF6B00; margin-bottom: 10px;">CLIENT DEAL SHEET (CDS)</h1>
    <p style="font-size: 14px; color: #666;">Contractor Onboarding Details</p>
    <p style="font-size: 12px; color: #999;">Date: {{CURRENT_DATE}}</p>
</div>

<hr style="border: 1px solid #FF6B00; margin: 20px 0;"/>

<!-- Contractor Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">1. CONTRACTOR DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Full Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{FIRST_NAME}} {{SURNAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Gender</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{GENDER}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Nationality</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{NATIONALITY}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Date of Birth</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{DOB}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Home Address</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{HOME_ADDRESS}}<br/>{{ADDRESS_LINE3}}<br/>{{ADDRESS_LINE4}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Phone Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PHONE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Email</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{EMAIL}}</td>
    </tr>
</table>

<!-- Management Company Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">2. MANAGEMENT COMPANY DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Route/Business Type</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{BUSINESS_TYPE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Umbrella Company Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{UMBRELLA_COMPANY_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Company Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{COMPANY_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Registered Address</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{REGISTERED_ADDRESS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Company VAT Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{COMPANY_VAT_NO}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Company Registration No</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{COMPANY_REG_NO}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Account Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ACCOUNT_NUMBER}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">IBAN Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{IBAN_NUMBER}}</td>
    </tr>
</table>

<!-- Placement Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">3. PLACEMENT DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Client Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Project Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PROJECT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Role/Position</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ROLE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Start Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{START_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">End Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{END_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Location</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LOCATION}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Duration</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{DURATION}} months</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Currency</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}}</td>
    </tr>
</table>

<!-- Financial Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">4. FINANCIAL DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Client Charge Rate</td>
        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #FF6B00;">{{CURRENCY}} {{CLIENT_CHARGE_RATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Candidate Pay Rate</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{CANDIDATE_PAY_RATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Candidate Basic Salary (EOSB)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{CANDIDATE_BASIC_SALARY}}</td>
    </tr>
</table>

<!-- Monthly Costs -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Monthly Costs</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%;">Management Company Charges</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{MANAGEMENT_COMPANY_CHARGES}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Taxes</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{TAXES}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Bank Fees</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{BANK_FEES}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">FX (Foreign Exchange)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{FX}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Nationalisation</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{NATIONALISATION}}</td>
    </tr>
</table>

<!-- Provisions -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Provisions</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%;">EOSB (End of Service Benefit)</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{EOSB}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Vacation Pay</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{VACATION_PAY}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Sick Leave</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{SICK_LEAVE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Other Provision</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{OTHER_PROVISION}}</td>
    </tr>
</table>

<!-- One Time Costs -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">One-Time Costs</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%;">Flights</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{FLIGHTS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Visa Costs</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{VISA}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Medical Insurance</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{MEDICAL_INSURANCE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Family Costs</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{FAMILY_COSTS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Other One-Time Costs</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CURRENCY}} {{OTHER_ONE_TIME_COSTS}}</td>
    </tr>
</table>

<!-- Additional Info -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Additional Information</h3>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%;">Upfront Invoices</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{UPFRONT_INVOICES}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Security Deposit</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{SECURITY_DEPOSIT}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Laptop Provider</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LAPTOP_PROVIDER}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Other Notes</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{OTHER_NOTES}}</td>
    </tr>
</table>

<!-- Aventus Deal -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">5. AVENTUS DEAL</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Consultant</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CONSULTANT}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Any Splits?</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ANY_SPLITS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Resourcer</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{RESOURCER}}</td>
    </tr>
</table>

<!-- Invoice Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">6. INVOICE DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Timesheet Required?</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{TIMESHEET_REQUIRED}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Timesheet Approver Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{TIMESHEET_APPROVER_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Invoice Email</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{INVOICE_EMAIL}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client Contact</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_CONTACT}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Invoice Address</td>
        <td style="padding: 10px; border: 1px solid #ddd;">
            {{INVOICE_ADDRESS_LINE1}}<br/>
            {{INVOICE_ADDRESS_LINE2}}<br/>
            {{INVOICE_ADDRESS_LINE3}}<br/>
            {{INVOICE_ADDRESS_LINE4}}<br/>
            PO Box: {{INVOICE_PO_BOX}}
        </td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Tax Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{INVOICE_TAX_NUMBER}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Contractor Pay Frequency</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CONTRACTOR_PAY_FREQUENCY}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client Invoice Frequency</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_INVOICE_FREQUENCY}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client Payment Terms</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_PAYMENT_TERMS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Invoicing Preferences</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{INVOICING_PREFERENCES}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Supporting Docs Required?</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{SUPPORTING_DOCS_REQUIRED}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">PO Required</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PO_REQUIRED}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">PO Number</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PO_NUMBER}}</td>
    </tr>
</table>

<div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
    <p style="text-align: center; color: #999; font-size: 12px;">
        <strong>Aventus Resources</strong><br/>
        This document is confidential. Generated on {{CURRENT_DATE}}
    </p>
</div>
"""


# Costing Sheet Template
COSTING_SHEET_TEMPLATE = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF6B00; margin-bottom: 10px;">CONTRACTOR COSTING SHEET</h1>
    <p style="font-size: 14px; color: #666;">Expense Summary & Cost Analysis</p>
    <p style="font-size: 12px; color: #999;">Date: {{CURRENT_DATE}}</p>
</div>

<hr style="border: 1px solid #FF6B00; margin: 20px 0;"/>

<!-- Contractor Information -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">CONTRACTOR INFORMATION</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 30%; font-weight: bold;">Contractor Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CONTRACTOR_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Role</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ROLE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Location</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LOCATION}}</td>
    </tr>
</table>

<!-- Expense Items -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">EXPENSE ITEMS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <thead>
        <tr style="background-color: #1F2937; color: white;">
            <th style="padding: 12px; text-align: left; border: 1px solid #374151;">#</th>
            <th style="padding: 12px; text-align: left; border: 1px solid #374151;">Category</th>
            <th style="padding: 12px; text-align: left; border: 1px solid #374151;">Description</th>
            <th style="padding: 12px; text-align: right; border: 1px solid #374151;">Amount</th>
            <th style="padding: 12px; text-align: center; border: 1px solid #374151;">Currency</th>
        </tr>
    </thead>
    <tbody>
        {{EXPENSE_ITEMS}}
    </tbody>
</table>

<!-- Total Summary -->
<div style="margin-top: 30px; padding: 20px; background-color: #FEF3C7; border: 2px solid #F59E0B; border-radius: 8px;">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px; font-size: 18px; font-weight: bold;">TOTAL EXPENSES:</td>
            <td style="padding: 10px; text-align: right; font-size: 24px; font-weight: bold; color: #FF6B00;">{{TOTAL_AMOUNT}} {{CURRENCY}}</td>
        </tr>
    </table>
</div>

<!-- Notes -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">NOTES</h2>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB; min-height: 80px;">
    <p style="margin: 0; white-space: pre-wrap;">{{NOTES}}</p>
</div>

<div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
    <p style="text-align: center; color: #999; font-size: 12px;">
        <strong>Aventus Resources</strong><br/>
        Expense Report - Generated on {{CURRENT_DATE}}
    </p>
</div>
"""


# Quote Sheet Template
QUOTE_SHEET_TEMPLATE = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF6B00; margin-bottom: 10px;">QUOTE SHEET</h1>
    <p style="font-size: 14px; color: #666;">Saudi Arabia 3rd Party Quotation</p>
    <p style="font-size: 12px; color: #999;">Quotation Number: {{QUOTATION_NUMBER}}</p>
    <p style="font-size: 12px; color: #999;">Date: {{QUOTATION_DATE}}</p>
</div>

<hr style="border: 1px solid #FF6B00; margin: 20px 0;"/>

<!-- Contractor Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">CONTRACTOR DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Contractor Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CONTRACTOR_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Position</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{POSITION}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Location</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LOCATION}}</td>
    </tr>
</table>

<!-- Cost Breakdown -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">COST BREAKDOWN</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 12px; border: 1px solid #ddd; background-color: #F9FAFB; width: 60%; font-weight: bold;">Monthly Rate</td>
        <td style="padding: 12px; border: 1px solid #ddd; text-align: right; font-size: 16px;">{{MONTHLY_RATE}} SAR</td>
    </tr>
    <tr>
        <td style="padding: 12px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Setup Fee (One-Time)</td>
        <td style="padding: 12px; border: 1px solid #ddd; text-align: right;">{{SETUP_FEE}} SAR</td>
    </tr>
    <tr>
        <td style="padding: 12px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Other Charges</td>
        <td style="padding: 12px; border: 1px solid #ddd; text-align: right;">{{OTHER_CHARGES}} SAR</td>
    </tr>
    <tr style="background-color: #FEF3C7;">
        <td style="padding: 15px; border: 2px solid #F59E0B; font-weight: bold; font-size: 16px;">TOTAL COST</td>
        <td style="padding: 15px; border: 2px solid #F59E0B; text-align: right; font-weight: bold; font-size: 20px; color: #FF6B00;">{{TOTAL_COST}} SAR</td>
    </tr>
</table>

<!-- Payment Terms -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">TERMS & CONDITIONS</h2>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB;">
    <ul style="margin: 0; padding-left: 20px;">
        <li style="margin-bottom: 10px;">Monthly rate is per calendar month</li>
        <li style="margin-bottom: 10px;">Setup fee is a one-time charge payable upon contract signing</li>
        <li style="margin-bottom: 10px;">Payment terms as per master agreement</li>
        <li style="margin-bottom: 10px;">All rates are in Saudi Riyals (SAR)</li>
        <li style="margin-bottom: 10px;">Quotation valid for 30 days from quotation date</li>
    </ul>
</div>

<!-- Notes -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Additional Notes</h3>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB; min-height: 80px;">
    <p style="margin: 0; white-space: pre-wrap;">{{NOTES}}</p>
</div>

<!-- Provider Info -->
<div style="margin-top: 40px; padding: 20px; background-color: #F3F4F6; border-radius: 8px;">
    <p style="margin: 0; font-weight: bold;">Saudi Arabia Third-Party Provider</p>
    <p style="margin: 5px 0 0 0; color: #666;">{{THIRD_PARTY_NAME}}</p>
</div>

<div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
    <p style="text-align: center; color: #999; font-size: 12px;">
        <strong>Aventus Resources</strong><br/>
        Quote Sheet - Generated on {{CURRENT_DATE}}
    </p>
</div>
"""


# COHF (Cost of Hire Form) Template
COHF_TEMPLATE = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF6B00; margin-bottom: 10px;">COST OF HIRE FORM (COHF)</h1>
    <p style="font-size: 14px; color: #666;">UAE Third-Party Contractor Costs</p>
    <p style="font-size: 12px; color: #999;">Date: {{CURRENT_DATE}}</p>
</div>

<hr style="border: 1px solid #FF6B00; margin: 20px 0;"/>

<!-- Contractor Details -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">CONTRACTOR DETAILS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Contractor Name</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CONTRACTOR_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Position</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{POSITION}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Start Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{START_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">End Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{END_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Location</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LOCATION}}</td>
    </tr>
</table>

<!-- Monthly Costs -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">MONTHLY COSTS (AED)</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 60%;">Monthly Base Salary</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{MONTHLY_BASE_SALARY}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Housing Allowance</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{HOUSING_ALLOWANCE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Transport Allowance</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{TRANSPORT_ALLOWANCE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Other Allowances</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{OTHER_ALLOWANCES}} AED</td>
    </tr>
    <tr style="background-color: #DBEAFE;">
        <td style="padding: 12px; border: 2px solid #3B82F6; font-weight: bold;">Total Monthly Cost</td>
        <td style="padding: 12px; border: 2px solid #3B82F6; text-align: right; font-weight: bold; font-size: 16px;">{{TOTAL_MONTHLY_COST}} AED</td>
    </tr>
</table>

<!-- One-Time Costs -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">ONE-TIME COSTS (AED)</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 60%;">Recruitment Fee</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{RECRUITMENT_FEE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Visa Fee</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{VISA_FEE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Medical Insurance</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{MEDICAL_INSURANCE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Flight Tickets</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{FLIGHT_TICKETS}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Setup Costs</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{SETUP_COSTS}} AED</td>
    </tr>
    <tr style="background-color: #DBEAFE;">
        <td style="padding: 12px; border: 2px solid #3B82F6; font-weight: bold;">Total One-Time Cost</td>
        <td style="padding: 12px; border: 2px solid #3B82F6; text-align: right; font-weight: bold; font-size: 16px;">{{TOTAL_ONE_TIME_COST}} AED</td>
    </tr>
</table>

<!-- Third Party Charges -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">THIRD PARTY CHARGES (AED)</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 60%;">Management Fee</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{MANAGEMENT_FEE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Service Charge</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{SERVICE_CHARGE}} AED</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB;">Admin Fee</td>
        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{{ADMIN_FEE}} AED</td>
    </tr>
    <tr style="background-color: #DBEAFE;">
        <td style="padding: 12px; border: 2px solid #3B82F6; font-weight: bold;">Total Third Party Charges</td>
        <td style="padding: 12px; border: 2px solid #3B82F6; text-align: right; font-weight: bold; font-size: 16px;">{{TOTAL_THIRD_PARTY_CHARGES}} AED</td>
    </tr>
</table>

<!-- Grand Total -->
<div style="margin-top: 30px; padding: 20px; background-color: #FEF3C7; border: 3px solid #F59E0B; border-radius: 8px;">
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 10px; font-size: 20px; font-weight: bold;">GRAND TOTAL (Monthly):</td>
            <td style="padding: 10px; text-align: right; font-size: 28px; font-weight: bold; color: #FF6B00;">{{GRAND_TOTAL}} AED</td>
        </tr>
    </table>
</div>

<!-- Payment Terms -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 30px;">PAYMENT TERMS</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 35%; font-weight: bold;">Payment Terms</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PAYMENT_TERMS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Invoice Frequency</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{INVOICE_FREQUENCY}}</td>
    </tr>
</table>

<!-- Notes -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Additional Notes</h3>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB; min-height: 80px;">
    <p style="margin: 0; white-space: pre-wrap;">{{NOTES}}</p>
</div>

<!-- Approval Section -->
<div style="margin-top: 40px; padding: 20px; background-color: #F0FDF4; border: 2px solid #10B981; border-radius: 8px;">
    <h3 style="margin: 0 0 15px 0; color: #047857;">APPROVAL</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 15px; width: 50%; vertical-align: top;">
                <p style="margin: 0; font-weight: bold;">UAE Third Party:</p>
                <p style="margin: 10px 0 0 0;">_______________________</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Signature & Date</p>
            </td>
            <td style="padding: 15px; width: 50%; vertical-align: top;">
                <p style="margin: 0; font-weight: bold;">Aventus Manager:</p>
                <p style="margin: 10px 0 0 0;">_______________________</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Signature & Date (DocuSign)</p>
            </td>
        </tr>
    </table>
</div>

<div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
    <p style="text-align: center; color: #999; font-size: 12px;">
        <strong>Aventus Resources</strong><br/>
        Cost of Hire Form - Generated on {{CURRENT_DATE}}
    </p>
</div>
"""


def upgrade():
    """Seed additional templates"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Seeding additional templates...")

            # Template 1: CDS (Client Deal Sheet)
            template_1_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_1_id,
                "name": "Client Deal Sheet (CDS)",
                "template_type": "cds",
                "description": "Comprehensive contractor onboarding details including personal info, management company, placement, costs, and invoice details",
                "content": CDS_TEMPLATE,
                "country": None,
                "is_active": True
            })
            logger.info(f"✓ Created template: Client Deal Sheet (CDS)")

            # Template 2: Costing Sheet
            template_2_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_2_id,
                "name": "Contractor Costing Sheet",
                "template_type": "costing_sheet",
                "description": "Expense tracking and cost analysis for contractor expenses (flights, accommodation, equipment, etc.)",
                "content": COSTING_SHEET_TEMPLATE,
                "country": None,
                "is_active": True
            })
            logger.info(f"✓ Created template: Contractor Costing Sheet")

            # Template 3: Quote Sheet (Saudi Arabia)
            template_3_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_3_id,
                "name": "Saudi Arabia Quote Sheet",
                "template_type": "quote_sheet",
                "description": "Quotation document from Saudi 3rd party providers with monthly rate, setup fee, and total cost breakdown",
                "content": QUOTE_SHEET_TEMPLATE,
                "country": "Saudi Arabia",
                "is_active": True
            })
            logger.info(f"✓ Created template: Saudi Arabia Quote Sheet")

            # Template 4: COHF (Cost of Hire Form) - UAE
            template_4_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_4_id,
                "name": "UAE Cost of Hire Form (COHF)",
                "template_type": "cohf",
                "description": "Comprehensive cost breakdown for UAE contractors including monthly costs, one-time costs, and third party charges",
                "content": COHF_TEMPLATE,
                "country": "UAE",
                "is_active": True
            })
            logger.info(f"✓ Created template: UAE Cost of Hire Form (COHF)")

            conn.commit()
            logger.info(f"✓ Successfully seeded {4} additional templates")

        except Exception as e:
            logger.error(f"✗ Error during template seeding: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Seed additional templates")
    upgrade()
    print("Migration completed successfully!")
