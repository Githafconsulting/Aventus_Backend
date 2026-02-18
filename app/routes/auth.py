from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import uuid
from app.database import get_db
from app.models.user import User, UserRole
from app.models.contractor import Contractor
from app.models.proposal import Proposal
from app.models.work_order import WorkOrder
from app.models.quote_sheet import QuoteSheet
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
from app.utils.storage import storage
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


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token - returns a new JWT token
    Call this before current token expires to maintain session
    """
    # Verify user is still active (unless first login)
    if not current_user.is_active and not current_user.is_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.email, "role": current_user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information (works for both active and inactive first-time users)
    For contractors, includes their photo from contractor documents if no profile photo is set.
    """
    # If user is a contractor and doesn't have a profile photo, get it from contractor record
    if current_user.contractor_id and not current_user.profile_photo:
        contractor = db.query(Contractor).filter(Contractor.id == current_user.contractor_id).first()
        if contractor and contractor.photo_document:
            # Temporarily set the profile_photo for the response
            current_user.profile_photo = contractor.photo_document

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


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: CreateUserRequest,
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Update a user (admin cannot update superadmin)
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Admin cannot update superadmin accounts
    if current_user.role == UserRole.ADMIN and user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot update superadmin accounts"
        )

    # Update fields
    if user_data.name:
        user.name = user_data.name
    if user_data.email:
        # Check if email is already taken by another user
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered to another user"
            )
        user.email = user_data.email
    if user_data.phone_number is not None:
        user.phone_number = user_data.phone_number
    if user_data.role:
        # Admin cannot promote user to superadmin
        if current_user.role == UserRole.ADMIN and user_data.role == "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin users cannot create superadmin accounts"
            )
        user.role = UserRole(user_data.role)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.profile_photo is not None:
        user.profile_photo = user_data.profile_photo
    if user_data.permissions is not None:
        user.permissions = user_data.permissions

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user


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

    # Check for linked records that prevent deletion
    linked = []

    contractor_count = db.query(Contractor).filter(Contractor.consultant_id == user_id).count()
    if contractor_count:
        linked.append(f"{contractor_count} contractor(s)")

    proposal_count = db.query(Proposal).filter(Proposal.consultant_id == user_id).count()
    if proposal_count:
        linked.append(f"{proposal_count} proposal(s)")

    work_order_count = db.query(WorkOrder).filter(WorkOrder.created_by == user_id).count()
    if work_order_count:
        linked.append(f"{work_order_count} work order(s)")

    quote_sheet_count = db.query(QuoteSheet).filter(QuoteSheet.consultant_id == user_id).count()
    if quote_sheet_count:
        linked.append(f"{quote_sheet_count} quote sheet(s)")

    if linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete '{user.name}'. They are linked to {', '.join(linked)}. Remove or reassign these records first."
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/upload-photo")
async def upload_user_photo(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Upload a profile photo for a user
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP"
        )

    # Check file size (5MB max)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB"
        )
    # Reset file position for upload
    await file.seek(0)

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Admin cannot update superadmin photos
    if current_user.role == UserRole.ADMIN and user.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot update superadmin accounts"
        )

    try:
        # Upload to Supabase Storage
        photo_url = await storage.upload_document(file, f"users/{user_id}", "profile_photo")

        # Update user profile photo
        user.profile_photo = photo_url
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return {"profile_photo": photo_url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}"
        )


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

    # Return signed contracts from child table
    contracts_signed = [
        {
            "contractor_id": sc.contractor_id,
            "contractor_name": sc.contractor_name,
            "contract_url": sc.contract_url,
            "signed_date": sc.signed_date.isoformat() if sc.signed_date else None,
        }
        for sc in (user.signed_contracts or [])
    ]

    return {
        "contracts": contracts_signed,
        "total": len(contracts_signed)
    }
