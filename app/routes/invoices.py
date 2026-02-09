"""
Invoice API routes.

Handles invoice generation, payment tracking, and portal access.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.payroll import Payroll
from app.models.contractor import Contractor
from app.models.client import Client
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceDetailResponse,
    InvoiceListResponse,
    InvoiceBulkSend,
    InvoicePaymentCreate,
    InvoicePaymentResponse,
    InvoicePortalResponse,
    InvoiceStatsResponse,
)
from app.repositories.implementations.invoice_repo import InvoiceRepository, InvoicePaymentRepository
from app.services.invoice_service import InvoiceService
from app.utils.auth import get_current_active_user
from app.models.user import User
from app.utils.payroll_pdf import generate_invoice_pdf

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


def _batch_load_invoice_relations(invoices: list, db: Session) -> list[InvoiceListResponse]:
    """
    Batch load related entities for invoices to avoid N+1 queries.
    Instead of 3 queries per invoice, this makes only 3 queries total.
    """
    if not invoices:
        return []

    # Collect all unique IDs
    client_ids = {inv.client_id for inv in invoices if inv.client_id}
    contractor_ids = {inv.contractor_id for inv in invoices if inv.contractor_id}
    payroll_ids = {inv.payroll_id for inv in invoices if inv.payroll_id}

    # Batch load all related entities (3 queries instead of 3*N)
    clients_map = {}
    if client_ids:
        clients = db.query(Client).filter(Client.id.in_(client_ids)).all()
        clients_map = {c.id: c for c in clients}

    contractors_map = {}
    if contractor_ids:
        contractors = db.query(Contractor).filter(Contractor.id.in_(contractor_ids)).all()
        contractors_map = {c.id: c for c in contractors}

    payrolls_map = {}
    if payroll_ids:
        payrolls = db.query(Payroll).filter(Payroll.id.in_(payroll_ids)).all()
        payrolls_map = {p.id: p for p in payrolls}

    # Build response using lookup dictionaries
    result = []
    for invoice in invoices:
        client = clients_map.get(invoice.client_id)
        contractor = contractors_map.get(invoice.contractor_id)
        payroll = payrolls_map.get(invoice.payroll_id)

        result.append(InvoiceListResponse(
            id=invoice.id,
            payroll_id=invoice.payroll_id,
            client_id=invoice.client_id,
            client_name=client.company_name if client else None,
            contractor_id=invoice.contractor_id,
            contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
            invoice_number=invoice.invoice_number,
            total_amount=invoice.total_amount,
            amount_paid=invoice.amount_paid,
            balance=invoice.balance,
            currency=payroll.currency if payroll else None,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            status=invoice.status,
            period=payroll.period if payroll else None,
            created_at=invoice.created_at,
        ))

    return result


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    """Get invoice service instance."""
    invoice_repo = InvoiceRepository(db)
    payment_repo = InvoicePaymentRepository(db)
    return InvoiceService(invoice_repo, payment_repo, db)


@router.get("/", response_model=List[InvoiceListResponse])
async def list_invoices(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    query: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all invoices with optional filters."""
    service = get_invoice_service(db)

    status_enum = None
    if status and status != "all":
        try:
            status_enum = InvoiceStatus(status)
        except ValueError:
            pass

    invoices, total = await service.search(
        query=query,
        status=status_enum,
        client_id=client_id,
        skip=skip,
        limit=limit,
    )

    # Use batch loading to avoid N+1 queries (3 queries instead of 3*N)
    return _batch_load_invoice_relations(invoices, db)


@router.get("/stats", response_model=InvoiceStatsResponse)
async def get_invoice_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get invoice statistics."""
    service = get_invoice_service(db)
    return await service.get_stats()


@router.get("/overdue", response_model=List[InvoiceListResponse])
async def get_overdue_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all overdue invoices."""
    repo = InvoiceRepository(db)
    invoices = await repo.get_overdue()

    # Use batch loading to avoid N+1 queries
    return _batch_load_invoice_relations(invoices, db)


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get invoice details with payments."""
    invoice_repo = InvoiceRepository(db)
    payment_repo = InvoicePaymentRepository(db)

    invoice = await invoice_repo.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    payments = await payment_repo.get_by_invoice_id(invoice_id)
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()
    payroll = db.query(Payroll).filter(Payroll.id == invoice.payroll_id).first()

    return InvoiceDetailResponse(
        id=invoice.id,
        payroll_id=invoice.payroll_id,
        client_id=invoice.client_id,
        contractor_id=invoice.contractor_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        vat_rate=invoice.vat_rate,
        vat_amount=invoice.vat_amount,
        total_amount=invoice.total_amount,
        amount_paid=invoice.amount_paid,
        balance=invoice.balance,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        pdf_url=invoice.pdf_url,
        status=invoice.status,
        sent_at=invoice.sent_at,
        viewed_at=invoice.viewed_at,
        paid_at=invoice.paid_at,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        client_name=client.company_name if client else None,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        period=payroll.period if payroll else None,
        currency=payroll.currency if payroll else None,
        payments=[InvoicePaymentResponse(
            id=p.id,
            invoice_id=p.invoice_id,
            amount=p.amount,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            reference_number=p.reference_number,
            notes=p.notes,
            created_at=p.created_at,
        ) for p in payments],
    )


@router.post("/generate/{payroll_id}", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice(
    payroll_id: int,
    data: Optional[InvoiceCreate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate an invoice for a payroll."""
    service = get_invoice_service(db)

    payment_terms = data.payment_terms if data else "Net 30"
    notes = data.notes if data else None

    try:
        invoice = await service.generate_invoice(
            payroll_id=payroll_id,
            payment_terms=payment_terms,
            notes=notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()
    payroll = db.query(Payroll).filter(Payroll.id == invoice.payroll_id).first()

    return InvoiceResponse(
        id=invoice.id,
        payroll_id=invoice.payroll_id,
        client_id=invoice.client_id,
        contractor_id=invoice.contractor_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        vat_rate=invoice.vat_rate,
        vat_amount=invoice.vat_amount,
        total_amount=invoice.total_amount,
        amount_paid=invoice.amount_paid,
        balance=invoice.balance,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        pdf_url=invoice.pdf_url,
        status=invoice.status,
        sent_at=invoice.sent_at,
        viewed_at=invoice.viewed_at,
        paid_at=invoice.paid_at,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        client_name=client.company_name if client else None,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        period=payroll.period if payroll else None,
        currency=payroll.currency if payroll else None,
    )


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a draft invoice."""
    service = get_invoice_service(db)

    try:
        invoice = await service.update_invoice(
            invoice_id=invoice_id,
            payment_terms=data.payment_terms,
            due_date=data.due_date,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()
    payroll = db.query(Payroll).filter(Payroll.id == invoice.payroll_id).first()

    return InvoiceResponse(
        id=invoice.id,
        payroll_id=invoice.payroll_id,
        client_id=invoice.client_id,
        contractor_id=invoice.contractor_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        vat_rate=invoice.vat_rate,
        vat_amount=invoice.vat_amount,
        total_amount=invoice.total_amount,
        amount_paid=invoice.amount_paid,
        balance=invoice.balance,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        pdf_url=invoice.pdf_url,
        status=invoice.status,
        sent_at=invoice.sent_at,
        viewed_at=invoice.viewed_at,
        paid_at=invoice.paid_at,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        client_name=client.company_name if client else None,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        period=payroll.period if payroll else None,
        currency=payroll.currency if payroll else None,
    )


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a draft invoice."""
    service = get_invoice_service(db)

    try:
        success = await service.delete_invoice(invoice_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send invoice email to client."""
    service = get_invoice_service(db)

    try:
        success = await service.send_invoice(invoice_id)
        return {"success": success, "message": "Invoice sent successfully" if success else "Failed to send"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/send/bulk")
async def send_invoices_bulk(
    data: InvoiceBulkSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk send invoices."""
    service = get_invoice_service(db)
    return await service.send_bulk(data.invoice_ids)


@router.post("/{invoice_id}/payments", response_model=InvoicePaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    invoice_id: int,
    data: InvoicePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a payment against an invoice."""
    service = get_invoice_service(db)

    try:
        payment = await service.record_payment(
            invoice_id=invoice_id,
            amount=data.amount,
            payment_date=data.payment_date,
            payment_method=data.payment_method,
            reference_number=data.reference_number,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return InvoicePaymentResponse(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        notes=payment.notes,
        created_at=payment.created_at,
    )


@router.get("/{invoice_id}/payments", response_model=List[InvoicePaymentResponse])
async def list_payments(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all payments for an invoice."""
    payment_repo = InvoicePaymentRepository(db)
    payments = await payment_repo.get_by_invoice_id(invoice_id)

    return [InvoicePaymentResponse(
        id=p.id,
        invoice_id=p.invoice_id,
        amount=p.amount,
        payment_date=p.payment_date,
        payment_method=p.payment_method,
        reference_number=p.reference_number,
        notes=p.notes,
        created_at=p.created_at,
    ) for p in payments]


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download invoice PDF."""
    repo = InvoiceRepository(db)
    invoice = await repo.get(invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    payroll = db.query(Payroll).filter(Payroll.id == invoice.payroll_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()

    if not payroll or not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related records not found"
        )

    pdf_buffer = generate_invoice_pdf(payroll, contractor)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'
        }
    )


@router.post("/{invoice_id}/reminder")
async def send_overdue_reminder(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Send overdue reminder email."""
    service = get_invoice_service(db)

    try:
        success = await service.send_overdue_reminder(invoice_id)
        return {"success": success, "message": "Reminder sent successfully" if success else "Failed to send"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Public portal endpoints (no auth required)
@router.get("/portal/{token}", response_model=InvoicePortalResponse)
async def get_invoice_portal(
    token: str,
    db: Session = Depends(get_db),
):
    """Get invoice via portal access token (public)."""
    service = get_invoice_service(db)

    invoice = await service.get_by_access_token(token)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or link expired"
        )

    # Mark as viewed
    await service.mark_viewed(invoice.id)

    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()
    payroll = db.query(Payroll).filter(Payroll.id == invoice.payroll_id).first()

    payment_repo = InvoicePaymentRepository(db)
    payments = await payment_repo.get_by_invoice_id(invoice.id)

    return InvoicePortalResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        client_name=client.company_name if client else None,
        contractor_name=f"{contractor.first_name} {contractor.surname}" if contractor else None,
        period=payroll.period if payroll else None,
        subtotal=invoice.subtotal,
        vat_rate=invoice.vat_rate,
        vat_amount=invoice.vat_amount,
        total_amount=invoice.total_amount,
        amount_paid=invoice.amount_paid,
        balance=invoice.balance,
        currency=payroll.currency if payroll else None,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        pdf_url=invoice.pdf_url,
        status=invoice.status,
        payments=[InvoicePaymentResponse(
            id=p.id,
            invoice_id=p.invoice_id,
            amount=p.amount,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            reference_number=p.reference_number,
            notes=p.notes,
            created_at=p.created_at,
        ) for p in payments],
    )
