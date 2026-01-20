from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.proposal import Proposal, ProposalStatus
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.proposal import ProposalCreate, ProposalUpdate, ProposalResponse
from app.utils.auth import get_current_active_user
from app.utils.email import send_proposal_email
from datetime import datetime

router = APIRouter(prefix="/api/v1/proposals", tags=["proposals"])


def generate_proposal_number(db: Session) -> str:
    """Generate unique proposal number like PROP-2025-001"""
    year = datetime.utcnow().year

    # Get the count of proposals created this year
    count = db.query(Proposal).filter(
        Proposal.proposal_number.like(f"PROP-{year}-%")
    ).count()

    next_number = count + 1
    return f"PROP-{year}-{next_number:03d}"


@router.post("/", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new proposal
    """
    # Verify client exists
    client = db.query(Client).filter(Client.id == proposal_data.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    # Generate proposal number
    proposal_number = generate_proposal_number(db)

    # Create proposal
    proposal_dict = proposal_data.model_dump()
    proposal = Proposal(
        **proposal_dict,
        proposal_number=proposal_number,
        consultant_id=current_user.id,
        client_company_name=client.company_name
    )

    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return proposal


@router.get("/", response_model=List[ProposalResponse])
async def get_proposals(
    status_filter: Optional[ProposalStatus] = None,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all proposals with optional filters
    """
    query = db.query(Proposal)

    # Consultants can only see their own proposals
    if current_user.role == UserRole.CONSULTANT:
        query = query.filter(Proposal.consultant_id == current_user.id)

    if status_filter:
        query = query.filter(Proposal.status == status_filter)

    if client_id:
        query = query.filter(Proposal.client_id == client_id)

    proposals = query.order_by(Proposal.created_at.desc()).all()
    return proposals


@router.get("/summary", response_model=List[dict])
async def get_proposals_summary(
    status_filter: Optional[ProposalStatus] = None,
    client_id: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get proposals with minimal fields for dashboard/list views.
    Much faster than full list - only fetches required columns.
    Supports pagination with page and limit parameters.
    """
    # Only select the columns needed for dashboard display
    query = db.query(
        Proposal.id,
        Proposal.proposal_number,
        Proposal.client_id,
        Proposal.client_company_name,
        Proposal.project_name,
        Proposal.status,
        Proposal.total_amount,
        Proposal.currency,
        Proposal.created_at,
        Proposal.valid_until
    )

    # Consultants can only see their own proposals
    if current_user.role == UserRole.CONSULTANT:
        query = query.filter(Proposal.consultant_id == current_user.id)

    if status_filter:
        query = query.filter(Proposal.status == status_filter)

    if client_id:
        query = query.filter(Proposal.client_id == client_id)

    # Apply pagination
    offset = (page - 1) * limit
    results = query.order_by(Proposal.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to list of dicts
    return [
        {
            "id": r.id,
            "proposal_number": r.proposal_number,
            "client_id": r.client_id,
            "client_company_name": r.client_company_name,
            "project_name": r.project_name,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "total_amount": r.total_amount,
            "currency": r.currency,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "valid_until": r.valid_until.isoformat() if r.valid_until else None
        }
        for r in results
    ]


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific proposal by ID
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and proposal.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this proposal"
        )

    return proposal


@router.put("/{proposal_id}", response_model=ProposalResponse)
async def update_proposal(
    proposal_id: str,
    proposal_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a proposal
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and proposal.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this proposal"
        )

    # Verify client exists if being updated
    if proposal_data.client_id:
        client = db.query(Client).filter(Client.id == proposal_data.client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        proposal.client_company_name = client.company_name

    # Update fields
    update_data = proposal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proposal, field, value)

    db.commit()
    db.refresh(proposal)

    return proposal


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a proposal (admin/superadmin only)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete proposals"
        )

    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    db.delete(proposal)
    db.commit()

    return None


@router.post("/{proposal_id}/send", response_model=ProposalResponse)
async def send_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send proposal to client via email
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and proposal.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send this proposal"
        )

    # Get client
    client = db.query(Client).filter(Client.id == proposal.client_id).first()
    if not client or not client.contact_person_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client email not found"
        )

    # Generate proposal link
    from app.config import settings
    proposal_link = f"{settings.frontend_url}/proposals/{proposal.id}"

    # Send email
    email_sent = send_proposal_email(
        client_email=client.contact_person_email,
        client_company_name=client.company_name,
        proposal_link=proposal_link,
        consultant_name=current_user.full_name,
        project_name=proposal.project_name
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send proposal email"
        )

    # Update proposal status
    proposal.status = ProposalStatus.SENT
    proposal.sent_at = datetime.utcnow()

    db.commit()
    db.refresh(proposal)

    return proposal


@router.patch("/{proposal_id}/status", response_model=ProposalResponse)
async def update_proposal_status(
    proposal_id: str,
    new_status: ProposalStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update proposal status
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )

    # Check permissions
    if current_user.role == UserRole.CONSULTANT and proposal.consultant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this proposal"
        )

    # Update status and set timestamps
    proposal.status = new_status

    if new_status == ProposalStatus.VIEWED and not proposal.viewed_at:
        proposal.viewed_at = datetime.utcnow()

    if new_status in [ProposalStatus.ACCEPTED, ProposalStatus.REJECTED] and not proposal.responded_at:
        proposal.responded_at = datetime.utcnow()

    db.commit()
    db.refresh(proposal)

    return proposal
