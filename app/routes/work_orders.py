from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from app.database import get_db
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.contractor import Contractor
from app.models.third_party import ThirdParty
from app.schemas.work_order import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse
from app.models.user import User, UserRole
from app.models.contractor import Contractor, ContractorStatus
from app.utils.auth import get_current_active_user, require_role
from app.utils.storage import storage, upload_file
from app.utils.work_order_pdf_generator import generate_work_order_pdf
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])


def generate_work_order_number(db: Session) -> str:
    """Generate unique work order number like WO-2024-001"""
    year = datetime.utcnow().year

    # Get the count of work orders created this year
    count = db.query(WorkOrder).filter(
        WorkOrder.work_order_number.like(f"WO-{year}-%")
    ).count()

    next_number = count + 1
    return f"WO-{year}-{next_number:03d}"


@router.post("/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    work_order_data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new work order
    """
    # Verify contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == work_order_data.contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contractor not found"
        )

    # Verify third party exists if provided
    if work_order_data.third_party_id:
        third_party = db.query(ThirdParty).filter(ThirdParty.id == work_order_data.third_party_id).first()
        if not third_party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third party not found"
            )

    # Generate work order number
    work_order_number = generate_work_order_number(db)

    # Create work order
    work_order_dict = work_order_data.model_dump()
    work_order = WorkOrder(
        **work_order_dict,
        work_order_number=work_order_number,
        created_by=current_user.id
    )

    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    return work_order


@router.get("/", response_model=List[WorkOrderResponse])
async def get_work_orders(
    status_filter: Optional[WorkOrderStatus] = None,
    contractor_id: Optional[str] = None,
    third_party_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all work orders with optional filters
    """
    query = db.query(WorkOrder)

    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)

    if contractor_id:
        query = query.filter(WorkOrder.contractor_id == contractor_id)

    if third_party_id:
        query = query.filter(WorkOrder.third_party_id == third_party_id)

    work_orders = query.order_by(WorkOrder.created_at.desc()).all()
    return work_orders


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific work order by ID
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    return work_order


@router.put("/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: str,
    work_order_data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a work order
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # Verify contractor exists if being updated
    if work_order_data.contractor_id:
        contractor = db.query(Contractor).filter(Contractor.id == work_order_data.contractor_id).first()
        if not contractor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contractor not found"
            )

    # Verify third party exists if being updated
    if work_order_data.third_party_id:
        third_party = db.query(ThirdParty).filter(ThirdParty.id == work_order_data.third_party_id).first()
        if not third_party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third party not found"
            )

    # Update fields
    update_data = work_order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(work_order, field, value)

    db.commit()
    db.refresh(work_order)

    return work_order


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Delete a work order (Admin/Superadmin only)
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    db.delete(work_order)
    db.commit()

    return None


@router.post("/{work_order_id}/upload-document")
async def upload_work_order_document(
    work_order_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for a work order
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # Upload file to storage
    try:
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"work-orders/{work_order_id}/{document_type}_{timestamp}_{unique_id}.{file_ext}"

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

    # Get existing documents or initialize empty list
    documents = work_order.documents if work_order.documents else []

    # Add new document
    documents.append({
        "type": document_type,
        "filename": file.filename,
        "url": file_url,
        "uploaded_at": datetime.utcnow().isoformat()
    })

    # Update work order with new document
    work_order.documents = documents
    db.commit()
    db.refresh(work_order)

    return {"message": "Document uploaded successfully", "url": file_url}


@router.delete("/{work_order_id}/documents/{document_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order_document(
    work_order_id: str,
    document_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document from a work order
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    if not work_order.documents or document_index >= len(work_order.documents):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Remove document from list
    documents = work_order.documents
    documents.pop(document_index)
    work_order.documents = documents

    db.commit()

    return None


@router.patch("/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: str,
    new_status: WorkOrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update work order status
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # If status is being changed to APPROVED, set approved_by
    if new_status == WorkOrderStatus.APPROVED and work_order.status != WorkOrderStatus.APPROVED:
        work_order.approved_by = current_user.id

    work_order.status = new_status
    db.commit()
    db.refresh(work_order)

    return work_order


# ============= PUBLIC ENDPOINTS (No Auth Required) =============

class ClientSignatureData(BaseModel):
    signature_type: str  # "typed" or "drawn"
    signature_data: str  # Name for typed, base64 for drawn


@router.get("/public/by-token/{signature_token}")
async def get_work_order_by_token(
    signature_token: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Get work order by signature token (for client signature page)
    No authentication required
    """
    work_order = db.query(WorkOrder).filter(
        WorkOrder.client_signature_token == signature_token
    ).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found or link is invalid"
        )

    # Check if already signed by client
    if work_order.status in [WorkOrderStatus.PENDING_AVENTUS_SIGNATURE, WorkOrderStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This work order has already been signed"
        )

    # Return work order details for display
    return {
        "work_order_number": work_order.work_order_number,
        "contractor_name": work_order.contractor_name,
        "client_name": work_order.client_name,
        "role": work_order.role,
        "location": work_order.location,
        "start_date": work_order.start_date.isoformat() if work_order.start_date else None,
        "end_date": work_order.end_date.isoformat() if work_order.end_date else None,
        "duration": work_order.duration,
        "currency": work_order.currency,
        "charge_rate": work_order.charge_rate,
        "pay_rate": work_order.pay_rate,
        "project_name": work_order.project_name,
        "business_type": work_order.business_type,
        "umbrella_company_name": work_order.umbrella_company_name,
        "status": work_order.status.value,
        "work_order_id": work_order.id
    }


@router.get("/public/pdf/{signature_token}")
async def get_work_order_pdf_by_token(
    signature_token: str,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Get work order PDF by signature token
    No authentication required
    """
    work_order = db.query(WorkOrder).filter(
        WorkOrder.client_signature_token == signature_token
    ).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found or link is invalid"
        )

    # Prepare data for PDF
    work_order_data = {
        "work_order_number": work_order.work_order_number,
        "contractor_name": work_order.contractor_name,
        "client_name": work_order.client_name,
        "role": work_order.role,
        "location": work_order.location,
        "start_date": work_order.start_date.strftime('%d %B %Y') if work_order.start_date else '',
        "end_date": work_order.end_date.strftime('%d %B %Y') if work_order.end_date else '',
        "duration": work_order.duration or '',
        "currency": work_order.currency or 'AED',
        "charge_rate": work_order.charge_rate or '',
        "pay_rate": work_order.pay_rate or '',
        "project_name": work_order.project_name or '',
        "business_type": work_order.business_type or '',
        "umbrella_company_name": work_order.umbrella_company_name or '',
        # Include signature data for signed work orders
        "client_signature_type": work_order.client_signature_type,
        "client_signature_data": work_order.client_signature_data,
        "client_signed_date": work_order.client_signed_date.strftime('%d %B %Y') if work_order.client_signed_date else '',
        "aventus_signature_type": work_order.aventus_signature_type,
        "aventus_signature_data": work_order.aventus_signature_data,
        "aventus_signed_date": work_order.aventus_signed_date.strftime('%d %B %Y') if work_order.aventus_signed_date else '',
    }

    # Generate PDF
    pdf_buffer = generate_work_order_pdf(work_order_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=work_order_{work_order.work_order_number}.pdf"
        }
    )


@router.post("/public/sign/{signature_token}")
async def sign_work_order(
    signature_token: str,
    signature_data: ClientSignatureData,
    db: Session = Depends(get_db)
):
    """
    PUBLIC ENDPOINT: Client signs work order using signature token
    No authentication required
    """
    try:
        work_order = db.query(WorkOrder).filter(
            WorkOrder.client_signature_token == signature_token
        ).first()

        if not work_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work order not found or link is invalid"
            )

        # Check if already signed by client
        if work_order.status in [WorkOrderStatus.PENDING_AVENTUS_SIGNATURE, WorkOrderStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This work order has already been signed"
            )

        # Check if work order is in correct status
        if work_order.status != WorkOrderStatus.PENDING_CLIENT_SIGNATURE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This work order is not pending signature. Current status: {work_order.status}"
            )

        # Update work order with signature
        work_order.client_signature_type = signature_data.signature_type
        work_order.client_signature_data = signature_data.signature_data
        work_order.client_signed_date = datetime.now(timezone.utc)
        work_order.status = WorkOrderStatus.PENDING_AVENTUS_SIGNATURE

        # Note: Contractor status is NOT updated yet
        # It will be updated to WORK_ORDER_COMPLETED only after Aventus counter-signs

        db.commit()
        db.refresh(work_order)

        # Generate signed work order PDF and save to contractor documents
        try:
            contractor = db.query(Contractor).filter(Contractor.id == work_order.contractor_id).first()
            if contractor:
                # Convert WorkOrder model to dictionary for PDF generator
                work_order_data = {
                    "work_order_number": work_order.work_order_number,
                    "contractor_name": work_order.contractor_name,
                    "client_name": work_order.client_name,
                    "role": work_order.role,
                    "location": work_order.location,
                    "start_date": work_order.start_date.strftime("%d %B %Y") if work_order.start_date else "",
                    "end_date": work_order.end_date.strftime("%d %B %Y") if work_order.end_date else "",
                    "duration": work_order.duration,
                    "charge_rate": work_order.charge_rate,
                    "pay_rate": work_order.pay_rate,
                    "currency": work_order.currency,
                    "project_name": work_order.project_name,
                    "client_signature_type": work_order.client_signature_type,
                    "client_signature_data": work_order.client_signature_data,
                    "client_signed_date": work_order.client_signed_date.strftime("%d %B %Y") if work_order.client_signed_date else "",
                }

                # Generate the PDF
                pdf_buffer = generate_work_order_pdf(work_order_data)

                # Upload to storage
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                filename = f"work_order_{work_order.work_order_number}_{timestamp}.pdf"
                folder = f"contractor-documents/{contractor.id}"

                pdf_url = upload_file(pdf_buffer, filename, folder)

                # Add to contractor's other_documents
                other_docs = list(contractor.other_documents or [])
                other_docs.append({
                    "type": "signed_work_order",
                    "name": f"Signed Work Order - {work_order.work_order_number}",
                    "url": pdf_url,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "work_order_id": work_order.id
                })
                contractor.other_documents = other_docs
                flag_modified(contractor, "other_documents")

                db.commit()
                print(f"Signed work order PDF saved to contractor documents: {pdf_url}")
        except Exception as pdf_error:
            # Don't fail the signing if PDF upload fails, just log it
            print(f"Warning: Failed to save signed work order PDF: {pdf_error}")

        return {
            "message": "Work order signed successfully. Awaiting Aventus counter-signature.",
            "work_order_number": work_order.work_order_number,
            "signed_date": work_order.client_signed_date.isoformat(),
            "status": "pending_aventus_signature"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error signing work order: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sign work order: {str(e)}"
        )

# ============================================
# AVENTUS COUNTER-SIGNATURE ENDPOINTS
# ============================================

@router.get("/{work_order_id}/view-signed")
async def view_signed_work_order(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"]))
):
    """
    View work order that has been signed by client, pending Aventus counter-signature.
    Returns work order details including client signature.
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # Check if work order has been signed by client
    if work_order.status != WorkOrderStatus.PENDING_AVENTUS_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order is not pending Aventus signature. Current status: {work_order.status.value}"
        )

    # Get contractor details
    contractor = db.query(Contractor).filter(Contractor.id == work_order.contractor_id).first()

    return {
        "work_order_id": work_order.id,
        "work_order_number": work_order.work_order_number,
        "contractor_name": work_order.contractor_name,
        "client_name": work_order.client_name,
        "role": work_order.role,
        "location": work_order.location,
        "start_date": work_order.start_date.isoformat() if work_order.start_date else None,
        "end_date": work_order.end_date.isoformat() if work_order.end_date else None,
        "status": work_order.status.value,
        "client_signature": {
            "type": work_order.client_signature_type,
            "data": work_order.client_signature_data,
            "signed_date": work_order.client_signed_date.isoformat() if work_order.client_signed_date else None
        },
        "ready_for_counter_signature": True
    }


class AventusSignatureData(BaseModel):
    signature_type: str  # "typed" or "drawn"
    signature_data: str  # Name or base64 image


@router.post("/{work_order_id}/counter-sign")
async def counter_sign_work_order(
    work_order_id: str,
    signature_data: AventusSignatureData,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"]))
):
    """
    Aventus admin counter-signs a work order that has been signed by client.
    This completes the work order and updates contractor status to WORK_ORDER_COMPLETED.
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found"
        )

    # Check if work order is pending Aventus signature
    if work_order.status != WorkOrderStatus.PENDING_AVENTUS_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Work order is not pending Aventus signature. Current status: {work_order.status.value}"
        )

    # Check if already counter-signed
    if work_order.aventus_signed_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work order has already been counter-signed by Aventus"
        )

    # Add Aventus signature
    work_order.aventus_signature_type = signature_data.signature_type
    work_order.aventus_signature_data = signature_data.signature_data
    work_order.aventus_signed_date = datetime.now(timezone.utc)
    work_order.aventus_signed_by = current_user.id
    work_order.status = WorkOrderStatus.COMPLETED

    # NOW update contractor status to work_order_completed
    contractor = db.query(Contractor).filter(
        Contractor.id == work_order.contractor_id
    ).first()

    if contractor:
        contractor.status = ContractorStatus.WORK_ORDER_COMPLETED

    db.commit()
    db.refresh(work_order)

    return {
        "message": "Work order counter-signed successfully. Work order is now fully executed.",
        "work_order_number": work_order.work_order_number,
        "client_signed_date": work_order.client_signed_date.isoformat() if work_order.client_signed_date else None,
        "aventus_signed_date": work_order.aventus_signed_date.isoformat(),
        "aventus_signed_by": current_user.name,
        "status": "completed"
    }
