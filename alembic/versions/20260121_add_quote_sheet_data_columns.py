"""Add quote_sheet_data and quote_sheet_status columns to contractors

Revision ID: add_quote_sheet_data
Revises: 20260118_0001_add_payslips_invoices_tables
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_quote_sheet_data'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add quote_sheet_data and quote_sheet_status columns to contractors table."""
    op.add_column('contractors', sa.Column('quote_sheet_data', sa.JSON(), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_status', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove quote_sheet_data and quote_sheet_status columns from contractors table."""
    op.drop_column('contractors', 'quote_sheet_status')
    op.drop_column('contractors', 'quote_sheet_data')
