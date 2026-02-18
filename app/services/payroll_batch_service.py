"""
Payroll Batch Service - Business logic for batch payroll processing.
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.payroll import Payroll, PayrollStatus
from app.models.payroll_batch import PayrollBatch, BatchStatus
from app.models.contractor import Contractor, OnboardingRoute
from app.models.client import Client
from app.models.third_party import ThirdParty


# Routes that go through 3rd party invoice flow
THIRD_PARTY_ROUTES = {OnboardingRoute.UAE.value, OnboardingRoute.SAUDI.value}
# Routes that end at payslip generation (no 3rd party invoice)
DIRECT_ROUTES = {OnboardingRoute.FREELANCER.value, OnboardingRoute.WPS.value}


def _get_route_label(route: str, third_party_name: Optional[str] = None) -> str:
    """Generate a human-readable route label."""
    labels = {
        OnboardingRoute.UAE.value: f"UAE - {third_party_name}" if third_party_name else "UAE",
        OnboardingRoute.SAUDI.value: f"Saudi - {third_party_name}" if third_party_name else "Saudi",
        OnboardingRoute.FREELANCER.value: "Freelancer",
        OnboardingRoute.WPS.value: "WPS",
        OnboardingRoute.OFFSHORE.value: "Offshore",
    }
    return labels.get(route, route)


def create_or_get_batch(
    db: Session,
    period: str,
    client_id: str,
    client_name: str,
    route: str,
    third_party_id: Optional[str] = None,
    third_party_name: Optional[str] = None,
    currency: str = "AED",
) -> PayrollBatch:
    """Find an existing batch or create a new one for the given grouping keys."""
    # Look for existing batch with same grouping
    query = db.query(PayrollBatch).filter(
        PayrollBatch.period == period,
        PayrollBatch.client_id == client_id,
        PayrollBatch.onboarding_route == route,
    )
    if third_party_id:
        query = query.filter(PayrollBatch.third_party_id == third_party_id)
    else:
        query = query.filter(PayrollBatch.third_party_id.is_(None))

    batch = query.first()
    if batch:
        return batch

    # Create new batch
    batch = PayrollBatch(
        period=period,
        client_id=client_id,
        client_name=client_name,
        onboarding_route=route,
        route_label=_get_route_label(route, third_party_name),
        third_party_id=third_party_id,
        third_party_name=third_party_name,
        currency=currency,
        status=BatchStatus.AWAITING_APPROVAL,
        tp_invoice_upload_token=str(uuid.uuid4()),
        tp_invoice_token_expiry=datetime.utcnow() + timedelta(days=90),
    )
    db.add(batch)
    db.flush()
    return batch


def assign_payroll_to_batch(db: Session, payroll_id: int) -> Optional[int]:
    """
    Auto-assign a payroll record to a batch based on its contractor's client/route.
    Returns batch_id if assigned, None if unable.
    """
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        return None

    contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
    if not contractor or not contractor.client_id or not contractor.onboarding_route:
        return None

    route_value = contractor.onboarding_route.value if hasattr(contractor.onboarding_route, 'value') else str(contractor.onboarding_route)

    # Get client name
    client = db.query(Client).filter(Client.id == contractor.client_id).first()
    client_name = client.company_name if client else (payroll.client_name or "Unknown")

    # Get third party info if applicable
    third_party_id = None
    third_party_name = None
    if route_value in THIRD_PARTY_ROUTES and contractor.third_party_id:
        third_party = db.query(ThirdParty).filter(ThirdParty.id == contractor.third_party_id).first()
        if third_party:
            third_party_id = third_party.id
            third_party_name = third_party.company_name

    batch = create_or_get_batch(
        db=db,
        period=payroll.period,
        client_id=contractor.client_id,
        client_name=client_name,
        route=route_value,
        third_party_id=third_party_id,
        third_party_name=third_party_name,
        currency=payroll.currency or "AED",
    )

    payroll.batch_id = batch.id
    db.flush()  # Flush so the payroll is included in aggregate query
    _recalculate_batch_aggregates(db, batch)
    db.flush()
    return batch.id


def _recalculate_batch_aggregates(db: Session, batch: PayrollBatch):
    """Recalculate batch totals from its payrolls."""
    payrolls = db.query(Payroll).filter(Payroll.batch_id == batch.id).all()
    batch.contractor_count = len(payrolls)
    batch.total_net_salary = sum(p.net_salary or 0 for p in payrolls)
    batch.total_payable = sum(p.total_payable or 0 for p in payrolls)


def approve_payroll_in_batch(db: Session, batch_id: int, payroll_id: int) -> dict:
    """
    Approve a single payroll within a batch.
    Updates batch status based on how many payrolls are now approved.
    """
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    payroll = db.query(Payroll).filter(
        Payroll.id == payroll_id, Payroll.batch_id == batch_id
    ).first()
    if not payroll:
        return {"error": "Payroll not found in this batch"}

    if payroll.status != PayrollStatus.CALCULATED:
        return {"error": f"Payroll must be in CALCULATED status, currently {payroll.status.value}"}

    payroll.status = PayrollStatus.APPROVED
    payroll.approved_at = datetime.utcnow()

    _check_and_advance_batch(db, batch)
    db.flush()
    return {"success": True, "batch_status": batch.status.value}


def approve_all_payrolls_in_batch(db: Session, batch_id: int) -> dict:
    """
    Approve all CALCULATED payrolls in a batch at once.
    Returns count of approved payrolls and resulting batch status.
    """
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).with_for_update().first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status not in (BatchStatus.AWAITING_APPROVAL, BatchStatus.PARTIALLY_APPROVED):
        return {"error": f"Batch must be in awaiting_approval or partially_approved status, currently {batch.status.value}"}

    payrolls = db.query(Payroll).filter(
        Payroll.batch_id == batch_id,
        Payroll.status == PayrollStatus.CALCULATED,
    ).with_for_update().all()

    if not payrolls:
        return {"error": "No payrolls in CALCULATED status to approve"}

    now = datetime.utcnow()
    for p in payrolls:
        p.status = PayrollStatus.APPROVED
        p.approved_at = now

    _check_and_advance_batch(db, batch)
    db.flush()
    return {
        "success": True,
        "approved_count": len(payrolls),
        "batch_status": batch.status.value,
    }


def adjust_payroll_in_batch(
    db: Session, batch_id: int, payroll_id: int,
    adjustments: dict, notes: str, adjusted_by: str
) -> dict:
    """
    Approve a payroll with adjustments (admin corrected system calc error).
    """
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    payroll = db.query(Payroll).filter(
        Payroll.id == payroll_id, Payroll.batch_id == batch_id
    ).first()
    if not payroll:
        return {"error": "Payroll not found in this batch"}

    # Apply adjustments
    if "net_salary" in adjustments and adjustments["net_salary"] is not None:
        payroll.net_salary = adjustments["net_salary"]
    if "total_accruals" in adjustments and adjustments["total_accruals"] is not None:
        payroll.total_accruals = adjustments["total_accruals"]
    if "management_fee" in adjustments and adjustments["management_fee"] is not None:
        payroll.management_fee = adjustments["management_fee"]

    # Recalculate invoice totals
    payroll.invoice_total = (payroll.net_salary or 0) + (payroll.total_accruals or 0) + (payroll.management_fee or 0)
    payroll.vat_amount = payroll.invoice_total * (payroll.vat_rate or 0)
    payroll.total_payable = payroll.invoice_total + payroll.vat_amount

    payroll.status = PayrollStatus.APPROVED_ADJUSTED
    payroll.reconciliation_notes = notes
    payroll.adjusted_by = adjusted_by
    payroll.adjusted_at = datetime.utcnow()
    payroll.approved_at = datetime.utcnow()

    _recalculate_batch_aggregates(db, batch)
    _check_and_advance_batch(db, batch)
    db.flush()
    return {"success": True, "batch_status": batch.status.value}


def flag_mismatch(
    db: Session, batch_id: int, payroll_id: int,
    tp_draft_amount: float, notes: str
) -> dict:
    """Mark a payroll as having a 3rd party draft mismatch."""
    payroll = db.query(Payroll).filter(
        Payroll.id == payroll_id, Payroll.batch_id == batch_id
    ).first()
    if not payroll:
        return {"error": "Payroll not found in this batch"}

    payroll.status = PayrollStatus.MISMATCH_3RD_PARTY
    payroll.tp_draft_amount = tp_draft_amount
    payroll.reconciliation_notes = notes
    db.flush()
    return {"success": True}


def _check_and_advance_batch(db: Session, batch: PayrollBatch):
    """Auto-advance batch status if all payrolls are approved/adjusted."""
    payrolls = db.query(Payroll).filter(Payroll.batch_id == batch.id).all()
    if not payrolls:
        return

    total = len(payrolls)
    approved_count = sum(
        1 for p in payrolls
        if p.status in (PayrollStatus.APPROVED, PayrollStatus.APPROVED_ADJUSTED)
    )
    mismatch_count = sum(1 for p in payrolls if p.status == PayrollStatus.MISMATCH_3RD_PARTY)

    if approved_count == total:
        batch.status = BatchStatus.SUBMIT_FOR_INVOICE
    elif approved_count > 0 or mismatch_count > 0:
        batch.status = BatchStatus.PARTIALLY_APPROVED
    else:
        batch.status = BatchStatus.AWAITING_APPROVAL


def check_and_advance_batch(db: Session, batch_id: int):
    """Public wrapper: check if a batch should advance after a payroll status change."""
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if batch:
        _check_and_advance_batch(db, batch)


def request_invoice(db: Session, batch_id: int, deadline_days: int = 7) -> dict:
    """
    Mark batch as invoice requested and set deadline.
    Email sending is handled by the route layer.
    """
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status != BatchStatus.SUBMIT_FOR_INVOICE:
        return {"error": f"Batch must be in SUBMIT_FOR_INVOICE status, currently {batch.status.value}"}

    batch.status = BatchStatus.INVOICE_REQUESTED
    batch.invoice_requested_at = datetime.utcnow()
    batch.invoice_deadline = datetime.utcnow() + timedelta(days=deadline_days)

    # Regenerate upload token
    batch.tp_invoice_upload_token = str(uuid.uuid4())
    batch.tp_invoice_token_expiry = batch.invoice_deadline + timedelta(days=7)

    db.flush()
    return {
        "success": True,
        "upload_token": batch.tp_invoice_upload_token,
        "deadline": batch.invoice_deadline.isoformat(),
    }


def receive_invoice(db: Session, upload_token: str, file_url: str) -> dict:
    """Process an uploaded invoice from 3rd party or freelancer."""
    batch = db.query(PayrollBatch).filter(
        PayrollBatch.tp_invoice_upload_token == upload_token
    ).first()
    if not batch:
        return {"error": "Invalid upload token"}

    if batch.tp_invoice_token_expiry and batch.tp_invoice_token_expiry < datetime.utcnow():
        return {"error": "Upload token has expired"}

    # Only allow upload when invoice has been requested or update was requested
    allowed_statuses = {BatchStatus.INVOICE_REQUESTED, BatchStatus.INVOICE_UPDATE_REQUESTED}
    if batch.status not in allowed_statuses:
        return {"error": f"Invoice upload not expected in status {batch.status.value}"}

    batch.tp_invoice_url = file_url
    batch.tp_invoice_uploaded_at = datetime.utcnow()
    batch.status = BatchStatus.INVOICE_RECEIVED
    db.flush()
    return {"success": True, "batch_id": batch.id}


def finance_approve(db: Session, batch_id: int, reviewed_by: str) -> dict:
    """Finance approves the received invoice - mark ready for payment."""
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status != BatchStatus.INVOICE_RECEIVED:
        return {"error": f"Batch must be in INVOICE_RECEIVED status, currently {batch.status.value}"}

    batch.status = BatchStatus.READY_FOR_PAYMENT
    batch.finance_reviewed_by = reviewed_by
    batch.finance_reviewed_at = datetime.utcnow()
    db.flush()
    return {"success": True}


def finance_request_update(db: Session, batch_id: int, notes: str, reviewed_by: str) -> dict:
    """Finance found discrepancy - request corrected invoice."""
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status != BatchStatus.INVOICE_RECEIVED:
        return {"error": f"Batch must be in INVOICE_RECEIVED status, currently {batch.status.value}"}

    batch.status = BatchStatus.INVOICE_UPDATE_REQUESTED
    batch.finance_notes = notes
    batch.finance_reviewed_by = reviewed_by
    batch.finance_reviewed_at = datetime.utcnow()

    # Regenerate upload token for re-upload
    batch.tp_invoice_upload_token = str(uuid.uuid4())
    batch.tp_invoice_token_expiry = datetime.utcnow() + timedelta(days=14)

    db.flush()
    return {"success": True, "upload_token": batch.tp_invoice_upload_token}


def mark_paid(db: Session, batch_id: int, payment_ref: str, paid_by: str) -> dict:
    """Mark batch as paid and update all payrolls."""
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status != BatchStatus.READY_FOR_PAYMENT:
        return {"error": f"Batch must be in READY_FOR_PAYMENT status, currently {batch.status.value}"}

    batch.status = BatchStatus.PAID
    batch.paid_at = datetime.utcnow()
    batch.paid_by = paid_by
    batch.payment_reference = payment_ref

    # Mark all payrolls as paid
    payrolls = db.query(Payroll).filter(Payroll.batch_id == batch_id).all()
    for p in payrolls:
        if p.status in (PayrollStatus.APPROVED, PayrollStatus.APPROVED_ADJUSTED):
            p.status = PayrollStatus.PAID
            p.paid_at = datetime.utcnow()

    db.flush()
    return {"success": True}


def generate_payslips_for_batch(db: Session, batch_id: int) -> dict:
    """
    For freelancer/WPS batches, generate payslips directly (no 3rd party invoice).
    The actual PDF generation + email sending is done by the route layer.
    """
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        return {"error": "Batch not found"}

    if batch.status != BatchStatus.SUBMIT_FOR_INVOICE:
        return {"error": f"Batch must be in SUBMIT_FOR_INVOICE status, currently {batch.status.value}"}

    if batch.onboarding_route not in DIRECT_ROUTES:
        return {"error": "Payslip generation is only for Freelancer/WPS routes"}

    batch.status = BatchStatus.PAYSLIPS_GENERATED

    # Mark all payrolls as paid (for direct routes, approval = paid)
    payrolls = db.query(Payroll).filter(Payroll.batch_id == batch_id).all()
    for p in payrolls:
        if p.status in (PayrollStatus.APPROVED, PayrollStatus.APPROVED_ADJUSTED):
            p.status = PayrollStatus.PAID
            p.paid_at = datetime.utcnow()

    db.flush()
    return {"success": True, "payroll_ids": [p.id for p in payrolls]}


def get_batch_stats(db: Session, period: Optional[str] = None) -> dict:
    """Get batch counts by status."""
    query = db.query(PayrollBatch.status, func.count(PayrollBatch.id))
    if period:
        query = query.filter(PayrollBatch.period == period)
    counts = query.group_by(PayrollBatch.status).all()

    stats = {s.value: 0 for s in BatchStatus}
    for status, count in counts:
        stats[status.value if hasattr(status, 'value') else status] = count

    stats["total"] = sum(stats.values())
    return stats
