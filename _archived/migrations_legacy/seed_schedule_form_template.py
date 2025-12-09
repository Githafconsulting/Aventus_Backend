"""
Migration: Seed Schedule Form template
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


# Schedule Form Template
SCHEDULE_FORM_TEMPLATE = """
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #FF6B00; margin-bottom: 10px;">CONTRACTOR SCHEDULE FORM</h1>
    <p style="font-size: 14px; color: #666;">Work Schedule & Attendance Record</p>
    <p style="font-size: 12px; color: #999;">Period: {{PERIOD}}</p>
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
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Role/Position</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ROLE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Client</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{CLIENT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Project</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PROJECT_NAME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Location</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LOCATION}}</td>
    </tr>
</table>

<!-- Schedule Period -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">SCHEDULE PERIOD</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 30%; font-weight: bold;">From Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{FROM_DATE}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">To Date</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{TO_DATE}}</td>
    </tr>
</table>

<!-- Work Schedule -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">STANDARD WORK SCHEDULE</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 30%; font-weight: bold;">Working Days</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{WORKING_DAYS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Start Time</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{START_TIME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">End Time</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{END_TIME}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Break Duration</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{BREAK_DURATION}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Total Hours Per Day</td>
        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #FF6B00;">{{HOURS_PER_DAY}}</td>
    </tr>
</table>

<!-- Weekly Schedule Breakdown -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">WEEKLY SCHEDULE</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #1F2937; color: white;">
            <th style="padding: 12px; text-align: left; border: 1px solid #374151;">Day</th>
            <th style="padding: 12px; text-align: center; border: 1px solid #374151;">Start Time</th>
            <th style="padding: 12px; text-align: center; border: 1px solid #374151;">End Time</th>
            <th style="padding: 12px; text-align: center; border: 1px solid #374151;">Hours</th>
            <th style="padding: 12px; text-align: center; border: 1px solid #374151;">Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Sunday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SUNDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SUNDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SUNDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SUNDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Monday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{MONDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{MONDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{MONDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{MONDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Tuesday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{TUESDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{TUESDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{TUESDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{TUESDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Wednesday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{WEDNESDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{WEDNESDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{WEDNESDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{WEDNESDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Thursday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{THURSDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{THURSDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{THURSDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{THURSDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Friday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{FRIDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{FRIDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{FRIDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{FRIDAY_STATUS}}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Saturday</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SATURDAY_START}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SATURDAY_END}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SATURDAY_HOURS}}</td>
            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{{SATURDAY_STATUS}}</td>
        </tr>
        <tr style="background-color: #FEF3C7;">
            <td style="padding: 12px; border: 2px solid #F59E0B; font-weight: bold;" colspan="3">TOTAL HOURS (WEEK)</td>
            <td style="padding: 12px; border: 2px solid #F59E0B; text-align: center; font-weight: bold; font-size: 16px; color: #FF6B00;" colspan="2">{{TOTAL_WEEKLY_HOURS}}</td>
        </tr>
    </tbody>
</table>

<!-- Leave & Absences -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">LEAVE & ABSENCES</h2>

<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; width: 30%; font-weight: bold;">Annual Leave Days</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{ANNUAL_LEAVE_DAYS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Sick Leave Days</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{SICK_LEAVE_DAYS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Public Holidays</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{PUBLIC_HOLIDAYS}}</td>
    </tr>
    <tr>
        <td style="padding: 10px; border: 1px solid #ddd; background-color: #F9FAFB; font-weight: bold;">Leave Policy</td>
        <td style="padding: 10px; border: 1px solid #ddd;">{{LEAVE_POLICY}}</td>
    </tr>
</table>

<!-- Special Instructions -->
<h2 style="background-color: #F3F4F6; padding: 12px; border-left: 4px solid #FF6B00; margin-top: 20px;">SPECIAL INSTRUCTIONS</h2>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB; min-height: 100px;">
    <p style="margin: 0; white-space: pre-wrap;">{{SPECIAL_INSTRUCTIONS}}</p>
</div>

<!-- Additional Notes -->
<h3 style="color: #666; margin-top: 25px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB;">Additional Notes</h3>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #F9FAFB; min-height: 80px;">
    <p style="margin: 0; white-space: pre-wrap;">{{ADDITIONAL_NOTES}}</p>
</div>

<!-- Important Information -->
<div style="margin-top: 30px; padding: 15px; background-color: #DBEAFE; border-left: 4px solid #3B82F6; border-radius: 4px;">
    <p style="margin: 0; font-size: 12px; color: #1E40AF;">
        <strong>Note:</strong> This schedule is subject to change based on project requirements and client needs.
        Any changes to the schedule must be communicated at least 24 hours in advance unless in case of emergency.
        Overtime work requires prior approval from the project manager.
    </p>
</div>

<!-- Approval Section -->
<div style="margin-top: 40px; padding: 20px; background-color: #F0FDF4; border: 2px solid #10B981; border-radius: 8px;">
    <h3 style="margin: 0 0 15px 0; color: #047857;">APPROVAL</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 15px; width: 33%; vertical-align: top;">
                <p style="margin: 0; font-weight: bold;">Contractor:</p>
                <p style="margin: 10px 0 0 0;">_______________________</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Signature & Date</p>
            </td>
            <td style="padding: 15px; width: 33%; vertical-align: top;">
                <p style="margin: 0; font-weight: bold;">Project Manager:</p>
                <p style="margin: 10px 0 0 0;">_______________________</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Signature & Date</p>
            </td>
            <td style="padding: 15px; width: 33%; vertical-align: top;">
                <p style="margin: 0; font-weight: bold;">Client Approval:</p>
                <p style="margin: 10px 0 0 0;">_______________________</p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Signature & Date</p>
            </td>
        </tr>
    </table>
</div>

<div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #E5E7EB;">
    <p style="text-align: center; color: #999; font-size: 12px;">
        <strong>Aventus Resources</strong><br/>
        Contractor Schedule Form - Generated on {{CURRENT_DATE}}
    </p>
</div>
"""


def upgrade():
    """Seed schedule form template"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        try:
            logger.info("Seeding Schedule Form template...")

            # Schedule Form Template
            template_id = str(uuid.uuid4())
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active)
                VALUES (:id, :name, :template_type, :description, :content, :country, :is_active)
            """), {
                "id": template_id,
                "name": "Contractor Schedule Form",
                "template_type": "schedule_form",
                "description": "Work schedule and attendance tracking form with weekly breakdown, leave allocation, and approval section",
                "content": SCHEDULE_FORM_TEMPLATE,
                "country": None,
                "is_active": True
            })
            logger.info(f"✓ Created template: Contractor Schedule Form")

            conn.commit()
            logger.info(f"✓ Successfully seeded Schedule Form template")

        except Exception as e:
            logger.error(f"✗ Error during template seeding: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("Running migration: Seed Schedule Form template")
    upgrade()
    print("Migration completed successfully!")
