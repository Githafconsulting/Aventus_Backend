"""
Migration: Add Quote Sheet form fields to quote_sheets table
Date: 2024-12-06
Description: Adds all the form fields for the Saudi Arabia Quote Sheet
             including Employee Info, Cash Benefits, Employee Cost, Family Cost,
             Government Charges, and Mobilization Cost fields.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def run_migration():
    """Add Quote Sheet form columns to quote_sheets table"""

    engine = create_engine(DATABASE_URL)

    # All new columns to add
    new_columns = [
        # Basic info
        ("issued_date", "VARCHAR"),

        # (A) Employee Contract Information
        ("employee_name", "VARCHAR"),
        ("role", "VARCHAR"),
        ("date_of_hiring", "VARCHAR"),
        ("nationality", "VARCHAR"),
        ("family_status", "VARCHAR"),
        ("num_children", "VARCHAR"),

        # (B) Employee Cash Benefits
        ("basic_salary", "FLOAT"),
        ("transport_allowance", "FLOAT"),
        ("housing_allowance", "FLOAT"),
        ("rate_per_day", "FLOAT"),
        ("working_days_month", "FLOAT"),
        ("aed_to_sar", "FLOAT"),
        ("gross_salary", "FLOAT"),

        # (C) Employee Cost
        ("vacation_one_time", "FLOAT"),
        ("vacation_annual", "FLOAT"),
        ("vacation_monthly", "FLOAT"),
        ("flight_one_time", "FLOAT"),
        ("flight_annual", "FLOAT"),
        ("flight_monthly", "FLOAT"),
        ("eosb_one_time", "FLOAT"),
        ("eosb_annual", "FLOAT"),
        ("eosb_monthly", "FLOAT"),
        ("gosi_one_time", "FLOAT"),
        ("gosi_annual", "FLOAT"),
        ("gosi_monthly", "FLOAT"),
        ("medical_one_time", "FLOAT"),
        ("medical_annual", "FLOAT"),
        ("medical_monthly", "FLOAT"),
        ("exit_reentry_one_time", "FLOAT"),
        ("exit_reentry_annual", "FLOAT"),
        ("exit_reentry_monthly", "FLOAT"),
        ("salary_transfer_one_time", "FLOAT"),
        ("salary_transfer_annual", "FLOAT"),
        ("salary_transfer_monthly", "FLOAT"),
        ("sick_leave_one_time", "FLOAT"),
        ("sick_leave_annual", "FLOAT"),
        ("sick_leave_monthly", "FLOAT"),
        ("employee_cost_one_time_total", "FLOAT"),
        ("employee_cost_annual_total", "FLOAT"),
        ("employee_cost_monthly_total", "FLOAT"),

        # (D) Family Cost
        ("family_medical_one_time", "FLOAT"),
        ("family_medical_annual", "FLOAT"),
        ("family_medical_monthly", "FLOAT"),
        ("family_flight_one_time", "FLOAT"),
        ("family_flight_annual", "FLOAT"),
        ("family_flight_monthly", "FLOAT"),
        ("family_exit_one_time", "FLOAT"),
        ("family_exit_annual", "FLOAT"),
        ("family_exit_monthly", "FLOAT"),
        ("family_joining_one_time", "FLOAT"),
        ("family_joining_annual", "FLOAT"),
        ("family_joining_monthly", "FLOAT"),
        ("family_visa_one_time", "FLOAT"),
        ("family_visa_annual", "FLOAT"),
        ("family_visa_monthly", "FLOAT"),
        ("family_levy_one_time", "FLOAT"),
        ("family_levy_annual", "FLOAT"),
        ("family_levy_monthly", "FLOAT"),
        ("family_cost_one_time_total", "FLOAT"),
        ("family_cost_annual_total", "FLOAT"),
        ("family_cost_monthly_total", "FLOAT"),

        # (E) Government Related Charges
        ("sce_one_time", "FLOAT"),
        ("sce_annual", "FLOAT"),
        ("sce_monthly", "FLOAT"),
        ("medical_test_one_time", "FLOAT"),
        ("medical_test_annual", "FLOAT"),
        ("medical_test_monthly", "FLOAT"),
        ("visa_cost_one_time", "FLOAT"),
        ("visa_cost_annual", "FLOAT"),
        ("visa_cost_monthly", "FLOAT"),
        ("ewakala_one_time", "FLOAT"),
        ("ewakala_annual", "FLOAT"),
        ("ewakala_monthly", "FLOAT"),
        ("chamber_mofa_one_time", "FLOAT"),
        ("chamber_mofa_annual", "FLOAT"),
        ("chamber_mofa_monthly", "FLOAT"),
        ("iqama_one_time", "FLOAT"),
        ("iqama_annual", "FLOAT"),
        ("iqama_monthly", "FLOAT"),
        ("saudi_admin_one_time", "FLOAT"),
        ("saudi_admin_annual", "FLOAT"),
        ("saudi_admin_monthly", "FLOAT"),
        ("ajeer_one_time", "FLOAT"),
        ("ajeer_annual", "FLOAT"),
        ("ajeer_monthly", "FLOAT"),
        ("govt_cost_one_time_total", "FLOAT"),
        ("govt_cost_annual_total", "FLOAT"),
        ("govt_cost_monthly_total", "FLOAT"),

        # (F) Mobilization Cost
        ("visa_processing_one_time", "FLOAT"),
        ("visa_processing_annual", "FLOAT"),
        ("visa_processing_monthly", "FLOAT"),
        ("recruitment_one_time", "FLOAT"),
        ("recruitment_annual", "FLOAT"),
        ("recruitment_monthly", "FLOAT"),
        ("joining_ticket_one_time", "FLOAT"),
        ("joining_ticket_annual", "FLOAT"),
        ("joining_ticket_monthly", "FLOAT"),
        ("relocation_one_time", "FLOAT"),
        ("relocation_annual", "FLOAT"),
        ("relocation_monthly", "FLOAT"),
        ("other_cost_one_time", "FLOAT"),
        ("other_cost_annual", "FLOAT"),
        ("other_cost_monthly", "FLOAT"),
        ("mobilization_one_time_total", "FLOAT"),
        ("mobilization_annual_total", "FLOAT"),
        ("mobilization_monthly_total", "FLOAT"),

        # Grand Totals
        ("total_one_time", "FLOAT"),
        ("total_annual", "FLOAT"),
        ("total_monthly", "FLOAT"),
        ("fnrco_service_charge", "FLOAT"),
        ("total_invoice_amount", "FLOAT"),

        # Remarks
        ("remarks_data", "JSONB"),

        # Timestamps
        ("submitted_at", "TIMESTAMP"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in new_columns:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'quote_sheets'
                    AND column_name = '{column_name}'
                """))

                if result.fetchone() is None:
                    # Column doesn't exist, add it
                    conn.execute(text(f"""
                        ALTER TABLE quote_sheets
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    print(f"Added column: {column_name}")
                else:
                    print(f"Column already exists: {column_name}")

            except Exception as e:
                print(f"Error adding column {column_name}: {e}")

        # Also update the status enum to include 'submitted'
        try:
            conn.execute(text("""
                ALTER TYPE quotesheetstatus ADD VALUE IF NOT EXISTS 'submitted'
            """))
            print("Added 'submitted' to QuoteSheetStatus enum")
        except Exception as e:
            print(f"Note: {e}")

        conn.commit()
        print("\nMigration completed successfully!")


if __name__ == "__main__":
    print("Running migration to add Quote Sheet form fields...")
    run_migration()
