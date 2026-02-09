"""
Application Settings.

Pydantic-based settings management with environment variable support.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses pydantic-settings for validation and type coercion.
    """

    # Application
    app_name: str = Field(default="Aventus HR API", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Company Info (for emails/PDFs)
    company_name: str = Field(default="Aventus HR", env="COMPANY_NAME")
    logo_url: str = Field(default="", env="LOGO_URL")
    logo_path: Optional[str] = Field(default=None, env="LOGO_PATH")
    support_email: str = Field(default="support@aventushr.com", env="SUPPORT_EMAIL")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")

    # Security / JWT
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    jwt_secret: str = Field(default="", env="JWT_SECRET")  # Falls back to secret_key
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=480, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_expiry_hours: int = Field(default=24, env="JWT_EXPIRY_HOURS")
    contract_token_expiry_hours: int = Field(default=72, env="CONTRACT_TOKEN_EXPIRY_HOURS")

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS",
    )

    # Frontend URLs
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    contract_signing_url: str = Field(
        default="http://localhost:3000/contract/sign",
        env="CONTRACT_SIGNING_URL",
    )
    password_reset_url: str = Field(
        default="http://localhost:3000/reset-password",
        env="PASSWORD_RESET_URL",
    )

    # AWS (Email via Lambda/SES)
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="me-central-1", env="AWS_REGION")
    email_lambda_function_name: str = Field(default="", env="EMAIL_LAMBDA_FUNCTION_NAME")
    from_email: str = Field(default="noreply@aventushr.com", env="FROM_EMAIL")

    # Supabase (Storage)
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_KEY")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    supabase_bucket: str = Field(default="contractor-documents", env="SUPABASE_BUCKET")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # Allow extra fields
        extra = "allow"

    @property
    def effective_jwt_secret(self) -> str:
        """Get JWT secret, falling back to secret_key if not set."""
        return self.jwt_secret if self.jwt_secret else self.secret_key


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to avoid reading env vars on every request.
    """
    return Settings()


# Singleton instance
settings = get_settings()
