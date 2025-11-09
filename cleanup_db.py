"""
Cleanup database - Remove all accounts except superadmin
"""
from app.database import SessionLocal
from app.models.user import User, UserRole

def cleanup_database():
    """Remove all non-superadmin users"""
    print("Starting database cleanup...")

    db = SessionLocal()

    try:
        # Get all non-superadmin users
        non_superadmin_users = db.query(User).filter(
            User.role != UserRole.SUPERADMIN
        ).all()

        if not non_superadmin_users:
            print("[INFO] No non-superadmin users found. Database is clean.")
            return

        print(f"[INFO] Found {len(non_superadmin_users)} non-superadmin users to delete:")
        for user in non_superadmin_users:
            print(f"  - {user.email} ({user.role.value})")

        # Delete all non-superadmin users
        for user in non_superadmin_users:
            db.delete(user)

        db.commit()

        print(f"\n[SUCCESS] Deleted {len(non_superadmin_users)} users")
        print("[OK] Only superadmin account remains")

        # Verify
        remaining_users = db.query(User).all()
        print(f"\n[INFO] Remaining users: {len(remaining_users)}")
        for user in remaining_users:
            print(f"  - {user.email} ({user.role.value})")

    except Exception as e:
        print(f"[ERROR] Error cleaning database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_database()
