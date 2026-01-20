from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.quote_sheet import QuoteSheet, QuoteSheetStatus
from app.models.contractor import Contractor
from app.models.third_party import ThirdParty
from app.models.user import User, UserRole
from app.schemas.quote_sheet import QuoteSheetCreate, QuoteSheetUpdate, QuoteSheetResponse, QuoteSheetUpload
from app.utils.auth import get_current_active_user
from app.utils.email import send_quote_sheet_request_email
from app.utils.storage import storage
from app.utils.quote_sheet_pdf_generator import generate_quote_sheet_pdf
from datetime import datetime, timedelta
import uuid
import secrets
from pydantic import BaseModel

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

    # Update contractor status to PENDING_CDS_CS so consultant can fill CDS & CS form
    from app.models.contractor import ContractorStatus
    contractor = db.query(Contractor).filter(Contractor.id == quote_sheet.contractor_id).first()
    if contractor and contractor.status in [
        ContractorStatus.DOCUMENTS_UPLOADED,
        ContractorStatus.PENDING_THIRD_PARTY_RESPONSE,
        ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
    ]:
        # Change status to PENDING_CDS_CS - will change to PENDING_REVIEW after costing sheet submission
        contractor.status = ContractorStatus.PENDING_CDS_CS
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


@router.get("/summary", response_model=List[dict])
async def get_quote_sheets_summary(
    status_filter: Optional[QuoteSheetStatus] = None,
    contractor_id: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get quote sheets with minimal fields for dashboard/list views.
    Much faster than full list - only fetches required columns.
    Supports pagination with page and limit parameters.
    """
    # Only select the columns needed for dashboard display
    query = db.query(
        QuoteSheet.id,
        QuoteSheet.contractor_id,
        QuoteSheet.contractor_name,
        QuoteSheet.third_party_company_name,
        QuoteSheet.status,
        QuoteSheet.total_invoice_amount,
        QuoteSheet.created_at,
        QuoteSheet.submitted_at
    )

    # Consultants can only see their own quote sheets
    if current_user.role == UserRole.CONSULTANT:
        query = query.filter(QuoteSheet.consultant_id == current_user.id)

    if status_filter:
        query = query.filter(QuoteSheet.status == status_filter)

    if contractor_id:
        query = query.filter(QuoteSheet.contractor_id == contractor_id)

    # Apply pagination
    offset = (page - 1) * limit
    results = query.order_by(QuoteSheet.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to list of dicts
    return [
        {
            "id": r.id,
            "contractor_id": r.contractor_id,
            "contractor_name": r.contractor_name,
            "third_party_company_name": r.third_party_company_name,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "total_invoice_amount": r.total_invoice_amount,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None
        }
        for r in results
    ]


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


# ============== NEW ENDPOINTS FOR FORM SUBMISSION ==============

class QuoteSheetFormData(BaseModel):
    """Schema for Quote Sheet form submission by third party"""
    # (A) Employee Contract Information
    employee_name: Optional[str] = None
    role: Optional[str] = None
    date_of_hiring: Optional[str] = None
    nationality: Optional[str] = None
    family_status: Optional[str] = None
    num_children: Optional[str] = None

    # (B) Employee Cash Benefits
    basic_salary: Optional[float] = None
    transport_allowance: Optional[float] = None
    housing_allowance: Optional[float] = None
    rate_per_day: Optional[float] = None
    working_days_month: Optional[float] = None
    aed_to_sar: Optional[float] = None
    gross_salary: Optional[float] = None

    # (C) Employee Cost
    vacation_one_time: Optional[float] = None
    vacation_annual: Optional[float] = None
    vacation_monthly: Optional[float] = None
    flight_one_time: Optional[float] = None
    flight_annual: Optional[float] = None
    flight_monthly: Optional[float] = None
    eosb_one_time: Optional[float] = None
    eosb_annual: Optional[float] = None
    eosb_monthly: Optional[float] = None
    gosi_one_time: Optional[float] = None
    gosi_annual: Optional[float] = None
    gosi_monthly: Optional[float] = None
    medical_one_time: Optional[float] = None
    medical_annual: Optional[float] = None
    medical_monthly: Optional[float] = None
    exit_reentry_one_time: Optional[float] = None
    exit_reentry_annual: Optional[float] = None
    exit_reentry_monthly: Optional[float] = None
    salary_transfer_one_time: Optional[float] = None
    salary_transfer_annual: Optional[float] = None
    salary_transfer_monthly: Optional[float] = None
    sick_leave_one_time: Optional[float] = None
    sick_leave_annual: Optional[float] = None
    sick_leave_monthly: Optional[float] = None
    employee_cost_one_time_total: Optional[float] = None
    employee_cost_annual_total: Optional[float] = None
    employee_cost_monthly_total: Optional[float] = None

    # (D) Family Cost
    family_medical_one_time: Optional[float] = None
    family_medical_annual: Optional[float] = None
    family_medical_monthly: Optional[float] = None
    family_flight_one_time: Optional[float] = None
    family_flight_annual: Optional[float] = None
    family_flight_monthly: Optional[float] = None
    family_exit_one_time: Optional[float] = None
    family_exit_annual: Optional[float] = None
    family_exit_monthly: Optional[float] = None
    family_joining_one_time: Optional[float] = None
    family_joining_annual: Optional[float] = None
    family_joining_monthly: Optional[float] = None
    family_visa_one_time: Optional[float] = None
    family_visa_annual: Optional[float] = None
    family_visa_monthly: Optional[float] = None
    family_levy_one_time: Optional[float] = None
    family_levy_annual: Optional[float] = None
    family_levy_monthly: Optional[float] = None
    family_cost_one_time_total: Optional[float] = None
    family_cost_annual_total: Optional[float] = None
    family_cost_monthly_total: Optional[float] = None

    # (E) Government Related Charges
    sce_one_time: Optional[float] = None
    sce_annual: Optional[float] = None
    sce_monthly: Optional[float] = None
    medical_test_one_time: Optional[float] = None
    medical_test_annual: Optional[float] = None
    medical_test_monthly: Optional[float] = None
    visa_cost_one_time: Optional[float] = None
    visa_cost_annual: Optional[float] = None
    visa_cost_monthly: Optional[float] = None
    ewakala_one_time: Optional[float] = None
    ewakala_annual: Optional[float] = None
    ewakala_monthly: Optional[float] = None
    chamber_mofa_one_time: Optional[float] = None
    chamber_mofa_annual: Optional[float] = None
    chamber_mofa_monthly: Optional[float] = None
    iqama_one_time: Optional[float] = None
    iqama_annual: Optional[float] = None
    iqama_monthly: Optional[float] = None
    saudi_admin_one_time: Optional[float] = None
    saudi_admin_annual: Optional[float] = None
    saudi_admin_monthly: Optional[float] = None
    ajeer_one_time: Optional[float] = None
    ajeer_annual: Optional[float] = None
    ajeer_monthly: Optional[float] = None
    govt_cost_one_time_total: Optional[float] = None
    govt_cost_annual_total: Optional[float] = None
    govt_cost_monthly_total: Optional[float] = None

    # (F) Mobilization Cost
    visa_processing_one_time: Optional[float] = None
    visa_processing_annual: Optional[float] = None
    visa_processing_monthly: Optional[float] = None
    recruitment_one_time: Optional[float] = None
    recruitment_annual: Optional[float] = None
    recruitment_monthly: Optional[float] = None
    joining_ticket_one_time: Optional[float] = None
    joining_ticket_annual: Optional[float] = None
    joining_ticket_monthly: Optional[float] = None
    relocation_one_time: Optional[float] = None
    relocation_annual: Optional[float] = None
    relocation_monthly: Optional[float] = None
    other_cost_one_time: Optional[float] = None
    other_cost_annual: Optional[float] = None
    other_cost_monthly: Optional[float] = None
    mobilization_one_time_total: Optional[float] = None
    mobilization_annual_total: Optional[float] = None
    mobilization_monthly_total: Optional[float] = None

    # Grand Totals
    total_one_time: Optional[float] = None
    total_annual: Optional[float] = None
    total_monthly: Optional[float] = None
    fnrco_service_charge: Optional[float] = None
    total_invoice_amount: Optional[float] = None

    # Remarks
    remarks_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@router.post("/submit/{token}")
async def submit_quote_sheet_form(
    token: str,
    form_data: QuoteSheetFormData,
    db: Session = Depends(get_db)
):
    """
    Submit Quote Sheet form data by third party using their token.
    This generates a PDF and saves all the form data.
    """
    # Find quote sheet by token
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.upload_token == token).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token"
        )

    # Check token expiry
    if datetime.utcnow() > quote_sheet.token_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )

    # Update all form fields
    form_dict = form_data.model_dump(exclude_unset=True)
    for field, value in form_dict.items():
        if hasattr(quote_sheet, field):
            setattr(quote_sheet, field, value)

    # Set issued date if not provided
    if not quote_sheet.issued_date:
        quote_sheet.issued_date = datetime.now().strftime('%B %d, %Y')

    # Generate PDF
    try:
        # Prepare data for PDF generation
        pdf_data = {
            **form_dict,
            'contractor_name': quote_sheet.contractor_name,
            'third_party_company_name': quote_sheet.third_party_company_name,
            'issued_date': quote_sheet.issued_date,
        }

        pdf_buffer = generate_quote_sheet_pdf(pdf_data)

        # Upload PDF to storage
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"quote-sheets/{quote_sheet.id}/quote_sheet_{timestamp}_{unique_id}.pdf"

        response = storage.client.storage.from_(storage.bucket).upload(
            filename,
            pdf_buffer.getvalue(),
            file_options={"content-type": "application/pdf"}
        )

        file_url = storage.client.storage.from_(storage.bucket).get_public_url(filename)

        quote_sheet.document_url = file_url
        quote_sheet.document_filename = f"Quote_Sheet_{quote_sheet.contractor_name}_{timestamp}.pdf"

    except Exception as e:
        print(f"Error generating/uploading PDF: {e}")
        # Continue without PDF if it fails

    # Update status and timestamps
    quote_sheet.status = QuoteSheetStatus.SUBMITTED
    quote_sheet.submitted_at = datetime.utcnow()

    # Update contractor status
    from app.models.contractor import ContractorStatus
    contractor = db.query(Contractor).filter(Contractor.id == quote_sheet.contractor_id).first()
    if contractor:
        contractor.status = ContractorStatus.PENDING_CDS_CS
        contractor.third_party_response_received_date = datetime.utcnow()
        if quote_sheet.document_url:
            contractor.third_party_document = quote_sheet.document_url
        contractor.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(quote_sheet)

    return {
        "message": "Quote sheet submitted successfully",
        "quote_sheet_id": quote_sheet.id,
        "document_url": quote_sheet.document_url
    }


@router.get("/preview-pdf/{token}")
async def preview_quote_sheet_pdf(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Preview Quote Sheet as PDF (public endpoint for third parties)
    """
    quote_sheet = db.query(QuoteSheet).filter(QuoteSheet.upload_token == token).first()

    if not quote_sheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token"
        )

    # Generate PDF with current data
    pdf_data = {
        'contractor_name': quote_sheet.contractor_name,
        'third_party_company_name': quote_sheet.third_party_company_name,
        'issued_date': quote_sheet.issued_date or datetime.now().strftime('%B %d, %Y'),
        'employee_name': quote_sheet.employee_name,
        'role': quote_sheet.role,
        'date_of_hiring': quote_sheet.date_of_hiring,
        'nationality': quote_sheet.nationality,
        'family_status': quote_sheet.family_status,
        'num_children': quote_sheet.num_children,
        'basic_salary': quote_sheet.basic_salary,
        'transport_allowance': quote_sheet.transport_allowance,
        'housing_allowance': quote_sheet.housing_allowance,
        'rate_per_day': quote_sheet.rate_per_day,
        'working_days_month': quote_sheet.working_days_month,
        'aed_to_sar': quote_sheet.aed_to_sar,
        'gross_salary': quote_sheet.gross_salary,
        # ... all other fields would be included here
    }

    # Get all fields from model
    for column in QuoteSheet.__table__.columns:
        if column.name not in pdf_data:
            pdf_data[column.name] = getattr(quote_sheet, column.name, None)

    pdf_buffer = generate_quote_sheet_pdf(pdf_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=quote_sheet_preview.pdf"}
    )


@router.get("/download-pdf/{quote_sheet_id}")
async def download_quote_sheet_pdf(
    quote_sheet_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download Quote Sheet PDF (authenticated endpoint)
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
            detail="Not authorized to download this quote sheet"
        )

    # Generate PDF with all data
    pdf_data = {}
    for column in QuoteSheet.__table__.columns:
        pdf_data[column.name] = getattr(quote_sheet, column.name, None)

    pdf_buffer = generate_quote_sheet_pdf(pdf_data)

    filename = f"Quote_Sheet_{quote_sheet.contractor_name or 'Unknown'}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
