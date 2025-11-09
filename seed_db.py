"""
Database seed script
Creates initial admin users for testing
"""
import sys
import uuid
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash


def seed_database():
    """Seed database with initial users"""
    print("Starting database seeding...")

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")

    # Create database session
    db = SessionLocal()

    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"[WARNING] Database already has {existing_users} users. Skipping seed.")
            return

        # Create test users - Only superadmin for initial setup
        users_data = [
            {
                "name": "Super Admin",
                "email": "superadmin@aventus.com",
                "password": "superadmin123",
                "role": UserRole.SUPERADMIN
            },
        ]

        created_users = []
        for user_data in users_data:
            user = User(
                id=str(uuid.uuid4()),
                name=user_data["name"],
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                is_first_login=False
            )
            db.add(user)
            created_users.append(user_data)

        db.commit()

        print("\n[OK] Successfully created users:")
        print("-" * 60)
        for user in created_users:
            print(f"Role: {user['role'].value}")
            print(f"Email: {user['email']}")
            print(f"Password: {user['password']}")
            print("-" * 60)

        print("\n[SUCCESS] Database seeding completed successfully!")

    except Exception as e:
        print(f"[ERROR] Error seeding database: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
