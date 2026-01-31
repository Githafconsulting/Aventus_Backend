"""
Offboarding API Routes.

Endpoints for managing contractor offboarding process.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.offboarding import OffboardingStatus
from app.models.contractor import Contractor
from app.services.offboarding_service import OffboardingService
from app.schemas.offboarding import (
    InitiateOffboardingRequest,
    ApproveSettlementRequest,
    CancelOffboardingRequest,
    CompleteOffboardingRequest,
    OffboardingResponse,
    OffboardingListResponse,
    OffboardingStatusResponse,
    OffboardingDocumentsResponse,
    SettlementBreakdown,
)
from app.routes.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/v1/offboarding", tags=["Offboarding"])


@router.post(
    "/contractors/{contractor_id}/initiate",
    response_model=OffboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_offboarding(
    contractor_id: str,
    request: InitiateOffboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"])),
):
    """
    Initiate offboarding process for a contractor.

    Only admin, superadmin, or consultant can initiate offboarding.
    """
    service = OffboardingService(db)

    try:
        offboarding = await service.initiate_offboarding(
            contractor_id=contractor_id,
            request=request,
            initiated_by=current_user.id,
        )
        return offboarding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/contractors/{contractor_id}/status",
    response_model=OffboardingStatusResponse,
)
async def get_offboarding_status(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get offboarding status for a contractor.
    """
    service = OffboardingService(db)

    try:
        return await service.get_offboarding_status(contractor_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/contractors/{contractor_id}/settlement-preview",
    response_model=SettlementBreakdown,
)
async def get_settlement_preview(
    contractor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin", "consultant"])),
):
    """
    Calculate and preview final settlement for a contractor.

    Admin, superadmin, or consultant can view settlement details.
    """
    service = OffboardingService(db)

    try:
        return await service.calculate_final_settlement(contractor_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{offboarding_id}/approve-settlement",
    response_model=OffboardingResponse,
)
async def approve_settlement(
    offboarding_id: str,
    request: ApproveSettlementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Approve settlement calculation.

    Only admin or superadmin can approve settlements.
    """
    service = OffboardingService(db)

    try:
        offboarding = await service.approve_settlement(
            offboarding_id=offboarding_id,
            approved_by=current_user.id,
            adjustments=request.adjustments,
        )
        return offboarding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{offboarding_id}/generate-documents",
    response_model=OffboardingDocumentsResponse,
)
async def generate_documents(
    offboarding_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Generate offboarding documents.

    Creates termination letter, experience letter, and clearance certificate.
    """
    service = OffboardingService(db)

    try:
        documents = await service.generate_offboarding_documents(offboarding_id)
        offboarding = await service.get_offboarding_by_id(offboarding_id)

        return OffboardingDocumentsResponse(
            offboarding_id=offboarding_id,
            termination_letter_url=documents.get("termination_letter_url"),
            experience_letter_url=documents.get("experience_letter_url"),
            clearance_certificate_url=documents.get("clearance_certificate_url"),
            final_payslip_url=offboarding.final_payslip_url if offboarding else None,
            all_documents_generated=all([
                documents.get("termination_letter_url"),
                documents.get("experience_letter_url"),
                documents.get("clearance_certificate_url"),
            ]),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{offboarding_id}/complete",
    response_model=OffboardingResponse,
)
async def complete_offboarding(
    offboarding_id: str,
    request: CompleteOffboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Complete offboarding process.

    Only admin or superadmin can complete offboarding.
    """
    service = OffboardingService(db)

    try:
        offboarding = await service.complete_offboarding(
            offboarding_id=offboarding_id,
            completed_by=current_user.id,
        )
        return offboarding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{offboarding_id}/cancel",
    response_model=OffboardingResponse,
)
async def cancel_offboarding(
    offboarding_id: str,
    request: CancelOffboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    Cancel an offboarding process.

    Only admin or superadmin can cancel offboarding.
    """
    service = OffboardingService(db)

    try:
        offboarding = await service.cancel_offboarding(
            offboarding_id=offboarding_id,
            cancelled_by=current_user.id,
            reason=request.reason,
        )
        return offboarding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{offboarding_id}",
    response_model=OffboardingResponse,
)
async def get_offboarding(
    offboarding_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get offboarding record by ID.
    """
    service = OffboardingService(db)
    offboarding = await service.get_offboarding_by_id(offboarding_id)

    if not offboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offboarding not found: {offboarding_id}",
        )

    return offboarding


@router.get(
    "/{offboarding_id}/documents",
    response_model=OffboardingDocumentsResponse,
)
async def get_offboarding_documents(
    offboarding_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get offboarding documents.
    """
    service = OffboardingService(db)
    offboarding = await service.get_offboarding_by_id(offboarding_id)

    if not offboarding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offboarding not found: {offboarding_id}",
        )

    return OffboardingDocumentsResponse(
        offboarding_id=offboarding_id,
        termination_letter_url=offboarding.termination_letter_url,
        experience_letter_url=offboarding.experience_letter_url,
        clearance_certificate_url=offboarding.clearance_certificate_url,
        final_payslip_url=offboarding.final_payslip_url,
        all_documents_generated=all([
            offboarding.termination_letter_url,
            offboarding.experience_letter_url,
            offboarding.clearance_certificate_url,
        ]),
    )


@router.get(
    "/",
    response_model=List[OffboardingListResponse],
)
async def list_offboardings(
    status_filter: Optional[OffboardingStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "superadmin"])),
):
    """
    List all offboarding records.

    Only admin or superadmin can list all offboardings.
    """
    service = OffboardingService(db)
    offboardings = await service.list_offboardings(
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    # Enrich with contractor names
    result = []
    for ob in offboardings:
        contractor = db.query(Contractor).filter(Contractor.id == ob.contractor_id).first()
        result.append(OffboardingListResponse(
            id=ob.id,
            contractor_id=ob.contractor_id,
            contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
            reason=ob.reason,
            status=ob.status,
            initiated_date=ob.initiated_date,
            last_working_date=ob.last_working_date,
            final_settlement_amount=ob.final_settlement_amount,
        ))

    return result
