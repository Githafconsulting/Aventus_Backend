from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.third_party import ThirdParty
from app.schemas.third_party import ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyResponse
from app.models.user import User, UserRole
from app.utils.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/v1/third-parties", tags=["third-parties"])


@router.post("/", response_model=ThirdPartyResponse, status_code=status.HTTP_201_CREATED)
async def create_third_party(
    third_party_data: ThirdPartyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Create a new third party company (Admin/Superadmin only)
    """
    # Check if company name already exists
    existing = db.query(ThirdParty).filter(ThirdParty.company_name == third_party_data.company_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A third party company with this name already exists"
        )

    third_party = ThirdParty(**third_party_data.model_dump())
    db.add(third_party)
    db.commit()
    db.refresh(third_party)

    return third_party


@router.get("/", response_model=List[ThirdPartyResponse])
async def get_third_parties(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all third party companies
    """
    query = db.query(ThirdParty)

    if not include_inactive:
        query = query.filter(ThirdParty.is_active == True)

    third_parties = query.order_by(ThirdParty.company_name).all()
    return third_parties


@router.get("/{third_party_id}", response_model=ThirdPartyResponse)
async def get_third_party(
    third_party_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific third party company by ID
    """
    third_party = db.query(ThirdParty).filter(ThirdParty.id == third_party_id).first()

    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party company not found"
        )

    return third_party


@router.put("/{third_party_id}", response_model=ThirdPartyResponse)
async def update_third_party(
    third_party_id: str,
    third_party_data: ThirdPartyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Update a third party company (Admin/Superadmin only)
    """
    third_party = db.query(ThirdParty).filter(ThirdParty.id == third_party_id).first()

    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party company not found"
        )

    # Check if updating company name to an existing one
    if third_party_data.company_name and third_party_data.company_name != third_party.company_name:
        existing = db.query(ThirdParty).filter(
            ThirdParty.company_name == third_party_data.company_name,
            ThirdParty.id != third_party_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A third party company with this name already exists"
            )

    # Update fields
    update_data = third_party_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(third_party, field, value)

    db.commit()
    db.refresh(third_party)

    return third_party


@router.delete("/{third_party_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_third_party(
    third_party_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Delete a third party company (Admin/Superadmin only)
    """
    third_party = db.query(ThirdParty).filter(ThirdParty.id == third_party_id).first()

    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party company not found"
        )

    db.delete(third_party)
    db.commit()

    return None
