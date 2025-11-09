"""
Reset database - Drop all tables and recreate
"""
from app.database import engine, Base
from app.models.user import User
from app.models.contractor import Contractor

def reset_database():
    """Drop all tables and recreate"""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("[OK] All tables dropped")

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created")

    print("\n[SUCCESS] Database reset completed!")
    print("Now run: python seed_db.py")

if __name__ == "__main__":
    reset_database()
