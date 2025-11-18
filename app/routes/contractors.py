from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
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
    ThirdPartyRequest
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
    send_third_party_contractor_request
)
from app.utils.contract_template import populate_contract_template
from app.utils.pdf_generator import generate_contract_pdf
from app.config import settings
from fastapi.responses import StreamingResponse

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
            document_token=document_token,
            expiry_date=token_expiry
        )

        if email_sent:
            print(f"[SUCCESS] Document upload email sent to {contractor.email}")
        else:
            print(f"[WARNING] Failed to send document upload email to {contractor.email}")
    except Exception as e:
        print(f"[ERROR] Exception sending document upload email: {str(e)}")

    print(f"[INFO] Document upload URL: {settings.frontend_url}/documents/upload/{document_token}")

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Admin views the signed contract PDF
    Supports both Authorization header and query parameter token
    """
    # Verify user has admin or superadmin role
    if current_user.role not in ["admin", "superadmin"]:
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

    # Convert contractor model to dictionary
    contractor_dict = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'email': contractor.email,
        'dob': contractor.dob,
        'nationality': contractor.nationality,
        'role': contractor.role,
        'client_name': contractor.client_name,
        'start_date': contractor.start_date,
        'end_date': contractor.end_date,
        'duration': contractor.duration,
        'location': contractor.location,
        'currency': contractor.currency,
        'pay_rate': contractor.candidate_pay_rate,
        'charge_rate': contractor.client_charge_rate,
        'signature_data': contractor.signature_data,
        'signature_type': contractor.signature_type,
        'signed_date': contractor.signed_date,
        'superadmin_signature_data': contractor.superadmin_signature_data,
        'superadmin_signature_type': contractor.superadmin_signature_type,
    }

    # Generate PDF with both signatures
    pdf_buffer = generate_contract_pdf(contractor_dict, include_signature=True)

    # Return PDF as streaming response
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=signed_contract_{contractor.first_name}_{contractor.surname}.pdf"
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
    marital_status: Optional[str] = Form(None),
    number_of_children: Optional[str] = Form(None),
    phone: str = Form(...),
    home_address: str = Form(...),
    address_line2: Optional[str] = Form(None),
    address_line3: Optional[str] = Form(None),
    address_line4: Optional[str] = Form(None),
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
        contractor.marital_status = marital_status
        contractor.number_of_children = number_of_children
        contractor.phone = phone
        contractor.home_address = home_address
        contractor.address_line2 = address_line2
        contractor.address_line3 = address_line3
        contractor.address_line4 = address_line4
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
        print(f"[INFO] Documents uploaded for contractor {contractor.email}")

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
                    print(f"[SUCCESS] Notification sent to consultant {consultant.email}")
                except Exception as e:
                    print(f"[ERROR] Failed to send consultant notification: {str(e)}")

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

    # Check if documents are uploaded
    if contractor.status != ContractorStatus.DOCUMENTS_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents must be uploaded before completing CDS"
        )

    # Extract nested data object if it exists
    form_data = cds_data.get('data', cds_data)

    # Update personal details (update even if empty to allow clearing fields)
    if 'firstName' in form_data:
        contractor.first_name = form_data['firstName']
    if 'surname' in form_data:
        contractor.surname = form_data['surname']
    if 'gender' in form_data:
        contractor.gender = form_data['gender']
    if 'nationality' in form_data:
        contractor.nationality = form_data['nationality']
    if 'homeAddress' in form_data:
        contractor.home_address = form_data['homeAddress']
    if 'addressLine3' in form_data:
        contractor.address_line3 = form_data['addressLine3']
    if 'addressLine4' in form_data:
        contractor.address_line4 = form_data['addressLine4']
    if 'phone' in form_data:
        contractor.phone = form_data['phone']
    if 'email' in form_data:
        contractor.email = form_data['email']
    if 'dob' in form_data:
        contractor.dob = form_data['dob']

    # Update management company details
    if 'businessType' in form_data:
        contractor.business_type = form_data['businessType']
    if 'thirdPartyId' in form_data:
        contractor.third_party_id = form_data['thirdPartyId']
    if 'umbrellaCompanyName' in form_data:
        contractor.umbrella_company_name = form_data['umbrellaCompanyName']
    if 'registeredAddress' in form_data:
        contractor.registered_address = form_data['registeredAddress']
    if 'companyVATNo' in form_data:
        contractor.company_vat_no = form_data['companyVATNo']
    if 'companyName' in form_data:
        contractor.company_name = form_data['companyName']
    if 'accountNumber' in form_data:
        contractor.account_number = form_data['accountNumber']
    if 'ibanNumber' in form_data:
        contractor.iban_number = form_data['ibanNumber']
    if 'companyRegNo' in form_data:
        contractor.company_reg_no = form_data['companyRegNo']

    # Update placement details
    if 'clientName' in form_data:
        contractor.client_name = form_data['clientName']
    if 'projectName' in form_data:
        contractor.project_name = form_data['projectName']
    if 'role' in form_data:
        contractor.role = form_data['role']
    if 'startDate' in form_data:
        contractor.start_date = form_data['startDate']
    if 'endDate' in form_data:
        contractor.end_date = form_data['endDate']
    if 'location' in form_data:
        contractor.location = form_data['location']
    if 'duration' in form_data:
        contractor.duration = form_data['duration']
    if 'currency' in form_data:
        contractor.currency = form_data['currency']
    if 'clientChargeRate' in form_data:
        contractor.client_charge_rate = form_data['clientChargeRate']
    if 'candidatePayRate' in form_data:
        contractor.candidate_pay_rate = form_data['candidatePayRate']
    if 'candidateBasicSalary' in form_data:
        contractor.candidate_basic_salary = form_data['candidateBasicSalary']

    # Update monthly costs
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

    # Update provisions
    if 'eosb' in form_data:
        contractor.eosb = form_data['eosb']
    if 'vacationPay' in form_data:
        contractor.vacation_pay = form_data['vacationPay']
    if 'sickLeave' in form_data:
        contractor.sick_leave = form_data['sickLeave']
    if 'otherProvision' in form_data:
        contractor.other_provision = form_data['otherProvision']

    # Update one-time costs
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

    # Update additional info
    if 'upfrontInvoices' in form_data:
        contractor.upfront_invoices = form_data['upfrontInvoices']
    if 'securityDeposit' in form_data:
        contractor.security_deposit = form_data['securityDeposit']
    if 'laptopProvider' in form_data:
        contractor.laptop_provider = form_data['laptopProvider']
    if 'otherNotes' in form_data:
        contractor.other_notes = form_data['otherNotes']

    # Update Aventus Deal details
    if 'consultant' in form_data:
        contractor.consultant = form_data['consultant']
    if 'anySplits' in form_data:
        contractor.any_splits = form_data['anySplits']
    if 'resourcer' in form_data:
        contractor.resourcer = form_data['resourcer']

    # Update invoice details
    if 'timesheetRequired' in form_data:
        contractor.timesheet_required = form_data['timesheetRequired']
    if 'timesheetApproverName' in form_data:
        contractor.timesheet_approver_name = form_data['timesheetApproverName']
    if 'invoiceEmail' in form_data:
        contractor.invoice_email = form_data['invoiceEmail']
    if 'clientContact' in form_data:
        contractor.client_contact = form_data['clientContact']
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
    if 'invoiceTaxNumber' in form_data:
        contractor.invoice_tax_number = form_data['invoiceTaxNumber']
    if 'contractorPayFrequency' in form_data:
        contractor.contractor_pay_frequency = form_data['contractorPayFrequency']
    if 'clientInvoiceFrequency' in form_data:
        contractor.client_invoice_frequency = form_data['clientInvoiceFrequency']
    if 'clientPaymentTerms' in form_data:
        contractor.client_payment_terms = form_data['clientPaymentTerms']
    if 'invoicingPreferences' in form_data:
        contractor.invoicing_preferences = form_data['invoicingPreferences']
    if 'invoiceInstructions' in form_data:
        contractor.invoice_instructions = form_data['invoiceInstructions']
    if 'supportingDocsRequired' in form_data:
        contractor.supporting_docs_required = form_data['supportingDocsRequired']
    if 'poRequired' in form_data:
        contractor.po_required = form_data['poRequired']
    if 'poNumber' in form_data:
        contractor.po_number = form_data['poNumber']

    # Update pay details
    if 'umbrellaOrDirect' in form_data:
        contractor.umbrella_or_direct = form_data['umbrellaOrDirect']
    if 'candidateBankDetails' in form_data:
        contractor.candidate_bank_details = form_data['candidateBankDetails']
    if 'candidateIBAN' in form_data:
        contractor.candidate_iban = form_data['candidateIBAN']

    # Keep status as DOCUMENTS_UPLOADED - don't change it yet
    # Status will be changed to PENDING_REVIEW after costing sheet submission

    db.commit()
    db.refresh(contractor)

    print(f"[INFO] CDS form saved for contractor {contractor.email}")

    return {
        "message": "CDS form saved successfully",
        "contractor_id": contractor.id,
        "status": contractor.status
    }


@router.put("/{contractor_id}/costing-sheet")
async def submit_costing_sheet(
    contractor_id: str,
    expenses: str = Form("[]"),
    notes: str = Form(""),
    total_amount: str = Form("0"),
    costing_documents: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["consultant", "admin", "superadmin"]))
):
    """
    Step 3: Consultant submits costing sheet with expense details (optional)
    This changes status to PENDING_REVIEW and sends notification to admins
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Check if documents are uploaded
    if contractor.status != ContractorStatus.DOCUMENTS_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documents must be uploaded before submitting costing sheet"
        )

    # Parse expenses JSON
    try:
        expenses_data = json.loads(expenses)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expenses data format"
        )

    # Store costing sheet data
    costing_sheet_data = {
        "expenses": expenses_data,
        "notes": notes,
        "total_amount": total_amount,
        "submitted_at": datetime.now().isoformat()
    }

    # Handle file uploads for receipts (if provided)
    # Note: Receipt files come as separate form fields named receipt_0, receipt_1, etc.
    # For now, we'll store the expense data without file URLs
    # You can extend this to upload to Supabase storage if needed

    # Handle costing documents upload (if provided)
    if costing_documents:
        doc_urls = []
        for doc in costing_documents:
            if doc and doc.filename:
                # TODO: Upload to Supabase storage
                # For now, just store the filename
                doc_urls.append(doc.filename)
        if doc_urls:
            costing_sheet_data["costing_documents"] = doc_urls

    contractor.costing_sheet_data = costing_sheet_data

    # Update status to pending review
    contractor.status = ContractorStatus.PENDING_REVIEW

    db.commit()
    db.refresh(contractor)

    # Send notification email to admin/superadmin
    print(f"[INFO] Costing sheet submitted for contractor {contractor.email}")

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
            print(f"[SUCCESS] Review notification sent to {len(admin_emails)} admins")
        except Exception as e:
            print(f"[ERROR] Failed to send review notification: {str(e)}")

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

    # Check status
    if contractor.status != ContractorStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be in pending review status"
        )

    if not approval_data.approved:
        # If not approved, set status to REJECTED
        contractor.reviewed_date = datetime.now(timezone.utc)
        contractor.reviewed_by = current_user.id
        contractor.status = ContractorStatus.REJECTED
        # Optionally store rejection notes
        db.commit()
        db.refresh(contractor)

        return {
            "message": "Contractor rejected",
            "contractor_id": contractor.id,
            "approved": False,
            "status": "rejected"
        }

    # Generate unique contract token
    contract_token = generate_unique_token()
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.contract_token_expiry_hours)

    # Update contractor
    contractor.contract_token = contract_token
    contractor.token_expiry = token_expiry
    contractor.reviewed_date = datetime.now(timezone.utc)
    contractor.reviewed_by = current_user.id
    contractor.approved_date = datetime.now(timezone.utc)
    contractor.approved_by = current_user.id
    contractor.status = ContractorStatus.APPROVED

    # Generate contract from template
    contractor_dict = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'email': contractor.email,
        'phone': contractor.phone,
        'dob': contractor.dob,
        'nationality': contractor.nationality,
        'home_address': contractor.home_address,
        'role': contractor.role,
        'client_name': contractor.client_name,
        'start_date': contractor.start_date,
        'end_date': contractor.end_date,
        'duration': contractor.duration,
        'location': contractor.location,
        'currency': contractor.currency,
        'pay_rate': contractor.candidate_pay_rate,
        'charge_rate': contractor.client_charge_rate,
    }

    generated_contract = populate_contract_template(contractor_dict)
    contractor.generated_contract = generated_contract

    db.commit()
    db.refresh(contractor)

    # Send contract email to contractor
    contractor_name = f"{contractor.first_name} {contractor.surname}"

    try:
        email_sent = send_contract_email(
            contractor_email=contractor.email,
            contractor_name=contractor_name,
            contract_token=contract_token,
            expiry_date=token_expiry
        )

        if email_sent:
            contractor.sent_date = datetime.now(timezone.utc)
            contractor.status = ContractorStatus.PENDING_SIGNATURE
            db.commit()
            db.refresh(contractor)
            print(f"[SUCCESS] Contract email sent to {contractor.email}")
        else:
            print(f"[WARNING] Failed to send contract email to {contractor.email}")
    except Exception as e:
        print(f"[ERROR] Exception sending email: {str(e)}")

    return {
        "message": "Contractor approved and contract sent",
        "contractor_id": contractor.id,
        "status": contractor.status,
        "contract_token": contract_token
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

    # Check if already signed
    if contractor.status not in [ContractorStatus.PENDING_SIGNATURE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This contract has already been processed"
        )

    # Convert contractor model to dictionary
    contractor_dict = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'email': contractor.email,
        'dob': contractor.dob,
        'nationality': contractor.nationality,
        'role': contractor.role,
        'client_name': contractor.client_name,
        'start_date': contractor.start_date,
        'end_date': contractor.end_date,
        'duration': contractor.duration,
        'location': contractor.location,
        'currency': contractor.currency,
        'pay_rate': contractor.candidate_pay_rate,
        'charge_rate': contractor.client_charge_rate,
    }

    # Generate PDF
    pdf_buffer = generate_contract_pdf(contractor_dict)

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
            print(f"[INFO] Added stored superadmin signature")
        else:
            # Fallback to typed name if no signature is set
            contractor.superadmin_signature_type = "typed"
            contractor.superadmin_signature_data = superadmin.name
            print(f"[INFO] Added default superadmin signature: {superadmin.name}")
    else:
        print(f"[WARNING] No superadmin found to add signature")

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

    # Add other documents
    if contractor.other_documents:
        for idx, doc in enumerate(contractor.other_documents):
            documents.append({
                "document_name": doc.get("name", f"Other Document {idx + 1}"),
                "document_type": "other",
                "document_url": doc.get("data") or doc.get("url"),
                "uploaded_date": contractor.documents_uploaded_date
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
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()

    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify contractor is in correct status
    if contractor.status != ContractorStatus.DOCUMENTS_UPLOADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot select route. Contractor status is {contractor.status}"
        )

    # Validate and set route
    if data.route not in ["wps_freelancer", "third_party"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route. Must be 'wps_freelancer' or 'third_party'"
        )

    contractor.onboarding_route = OnboardingRoute(data.route)

    # If third party route selected, update status to pending third party response
    if data.route == "third_party":
        contractor.status = ContractorStatus.PENDING_THIRD_PARTY_RESPONSE
    # If WPS/Freelancer route, status stays as DOCUMENTS_UPLOADED

    db.commit()
    db.refresh(contractor)

    return {
        "message": f"Onboarding route set to {data.route}",
        "contractor_id": contractor.id,
        "route": contractor.onboarding_route,
        "status": contractor.status
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

    # Verify contractor has third party route selected
    if contractor.onboarding_route != OnboardingRoute.THIRD_PARTY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must have third party route selected"
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

    # Update contractor with third party company ID
    contractor.third_party_company_id = data.third_party_id
    contractor.third_party_email_sent_date = datetime.now(timezone.utc)

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

        if not email_sent:
            print(f"[WARNING] Failed to send email to {third_party.contact_person_email}")
        else:
            print(f"[SUCCESS] Third party request email sent to {third_party.contact_person_email}")
    except Exception as e:
        print(f"[ERROR] Exception sending email: {str(e)}")

    db.commit()
    db.refresh(contractor)

    return {
        "message": "Third party request email sent successfully",
        "contractor_id": contractor.id,
        "third_party_company": third_party.company_name,
        "email_sent_to": third_party.contact_person_email,
        "email_sent_date": contractor.third_party_email_sent_date
    }
 
