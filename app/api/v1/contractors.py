"""
Contractors API Routes.

Thin route layer that delegates to ContractorService.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status

from app.api.dependencies import (
    get_contractor_service,
    get_current_user,
    get_current_admin_user,
)
from app.api.responses import success_response, paginated_response, created_response
from app.services.contractor_service import ContractorService
from app.schemas.contractor import ContractorCreate, ContractorUpdate, ContractorResponse
from app.domain.contractor.exceptions import (
    ContractorNotFoundError,
    InvalidStatusTransitionError,
)
from app.domain.contractor.value_objects import ContractorStatus, OnboardingRoute

router = APIRouter(prefix="/contractors", tags=["Contractors"])


@router.post("/initial", status_code=status.HTTP_201_CREATED)
async def create_initial_contractor(
    data: ContractorCreate,
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """
    Create initial contractor record.

    Generates document upload token and prepares for onboarding.
    """
    result = await service.create_initial(data)
    return created_response(result, "Contractor created successfully")


@router.get("/")
async def list_contractors(
    query: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    route: Optional[str] = Query(None, description="Filter by onboarding route"),
    client_id: Optional[int] = Query(None, description="Filter by client"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_user),
):
    """List contractors with filters and pagination."""
    contractors, total = await service.search(
        query=query,
        status=status,
        route=route,
        client_id=client_id,
        page=page,
        page_size=page_size,
    )

    # Convert to dict for response
    contractor_list = [
        {
            "id": c.id,
            "first_name": c.first_name,
            "surname": c.surname,
            "email": c.email,
            "status": c.status,
            "onboarding_route": c.onboarding_route,
            "client_id": c.client_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contractors
    ]

    return paginated_response(contractor_list, total, page, page_size)


@router.get("/pending-review")
async def get_pending_review(
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get contractors pending admin review."""
    contractors = await service.get_pending_review()
    return success_response([
        {
            "id": c.id,
            "first_name": c.first_name,
            "surname": c.surname,
            "email": c.email,
            "status": c.status,
            "onboarding_route": c.onboarding_route,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in contractors
    ])


@router.get("/statistics")
async def get_statistics(
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get contractor statistics."""
    stats = await service.get_statistics()
    return success_response(stats)


@router.get("/{id}")
async def get_contractor(
    id: int = Path(..., description="Contractor ID"),
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_user),
):
    """Get contractor by ID."""
    try:
        contractor = await service.get(id)
        return success_response(contractor)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/token/{token}")
async def get_contractor_by_token(
    token: str = Path(..., description="Document upload token"),
    service: ContractorService = Depends(get_contractor_service),
):
    """
    Get contractor by document upload token.

    Public endpoint - no auth required.
    """
    try:
        contractor = await service.get_by_token(token)
        # Return limited info for public endpoint
        return success_response({
            "id": contractor.id,
            "first_name": contractor.first_name,
            "surname": contractor.surname,
            "email": contractor.email,
            "status": contractor.status,
        })
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/contract-token/{token}")
async def get_contractor_by_contract_token(
    token: str = Path(..., description="Contract signing token"),
    service: ContractorService = Depends(get_contractor_service),
):
    """
    Get contractor by contract signing token.

    Public endpoint - no auth required.
    """
    try:
        contractor = await service.get_by_contract_token(token)
        return success_response({
            "id": contractor.id,
            "first_name": contractor.first_name,
            "surname": contractor.surname,
            "email": contractor.email,
            "status": contractor.status,
        })
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{id}")
async def update_contractor(
    id: int = Path(..., description="Contractor ID"),
    data: ContractorUpdate = ...,
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Update contractor data."""
    try:
        contractor = await service.update(id, data)
        return success_response(contractor)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{id}/select-route")
async def select_onboarding_route(
    id: int = Path(..., description="Contractor ID"),
    route: OnboardingRoute = ...,
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Select onboarding route for contractor."""
    try:
        contractor = await service.select_route(id, route)
        return success_response(contractor)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/update-status")
async def update_contractor_status(
    id: int = Path(..., description="Contractor ID"),
    new_status: ContractorStatus = ...,
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Update contractor status."""
    try:
        contractor = await service.update_status(id, new_status)
        return success_response(contractor)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/generate-contract-token")
async def generate_contract_token(
    id: int = Path(..., description="Contractor ID"),
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """Generate contract signing token for contractor."""
    try:
        result = await service.generate_contract_token(id)
        return success_response(result)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/client/{client_id}")
async def get_contractors_by_client(
    client_id: int = Path(..., description="Client ID"),
    service: ContractorService = Depends(get_contractor_service),
    current_user: dict = Depends(get_current_user),
):
    """Get all contractors for a specific client."""
    contractors = await service.get_by_client(client_id)
    return success_response([
        {
            "id": c.id,
            "first_name": c.first_name,
            "surname": c.surname,
            "email": c.email,
            "status": c.status,
        }
        for c in contractors
    ])
