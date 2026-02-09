"""
FastAPI Dependencies.

Provides dependency injection for services and common dependencies.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.config.settings import settings
from app.repositories.implementations.contractor_repo import ContractorRepository
from app.repositories.implementations.client_repo import ClientRepository
from app.services.contractor_service import ContractorService
from app.services.notification_service import NotificationService
from app.services.onboarding_service import OnboardingService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        User payload dict

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return {
            "id": int(user_id),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current user and verify they have admin role.

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_contractor_repository(
    db: Session = Depends(get_db),
) -> ContractorRepository:
    """Get contractor repository instance."""
    return ContractorRepository(db)


def get_client_repository(
    db: Session = Depends(get_db),
) -> ClientRepository:
    """Get client repository instance."""
    return ClientRepository(db)


def get_contractor_service(
    repo: ContractorRepository = Depends(get_contractor_repository),
) -> ContractorService:
    """Get contractor service instance."""
    return ContractorService(repo)


def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    return NotificationService()


def get_onboarding_service(
    contractor_repo: ContractorRepository = Depends(get_contractor_repository),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OnboardingService:
    """Get onboarding service instance."""
    return OnboardingService(contractor_repo, notification_service)


# Optional auth - allows public access but provides user if authenticated
async def get_optional_user(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
    ),
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return {
            "id": int(payload.get("sub")),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except jwt.PyJWTError:
        return None
