from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import uuid
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserResponse, UserLogin, PasswordReset, CreateUserRequest
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_active_user,
    require_role,
    generate_temp_password
)
from app.utils.email import send_activation_email
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - returns JWT access token
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Allow inactive users to login ONLY if it's their first login (to reset password)
    if not user.is_active and not user.is_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login-json", response_model=Token)
async def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login endpoint with JSON body - returns JWT access token
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Allow inactive users to login ONLY if it's their first login (to reset password)
    if not user.is_active and not user.is_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information (works for both active and inactive first-time users)
    """
    return current_user


@router.post("/reset-password")
async def reset_password(
    password_data: PasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset password for current user (works for both active and inactive first-time users)
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password and activate account
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.is_first_login = False
    current_user.is_active = True  # Activate account after password reset
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Create a new user (superadmin can create all, admin can create all except superadmin)
    """
    # Validate role
    valid_roles = ["admin", "consultant", "client", "contractor"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(valid_roles)}"
        )

    # Admin cannot create superadmin accounts
    if current_user.role == UserRole.ADMIN and user_data.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot create superadmin accounts"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Generate temporary password
    temp_password = generate_temp_password()

    # Map role string to UserRole enum
    role_mapping = {
        "admin": UserRole.ADMIN,
        "consultant": UserRole.CONSULTANT,
        "client": UserRole.CLIENT,
        "contractor": UserRole.CONTRACTOR
    }

    # Create new user - INACTIVE until they reset their password
    new_user = User(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(temp_password),
        role=role_mapping[user_data.role],
        phone_number=user_data.phone_number,
        profile_photo=user_data.profile_photo,
        permissions=user_data.permissions,
        is_active=False,  # User starts as inactive
        is_first_login=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send activation email with temporary password
    email_sent = False
    try:
        email_sent = send_activation_email(
            contractor_email=new_user.email,
            contractor_name=new_user.name,
            temporary_password=temp_password
        )
        if email_sent:
            print(f"[SUCCESS] Activation email sent to {new_user.email}")
        else:
            print(f"[WARNING] Email sending returned False for {new_user.email}")
    except Exception as e:
        # Log error but don't fail the user creation
        print(f"[ERROR] Failed to send activation email to {new_user.email}: {str(e)}")

    return new_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    List all users (superadmin sees all, admin sees all except superadmin)
    """
    query = db.query(User)

    # Admin cannot see superadmin accounts
    if current_user.role == UserRole.ADMIN:
        query = query.filter(User.role != UserRole.SUPERADMIN)

    users = query.all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin cannot delete superadmin)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Admin cannot delete superadmin accounts
    if current_user.role == UserRole.ADMIN and user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot delete superadmin accounts"
        )

    # Users cannot delete themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.get("/my-contracts")
async def get_my_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin"]))
):
    """
    Get all contracts signed by the current superadmin
    Only superadmins can access this endpoint
    """
    # Get current user with latest data
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Return contracts signed array (or empty array if None)
    contracts_signed = user.contracts_signed or []

    return {
        "contracts": contracts_signed,
        "total": len(contracts_signed)
    }
