from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server Configuration
    app_name: str = "Aventus HR Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours - for form-heavy app
    refresh_token_expire_days: int = 7

    # Database
    database_url: str

    # Email Service (Resend)
    resend_api_key: str
    from_email: str
    company_name: str = "Aventus HR"
    logo_url: str = "http://localhost:3000/av-logo.png"

    # Frontend URLs
    frontend_url: str = "http://localhost:3000"
    contract_signing_url: str = "http://localhost:3000/contract/sign"
    password_reset_url: str = "http://localhost:3000/reset-password"

    # Token Expiry
    contract_token_expiry_hours: int = 72

    # Supabase Storage
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_bucket: str = "contractor-documents"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# Global settings instance
settings = Settings()
