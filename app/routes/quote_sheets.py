from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.quote_sheet import QuoteSheet, QuoteSheetStatus
from app.models.contractor import Contractor
from app.models.third_party import ThirdParty
from app.models.user import User, UserRole
from app.schemas.quote_sheet import QuoteSheetCreate, QuoteSheetUpdate, QuoteSheetResponse, QuoteSheetUpload
from app.utils.auth import get_current_active_user
from app.utils.email import send_quote_sheet_request_email
from app.utils.storage import storage
from datetime import datetime, timedelta
import uuid
import secrets

router = APIRouter(prefix="/api/v1/quote-sheets", tags=["quote-sheets"])


def generate_upload_token() -> str:
    """Generate secure random token for quote sheet upload"""
    return secrets.token_urlsafe(32)


@router.post("/request", response_model=QuoteSheetResponse, status_code=status.HTTP_201_CREATED)
async def request_quote_sheet(
    quote_sheet_data: QuoteSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Request a quote sheet from a third party
    Sends email with upload link
    """
    # Verify contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == quote_sheet_data.contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify third party exists
    third_party = db.query(ThirdParty).filter(ThirdParty.id == quote_sheet_data.third_party_id).first()
    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party not found"
        )

    # Generate upload token (valid for 7 days)
    upload_token = generate_upload_token()
    token_expiry = datetime.utcnow() + timedelta(days=7)

    # Create quote sheet request
    quote_sheet_dict = quote_sheet_data.model_dump()
    quote_sheet = QuoteSheet(
        **quote_sheet_dict,
        consultant_id=current_user.id,
        upload_token=upload_token,
        token_expiry=token_expiry,
        contractor_name=contractor.full_name,
        third_party_company_name=third_party.company_name
    )

    db.add(quote_sheet)
    db.commit()
    db.refresh(quote_sheet)

    # Send email to third party
    if third_party.contact_person_email:
        send_quote_sheet_request_email(
            third_party_email=third_party.contact_person_email,
            third_party_company_name=third_party.company_name,
            contractor_name=contractor.full_name,
            upload_token=upload_token,
            consultant_name=current_user.full_name
        )

    return quote_sheet


@router.get("/public/{token}")
async def get_quote_sheet_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get quote sheet details by token (public endpoint for third parties)
    """
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.upload_token == token).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid upload token"
        )

    # Check token expiry
    if datetime.utcnow() > quote_sheet.token_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload token has expired"
        )

    return {
        "contractor_name": quote_sheet.contractor_name,
        "third_party_company_name": quote_sheet.third_party_company_name,
        "status": quote_sheet.status,
        "created_at": quote_sheet.created_at,
        "token_expiry": quote_sheet.token_expiry
    }


@router.post("/upload/{token}")
async def upload_quote_sheet(
    token: str,
    file: UploadFile = File(...),
    proposed_rate: Optional[float] = None,
    currency: Optional[str] = "AED",
    payment_terms: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload quote sheet document using the token (public endpoint for third parties)
    """
    # Find quote sheet by token
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.upload_token == token).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid upload token"
        )

    # Check token expiry
    if datetime.utcnow() > quote_sheet.token_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload token has expired"
        )

    # Upload file to storage
    try:
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"quote-sheets/{quote_sheet.id}/quote_sheet_{timestamp}_{unique_id}.{file_ext}"

        content = await file.read()

        response = storage.client.storage.from_(storage.bucket).upload(
            filename,
            content,
            file_options={"content-type": file.content_type}
        )

        file_url = storage.client.storage.from_(storage.bucket).get_public_url(filename)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

    # Update quote sheet
    quote_sheet.document_url = file_url
    quote_sheet.document_filename = file.filename
    quote_sheet.proposed_rate = proposed_rate
    quote_sheet.currency = currency
    quote_sheet.payment_terms = payment_terms
    quote_sheet.notes = notes
    quote_sheet.status = QuoteSheetStatus.UPLOADED
    quote_sheet.uploaded_at = datetime.utcnow()

    # Update contractor status and add document - move from pending_third_party_response to documents_uploaded
    # Consultant will then fill CDS & CS form, which moves it to pending_review
    from app.models.contractor import ContractorStatus
    contractor = db.query(Contractor).filter(Contractor.id == quote_sheet.contractor_id).first()
    if contractor and contractor.status == ContractorStatus.PENDING_THIRD_PARTY_RESPONSE:
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED
        contractor.third_party_response_received_date = datetime.utcnow()
        contractor.third_party_document = file_url  # Add quote sheet to contractor documents
        contractor.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(quote_sheet)

    return {"message": "Quote sheet uploaded successfully", "quote_sheet_id": quote_sheet.id}


@router.get("/", response_model=List[QuoteSheetResponse])
async def get_quote_sheets(
    status_filter: Optional[QuoteSheetStatus] = None,
    contractor_id: Optional[str] = None,
    third_party_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all quote sheets with optional filters
    """
    query = db.query(QuoteSheet)

    # Consultants can only see their own quote sheets
    if current_user.role == UserRole.CONSULTANT:
        query = query.filter(QuoteSheet.consultant_id == current_user.id)

    if status_filter:
        query = query.filter(QuoteSheet.status == status_filter)

    if contractor_id:
        query = query.filter(QuoteSheet.contractor_id == contractor_id)

    if third_party_id:
        query = query.filter(QuoteSheet.third_party_id == third_party_id)

    quote_sheets = query.order_by(QuoteSheet.created_at.desc()).all()
    return quote_sheets


@router.get("/{quote_sheet_id}", response_model=QuoteSheetResponse)
async def get_quote_sheet(
    quote_sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific quote sheet by ID
    """
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.id == quote_sheet_id).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote sheet not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and quote_sheet.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this quote sheet"
        )

    return quote_sheet


@router.put("/{quote_sheet_id}", response_model=QuoteSheetResponse)
async def update_quote_sheet(
    quote_sheet_id: str,
    quote_sheet_data: QuoteSheetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a quote sheet (consultant/admin only)
    """
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.id == quote_sheet_id).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote sheet not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and quote_sheet.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this quote sheet"
        )

    # Update fields
    update_data = quote_sheet_data.model_dump(exclude_unset=True)

    # If status is being changed to REVIEWED, set reviewed_at
    if "status" in update_data and update_data["status"] == QuoteSheetStatus.REVIEWED:
        quote_sheet.reviewed_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(quote_sheet, field, value)

    db.commit()
    db.refresh(quote_sheet)

    return quote_sheet


@router.delete("/{quote_sheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote_sheet(
    quote_sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a quote sheet (admin/superadmin only)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete quote sheets"
        )

    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.id == quote_sheet_id).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote sheet not found"
        )

    db.delete(quote_sheet)
    db.commit()

    return None
