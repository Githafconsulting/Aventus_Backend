"""Phase 2: Consolidate and drop contractor legacy dual-write columns.

Copies data from legacy columns to canonical columns (where canonical is NULL),
then drops the legacy columns. Hybrid properties on the model provide backward
compatibility for reads.

Revision ID: phase2_legacy_cols
Revises: b3c4d5e6f7a8
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "phase2_legacy_cols"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None

# Mapping: (legacy_column, canonical_column)
LEGACY_TO_CANONICAL = [
    ("home_address", "address_line1"),
    ("registered_address", "mgmt_address_line1"),
    ("management_address_line2", "mgmt_address_line2"),
    ("management_address_line3", "mgmt_address_line3"),
    ("bank_name", "mgmt_bank_name"),
    ("account_number", "mgmt_account_number"),
    ("iban_number", "mgmt_iban_number"),
    ("invoice_email", "invoice_email1"),
    ("client_contact", "client_contact1"),
    ("client_charge_rate", "charge_rate_month"),
    ("candidate_pay_rate", "gross_salary"),
    ("candidate_basic_salary", "gross_salary"),
    ("contractor_total_fixed_costs", "total_contractor_fixed_costs"),
    ("laptop_provider", "laptop_provided_by"),
    ("other_notes", "any_notes"),
]

# Columns to drop (some map to the same canonical, so deduplicate)
COLUMNS_TO_DROP = [
    "home_address",
    "registered_address",
    "management_address_line2",
    "management_address_line3",
    "bank_name",
    "account_number",
    "iban_number",
    "invoice_email",
    "client_contact",
    "client_charge_rate",
    "candidate_pay_rate",
    "candidate_basic_salary",
    "contractor_costs",
    "contractor_total_fixed_costs",
    "laptop_provider",
    "other_notes",
]


def upgrade() -> None:
    # Step 1: Consolidate data — copy legacy→canonical where canonical is null
    conn = op.get_bind()
    for legacy, canonical in LEGACY_TO_CANONICAL:
        conn.execute(
            sa.text(
                f'UPDATE contractors SET "{canonical}" = "{legacy}" '
                f'WHERE "{canonical}" IS NULL AND "{legacy}" IS NOT NULL'
            )
        )

    # Step 2: Drop legacy columns
    for col in COLUMNS_TO_DROP:
        op.drop_column("contractors", col)


def downgrade() -> None:
    # Re-create the legacy columns (data cannot be fully restored)
    op.add_column("contractors", sa.Column("home_address", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("registered_address", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("management_address_line2", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("management_address_line3", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("bank_name", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("account_number", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("iban_number", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("invoice_email", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("client_contact", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("client_charge_rate", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("candidate_pay_rate", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("candidate_basic_salary", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("contractor_costs", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("contractor_total_fixed_costs", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("laptop_provider", sa.String(), nullable=True))
    op.add_column("contractors", sa.Column("other_notes", sa.Text(), nullable=True))

    # Copy canonical→legacy for backward compat
    conn = op.get_bind()
    for legacy, canonical in LEGACY_TO_CANONICAL:
        conn.execute(
            sa.text(
                f'UPDATE contractors SET "{legacy}" = "{canonical}" '
                f'WHERE "{legacy}" IS NULL AND "{canonical}" IS NOT NULL'
            )
        )
