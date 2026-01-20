"""Add payslips and invoices tables

Revision ID: 9a7b2c3d4e5f
Revises: 38226a471bea
Create Date: 2026-01-18 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a7b2c3d4e5f'
down_revision: Union[str, None] = '38226a471bea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create payslips, invoices, and invoice_payments tables."""

    # Create payslips table
    op.create_table(
        'payslips',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('payroll_id', sa.Integer(), sa.ForeignKey('payrolls.id'), nullable=False),
        sa.Column('contractor_id', sa.String(), sa.ForeignKey('contractors.id'), nullable=False),
        sa.Column('document_number', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('pdf_storage_key', sa.String(), nullable=True),
        sa.Column('pdf_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('generated', 'sent', 'viewed', 'acknowledged', name='payslipstatus'), default='generated'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('access_token', sa.String(), unique=True, nullable=True, index=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('payroll_id', sa.Integer(), sa.ForeignKey('payrolls.id'), unique=True, nullable=False),
        sa.Column('client_id', sa.String(), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('contractor_id', sa.String(), sa.ForeignKey('contractors.id'), nullable=False),
        sa.Column('invoice_number', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('vat_rate', sa.Float(), default=0.05),
        sa.Column('vat_amount', sa.Float(), default=0),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('amount_paid', sa.Float(), default=0),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('pdf_storage_key', sa.String(), nullable=True),
        sa.Column('pdf_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'sent', 'viewed', 'partially_paid', 'paid', 'overdue', name='invoicestatus'), default='draft'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('access_token', sa.String(), unique=True, nullable=True, index=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create invoice_payments table
    op.create_table(
        'invoice_payments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('reference_number', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop payslips, invoices, and invoice_payments tables."""
    op.drop_table('invoice_payments')
    op.drop_table('invoices')
    op.drop_table('payslips')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS invoicestatus')
    op.execute('DROP TYPE IF EXISTS payslipstatus')
