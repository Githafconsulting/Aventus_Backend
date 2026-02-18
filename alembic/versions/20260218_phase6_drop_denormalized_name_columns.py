"""Phase 6: Drop denormalized name columns.

Removes redundant _name columns across 8 tables now that models resolve
names from FK relationships via @property. Also removes Payroll.country
(derivable from contractor).

Revision ID: phase6_drop_names
Revises: phase4_qs_costs
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "phase6_drop_names"
down_revision = "phase4_qs_costs"
branch_labels = None
depends_on = None

# Columns to drop: (table, column, type, nullable, extra_kwargs)
COLUMNS_TO_DROP = [
    # contractors
    ("contractors", "client_name", sa.String(), True, {}),
    ("contractors", "consultant_name", sa.String(), True, {}),
    # payrolls
    ("payrolls", "client_name", sa.String(), True, {}),
    ("payrolls", "third_party_name", sa.String(), True, {}),
    ("payrolls", "country", sa.String(), True, {}),
    # payroll_batches
    ("payroll_batches", "client_name", sa.String(), False, {}),
    ("payroll_batches", "third_party_name", sa.String(), True, {}),
    # contracts
    ("contracts", "consultant_name", sa.String(), True, {}),
    ("contracts", "client_name", sa.String(), True, {}),
    ("contracts", "client_address", sa.Text(), True, {}),
    ("contracts", "job_title", sa.String(), True, {}),
    # work_orders
    ("work_orders", "contractor_name", sa.String(), True, {}),
    ("work_orders", "client_name", sa.String(), True, {}),
    ("work_orders", "project_name", sa.String(), True, {}),
    ("work_orders", "business_type", sa.String(), True, {}),
    ("work_orders", "umbrella_company_name", sa.String(), True, {}),
    # quote_sheets (third_party_company_name kept: email-domain fallback when no FK)
    ("quote_sheets", "contractor_name", sa.String(), True, {}),
    ("quote_sheets", "employee_name", sa.String(), True, {}),
    # proposals
    ("proposals", "client_company_name", sa.String(), True, {}),
    # client_invoice_line_items
    ("client_invoice_line_items", "contractor_name", sa.String(), True, {}),
]


def upgrade() -> None:
    for table, column, _, _, _ in COLUMNS_TO_DROP:
        op.drop_column(table, column)


def downgrade() -> None:
    # Re-create all dropped columns
    for table, column, col_type, nullable, _ in COLUMNS_TO_DROP:
        op.add_column(table, sa.Column(column, col_type, nullable=nullable))

    # Repopulate from FK relationships
    conn = op.get_bind()

    # contractors.client_name ← clients.company_name
    conn.execute(sa.text("""
        UPDATE contractors SET client_name = c.company_name
        FROM clients c WHERE contractors.client_id = c.id
    """))

    # contractors.consultant_name ← users.name
    conn.execute(sa.text("""
        UPDATE contractors SET consultant_name = u.name
        FROM users u WHERE contractors.consultant_id = u.id
    """))

    # payrolls.client_name ← contractors → clients
    conn.execute(sa.text("""
        UPDATE payrolls SET client_name = cl.company_name
        FROM contractors c
        JOIN clients cl ON c.client_id = cl.id
        WHERE payrolls.contractor_id = c.id
    """))

    # payrolls.third_party_name ← contractors → third_parties
    conn.execute(sa.text("""
        UPDATE payrolls SET third_party_name = tp.company_name
        FROM contractors c
        JOIN third_parties tp ON c.third_party_id = tp.id
        WHERE payrolls.contractor_id = c.id
    """))

    # payrolls.country ← contractors.onboarding_route (used for VAT route display)
    conn.execute(sa.text("""
        UPDATE payrolls SET country = c.onboarding_route
        FROM contractors c WHERE payrolls.contractor_id = c.id
    """))

    # payroll_batches.client_name ← clients.company_name
    conn.execute(sa.text("""
        UPDATE payroll_batches SET client_name = COALESCE(c.company_name, 'Unknown')
        FROM clients c WHERE payroll_batches.client_id = c.id
    """))

    # payroll_batches.third_party_name ← third_parties.company_name
    conn.execute(sa.text("""
        UPDATE payroll_batches SET third_party_name = tp.company_name
        FROM third_parties tp WHERE payroll_batches.third_party_id = tp.id
    """))

    # contracts.consultant_name ← contractors first+surname
    conn.execute(sa.text("""
        UPDATE contracts SET consultant_name = c.first_name || ' ' || c.surname
        FROM contractors c WHERE contracts.contractor_id = c.id
    """))

    # contracts.client_name ← contractors → clients
    conn.execute(sa.text("""
        UPDATE contracts SET client_name = cl.company_name
        FROM contractors c
        JOIN clients cl ON c.client_id = cl.id
        WHERE contracts.contractor_id = c.id
    """))

    # contracts.job_title ← contractors.role
    conn.execute(sa.text("""
        UPDATE contracts SET job_title = c.role
        FROM contractors c WHERE contracts.contractor_id = c.id
    """))

    # contracts.client_address ← clients address fields
    conn.execute(sa.text("""
        UPDATE contracts SET client_address = CONCAT_WS(', ',
            NULLIF(cl.address_line1, ''), NULLIF(cl.address_line2, ''),
            NULLIF(cl.address_line3, ''), NULLIF(cl.address_line4, ''),
            NULLIF(cl.country, ''))
        FROM contractors c
        JOIN clients cl ON c.client_id = cl.id
        WHERE contracts.contractor_id = c.id
    """))

    # work_orders.contractor_name ← contractors first+surname
    conn.execute(sa.text("""
        UPDATE work_orders SET contractor_name = c.first_name || ' ' || c.surname
        FROM contractors c WHERE work_orders.contractor_id = c.id
    """))

    # work_orders.client_name ← contractors → clients
    conn.execute(sa.text("""
        UPDATE work_orders SET client_name = cl.company_name
        FROM contractors c
        JOIN clients cl ON c.client_id = cl.id
        WHERE work_orders.contractor_id = c.id
    """))

    # work_orders.project_name ← contractors.project_name
    conn.execute(sa.text("""
        UPDATE work_orders SET project_name = c.project_name
        FROM contractors c WHERE work_orders.contractor_id = c.id
    """))

    # work_orders.business_type ← contractors.business_type
    conn.execute(sa.text("""
        UPDATE work_orders SET business_type = c.business_type
        FROM contractors c WHERE work_orders.contractor_id = c.id
    """))

    # work_orders.umbrella_company_name ← contractors.umbrella_company_name
    conn.execute(sa.text("""
        UPDATE work_orders SET umbrella_company_name = c.umbrella_company_name
        FROM contractors c WHERE work_orders.contractor_id = c.id
    """))

    # quote_sheets.contractor_name ← contractors first+surname
    conn.execute(sa.text("""
        UPDATE quote_sheets SET contractor_name = c.first_name || ' ' || c.surname
        FROM contractors c WHERE quote_sheets.contractor_id = c.id
    """))

    # quote_sheets.employee_name ← contractors first+surname
    conn.execute(sa.text("""
        UPDATE quote_sheets SET employee_name = c.first_name || ' ' || c.surname
        FROM contractors c WHERE quote_sheets.contractor_id = c.id
    """))

    # proposals.client_company_name ← clients.company_name
    conn.execute(sa.text("""
        UPDATE proposals SET client_company_name = c.company_name
        FROM clients c WHERE proposals.client_id = c.id
    """))

    # client_invoice_line_items.contractor_name ← contractors first+surname
    conn.execute(sa.text("""
        UPDATE client_invoice_line_items SET contractor_name = c.first_name || ' ' || c.surname
        FROM contractors c WHERE client_invoice_line_items.contractor_id = c.id
    """))
