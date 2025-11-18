"""
Add workflow, timesheet, invoice, and payment terms fields to clients table
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found in environment variables")

engine = create_engine(database_url)


def upgrade():
    """Add new fields to clients table"""
    with engine.connect() as conn:
        # Workflow Configuration
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS work_order_applicable BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS proposal_applicable BOOLEAN DEFAULT FALSE
        """))

        # Timesheet Configuration
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS timesheet_required BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS timesheet_approver_name VARCHAR
        """))

        # Payment Terms
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS po_required BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS po_number VARCHAR,
            ADD COLUMN IF NOT EXISTS contractor_pay_frequency VARCHAR,
            ADD COLUMN IF NOT EXISTS client_invoice_frequency VARCHAR,
            ADD COLUMN IF NOT EXISTS client_payment_terms VARCHAR,
            ADD COLUMN IF NOT EXISTS invoicing_preferences VARCHAR,
            ADD COLUMN IF NOT EXISTS invoice_instructions TEXT
        """))

        # Supporting Documents
        conn.execute(text("""
            ALTER TABLE clients
            ADD COLUMN IF NOT EXISTS supporting_documents_required JSONB DEFAULT '[]'::jsonb
        """))

        conn.commit()
        print("✅ Migration completed: Added workflow and invoice fields to clients table")


def downgrade():
    """Remove new fields from clients table"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE clients
            DROP COLUMN IF EXISTS work_order_applicable,
            DROP COLUMN IF EXISTS proposal_applicable,
            DROP COLUMN IF EXISTS timesheet_required,
            DROP COLUMN IF EXISTS timesheet_approver_name,
            DROP COLUMN IF EXISTS po_required,
            DROP COLUMN IF EXISTS po_number,
            DROP COLUMN IF EXISTS contractor_pay_frequency,
            DROP COLUMN IF EXISTS client_invoice_frequency,
            DROP COLUMN IF EXISTS client_payment_terms,
            DROP COLUMN IF EXISTS invoicing_preferences,
            DROP COLUMN IF EXISTS invoice_instructions,
            DROP COLUMN IF EXISTS supporting_documents_required
        """))
        conn.commit()
        print("✅ Migration rolled back: Removed workflow and invoice fields from clients table")


if __name__ == "__main__":
    print("Running migration: add_client_workflow_and_invoice_fields")
    upgrade()
