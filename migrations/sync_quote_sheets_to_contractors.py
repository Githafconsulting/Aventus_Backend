"""
Migration: Sync existing quote sheets to contractor documents
This copies quote sheet document URLs from the quote_sheets table to the contractor.third_party_document field
for contractors who had quote sheets uploaded before this field was added.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import settings

def run_migration():
    """Sync quote sheet documents to contractors"""
    engine = create_engine(settings.database_url)

    with engine.begin() as conn:
        # Find all quote sheets with documents that haven't been synced to contractors
        result = conn.execute(text("""
            SELECT
                qs.id as quote_sheet_id,
                qs.contractor_id,
                qs.document_url,
                qs.uploaded_at,
                CONCAT(c.first_name, ' ', c.surname) as contractor_name,
                c.third_party_document
            FROM quote_sheets qs
            JOIN contractors c ON c.id = qs.contractor_id
            WHERE qs.document_url IS NOT NULL
            AND qs.document_url != ''
            AND (c.third_party_document IS NULL OR c.third_party_document = '')
        """))

        quote_sheets = result.fetchall()

        if not quote_sheets:
            print("SUCCESS: No quote sheets need to be synced. All contractors are up to date.")
            return

        print(f"Found {len(quote_sheets)} quote sheet(s) to sync to contractors\n")

        # Update each contractor with their quote sheet document
        for qs in quote_sheets:
            contractor_id = qs.contractor_id
            contractor_name = qs.contractor_name
            document_url = qs.document_url
            uploaded_at = qs.uploaded_at

            conn.execute(text("""
                UPDATE contractors
                SET
                    third_party_document = :document_url,
                    third_party_response_received_date = :uploaded_at,
                    updated_at = NOW()
                WHERE id = :contractor_id
            """), {
                "document_url": document_url,
                "uploaded_at": uploaded_at,
                "contractor_id": contractor_id
            })

            print(f"SUCCESS: Synced quote sheet to contractor: {contractor_name} (ID: {contractor_id})")

        print(f"\nSUCCESS: Successfully synced {len(quote_sheets)} quote sheet(s) to contractors")

if __name__ == "__main__":
    print("Starting migration: Sync quote sheets to contractors...\n")
    try:
        run_migration()
        print("\nSUCCESS: Migration completed successfully!")
    except Exception as e:
        print(f"\nERROR: Migration failed: {str(e)}")
        sys.exit(1)
