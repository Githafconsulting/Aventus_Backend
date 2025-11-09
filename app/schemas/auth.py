from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: bool
    is_first_login: bool
    contractor_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None
    role: str  # "admin" or "consultant"
    permissions: Optional[dict] = None
    is_active: bool = True
