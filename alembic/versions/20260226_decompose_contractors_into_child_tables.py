"""Decompose contractors table into 7 normalized child tables.

Extracts 117 columns from the monolithic contractors table into 7 1:1 child
tables: contractor_mgmt_company, contractor_banking, contractor_invoicing,
contractor_deal_terms, contractor_tokens, contractor_signatures, contractor_cohf.

Data is migrated from the parent table, then the original columns are dropped.
Backward compatibility is maintained via @property getter/setter pairs on the
Contractor model.

Revision ID: decompose_contractors
Revises: phase6_drop_names
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "decompose_contractors"
down_revision = "phase6_drop_names"
branch_labels = None
depends_on = None


def upgrade():
    # =======================================================
    # Phase 1: contractor_mgmt_company (14 columns)
    # =======================================================
    op.create_table(
        "contractor_mgmt_company",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("umbrella_company_name", sa.String, nullable=True),
        sa.Column("company_vat_no", sa.String, nullable=True),
        sa.Column("company_name", sa.String, nullable=True),
        sa.Column("company_reg_no", sa.String, nullable=True),
        sa.Column("mgmt_address_line1", sa.String, nullable=True),
        sa.Column("mgmt_address_line2", sa.String, nullable=True),
        sa.Column("mgmt_address_line3", sa.String, nullable=True),
        sa.Column("mgmt_address_line4", sa.String, nullable=True),
        sa.Column("mgmt_country", sa.String, nullable=True),
        sa.Column("mgmt_bank_name", sa.String, nullable=True),
        sa.Column("mgmt_account_name", sa.String, nullable=True),
        sa.Column("mgmt_account_number", sa.String, nullable=True),
        sa.Column("mgmt_iban_number", sa.String, nullable=True),
        sa.Column("mgmt_swift_bic", sa.String, nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_mgmt_company (contractor_id, umbrella_company_name, company_vat_no, company_name, company_reg_no, mgmt_address_line1, mgmt_address_line2, mgmt_address_line3, mgmt_address_line4, mgmt_country, mgmt_bank_name, mgmt_account_name, mgmt_account_number, mgmt_iban_number, mgmt_swift_bic)
        SELECT id, umbrella_company_name, company_vat_no, company_name, company_reg_no, mgmt_address_line1, mgmt_address_line2, mgmt_address_line3, mgmt_address_line4, mgmt_country, mgmt_bank_name, mgmt_account_name, mgmt_account_number, mgmt_iban_number, mgmt_swift_bic
        FROM contractors
        WHERE umbrella_company_name IS NOT NULL OR company_vat_no IS NOT NULL OR company_name IS NOT NULL OR company_reg_no IS NOT NULL OR mgmt_address_line1 IS NOT NULL OR mgmt_bank_name IS NOT NULL OR mgmt_account_number IS NOT NULL OR mgmt_iban_number IS NOT NULL OR mgmt_swift_bic IS NOT NULL
    """)

    # =======================================================
    # Phase 2: contractor_banking (9 columns)
    # =======================================================
    op.create_table(
        "contractor_banking",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("contractor_bank_name", sa.String, nullable=True),
        sa.Column("contractor_account_name", sa.String, nullable=True),
        sa.Column("contractor_account_no", sa.String, nullable=True),
        sa.Column("contractor_iban", sa.String, nullable=True),
        sa.Column("contractor_swift_bic", sa.String, nullable=True),
        sa.Column("candidate_bank_name", sa.String, nullable=True),
        sa.Column("candidate_bank_details", sa.String, nullable=True),
        sa.Column("candidate_iban", sa.String, nullable=True),
        sa.Column("umbrella_or_direct", sa.String, nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_banking (contractor_id, contractor_bank_name, contractor_account_name, contractor_account_no, contractor_iban, contractor_swift_bic, candidate_bank_name, candidate_bank_details, candidate_iban, umbrella_or_direct)
        SELECT id, contractor_bank_name, contractor_account_name, contractor_account_no, contractor_iban, contractor_swift_bic, candidate_bank_name, candidate_bank_details, candidate_iban, umbrella_or_direct
        FROM contractors
        WHERE contractor_bank_name IS NOT NULL OR contractor_account_no IS NOT NULL OR contractor_iban IS NOT NULL OR candidate_bank_name IS NOT NULL OR candidate_iban IS NOT NULL OR umbrella_or_direct IS NOT NULL
    """)

    # =======================================================
    # Phase 3: contractor_invoicing (22 columns)
    # =======================================================
    op.create_table(
        "contractor_invoicing",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("timesheet_required", sa.String, nullable=True),
        sa.Column("timesheet_approver_name", sa.String, nullable=True),
        sa.Column("invoice_email1", sa.String, nullable=True),
        sa.Column("invoice_email2", sa.String, nullable=True),
        sa.Column("client_contact1", sa.String, nullable=True),
        sa.Column("client_contact2", sa.String, nullable=True),
        sa.Column("invoice_address_line1", sa.String, nullable=True),
        sa.Column("invoice_address_line2", sa.String, nullable=True),
        sa.Column("invoice_address_line3", sa.String, nullable=True),
        sa.Column("invoice_address_line4", sa.String, nullable=True),
        sa.Column("invoice_po_box", sa.String, nullable=True),
        sa.Column("invoice_country", sa.String, nullable=True),
        sa.Column("invoice_tax_number", sa.String, nullable=True),
        sa.Column("tax_number", sa.String, nullable=True),
        sa.Column("contractor_pay_frequency", sa.String, nullable=True),
        sa.Column("client_invoice_frequency", sa.String, nullable=True),
        sa.Column("client_payment_terms", sa.String, nullable=True),
        sa.Column("invoicing_preferences", sa.String, nullable=True),
        sa.Column("invoice_instructions", sa.Text, nullable=True),
        sa.Column("supporting_docs_required", sa.String, nullable=True),
        sa.Column("po_required", sa.String, nullable=True),
        sa.Column("po_number", sa.String, nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_invoicing (contractor_id, timesheet_required, timesheet_approver_name, invoice_email1, invoice_email2, client_contact1, client_contact2, invoice_address_line1, invoice_address_line2, invoice_address_line3, invoice_address_line4, invoice_po_box, invoice_country, invoice_tax_number, tax_number, contractor_pay_frequency, client_invoice_frequency, client_payment_terms, invoicing_preferences, invoice_instructions, supporting_docs_required, po_required, po_number)
        SELECT id, timesheet_required, timesheet_approver_name, invoice_email1, invoice_email2, client_contact1, client_contact2, invoice_address_line1, invoice_address_line2, invoice_address_line3, invoice_address_line4, invoice_po_box, invoice_country, invoice_tax_number, tax_number, contractor_pay_frequency, client_invoice_frequency, client_payment_terms, invoicing_preferences, invoice_instructions, supporting_docs_required, po_required, po_number
        FROM contractors
        WHERE timesheet_required IS NOT NULL OR invoice_email1 IS NOT NULL OR client_contact1 IS NOT NULL OR invoice_address_line1 IS NOT NULL OR contractor_pay_frequency IS NOT NULL OR client_invoice_frequency IS NOT NULL OR po_required IS NOT NULL
    """)

    # =======================================================
    # Phase 4: contractor_deal_terms (35 columns)
    # =======================================================
    op.create_table(
        "contractor_deal_terms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("rate_type", sa.String, nullable=True),
        sa.Column("charge_rate_month", sa.String, nullable=True),
        sa.Column("gross_salary", sa.String, nullable=True),
        sa.Column("charge_rate_day", sa.String, nullable=True),
        sa.Column("day_rate", sa.String, nullable=True),
        sa.Column("candidate_pay_rate_period", sa.String, nullable=True),
        sa.Column("management_company_charges", sa.String, nullable=True),
        sa.Column("taxes", sa.String, nullable=True),
        sa.Column("bank_fees", sa.String, nullable=True),
        sa.Column("fx", sa.String, nullable=True),
        sa.Column("nationalisation", sa.String, nullable=True),
        sa.Column("leave_allowance", sa.String, nullable=True),
        sa.Column("eosb", sa.String, nullable=True),
        sa.Column("vacation_days", sa.String, nullable=True),
        sa.Column("vacation_pay", sa.String, nullable=True),
        sa.Column("sick_leave", sa.String, nullable=True),
        sa.Column("other_provision", sa.String, nullable=True),
        sa.Column("flights", sa.String, nullable=True),
        sa.Column("visa", sa.String, nullable=True),
        sa.Column("medical_insurance", sa.String, nullable=True),
        sa.Column("family_costs", sa.String, nullable=True),
        sa.Column("other_one_time_costs", sa.String, nullable=True),
        sa.Column("laptop_provided_by", sa.String, nullable=True),
        sa.Column("any_notes", sa.Text, nullable=True),
        sa.Column("upfront_invoices", sa.String, nullable=True),
        sa.Column("security_deposit", sa.String, nullable=True),
        sa.Column("total_monthly_costs", sa.String, nullable=True),
        sa.Column("total_contractor_fixed_costs", sa.String, nullable=True),
        sa.Column("monthly_contractor_fixed_costs", sa.String, nullable=True),
        sa.Column("total_contractor_monthly_cost", sa.String, nullable=True),
        sa.Column("estimated_monthly_gp", sa.String, nullable=True),
        sa.Column("consultant", sa.String, nullable=True),
        sa.Column("resourcer", sa.String, nullable=True),
        sa.Column("aventus_split", sa.String, nullable=True),
        sa.Column("resourcer_split", sa.String, nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_deal_terms (contractor_id, rate_type, charge_rate_month, gross_salary, charge_rate_day, day_rate, candidate_pay_rate_period, management_company_charges, taxes, bank_fees, fx, nationalisation, leave_allowance, eosb, vacation_days, vacation_pay, sick_leave, other_provision, flights, visa, medical_insurance, family_costs, other_one_time_costs, laptop_provided_by, any_notes, upfront_invoices, security_deposit, total_monthly_costs, total_contractor_fixed_costs, monthly_contractor_fixed_costs, total_contractor_monthly_cost, estimated_monthly_gp, consultant, resourcer, aventus_split, resourcer_split)
        SELECT id, rate_type, charge_rate_month, gross_salary, charge_rate_day, day_rate, candidate_pay_rate_period, management_company_charges, taxes, bank_fees, fx, nationalisation, leave_allowance, eosb, vacation_days, vacation_pay, sick_leave, other_provision, flights, visa, medical_insurance, family_costs, other_one_time_costs, laptop_provided_by, any_notes, upfront_invoices, security_deposit, total_monthly_costs, total_contractor_fixed_costs, monthly_contractor_fixed_costs, total_contractor_monthly_cost, estimated_monthly_gp, consultant, resourcer, aventus_split, resourcer_split
        FROM contractors
        WHERE rate_type IS NOT NULL OR charge_rate_month IS NOT NULL OR gross_salary IS NOT NULL OR charge_rate_day IS NOT NULL OR day_rate IS NOT NULL OR management_company_charges IS NOT NULL OR consultant IS NOT NULL
    """)

    # =======================================================
    # Phase 5: contractor_tokens (12 columns)
    # =======================================================
    op.create_table(
        "contractor_tokens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("contract_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_upload_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("document_token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contract_upload_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("contract_upload_token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_sheet_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("quote_sheet_token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("cohf_token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("third_party_contract_upload_token", sa.String, unique=True, nullable=True, index=True),
        sa.Column("third_party_contract_token_expiry", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_tokens (contractor_id, contract_token, token_expiry, document_upload_token, document_token_expiry, contract_upload_token, contract_upload_token_expiry, quote_sheet_token, quote_sheet_token_expiry, cohf_token, cohf_token_expiry, third_party_contract_upload_token, third_party_contract_token_expiry)
        SELECT id, contract_token, token_expiry, document_upload_token, document_token_expiry, contract_upload_token, contract_upload_token_expiry, quote_sheet_token, quote_sheet_token_expiry, cohf_token, cohf_token_expiry, third_party_contract_upload_token, third_party_contract_token_expiry
        FROM contractors
        WHERE contract_token IS NOT NULL OR document_upload_token IS NOT NULL OR contract_upload_token IS NOT NULL OR quote_sheet_token IS NOT NULL OR cohf_token IS NOT NULL OR third_party_contract_upload_token IS NOT NULL
    """)

    # =======================================================
    # Phase 6: contractor_signatures (18 columns)
    # =======================================================
    op.create_table(
        "contractor_signatures",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("signature_type", sa.String, nullable=True),
        sa.Column("signature_data", sa.Text, nullable=True),
        sa.Column("signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superadmin_signature_type", sa.String, nullable=True),
        sa.Column("superadmin_signature_data", sa.Text, nullable=True),
        sa.Column("cohf_third_party_signature", sa.Text, nullable=True),
        sa.Column("cohf_third_party_name", sa.String, nullable=True),
        sa.Column("cohf_aventus_signature_type", sa.String, nullable=True),
        sa.Column("cohf_aventus_signature_data", sa.Text, nullable=True),
        sa.Column("cohf_aventus_signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_aventus_signed_by", sa.String, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("quote_sheet_third_party_signature", sa.Text, nullable=True),
        sa.Column("quote_sheet_third_party_name", sa.String, nullable=True),
        sa.Column("quote_sheet_third_party_signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_sheet_aventus_signature_type", sa.String, nullable=True),
        sa.Column("quote_sheet_aventus_signature_data", sa.Text, nullable=True),
        sa.Column("quote_sheet_aventus_signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_sheet_aventus_signed_by", sa.String, sa.ForeignKey("users.id"), nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_signatures (contractor_id, signature_type, signature_data, signed_date, superadmin_signature_type, superadmin_signature_data, cohf_third_party_signature, cohf_third_party_name, cohf_aventus_signature_type, cohf_aventus_signature_data, cohf_aventus_signed_date, cohf_aventus_signed_by, quote_sheet_third_party_signature, quote_sheet_third_party_name, quote_sheet_third_party_signed_date, quote_sheet_aventus_signature_type, quote_sheet_aventus_signature_data, quote_sheet_aventus_signed_date, quote_sheet_aventus_signed_by)
        SELECT id, signature_type, signature_data, signed_date, superadmin_signature_type, superadmin_signature_data, cohf_third_party_signature, cohf_third_party_name, cohf_aventus_signature_type, cohf_aventus_signature_data, cohf_aventus_signed_date, cohf_aventus_signed_by, quote_sheet_third_party_signature, quote_sheet_third_party_name, quote_sheet_third_party_signed_date, quote_sheet_aventus_signature_type, quote_sheet_aventus_signature_data, quote_sheet_aventus_signed_date, quote_sheet_aventus_signed_by
        FROM contractors
        WHERE signature_type IS NOT NULL OR signature_data IS NOT NULL OR superadmin_signature_type IS NOT NULL OR cohf_third_party_signature IS NOT NULL OR quote_sheet_third_party_signature IS NOT NULL
    """)

    # =======================================================
    # Phase 7: contractor_cohf (7 columns)
    # =======================================================
    op.create_table(
        "contractor_cohf",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String, sa.ForeignKey("contractors.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("cohf_data", sa.JSON, nullable=True),
        sa.Column("cohf_status", sa.String, nullable=True),
        sa.Column("cohf_submitted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_sent_to_3rd_party_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_docusign_received_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohf_signed_document", sa.String, nullable=True),
    )
    op.execute("""
        INSERT INTO contractor_cohf (contractor_id, cohf_data, cohf_status, cohf_submitted_date, cohf_sent_to_3rd_party_date, cohf_docusign_received_date, cohf_completed_date, cohf_signed_document)
        SELECT id, cohf_data::json, cohf_status, cohf_submitted_date, cohf_sent_to_3rd_party_date, cohf_docusign_received_date, cohf_completed_date, cohf_signed_document
        FROM contractors
        WHERE cohf_data IS NOT NULL OR cohf_status IS NOT NULL OR cohf_submitted_date IS NOT NULL OR cohf_signed_document IS NOT NULL
    """)

    # =======================================================
    # Drop all moved columns from contractors
    # =======================================================
    # Phase 1: mgmt_company
    for col in [
        "umbrella_company_name", "company_vat_no", "company_name", "company_reg_no",
        "mgmt_address_line1", "mgmt_address_line2", "mgmt_address_line3", "mgmt_address_line4",
        "mgmt_country", "mgmt_bank_name", "mgmt_account_name", "mgmt_account_number",
        "mgmt_iban_number", "mgmt_swift_bic",
    ]:
        op.drop_column("contractors", col)

    # Phase 2: banking
    for col in [
        "contractor_bank_name", "contractor_account_name", "contractor_account_no",
        "contractor_iban", "contractor_swift_bic", "candidate_bank_name",
        "candidate_bank_details", "candidate_iban", "umbrella_or_direct",
    ]:
        op.drop_column("contractors", col)

    # Phase 3: invoicing
    for col in [
        "timesheet_required", "timesheet_approver_name", "invoice_email1", "invoice_email2",
        "client_contact1", "client_contact2", "invoice_address_line1", "invoice_address_line2",
        "invoice_address_line3", "invoice_address_line4", "invoice_po_box", "invoice_country",
        "invoice_tax_number", "tax_number", "contractor_pay_frequency",
        "client_invoice_frequency", "client_payment_terms", "invoicing_preferences",
        "invoice_instructions", "supporting_docs_required", "po_required", "po_number",
    ]:
        op.drop_column("contractors", col)

    # Phase 4: deal_terms
    for col in [
        "rate_type", "charge_rate_month", "gross_salary", "charge_rate_day", "day_rate",
        "candidate_pay_rate_period", "management_company_charges", "taxes", "bank_fees",
        "fx", "nationalisation", "leave_allowance", "eosb", "vacation_days", "vacation_pay",
        "sick_leave", "other_provision", "flights", "visa", "medical_insurance",
        "family_costs", "other_one_time_costs", "laptop_provided_by", "any_notes",
        "upfront_invoices", "security_deposit", "total_monthly_costs",
        "total_contractor_fixed_costs", "monthly_contractor_fixed_costs",
        "total_contractor_monthly_cost", "estimated_monthly_gp", "consultant", "resourcer",
        "aventus_split", "resourcer_split",
    ]:
        op.drop_column("contractors", col)

    # Phase 5: tokens
    for col in [
        "contract_token", "token_expiry", "document_upload_token", "document_token_expiry",
        "contract_upload_token", "contract_upload_token_expiry", "quote_sheet_token",
        "quote_sheet_token_expiry", "cohf_token", "cohf_token_expiry",
        "third_party_contract_upload_token", "third_party_contract_token_expiry",
    ]:
        op.drop_column("contractors", col)

    # Phase 6: signatures
    for col in [
        "signature_type", "signature_data", "signed_date", "superadmin_signature_type",
        "superadmin_signature_data", "cohf_third_party_signature", "cohf_third_party_name",
        "cohf_aventus_signature_type", "cohf_aventus_signature_data",
        "cohf_aventus_signed_date", "cohf_aventus_signed_by",
        "quote_sheet_third_party_signature", "quote_sheet_third_party_name",
        "quote_sheet_third_party_signed_date", "quote_sheet_aventus_signature_type",
        "quote_sheet_aventus_signature_data", "quote_sheet_aventus_signed_date",
        "quote_sheet_aventus_signed_by",
    ]:
        op.drop_column("contractors", col)

    # Phase 7: cohf
    for col in [
        "cohf_data", "cohf_status", "cohf_submitted_date", "cohf_sent_to_3rd_party_date",
        "cohf_docusign_received_date", "cohf_completed_date", "cohf_signed_document",
    ]:
        op.drop_column("contractors", col)


def downgrade():
    # =======================================================
    # Re-add all columns to contractors
    # =======================================================
    # Phase 1: mgmt_company
    op.add_column("contractors", sa.Column("umbrella_company_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("company_vat_no", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("company_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("company_reg_no", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_address_line1", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_address_line2", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_address_line3", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_address_line4", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_country", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_bank_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_account_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_account_number", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_iban_number", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("mgmt_swift_bic", sa.String, nullable=True))

    # Phase 2: banking
    op.add_column("contractors", sa.Column("contractor_bank_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("contractor_account_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("contractor_account_no", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("contractor_iban", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("contractor_swift_bic", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("candidate_bank_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("candidate_bank_details", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("candidate_iban", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("umbrella_or_direct", sa.String, nullable=True))

    # Phase 3: invoicing
    op.add_column("contractors", sa.Column("timesheet_required", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("timesheet_approver_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_email1", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_email2", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("client_contact1", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("client_contact2", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_address_line1", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_address_line2", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_address_line3", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_address_line4", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_po_box", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_country", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_tax_number", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("tax_number", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("contractor_pay_frequency", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("client_invoice_frequency", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("client_payment_terms", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoicing_preferences", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("invoice_instructions", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("supporting_docs_required", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("po_required", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("po_number", sa.String, nullable=True))

    # Phase 4: deal_terms
    op.add_column("contractors", sa.Column("rate_type", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("charge_rate_month", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("gross_salary", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("charge_rate_day", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("day_rate", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("candidate_pay_rate_period", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("management_company_charges", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("taxes", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("bank_fees", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("fx", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("nationalisation", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("leave_allowance", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("eosb", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("vacation_days", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("vacation_pay", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("sick_leave", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("other_provision", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("flights", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("visa", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("medical_insurance", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("family_costs", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("other_one_time_costs", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("laptop_provided_by", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("any_notes", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("upfront_invoices", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("security_deposit", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("total_monthly_costs", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("total_contractor_fixed_costs", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("monthly_contractor_fixed_costs", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("total_contractor_monthly_cost", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("estimated_monthly_gp", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("consultant", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("resourcer", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("aventus_split", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("resourcer_split", sa.String, nullable=True))

    # Phase 5: tokens
    op.add_column("contractors", sa.Column("contract_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("document_upload_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("document_token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("contract_upload_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("contract_upload_token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("quote_sheet_token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("cohf_token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("third_party_contract_upload_token", sa.String, unique=True, nullable=True, index=True))
    op.add_column("contractors", sa.Column("third_party_contract_token_expiry", sa.DateTime(timezone=True), nullable=True))

    # Phase 6: signatures
    op.add_column("contractors", sa.Column("signature_type", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("signature_data", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("signed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("superadmin_signature_type", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("superadmin_signature_data", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("cohf_third_party_signature", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("cohf_third_party_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("cohf_aventus_signature_type", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("cohf_aventus_signature_data", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("cohf_aventus_signed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_aventus_signed_by", sa.String, sa.ForeignKey("users.id"), nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_third_party_signature", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_third_party_name", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_third_party_signed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_aventus_signature_type", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_aventus_signature_data", sa.Text, nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_aventus_signed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("quote_sheet_aventus_signed_by", sa.String, sa.ForeignKey("users.id"), nullable=True))

    # Phase 7: cohf
    op.add_column("contractors", sa.Column("cohf_data", sa.JSON, nullable=True))
    op.add_column("contractors", sa.Column("cohf_status", sa.String, nullable=True))
    op.add_column("contractors", sa.Column("cohf_submitted_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_sent_to_3rd_party_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_docusign_received_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_completed_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contractors", sa.Column("cohf_signed_document", sa.String, nullable=True))

    # =======================================================
    # Restore data from child tables back to contractors
    # =======================================================
    op.execute("""
        UPDATE contractors SET
            umbrella_company_name = m.umbrella_company_name, company_vat_no = m.company_vat_no,
            company_name = m.company_name, company_reg_no = m.company_reg_no,
            mgmt_address_line1 = m.mgmt_address_line1, mgmt_address_line2 = m.mgmt_address_line2,
            mgmt_address_line3 = m.mgmt_address_line3, mgmt_address_line4 = m.mgmt_address_line4,
            mgmt_country = m.mgmt_country, mgmt_bank_name = m.mgmt_bank_name,
            mgmt_account_name = m.mgmt_account_name, mgmt_account_number = m.mgmt_account_number,
            mgmt_iban_number = m.mgmt_iban_number, mgmt_swift_bic = m.mgmt_swift_bic
        FROM contractor_mgmt_company m WHERE m.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            contractor_bank_name = b.contractor_bank_name, contractor_account_name = b.contractor_account_name,
            contractor_account_no = b.contractor_account_no, contractor_iban = b.contractor_iban,
            contractor_swift_bic = b.contractor_swift_bic, candidate_bank_name = b.candidate_bank_name,
            candidate_bank_details = b.candidate_bank_details, candidate_iban = b.candidate_iban,
            umbrella_or_direct = b.umbrella_or_direct
        FROM contractor_banking b WHERE b.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            timesheet_required = i.timesheet_required, timesheet_approver_name = i.timesheet_approver_name,
            invoice_email1 = i.invoice_email1, invoice_email2 = i.invoice_email2,
            client_contact1 = i.client_contact1, client_contact2 = i.client_contact2,
            invoice_address_line1 = i.invoice_address_line1, invoice_address_line2 = i.invoice_address_line2,
            invoice_address_line3 = i.invoice_address_line3, invoice_address_line4 = i.invoice_address_line4,
            invoice_po_box = i.invoice_po_box, invoice_country = i.invoice_country,
            invoice_tax_number = i.invoice_tax_number, tax_number = i.tax_number,
            contractor_pay_frequency = i.contractor_pay_frequency, client_invoice_frequency = i.client_invoice_frequency,
            client_payment_terms = i.client_payment_terms, invoicing_preferences = i.invoicing_preferences,
            invoice_instructions = i.invoice_instructions, supporting_docs_required = i.supporting_docs_required,
            po_required = i.po_required, po_number = i.po_number
        FROM contractor_invoicing i WHERE i.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            rate_type = d.rate_type, charge_rate_month = d.charge_rate_month,
            gross_salary = d.gross_salary, charge_rate_day = d.charge_rate_day,
            day_rate = d.day_rate, candidate_pay_rate_period = d.candidate_pay_rate_period,
            management_company_charges = d.management_company_charges, taxes = d.taxes,
            bank_fees = d.bank_fees, fx = d.fx, nationalisation = d.nationalisation,
            leave_allowance = d.leave_allowance, eosb = d.eosb, vacation_days = d.vacation_days,
            vacation_pay = d.vacation_pay, sick_leave = d.sick_leave, other_provision = d.other_provision,
            flights = d.flights, visa = d.visa, medical_insurance = d.medical_insurance,
            family_costs = d.family_costs, other_one_time_costs = d.other_one_time_costs,
            laptop_provided_by = d.laptop_provided_by, any_notes = d.any_notes,
            upfront_invoices = d.upfront_invoices, security_deposit = d.security_deposit,
            total_monthly_costs = d.total_monthly_costs, total_contractor_fixed_costs = d.total_contractor_fixed_costs,
            monthly_contractor_fixed_costs = d.monthly_contractor_fixed_costs,
            total_contractor_monthly_cost = d.total_contractor_monthly_cost,
            estimated_monthly_gp = d.estimated_monthly_gp, consultant = d.consultant,
            resourcer = d.resourcer, aventus_split = d.aventus_split, resourcer_split = d.resourcer_split
        FROM contractor_deal_terms d WHERE d.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            contract_token = t.contract_token, token_expiry = t.token_expiry,
            document_upload_token = t.document_upload_token, document_token_expiry = t.document_token_expiry,
            contract_upload_token = t.contract_upload_token, contract_upload_token_expiry = t.contract_upload_token_expiry,
            quote_sheet_token = t.quote_sheet_token, quote_sheet_token_expiry = t.quote_sheet_token_expiry,
            cohf_token = t.cohf_token, cohf_token_expiry = t.cohf_token_expiry,
            third_party_contract_upload_token = t.third_party_contract_upload_token,
            third_party_contract_token_expiry = t.third_party_contract_token_expiry
        FROM contractor_tokens t WHERE t.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            signature_type = s.signature_type, signature_data = s.signature_data,
            signed_date = s.signed_date, superadmin_signature_type = s.superadmin_signature_type,
            superadmin_signature_data = s.superadmin_signature_data,
            cohf_third_party_signature = s.cohf_third_party_signature,
            cohf_third_party_name = s.cohf_third_party_name,
            cohf_aventus_signature_type = s.cohf_aventus_signature_type,
            cohf_aventus_signature_data = s.cohf_aventus_signature_data,
            cohf_aventus_signed_date = s.cohf_aventus_signed_date,
            cohf_aventus_signed_by = s.cohf_aventus_signed_by,
            quote_sheet_third_party_signature = s.quote_sheet_third_party_signature,
            quote_sheet_third_party_name = s.quote_sheet_third_party_name,
            quote_sheet_third_party_signed_date = s.quote_sheet_third_party_signed_date,
            quote_sheet_aventus_signature_type = s.quote_sheet_aventus_signature_type,
            quote_sheet_aventus_signature_data = s.quote_sheet_aventus_signature_data,
            quote_sheet_aventus_signed_date = s.quote_sheet_aventus_signed_date,
            quote_sheet_aventus_signed_by = s.quote_sheet_aventus_signed_by
        FROM contractor_signatures s WHERE s.contractor_id = contractors.id
    """)
    op.execute("""
        UPDATE contractors SET
            cohf_data = c.cohf_data, cohf_status = c.cohf_status,
            cohf_submitted_date = c.cohf_submitted_date,
            cohf_sent_to_3rd_party_date = c.cohf_sent_to_3rd_party_date,
            cohf_docusign_received_date = c.cohf_docusign_received_date,
            cohf_completed_date = c.cohf_completed_date,
            cohf_signed_document = c.cohf_signed_document
        FROM contractor_cohf c WHERE c.contractor_id = contractors.id
    """)

    # Drop child tables (reverse order)
    op.drop_table("contractor_cohf")
    op.drop_table("contractor_signatures")
    op.drop_table("contractor_tokens")
    op.drop_table("contractor_deal_terms")
    op.drop_table("contractor_invoicing")
    op.drop_table("contractor_banking")
    op.drop_table("contractor_mgmt_company")
