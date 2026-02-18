"""
Contract routes for managing contract templates, generation, signing, and activation
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.contract import Contract, ContractTemplate, ContractStatus
from app.models.contractor import Contractor
from app.models.user import User, UserRole
from app.utils.auth import get_current_active_user, require_role
from app.utils.email import send_contract_email, send_activation_email, send_signed_contract_email
from app.utils.contract_pdf_generator import generate_consultant_contract_pdf
from app.utils.storage import upload_file
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
import secrets
import string

router = APIRouter(prefix="/contracts", tags=["contracts"])


# Pydantic models
class ContractTemplateCreate(BaseModel):
    name: str
    template_content: str
    version: str = "1.0"


class ContractTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_content: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class ContractGenerate(BaseModel):
    contractor_id: str
    template_id: int
    contract_content: str  # Pre-filled contract content from frontend


class ContractSign(BaseModel):
    signature_type: str  # "typed" or "drawn"
    signature_data: str
    notes: Optional[str] = None


class ContractActivate(BaseModel):
    temporary_password: str


class AventusCounterSign(BaseModel):
    signature_type: str  # "typed" or "drawn"
    signature_data: str
    signer_name: str = "Richard"  # Default to Richard


def generate_token(length: int = 32) -> str:
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_temporary_password(length: int = 12) -> str:
    """Generate a temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Contract Template endpoints
@router.post("/templates")
def create_contract_template(
    template: ContractTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new contract template"""
    new_template = ContractTemplate(
        name=template.name,
        template_content=template.template_content,
        version=template.version
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    return {
        "message": "Contract template created successfully",
        "template_id": new_template.id
    }


@router.get("/templates")
def get_contract_templates(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all contract templates"""
    query = db.query(ContractTemplate)

    if active_only:
        query = query.filter(ContractTemplate.is_active == True)

    templates = query.order_by(ContractTemplate.created_at.desc()).all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "template_content": t.template_content,
                "version": t.version,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ]
    }


@router.get("/templates/{template_id}")
def get_contract_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific contract template"""
    template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    return {
        "id": template.id,
        "name": template.name,
        "template_content": template.template_content,
        "version": template.version,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@router.put("/templates/{template_id}")
def update_contract_template(
    template_id: int,
    updates: ContractTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a contract template"""
    template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    if updates.name is not None:
        template.name = updates.name
    if updates.template_content is not None:
        template.template_content = updates.template_content
    if updates.version is not None:
        template.version = updates.version
    if updates.is_active is not None:
        template.is_active = updates.is_active

    db.commit()
    db.refresh(template)

    return {"message": "Contract template updated successfully"}


# Contract endpoints
@router.post("/generate")
def generate_contract(
    contract_data: ContractGenerate,
    db: Session = Depends(get_db)
):
    """Generate a contract for a contractor"""
    # Check if contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == contract_data.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Check if template exists
    template = db.query(ContractTemplate).filter(ContractTemplate.id == contract_data.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Contract template not found")

    # Generate unique token
    token = generate_token()
    token_expiry = datetime.utcnow() + timedelta(days=7)  # 7 days expiry

    # Extract contract details from contractor data
    cds_data = contractor.cds_form_data or {}

    # Create new contract
    new_contract = Contract(
        contractor_id=contract_data.contractor_id,
        template_id=contract_data.template_id,
        contract_content=contract_data.contract_content,
        contract_date=datetime.utcnow().strftime("%Y-%m-%d"),
        consultant_name=f"{contractor.first_name} {contractor.surname}",
        client_name=cds_data.get("clientName", ""),
        client_address=cds_data.get("clientAddress", ""),
        job_title=cds_data.get("role", contractor.role),
        commencement_date=cds_data.get("startDate", contractor.start_date),
        contract_rate=cds_data.get("dayRate", contractor.candidate_pay_rate),
        working_location=cds_data.get("location", contractor.location),
        duration=cds_data.get("duration", contractor.duration),
        contract_token=token,
        token_expiry=token_expiry,
        status=ContractStatus.DRAFT
    )

    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)

    return {
        "message": "Contract generated successfully",
        "contract_id": new_contract.id,
        "token": token
    }


@router.post("/{contract_id}/send")
def send_contract(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """Send contract to contractor via email"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get contractor
    contractor = db.query(Contractor).filter(Contractor.id == contract.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Send email
    email_sent = send_contract_email(
        contractor_email=contractor.email,
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        contract_token=contract.contract_token,
        expiry_date=contract.token_expiry
    )

    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send contract email")

    # Update contract status
    contract.status = ContractStatus.SENT
    contract.sent_date = datetime.utcnow()

    db.commit()
    db.refresh(contract)

    return {
        "message": "Contract sent successfully",
        "contract_token": contract.contract_token,
        "contractor_email": contractor.email,
        "review_link": f"/contract/{contract.contract_token}/review"
    }


@router.get("/token/{token}")
def get_contract_by_token(token: str, db: Session = Depends(get_db)):
    """Get contract by token (for contractor to review)"""
    contract = db.query(Contract).filter(Contract.contract_token == token).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check if token is expired
    if contract.token_expiry and datetime.utcnow() > contract.token_expiry:
        raise HTTPException(status_code=400, detail="Contract token has expired")

    # Mark as reviewed if not already
    if contract.status == ContractStatus.SENT:
        contract.status = ContractStatus.REVIEWED
        contract.reviewed_date = datetime.utcnow()
        db.commit()

    return {
        "id": contract.id,
        "contract_content": contract.contract_content,
        "consultant_name": contract.consultant_name,
        "client_name": contract.client_name,
        "job_title": contract.job_title,
        "commencement_date": contract.commencement_date,
        "contract_rate": contract.contract_rate,
        "working_location": contract.working_location,
        "duration": contract.duration,
        "status": contract.status,
        "sent_date": contract.sent_date.isoformat() if contract.sent_date else None,
    }


@router.get("/token/{token}/pdf")
def get_contract_pdf_by_token(token: str, db: Session = Depends(get_db)):
    """Get contract PDF by token - returns the new 5-page consultant contract with AVENTUS branding"""
    contract = db.query(Contract).filter(Contract.contract_token == token).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check if token is expired
    if contract.token_expiry and datetime.utcnow() > contract.token_expiry:
        raise HTTPException(status_code=400, detail="Contract token has expired")

    # Get contractor data
    contractor = db.query(Contractor).filter(Contractor.id == contract.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Prepare contractor data for PDF - use latest data from contractor record
    cds_data = contractor.cds_form_data or {}
    contractor_data = {
        'first_name': contractor.first_name,
        'surname': contractor.surname,
        'client_name': cds_data.get('clientName', contract.client_name or contractor.client_name or '[Client Name]'),
        'client_address': cds_data.get('clientAddress', contract.client_address or '[Client Address]'),
        'role': cds_data.get('role', contract.job_title or contractor.role or '[Job Title]'),
        'location': cds_data.get('location', contract.working_location or contractor.location or '[Location]'),
        'duration': contractor.duration or contract.duration or '6 months',
        'start_date': contractor.start_date or contract.commencement_date or '[Start Date]',
        'candidate_pay_rate': contractor.candidate_pay_rate or contract.contract_rate or '[Day Rate]',
        'currency': contractor.currency or 'USD'
    }

    # Generate PDF using the new consultant contract generator
    pdf_buffer = generate_consultant_contract_pdf(contractor_data)

    # Return PDF
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=contract_{contractor.first_name}_{contractor.surname}.pdf"}
    )


@router.post("/token/{token}/sign")
def sign_contract(
    token: str,
    signature: ContractSign,
    db: Session = Depends(get_db)
):
    """Contractor signs the contract - awaits Aventus counter-signature"""
    contract = db.query(Contract).filter(Contract.contract_token == token).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check if token is expired
    if contract.token_expiry and datetime.utcnow() > contract.token_expiry:
        raise HTTPException(status_code=400, detail="Contract token has expired")

    # Check if already signed
    if contract.status in [ContractStatus.PENDING_AVENTUS_SIGNATURE, ContractStatus.SIGNED, ContractStatus.VALIDATED, ContractStatus.ACTIVATED]:
        raise HTTPException(status_code=400, detail="Contract has already been signed")

    # Update contract with contractor signature
    contract.contractor_signature_type = signature.signature_type
    contract.contractor_signature_data = signature.signature_data
    contract.contractor_signed_date = datetime.utcnow()
    contract.contractor_notes = signature.notes
    # Set status to pending Aventus counter-signature
    contract.status = ContractStatus.PENDING_AVENTUS_SIGNATURE

    db.commit()
    db.refresh(contract)

    return {
        "message": "Contract signed successfully. Awaiting Aventus counter-signature.",
        "contract_id": contract.id,
        "status": "pending_aventus_signature"
    }


@router.post("/{contract_id}/counter-sign")
def counter_sign_contract(
    contract_id: int,
    signature_data: AventusCounterSign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Admin counter-signs a contract that has been signed by contractor.
    This completes the signing process, emails signed copy to contractor,
    and stores the signed contract in contractor's documents.
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check if contract is pending Aventus signature
    if contract.status != ContractStatus.PENDING_AVENTUS_SIGNATURE:
        raise HTTPException(
            status_code=400,
            detail=f"Contract is not pending Aventus signature. Current status: {contract.status.value}"
        )

    # Get contractor
    contractor = db.query(Contractor).filter(Contractor.id == contract.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Add Aventus signature
    contract.aventus_signature_type = signature_data.signature_type
    contract.aventus_signature_data = signature_data.signature_data
    contract.aventus_signer_name = signature_data.signer_name
    contract.aventus_signed_date = datetime.utcnow()
    contract.aventus_signed_by = current_user.id
    contract.status = ContractStatus.SIGNED

    db.flush()

    # Generate signed contract PDF and commit everything in one transaction
    try:
        cds_data = contractor.cds_form_data or {}
        contractor_data = {
            'first_name': contractor.first_name,
            'surname': contractor.surname,
            'client_name': cds_data.get('clientName', contract.client_name or contractor.client_name or '[Client Name]'),
            'client_address': cds_data.get('clientAddress', contract.client_address or '[Client Address]'),
            'role': cds_data.get('role', contract.job_title or contractor.role or '[Job Title]'),
            'location': cds_data.get('location', contract.working_location or contractor.location or '[Location]'),
            'duration': contractor.duration or contract.duration or '6 months',
            'start_date': contractor.start_date or contract.commencement_date or '[Start Date]',
            'candidate_pay_rate': contractor.candidate_pay_rate or contract.contract_rate or '[Day Rate]',
            'currency': contractor.currency or 'USD',
        }

        # Generate the PDF with both signatures
        pdf_buffer = generate_consultant_contract_pdf(
            contractor_data,
            contractor_signature_type=contract.contractor_signature_type,
            contractor_signature_data=contract.contractor_signature_data,
            superadmin_signature_type=contract.aventus_signature_type,
            superadmin_signature_data=contract.aventus_signature_data,
            signed_date=contract.aventus_signed_date.strftime('%d %B %Y') if contract.aventus_signed_date else ''
        )

        # Upload to storage
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"signed_contract_{contractor.first_name}_{contractor.surname}_{timestamp}.pdf"
        folder = f"contractor-documents/{contractor.id}"

        pdf_url = upload_file(pdf_buffer, filename, folder)

        # Add to contractor's other_documents
        other_docs = list(contractor.other_documents or [])
        other_docs.append({
            "type": "signed_contract",
            "name": f"Signed Contract - {contractor.first_name} {contractor.surname}",
            "url": pdf_url,
            "uploaded_at": datetime.utcnow().isoformat(),
            "contract_id": contract.id
        })
        contractor.other_documents = other_docs
        flag_modified(contractor, "other_documents")
    except Exception as pdf_error:
        db.rollback()
        print(f"Error: Failed to generate/upload signed contract PDF: {pdf_error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate signed contract PDF. Contract was not signed."
        )

    # Single commit: signature + PDF URL saved atomically
    db.commit()
    db.refresh(contract)

    # Email is a side effect — sent after commit (failure is non-fatal)
    try:
        send_signed_contract_email(
            contractor_email=contractor.email,
            contractor_name=f"{contractor.first_name} {contractor.surname}",
            pdf_url=pdf_url
        )
        print(f"Signed contract email sent to {contractor.email}")
    except Exception as email_error:
        print(f"Warning: Failed to send signed contract email: {email_error}")

    return {
        "message": "Contract counter-signed successfully. Signed copy emailed to contractor.",
        "contract_id": contract.id,
        "contractor_email": contractor.email,
        "aventus_signed_by": current_user.name,
        "aventus_signed_date": contract.aventus_signed_date.isoformat(),
        "status": "signed"
    }


@router.get("/pending-counter-signature")
def get_pending_counter_signature_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """Get all contracts pending Aventus counter-signature"""
    contracts = db.query(Contract).filter(
        Contract.status == ContractStatus.PENDING_AVENTUS_SIGNATURE
    ).order_by(Contract.contractor_signed_date.desc()).all()

    return {
        "contracts": [
            {
                "id": c.id,
                "contractor_id": c.contractor_id,
                "consultant_name": c.consultant_name,
                "client_name": c.client_name,
                "job_title": c.job_title,
                "contractor_signed_date": c.contractor_signed_date.isoformat() if c.contractor_signed_date else None,
            }
            for c in contracts
        ]
    }


@router.get("/contractor/{contractor_id}")
def get_contractor_contracts(
    contractor_id: str,
    db: Session = Depends(get_db)
):
    """Get all contracts for a contractor"""
    contracts = db.query(Contract).filter(
        Contract.contractor_id == contractor_id
    ).order_by(Contract.created_at.desc()).all()

    return {
        "contracts": [
            {
                "id": c.id,
                "status": c.status,
                "contract_date": c.contract_date,
                "client_name": c.client_name,
                "job_title": c.job_title,
                "sent_date": c.sent_date.isoformat() if c.sent_date else None,
                "contractor_signed_date": c.contractor_signed_date.isoformat() if c.contractor_signed_date else None,
                "activated_date": c.activated_date.isoformat() if c.activated_date else None,
            }
            for c in contracts
        ]
    }


@router.get("/pending")
def get_pending_contracts(db: Session = Depends(get_db)):
    """Get all contracts pending validation (signed by contractor, waiting for admin)"""
    contracts = db.query(Contract).filter(
        Contract.status == ContractStatus.SIGNED
    ).order_by(Contract.contractor_signed_date.desc()).all()

    return {
        "contracts": [
            {
                "id": c.id,
                "contractor_id": c.contractor_id,
                "consultant_name": c.consultant_name,
                "client_name": c.client_name,
                "job_title": c.job_title,
                "contractor_signed_date": c.contractor_signed_date.isoformat() if c.contractor_signed_date else None,
            }
            for c in contracts
        ]
    }


@router.get("/{contract_id}")
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get contract details (for admin validation)"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {
        "id": contract.id,
        "contractor_id": contract.contractor_id,
        "contract_content": contract.contract_content,
        "consultant_name": contract.consultant_name,
        "client_name": contract.client_name,
        "job_title": contract.job_title,
        "commencement_date": contract.commencement_date,
        "contract_rate": contract.contract_rate,
        "working_location": contract.working_location,
        "duration": contract.duration,
        "status": contract.status,
        "sent_date": contract.sent_date.isoformat() if contract.sent_date else None,
        "contractor_signature_type": contract.contractor_signature_type,
        "contractor_signature_data": contract.contractor_signature_data,
        "contractor_signed_date": contract.contractor_signed_date.isoformat() if contract.contractor_signed_date else None,
        "aventus_signature_type": contract.aventus_signature_type,
        "aventus_signature_data": contract.aventus_signature_data,
    }


@router.post("/{contract_id}/validate")
def validate_contract(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """Admin validates the signed contract"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status != ContractStatus.SIGNED:
        raise HTTPException(status_code=400, detail="Contract must be signed before validation")

    # Update contract status
    contract.status = ContractStatus.VALIDATED
    contract.validated_date = datetime.utcnow()

    db.commit()
    db.refresh(contract)

    return {
        "message": "Contract validated successfully",
        "contract_id": contract.id
    }


@router.post("/{contract_id}/activate")
def activate_account(
    contract_id: int,
    db: Session = Depends(get_db)
):
    """Activate contractor account and send activation email with temporary password"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status != ContractStatus.VALIDATED:
        raise HTTPException(status_code=400, detail="Contract must be validated before activation")

    # Get contractor
    contractor = db.query(Contractor).filter(Contractor.id == contract.contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Generate temporary password
    temp_password = generate_temporary_password()

    # Send activation email
    email_sent = send_activation_email(
        contractor_email=contractor.email,
        contractor_name=f"{contractor.first_name} {contractor.surname}",
        temporary_password=temp_password
    )

    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send activation email")

    # Update contract
    contract.status = ContractStatus.ACTIVATED
    contract.activated_date = datetime.utcnow()
    contract.temporary_password = temp_password

    # Update contractor status
    contractor.status = "active"
    contractor.activated_date = datetime.utcnow()

    db.commit()
    db.refresh(contract)

    return {
        "message": "Account activated successfully and email sent",
        "temporary_password": temp_password,
        "contractor_email": contractor.email
    }


@router.delete("/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Delete a contract"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully"}
