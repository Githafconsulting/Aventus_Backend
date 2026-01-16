"""Add dual signature columns to contractors

Revision ID: 38226a471bea
Revises:
Create Date: 2026-01-16 14:49:53.121989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '38226a471bea'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema - Add dual signature columns."""
    # Add dual signature columns to contractors table
    op.add_column('contractors', sa.Column('quote_sheet_third_party_signature', sa.Text(), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_third_party_name', sa.String(), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_third_party_signed_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_aventus_signature_type', sa.String(), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_aventus_signature_data', sa.Text(), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_aventus_signed_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('contractors', sa.Column('quote_sheet_aventus_signed_by', sa.String(), nullable=True))
    op.add_column('contractors', sa.Column('cohf_aventus_signature_type', sa.String(), nullable=True))
    op.add_column('contractors', sa.Column('cohf_aventus_signature_data', sa.Text(), nullable=True))
    op.add_column('contractors', sa.Column('cohf_aventus_signed_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('contractors', sa.Column('cohf_aventus_signed_by', sa.String(), nullable=True))

    # Add foreign keys for signed_by columns
    op.create_foreign_key('fk_contractors_cohf_aventus_signed_by', 'contractors', 'users', ['cohf_aventus_signed_by'], ['id'])
    op.create_foreign_key('fk_contractors_quote_sheet_aventus_signed_by', 'contractors', 'users', ['quote_sheet_aventus_signed_by'], ['id'])

    # Add dual signature columns to work_orders table
    op.add_column('work_orders', sa.Column('aventus_signature_type', sa.String(), nullable=True))
    op.add_column('work_orders', sa.Column('aventus_signature_data', sa.String(), nullable=True))
    op.add_column('work_orders', sa.Column('aventus_signed_date', sa.DateTime(), nullable=True))
    op.add_column('work_orders', sa.Column('aventus_signed_by', sa.String(), nullable=True))

    # Add foreign key for work_orders signed_by
    op.create_foreign_key('fk_work_orders_aventus_signed_by', 'work_orders', 'users', ['aventus_signed_by'], ['id'])


def downgrade() -> None:
    """Downgrade database schema - Remove dual signature columns."""
    # Drop foreign keys
    op.drop_constraint('fk_work_orders_aventus_signed_by', 'work_orders', type_='foreignkey')
    op.drop_constraint('fk_contractors_quote_sheet_aventus_signed_by', 'contractors', type_='foreignkey')
    op.drop_constraint('fk_contractors_cohf_aventus_signed_by', 'contractors', type_='foreignkey')

    # Drop work_orders columns
    op.drop_column('work_orders', 'aventus_signed_by')
    op.drop_column('work_orders', 'aventus_signed_date')
    op.drop_column('work_orders', 'aventus_signature_data')
    op.drop_column('work_orders', 'aventus_signature_type')

    # Drop contractors columns
    op.drop_column('contractors', 'cohf_aventus_signed_by')
    op.drop_column('contractors', 'cohf_aventus_signed_date')
    op.drop_column('contractors', 'cohf_aventus_signature_data')
    op.drop_column('contractors', 'cohf_aventus_signature_type')
    op.drop_column('contractors', 'quote_sheet_aventus_signed_by')
    op.drop_column('contractors', 'quote_sheet_aventus_signed_date')
    op.drop_column('contractors', 'quote_sheet_aventus_signature_data')
    op.drop_column('contractors', 'quote_sheet_aventus_signature_type')
    op.drop_column('contractors', 'quote_sheet_third_party_signed_date')
    op.drop_column('contractors', 'quote_sheet_third_party_name')
    op.drop_column('contractors', 'quote_sheet_third_party_signature')
