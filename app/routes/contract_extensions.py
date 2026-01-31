"""
Contract Extension API Routes.

Endpoints for managing contractor contract extensions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.contractor import Contractor
from app.models.contract_extension import ExtensionStatus
from app.services.contract_extension_service import ContractExtensionService
from app.schemas.contract_extension import (
    RequestExtensionRequest,
    ApproveExtensionRequest,
    RejectExtensionRequest,
    ExtensionSignatureRequest,
    ContractExtensionResponse,
    ContractExtensionListResponse,
    ExtensionSigningPageResponse,
    ExtensionHistoryResponse,
)
from app.routes.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/v1", tags=["Contract Extensions"])


# ============ Contractor-specific endpoints ============

@router.post(
    "/contractors/{contractor_id}/extensions",
    response_model=ContractExtensionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_extension(
    contractor_id: str,
    request: RequestExtensionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"])),
):
    """
    Request a contract extension for a contractor.

    Only admin, superadmin, or consultant can request extensions.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.request_extension(
            contractor_id=contractor_id,
            request=request,
            requested_by=current_user.id,
        )

        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/contractors/{contractor_id}/extensions",
    response_model=ExtensionHistoryResponse,
)
async def get_contractor_extensions(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all extensions for a contractor.
    """
    service = ContractExtensionService(db)

    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor not found: {contractor_id}",
        )

    extensions = await service.get_extensions_for_contractor(contractor_id)

    return ExtensionHistoryResponse(
        contractor_id=contractor_id,
        total_extensions=len(extensions),
        extensions=[_to_list_response(ext, contractor) for ext in extensions],
    )


@router.get(
    "/contractors/{contractor_id}/extensions/{extension_id}",
    response_model=ContractExtensionResponse,
)
async def get_extension(
    contractor_id: str,
    extension_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific extension.
    """
    service = ContractExtensionService(db)
    extension = await service.get_extension_by_id(extension_id)

    if not extension or extension.contractor_id != contractor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extension not found: {extension_id}",
        )

    return _to_response(extension)


# ============ Extension workflow endpoints ============

@router.post(
    "/extensions/{extension_id}/approve",
    response_model=ContractExtensionResponse,
)
async def approve_extension(
    extension_id: str,
    request: ApproveExtensionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Approve an extension request.

    Only admin or superadmin can approve extensions.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.approve_extension(
            extension_id=extension_id,
            approved_by=current_user.id,
            notes=request.notes,
        )
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/{extension_id}/reject",
    response_model=ContractExtensionResponse,
)
async def reject_extension(
    extension_id: str,
    request: RejectExtensionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Reject an extension request.

    Only admin or superadmin can reject extensions.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.reject_extension(
            extension_id=extension_id,
            rejected_by=current_user.id,
            reason=request.reason,
        )
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/{extension_id}/generate-document",
)
async def generate_extension_document(
    extension_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Generate extension agreement document.
    """
    service = ContractExtensionService(db)

    try:
        document_url = await service.generate_extension_document(extension_id)
        return {"document_url": document_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/{extension_id}/send-for-signature",
    response_model=ContractExtensionResponse,
)
async def send_for_signature(
    extension_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Send extension for contractor signature.

    Generates signature token and sends notification.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.send_for_signature(extension_id)
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/{extension_id}/aventus-sign",
    response_model=ContractExtensionResponse,
)
async def aventus_sign_extension(
    extension_id: str,
    signature: ExtensionSignatureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Add Aventus counter-signature to extension.

    Only admin or superadmin can counter-sign.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.process_aventus_signature(
            extension_id=extension_id,
            signed_by=current_user.id,
            signature_type=signature.signature_type,
            signature_data=signature.signature_data,
        )
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/{extension_id}/complete",
    response_model=ContractExtensionResponse,
)
async def complete_extension(
    extension_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Complete extension and apply to contractor.

    Updates contractor end date and rates.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.complete_extension(extension_id)
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============ Public signing endpoints ============

@router.get(
    "/extensions/sign/{token}",
    response_model=ExtensionSigningPageResponse,
)
async def get_signing_page(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Get extension signing page data (public endpoint).

    Returns extension details for contractor to review and sign.
    """
    service = ContractExtensionService(db)

    try:
        return await service.get_signing_page_data(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/extensions/sign/{token}",
    response_model=ContractExtensionResponse,
)
async def submit_signature(
    token: str,
    signature: ExtensionSignatureRequest,
    db: Session = Depends(get_db),
):
    """
    Submit contractor signature (public endpoint).

    Contractor signs the extension agreement.
    """
    service = ContractExtensionService(db)

    try:
        extension = await service.process_contractor_signature(token, signature)
        return _to_response(extension)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============ Admin list endpoints ============

@router.get(
    "/extensions",
    response_model=List[ContractExtensionListResponse],
)
async def list_extensions(
    status_filter: Optional[ExtensionStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    List all extension requests.

    Only admin or superadmin can list all extensions.
    """
    service = ContractExtensionService(db)
    extensions = await service.list_extensions(
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    result = []
    for ext in extensions:
        contractor = db.query(Contractor).filter(Contractor.id == ext.contractor_id).first()
        result.append(_to_list_response(ext, contractor))

    return result


# ============ Helper functions ============

def _to_response(extension) -> ContractExtensionResponse:
    """Convert extension model to response schema."""
    return ContractExtensionResponse(
        id=extension.id,
        contractor_id=extension.contractor_id,
        original_end_date=extension.original_end_date,
        new_end_date=extension.new_end_date,
        extension_months=extension.extension_months,
        new_monthly_rate=extension.new_monthly_rate,
        new_day_rate=extension.new_day_rate,
        rate_change_reason=extension.rate_change_reason,
        status=extension.status,
        requested_by=extension.requested_by,
        requested_date=extension.requested_date,
        approved_by=extension.approved_by,
        approved_date=extension.approved_date,
        rejection_reason=extension.rejection_reason,
        rejected_by=extension.rejected_by,
        rejected_date=extension.rejected_date,
        extension_document_url=extension.extension_document_url,
        contractor_signed_date=extension.contractor_signed_date,
        has_contractor_signature=extension.contractor_signed_date is not None,
        aventus_signed_date=extension.aventus_signed_date,
        has_aventus_signature=extension.aventus_signed_date is not None,
        notes=extension.notes,
        created_at=extension.created_at,
        updated_at=extension.updated_at,
    )


def _to_list_response(extension, contractor) -> ContractExtensionListResponse:
    """Convert extension model to list response schema."""
    return ContractExtensionListResponse(
        id=extension.id,
        contractor_id=extension.contractor_id,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        original_end_date=extension.original_end_date,
        new_end_date=extension.new_end_date,
        extension_months=extension.extension_months,
        status=extension.status,
        requested_date=extension.requested_date,
        has_rate_change=extension.new_monthly_rate is not None or extension.new_day_rate is not None,
    )
