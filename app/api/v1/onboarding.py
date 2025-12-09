"""
Onboarding API Routes.

Thin route layer for onboarding workflow operations.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel

from app.api.dependencies import (
    get_onboarding_service,
    get_current_user,
    get_current_admin_user,
)
from app.api.responses import success_response
from app.services.onboarding_service import OnboardingService
from app.domain.contractor.exceptions import ContractorNotFoundError

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


class ExecuteStepRequest(BaseModel):
    """Request to execute an onboarding step."""
    step_id: str
    data: Dict[str, Any] = {}


@router.get("/routes")
async def get_available_routes(
    service: OnboardingService = Depends(get_onboarding_service),
    current_user: dict = Depends(get_current_user),
):
    """Get list of available onboarding routes."""
    routes = await service.get_available_routes()
    return success_response(routes)


@router.get("/routes/{route}/documents")
async def get_required_documents(
    route: str = Path(..., description="Onboarding route"),
    service: OnboardingService = Depends(get_onboarding_service),
    current_user: dict = Depends(get_current_user),
):
    """Get required documents for a specific route."""
    try:
        documents = await service.get_required_documents(route)
        return success_response(documents)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/contractor/{contractor_id}/status")
async def get_workflow_status(
    contractor_id: int = Path(..., description="Contractor ID"),
    service: OnboardingService = Depends(get_onboarding_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current workflow status for a contractor.

    Returns workflow steps, current step, completed and pending steps.
    """
    try:
        status = await service.get_workflow_status(contractor_id)
        return success_response(status)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/contractor/{contractor_id}/next-action")
async def get_next_action(
    contractor_id: int = Path(..., description="Contractor ID"),
    service: OnboardingService = Depends(get_onboarding_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the next required action for a contractor.

    Returns action type, description, and who needs to act.
    """
    try:
        action = await service.get_next_action(contractor_id)
        return success_response(action)
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/contractor/{contractor_id}/execute-step")
async def execute_step(
    contractor_id: int = Path(..., description="Contractor ID"),
    request: ExecuteStepRequest = ...,
    service: OnboardingService = Depends(get_onboarding_service),
    current_user: dict = Depends(get_current_admin_user),
):
    """
    Execute an onboarding step for a contractor.

    Advances the contractor through the onboarding workflow.
    """
    try:
        result = await service.execute_step(
            contractor_id,
            request.step_id,
            request.data,
        )
        return success_response({
            "next_status": result.next_status.value,
            "message": result.message,
            "requires_external_action": result.requires_external_action,
            "external_action_type": result.external_action_type,
        })
    except ContractorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
