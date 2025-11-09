"""
Environment Variables Checker
Validates that all required environment variables are set correctly
"""
import sys
from pathlib import Path


def check_env():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")

    if not env_path.exists():
        print("❌ .env file not found!")
        print("📝 Please create .env file from .env.example:")
        print("   cp .env.example .env")
        return False

    print("✓ .env file found")

    # Read .env file
    with open(env_path, 'r') as f:
        env_content = f.read()

    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "RESEND_API_KEY",
        "FROM_EMAIL",
    ]

    missing_vars = []
    placeholder_vars = []

    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
        elif f"{var}=your" in env_content or f"{var}=[YOUR" in env_content:
            placeholder_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        return False

    if placeholder_vars:
        print(f"\n⚠️  Variables with placeholder values: {', '.join(placeholder_vars)}")
        print("   Please update these with actual values")
        return False

    print("✓ All required variables are set")
    print("\n✅ Environment configuration looks good!")
    return True


if __name__ == "__main__":
    if not check_env():
        print("\n💡 Setup Guide:")
        print("1. Copy .env.example to .env")
        print("2. Get Supabase database URL from your project")
        print("3. Get Resend API key from resend.com")
        print("4. Generate a SECRET_KEY using: python -c \"import secrets; print(secrets.token_hex(32))\"")
        sys.exit(1)
    else:
        print("\n🚀 You're ready to run the application!")
        print("   python run.py")
