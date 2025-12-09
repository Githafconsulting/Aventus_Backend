"""Add summary calculation fields to contractors table"""
from sqlalchemy import text
from app.database import engine

def upgrade():
    """Add contractor_total_fixed_costs and estimated_monthly_gp columns to contractors table"""
    with engine.connect() as conn:
        # Add contractor_total_fixed_costs column
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS contractor_total_fixed_costs VARCHAR;
        """))

        # Add estimated_monthly_gp column
        conn.execute(text("""
            ALTER TABLE contractors
            ADD COLUMN IF NOT EXISTS estimated_monthly_gp VARCHAR;
        """))

        conn.commit()
        print("[SUCCESS] Added contractor_total_fixed_costs and estimated_monthly_gp columns to contractors table")

def downgrade():
    """Remove contractor_total_fixed_costs and estimated_monthly_gp columns from contractors table"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE contractors
            DROP COLUMN IF EXISTS contractor_total_fixed_costs;
        """))

        conn.execute(text("""
            ALTER TABLE contractors
            DROP COLUMN IF EXISTS estimated_monthly_gp;
        """))

        conn.commit()
        print("[SUCCESS] Removed contractor_total_fixed_costs and estimated_monthly_gp columns from contractors table")

if __name__ == "__main__":
    print("Running migration: Add summary fields to contractors")
    upgrade()
    print("Migration completed successfully")
