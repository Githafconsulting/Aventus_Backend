"""
Migration script to create contract_templates and contracts tables
"""
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.database_url)

def run_migration():
    with engine.connect() as conn:
        # Create contract_templates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contract_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                template_content TEXT NOT NULL,
                version VARCHAR NOT NULL DEFAULT '1.0',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                created_by VARCHAR
            );
        """))

        # Create contracts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                contractor_id VARCHAR NOT NULL REFERENCES contractors(id),
                template_id INTEGER REFERENCES contract_templates(id),

                contract_content TEXT NOT NULL,

                contract_date VARCHAR,
                consultant_name VARCHAR,
                client_name VARCHAR,
                client_address TEXT,
                job_title VARCHAR,
                commencement_date VARCHAR,
                contract_rate VARCHAR,
                working_location VARCHAR,
                duration VARCHAR,

                contract_token VARCHAR UNIQUE NOT NULL,
                token_expiry TIMESTAMP WITH TIME ZONE,

                status VARCHAR DEFAULT 'draft',

                sent_date TIMESTAMP WITH TIME ZONE,
                sent_by VARCHAR,

                reviewed_date TIMESTAMP WITH TIME ZONE,
                contractor_signature_type VARCHAR,
                contractor_signature_data TEXT,
                contractor_signed_date TIMESTAMP WITH TIME ZONE,
                contractor_notes TEXT,

                aventus_signature_type VARCHAR,
                aventus_signature_data TEXT,
                aventus_signed_date TIMESTAMP WITH TIME ZONE,

                validated_date TIMESTAMP WITH TIME ZONE,
                validated_by VARCHAR,

                activated_date TIMESTAMP WITH TIME ZONE,
                activated_by VARCHAR,
                temporary_password VARCHAR,

                declined_date TIMESTAMP WITH TIME ZONE,
                decline_reason TEXT,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))

        # Create index on contractor_id
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contracts_contractor_id
            ON contracts(contractor_id);
        """))

        # Create index on contract_token
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contracts_token
            ON contracts(contract_token);
        """))

        # Create index on status
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contracts_status
            ON contracts(status);
        """))

        conn.commit()
        print("Contract templates and contracts tables created successfully!")

if __name__ == "__main__":
    run_migration()
