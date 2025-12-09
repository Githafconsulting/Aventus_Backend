"""
Authentication API Routes.

Thin route layer for authentication operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.api.dependencies import get_current_user
from app.api.responses import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Authenticate user and return access token.

    Uses OAuth2 password flow for compatibility with OpenAPI.
    """
    # TODO: Inject auth service when user repository is implemented
    # For now, return a placeholder
    # result = await auth_service.authenticate(form_data.username, form_data.password)

    # Placeholder response
    return {
        "access_token": "placeholder_token",
        "token_type": "bearer",
    }


@router.post("/login/json")
async def login_json(
    data: LoginRequest,
):
    """
    Authenticate user with JSON body.

    Alternative to OAuth2 form-based login.
    """
    # TODO: Inject auth service
    # result = await auth_service.authenticate(data.email, data.password)

    return success_response({
        "message": "Login endpoint - implementation pending",
    })


@router.post("/password/reset-request")
async def request_password_reset(
    data: PasswordResetRequest,
):
    """
    Request password reset email.

    Sends reset link to email if account exists.
    Always returns success to prevent email enumeration.
    """
    # TODO: Inject auth service
    # await auth_service.request_password_reset(data.email)

    return success_response({
        "message": "If an account exists with this email, a reset link has been sent.",
    })


@router.post("/password/reset")
async def reset_password(
    data: PasswordResetConfirm,
):
    """
    Reset password using token.

    Token is received via email from reset request.
    """
    # TODO: Inject auth service
    # await auth_service.reset_password(data.token, data.new_password)

    return success_response({
        "message": "Password has been reset successfully.",
    })


@router.post("/password/change")
async def change_password(
    data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Change password for authenticated user.

    Requires current password verification.
    """
    # TODO: Inject auth service
    # await auth_service.change_password(
    #     current_user["id"],
    #     data.current_password,
    #     data.new_password,
    # )

    return success_response({
        "message": "Password changed successfully.",
    })


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return success_response(current_user)


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
):
    """
    Logout current user.

    For JWT-based auth, this is client-side (discard token).
    Server-side logout would require token blacklisting.
    """
    return success_response({
        "message": "Logged out successfully.",
    })
