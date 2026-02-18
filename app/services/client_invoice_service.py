"""
Client Invoice Service - Consolidated invoices (one per client per period).
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.client_invoice import ClientInvoice, ClientInvoiceStatus, ClientInvoiceLineItem, ClientInvoicePayment
from app.models.payroll import Payroll, PayrollStatus
from app.models.contractor import Contractor
from app.models.client import Client


def _generate_invoice_number(db: Session) -> str:
    """Generate next sequential CINV-YYYY-NNNN number."""
    year = datetime.utcnow().year
    prefix = f"CINV-{year}-"

    last = (
        db.query(ClientInvoice)
        .filter(ClientInvoice.invoice_number.like(f"{prefix}%"))
        .order_by(ClientInvoice.invoice_number.desc())
        .with_for_update()
        .first()
    )

    if last:
        try:
            seq = int(last.invoice_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def _get_contractor_name(contractor: Contractor) -> str:
    """Get formatted contractor name."""
    parts = [contractor.first_name, contractor.surname]
    return " ".join(p for p in parts if p) or "Unknown"


def generate_client_invoice(
    db: Session,
    client_id: str,
    period: str,
    payment_terms: str = "Net 30",
    notes: Optional[str] = None,
) -> dict:
    """
    Generate a consolidated invoice for all approved payrolls for a client in a period.
    """
    # Check if invoice already exists
    existing = db.query(ClientInvoice).filter(
        ClientInvoice.client_id == client_id,
        ClientInvoice.period == period,
    ).first()
    if existing:
        return {"error": f"Invoice already exists for this client/period: {existing.invoice_number}"}

    # Get client
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"error": "Client not found"}

    # Get all approved payrolls for this client+period (via contractor's client_id)
    payrolls = (
        db.query(Payroll)
        .join(Contractor, Payroll.contractor_id == Contractor.id)
        .filter(
            Contractor.client_id == client_id,
            Payroll.period == period,
            Payroll.status.in_([PayrollStatus.APPROVED, PayrollStatus.APPROVED_ADJUSTED, PayrollStatus.PAID]),
        )
        .all()
    )

    if not payrolls:
        return {"error": "No approved payrolls found for this client/period"}

    # Calculate totals
    subtotal = sum(p.invoice_total or 0 for p in payrolls)
    # Use weighted average VAT rate (all payrolls for same client should have same rate)
    vat_rate = payrolls[0].vat_rate if payrolls else 0.05
    vat_amount = subtotal * vat_rate
    total_amount = subtotal + vat_amount

    # Parse payment terms for due date
    due_days = 30
    if payment_terms:
        try:
            due_days = int(payment_terms.lower().replace("net ", "").strip())
        except ValueError:
            due_days = 30

    invoice_date = date.today()
    due_date = invoice_date + timedelta(days=due_days)

    # Create invoice
    invoice = ClientInvoice(
        client_id=client_id,
        period=period,
        invoice_number=_generate_invoice_number(db),
        subtotal=round(subtotal, 2),
        vat_rate=vat_rate,
        vat_amount=round(vat_amount, 2),
        total_amount=round(total_amount, 2),
        amount_paid=0,
        balance=round(total_amount, 2),
        currency=payrolls[0].currency or "AED",
        invoice_date=invoice_date,
        due_date=due_date,
        payment_terms=payment_terms,
        status=ClientInvoiceStatus.DRAFT,
        access_token=str(uuid.uuid4()),
        token_expiry=datetime.utcnow() + timedelta(days=90),
        notes=notes,
    )
    db.add(invoice)
    db.flush()

    # Create line items
    for payroll in payrolls:
        line_item = ClientInvoiceLineItem(
            client_invoice_id=invoice.id,
            payroll_id=payroll.id,
            contractor_id=payroll.contractor_id,
            description=f"Services for {period}",
            subtotal=round(payroll.invoice_total or 0, 2),
            vat_amount=round((payroll.invoice_total or 0) * vat_rate, 2),
            total=round((payroll.invoice_total or 0) * (1 + vat_rate), 2),
        )
        db.add(line_item)

    db.flush()
    return {"success": True, "invoice_id": invoice.id, "invoice_number": invoice.invoice_number}


def record_payment(
    db: Session,
    invoice_id: int,
    amount: float,
    payment_date: date,
    payment_method: Optional[str] = None,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Record a payment against a client invoice."""
    invoice = db.query(ClientInvoice).filter(ClientInvoice.id == invoice_id).first()
    if not invoice:
        return {"error": "Invoice not found"}

    payment = ClientInvoicePayment(
        client_invoice_id=invoice_id,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
    )
    db.add(payment)

    # Update invoice payment tracking
    invoice.amount_paid = (invoice.amount_paid or 0) + amount
    invoice.balance = (invoice.total_amount or 0) - invoice.amount_paid

    if invoice.balance <= 0:
        invoice.status = ClientInvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
        invoice.balance = 0
    elif invoice.amount_paid > 0:
        invoice.status = ClientInvoiceStatus.PARTIALLY_PAID

    db.flush()
    return {"success": True}


def mark_viewed(db: Session, access_token: str) -> dict:
    """Mark invoice as viewed via portal access."""
    invoice = db.query(ClientInvoice).filter(
        ClientInvoice.access_token == access_token
    ).first()
    if not invoice:
        return {"error": "Invalid access token"}

    if invoice.token_expiry and invoice.token_expiry < datetime.utcnow():
        return {"error": "Access token expired"}

    if invoice.status == ClientInvoiceStatus.SENT:
        invoice.status = ClientInvoiceStatus.VIEWED
        invoice.viewed_at = datetime.utcnow()
        db.flush()

    return {"success": True}


def get_stats(db: Session) -> dict:
    """Get client invoice statistics."""
    counts = (
        db.query(ClientInvoice.status, func.count(ClientInvoice.id))
        .group_by(ClientInvoice.status)
        .all()
    )

    stats = {s.value: 0 for s in ClientInvoiceStatus}
    for status, count in counts:
        key = status.value if hasattr(status, 'value') else status
        stats[key] = count

    stats["total"] = sum(stats.values())

    # Total outstanding
    outstanding = (
        db.query(func.coalesce(func.sum(ClientInvoice.balance), 0))
        .filter(ClientInvoice.status.in_([
            ClientInvoiceStatus.SENT, ClientInvoiceStatus.VIEWED,
            ClientInvoiceStatus.PARTIALLY_PAID, ClientInvoiceStatus.OVERDUE,
        ]))
        .scalar()
    )
    stats["total_outstanding"] = float(outstanding or 0)

    return stats
