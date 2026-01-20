# Contractors API routes
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uuid
import json

from app.database import get_db
from app.models.contractor import Contractor, ContractorStatus, OnboardingRoute
from app.models.third_party import ThirdParty
from app.models.user import User, UserRole
from app.models.quote_sheet import QuoteSheet, QuoteSheetStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.client import Client
from app.schemas.contractor import (
    ContractorResponse,
    ContractorDetailResponse,
    SignatureSubmission,
    ContractorInitialCreate,
    CostingSheetData,
    DocumentUploadData,
    SuperadminSignatureData,
    ContractorApproval,
    DocumentResponse,
    RouteSelection,
    ThirdPartyRequest,
    QuoteSheetRequest,
    COHFData,
    COHFSubmission,
    COHFEmailData
)
from app.utils.auth import (
    get_current_active_user,
    require_role,
    generate_unique_token,
    generate_temp_password,
    get_password_hash
)
from app.utils.email import (
    send_contract_email,
    send_activation_email,
    send_document_upload_email,
    send_documents_uploaded_notification,
    send_review_notification,
    send_third_party_contractor_request,
    send_work_order_to_client
)
from app.utils.contract_template import populate_contract_template
from app.utils.contract_pdf_generator import generate_consultant_contract_pdf
from app.utils.work_order_pdf_generator import generate_work_order_pdf
from app.utils.cohf_pdf_generator import generate_cohf_pdf
from app.utils.storage import upload_file
from app.config import settings
from fastapi.responses import StreamingResponse, RedirectResponse

router = APIRouter(prefix="/contractors", tags=["Contractors"])


@router.post("/initial", response_model=ContractorDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_contractor_initial(
    contractor_data: ContractorInitialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    NEW Step 1: Consultant creates initial contractor entry (name, email, phone)
    and sends document upload link to contractor
    """
    # Check if contractor email already exists
    existing = db.query(Contractor).filter(Contractor.email == contractor_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor with this email already exists"
        )

    # Generate unique ID and document upload token
    contractor_id = str(uuid.uuid4())
    document_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.contract_token_expiry_hours)

    # Create contractor record with minimal info
    contractor = Contractor(
        id=contractor_id,
        status=ContractorStatus.PENDING_DOCUMENTS,
        document_upload_token=document_token,
        document_token_expiry=token_expiry,
        first_name=contractor_data.first_name,
        surname=contractor_data.surname,
        email=contractor_data.email,
        phone=contractor_data.phone,
        consultant_id=current_user.id,
        consultant_name=current_user.name,
        # Set dummy values for required fields (will be filled later)
        gender="Not specified",
        nationality="Not specified",
        home_address="Not specified",
        dob="Not specified",
        currency="AED"
    )

    # Save to database
    db.add(contractor)
    db.commit()
    db.refresh(contractor)

    # Send document upload email to contractor
    contractor_name = f"{contractor.first_name} {contractor.surname}"

    try:
        email_sent = send_document_upload_email(
            contractor_email=contractor.email,
            contractor_name=contractor_name,
            upload_token=document_token,
            expiry_date=token_expiry
        )
    except Exception as e:
        # Log error but don't fail the request
        pass

    return contractor




@router.get("/", response_model=List[ContractorResponse])
async def list_contractors(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all contractors (with optional status filter)
    """
    query = db.query(Contractor)

    if status_filter:
        query = query.filter(Contractor.status == status_filter)

    contractors = query.order_by(Contractor.created_at.desc()).all()
    return contractors


@router.get("/{contractor_id}/signed-contract")
async def get_signed_contract(
    contractor_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Admin views the signed contract PDF
    Supports both Authorization header and query parameter token
    """
    # Authenticate via token query parameter (for direct links)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify JWT token
    from jose import JWTError, jwt
    from app.config import settings
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Get user and verify role
    user = db.query(User).filter(User.email == email).first()
    if not user or user.role not in ["admin", "superadmin", "consultant"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view signed contracts"
        )

    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if contract is signed
    if contractor.status not in [ContractorStatus.SIGNED, ContractorStatus.ACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract has not been signed yet"
        )

    # Prepare contractor data for the 5-page consultant contract
    cds_data = contractor.cds_form_data or {}
    contractor_data = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'client_name': cds_data.get('clientName', contractor.client_name),
        'client_address': cds_data.get('clientAddress', ''),
        'role': cds_data.get('role', contractor.role),
        'location': cds_data.get('location', contractor.location),
        'duration': contractor.duration or cds_data.get('duration', '6 months'),
        'start_date': contractor.start_date or cds_data.get('startDate', ''),
        'candidate_pay_rate': contractor.candidate_pay_rate or cds_data.get('dayRate', ''),
        'currency': contractor.currency or 'USD'
    }

    # Generate PDF with the 5-page consultant contract generator including signatures
    pdf_buffer = generate_consultant_contract_pdf(
        contractor_data,
        contractor_signature_type=contractor.signature_type,
        contractor_signature_data=contractor.signature_data,
        superadmin_signature_type=contractor.superadmin_signature_type,
        superadmin_signature_data=contractor.superadmin_signature_data,
        signed_date=contractor.signed_date.strftime('%Y-%m-%d') if contractor.signed_date else None
    )

    # Return PDF as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=signed_contract_{contractor.first_name}_{contractor.surname}.pdf"
        }
    )


@router.get("/{contractor_id}/contract-preview")
async def get_contractor_contract_preview(
    contractor_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Generate and preview contractor contract PDF
    Accepts authentication via query parameter for iframe compatibility
    """
    # Authenticate via token query parameter (for iframe)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify JWT token
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or user.role not in ["consultant", "admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Prepare contractor data for PDF generation
    cds_data = contractor.cds_form_data or {}
    contractor_data = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'client_name': cds_data.get('clientName', contractor.client_name),
        'client_address': cds_data.get('clientAddress', ''),
        'role': cds_data.get('role', contractor.role),
        'location': cds_data.get('location', contractor.location),
        'duration': contractor.duration or cds_data.get('duration', '6 months'),
        'start_date': contractor.start_date or cds_data.get('startDate', ''),
        'candidate_pay_rate': contractor.candidate_pay_rate or cds_data.get('dayRate', ''),
        'currency': contractor.currency or 'USD'
    }

    # Generate PDF
    pdf_buffer = generate_consultant_contract_pdf(contractor_data)

    # Return as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=contract_{contractor.first_name}_{contractor.surname}.pdf"
        }
    )


@router.get("/{contractor_id}", response_model=ContractorDetailResponse)
async def get_contractor(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get contractor details by ID
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    return contractor


@router.get("/token/{token}", response_model=ContractorDetailResponse)
async def get_contractor_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get contractor details by contract token (for signing portal)
    No authentication required - used by contractor to access contract
    """
    contractor = db.query(Contractor).filter(Contractor.contract_token == token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired contract link"
        )

    # Check if token is expired
    if contractor.token_expiry and contractor.token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract link has expired"
        )

    # Check if already signed
    if contractor.status not in [ContractorStatus.PENDING_SIGNATURE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been processed"
        )

    return contractor


@router.get("/document-token/{token}", response_model=ContractorDetailResponse)
async def get_contractor_by_document_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get contractor details by document upload token (for document upload portal)
    No authentication required - used by contractor to upload documents
    """
    contractor = db.query(Contractor).filter(Contractor.document_upload_token == token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired document upload link"
        )

    # Check if token is expired
    if contractor.document_token_expiry and contractor.document_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document upload link has expired"
        )

    # Check if already uploaded
    if contractor.status not in [ContractorStatus.PENDING_DOCUMENTS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents have already been uploaded for this contractor"
        )

    return contractor


@router.post("/upload-documents/{token}")
async def upload_documents(
    token: str,
    # Personal Information (Form fields)
    first_name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    nationality: str = Form(...),
    country: Optional[str] = Form(None),
    current_location: Optional[str] = Form(None),
    marital_status: Optional[str] = Form(None),
    number_of_children: Optional[str] = Form(None),
    phone: str = Form(...),
    home_address: str = Form(...),
    address_line2: Optional[str] = Form(None),
    address_line3: Optional[str] = Form(None),
    address_line4: Optional[str] = Form(None),
    candidate_bank_name: Optional[str] = Form(None),
    candidate_bank_details: Optional[str] = Form(None),
    candidate_iban: Optional[str] = Form(None),
    # Document Files
    passport_document: UploadFile = File(...),
    photo_document: UploadFile = File(...),
    visa_page_document: UploadFile = File(...),
    id_front_document: UploadFile = File(...),
    id_back_document: UploadFile = File(...),
    degree_document: UploadFile = File(...),
    emirates_id_document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    NEW Step 2: Contractor uploads personal information and required documents
    """
    from app.utils.storage import storage

    contractor = db.query(Contractor).filter(Contractor.document_upload_token == token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid document upload link"
        )

    # Check if token is expired
    if contractor.document_token_expiry and contractor.document_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document upload link has expired"
        )

    # Check status
    if contractor.status != ContractorStatus.PENDING_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents have already been uploaded"
        )

    try:
        # Update personal information
        contractor.first_name = first_name
        contractor.surname = surname
        contractor.email = email
        contractor.gender = gender
        contractor.dob = dob
        contractor.nationality = nationality
        contractor.country = country
        contractor.current_location = current_location
        contractor.marital_status = marital_status
        contractor.number_of_children = number_of_children
        contractor.phone = phone
        contractor.home_address = home_address
        contractor.address_line2 = address_line2
        contractor.address_line3 = address_line3
        contractor.address_line4 = address_line4
        contractor.candidate_bank_name = candidate_bank_name
        contractor.candidate_bank_details = candidate_bank_details
        contractor.candidate_iban = candidate_iban

        # Upload documents to Supabase Storage and get URLs
        passport_url = await storage.upload_document(passport_document, contractor.id, "passport")
        photo_url = await storage.upload_document(photo_document, contractor.id, "photo")
        visa_url = await storage.upload_document(visa_page_document, contractor.id, "visa")
        id_front_url = await storage.upload_document(id_front_document, contractor.id, "id_front")
        id_back_url = await storage.upload_document(id_back_document, contractor.id, "id_back")
        degree_url = await storage.upload_document(degree_document, contractor.id, "degree")

        # Update contractor with document URLs
        contractor.passport_document = passport_url
        contractor.photo_document = photo_url
        contractor.visa_page_document = visa_url
        contractor.id_front_document = id_front_url
        contractor.id_back_document = id_back_url
        contractor.degree_document = degree_url

        # Upload Emirates ID if provided (optional)
        if emirates_id_document:
            emirates_id_url = await storage.upload_document(emirates_id_document, contractor.id, "emirates_id")
            contractor.emirates_id_document = emirates_id_url

        contractor.documents_uploaded_date = datetime.now(timezone.utc)
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

        db.commit()
        db.refresh(contractor)

        # Send notification email to consultant
        # Get consultant info to send notification
        if contractor.consultant_id:
            consultant = db.query(User).filter(User.id == contractor.consultant_id).first()
            if consultant:
                try:
                    send_documents_uploaded_notification(
                        consultant_email=consultant.email,
                        consultant_name=consultant.name,
                        contractor_name=f"{contractor.first_name} {contractor.surname}",
                        contractor_id=contractor.id
                    )
                except Exception as e:
                    pass  # Silent fail on notification

        return {
            "message": "Documents uploaded successfully",
            "contractor_id": contractor.id,
            "status": contractor.status
        }

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to upload documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )


@router.get("/{contractor_id}/cds-form")
async def get_cds_form(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Get CDS form data with auto-prefill from COHF if available (UAE route).
    Returns existing CDS data if already filled, or COHF data mapped to CDS fields.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Start with existing CDS data if available
    cds_data = contractor.cds_form_data or {}

    # If UAE route and COHF is completed, prefill from COHF
    if (contractor.onboarding_route == OnboardingRoute.UAE and
        contractor.cohf_status == "signed" and
        contractor.cohf_data):

        cohf = contractor.cohf_data

        # Map COHF fields to CDS fields (only if not already in CDS)
        # Personal Information
        if not cds_data.get('firstName') and cohf.get('first_name'):
            cds_data['firstName'] = cohf.get('first_name')
        if not cds_data.get('lastName') and cohf.get('surname'):
            cds_data['lastName'] = cohf.get('surname')
        if not cds_data.get('title') and cohf.get('title'):
            cds_data['title'] = cohf.get('title')
        if not cds_data.get('nationality') and cohf.get('nationality'):
            cds_data['nationality'] = cohf.get('nationality')
        if not cds_data.get('dob'):
            cds_data['dob'] = cohf.get('date_of_birth') or cohf.get('dob')
        if not cds_data.get('maritalStatus') and cohf.get('marital_status'):
            cds_data['maritalStatus'] = cohf.get('marital_status')
        if not cds_data.get('mobileNo'):
            cds_data['mobileNo'] = cohf.get('mobile') or cohf.get('phone')
        if not cds_data.get('email') and cohf.get('email'):
            cds_data['email'] = cohf.get('email')
        if not cds_data.get('addressLine1'):
            cds_data['addressLine1'] = cohf.get('address') or cohf.get('home_address')
        if not cds_data.get('currentLocation') and cohf.get('current_location'):
            cds_data['currentLocation'] = cohf.get('current_location')
        if not cds_data.get('visaStatus') and cohf.get('visa_status'):
            cds_data['visaStatus'] = cohf.get('visa_status')

        # Remuneration Information
        if not cds_data.get('grossSalary') and cohf.get('gross_salary'):
            cds_data['grossSalary'] = cohf.get('gross_salary')
        if not cds_data.get('basicSalaryMonthly'):
            cds_data['basicSalaryMonthly'] = cohf.get('basic_salary') or cohf.get('basic_salary_monthly')
        if not cds_data.get('housingMonthly'):
            cds_data['housingMonthly'] = cohf.get('housing_allowance') or cohf.get('housing_monthly')
        if not cds_data.get('transportMonthly'):
            cds_data['transportMonthly'] = cohf.get('transport_allowance') or cohf.get('transport_monthly')
        if not cds_data.get('leaveAllowance') and cohf.get('leave_allowance'):
            cds_data['leaveAllowance'] = cohf.get('leave_allowance')
        if not cds_data.get('medicalInsuranceCategory') and cohf.get('medical_insurance_category'):
            cds_data['medicalInsuranceCategory'] = cohf.get('medical_insurance_category')
        if not cds_data.get('medical'):
            cds_data['medical'] = cohf.get('medical_insurance_cost') or cohf.get('medical')
        if not cds_data.get('managementFee') and cohf.get('management_fee'):
            cds_data['managementFee'] = cohf.get('management_fee')

        # Deployment Information
        if not cds_data.get('visaType') and cohf.get('visa_type'):
            cds_data['visaType'] = cohf.get('visa_type')
        if not cds_data.get('jobTitle'):
            cds_data['jobTitle'] = cohf.get('job_title') or cohf.get('role')
        if not cds_data.get('companyName'):
            cds_data['companyName'] = cohf.get('company_name') or cohf.get('client_name')
        if not cds_data.get('workLocation') and cohf.get('work_location'):
            cds_data['workLocation'] = cohf.get('work_location')
        if not cds_data.get('startDate'):
            cds_data['startDate'] = cohf.get('expected_start_date') or cohf.get('start_date')
        if not cds_data.get('duration'):
            cds_data['duration'] = cohf.get('expected_tenure') or cohf.get('duration')
        if not cds_data.get('probationPeriod') and cohf.get('probation_period'):
            cds_data['probationPeriod'] = cohf.get('probation_period')
        if not cds_data.get('noticePeriod') and cohf.get('notice_period'):
            cds_data['noticePeriod'] = cohf.get('notice_period')
        if not cds_data.get('annualLeaveType') and cohf.get('annual_leave_type'):
            cds_data['annualLeaveType'] = cohf.get('annual_leave_type')
        if not cds_data.get('annualLeaveDays') and cohf.get('annual_leave_days'):
            cds_data['annualLeaveDays'] = cohf.get('annual_leave_days')
        if not cds_data.get('weeklyWorkingDays') and cohf.get('weekly_working_days'):
            cds_data['weeklyWorkingDays'] = cohf.get('weekly_working_days')
        if not cds_data.get('weekendDays') and cohf.get('weekend_days'):
            cds_data['weekendDays'] = cohf.get('weekend_days')
        if not cds_data.get('chargeableRate') and cohf.get('chargeable_rate'):
            cds_data['chargeableRate'] = cohf.get('chargeable_rate')

    return {
        "contractor_id": contractor_id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cds_data": cds_data,
        "onboarding_route": contractor.onboarding_route.value if contractor.onboarding_route else None,
        "status": contractor.status.value,
        "prefilled_from_cohf": bool(contractor.onboarding_route == OnboardingRoute.UAE and contractor.cohf_data and contractor.cohf_status == "signed")
    }


@router.put("/{contractor_id}/cds-form")
async def submit_cds_form(
    contractor_id: str,
    cds_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Step 2: Consultant submits CDS (Contractor Detail Sheet) form data
    This saves contractor details but doesn't change status - keeps it as DOCUMENTS_UPLOADED
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if contractor is ready for CDS
    # Allow: DOCUMENTS_UPLOADED, PENDING_CDS_CS, COHF_COMPLETED (UAE route), PENDING_COHF (filled but not signed), PENDING_REVIEW (editing after rejection)
    # Also allow Saudi route statuses so consultants can fill CDS while quote sheet process is ongoing
    valid_statuses = [
        ContractorStatus.DOCUMENTS_UPLOADED,
        ContractorStatus.PENDING_CDS_CS,
        ContractorStatus.COHF_COMPLETED,
        ContractorStatus.PENDING_COHF,
        ContractorStatus.AWAITING_COHF_SIGNATURE,
        ContractorStatus.PENDING_REVIEW,
        ContractorStatus.CDS_CS_COMPLETED,
        ContractorStatus.PENDING_THIRD_PARTY_RESPONSE,
        ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
    ]
    if contractor.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Documents must be uploaded before completing CDS. Current status: {contractor.status}"
        )

    # Extract nested data object if it exists
    form_data = cds_data.get('data', cds_data)

    # ==========================================
    # SECTION 1: CONTRACTOR DETAILS
    # ==========================================
    if 'firstName' in form_data:
        contractor.first_name = form_data['firstName']
    if 'middleNames' in form_data:
        contractor.middle_names = form_data['middleNames']
    if 'lastName' in form_data:
        contractor.surname = form_data['lastName']
    # Legacy support
    if 'surname' in form_data:
        contractor.surname = form_data['surname']
    if 'gender' in form_data:
        contractor.gender = form_data['gender']
    if 'maritalStatus' in form_data:
        contractor.marital_status = form_data['maritalStatus']
    if 'numberOfChildren' in form_data:
        contractor.number_of_children = form_data['numberOfChildren']
    if 'nationality' in form_data:
        contractor.nationality = form_data['nationality']
    if 'countryOfResidence' in form_data:
        contractor.country_of_residence = form_data['countryOfResidence']
    if 'country' in form_data:
        contractor.country = form_data['country']
    if 'currentLocation' in form_data:
        contractor.current_location = form_data['currentLocation']
    # Address fields
    if 'addressLine1' in form_data:
        contractor.address_line1 = form_data['addressLine1']
        contractor.home_address = form_data['addressLine1']  # Also update legacy field
    if 'homeAddress' in form_data:
        contractor.home_address = form_data['homeAddress']
    if 'addressLine2' in form_data:
        contractor.address_line2 = form_data['addressLine2']
    if 'addressLine3' in form_data:
        contractor.address_line3 = form_data['addressLine3']
    if 'addressLine4' in form_data:
        contractor.address_line4 = form_data['addressLine4']
    # Contact
    if 'mobileNo' in form_data:
        contractor.mobile_no = form_data['mobileNo']
        contractor.phone = form_data['mobileNo']  # Also update legacy field
    if 'phone' in form_data:
        contractor.phone = form_data['phone']
    if 'email' in form_data:
        contractor.email = form_data['email']
    if 'dob' in form_data:
        contractor.dob = form_data['dob']
    # Contractor Banking
    if 'contractorBankName' in form_data:
        contractor.contractor_bank_name = form_data['contractorBankName']
    if 'contractorAccountName' in form_data:
        contractor.contractor_account_name = form_data['contractorAccountName']
    if 'contractorAccountNo' in form_data:
        contractor.contractor_account_no = form_data['contractorAccountNo']
    if 'contractorIBAN' in form_data:
        contractor.contractor_iban = form_data['contractorIBAN']
    if 'contractorSwiftBic' in form_data:
        contractor.contractor_swift_bic = form_data['contractorSwiftBic']

    # ==========================================
    # SECTION 2: MANAGEMENT COMPANY
    # ==========================================
    if 'thirdPartyId' in form_data:
        contractor.third_party_id = form_data['thirdPartyId']
    if 'companyName' in form_data:
        contractor.company_name = form_data['companyName']
        contractor.umbrella_company_name = form_data['companyName']  # Also update legacy
    if 'umbrellaCompanyName' in form_data:
        contractor.umbrella_company_name = form_data['umbrellaCompanyName']
    # Management Address
    if 'mgmtAddressLine1' in form_data:
        contractor.mgmt_address_line1 = form_data['mgmtAddressLine1']
        contractor.registered_address = form_data['mgmtAddressLine1']  # Legacy
    if 'registeredAddress' in form_data:
        contractor.registered_address = form_data['registeredAddress']
    if 'mgmtAddressLine2' in form_data:
        contractor.mgmt_address_line2 = form_data['mgmtAddressLine2']
        contractor.management_address_line2 = form_data['mgmtAddressLine2']  # Legacy
    if 'managementAddressLine2' in form_data:
        contractor.management_address_line2 = form_data['managementAddressLine2']
    if 'mgmtAddressLine3' in form_data:
        contractor.mgmt_address_line3 = form_data['mgmtAddressLine3']
        contractor.management_address_line3 = form_data['mgmtAddressLine3']  # Legacy
    if 'managementAddressLine3' in form_data:
        contractor.management_address_line3 = form_data['managementAddressLine3']
    if 'mgmtAddressLine4' in form_data:
        contractor.mgmt_address_line4 = form_data['mgmtAddressLine4']
    if 'mgmtCountry' in form_data:
        contractor.mgmt_country = form_data['mgmtCountry']
    if 'companyRegNo' in form_data:
        contractor.company_reg_no = form_data['companyRegNo']
    if 'companyVATNo' in form_data:
        contractor.company_vat_no = form_data['companyVATNo']
    # Management Banking
    if 'mgmtBankName' in form_data:
        contractor.mgmt_bank_name = form_data['mgmtBankName']
        contractor.bank_name = form_data['mgmtBankName']  # Legacy
    if 'bankName' in form_data:
        contractor.bank_name = form_data['bankName']
    if 'mgmtAccountName' in form_data:
        contractor.mgmt_account_name = form_data['mgmtAccountName']
    if 'mgmtAccountNumber' in form_data:
        contractor.mgmt_account_number = form_data['mgmtAccountNumber']
        contractor.account_number = form_data['mgmtAccountNumber']  # Legacy
    if 'accountNumber' in form_data:
        contractor.account_number = form_data['accountNumber']
    if 'mgmtIBANNumber' in form_data:
        contractor.mgmt_iban_number = form_data['mgmtIBANNumber']
        contractor.iban_number = form_data['mgmtIBANNumber']  # Legacy
    if 'ibanNumber' in form_data:
        contractor.iban_number = form_data['ibanNumber']
    if 'mgmtSwiftBic' in form_data:
        contractor.mgmt_swift_bic = form_data['mgmtSwiftBic']

    # ==========================================
    # SECTION 3: PLACEMENT DETAILS
    # ==========================================
    if 'clientId' in form_data:
        contractor.client_id = form_data['clientId']
    if 'clientName' in form_data:
        contractor.client_name = form_data['clientName']
    if 'location' in form_data:
        contractor.location = form_data['location']
    if 'role' in form_data:
        contractor.role = form_data['role']
    if 'startDate' in form_data:
        contractor.start_date = form_data['startDate']
    if 'duration' in form_data:
        contractor.duration = form_data['duration']
    if 'endDate' in form_data:
        contractor.end_date = form_data['endDate']
    if 'currency' in form_data:
        contractor.currency = form_data['currency']
    # Rate type and rates
    if 'rateType' in form_data:
        contractor.rate_type = form_data['rateType']
    if 'chargeRateMonth' in form_data:
        contractor.charge_rate_month = form_data['chargeRateMonth']
        contractor.client_charge_rate = form_data['chargeRateMonth']  # Legacy
    if 'grossSalary' in form_data:
        contractor.gross_salary = form_data['grossSalary']
        contractor.candidate_pay_rate = form_data['grossSalary']  # Legacy
    if 'chargeRateDay' in form_data:
        contractor.charge_rate_day = form_data['chargeRateDay']
    if 'dayRate' in form_data:
        contractor.day_rate = form_data['dayRate']
    # Legacy fields
    if 'clientChargeRate' in form_data:
        contractor.client_charge_rate = form_data['clientChargeRate']
    if 'candidatePayRate' in form_data:
        contractor.candidate_pay_rate = form_data['candidatePayRate']
    if 'projectName' in form_data:
        contractor.project_name = form_data['projectName']
    if 'candidateBasicSalary' in form_data:
        contractor.candidate_basic_salary = form_data['candidateBasicSalary']
    if 'businessType' in form_data:
        contractor.business_type = form_data['businessType']

    # ==========================================
    # SECTION 4: AVENTUS DEAL
    # ==========================================
    if 'consultant' in form_data:
        contractor.consultant = form_data['consultant']
    if 'resourcer' in form_data:
        contractor.resourcer = form_data['resourcer']
    if 'aventusSplit' in form_data:
        contractor.aventus_split = form_data['aventusSplit']
    if 'resourcerSplit' in form_data:
        contractor.resourcer_split = form_data['resourcerSplit']

    # ==========================================
    # SECTION 5: INVOICE DETAILS
    # ==========================================
    if 'timesheetRequired' in form_data:
        contractor.timesheet_required = form_data['timesheetRequired']
    if 'timesheetApproverName' in form_data:
        contractor.timesheet_approver_name = form_data['timesheetApproverName']
    if 'invoicingPreferences' in form_data:
        contractor.invoicing_preferences = form_data['invoicingPreferences']
    if 'invoiceInstructions' in form_data:
        contractor.invoice_instructions = form_data['invoiceInstructions']
    # Client contacts
    if 'clientContact1' in form_data:
        contractor.client_contact1 = form_data['clientContact1']
        contractor.client_contact = form_data['clientContact1']  # Legacy
    if 'clientContact' in form_data:
        contractor.client_contact = form_data['clientContact']
    if 'clientContact2' in form_data:
        contractor.client_contact2 = form_data['clientContact2']
    if 'invoiceEmail1' in form_data:
        contractor.invoice_email1 = form_data['invoiceEmail1']
        contractor.invoice_email = form_data['invoiceEmail1']  # Legacy
    if 'invoiceEmail' in form_data:
        contractor.invoice_email = form_data['invoiceEmail']
    if 'invoiceEmail2' in form_data:
        contractor.invoice_email2 = form_data['invoiceEmail2']
    # Address
    if 'invoiceAddressLine1' in form_data:
        contractor.invoice_address_line1 = form_data['invoiceAddressLine1']
    if 'invoiceAddressLine2' in form_data:
        contractor.invoice_address_line2 = form_data['invoiceAddressLine2']
    if 'invoiceAddressLine3' in form_data:
        contractor.invoice_address_line3 = form_data['invoiceAddressLine3']
    if 'invoiceAddressLine4' in form_data:
        contractor.invoice_address_line4 = form_data['invoiceAddressLine4']
    if 'invoicePOBox' in form_data:
        contractor.invoice_po_box = form_data['invoicePOBox']
    if 'invoiceCountry' in form_data:
        contractor.invoice_country = form_data['invoiceCountry']
    # PO & Payment
    if 'poRequired' in form_data:
        contractor.po_required = form_data['poRequired']
    if 'poNumber' in form_data:
        contractor.po_number = form_data['poNumber']
    if 'taxNumber' in form_data:
        contractor.tax_number = form_data['taxNumber']
        contractor.invoice_tax_number = form_data['taxNumber']  # Legacy
    if 'invoiceTaxNumber' in form_data:
        contractor.invoice_tax_number = form_data['invoiceTaxNumber']
    if 'contractorPayFrequency' in form_data:
        contractor.contractor_pay_frequency = form_data['contractorPayFrequency']
    if 'clientInvoiceFrequency' in form_data:
        contractor.client_invoice_frequency = form_data['clientInvoiceFrequency']
    if 'clientPaymentTerms' in form_data:
        contractor.client_payment_terms = form_data['clientPaymentTerms']
    if 'supportingDocsRequired' in form_data:
        contractor.supporting_docs_required = form_data['supportingDocsRequired']

    # ==========================================
    # LEGACY FIELDS (for backward compatibility)
    # ==========================================
    # Monthly costs (moved to costing sheet but kept for legacy)
    if 'managementCompanyCharges' in form_data:
        contractor.management_company_charges = form_data['managementCompanyCharges']
    if 'taxes' in form_data:
        contractor.taxes = form_data['taxes']
    if 'bankFees' in form_data:
        contractor.bank_fees = form_data['bankFees']
    if 'fx' in form_data:
        contractor.fx = form_data['fx']
    if 'nationalisation' in form_data:
        contractor.nationalisation = form_data['nationalisation']
    # Provisions
    if 'eosb' in form_data:
        contractor.eosb = form_data['eosb']
    if 'vacationPay' in form_data:
        contractor.vacation_pay = form_data['vacationPay']
    if 'sickLeave' in form_data:
        contractor.sick_leave = form_data['sickLeave']
    if 'otherProvision' in form_data:
        contractor.other_provision = form_data['otherProvision']
    # One-time costs
    if 'flights' in form_data:
        contractor.flights = form_data['flights']
    if 'visa' in form_data:
        contractor.visa = form_data['visa']
    if 'medicalInsurance' in form_data:
        contractor.medical_insurance = form_data['medicalInsurance']
    if 'familyCosts' in form_data:
        contractor.family_costs = form_data['familyCosts']
    if 'otherOneTimeCosts' in form_data:
        contractor.other_one_time_costs = form_data['otherOneTimeCosts']
    # Additional info
    if 'upfrontInvoices' in form_data:
        contractor.upfront_invoices = form_data['upfrontInvoices']
    if 'securityDeposit' in form_data:
        contractor.security_deposit = form_data['securityDeposit']
    if 'laptopProvider' in form_data:
        contractor.laptop_provider = form_data['laptopProvider']
    if 'otherNotes' in form_data:
        contractor.other_notes = form_data['otherNotes']
    # Summary calculations
    if 'contractorTotalFixedCosts' in form_data:
        contractor.contractor_total_fixed_costs = form_data['contractorTotalFixedCosts']
    if 'estimatedMonthlyGP' in form_data:
        contractor.estimated_monthly_gp = form_data['estimatedMonthlyGP']
    # Pay details (moved to contractor section)
    if 'umbrellaOrDirect' in form_data:
        contractor.umbrella_or_direct = form_data['umbrellaOrDirect']
    if 'candidateBankDetails' in form_data:
        contractor.candidate_bank_details = form_data['candidateBankDetails']
    if 'candidateIBAN' in form_data:
        contractor.candidate_iban = form_data['candidateIBAN']

    # Save complete CDS form data as JSON for easy retrieval
    # This ensures all form fields are preserved when navigating back to the form
    contractor.cds_form_data = {
        **form_data,
        "saved_at": datetime.now().isoformat()
    }

    # Keep status unchanged (either DOCUMENTS_UPLOADED or PENDING_CDS_CS)
    # Status will be changed to PENDING_REVIEW after costing sheet submission

    db.commit()
    db.refresh(contractor)

    return {
        "message": "CDS form saved successfully",
        "contractor_id": contractor.id,
        "status": contractor.status
    }


@router.put("/{contractor_id}/costing-sheet")
async def submit_costing_sheet(
    contractor_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Step 3: Consultant submits costing sheet with full costing details
    Accepts JSON body with all costing data
    This changes status to PENDING_REVIEW and sends notification to admins
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if contractor is ready for costing sheet submission
    # Allow: DOCUMENTS_UPLOADED, PENDING_CDS_CS, CDS_CS_COMPLETED, COHF_COMPLETED (UAE route), PENDING_COHF (COHF in progress), PENDING_REVIEW (editing)
    valid_statuses = [
        ContractorStatus.DOCUMENTS_UPLOADED,
        ContractorStatus.PENDING_CDS_CS,
        ContractorStatus.CDS_CS_COMPLETED,
        ContractorStatus.COHF_COMPLETED,  # UAE route after COHF is done
        ContractorStatus.PENDING_COHF,  # UAE route - COHF filled but not signed
        ContractorStatus.AWAITING_COHF_SIGNATURE,  # UAE route - sent to third party
        ContractorStatus.PENDING_REVIEW,  # Allow re-submission after rejection
        ContractorStatus.PENDING_THIRD_PARTY_QUOTE,  # Saudi route
        ContractorStatus.PENDING_THIRD_PARTY_RESPONSE,  # Saudi route
    ]
    if contractor.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CDS form must be completed before submitting costing sheet. Current status: {contractor.status}"
        )

    # Parse JSON body
    try:
        costing_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON data"
        )

    # Store complete costing sheet data with timestamp
    costing_sheet_data = {
        **costing_data,
        "submitted_at": datetime.now().isoformat()
    }

    contractor.costing_sheet_data = costing_sheet_data

    # Update status to PENDING_REVIEW so admin can approve/reject
    contractor.status = ContractorStatus.PENDING_REVIEW

    db.commit()
    db.refresh(contractor)

    # Send notification email to admin/superadmin
    # Get all admin and superadmin emails to notify
    admins = db.query(User).filter(
        User.role.in_([UserRole.ADMIN, UserRole.SUPERADMIN]),
        User.is_active == True
    ).all()

    if admins:
        admin_emails = [admin.email for admin in admins]
        consultant_name = contractor.consultant_name or "Unknown"
        contractor_name = f"{contractor.first_name} {contractor.surname}"

        try:
            send_review_notification(
                admin_emails=admin_emails,
                contractor_name=contractor_name,
                consultant_name=consultant_name,
                contractor_id=contractor.id
            )
        except Exception as e:
            pass  # Silent fail on notification

    return {
        "message": "Costing sheet submitted successfully",
        "contractor_id": contractor.id,
        "status": contractor.status
    }


@router.post("/{contractor_id}/approve")
async def approve_contractor(
    contractor_id: str,
    approval_data: ContractorApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    NEW Step 4: Admin/Superadmin approves contractor and triggers contract generation
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be pending review
    if contractor.status != ContractorStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be pending review status for approval/rejection"
        )

    if not approval_data.approved:
        # REJECTION: Return contractor to DOCUMENTS_UPLOADED status so consultant can edit and resubmit
        contractor.reviewed_date = datetime.now(timezone.utc)
        contractor.reviewed_by = current_user.id
        contractor.status = ContractorStatus.DOCUMENTS_UPLOADED
        # Store rejection notes if provided
        if approval_data.notes:
            # Could store rejection notes in a dedicated field if needed
            pass
        db.commit()
        db.refresh(contractor)

        return {
            "message": "Contractor rejected - consultant can now edit and resubmit CDS & CS forms",
            "contractor_id": contractor.id,
            "approved": False,
            "status": "documents_uploaded"
        }

    # APPROVAL: Just set status to APPROVED
    # Contract will be generated later after work order flow completes
    contractor.reviewed_date = datetime.now(timezone.utc)
    contractor.reviewed_by = current_user.id
    contractor.approved_date = datetime.now(timezone.utc)
    contractor.approved_by = current_user.id
    contractor.status = ContractorStatus.APPROVED

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Contractor approved - consultant can now send work order to client",
        "contractor_id": contractor.id,
        "status": "approved",
        "approved": True
    }


@router.get("/{contractor_id}/work-order")
async def get_contractor_work_order(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get or generate work order preview for a contractor
    Returns existing work order or generates a preview without saving
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if work order already exists for this contractor
    existing_work_order = db.query(WorkOrder).filter(
        WorkOrder.contractor_id == contractor_id
    ).order_by(WorkOrder.created_at.desc()).first()

    if existing_work_order:
        # Return existing work order
        return {
            "id": existing_work_order.id,
            "work_order_number": existing_work_order.work_order_number,
            "contractor_id": existing_work_order.contractor_id,
            "contractor_name": existing_work_order.contractor_name,
            "client_name": existing_work_order.client_name,
            "role": existing_work_order.role,
            "location": existing_work_order.location,
            "start_date": existing_work_order.start_date,
            "end_date": existing_work_order.end_date,
            "duration": existing_work_order.duration,
            "currency": existing_work_order.currency,
            "charge_rate": existing_work_order.charge_rate,
            "pay_rate": existing_work_order.pay_rate,
            "project_name": existing_work_order.project_name,
            "business_type": existing_work_order.business_type,
            "umbrella_company_name": existing_work_order.umbrella_company_name,
            "status": existing_work_order.status.value
        }

    # Generate preview from contractor data
    if not contractor.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client information is missing for this contractor"
        )

    client = db.query(Client).filter(Client.id == contractor.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Generate preview work order number
    work_order_count = db.query(WorkOrder).count()
    preview_wo_number = f"WO-{datetime.now().year}-{str(work_order_count + 1).zfill(4)}"

    # Format dates
    start_date_str = contractor.start_date if contractor.start_date else datetime.now().strftime("%Y-%m-%d")
    end_date_str = contractor.end_date if contractor.end_date else None

    # Return preview data
    return {
        "id": None,  # Preview has no ID yet
        "work_order_number": preview_wo_number,
        "contractor_id": contractor.id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "client_name": client.company_name,
        "role": contractor.role,
        "location": contractor.location or "",
        "start_date": start_date_str,
        "end_date": end_date_str,
        "duration": contractor.duration,
        "currency": contractor.currency,
        "charge_rate": contractor.client_charge_rate,
        "pay_rate": contractor.candidate_pay_rate,
        "project_name": contractor.project_name,
        "business_type": contractor.business_type,
        "umbrella_company_name": contractor.umbrella_company_name,
        "status": "pending_approval"
    }


@router.get("/{contractor_id}/work-order/pdf")
async def get_contractor_work_order_pdf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate and return work order PDF for preview
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check for existing work order first
    existing_work_order = db.query(WorkOrder).filter(
        WorkOrder.contractor_id == contractor_id
    ).order_by(WorkOrder.created_at.desc()).first()

    if existing_work_order:
        # Use existing work order data
        work_order_data = {
            "work_order_number": existing_work_order.work_order_number,
            "contractor_name": existing_work_order.contractor_name,
            "client_name": existing_work_order.client_name,
            "role": existing_work_order.role,
            "location": existing_work_order.location,
            "start_date": existing_work_order.start_date.strftime("%d %B %Y") if existing_work_order.start_date else "N/A",
            "end_date": existing_work_order.end_date.strftime("%d %B %Y") if existing_work_order.end_date else "N/A",
            "duration": existing_work_order.duration,
            "currency": existing_work_order.currency,
            "charge_rate": existing_work_order.charge_rate,
            "pay_rate": existing_work_order.pay_rate,
            "project_name": existing_work_order.project_name,
            "business_type": existing_work_order.business_type,
            "umbrella_company_name": existing_work_order.umbrella_company_name
        }
    else:
        # Generate preview from contractor data
        if not contractor.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client information is missing"
            )

        client = db.query(Client).filter(Client.id == contractor.client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Generate preview work order number
        work_order_count = db.query(WorkOrder).count()
        preview_wo_number = f"WO-{datetime.now().year}-{str(work_order_count + 1).zfill(4)}"

        # Parse dates
        start_date = datetime.fromisoformat(contractor.start_date) if contractor.start_date else datetime.now()
        end_date = datetime.fromisoformat(contractor.end_date) if contractor.end_date else None

        work_order_data = {
            "work_order_number": preview_wo_number,
            "contractor_name": f"{contractor.first_name} {contractor.surname}",
            "client_name": client.company_name,
            "role": contractor.role,
            "location": contractor.location or "",
            "start_date": start_date.strftime("%d %B %Y"),
            "end_date": end_date.strftime("%d %B %Y") if end_date else "N/A",
            "duration": contractor.duration,
            "currency": contractor.currency,
            "charge_rate": contractor.client_charge_rate,
            "pay_rate": contractor.candidate_pay_rate,
            "project_name": contractor.project_name,
            "business_type": contractor.business_type,
            "umbrella_company_name": contractor.umbrella_company_name
        }

    # Generate PDF
    pdf_buffer = generate_work_order_pdf(work_order_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="work_order_{work_order_data["work_order_number"]}.pdf"'
        }
    )


@router.post("/{contractor_id}/work-order/approve")
async def approve_contractor_work_order(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Approve work order and send to client for signature
    Creates work order if doesn't exist, then sends email to client
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be approved
    if contractor.status != ContractorStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be approved before sending work order to client"
        )

    # Check if client_id exists
    if not contractor.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client information is missing for this contractor"
        )

    # Get client details
    client = db.query(Client).filter(Client.id == contractor.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Check if work order already exists
    existing_work_order = db.query(WorkOrder).filter(
        WorkOrder.contractor_id == contractor_id
    ).order_by(WorkOrder.created_at.desc()).first()

    if existing_work_order and existing_work_order.status == WorkOrderStatus.PENDING_CLIENT_SIGNATURE:
        # Work order already sent, return success
        return {
            "message": "Work order already sent to client",
            "work_order_id": existing_work_order.id,
            "work_order_number": existing_work_order.work_order_number,
            "status": "pending_client_signature"
        }

    # Generate work order number
    work_order_count = db.query(WorkOrder).count()
    work_order_number = f"WO-{datetime.now().year}-{str(work_order_count + 1).zfill(4)}"

    # Generate unique signature token for client
    signature_token = generate_unique_token()

    # Create work order
    work_order = WorkOrder(
        id=str(uuid.uuid4()),
        work_order_number=work_order_number,
        contractor_id=contractor.id,
        third_party_id=contractor.third_party_id,
        title=f"Work Order - {contractor.role}",
        description=f"Work order for {contractor.first_name} {contractor.surname} at {client.company_name}",
        location=contractor.location or "",
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        client_name=client.company_name,
        project_name=contractor.project_name,
        role=contractor.role,
        duration=contractor.duration,
        currency=contractor.currency,
        business_type=contractor.business_type,
        umbrella_company_name=contractor.umbrella_company_name,
        start_date=datetime.fromisoformat(contractor.start_date) if contractor.start_date else datetime.now(),
        end_date=datetime.fromisoformat(contractor.end_date) if contractor.end_date else None,
        charge_rate=contractor.client_charge_rate,
        pay_rate=contractor.candidate_pay_rate,
        status=WorkOrderStatus.PENDING_CLIENT_SIGNATURE,
        client_signature_token=signature_token,
        created_by=current_user.id,
        generated_by=current_user.id,
        generated_date=datetime.now(timezone.utc)
    )

    db.add(work_order)

    # Update contractor status
    contractor.status = ContractorStatus.PENDING_CLIENT_WO_SIGNATURE

    db.commit()
    db.refresh(work_order)
    db.refresh(contractor)

    # Send email to client with link to sign work order
    print(f"[DEBUG] Client ID: {client.id}")
    print(f"[DEBUG] Client Company Name: {client.company_name}")
    print(f"[DEBUG] Client Contact Person Name: {client.contact_person_name}")
    print(f"[DEBUG] Client Contact Person Email: {client.contact_person_email}")
    client_email = client.contact_person_email if client.contact_person_email else None
    work_order_link = f"{settings.frontend_url}/sign-work-order/{signature_token}"

    # Set token expiry (72 hours from now)
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=72)

    if client_email:
        try:
            print(f"[DEBUG] Sending work order email to: {client_email}")
            email_sent = send_work_order_to_client(
                client_email=client_email,
                client_name=client.company_name,
                contractor_name=f"{contractor.first_name} {contractor.surname}",
                work_order_token=signature_token,
                expiry_date=token_expiry
            )

            # Email sent silently
        except Exception as e:
            print(f"[ERROR] Exception sending work order email: {str(e)}")
    else:
        print(f"[WARNING] No email found for client {client.company_name}")

    return {
        "message": "Work order approved and sent to client for signature",
        "work_order_id": work_order.id,
        "work_order_number": work_order_number,
        "contractor_id": contractor.id,
        "status": "pending_client_wo_signature",
        "client_signature_link": work_order_link
    }


@router.post("/{contractor_id}/send-work-order")
async def send_work_order_to_client_endpoint(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Send work order to client for signature after contractor is approved
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be approved
    if contractor.status != ContractorStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be approved before sending work order to client"
        )

    # Check if client_id exists
    if not contractor.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client information is missing for this contractor"
        )

    # Get client details
    client = db.query(Client).filter(Client.id == contractor.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Generate work order number
    work_order_count = db.query(WorkOrder).count()
    work_order_number = f"WO-{datetime.now().year}-{str(work_order_count + 1).zfill(4)}"

    # Generate unique signature token for client
    signature_token = generate_unique_token()

    # Create work order
    work_order = WorkOrder(
        id=str(uuid.uuid4()),
        work_order_number=work_order_number,
        contractor_id=contractor.id,
        third_party_id=contractor.third_party_id,
        title=f"Work Order - {contractor.role}",
        description=f"Work order for {contractor.first_name} {contractor.surname} at {client.company_name}",
        location=contractor.location or "",
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        client_name=client.company_name,
        project_name=contractor.project_name,
        role=contractor.role,
        duration=contractor.duration,
        currency=contractor.currency,
        business_type=contractor.business_type,
        umbrella_company_name=contractor.umbrella_company_name,
        start_date=datetime.fromisoformat(contractor.start_date) if contractor.start_date else datetime.now(),
        end_date=datetime.fromisoformat(contractor.end_date) if contractor.end_date else None,
        charge_rate=contractor.client_charge_rate,
        pay_rate=contractor.candidate_pay_rate,
        status=WorkOrderStatus.PENDING_CLIENT_SIGNATURE,
        client_signature_token=signature_token,
        created_by=current_user.id,
        generated_by=current_user.id,
        generated_date=datetime.now(timezone.utc)
    )

    db.add(work_order)

    # Update contractor status
    contractor.status = ContractorStatus.PENDING_CLIENT_WO_SIGNATURE

    db.commit()
    db.refresh(work_order)
    db.refresh(contractor)

    # Send email to client with link to sign work order
    print(f"[DEBUG] Client ID: {client.id}")
    print(f"[DEBUG] Client Company Name: {client.company_name}")
    print(f"[DEBUG] Client Contact Person Name: {client.contact_person_name}")
    print(f"[DEBUG] Client Contact Person Email: {client.contact_person_email}")
    client_email = client.contact_person_email if client.contact_person_email else None
    work_order_link = f"{settings.frontend_url}/sign-work-order/{signature_token}"

    # Set token expiry (72 hours from now)
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=72)

    if client_email:
        try:
            print(f"[DEBUG] Sending work order email to: {client_email}")
            email_sent = send_work_order_to_client(
                client_email=client_email,
                client_name=client.company_name,
                contractor_name=f"{contractor.first_name} {contractor.surname}",
                work_order_token=signature_token,
                expiry_date=token_expiry
            )

            # Email sent silently
        except Exception as e:
            print(f"[ERROR] Exception sending work order email: {str(e)}")
    else:
        print(f"[WARNING] No email found for client {client.company_name}")

    return {
        "message": "Work order sent to client for signature",
        "work_order_id": work_order.id,
        "work_order_number": work_order_number,
        "contractor_id": contractor.id,
        "status": "pending_client_wo_signature",
        "client_signature_link": work_order_link
    }


@router.post("/{contractor_id}/forward-work-order-to-superadmin")
async def forward_work_order_to_superadmin(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Consultant forwards signed work order to superadmin for approval
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be work_order_completed
    if contractor.status != ContractorStatus.WORK_ORDER_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work order must be completed before forwarding to superadmin"
        )

    # Update contractor status to pending contract upload
    # After superadmin approves, they will trigger the contract upload request
    contractor.status = ContractorStatus.PENDING_CONTRACT_UPLOAD

    db.commit()
    db.refresh(contractor)

    # TODO: Send notification to superadmin
    return {
        "message": "Work order forwarded to superadmin - awaiting contract upload request",
        "contractor_id": contractor.id,
        "status": "pending_contract_upload"
    }


@router.post("/{contractor_id}/request-contract-upload")
async def request_contract_upload_from_client(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Superadmin approves work order and sends email to client requesting contract upload
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status
    if contractor.status != ContractorStatus.PENDING_CONTRACT_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be in pending_contract_upload status"
        )

    # Get client details
    if not contractor.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client information is missing"
        )

    client = db.query(Client).filter(Client.id == contractor.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Generate upload token
    upload_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days to upload

    # Store upload token in contractor
    contractor.contract_upload_token = upload_token
    contractor.contract_upload_token_expiry = token_expiry

    db.commit()
    db.refresh(contractor)

    # Send email to client with upload link
    upload_link = f"{settings.frontend_url}/upload-contract/{upload_token}"
    client_email = client.contact_person_email if client.contact_person_email else None

    # TODO: Create and send email function
    return {
        "message": "Contract upload request sent to client",
        "contractor_id": contractor.id,
        "client_company": client.company_name,
        "upload_link": upload_link,
        "token_expiry": token_expiry.isoformat(),
        "status": "pending_contract_upload"
    }


@router.post("/{contractor_id}/recall")
async def recall_contractor_for_editing(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Recall a contractor from cds_cs_completed status back to pending_cds_cs
    to allow consultant to make changes and resubmit
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - can only recall from pending_review or cds_cs_completed (for backward compatibility)
    if contractor.status not in [ContractorStatus.PENDING_REVIEW, ContractorStatus.CDS_CS_COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only recall contractors that are pending review or have completed CDS & CS"
        )

    # Only allow consultant to recall their own contractors (or admin/superadmin)
    if current_user.role == UserRole.CONSULTANT and contractor.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only recall your own contractors"
        )

    # Change status back to documents_uploaded so consultant can edit CDS & CS
    contractor.status = ContractorStatus.DOCUMENTS_UPLOADED
    contractor.reviewed_date = None  # Clear review date since it's being recalled
    contractor.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Contractor recalled for editing. You can now make changes and resubmit.",
        "contractor_id": contractor.id,
        "status": contractor.status
    }


@router.get("/token/{token}/pdf")
async def get_contract_pdf(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Generate and return contract PDF for the given token
    No authentication required - used by contractor to view contract
    """
    contractor = db.query(Contractor).filter(Contractor.contract_token == token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired contract link"
        )

    # Check if token is expired
    if contractor.token_expiry and contractor.token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract link has expired"
        )

    # Check if contract is available for viewing (contractor or superadmin can view)
    if contractor.status not in [ContractorStatus.PENDING_SIGNATURE, ContractorStatus.PENDING_SUPERADMIN_SIGNATURE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been processed"
        )

    # Prepare contractor data for PDF generation (5-page consultant contract)
    cds_data = contractor.cds_form_data or {}
    contractor_data = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'client_name': cds_data.get('clientName', contractor.client_name),
        'client_address': cds_data.get('clientAddress', ''),
        'role': cds_data.get('role', contractor.role),
        'location': cds_data.get('location', contractor.location),
        'duration': contractor.duration or cds_data.get('duration', '6 months'),
        'start_date': contractor.start_date or cds_data.get('startDate', ''),
        'candidate_pay_rate': contractor.candidate_pay_rate or cds_data.get('dayRate', ''),
        'currency': contractor.currency or 'USD'
    }

    # Generate PDF using the 5-page consultant contract generator
    # If contractor has signed, include their signature in the preview
    if contractor.status == ContractorStatus.PENDING_SUPERADMIN_SIGNATURE and contractor.signature_data:
        pdf_buffer = generate_consultant_contract_pdf(
            contractor_data,
            contractor_signature_type=contractor.signature_type,
            contractor_signature_data=contractor.signature_data,
            superadmin_signature_type=None,
            superadmin_signature_data=None,
            signed_date=contractor.signed_date.strftime('%Y-%m-%d') if contractor.signed_date else None
        )
    else:
        # Contractor hasn't signed yet, show blank contract
        pdf_buffer = generate_consultant_contract_pdf(contractor_data)

    # Return PDF as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=contract_{contractor.first_name}_{contractor.surname}.pdf"
        }
    )


@router.post("/sign/{token}")
async def sign_contract(
    token: str,
    signature: SignatureSubmission,
    db: Session = Depends(get_db)
):
    """
    Contractor signs the contract
    """
    contractor = db.query(Contractor).filter(Contractor.contract_token == token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid contract link"
        )

    # Check if token is expired
    if contractor.token_expiry and contractor.token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract link has expired"
        )

    # Check if already signed
    if contractor.status != ContractorStatus.PENDING_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been signed"
        )

    # Update contractor with contractor signature
    contractor.signature_type = signature.signature_type
    contractor.signature_data = signature.signature_data
    contractor.signed_date = datetime.now(timezone.utc)

    # Automatically fetch and add superadmin signature
    # Get the first superadmin user with a signature set
    superadmin = db.query(User).filter(
        User.role == UserRole.SUPERADMIN,
        User.signature_type.isnot(None)
    ).first()

    if not superadmin:
        # If no superadmin with signature, get any superadmin and use their name
        superadmin = db.query(User).filter(
            User.role == UserRole.SUPERADMIN
        ).first()

    if superadmin:
        if superadmin.signature_type and superadmin.signature_data:
            contractor.superadmin_signature_type = superadmin.signature_type
            contractor.superadmin_signature_data = superadmin.signature_data
        else:
            # Fallback to typed name if no signature is set
            contractor.superadmin_signature_type = "typed"
            contractor.superadmin_signature_data = superadmin.name

    contractor.status = ContractorStatus.SIGNED

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Contract signed successfully",
        "contractor_id": contractor.id,
        "status": contractor.status
    }


@router.post("/{contractor_id}/activate")
async def activate_contractor(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Step 3: Admin activates contractor account
    Creates user account and sends login credentials
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if contract is signed
    if contractor.status != ContractorStatus.SIGNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must be signed before activation"
        )

    # Check if user account already exists
    existing_user = db.query(User).filter(User.email == contractor.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account already exists for this email"
        )

    # Generate temporary password
    temp_password = generate_temp_password()

    # Create user account
    user = User(
        id=str(uuid.uuid4()),
        name=f"{contractor.first_name} {contractor.surname}",
        email=contractor.email,
        password_hash=get_password_hash(temp_password),
        role=UserRole.CONTRACTOR,
        is_active=True,
        is_first_login=True,
        contractor_id=contractor.id
    )

    db.add(user)

    # Update contractor status
    contractor.status = ContractorStatus.ACTIVE
    contractor.activated_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contractor)
    db.refresh(user)

    # Send activation email with credentials
    contractor_name = f"{contractor.first_name} {contractor.surname}"
    email_sent = send_activation_email(
        contractor_email=contractor.email,
        contractor_name=contractor_name,
        temporary_password=temp_password
    )

    return {
        "message": "Contractor account activated successfully",
        "contractor_id": contractor.id,
        "user_id": user.id,
        "status": contractor.status,
        "email_sent": email_sent
    }


@router.delete("/{contractor_id}")
async def delete_contractor(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a contractor
    - Admins/Superadmins can delete any contractor
    - Consultants can only delete contractors they created
    - Cannot delete contractors that are signed, active, or suspended
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT:
        # Consultants can only delete their own contractors
        if contractor.consultant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel contractors you created"
            )

    # Prevent deletion of contractors in certain statuses
    if contractor.status in [ContractorStatus.SIGNED, ContractorStatus.ACTIVE, ContractorStatus.SUSPENDED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete contractor with status: {contractor.status}"
        )

    db.delete(contractor)
    db.commit()

    return {"message": "Contractor deleted successfully"}


@router.post("/{contractor_id}/cancel")
async def cancel_contractor(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel a contractor request by setting status to CANCELLED
    - Admins/Superadmins can cancel any contractor
    - Consultants can only cancel contractors they created
    - Cannot cancel contractors that are signed, active, or suspended
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT:
        # Consultants can only cancel their own contractors
        if contractor.consultant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel contractors you created"
            )

    # Prevent cancellation of contractors in certain statuses
    if contractor.status in [ContractorStatus.SIGNED, ContractorStatus.ACTIVE, ContractorStatus.SUSPENDED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel contractor with status: {contractor.status}"
        )

    # Set status to CANCELLED
    contractor.status = ContractorStatus.CANCELLED

    db.commit()
    db.refresh(contractor)

    return {"message": "Contractor request cancelled successfully", "contractor_id": contractor.id, "status": contractor.status.value}


# Superadmin Signature Management Endpoints

@router.put("/superadmin/signature")
async def set_superadmin_signature(
    signature_data: SuperadminSignatureData,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin"]))
):
    """
    Set or update the superadmin's signature
    """
    current_user.signature_type = signature_data.signature_type
    current_user.signature_data = signature_data.signature_data

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Superadmin signature updated successfully",
        "signature_type": current_user.signature_type
    }


@router.get("/superadmin/signature")
async def get_superadmin_signature(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin", "admin"]))
):
    """
    Get the superadmin's signature
    """
    superadmin = db.query(User).filter(
        User.role == UserRole.SUPERADMIN,
        User.signature_type.isnot(None)
    ).first()

    if not superadmin or not superadmin.signature_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No superadmin signature found"
        )

    return {
        "signature_type": superadmin.signature_type,
        "signature_data": superadmin.signature_data,
        "superadmin_name": superadmin.name
    }


# Document Retrieval Endpoints

@router.get("/{contractor_id}/documents")
async def get_contractor_documents(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all documents for a contractor
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if user has access to this contractor's documents
    if current_user.role == UserRole.CONTRACTOR:
        if current_user.contractor_id != contractor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these documents"
            )

    documents = []

    # Add uploaded documents
    if contractor.passport_document:
        documents.append({
            "document_name": "Passport",
            "document_type": "passport",
            "document_url": contractor.passport_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.photo_document:
        documents.append({
            "document_name": "Photo",
            "document_type": "photo",
            "document_url": contractor.photo_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.visa_page_document:
        documents.append({
            "document_name": "Visa Page",
            "document_type": "visa",
            "document_url": contractor.visa_page_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.emirates_id_document:
        documents.append({
            "document_name": "Emirates ID / Karma",
            "document_type": "emirates_id",
            "document_url": contractor.emirates_id_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.degree_document:
        documents.append({
            "document_name": "Degree Certificate",
            "document_type": "degree",
            "document_url": contractor.degree_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.id_front_document:
        documents.append({
            "document_name": "ID Front",
            "document_type": "id_front",
            "document_url": contractor.id_front_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    if contractor.id_back_document:
        documents.append({
            "document_name": "ID Back",
            "document_type": "id_back",
            "document_url": contractor.id_back_document,
            "uploaded_date": contractor.documents_uploaded_date
        })

    # Add third party quote sheet if available
    if contractor.third_party_document:
        documents.append({
            "document_name": "Quote Sheet (Third Party)",
            "document_type": "third_party",
            "document_url": contractor.third_party_document,
            "uploaded_date": contractor.third_party_response_received_date
        })

    # Add other documents (including signed COHF)
    if contractor.other_documents:
        for idx, doc in enumerate(contractor.other_documents):
            doc_type = doc.get("type", "other")
            documents.append({
                "document_name": doc.get("name", f"Other Document {idx + 1}"),
                "document_type": doc_type,
                "document_url": doc.get("data") or doc.get("url"),
                "uploaded_date": doc.get("uploaded_at") or contractor.documents_uploaded_date
            })

    # Add signed COHF document if available and not already in other_documents
    if contractor.cohf_signed_document:
        # Check if COHF is not already in documents (to avoid duplicates)
        cohf_already_added = any(doc.get("document_type") == "cohf_signed" for doc in documents)
        if not cohf_already_added:
            documents.append({
                "document_name": f"COHF - Signed by {contractor.cohf_third_party_name or 'Third Party'}",
                "document_type": "cohf_signed",
                "document_url": contractor.cohf_signed_document,
                "uploaded_date": contractor.cohf_completed_date
            })

    # Add signed contract if available
    if contractor.status in [ContractorStatus.SIGNED, ContractorStatus.ACTIVE]:
        documents.append({
            "document_name": "Signed Contract",
            "document_type": "contract",
            "document_url": f"/api/v1/contractors/{contractor.id}/signed-contract",
            "uploaded_date": contractor.signed_date
        })

    return {
        "contractor_id": contractor_id,
        "documents": documents,
        "total": len(documents)
    }


@router.post("/{contractor_id}/select-route")
async def select_onboarding_route(
    contractor_id: str,
    data: RouteSelection,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Select onboarding route for contractor after documents are uploaded
    Routes: wps, freelancer, uae, saudi, offshore

    Flow after route selection:
    - SAUDI: Quote Sheet → CDS & CS → Review
    - UAE: COHF first → CDS & CS → Review
    - OFFSHORE, FREELANCER, WPS: CDS & CS → Review
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Validate route
    valid_routes = ["wps", "freelancer", "uae", "saudi", "offshore"]
    if data.route not in valid_routes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid route. Must be one of: {', '.join(valid_routes)}"
        )

    # Map route to OnboardingRoute enum
    route_mapping = {
        "wps": OnboardingRoute.WPS,
        "freelancer": OnboardingRoute.FREELANCER,
        "uae": OnboardingRoute.UAE,
        "saudi": OnboardingRoute.SAUDI,
        "offshore": OnboardingRoute.OFFSHORE
    }

    contractor.onboarding_route = route_mapping.get(data.route)

    # Store business type for reference
    route_to_business_type = {
        "wps": "wps",
        "freelancer": "freelancer",
        "uae": "3rd_party_uae",
        "saudi": "3rd_party_saudi",
        "offshore": "offshore"
    }
    contractor.business_type = route_to_business_type.get(data.route, "freelancer")

    # Set status based on route-specific flow
    next_step = ""
    if data.route == "saudi":
        # Saudi route: Goes to Quote Sheet first
        contractor.status = ContractorStatus.PENDING_THIRD_PARTY_QUOTE
        next_step = "quote_sheet"
    elif data.route == "uae":
        # UAE route: Goes to COHF first
        contractor.status = ContractorStatus.PENDING_COHF
        contractor.cohf_status = "draft"
        next_step = "cohf"
    else:
        # WPS, Freelancer, Offshore: Go directly to CDS & CS
        contractor.status = ContractorStatus.PENDING_CDS_CS
        next_step = "cds_form"

    db.commit()
    db.refresh(contractor)

    return {
        "message": f"Onboarding route set to {data.route}",
        "contractor_id": contractor.id,
        "route": data.route,
        "business_type": contractor.business_type,
        "status": contractor.status.value,
        "next_step": next_step
    }


@router.post("/{contractor_id}/clear-route")
async def clear_onboarding_route(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Clear the onboarding route selection for a contractor.
    This allows them to select a different route.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Clear the onboarding route
    contractor.onboarding_route = None
    contractor.business_type = None

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Onboarding route cleared successfully",
        "contractor_id": contractor.id
    }


@router.post("/{contractor_id}/reset-for-testing")
async def reset_contractor_for_testing(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Reset contractor to documents_uploaded status for testing onboarding routes.
    Clears all route-specific data (COHF, quote sheets, CDS, etc.)
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Reset to documents_uploaded status
    contractor.status = ContractorStatus.DOCUMENTS_UPLOADED

    # Clear route selection
    contractor.onboarding_route = None
    contractor.business_type = None
    contractor.sub_route = None
    contractor.third_party_id = None

    # Clear COHF data (UAE route)
    contractor.cohf_data = None
    contractor.cohf_status = None
    contractor.cohf_submitted_date = None
    contractor.cohf_sent_to_3rd_party_date = None
    contractor.cohf_docusign_received_date = None

    # Clear quote sheet data (Saudi route)
    contractor.third_party_quote_sheet_url = None
    contractor.third_party_quote_requested_date = None
    contractor.third_party_quote_received_date = None

    # Clear CDS/CS data
    contractor.cds_form_data = None
    contractor.cds_submitted_date = None

    # Clear work order
    contractor.work_order_sent_date = None
    contractor.work_order_url = None

    # Clear contract data
    contractor.contract_token = None
    contractor.contract_sent_date = None
    contractor.signed_date = None
    contractor.signed_contract_url = None
    contractor.signature_data = None
    contractor.third_party_contract_url = None
    contractor.third_party_contract_uploaded_date = None

    # Clear approval data
    contractor.approved_date = None
    contractor.rejected_date = None
    contractor.rejection_reason = None

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Contractor reset to documents_uploaded status for testing",
        "contractor_id": contractor.id,
        "status": contractor.status,
        "route_cleared": True
    }


@router.post("/{contractor_id}/request-quote-sheet")
async def request_quote_sheet(
    contractor_id: str,
    data: QuoteSheetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Send quote sheet request email to third party with upload link (for SAUDI route)
    Supports both selecting from third party database or entering email directly
    """
    import secrets
    from app.utils.storage import storage
    from app.models.third_party import ThirdParty

    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # If third_party_id is provided, fetch third party details
    third_party_company_name = "Third Party"
    third_party_id_to_save = None

    if data.third_party_id:
        third_party = db.query(ThirdParty).filter(ThirdParty.id == data.third_party_id).first()
        if third_party:
            third_party_company_name = third_party.company_name
            third_party_id_to_save = data.third_party_id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third party not found"
            )
    else:
        # Extract company name from email domain if no third party selected
        third_party_company_name = data.third_party_email.split('@')[1] if '@' in data.third_party_email else "Third Party"

    # Generate upload token (valid for 14 days)
    upload_token = secrets.token_urlsafe(32)
    token_expiry = datetime.utcnow() + timedelta(days=14)

    # Create quote sheet request record
    quote_sheet = QuoteSheet(
        id=str(uuid.uuid4()),
        contractor_id=contractor_id,
        third_party_id=third_party_id_to_save,  # Save third party ID if selected from dropdown
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        third_party_company_name=third_party_company_name,
        consultant_id=current_user.id,
        upload_token=upload_token,
        token_expiry=token_expiry,
        status=QuoteSheetStatus.PENDING,
        created_at=datetime.utcnow()
    )

    db.add(quote_sheet)
    db.commit()
    db.refresh(quote_sheet)

    # Send email with upload link
    upload_url = f"{settings.frontend_url}/quote-sheet/upload?token={upload_token}"

    from app.utils.email import send_quote_sheet_request
    email_sent = send_quote_sheet_request(
        third_party_email=data.third_party_email,
        third_party_name=third_party_company_name,
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        upload_url=upload_url,
        expiry_date=token_expiry,
        email_subject=data.email_subject,
        email_cc=data.email_cc
    )

    if not email_sent:
        # If email fails, delete the quote sheet record
        db.delete(quote_sheet)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

    # Update contractor status to waiting for third party response
    contractor.status = ContractorStatus.PENDING_THIRD_PARTY_RESPONSE
    db.commit()

    return {
        "message": "Quote sheet request sent successfully",
        "contractor_id": contractor_id,
        "quote_sheet_id": quote_sheet.id,
        "upload_token": upload_token,
        "email_sent_to": data.third_party_email,
        "email_cc": data.email_cc
    }


@router.post("/{contractor_id}/send-third-party-request")
async def send_third_party_request(
    contractor_id: str,
    data: ThirdPartyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Send email request to third party company for contractor quote/documents
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify contractor has a third party route selected (UAE or SAUDI)
    if contractor.onboarding_route not in [OnboardingRoute.UAE, OnboardingRoute.SAUDI]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must have UAE or SAUDI third party route selected"
        )

    # Get third party company details
    third_party = db.query(ThirdParty).filter(ThirdParty.id == data.third_party_id).first()

    if not third_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party company not found"
        )

    # Create quote sheet with upload token
    upload_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(days=30)  # 30 days to upload

    quote_sheet = QuoteSheet(
        contractor_id=contractor_id,
        third_party_id=data.third_party_id,
        consultant_id=current_user.id,
        upload_token=upload_token,
        token_expiry=token_expiry,
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        third_party_company_name=third_party.company_name,
        status=QuoteSheetStatus.PENDING
    )

    db.add(quote_sheet)

    # Update contractor with third party company ID and status
    contractor.third_party_company_id = data.third_party_id
    contractor.third_party_email_sent_date = datetime.now(timezone.utc)
    contractor.status = ContractorStatus.PENDING_THIRD_PARTY_RESPONSE

    db.commit()
    db.refresh(quote_sheet)

    # Generate upload URL
    upload_url = f"{settings.frontend_url}/quote-sheet/upload?token={upload_token}"

    # Send email to third party
    try:
        email_sent = send_third_party_contractor_request(
            third_party_email=third_party.contact_person_email,
            third_party_company_name=third_party.company_name,
            email_subject=data.email_subject,
            email_body=data.email_body,
            consultant_name=current_user.name,
            upload_url=upload_url
        )

        # Email sent silently
    except Exception as e:
        pass  # Silent fail on email

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Third party request email sent successfully",
        "contractor_id": contractor.id,
        "third_party_company": third_party.company_name,
        "email_sent_to": third_party.contact_person_email,
        "email_sent_date": contractor.third_party_email_sent_date
    }


# ============= PUBLIC ENDPOINTS (No Auth Required) =============

@router.get("/public/contract-upload/{upload_token}")
async def get_contract_upload_details(
    upload_token: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Get contractor details for contract upload page
    No authentication required
    """
    contractor = db.query(Contractor).filter(
        Contractor.contract_upload_token == upload_token
    ).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract upload link is invalid or has expired"
        )

    # Check if token has expired
    if contractor.contract_upload_token_expiry:
        if datetime.now(timezone.utc) > contractor.contract_upload_token_expiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract upload link has expired"
            )

    # Check if already uploaded
    if contractor.client_uploaded_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract has already been uploaded"
        )

    # Return contractor details for display
    return {
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "role": contractor.role,
        "client_name": contractor.client_name,
        "start_date": contractor.start_date,
        "end_date": contractor.end_date,
        "location": contractor.location,
        "status": contractor.status.value,
        "contractor_id": contractor.id
    }


@router.post("/public/contract-upload/{upload_token}")
async def upload_contractor_contract(
    upload_token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Client uploads contractor contract
    No authentication required
    """
    contractor = db.query(Contractor).filter(
        Contractor.contract_upload_token == upload_token
    ).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract upload link is invalid"
        )

    # Check if token has expired
    if contractor.contract_upload_token_expiry:
        if datetime.now(timezone.utc) > contractor.contract_upload_token_expiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract upload link has expired"
            )

    # Check if already uploaded
    if contractor.client_uploaded_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract has already been uploaded"
        )

    # Upload file to storage
    try:
        from app.utils.storage import storage

        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"contractor-contracts/{contractor.id}/client_contract_{timestamp}_{unique_id}.{file_ext}"

        # Read file content
        content = await file.read()

        # Upload to Supabase Storage
        response = storage.client.storage.from_(storage.bucket).upload(
            filename,
            content,
            file_options={"content-type": file.content_type or "application/pdf"}
        )

        # Get public URL
        file_url = storage.client.storage.from_(storage.bucket).get_public_url(filename)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload contract: {str(e)}"
        )

    # Update contractor with uploaded contract
    contractor.client_uploaded_contract = file_url
    contractor.contract_uploaded_date = datetime.now(timezone.utc)
    contractor.status = ContractorStatus.CONTRACT_UPLOADED

    db.commit()
    db.refresh(contractor)

    # TODO: Send notification to superadmin for approval

    return {
        "message": "Contract uploaded successfully and is pending approval",
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "uploaded_date": contractor.contract_uploaded_date.isoformat(),
        "status": "contract_uploaded"
    }


@router.post("/{contractor_id}/approve-contract")
async def approve_uploaded_contract(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Superadmin approves uploaded contract and sends it to contractor for signature
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status
    if contractor.status != ContractorStatus.CONTRACT_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must be uploaded before approval"
        )

    # Generate contract token for contractor signature
    contract_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(days=7)

    # Update contractor
    contractor.contract_token = contract_token
    contractor.token_expiry = token_expiry
    contractor.contract_approved_date = datetime.now(timezone.utc)
    contractor.contract_approved_by = current_user.id
    contractor.status = ContractorStatus.CONTRACT_APPROVED

    db.commit()
    db.refresh(contractor)

    # Send contract to contractor for signature
    contract_link = f"{settings.frontend_url}/sign-contract/{contract_token}"

    # TODO: Send email to contractor with contract signing link
    return {
        "message": "Contract approved and sent to contractor for signature",
        "contractor_id": contractor.id,
        "contractor_email": contractor.email,
        "contract_signature_link": contract_link,
        "token_expiry": token_expiry.isoformat(),
        "status": "contract_approved"
    }


@router.post("/{contractor_id}/send-contract")
async def send_contract_to_contractor(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Send contractor's contract for signature.

    For WPS/Freelancer/Offshore routes: Can send after APPROVED status (Aventus generates contract)
    For UAE/Saudi routes: Must be WORK_ORDER_COMPLETED (client uploads contract)
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Routes where Aventus generates the contract (no work order needed)
    aventus_contract_routes = [OnboardingRoute.WPS, OnboardingRoute.FREELANCER, OnboardingRoute.OFFSHORE]

    # Check status based on route
    if contractor.onboarding_route in aventus_contract_routes:
        # WPS/Freelancer/Offshore: Can send after approval
        if contractor.status != ContractorStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contractor must be approved before sending contract. Current status: {contractor.status.value}"
            )
    else:
        # UAE/Saudi: Must have work order completed (client uploads contract)
        if contractor.status != ContractorStatus.WORK_ORDER_COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work order must be completed before sending contract. Current status: {contractor.status.value}"
            )

    # Generate contract token
    contract_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days expiry

    # Update contractor with contract token
    contractor.contract_token = contract_token
    contractor.token_expiry = token_expiry
    contractor.sent_date = datetime.now(timezone.utc)
    contractor.status = ContractorStatus.PENDING_SIGNATURE

    db.commit()
    db.refresh(contractor)

    # Send email to contractor
    contractor_name = f"{contractor.first_name} {contractor.surname}"
    contract_link = f"{settings.frontend_url}/sign-contract/{contract_token}"

    try:
        email_sent = send_contract_email(
            contractor_email=contractor.email,
            contractor_name=contractor_name,
            contract_token=contract_token,
            expiry_date=token_expiry
        )

        if email_sent:
            print(f"[SUCCESS] Contract email sent to {contractor.email}")
        else:
            print(f"[WARNING] Failed to send contract email to {contractor.email}")
    except Exception as e:
        print(f"[ERROR] Exception sending contract email: {str(e)}")

    return {
        "message": "Contract sent to contractor for signature",
        "contractor_id": contractor.id,
        "contractor_email": contractor.email,
        "contract_signature_link": contract_link,
        "token_expiry": token_expiry.isoformat(),
        "status": "pending_signature"
    }


@router.get("/public/sign-contract/{contract_token}")
async def get_contract_for_signature(
    contract_token: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Contractor views contract for signing
    No authentication required
    """
    contractor = db.query(Contractor).filter(
        Contractor.contract_token == contract_token
    ).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract link is invalid or has expired"
        )

    # Check if token has expired
    if contractor.token_expiry:
        if datetime.now(timezone.utc) > contractor.token_expiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract signature link has expired"
            )

    # Check if already signed
    if contractor.status == ContractorStatus.SIGNED or contractor.signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been signed"
        )

    # Return contract details and uploaded contract URL
    return {
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "email": contractor.email,
        "role": contractor.role,
        "client_name": contractor.client_name,
        "start_date": contractor.start_date,
        "end_date": contractor.end_date,
        "location": contractor.location,
        "contract_url": contractor.client_uploaded_contract,
        "status": contractor.status.value,
        "contractor_id": contractor.id
    }


@router.post("/public/sign-contract/{contract_token}")
async def contractor_sign_contract(
    contract_token: str,
    signature_data: SignatureSubmission,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Contractor signs the contract
    No authentication required
    After contractor signs, automatically adds superadmin signature
    """
    contractor = db.query(Contractor).filter(
        Contractor.contract_token == contract_token
    ).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract link is invalid"
        )

    # Check if token has expired
    if contractor.token_expiry:
        if datetime.now(timezone.utc) > contractor.token_expiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract signature link has expired"
            )

    # Check if already signed
    if contractor.status == ContractorStatus.SIGNED or contractor.signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been signed"
        )

    # Store contractor signature
    contractor.signature_type = signature_data.signature_type
    contractor.signature_data = signature_data.signature_data
    contractor.signed_date = datetime.now(timezone.utc)
    contractor.status = ContractorStatus.PENDING_SUPERADMIN_SIGNATURE

    db.commit()
    db.refresh(contractor)

    # Contract now awaiting superadmin review and signature
    return {
        "message": "Contract signed successfully - Awaiting administrator review",
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "signed_date": contractor.signed_date.isoformat(),
        "status": "pending_superadmin_signature",
        "next_step": "Administrator will review and sign the contract"
    }


@router.post("/{contractor_id}/superadmin-sign-contract")
async def superadmin_sign_contract(
    contractor_id: str,
    signature_data: SignatureSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin"]))
):
    """
    Superadmin reviews and signs the contract after contractor has signed
    Can use saved signature or upload a new one (custom stamp)
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be pending superadmin signature
    if contractor.status != ContractorStatus.PENDING_SUPERADMIN_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract is not awaiting superadmin signature. Current status: {contractor.status.value}"
        )

    # Check if contractor has already signed
    if not contractor.signature_data or not contractor.signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor has not signed the contract yet"
        )

    # Store superadmin signature
    contractor.superadmin_signature_type = signature_data.signature_type
    contractor.superadmin_signature_data = signature_data.signature_data
    contractor.status = ContractorStatus.SIGNED

    db.commit()
    db.refresh(contractor)

    # Generate signed PDF with both signatures
    print(f"[INFO] Generating signed contract PDF with superadmin signature for contractor {contractor.id}")
    try:
        # Prepare contractor data
        cds_data = contractor.cds_form_data or {}
        contractor_data = {
            'first_name': contractor.first_name,
            'surname': contractor.surname,
            'client_name': cds_data.get('clientName', contractor.client_name),
            'client_address': cds_data.get('clientAddress', ''),
            'role': cds_data.get('role', contractor.role),
            'location': cds_data.get('location', contractor.location),
            'duration': contractor.duration or cds_data.get('duration', '6 months'),
            'start_date': contractor.start_date or cds_data.get('startDate', ''),
            'candidate_pay_rate': contractor.candidate_pay_rate or cds_data.get('dayRate', ''),
            'currency': contractor.currency or 'USD'
        }

        # Generate PDF with both signatures
        pdf_buffer = generate_consultant_contract_pdf(
            contractor_data,
            contractor_signature_type=contractor.signature_type,
            contractor_signature_data=contractor.signature_data,
            superadmin_signature_type=contractor.superadmin_signature_type,
            superadmin_signature_data=contractor.superadmin_signature_data,
            signed_date=contractor.signed_date.strftime('%Y-%m-%d') if contractor.signed_date else None
        )

        # Upload to Supabase in contractor folder
        contractor_filename = f"signed_contract_{contractor.first_name}_{contractor.surname}.pdf"
        contractor_folder = f"contractor-documents/{contractor.id}"
        contractor_file_url = upload_file(pdf_buffer, contractor_filename, contractor_folder)

        # Upload to Supabase in superadmin folder
        superadmin = current_user
        superadmin_filename = f"{contractor.first_name}_{contractor.surname}_contract_{contractor.signed_date.strftime('%Y%m%d')}.pdf"
        superadmin_folder = f"superadmin-contracts/{superadmin.id}"
        pdf_buffer.seek(0)  # Reset buffer for second upload
        superadmin_file_url = upload_file(pdf_buffer, superadmin_filename, superadmin_folder)

        # Update superadmin's contracts_signed array
        contracts_signed = superadmin.contracts_signed or []
        contracts_signed.append({
            'contractor_id': contractor.id,
            'contractor_name': f"{contractor.first_name} {contractor.surname}",
            'contract_url': superadmin_file_url,
            'signed_date': contractor.signed_date.isoformat()
        })
        superadmin.contracts_signed = contracts_signed

        # Update contractor with signed contract URL
        contractor.signed_contract_url = contractor_file_url

        db.commit()
        db.refresh(contractor)
        db.refresh(superadmin)

        print(f"[INFO] Signed contract saved successfully")

    except Exception as e:
        print(f"[ERROR] Failed to generate/upload signed contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate signed contract: {str(e)}"
        )

    # Contract is now fully signed - ready for activation
    return {
        "message": "Contract signed successfully - Ready for activation",
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "signed_date": contractor.signed_date.isoformat(),
        "signed_contract_url": contractor.signed_contract_url,
        "status": "signed",
        "next_step": "Activate contractor account"
    }


@router.post("/{contractor_id}/reset-to-pending-signature")
async def reset_contractor_to_pending_signature(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin"]))
):
    """
    Reset contractor status to pending_superadmin_signature for testing
    SUPERADMIN ONLY - Use this to test the signing workflow
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Reset status and clear superadmin signature
    contractor.status = ContractorStatus.PENDING_SUPERADMIN_SIGNATURE
    contractor.superadmin_signature_type = None
    contractor.superadmin_signature_data = None
    contractor.signed_contract_url = None

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Contractor status reset to pending_superadmin_signature",
        "contractor_id": contractor.id,
        "status": contractor.status.value
    }


@router.post("/{contractor_id}/activate")
async def activate_contractor_account(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Superadmin activates contractor account and sends login credentials
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check status - must be signed
    if contractor.status != ContractorStatus.SIGNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must be signed before activation"
        )

    # Check if contractor user already exists
    existing_user = db.query(User).filter(User.email == contractor.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account already exists for this email"
        )

    # Generate temporary password
    temp_password = generate_temp_password()
    password_hash = get_password_hash(temp_password)

    # Create user account for contractor
    new_user = User(
        id=str(uuid.uuid4()),
        name=f"{contractor.first_name} {contractor.surname}",
        email=contractor.email,
        password_hash=password_hash,
        role=UserRole.CONTRACTOR,
        is_active=True,
        is_first_login=True,
        contractor_id=contractor.id,
        created_at=datetime.now(timezone.utc)
    )

    db.add(new_user)

    # Update contractor status to active
    contractor.status = ContractorStatus.ACTIVE
    contractor.activated_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contractor)
    db.refresh(new_user)

    # Send activation email with credentials
    try:
        email_sent = send_activation_email(
            contractor_email=contractor.email,
            contractor_name=f"{contractor.first_name} {contractor.surname}",
            temp_password=temp_password
        )

        # Email sent silently
    except Exception as e:
        print(f"[ERROR] Exception sending activation email: {str(e)}")

    return {
        "message": "Contractor account activated successfully",
        "contractor_id": contractor.id,
        "user_id": new_user.id,
        "email": contractor.email,
        "status": "active",
        "credentials_sent": True,
        "login_url": f"{settings.frontend_url}/login"
    }


# ============================================
# COHF (Cost of Hire Form) Endpoints - UAE Route
# ============================================

@router.get("/{contractor_id}/cohf/pdf")
async def get_cohf_pdf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Generate and download COHF PDF for a contractor (UAE route)
    Returns a 2-page A4 PDF document
    If COHF has been signed, redirects to the signed document
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # If signed COHF document exists, redirect to it
    if contractor.cohf_signed_document:
        return RedirectResponse(url=contractor.cohf_signed_document)

    # For unsigned COHF, validate contractor is on UAE route
    if contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF is only applicable for UAE route contractors. This contractor is on {contractor.onboarding_route.value if contractor.onboarding_route else 'no'} route."
        )

    # Prepare contractor data from model fields
    contractor_data = {
        "id": str(contractor.id),
        "first_name": contractor.first_name,
        "surname": contractor.surname,
        "email": contractor.email,
        "phone": contractor.phone,
        "nationality": contractor.nationality,
        "dob": contractor.dob,
        "current_location": contractor.current_location,
        "client_name": contractor.client_name,
        "role": contractor.role,
        "location": contractor.location,
        "start_date": contractor.start_date,
        "end_date": contractor.end_date,
        "duration": contractor.duration,
    }

    # Parse COHF data if exists
    cohf_data = {}
    if contractor.cohf_data:
        if isinstance(contractor.cohf_data, str):
            try:
                cohf_data = json.loads(contractor.cohf_data)
            except:
                cohf_data = {}
        elif isinstance(contractor.cohf_data, dict):
            cohf_data = contractor.cohf_data

    # Generate PDF
    pdf_buffer = generate_cohf_pdf(contractor_data, cohf_data)

    # Create filename
    contractor_name = f"{contractor.first_name}_{contractor.surname}".replace(" ", "_")
    filename = f"COHF_{contractor_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )


@router.get("/{contractor_id}/cohf")
async def get_cohf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Get COHF data for a contractor (UAE route)
    If COHF data exists, returns it regardless of current route (for viewing signed COHFs)
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Allow viewing if COHF data already exists (signed or in progress)
    has_cohf_data = contractor.cohf_data or contractor.cohf_status or contractor.cohf_signed_document

    # Only validate route if no COHF data exists yet
    if not has_cohf_data and contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF is only applicable for UAE route contractors. This contractor is on {contractor.onboarding_route.value if contractor.onboarding_route else 'no'} route."
        )

    return {
        "contractor_id": contractor_id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cohf_data": contractor.cohf_data,
        "cohf_status": contractor.cohf_status,
        "cohf_submitted_date": contractor.cohf_submitted_date,
        "cohf_sent_to_3rd_party_date": contractor.cohf_sent_to_3rd_party_date,
        "cohf_docusign_received_date": contractor.cohf_docusign_received_date,
        "cohf_completed_date": contractor.cohf_completed_date,
        "cohf_third_party_name": contractor.cohf_third_party_name,
        "cohf_third_party_signature": contractor.cohf_third_party_signature,
        "onboarding_route": contractor.onboarding_route.value if contractor.onboarding_route else None,
        "status": contractor.status.value
    }


@router.get("/{contractor_id}/cohf/review")
async def review_signed_cohf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Get signed COHF for review after third party has submitted it.
    Returns complete COHF data including signature information.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if COHF has been signed
    if contractor.cohf_status != "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF has not been signed yet. Current status: {contractor.cohf_status}"
        )

    # Note: We don't validate route here since if COHF is signed, it should be viewable

    return {
        "contractor_id": contractor_id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cohf_data": contractor.cohf_data,
        "cohf_status": contractor.cohf_status,
        "signed_date": contractor.cohf_completed_date,
        "third_party_name": contractor.cohf_third_party_name,
        "third_party_signature": contractor.cohf_third_party_signature,
        "onboarding_route": contractor.onboarding_route.value if contractor.onboarding_route else None,
        "status": contractor.status.value,
        "can_proceed_to_cds": contractor.status == ContractorStatus.COHF_COMPLETED
    }


@router.put("/{contractor_id}/cohf")
async def update_cohf(
    contractor_id: str,
    data: COHFSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Update COHF data for a contractor (UAE route)
    Actions: save, send_to_3rd_party, mark_docusign_received, complete
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify this is UAE route
    if contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COHF is only applicable for UAE route"
        )

    # Save COHF data (accept dict directly)
    if data.cohf_data:
        contractor.cohf_data = data.cohf_data

    # Handle action
    if data.action == "save":
        contractor.cohf_status = "draft"
        contractor.cohf_submitted_date = datetime.now(timezone.utc)
        message = "COHF saved as draft"

    elif data.action == "send_to_3rd_party":
        contractor.cohf_status = "sent_to_3rd_party"
        contractor.cohf_sent_to_3rd_party_date = datetime.now(timezone.utc)
        message = "COHF marked as sent to 3rd party"

    elif data.action == "mark_signed":
        contractor.cohf_status = "signed"
        contractor.cohf_docusign_received_date = datetime.now(timezone.utc)
        message = "COHF marked as signed"

    elif data.action == "complete":
        contractor.cohf_status = "completed"
        contractor.cohf_completed_date = datetime.now(timezone.utc)
        contractor.status = ContractorStatus.COHF_COMPLETED
        message = "COHF completed"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be one of: save, send_to_3rd_party, mark_signed, complete"
        )

    db.commit()
    db.refresh(contractor)

    return {
        "message": message,
        "contractor_id": contractor.id,
        "cohf_status": contractor.cohf_status,
        "status": contractor.status.value,
        "next_step": "cds_form" if data.action == "complete" else None
    }


@router.post("/{contractor_id}/cohf/send-email")
async def send_cohf_email_endpoint(
    contractor_id: str,
    data: COHFEmailData,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Send COHF to UAE 3rd party via email
    Generates a token for 3rd party to access and sign the COHF
    Accepts cohf_data directly - no need to save first
    """
    from app.utils.email import send_cohf_email

    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Validate contractor is on UAE route
    if contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF is only for UAE route contractors. This contractor is on {contractor.onboarding_route.value if contractor.onboarding_route else 'no'} route."
        )

    # If cohf_data is provided in the request, use it directly (no save needed)
    # Otherwise, use the saved cohf_data from the contractor
    cohf_data_to_use = data.cohf_data if data.cohf_data else contractor.cohf_data

    if not cohf_data_to_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COHF data must be provided or saved before sending"
        )

    # Store the cohf_data on the contractor for 3rd party to view
    contractor.cohf_data = cohf_data_to_use

    # Generate unique token for 3rd party access
    cohf_token = str(uuid.uuid4())
    token_expiry = datetime.now(timezone.utc) + timedelta(days=7)  # 7 day expiry

    # Update contractor with token and status
    contractor.cohf_token = cohf_token
    contractor.cohf_token_expiry = token_expiry
    contractor.cohf_status = "sent_to_3rd_party"
    contractor.cohf_sent_to_3rd_party_date = datetime.now(timezone.utc)
    contractor.status = ContractorStatus.AWAITING_COHF_SIGNATURE

    db.commit()
    db.refresh(contractor)

    # Send email to 3rd party
    contractor_name = f"{contractor.first_name} {contractor.surname}"
    third_party_company = data.third_party_company or "Third Party"

    email_sent = send_cohf_email(
        third_party_email=data.third_party_email,
        third_party_name=third_party_company,
        contractor_name=contractor_name,
        cohf_token=cohf_token,
        expiry_date=token_expiry
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send COHF email"
        )

    return {
        "message": f"COHF email sent to {data.third_party_email}",
        "contractor_id": contractor.id,
        "cohf_status": contractor.cohf_status,
        "status": contractor.status.value,
        "email_sent_to": data.third_party_email,
        "token_expiry": token_expiry.isoformat()
    }


@router.post("/{contractor_id}/cohf/recall")
async def recall_cohf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Recall COHF that was sent to 3rd party.
    Invalidates the token and allows editing/resending.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Validate contractor is on UAE route
    if contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF is only applicable for UAE route contractors. This contractor is on {contractor.onboarding_route.value if contractor.onboarding_route else 'no'} route."
        )

    if contractor.status != ContractorStatus.AWAITING_COHF_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COHF can only be recalled when awaiting signature"
        )

    # Invalidate the token and reset status
    contractor.cohf_token = None
    contractor.cohf_token_expiry = None
    contractor.cohf_status = "draft"
    contractor.status = ContractorStatus.PENDING_COHF

    db.commit()
    db.refresh(contractor)

    return {
        "message": "COHF recalled successfully. You can now edit and resend.",
        "contractor_id": contractor.id,
        "cohf_status": contractor.cohf_status,
        "status": contractor.status.value
    }


# ============================================
# Public COHF Endpoints (3rd Party Access)
# ============================================

@router.get("/public/cohf/{cohf_token}")
async def get_cohf_by_token(
    cohf_token: str,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for 3rd party to view COHF form.
    No authentication required - uses token from email.
    """
    contractor = db.query(Contractor).filter(Contractor.cohf_token == cohf_token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired COHF link"
        )

    # Check if token has expired
    if contractor.cohf_token_expiry and contractor.cohf_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This COHF link has expired. Please contact Aventus for a new link."
        )

    # Check if already signed
    if contractor.cohf_status == "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This COHF has already been signed."
        )

    # Return COHF data and contractor info
    return {
        "contractor_id": contractor.id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cohf_data": contractor.cohf_data,
        "cohf_status": contractor.cohf_status,
        "already_signed": contractor.cohf_status == "signed"
    }


@router.get("/public/cohf/{cohf_token}/pdf")
async def get_cohf_pdf_by_token(
    cohf_token: str,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for 3rd party to view COHF PDF.
    No authentication required - uses token from email.
    """
    contractor = db.query(Contractor).filter(Contractor.cohf_token == cohf_token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired COHF link"
        )

    # Check if token has expired
    if contractor.cohf_token_expiry and contractor.cohf_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This COHF link has expired."
        )

    # Prepare contractor data
    contractor_data = {
        "id": str(contractor.id),
        "first_name": contractor.first_name,
        "surname": contractor.surname,
        "email": contractor.email,
        "phone": contractor.phone,
        "nationality": contractor.nationality,
        "dob": contractor.dob,
        "current_location": contractor.current_location,
        "client_name": contractor.client_name,
        "role": contractor.role,
        "location": contractor.location,
        "start_date": contractor.start_date,
        "end_date": contractor.end_date,
        "duration": contractor.duration,
    }

    # Parse COHF data
    cohf_data = {}
    if contractor.cohf_data:
        if isinstance(contractor.cohf_data, str):
            try:
                cohf_data = json.loads(contractor.cohf_data)
            except:
                cohf_data = {}
        elif isinstance(contractor.cohf_data, dict):
            cohf_data = contractor.cohf_data

    # Generate PDF
    pdf_buffer = generate_cohf_pdf(contractor_data, cohf_data)

    contractor_name = f"{contractor.first_name}_{contractor.surname}".replace(" ", "_")
    filename = f"COHF_{contractor_name}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )


@router.post("/public/cohf/{cohf_token}/sign")
async def sign_cohf(
    cohf_token: str,
    signature_data: dict,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for 3rd party to sign COHF.
    No authentication required - uses token from email.

    Expected signature_data:
    {
        "signer_name": "John Doe",
        "signature_type": "drawn" or "typed",
        "signature": "base64 data or typed name",
        "cohf_data": { ... any updated form data ... }
    }
    """
    contractor = db.query(Contractor).filter(Contractor.cohf_token == cohf_token).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired COHF link"
        )

    # Check if token has expired
    if contractor.cohf_token_expiry and contractor.cohf_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This COHF link has expired. Please contact Aventus for a new link."
        )

    # Check if already signed
    if contractor.cohf_status == "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This COHF has already been signed."
        )

    # Extract signature info
    signer_name = signature_data.get("signer_name", "")
    signature_type = signature_data.get("signature_type", "typed")
    signature = signature_data.get("signature", "")
    updated_cohf_data = signature_data.get("cohf_data")

    if not signer_name or not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signer name and signature are required"
        )

    # Update COHF data if provided
    if updated_cohf_data:
        contractor.cohf_data = updated_cohf_data

    # Save signature
    contractor.cohf_third_party_name = signer_name
    contractor.cohf_third_party_signature = signature
    contractor.cohf_status = "signed"
    contractor.cohf_completed_date = datetime.now(timezone.utc)

    # Update contractor status to COHF_COMPLETED
    contractor.status = ContractorStatus.COHF_COMPLETED

    # Generate signed PDF and upload to storage
    try:
        contractor_data = {
            "id": str(contractor.id),
            "first_name": contractor.first_name,
            "surname": contractor.surname,
            "email": contractor.email,
            "phone": contractor.phone,
            "nationality": contractor.nationality,
            "dob": contractor.dob,
            "current_location": contractor.current_location,
            "client_name": contractor.client_name,
            "role": contractor.role,
            "location": contractor.location,
            "start_date": contractor.start_date,
            "end_date": contractor.end_date,
            "duration": contractor.duration,
        }

        cohf_data = contractor.cohf_data if isinstance(contractor.cohf_data, dict) else {}

        # Add signature info to cohf_data for PDF generation
        cohf_data["third_party_signer_name"] = signer_name
        cohf_data["third_party_signature"] = signature
        cohf_data["third_party_signature_type"] = signature_type
        cohf_data["signature_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Generate PDF
        pdf_buffer = generate_cohf_pdf(contractor_data, cohf_data)

        # Upload to storage
        contractor_name = f"{contractor.first_name}_{contractor.surname}".replace(" ", "_")
        filename = f"COHF_Signed_{contractor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Upload to Supabase storage (upload_file is sync, not async)
        pdf_url = upload_file(
            pdf_buffer,
            filename,
            f"cohf/{contractor.id}"
        )

        contractor.cohf_signed_document = pdf_url

        # Add to other_documents array so it appears in document list
        other_docs = contractor.other_documents or []
        other_docs.append({
            "name": f"COHF - Signed by {signer_name}",
            "url": pdf_url,
            "type": "cohf_signed",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "signed_by": signer_name
        })
        contractor.other_documents = other_docs

    except Exception as e:
        print(f"Error generating/uploading signed COHF PDF: {e}")
        import traceback
        traceback.print_exc()
        # Continue anyway - the signature is saved

    # Clear the token (one-time use)
    contractor.cohf_token = None
    contractor.cohf_token_expiry = None

    db.commit()
    db.refresh(contractor)

    return {
        "message": "COHF signed successfully",
        "contractor_id": contractor.id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cohf_status": contractor.cohf_status,
        "status": contractor.status.value
    }

# ============================================
# AVENTUS COUNTER-SIGNATURE ENDPOINTS FOR COHF
# ============================================

@router.get("/{contractor_id}/cohf/view-signed")
async def view_signed_cohf(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"]))
):
    """
    View COHF that has been signed by third party, pending Aventus counter-signature.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if contractor.cohf_status != "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"COHF has not been signed by third party yet. Current status: {contractor.cohf_status}"
        )

    return {
        "contractor_id": contractor_id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "cohf_data": contractor.cohf_data,
        "third_party_signature": {
            "name": contractor.cohf_third_party_name,
            "signature": contractor.cohf_third_party_signature,
            "signed_date": contractor.cohf_completed_date.isoformat() if contractor.cohf_completed_date else None
        },
        "cohf_signed_document": contractor.cohf_signed_document,
        "ready_for_counter_signature": not contractor.cohf_aventus_signed_date
    }


@router.post("/{contractor_id}/cohf/counter-sign")
async def counter_sign_cohf(
    contractor_id: str,
    signature_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Aventus admin counter-signs COHF after third party has signed it.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if contractor.cohf_status != "signed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COHF must be signed by third party before counter-signing"
        )

    if contractor.cohf_aventus_signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COHF has already been counter-signed by Aventus"
        )

    contractor.cohf_aventus_signature_type = signature_data.get("signature_type", "typed")
    contractor.cohf_aventus_signature_data = signature_data.get("signature_data")
    contractor.cohf_aventus_signed_date = datetime.now(timezone.utc)
    contractor.cohf_aventus_signed_by = current_user.id

    db.commit()
    db.refresh(contractor)

    return {
        "message": "COHF counter-signed successfully by Aventus",
        "contractor_id": contractor_id,
        "aventus_signed_by": current_user.name,
        "aventus_signed_date": contractor.cohf_aventus_signed_date.isoformat()
    }

# ============================================
# AVENTUS COUNTER-SIGNATURE ENDPOINTS FOR QUOTE SHEETS (SAUDI ROUTE)
# ============================================

@router.get("/{contractor_id}/quote-sheet/view-signed")
async def view_signed_quote_sheet(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"]))
):
    """
    View Quote Sheet that has been signed by third party, pending Aventus counter-signature.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if not contractor.quote_sheet_third_party_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote sheet has not been signed by third party yet"
        )

    return {
        "contractor_id": contractor_id,
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "costing_sheet_data": contractor.costing_sheet_data,
        "third_party_signature": {
            "name": contractor.quote_sheet_third_party_name,
            "signature": contractor.quote_sheet_third_party_signature,
            "signed_date": contractor.quote_sheet_third_party_signed_date.isoformat() if contractor.quote_sheet_third_party_signed_date else None
        },
        "third_party_document": contractor.third_party_document,
        "ready_for_counter_signature": not contractor.quote_sheet_aventus_signed_date
    }


@router.post("/{contractor_id}/quote-sheet/counter-sign")
async def counter_sign_quote_sheet(
    contractor_id: str,
    signature_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Aventus admin counter-signs Quote Sheet after third party has signed it.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if not contractor.quote_sheet_third_party_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote sheet must be signed by third party before counter-signing"
        )

    if contractor.quote_sheet_aventus_signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote sheet has already been counter-signed by Aventus"
        )

    contractor.quote_sheet_aventus_signature_type = signature_data.get("signature_type", "typed")
    contractor.quote_sheet_aventus_signature_data = signature_data.get("signature_data")
    contractor.quote_sheet_aventus_signed_date = datetime.now(timezone.utc)
    contractor.quote_sheet_aventus_signed_by = current_user.id

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Quote sheet counter-signed successfully by Aventus",
        "contractor_id": contractor_id,
        "aventus_signed_by": current_user.name,
        "aventus_signed_date": contractor.quote_sheet_aventus_signed_date.isoformat()
    }


# ============================================
# UAE 3rd Party Contract Upload Endpoints
# ============================================

@router.post("/{contractor_id}/upload-3rd-party-contract")
async def upload_third_party_contract(
    contractor_id: str,
    contract_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Upload contract received from UAE 3rd party.
    For UAE route, the 3rd party sends their contract to Aventus (instead of Aventus sending contract to contractor).
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify this is UAE route
    if contractor.onboarding_route != OnboardingRoute.UAE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="3rd party contract upload is only applicable for UAE route"
        )

    # Verify contractor is in correct status (after work order completed)
    valid_statuses = [
        ContractorStatus.WORK_ORDER_COMPLETED,
        ContractorStatus.PENDING_3RD_PARTY_CONTRACT
    ]
    if contractor.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contractor must be in status: {', '.join([s.value for s in valid_statuses])}"
        )

    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if contract_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPEG, and PNG files are allowed"
        )

    # Upload file to storage
    try:
        file_content = await contract_file.read()
        file_url = await upload_file(
            file_content=file_content,
            filename=contract_file.filename,
            content_type=contract_file.content_type,
            folder=f"contractors/{contractor_id}/3rd-party-contract"
        )

        # Update contractor record
        contractor.third_party_contract_url = file_url
        contractor.third_party_contract_uploaded_date = datetime.now(timezone.utc)
        contractor.status = ContractorStatus.CONTRACT_UPLOADED

        db.commit()
        db.refresh(contractor)

        return {
            "message": "3rd party contract uploaded successfully",
            "contractor_id": contractor.id,
            "contract_url": file_url,
            "uploaded_date": contractor.third_party_contract_uploaded_date,
            "status": contractor.status.value,
            "next_step": "activate"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload contract: {str(e)}"
        )


@router.get("/{contractor_id}/3rd-party-contract")
async def get_third_party_contract(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Get the 3rd party contract URL for UAE route
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if not contractor.third_party_contract_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No 3rd party contract uploaded yet"
        )

    return {
        "contractor_id": contractor.id,
        "contract_url": contractor.third_party_contract_url,
        "uploaded_date": contractor.third_party_contract_uploaded_date
    }


@router.post("/{contractor_id}/approve-3rd-party-contract")
async def approve_third_party_contract(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Approve the 3rd party contract for UAE route.
    After approval, contractor can be activated.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    if contractor.status != ContractorStatus.CONTRACT_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract must be uploaded before approval"
        )

    if not contractor.third_party_contract_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No 3rd party contract uploaded"
        )

    # Approve contract - for UAE route, skip to SIGNED status
    contractor.status = ContractorStatus.SIGNED
    contractor.contract_approved_date = datetime.now(timezone.utc)
    contractor.contract_approved_by = current_user.id
    contractor.signed_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contractor)

    return {
        "message": "3rd party contract approved. Contractor ready for activation.",
        "contractor_id": contractor.id,
        "status": contractor.status.value,
        "next_step": "activate"
    }


@router.post("/{contractor_id}/fix-status")
async def fix_contractor_status(
    contractor_id: str,
    target_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Admin endpoint to manually fix contractor status.
    Useful for fixing contractors stuck in wrong status due to bugs.

    Valid target statuses:
    - pending_cds_cs: For contractors who have quote sheet uploaded but status wasn't updated
    - pending_third_party_response: For contractors awaiting third party response
    - documents_uploaded: Reset to documents uploaded state
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Map string to enum
    status_map = {
        "pending_cds_cs": ContractorStatus.PENDING_CDS_CS,
        "pending_third_party_response": ContractorStatus.PENDING_THIRD_PARTY_RESPONSE,
        "pending_third_party_quote": ContractorStatus.PENDING_THIRD_PARTY_QUOTE,
        "documents_uploaded": ContractorStatus.DOCUMENTS_UPLOADED,
        "pending_review": ContractorStatus.PENDING_REVIEW,
        "pending_cohf": ContractorStatus.PENDING_COHF,
        "cohf_completed": ContractorStatus.COHF_COMPLETED,
    }

    if target_status not in status_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target status. Valid options: {list(status_map.keys())}"
        )

    old_status = contractor.status.value
    contractor.status = status_map[target_status]
    contractor.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(contractor)

    return {
        "message": f"Contractor status updated from {old_status} to {target_status}",
        "contractor_id": contractor.id,
        "old_status": old_status,
        "new_status": contractor.status.value
    }

