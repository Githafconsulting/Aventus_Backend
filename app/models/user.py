from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    CONSULTANT = "consultant"
    CLIENT = "client"
    CONTRACTOR = "contractor"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CONTRACTOR)
    phone_number = Column(String, nullable=True)
    profile_photo = Column(String, nullable=True)  # URL to profile photo
    permissions = Column(JSON, nullable=True)  # Role-based permissions
    is_active = Column(Boolean, default=True)
    is_first_login = Column(Boolean, default=True)
    contractor_id = Column(String, nullable=True)  # Link to contractor if role is contractor

    # Superadmin signature (for contract signing)
    signature_type = Column(String, nullable=True)  # "typed" or "drawn"
    signature_data = Column(String, nullable=True)  # Name or base64 image

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
