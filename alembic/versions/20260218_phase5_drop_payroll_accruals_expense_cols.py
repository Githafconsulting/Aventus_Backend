"""Phase 5: Drop Payroll.accruals JSON and Expense.year/month_number columns.

Payroll.accruals duplicates the individual accrual_* columns.
Expense.year and month_number are derivable from date via hybrid_property.

Revision ID: phase5_cleanup
Revises: phase2_legacy_cols
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "phase5_cleanup"
down_revision = "phase2_legacy_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop Payroll.accruals JSON column (data duplicated in individual accrual_* columns)
    op.drop_column("payrolls", "accruals")

    # Drop Expense.year and month_number (now derived from date via hybrid_property)
    op.drop_column("expenses", "year")
    op.drop_column("expenses", "month_number")


def downgrade() -> None:
    # Re-create Expense columns
    op.add_column("expenses", sa.Column("month_number", sa.Integer(), nullable=True))
    op.add_column("expenses", sa.Column("year", sa.Integer(), nullable=True))

    # Populate from date column
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE expenses SET year = EXTRACT(YEAR FROM date)::integer, "
            "month_number = EXTRACT(MONTH FROM date)::integer "
            "WHERE date IS NOT NULL"
        )
    )

    # Set NOT NULL after populating
    op.alter_column("expenses", "year", nullable=False)
    op.alter_column("expenses", "month_number", nullable=False)

    # Re-create Payroll.accruals JSON column
    op.add_column("payrolls", sa.Column("accruals", sa.JSON(), nullable=True))
