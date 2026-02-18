from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.third_party import ThirdParty, ThirdPartyDocument
from app.models.contractor import Contractor
from app.models.work_order import WorkOrder
from app.models.quote_sheet import QuoteSheet
from app.schemas.third_party import ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyResponse
from app.models.user import User, UserRole
from app.utils.auth import get_current_active_user, require_role
from app.utils.storage import storage
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/third-parties", tags=["third-parties"])


@router.post("/", response_model=ThirdPartyResponse, status_code=status.HTTP_201_CREATED)
async def create_third_party(
    third_party_data: ThirdPartyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Create a new third party company (Consultant/Admin/Superadmin)
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
    country: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all third party companies
    Optionally filter by country (e.g., UAE, Saudi Arabia)
    Supports aliases: UAE = United Arab Emirates, Saudi = Saudi Arabia
    """
    query = db.query(ThirdParty)

    if not include_inactive:
        query = query.filter(ThirdParty.is_active == True)

    if country:
        # Handle country aliases
        country_aliases = {
            "UAE": ["UAE", "United Arab Emirates"],
            "Saudi": ["Saudi", "Saudi Arabia"],
        }

        # Check if the provided country is an alias key
        if country in country_aliases:
            query = query.filter(ThirdParty.country.in_(country_aliases[country]))
        else:
            query = query.filter(ThirdParty.country == country)

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
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Update a third party company (Consultant/Admin/Superadmin)
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

    # Check for linked records that prevent deletion
    linked = []

    contractor_count = db.query(Contractor).filter(Contractor.third_party_id == third_party_id).count()
    if contractor_count:
        linked.append(f"{contractor_count} contractor(s)")

    work_order_count = db.query(WorkOrder).filter(WorkOrder.third_party_id == third_party_id).count()
    if work_order_count:
        linked.append(f"{work_order_count} work order(s)")

    quote_sheet_count = db.query(QuoteSheet).filter(QuoteSheet.third_party_id == third_party_id).count()
    if quote_sheet_count:
        linked.append(f"{quote_sheet_count} quote sheet(s)")

    if linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete '{third_party.company_name}'. It is linked to {', '.join(linked)}. Remove or reassign these records first."
        )

    db.delete(third_party)
    db.commit()

    return None


@router.post("/{third_party_id}/upload-document")
async def upload_third_party_document(
    third_party_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Upload a document for a third party company (Consultant/Admin/Superadmin)
    """
    third_party = db.query(ThirdParty).filter(ThirdParty.id == third_party_id).first()

    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party company not found"
        )

    # Upload file to storage using custom approach for third parties
    try:
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"third-parties/{third_party_id}/{document_type}_{timestamp}_{unique_id}.{file_ext}"

        # Read file content
        content = await file.read()

        # Upload to Supabase Storage
        response = storage.client.storage.from_(storage.bucket).upload(
            filename,
            content,
            file_options={"content-type": file.content_type}
        )

        # Get public URL
        file_url = storage.client.storage.from_(storage.bucket).get_public_url(filename)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

    # Add document to child table
    doc = ThirdPartyDocument(
        third_party_id=third_party.id,
        document_type=document_type,
        filename=file.filename,
        url=file_url,
        uploaded_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()

    return {"message": "Document uploaded successfully", "url": file_url}


@router.delete("/{third_party_id}/documents/{document_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_third_party_document(
    third_party_id: str,
    document_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Delete a document from a third party company (Admin/Superadmin only)
    """
    docs = (
        db.query(ThirdPartyDocument)
        .filter(ThirdPartyDocument.third_party_id == third_party_id)
        .order_by(ThirdPartyDocument.id)
        .all()
    )

    if document_index >= len(docs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    db.delete(docs[document_index])
    db.commit()

    return None
