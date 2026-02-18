"""Add missing foreign key constraints for ACID compliance

Adds FK constraints to:
- clients.third_party_id -> third_parties.id
- contractors.third_party_id -> third_parties.id
- contractors.client_id -> clients.id
- contractors.consultant_id -> users.id

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-18
"""
from alembic import op
from sqlalchemy import text

# revision identifiers
revision = 'b3c4d5e6f7a8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clean up empty strings to NULL before adding FK constraints
    conn = op.get_bind()
    conn.execute(text("UPDATE contractors SET third_party_id = NULL WHERE third_party_id = ''"))
    conn.execute(text("UPDATE contractors SET client_id = NULL WHERE client_id = ''"))
    conn.execute(text("UPDATE contractors SET consultant_id = NULL WHERE consultant_id = ''"))

    # clients.third_party_id -> third_parties.id
    op.create_foreign_key(
        'fk_clients_third_party_id',
        'clients', 'third_parties',
        ['third_party_id'], ['id'],
    )

    # contractors.third_party_id -> third_parties.id
    op.create_foreign_key(
        'fk_contractors_third_party_id',
        'contractors', 'third_parties',
        ['third_party_id'], ['id'],
    )

    # contractors.client_id -> clients.id
    op.create_foreign_key(
        'fk_contractors_client_id',
        'contractors', 'clients',
        ['client_id'], ['id'],
    )

    # contractors.consultant_id -> users.id
    op.create_foreign_key(
        'fk_contractors_consultant_id',
        'contractors', 'users',
        ['consultant_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_contractors_consultant_id', 'contractors', type_='foreignkey')
    op.drop_constraint('fk_contractors_client_id', 'contractors', type_='foreignkey')
    op.drop_constraint('fk_contractors_third_party_id', 'contractors', type_='foreignkey')
    op.drop_constraint('fk_clients_third_party_id', 'clients', type_='foreignkey')
