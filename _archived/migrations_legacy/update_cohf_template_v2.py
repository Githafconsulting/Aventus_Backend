"""
Migration: Update COHF template to Version 2
Date: 2024-12-06
Description: Updates the COHF template in the database with the new version 2 content
             including all new fields: Additional Payments, Client Declaration,
             extended Deployment Particulars, Documents Required, and 4 signature blocks.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# COHF Template Version 2 HTML Content
COHF_TEMPLATE_V2 = """
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
    <!-- Header -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #00A99D; padding-bottom: 15px; margin-bottom: 20px;">
        <div>
            <img src="/auxilium-logo.png" alt="Auxilium Logo" style="height: 60px;" onerror="this.style.display='none'"/>
        </div>
        <div style="text-align: right; font-size: 12px; color: #333;">
            <strong>Auxilium Management Group FZE</strong><br/>
            PO Box 333625<br/>
            Dubai<br/>
            UAE<br/>
            <span style="color: #00A99D;">www.auxilium.ae</span>
        </div>
    </div>

    <!-- Schedule Header -->
    <div style="text-align: center; margin-bottom: 10px;">
        <h2 style="color: #333; font-size: 14px; margin: 0;">SCHEDULE 2: CONFIRMATION OF HIRE FORM</h2>
    </div>

    <!-- Title -->
    <div style="text-align: center; margin-bottom: 25px;">
        <h1 style="color: #00A99D; font-size: 20px; margin: 0;">Confirmation of Hire Form - UAE</h1>
    </div>

    <!-- From/To Section -->
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
        <div style="width: 48%;">
            <strong style="font-size: 12px; color: #333;">From:</strong><br/>
            <span style="font-size: 11px; color: #333;">{{from_company}}</span>
        </div>
        <div style="width: 48%;">
            <strong style="font-size: 12px; color: #333;">To:</strong><br/>
            <span style="font-size: 11px; color: #333;">
                Auxilium Management Group FZE<br/>
                PO Box 333625<br/>
                Dubai<br/>
                UAE
            </span>
        </div>
    </div>

    <!-- Reference Section -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Reference</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; width: 35%; font-weight: bold;">Document Reference:</td>
                <td style="border: 1px solid #ddd; padding: 8px;">Service Agreement dated and associated General Terms (the "Agreement")</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Confirmation of Hire No:</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{reference_no}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Requested by:</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{requested_by}}</td>
            </tr>
        </table>
        <p style="font-size: 10px; color: #666; font-style: italic; margin-top: 8px;">Capitalised terms used in this form, but not defined in it shall have the meaning given to them in the Agreement.</p>
        <p style="font-size: 11px; color: #333; margin-top: 5px;">Please fill the below form for the candidate to initiate your request:</p>
    </div>

    <!-- Employee Candidate Information -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Employee Candidate Information</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; width: 35%; font-weight: bold;">Title</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{title}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Full Name - per passport</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{full_name}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Nationality</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{nationality}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Date of Birth</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{date_of_birth}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Marital Status</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{marital_status}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Mobile No.</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{mobile}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Email Address</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{email}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">UAE Address or Address in Home Country<br/><span style="font-weight: normal; font-size: 10px;">(if outside UAE)</span></td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{address}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Current Location</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{current_location}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Current Visa Status</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{visa_status}}</td>
            </tr>
        </table>
    </div>

    <!-- Remuneration Information -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Remuneration Information</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; width: 35%; font-weight: bold;">Gross Salary</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{gross_salary}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Basic Salary</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{basic_salary}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Housing Allowance</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{housing_allowance}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Transport Allowance</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{transport_allowance}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Leave Allowance</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{leave_allowance}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Family Status</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{family_status}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Medical Insurance Category</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{medical_insurance_category}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Flight Entitlement</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{flight_entitlement}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Medical Insurance</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{medical_insurance_cost}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Visa / Labour Card</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{visa_labour_card}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">EOSB</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{eosb}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Management Fee</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{management_fee}}</td>
            </tr>
        </table>
    </div>

    <!-- Additional Payments -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Additional Payments</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">Payment Type</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">Criteria for Payment</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">Cap</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">Payment Frequency</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">Commission</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{commission_criteria}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{commission_cap}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{commission_frequency}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{commission_notes}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">Bonus</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{bonus_criteria}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{bonus_cap}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{bonus_frequency}}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{bonus_notes}}</td>
                </tr>
            </tbody>
        </table>
        <div style="margin-top: 10px; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;">
            <p style="font-size: 11px; font-weight: bold; color: #333; margin: 0 0 8px 0;">Client Declaration:</p>
            <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">☐ I confirm that the above commission and/or bonus payments comply with UAE AML regulations and are not linked to any high-risk activities.</p>
            <p style="font-size: 10px; color: #333; margin: 0;">☐ I acknowledge that if the payments are uncapped, additional due diligence may be required by the Service Provider.</p>
        </div>
    </div>

    <!-- Deployment Particulars -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Deployment Particulars</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; width: 35%; font-weight: bold;">Visa Type</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{visa_type}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Job Title</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{job_title}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Company Name</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{company_name}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Employee Work Location</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{work_location}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Expected Start Date</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{expected_start_date}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Expected Tenure</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{expected_tenure}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Probation Period (Months)</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{probation_period}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Notice Period (Months)</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{notice_period}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Annual Leave Type (Calendar/Working Days)</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{annual_leave_type}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Annual Leave Days</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{annual_leave_days}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Weekly Working Days</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{weekly_working_days}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Weekend Days</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{weekend_days}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Chargeable Rate</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{chargeable_rate}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">Additional Terms &amp; Conditions</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{{additional_terms}}</td>
            </tr>
        </table>
    </div>

    <!-- Documents Required -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Documents Required</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; width: 33%;">☐ Passport Copy (in colour)</td>
                <td style="border: 1px solid #ddd; padding: 8px; width: 33%;">☐ Current Visa Copy</td>
                <td style="border: 1px solid #ddd; padding: 8px; width: 34%;">☐ Passport Size Photograph</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">☐ Attested University Degree</td>
                <td style="border: 1px solid #ddd; padding: 8px;">☐ Visa Cancellation (if any)</td>
                <td style="border: 1px solid #ddd; padding: 8px;">☐ Emirates ID Copy (if any)</td>
            </tr>
        </table>
    </div>

    <!-- Disclaimer -->
    <p style="font-size: 10px; color: #666; font-style: italic; margin-bottom: 20px;">Note: The Employment Visa application process for the Candidate is subject to government approvals and Auxilium will not be held responsible for any rejections by the relevant authorities.</p>

    <!-- Signatures Section -->
    <div style="margin-bottom: 20px;">
        <div style="background-color: #00A99D; color: white; padding: 8px 12px; font-weight: bold; font-size: 12px;">Signatures &amp; Company Stamp</div>
        <div style="display: flex; flex-wrap: wrap; margin-top: 15px;">
            <!-- Auxilium Signatory 1 -->
            <div style="width: 48%; border: 1px solid #ddd; padding: 15px; margin-right: 2%; margin-bottom: 15px;">
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">Signed by Lawrence Coward duly authorised</p>
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">for and on behalf of</p>
                <p style="font-size: 10px; color: #333; font-weight: bold; margin: 0 0 30px 0;">Auxilium Management Group FZE</p>
                <div style="border-bottom: 1px solid #333; margin-bottom: 5px;"></div>
                <p style="font-size: 9px; color: #666; margin: 0;">[Authorised Signatory]</p>
            </div>
            <!-- Auxilium Signatory 2 -->
            <div style="width: 48%; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px;">
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">Signed by Lawrence Coward duly authorised</p>
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">for and on behalf of</p>
                <p style="font-size: 10px; color: #333; font-weight: bold; margin: 0 0 30px 0;">Auxilium Management Group FZE</p>
                <div style="border-bottom: 1px solid #333; margin-bottom: 5px;"></div>
                <p style="font-size: 9px; color: #666; margin: 0;">[Authorised Signatory]</p>
            </div>
            <!-- Aventus Signatory 1 -->
            <div style="width: 48%; border: 1px solid #ddd; padding: 15px; margin-right: 2%;">
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">Signed by Richard White duly authorised</p>
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">for and on behalf of</p>
                <p style="font-size: 10px; color: #333; font-weight: bold; margin: 0 0 30px 0;">Aventus Talent Consultancy</p>
                <div style="border-bottom: 1px solid #333; margin-bottom: 5px;"></div>
                <p style="font-size: 9px; color: #666; margin: 0;">[Authorised Signatory]</p>
            </div>
            <!-- Aventus Signatory 2 -->
            <div style="width: 48%; border: 1px solid #ddd; padding: 15px;">
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">Signed by Richard White duly authorised</p>
                <p style="font-size: 10px; color: #333; margin: 0 0 5px 0;">for and on behalf of</p>
                <p style="font-size: 10px; color: #333; font-weight: bold; margin: 0 0 30px 0;">Aventus Talent Consultancy</p>
                <div style="border-bottom: 1px solid #333; margin-bottom: 5px;"></div>
                <p style="font-size: 9px; color: #666; margin: 0;">[Authorised Signatory]</p>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <p style="font-size: 10px; color: #666; text-align: center;">Note: Please sign and stamp above and submit this form for further process.</p>
</div>
"""


def run_migration():
    """Update COHF template in the database with Version 2 content"""

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # First, check if COHF template exists
        result = conn.execute(text("""
            SELECT id, name FROM templates
            WHERE template_type = 'cohf'
            ORDER BY created_at DESC
            LIMIT 1
        """))

        existing = result.fetchone()

        if existing:
            # Update existing COHF template
            template_id = existing[0]
            template_name = existing[1]

            conn.execute(text("""
                UPDATE templates
                SET content = :content,
                    description = 'COHF Version 2 - UAE Onboarding with Additional Payments, Client Declaration, Extended Deployment, Documents Required, and 4 Signature Blocks',
                    updated_at = NOW()
                WHERE id = :template_id
            """), {"content": COHF_TEMPLATE_V2.strip(), "template_id": template_id})

            conn.commit()
            print(f"Updated existing COHF template: {template_name} (ID: {template_id})")
        else:
            # Create new COHF template
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active, created_at)
                VALUES (
                    gen_random_uuid(),
                    'COHF - UAE Version 2',
                    'cohf',
                    'COHF Version 2 - UAE Onboarding with Additional Payments, Client Declaration, Extended Deployment, Documents Required, and 4 Signature Blocks',
                    :content,
                    'UAE',
                    true,
                    NOW()
                )
            """), {"content": COHF_TEMPLATE_V2.strip()})

            conn.commit()
            print("Created new COHF template: COHF - UAE Version 2")

        print("\nMigration completed successfully!")
        print("The COHF template now includes:")
        print("  - SCHEDULE 2: CONFIRMATION OF HIRE FORM header")
        print("  - Employee Candidate Information (10 fields)")
        print("  - Remuneration Information (12 fields including Leave Allowance, Medical Insurance Category, EOSB, Management Fee)")
        print("  - Additional Payments section with Commission/Bonus table")
        print("  - Client Declaration checkboxes (AML compliance)")
        print("  - Deployment Particulars (14 fields including Probation Period, Notice Period, Annual Leave Type, etc.)")
        print("  - Documents Required (6 checkboxes)")
        print("  - 4 Signature blocks (2 Auxilium, 2 Aventus)")


def rollback_migration():
    """This would restore the previous template (not implemented - backup before running)"""
    print("Rollback not implemented. Please restore from backup if needed.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Rolling back migration...")
        rollback_migration()
    else:
        print("Running migration to update COHF template to Version 2...")
        run_migration()
