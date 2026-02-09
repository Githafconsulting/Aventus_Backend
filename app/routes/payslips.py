"""
Payslip API routes.

Handles payslip generation, delivery, and portal access.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.payslip import Payslip, PayslipStatus
from app.models.payroll import Payroll
from app.models.contractor import Contractor
from app.schemas.payslip import (
    PayslipResponse,
    PayslipListResponse,
    PayslipBulkCreate,
    PayslipBulkSend,
    PayslipPortalResponse,
    PayslipStatsResponse,
)
from app.repositories.implementations.payslip_repo import PayslipRepository
from app.services.payslip_service import PayslipService
from app.utils.auth import get_current_active_user
from app.models.user import User
from app.utils.payroll_pdf import generate_payslip_pdf

router = APIRouter(prefix="/api/v1/payslips", tags=["payslips"])


def get_payslip_service(db: Session = Depends(get_db)) -> PayslipService:
    """Get payslip service instance."""
    repo = PayslipRepository(db)
    return PayslipService(repo, db)


@router.get("/", response_model=List[PayslipListResponse])
async def list_payslips(
    status: Optional[str] = None,
    period: Optional[str] = None,
    query: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all payslips with optional filters."""
    service = get_payslip_service(db)

    status_enum = None
    if status and status != "all":
        try:
            status_enum = PayslipStatus(status)
        except ValueError:
            pass

    payslips, total = await service.search(
        query=query,
        status=status_enum,
        period=period,
        skip=skip,
        limit=limit,
    )

    # Build response with nested data
    result = []
    for payslip in payslips:
        contractor = db.query(Contractor).filter(
            Contractor.id == payslip.contractor_id
        ).first()
        payroll = db.query(Payroll).filter(
            Payroll.id == payslip.payroll_id
        ).first()

        result.append(PayslipListResponse(
            id=payslip.id,
            payroll_id=payslip.payroll_id,
            contractor_id=payslip.contractor_id,
            contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else "Unknown",
            contractor_email=contractor.email if contractor else None,
            client_name=contractor.client_name if contractor else None,
            document_number=payslip.document_number,
            period=payslip.period,
            net_salary=payroll.net_salary if payroll else None,
            currency=payroll.currency if payroll else None,
            status=payslip.status,
            sent_at=payslip.sent_at,
            viewed_at=payslip.viewed_at,
            acknowledged_at=payslip.acknowledged_at,
            created_at=payslip.created_at,
        ))

    return result


@router.get("/stats", response_model=PayslipStatsResponse)
async def get_payslip_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get payslip statistics."""
    service = get_payslip_service(db)
    return await service.get_stats()


@router.get("/pending-payrolls")
async def get_pending_payrolls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get paid payrolls that don't have payslips generated yet."""
    from app.models.payroll import PayrollStatus
    from sqlalchemy import not_, exists

    # Get paid payrolls that don't have a payslip
    subquery = db.query(Payslip.payroll_id).subquery()

    payrolls = db.query(Payroll).filter(
        Payroll.status == PayrollStatus.PAID,
        ~Payroll.id.in_(db.query(subquery))
    ).order_by(Payroll.paid_at.desc()).all()

    result = []
    for payroll in payrolls:
        contractor = db.query(Contractor).filter(
            Contractor.id == payroll.contractor_id
        ).first()

        result.append({
            "id": payroll.id,
            "contractor_id": payroll.contractor_id,
            "contractor_name": f"{contractor.first_name} {contractor.surname}" if contractor else "Unknown",
            "client_name": payroll.client_name,
            "period": payroll.period,
            "net_salary": payroll.net_salary,
            "currency": payroll.currency,
            "paid_at": payroll.paid_at.isoformat() if payroll.paid_at else None,
            "has_payslip": False,
        })

    return result


@router.get("/{payslip_id}", response_model=PayslipResponse)
async def get_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get payslip details."""
    repo = PayslipRepository(db)
    payslip = await repo.get(payslip_id)

    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )

    contractor = db.query(Contractor).filter(
        Contractor.id == payslip.contractor_id
    ).first()
    payroll = db.query(Payroll).filter(
        Payroll.id == payslip.payroll_id
    ).first()

    return PayslipResponse(
        id=payslip.id,
        payroll_id=payslip.payroll_id,
        contractor_id=payslip.contractor_id,
        document_number=payslip.document_number,
        period=payslip.period,
        pdf_url=payslip.pdf_url,
        status=payslip.status,
        sent_at=payslip.sent_at,
        viewed_at=payslip.viewed_at,
        acknowledged_at=payslip.acknowledged_at,
        created_at=payslip.created_at,
        updated_at=payslip.updated_at,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        contractor_email=contractor.email if contractor else None,
        client_name=contractor.client_name if contractor else None,
        net_salary=payroll.net_salary if payroll else None,
        currency=payroll.currency if payroll else None,
    )


@router.post("/generate/{payroll_id}", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
async def generate_payslip(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a payslip for a payroll."""
    service = get_payslip_service(db)

    try:
        payslip = await service.generate_payslip(payroll_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    contractor = db.query(Contractor).filter(
        Contractor.id == payslip.contractor_id
    ).first()
    payroll = db.query(Payroll).filter(
        Payroll.id == payslip.payroll_id
    ).first()

    return PayslipResponse(
        id=payslip.id,
        payroll_id=payslip.payroll_id,
        contractor_id=payslip.contractor_id,
        document_number=payslip.document_number,
        period=payslip.period,
        pdf_url=payslip.pdf_url,
        status=payslip.status,
        sent_at=payslip.sent_at,
        viewed_at=payslip.viewed_at,
        acknowledged_at=payslip.acknowledged_at,
        created_at=payslip.created_at,
        updated_at=payslip.updated_at,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        contractor_email=contractor.email if contractor else None,
        client_name=contractor.client_name if contractor else None,
        net_salary=payroll.net_salary if payroll else None,
        currency=payroll.currency if payroll else None,
    )


@router.post("/generate/bulk")
async def generate_payslips_bulk(
    data: PayslipBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk generate payslips."""
    service = get_payslip_service(db)
    return await service.generate_bulk(data.payroll_ids)


@router.post("/{payslip_id}/send")
async def send_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send payslip email to contractor."""
    service = get_payslip_service(db)

    try:
        success = await service.send_payslip(payslip_id)
        return {"success": success, "message": "Payslip sent successfully" if success else "Failed to send"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/send/bulk")
async def send_payslips_bulk(
    data: PayslipBulkSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk send payslips."""
    service = get_payslip_service(db)
    return await service.send_bulk(data.payslip_ids)


@router.get("/{payslip_id}/pdf")
async def download_payslip_pdf(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download payslip PDF."""
    repo = PayslipRepository(db)
    payslip = await repo.get(payslip_id)

    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )

    payroll = db.query(Payroll).filter(Payroll.id == payslip.payroll_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == payslip.contractor_id).first()

    if not payroll or not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related records not found"
        )

    pdf_buffer = generate_payslip_pdf(payroll, contractor)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{payslip.document_number}.pdf"'
        }
    )


@router.put("/{payslip_id}/regenerate", response_model=PayslipResponse)
async def regenerate_payslip_pdf(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Regenerate payslip PDF."""
    service = get_payslip_service(db)

    try:
        payslip = await service.regenerate_pdf(payslip_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    contractor = db.query(Contractor).filter(
        Contractor.id == payslip.contractor_id
    ).first()
    payroll = db.query(Payroll).filter(
        Payroll.id == payslip.payroll_id
    ).first()

    return PayslipResponse(
        id=payslip.id,
        payroll_id=payslip.payroll_id,
        contractor_id=payslip.contractor_id,
        document_number=payslip.document_number,
        period=payslip.period,
        pdf_url=payslip.pdf_url,
        status=payslip.status,
        sent_at=payslip.sent_at,
        viewed_at=payslip.viewed_at,
        acknowledged_at=payslip.acknowledged_at,
        created_at=payslip.created_at,
        updated_at=payslip.updated_at,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        contractor_email=contractor.email if contractor else None,
        client_name=contractor.client_name if contractor else None,
        net_salary=payroll.net_salary if payroll else None,
        currency=payroll.currency if payroll else None,
    )


# Public portal endpoints (no auth required)
@router.get("/portal/{token}", response_model=PayslipPortalResponse)
async def get_payslip_portal(
    token: str,
    db: Session = Depends(get_db),
):
    """Get payslip via portal access token (public)."""
    service = get_payslip_service(db)

    payslip = await service.get_by_access_token(token)
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found or link expired"
        )

    # Mark as viewed
    await service.mark_viewed(payslip.id)

    contractor = db.query(Contractor).filter(
        Contractor.id == payslip.contractor_id
    ).first()
    payroll = db.query(Payroll).filter(
        Payroll.id == payslip.payroll_id
    ).first()

    return PayslipPortalResponse(
        id=payslip.id,
        document_number=payslip.document_number,
        period=payslip.period,
        pdf_url=payslip.pdf_url,
        status=payslip.status,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else "Contractor",
        net_salary=payroll.net_salary if payroll else None,
        currency=payroll.currency if payroll else None,
        created_at=payslip.created_at,
    )


@router.put("/portal/{token}/acknowledge")
async def acknowledge_payslip(
    token: str,
    db: Session = Depends(get_db),
):
    """Acknowledge receipt of payslip (public)."""
    service = get_payslip_service(db)

    payslip = await service.get_by_access_token(token)
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found or link expired"
        )

    await service.acknowledge(payslip.id)

    return {"success": True, "message": "Payslip acknowledged"}
