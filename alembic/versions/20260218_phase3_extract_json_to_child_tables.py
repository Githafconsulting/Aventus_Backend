"""Phase 3: Extract JSON array columns into proper child tables (1NF).

Creates 11 child tables, migrates data from JSON columns, then drops
the JSON columns. Parent models provide backward-compat properties
that serialize child rows into the same dict format.

Revision ID: phase3_json_to_tables
Revises: phase5_cleanup
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = "phase3_json_to_tables"
down_revision = "phase5_cleanup"
branch_labels = None
depends_on = None


def _create_if_not_exists(table_name, *columns):
    """Create table only if it doesn't already exist."""
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    if table_name not in set(inspector.get_table_names()):
        op.create_table(table_name, *columns)


def upgrade() -> None:
    # === Create child tables (skip if already created by Base.metadata.create_all) ===

    _create_if_not_exists(
        "client_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.String(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_type", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "client_projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.String(), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("third_party_id", sa.String(), sa.ForeignKey("third_parties.id"), nullable=True),
        sa.Column("third_party_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "contractor_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contractor_id", sa.String(), sa.ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_type", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_order_id", sa.String(), nullable=True),
        sa.Column("contract_id", sa.String(), nullable=True),
        sa.Column("signed_by", sa.String(), nullable=True),
    )

    _create_if_not_exists(
        "work_order_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("work_order_id", sa.String(), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_type", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "proposal_deliverables",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.String(), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    _create_if_not_exists(
        "proposal_milestones",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.String(), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    _create_if_not_exists(
        "proposal_payment_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.String(), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    _create_if_not_exists(
        "proposal_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.String(), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "third_party_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("third_party_id", sa.String(), sa.ForeignKey("third_parties.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_type", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "user_signed_contracts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contractor_id", sa.String(), sa.ForeignKey("contractors.id"), nullable=True),
        sa.Column("contractor_name", sa.String(), nullable=True),
        sa.Column("contract_url", sa.String(), nullable=False),
        sa.Column("signed_date", sa.DateTime(), nullable=True),
    )

    _create_if_not_exists(
        "quote_sheet_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("quote_sheet_id", sa.String(), sa.ForeignKey("quote_sheets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
    )

    # === Migrate data from JSON columns ===
    conn = op.get_bind()

    # Client documents
    conn.execute(sa.text("""
        INSERT INTO client_documents (client_id, document_type, filename, url, uploaded_at)
        SELECT c.id, d->>'type', d->>'filename', d->>'url',
               CASE WHEN d->>'uploaded_at' IS NOT NULL THEN (d->>'uploaded_at')::timestamp ELSE NULL END
        FROM clients c, jsonb_array_elements(c.documents::jsonb) AS d
        WHERE c.documents IS NOT NULL AND c.documents::text != '[]'
    """))

    # Client projects
    conn.execute(sa.text("""
        INSERT INTO client_projects (client_id, name, description, status, third_party_id, third_party_name)
        SELECT c.id, COALESCE(p->>'name', ''), p->>'description',
               COALESCE(p->>'status', 'Planning'), p->>'third_party_id', p->>'third_party_name'
        FROM clients c, jsonb_array_elements(c.projects::jsonb) AS p
        WHERE c.projects IS NOT NULL AND c.projects::text != '[]'
    """))

    # Contractor other_documents
    conn.execute(sa.text("""
        INSERT INTO contractor_documents (contractor_id, document_type, name, url, uploaded_at, work_order_id, contract_id, signed_by)
        SELECT c.id, d->>'type', d->>'name', COALESCE(d->>'url', d->>'data'),
               CASE WHEN d->>'uploaded_at' IS NOT NULL THEN (d->>'uploaded_at')::timestamptz ELSE NULL END,
               d->>'work_order_id', d->>'contract_id', d->>'signed_by'
        FROM contractors c, jsonb_array_elements(c.other_documents::jsonb) AS d
        WHERE c.other_documents IS NOT NULL AND c.other_documents::text != '[]'
    """))

    # Work order documents
    conn.execute(sa.text("""
        INSERT INTO work_order_documents (work_order_id, document_type, filename, url, uploaded_at)
        SELECT w.id, d->>'type', d->>'filename', d->>'url',
               CASE WHEN d->>'uploaded_at' IS NOT NULL THEN (d->>'uploaded_at')::timestamp ELSE NULL END
        FROM work_orders w, jsonb_array_elements(w.documents::jsonb) AS d
        WHERE w.documents IS NOT NULL AND w.documents::text != '[]'
    """))

    # Proposal deliverables
    conn.execute(sa.text("""
        INSERT INTO proposal_deliverables (proposal_id, title, description, sort_order)
        SELECT p.id, d->>'title', d->>'description', (row_number() OVER (PARTITION BY p.id) - 1)::int
        FROM proposals p, jsonb_array_elements(p.deliverables::jsonb) AS d
        WHERE p.deliverables IS NOT NULL AND p.deliverables::text != '[]'
    """))

    # Proposal milestones
    conn.execute(sa.text("""
        INSERT INTO proposal_milestones (proposal_id, title, description, due_date, sort_order)
        SELECT p.id, COALESCE(m->>'name', m->>'title'), m->>'description',
               CASE WHEN m->>'date' IS NOT NULL THEN (m->>'date')::timestamp ELSE NULL END,
               (row_number() OVER (PARTITION BY p.id) - 1)::int
        FROM proposals p, jsonb_array_elements(p.milestones::jsonb) AS m
        WHERE p.milestones IS NOT NULL AND p.milestones::text != '[]'
    """))

    # Proposal payment_schedule
    conn.execute(sa.text("""
        INSERT INTO proposal_payment_items (proposal_id, description, amount, due_date, percentage, sort_order)
        SELECT p.id, COALESCE(s->>'phase', s->>'description'),
               CASE WHEN s->>'amount' IS NOT NULL THEN (s->>'amount')::float ELSE NULL END,
               CASE WHEN s->>'due_date' IS NOT NULL THEN (s->>'due_date')::timestamp ELSE NULL END,
               CASE WHEN s->>'percentage' IS NOT NULL THEN (s->>'percentage')::float ELSE NULL END,
               (row_number() OVER (PARTITION BY p.id) - 1)::int
        FROM proposals p, jsonb_array_elements(p.payment_schedule::jsonb) AS s
        WHERE p.payment_schedule IS NOT NULL AND p.payment_schedule::text != '[]'
    """))

    # Proposal attachments
    conn.execute(sa.text("""
        INSERT INTO proposal_attachments (proposal_id, filename, url, uploaded_at)
        SELECT p.id, a->>'filename', a->>'url',
               CASE WHEN a->>'uploaded_at' IS NOT NULL THEN (a->>'uploaded_at')::timestamp ELSE NULL END
        FROM proposals p, jsonb_array_elements(p.attachments::jsonb) AS a
        WHERE p.attachments IS NOT NULL AND p.attachments::text != '[]'
    """))

    # Third party documents
    conn.execute(sa.text("""
        INSERT INTO third_party_documents (third_party_id, document_type, filename, url, uploaded_at)
        SELECT t.id, d->>'type', d->>'filename', d->>'url',
               CASE WHEN d->>'uploaded_at' IS NOT NULL THEN (d->>'uploaded_at')::timestamp ELSE NULL END
        FROM third_parties t, jsonb_array_elements(t.documents::jsonb) AS d
        WHERE t.documents IS NOT NULL AND t.documents::text != '[]'
    """))

    # User contracts_signed
    conn.execute(sa.text("""
        INSERT INTO user_signed_contracts (user_id, contractor_id, contractor_name, contract_url, signed_date)
        SELECT u.id, c->>'contractor_id', c->>'contractor_name', c->>'contract_url',
               CASE WHEN c->>'signed_date' IS NOT NULL THEN (c->>'signed_date')::timestamp ELSE NULL END
        FROM users u, jsonb_array_elements(u.contracts_signed::jsonb) AS c
        WHERE u.contracts_signed IS NOT NULL AND u.contracts_signed::text != '[]'
    """))

    # QuoteSheet additional_documents
    conn.execute(sa.text("""
        INSERT INTO quote_sheet_documents (quote_sheet_id, filename, url, document_type, uploaded_at)
        SELECT q.id, d->>'filename', d->>'url', d->>'type',
               CASE WHEN d->>'uploaded_at' IS NOT NULL THEN (d->>'uploaded_at')::timestamp ELSE NULL END
        FROM quote_sheets q, jsonb_array_elements(q.additional_documents::jsonb) AS d
        WHERE q.additional_documents IS NOT NULL AND q.additional_documents::text != '[]'
    """))

    # === Drop JSON columns ===
    op.drop_column("clients", "documents")
    op.drop_column("clients", "projects")
    op.drop_column("contractors", "other_documents")
    op.drop_column("work_orders", "documents")
    op.drop_column("proposals", "deliverables")
    op.drop_column("proposals", "milestones")
    op.drop_column("proposals", "payment_schedule")
    op.drop_column("proposals", "attachments")
    op.drop_column("third_parties", "documents")
    op.drop_column("users", "contracts_signed")
    op.drop_column("quote_sheets", "additional_documents")


def downgrade() -> None:
    # Re-add JSON columns
    op.add_column("clients", sa.Column("documents", JSON, server_default="[]"))
    op.add_column("clients", sa.Column("projects", JSON, server_default="[]", nullable=True))
    op.add_column("contractors", sa.Column("other_documents", JSON, nullable=True))
    op.add_column("work_orders", sa.Column("documents", JSON, server_default="[]"))
    op.add_column("proposals", sa.Column("deliverables", JSON, server_default="[]"))
    op.add_column("proposals", sa.Column("milestones", JSON, server_default="[]"))
    op.add_column("proposals", sa.Column("payment_schedule", JSON, server_default="[]"))
    op.add_column("proposals", sa.Column("attachments", JSON, server_default="[]"))
    op.add_column("third_parties", sa.Column("documents", JSON, server_default="[]"))
    op.add_column("users", sa.Column("contracts_signed", JSON, nullable=True))
    op.add_column("quote_sheets", sa.Column("additional_documents", JSON, server_default="[]"))

    # Migrate data back to JSON columns
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE clients SET documents = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('type', cd.document_type, 'filename', cd.filename, 'url', cd.url, 'uploaded_at', cd.uploaded_at))
             FROM client_documents cd WHERE cd.client_id = clients.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE clients SET projects = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('name', cp.name, 'description', cp.description, 'status', cp.status, 'third_party_id', cp.third_party_id, 'third_party_name', cp.third_party_name))
             FROM client_projects cp WHERE cp.client_id = clients.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE contractors SET other_documents = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('type', cd.document_type, 'name', cd.name, 'url', cd.url, 'uploaded_at', cd.uploaded_at, 'work_order_id', cd.work_order_id, 'contract_id', cd.contract_id, 'signed_by', cd.signed_by))
             FROM contractor_documents cd WHERE cd.contractor_id = contractors.id), NULL)
    """))

    conn.execute(sa.text("""
        UPDATE work_orders SET documents = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('type', wd.document_type, 'filename', wd.filename, 'url', wd.url, 'uploaded_at', wd.uploaded_at))
             FROM work_order_documents wd WHERE wd.work_order_id = work_orders.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE proposals SET deliverables = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('title', pd.title, 'description', pd.description) ORDER BY pd.sort_order)
             FROM proposal_deliverables pd WHERE pd.proposal_id = proposals.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE proposals SET milestones = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('name', pm.title, 'description', pm.description, 'date', pm.due_date) ORDER BY pm.sort_order)
             FROM proposal_milestones pm WHERE pm.proposal_id = proposals.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE proposals SET payment_schedule = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('phase', pp.description, 'amount', pp.amount, 'due_date', pp.due_date, 'percentage', pp.percentage) ORDER BY pp.sort_order)
             FROM proposal_payment_items pp WHERE pp.proposal_id = proposals.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE proposals SET attachments = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('filename', pa.filename, 'url', pa.url, 'uploaded_at', pa.uploaded_at))
             FROM proposal_attachments pa WHERE pa.proposal_id = proposals.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE third_parties SET documents = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('type', td.document_type, 'filename', td.filename, 'url', td.url, 'uploaded_at', td.uploaded_at))
             FROM third_party_documents td WHERE td.third_party_id = third_parties.id), '[]'::jsonb)
    """))

    conn.execute(sa.text("""
        UPDATE users SET contracts_signed = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('contractor_id', uc.contractor_id, 'contractor_name', uc.contractor_name, 'contract_url', uc.contract_url, 'signed_date', uc.signed_date))
             FROM user_signed_contracts uc WHERE uc.user_id = users.id), NULL)
    """))

    conn.execute(sa.text("""
        UPDATE quote_sheets SET additional_documents = COALESCE(
            (SELECT jsonb_agg(jsonb_build_object('filename', qd.filename, 'url', qd.url, 'type', qd.document_type, 'uploaded_at', qd.uploaded_at))
             FROM quote_sheet_documents qd WHERE qd.quote_sheet_id = quote_sheets.id), '[]'::jsonb)
    """))

    # Drop child tables
    op.drop_table("quote_sheet_documents")
    op.drop_table("user_signed_contracts")
    op.drop_table("third_party_documents")
    op.drop_table("proposal_attachments")
    op.drop_table("proposal_payment_items")
    op.drop_table("proposal_milestones")
    op.drop_table("proposal_deliverables")
    op.drop_table("work_order_documents")
    op.drop_table("contractor_documents")
    op.drop_table("client_projects")
    op.drop_table("client_documents")
