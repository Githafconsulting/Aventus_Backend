# Contractors API routes
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
    QuoteSheetRequest
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
from app.utils.pdf_generator import generate_contract_pdf
from app.utils.work_order_pdf_generator import generate_work_order_pdf
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
    country: Optional[str] = Form(None),
    current_location: Optional[str] = Form(None),
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
        contractor.country = country
        contractor.current_location = current_location
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

    # Check if contractor is ready for CDS (either documents uploaded or pending CDS/CS)
    if contractor.status not in [ContractorStatus.DOCUMENTS_UPLOADED, ContractorStatus.PENDING_CDS_CS]:
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
    if 'country' in form_data:
        contractor.country = form_data['country']
    if 'currentLocation' in form_data:
        contractor.current_location = form_data['currentLocation']
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
    if 'managementAddressLine2' in form_data:
        contractor.management_address_line2 = form_data['managementAddressLine2']
    if 'managementAddressLine3' in form_data:
        contractor.management_address_line3 = form_data['managementAddressLine3']
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
    if 'clientId' in form_data:
        contractor.client_id = form_data['clientId']
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

    # Update summary calculations
    if 'contractorTotalFixedCosts' in form_data:
        contractor.contractor_total_fixed_costs = form_data['contractorTotalFixedCosts']
    if 'estimatedMonthlyGP' in form_data:
        contractor.estimated_monthly_gp = form_data['estimatedMonthlyGP']

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

    # Keep status unchanged (either DOCUMENTS_UPLOADED or PENDING_CDS_CS)
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

    # Check if contractor is ready for costing sheet submission
    if contractor.status not in [ContractorStatus.DOCUMENTS_UPLOADED, ContractorStatus.PENDING_CDS_CS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CDS form must be completed before submitting costing sheet"
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

    # Update status to CDS & CS completed (awaiting admin review)
    contractor.status = ContractorStatus.CDS_CS_COMPLETED

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

    # Check status - must be pending review
    if contractor.status != ContractorStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contractor must be pending review status for approval/rejection"
        )

    if not approval_data.approved:
        # REJECTION: Return contractor to CDS_CS_COMPLETED status so consultant can edit and resubmit
        contractor.reviewed_date = datetime.now(timezone.utc)
        contractor.reviewed_by = current_user.id
        contractor.status = ContractorStatus.CDS_CS_COMPLETED
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
            "status": "cds_cs_completed"
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


@router.post("/{contractor_id}/send-work-order")
async def send_work_order_to_client(
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
    client_email = client.contact_person_email if client.contact_person_email else None
    work_order_link = f"{settings.frontend_url}/sign-work-order/{signature_token}"

    if client_email:
        try:
            email_sent = send_work_order_to_client(
                client_email=client_email,
                client_company_name=client.company_name,
                work_order_number=work_order_number,
                contractor_name=f"{contractor.first_name} {contractor.surname}",
                signature_link=work_order_link
            )

            if email_sent:
                print(f"[SUCCESS] Work order email sent to {client_email}")
            else:
                print(f"[WARNING] Failed to send work order email to {client_email}")
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
    print(f"[INFO] Work order for contractor {contractor_id} forwarded to superadmin for approval")

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
    print(f"[INFO] Contract upload request sent to client {client.company_name}")
    print(f"[INFO] Upload link: {upload_link}")
    print(f"[INFO] Email should be sent to: {client_email}")

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

    # Check status - can only recall from cds_cs_completed
    if contractor.status != ContractorStatus.CDS_CS_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only recall contractors that have completed CDS & CS"
        )

    # Only allow consultant to recall their own contractors (or admin/superadmin)
    if current_user.role == UserRole.CONSULTANT and contractor.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only recall your own contractors"
        )

    # Change status back to pending_cds_cs so consultant can edit
    contractor.status = ContractorStatus.PENDING_CDS_CS
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

    return {"message": "Contractor request cancelled successfully", "contractor": contractor}


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
    Routes: wps, freelancer, uae, saudi, offshore
    Sub-routes: direct, third_party (for uae and saudi)
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

    # Validate sub-route
    valid_sub_routes = ["direct", "third_party"]
    if data.sub_route and data.sub_route not in valid_sub_routes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sub-route. Must be one of: {', '.join(valid_sub_routes)}"
        )

    # Store route information
    # For backward compatibility, map new routes to business_type
    route_to_business_type = {
        "wps": "WPS",
        "freelancer": "Freelancer",
        "uae": "3RD Party" if data.sub_route == "third_party" else "Freelancer",
        "saudi": "3RD Party" if data.sub_route == "third_party" else "Freelancer",
        "offshore": "Freelancer"
    }

    contractor.business_type = route_to_business_type.get(data.route, "Freelancer")

    # Set onboarding route
    if data.sub_route == "third_party":
        contractor.onboarding_route = OnboardingRoute.THIRD_PARTY
        contractor.status = ContractorStatus.PENDING_THIRD_PARTY_RESPONSE
    else:
        # Direct route (WPS, Freelancer, UAE-Direct, Offshore)
        contractor.onboarding_route = OnboardingRoute.WPS_FREELANCER
        # Status stays as DOCUMENTS_UPLOADED until CDS & CS forms are completed

    db.commit()
    db.refresh(contractor)

    return {
        "message": f"Onboarding route set to {data.route} ({data.sub_route})",
        "contractor_id": contractor.id,
        "route": data.route,
        "sub_route": data.sub_route,
        "business_type": contractor.business_type,
        "status": contractor.status
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

    from app.utils.email import send_third_party_contractor_request
    email_sent = send_third_party_contractor_request(
        third_party_email=data.third_party_email,
        third_party_company_name=third_party_company_name,
        email_subject=data.email_subject,
        email_body=data.email_message,
        consultant_name=current_user.name,
        upload_url=upload_url,
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
    print(f"[INFO] Contract approved for contractor {contractor_id}")
    print(f"[INFO] Contract signature link: {contract_link}")
    print(f"[INFO] Email should be sent to: {contractor.email}")

    return {
        "message": "Contract approved and sent to contractor for signature",
        "contractor_id": contractor.id,
        "contractor_email": contractor.email,
        "contract_signature_link": contract_link,
        "token_expiry": token_expiry.isoformat(),
        "status": "contract_approved"
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
    contractor.status = ContractorStatus.SIGNED

    # AUTO-SIGN: Automatically add superadmin signature
    # Get superadmin user for signature
    superadmin = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
    if superadmin and superadmin.signature_data:
        contractor.superadmin_signature_type = superadmin.signature_type or "typed"
        contractor.superadmin_signature_data = superadmin.signature_data
        print(f"[INFO] Auto-signed with superadmin signature for contractor {contractor.id}")
    else:
        print(f"[WARNING] No superadmin signature found for auto-signing contractor {contractor.id}")

    db.commit()
    db.refresh(contractor)

    # Contract is now fully signed - ready for activation
    print(f"[INFO] Contract signed by contractor {contractor.id}")
    print(f"[INFO] Ready for account activation")

    return {
        "message": "Contract signed successfully - Your account is ready for activation",
        "contractor_name": f"{contractor.first_name} {contractor.surname}",
        "signed_date": contractor.signed_date.isoformat(),
        "status": "signed",
        "next_step": "Account activation by administrator"
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

        if email_sent:
            print(f"[SUCCESS] Activation email sent to {contractor.email}")
        else:
            print(f"[WARNING] Failed to send activation email to {contractor.email}")
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

