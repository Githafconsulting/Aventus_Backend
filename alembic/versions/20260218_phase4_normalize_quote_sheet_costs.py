"""Phase 4: Normalize QuoteSheet tripled cost columns into quote_sheet_cost_lines.

Moves 81 individual cost columns (27 categories x 3 amounts) into a
normalized child table. Section totals and grand totals remain on the
parent for query performance.

Revision ID: phase4_qs_costs
Revises: phase3_json_to_tables
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "phase4_qs_costs"
down_revision = "phase3_json_to_tables"
branch_labels = None
depends_on = None

# Category mapping: (column_prefix, section, label, sort_order)
CATEGORIES = [
    # Employee
    ("vacation", "employee", "Employee Vacation Cost", 0),
    ("flight", "employee", "Flight Cost", 1),
    ("eosb", "employee", "EOSB - End of Service Benefits", 2),
    ("gosi", "employee", "GOSI", 3),
    ("medical", "employee", "Medical Insurance Cost", 4),
    ("exit_reentry", "employee", "Exit Re-Entry Cost", 5),
    ("salary_transfer", "employee", "Salary Transfer Cost", 6),
    ("sick_leave", "employee", "Sick Leave Cost", 7),
    # Family
    ("family_medical", "family", "Family Medical Cost", 0),
    ("family_flight", "family", "Family Flight Cost", 1),
    ("family_exit", "family", "Family Exit Cost", 2),
    ("family_joining", "family", "Family Joining Cost", 3),
    ("family_visa", "family", "Family Visa Cost", 4),
    ("family_levy", "family", "Family Levy", 5),
    # Government
    ("sce", "government", "SCE", 0),
    ("medical_test", "government", "Medical Test Cost", 1),
    ("visa_cost", "government", "Visa Cost", 2),
    ("ewakala", "government", "Ewakala", 3),
    ("chamber_mofa", "government", "Chamber / MOFA", 4),
    ("iqama", "government", "Iqama Cost", 5),
    ("saudi_admin", "government", "Saudi Admin Cost", 6),
    ("ajeer", "government", "Ajeer Cost", 7),
    # Mobilization
    ("visa_processing", "mobilization", "Visa Processing", 0),
    ("recruitment", "mobilization", "Recruitment Cost", 1),
    ("joining_ticket", "mobilization", "Joining Ticket", 2),
    ("relocation", "mobilization", "Relocation Cost", 3),
    ("other_cost", "mobilization", "Other Cost", 4),
]


def upgrade() -> None:
    # Create cost lines table (skip if already created by Base.metadata.create_all)
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    if "quote_sheet_cost_lines" not in set(inspector.get_table_names()):
        op.create_table(
            "quote_sheet_cost_lines",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("quote_sheet_id", sa.String(), sa.ForeignKey("quote_sheets.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("section", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("one_time", sa.Float(), server_default="0"),
            sa.Column("annual", sa.Float(), server_default="0"),
            sa.Column("monthly", sa.Float(), server_default="0"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("quote_sheet_id", "category", name="uq_qs_cost_line_category"),
        )

    # Migrate data from flat columns to cost lines
    conn = op.get_bind()
    for prefix, section, label, sort_order in CATEGORIES:
        conn.execute(sa.text(f"""
            INSERT INTO quote_sheet_cost_lines (quote_sheet_id, section, category, label, one_time, annual, monthly, sort_order)
            SELECT id, :section, :category, :label,
                   COALESCE("{prefix}_one_time", 0),
                   COALESCE("{prefix}_annual", 0),
                   COALESCE("{prefix}_monthly", 0),
                   :sort_order
            FROM quote_sheets
            WHERE "{prefix}_one_time" IS NOT NULL
               OR "{prefix}_annual" IS NOT NULL
               OR "{prefix}_monthly" IS NOT NULL
        """), {
            "section": section,
            "category": prefix,
            "label": label,
            "sort_order": sort_order,
        })

    # Drop individual cost columns (keep section totals and grand totals)
    columns_to_drop = []
    for prefix, _, _, _ in CATEGORIES:
        columns_to_drop.extend([
            f"{prefix}_one_time",
            f"{prefix}_annual",
            f"{prefix}_monthly",
        ])

    for col in columns_to_drop:
        op.drop_column("quote_sheets", col)


def downgrade() -> None:
    # Re-create individual cost columns
    for prefix, _, _, _ in CATEGORIES:
        op.add_column("quote_sheets", sa.Column(f"{prefix}_one_time", sa.Float(), nullable=True))
        op.add_column("quote_sheets", sa.Column(f"{prefix}_annual", sa.Float(), nullable=True))
        op.add_column("quote_sheets", sa.Column(f"{prefix}_monthly", sa.Float(), nullable=True))

    # Migrate data back from cost lines to flat columns
    conn = op.get_bind()
    for prefix, _, _, _ in CATEGORIES:
        conn.execute(sa.text(f"""
            UPDATE quote_sheets SET
                "{prefix}_one_time" = cl.one_time,
                "{prefix}_annual" = cl.annual,
                "{prefix}_monthly" = cl.monthly
            FROM quote_sheet_cost_lines cl
            WHERE cl.quote_sheet_id = quote_sheets.id
              AND cl.category = :category
        """), {"category": prefix})

    # Drop cost lines table
    op.drop_table("quote_sheet_cost_lines")
