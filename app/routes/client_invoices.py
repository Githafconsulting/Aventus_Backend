"""
Client Invoice Routes - Consolidated client invoices (one per client per period).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.client_invoice import ClientInvoice, ClientInvoiceStatus, ClientInvoiceLineItem
from app.models.client import Client
from app.services import client_invoice_service
from app.schemas.client_invoice import (
    GenerateClientInvoiceRequest, RecordPaymentRequest,
)

router = APIRouter(prefix="/api/v1/client-invoices", tags=["Client Invoices"])


def _format_invoice_response(invoice: ClientInvoice, include_details: bool = False) -> dict:
    """Format a client invoice for API response."""
    client = invoice.client
    client_name = client.company_name if client else None

    data = {
        "id": invoice.id,
        "client_id": invoice.client_id,
        "client_name": client_name,
        "period": invoice.period,
        "invoice_number": invoice.invoice_number,
        "subtotal": invoice.subtotal,
        "vat_rate": invoice.vat_rate,
        "vat_amount": invoice.vat_amount,
        "total_amount": invoice.total_amount,
        "amount_paid": invoice.amount_paid,
        "balance": invoice.balance,
        "currency": invoice.currency,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "status": invoice.status.value if hasattr(invoice.status, 'value') else invoice.status,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
    }

    if include_details:
        data["payment_terms"] = invoice.payment_terms
        data["pdf_url"] = invoice.pdf_url
        data["sent_at"] = invoice.sent_at.isoformat() if invoice.sent_at else None
        data["viewed_at"] = invoice.viewed_at.isoformat() if invoice.viewed_at else None
        data["paid_at"] = invoice.paid_at.isoformat() if invoice.paid_at else None
        data["notes"] = invoice.notes
        data["line_items"] = [
            {
                "id": li.id,
                "payroll_id": li.payroll_id,
                "contractor_id": li.contractor_id,
                "contractor_name": li.contractor_name,
                "description": li.description,
                "subtotal": li.subtotal,
                "vat_amount": li.vat_amount,
                "total": li.total,
            }
            for li in invoice.line_items
        ]
        data["payments"] = [
            {
                "id": p.id,
                "amount": p.amount,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "payment_method": p.payment_method,
                "reference_number": p.reference_number,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in invoice.payments
        ]

    return data


@router.get("/")
def list_client_invoices(
    client_id: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List consolidated client invoices with optional filters."""
    query = db.query(ClientInvoice).order_by(ClientInvoice.created_at.desc())

    if client_id:
        query = query.filter(ClientInvoice.client_id == client_id)
    if period:
        query = query.filter(ClientInvoice.period == period)
    if status:
        try:
            inv_status = ClientInvoiceStatus(status)
            query = query.filter(ClientInvoice.status == inv_status)
        except ValueError:
            pass

    invoices = query.all()
    return {
        "invoices": [_format_invoice_response(inv) for inv in invoices],
        "count": len(invoices),
    }


@router.get("/stats")
def get_client_invoice_stats(db: Session = Depends(get_db)):
    """Get client invoice statistics."""
    return client_invoice_service.get_stats(db)


@router.get("/{invoice_id}")
def get_client_invoice_detail(invoice_id: int, db: Session = Depends(get_db)):
    """Get client invoice detail with line items and payments."""
    invoice = db.query(ClientInvoice).filter(ClientInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Client invoice not found")
    return _format_invoice_response(invoice, include_details=True)


@router.post("/generate")
def generate_invoice(
    request: GenerateClientInvoiceRequest,
    db: Session = Depends(get_db),
):
    """Generate a consolidated invoice for a client + period."""
    result = client_invoice_service.generate_client_invoice(
        db, request.client_id, request.period, request.payment_terms, request.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.post("/{invoice_id}/send")
def send_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Mark invoice as sent (email sending handled separately)."""
    invoice = db.query(ClientInvoice).filter(ClientInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Client invoice not found")

    invoice.status = ClientInvoiceStatus.SENT
    invoice.sent_at = datetime.utcnow()
    db.commit()
    return {"message": "Invoice marked as sent", "invoice_number": invoice.invoice_number}


@router.post("/{invoice_id}/payments")
def record_payment(
    invoice_id: int,
    request: RecordPaymentRequest,
    db: Session = Depends(get_db),
):
    """Record a payment against a client invoice."""
    result = client_invoice_service.record_payment(
        db, invoice_id, request.amount, request.payment_date,
        request.payment_method, request.reference_number, request.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return {"message": "Payment recorded successfully"}


# --- Portal access (public, no auth) ---

@router.get("/portal/{access_token}")
def portal_view(access_token: str, db: Session = Depends(get_db)):
    """Public portal: view client invoice via token."""
    invoice = db.query(ClientInvoice).filter(
        ClientInvoice.access_token == access_token
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.token_expiry and invoice.token_expiry < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Access link has expired")

    # Mark as viewed
    client_invoice_service.mark_viewed(db, access_token)
    db.commit()

    return _format_invoice_response(invoice, include_details=True)
