"""add payroll batch and client invoice tables

Revision ID: a1b2c3d4e5f6
Revises: 20260121_add_quote_sheet_data_columns
Create Date: 2026-02-13
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = None  # Set to latest revision ID if chaining migrations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Add new enum values to payrollstatus ---
    # PostgreSQL requires explicit enum value additions
    op.execute("ALTER TYPE payrollstatus ADD VALUE IF NOT EXISTS 'approved_adjusted'")
    op.execute("ALTER TYPE payrollstatus ADD VALUE IF NOT EXISTS 'mismatch_3rd_party'")

    # --- Create payroll_batches table ---
    op.create_table(
        'payroll_batches',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('client_name', sa.String(), nullable=False),
        sa.Column('onboarding_route', sa.String(), nullable=False),
        sa.Column('route_label', sa.String(), nullable=True),
        sa.Column('third_party_id', sa.String(), sa.ForeignKey('third_parties.id'), nullable=True),
        sa.Column('third_party_name', sa.String(), nullable=True),
        sa.Column('contractor_count', sa.Integer(), server_default='0'),
        sa.Column('total_net_salary', sa.Float(), server_default='0'),
        sa.Column('total_payable', sa.Float(), server_default='0'),
        sa.Column('currency', sa.String(10), server_default='AED'),
        sa.Column('status', sa.Enum(
            'awaiting_approval', 'partially_approved', 'submit_for_invoice',
            'invoice_requested', 'invoice_received', 'ready_for_payment',
            'invoice_update_requested', 'paid', 'payslips_generated',
            name='batchstatus'
        ), server_default='awaiting_approval', nullable=False),
        sa.Column('tp_invoice_url', sa.String(), nullable=True),
        sa.Column('tp_invoice_uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('tp_invoice_upload_token', sa.String(), nullable=True),
        sa.Column('tp_invoice_token_expiry', sa.DateTime(), nullable=True),
        sa.Column('invoice_requested_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_deadline', sa.DateTime(), nullable=True),
        sa.Column('finance_reviewed_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('finance_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('finance_notes', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('paid_by', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('payment_reference', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_payroll_batches_id', 'payroll_batches', ['id'])
    op.create_index('ix_payroll_batches_tp_invoice_upload_token', 'payroll_batches', ['tp_invoice_upload_token'], unique=True)

    # --- Add batch columns to payrolls ---
    op.add_column('payrolls', sa.Column('batch_id', sa.Integer(), sa.ForeignKey('payroll_batches.id'), nullable=True))
    op.add_column('payrolls', sa.Column('tp_draft_amount', sa.Float(), nullable=True))
    op.add_column('payrolls', sa.Column('reconciliation_notes', sa.Text(), nullable=True))
    op.add_column('payrolls', sa.Column('adjusted_by', sa.String(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('payrolls', sa.Column('adjusted_at', sa.DateTime(), nullable=True))

    # --- Create client_invoices table ---
    op.create_table(
        'client_invoices',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('client_id', sa.String(), sa.ForeignKey('clients.id'), nullable=False),
        sa.Column('period', sa.String(), nullable=False),
        sa.Column('invoice_number', sa.String(), nullable=False),
        sa.Column('subtotal', sa.Float(), server_default='0'),
        sa.Column('vat_rate', sa.Float(), server_default='0.05'),
        sa.Column('vat_amount', sa.Float(), server_default='0'),
        sa.Column('total_amount', sa.Float(), server_default='0'),
        sa.Column('amount_paid', sa.Float(), server_default='0'),
        sa.Column('balance', sa.Float(), server_default='0'),
        sa.Column('currency', sa.String(10), server_default='AED'),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('payment_terms', sa.String(), nullable=True),
        sa.Column('pdf_storage_key', sa.String(), nullable=True),
        sa.Column('pdf_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum(
            'draft', 'sent', 'viewed', 'partially_paid', 'paid', 'overdue',
            name='clientinvoicestatus'
        ), server_default='draft'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_client_invoices_id', 'client_invoices', ['id'])
    op.create_index('ix_client_invoices_invoice_number', 'client_invoices', ['invoice_number'], unique=True)
    op.create_index('ix_client_invoices_access_token', 'client_invoices', ['access_token'], unique=True)

    # --- Create client_invoice_line_items table ---
    op.create_table(
        'client_invoice_line_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('client_invoice_id', sa.Integer(), sa.ForeignKey('client_invoices.id'), nullable=False),
        sa.Column('payroll_id', sa.Integer(), sa.ForeignKey('payrolls.id'), nullable=True),
        sa.Column('contractor_id', sa.String(), sa.ForeignKey('contractors.id'), nullable=True),
        sa.Column('contractor_name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('subtotal', sa.Float(), server_default='0'),
        sa.Column('vat_amount', sa.Float(), server_default='0'),
        sa.Column('total', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_client_invoice_line_items_id', 'client_invoice_line_items', ['id'])

    # --- Create client_invoice_payments table ---
    op.create_table(
        'client_invoice_payments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('client_invoice_id', sa.Integer(), sa.ForeignKey('client_invoices.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('reference_number', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_client_invoice_payments_id', 'client_invoice_payments', ['id'])


def downgrade() -> None:
    op.drop_table('client_invoice_payments')
    op.drop_table('client_invoice_line_items')
    op.drop_table('client_invoices')
    op.drop_column('payrolls', 'adjusted_at')
    op.drop_column('payrolls', 'adjusted_by')
    op.drop_column('payrolls', 'reconciliation_notes')
    op.drop_column('payrolls', 'tp_draft_amount')
    op.drop_column('payrolls', 'batch_id')
    op.drop_table('payroll_batches')
    # Note: PostgreSQL doesn't support removing enum values in downgrade
