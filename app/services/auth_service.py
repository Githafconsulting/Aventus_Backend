"""
Authentication Service.

Application service for authentication operations.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import hashlib

from app.domain.token.token import Token
from app.exceptions.auth import AuthenticationError, AuthorizationError
from app.telemetry.logger import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


class AuthService:
    """
    Application service for authentication.

    Provides:
    - User authentication
    - Token generation and validation
    - Password management
    """

    def __init__(self, user_repo, notification_service=None):
        """
        Initialize auth service.

        Args:
            user_repo: User repository
            notification_service: For sending password reset emails
        """
        self.user_repo = user_repo
        self.notifications = notification_service

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with user data and access token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning(
                "Authentication failed: user not found",
                extra={"email": email}
            )
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not self._verify_password(password, user.password_hash):
            logger.warning(
                "Authentication failed: invalid password",
                extra={"email": email}
            )
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Generate access token
        access_token = self._generate_access_token(user)

        # Update last login
        await self.user_repo.update(user.id, {
            "last_login": datetime.utcnow(),
        })

        logger.info(
            "User authenticated",
            extra={"user_id": user.id, "email": email}
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def request_password_reset(self, email: str) -> bool:
        """
        Request password reset.

        Args:
            email: User email

        Returns:
            True if reset email sent
        """
        user = await self.user_repo.get_by_email(email)

        if not user:
            # Don't reveal if user exists
            logger.info(
                "Password reset requested for unknown email",
                extra={"email": email}
            )
            return True

        # Generate reset token
        token = Token.generate(hours=1)

        await self.user_repo.update(user.id, {
            "reset_token": token.value,
            "reset_token_expiry": token.expiry,
        })

        # Send reset email
        if self.notifications:
            await self.notifications.send_password_reset_email(
                email=user.email,
                name=user.name,
                reset_token=token.value,
                expiry_date=token.expiry,
            )

        logger.info(
            "Password reset requested",
            extra={"user_id": user.id}
        )

        return True

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Reset password using token.

        Args:
            token: Reset token
            new_password: New password

        Returns:
            True if password reset

        Raises:
            AuthenticationError: If token is invalid
        """
        user = await self.user_repo.first_by(reset_token=token)

        if not user:
            raise AuthenticationError("Invalid or expired reset token")

        # Validate token
        if user.reset_token_expiry < datetime.utcnow():
            raise AuthenticationError("Reset token has expired")

        # Hash new password
        password_hash = self._hash_password(new_password)

        # Update user
        await self.user_repo.update(user.id, {
            "password_hash": password_hash,
            "reset_token": None,
            "reset_token_expiry": None,
            "password_changed_at": datetime.utcnow(),
        })

        logger.info(
            "Password reset completed",
            extra={"user_id": user.id}
        )

        return True

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change password for authenticated user.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed

        Raises:
            AuthenticationError: If current password is wrong
        """
        user = await self.user_repo.get(user_id)

        if not user:
            raise AuthenticationError("User not found")

        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        # Hash new password
        password_hash = self._hash_password(new_password)

        await self.user_repo.update(user_id, {
            "password_hash": password_hash,
            "password_changed_at": datetime.utcnow(),
        })

        logger.info(
            "Password changed",
            extra={"user_id": user_id}
        )

        return True

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        # In production, use bcrypt or argon2
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, hash_value = password_hash.split("$")
            hash_obj = hashlib.sha256((password + salt).encode())
            return hash_obj.hexdigest() == hash_value
        except (ValueError, AttributeError):
            return False

    def _generate_access_token(self, user) -> str:
        """Generate JWT access token."""
        # Import here to avoid circular imports
        import jwt

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24),
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm="HS256",
        )

    @staticmethod
    def generate_temporary_password() -> str:
        """Generate a temporary password for new users."""
        return secrets.token_urlsafe(12)
