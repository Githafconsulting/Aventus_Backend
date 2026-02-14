"""
Payroll Batch Routes - API endpoints for batch payroll management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.payroll import Payroll, PayrollStatus
from app.models.payroll_batch import PayrollBatch, BatchStatus
from app.models.contractor import Contractor
from app.services import payroll_batch_service
from app.schemas.payroll_batch import (
    AdjustPayrollRequest, FlagMismatchRequest, RequestInvoiceRequest,
    FinanceRejectRequest, MarkPaidRequest,
)

router = APIRouter(prefix="/api/v1/payroll-batches", tags=["Payroll Batches"])


def _format_batch_response(batch: PayrollBatch, include_payrolls: bool = False) -> dict:
    """Format a batch for API response."""
    # Count approved payrolls
    approved_count = sum(
        1 for p in batch.payrolls
        if p.status in (PayrollStatus.APPROVED, PayrollStatus.APPROVED_ADJUSTED, PayrollStatus.PAID)
    )

    data = {
        "id": batch.id,
        "batch_id": f"PB-{batch.id:04d}",
        "period": batch.period,
        "client_id": batch.client_id,
        "client_name": batch.client_name,
        "onboarding_route": batch.onboarding_route,
        "route_label": batch.route_label,
        "third_party_id": batch.third_party_id,
        "third_party_name": batch.third_party_name,
        "contractor_count": batch.contractor_count,
        "approved_count": approved_count,
        "total_net_salary": batch.total_net_salary,
        "total_payable": batch.total_payable,
        "currency": batch.currency,
        "status": batch.status.value if hasattr(batch.status, 'value') else batch.status,
        "tp_invoice_url": batch.tp_invoice_url,
        "tp_invoice_uploaded_at": batch.tp_invoice_uploaded_at.isoformat() if batch.tp_invoice_uploaded_at else None,
        "invoice_requested_at": batch.invoice_requested_at.isoformat() if batch.invoice_requested_at else None,
        "invoice_deadline": batch.invoice_deadline.isoformat() if batch.invoice_deadline else None,
        "finance_reviewed_by": batch.finance_reviewed_by,
        "finance_reviewed_at": batch.finance_reviewed_at.isoformat() if batch.finance_reviewed_at else None,
        "finance_notes": batch.finance_notes,
        "paid_at": batch.paid_at.isoformat() if batch.paid_at else None,
        "paid_by": batch.paid_by,
        "payment_reference": batch.payment_reference,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
    }

    if include_payrolls:
        data["payrolls"] = [_format_payroll_in_batch(p) for p in batch.payrolls]

    return data


def _format_payroll_in_batch(payroll: Payroll) -> dict:
    """Format a payroll record within a batch context."""
    contractor = payroll.contractor
    contractor_name = "Unknown"
    if contractor:
        parts = [contractor.first_name, contractor.surname]
        contractor_name = " ".join(p for p in parts if p) or "Unknown"

    return {
        "id": payroll.id,
        "contractor_id": payroll.contractor_id,
        "contractor_name": contractor_name,
        "period": payroll.period,
        "currency": payroll.currency,
        "rate_type": payroll.rate_type.value if payroll.rate_type and hasattr(payroll.rate_type, 'value') else payroll.rate_type,
        "gross_pay": payroll.gross_pay,
        "net_salary": payroll.net_salary,
        "total_accruals": payroll.total_accruals,
        "management_fee": payroll.management_fee,
        "invoice_total": payroll.invoice_total,
        "vat_rate": payroll.vat_rate,
        "vat_amount": payroll.vat_amount,
        "total_payable": payroll.total_payable,
        "expenses_reimbursement": payroll.expenses_reimbursement,
        "leave_deductibles": payroll.leave_deductibles,
        "status": payroll.status.value if hasattr(payroll.status, 'value') else payroll.status,
        "tp_draft_amount": payroll.tp_draft_amount,
        "reconciliation_notes": payroll.reconciliation_notes,
        "approved_at": payroll.approved_at.isoformat() if payroll.approved_at else None,
        "adjusted_at": payroll.adjusted_at.isoformat() if payroll.adjusted_at else None,
        "adjusted_by": payroll.adjusted_by,
    }


@router.get("/")
def list_batches(
    period: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List payroll batches with optional filters."""
    query = db.query(PayrollBatch).order_by(PayrollBatch.created_at.desc())

    if period:
        query = query.filter(PayrollBatch.period == period)
    if client_id:
        query = query.filter(PayrollBatch.client_id == client_id)
    if status:
        try:
            batch_status = BatchStatus(status)
            query = query.filter(PayrollBatch.status == batch_status)
        except ValueError:
            pass

    batches = query.all()
    return {
        "batches": [_format_batch_response(b) for b in batches],
        "count": len(batches),
    }


@router.get("/stats")
def get_batch_stats(
    period: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get batch counts by status."""
    return payroll_batch_service.get_batch_stats(db, period)


@router.get("/{batch_id}")
def get_batch_detail(batch_id: int, db: Session = Depends(get_db)):
    """Get batch detail with all payrolls."""
    batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _format_batch_response(batch, include_payrolls=True)


@router.put("/{batch_id}/approve-all")
def approve_all_payrolls_in_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """Approve all CALCULATED payrolls in a batch at once."""
    result = payroll_batch_service.approve_all_payrolls_in_batch(db, batch_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/payrolls/{payroll_id}/approve")
def approve_payroll_in_batch(
    batch_id: int,
    payroll_id: int,
    db: Session = Depends(get_db),
):
    """Approve a single payroll within a batch."""
    result = payroll_batch_service.approve_payroll_in_batch(db, batch_id, payroll_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/payrolls/{payroll_id}/adjust")
def adjust_payroll_in_batch(
    batch_id: int,
    payroll_id: int,
    request: AdjustPayrollRequest,
    db: Session = Depends(get_db),
):
    """Approve a payroll with adjustments (admin corrected a calculation error)."""
    adjustments = {
        "net_salary": request.net_salary,
        "total_accruals": request.total_accruals,
        "management_fee": request.management_fee,
    }
    # TODO: Get actual user ID from auth token
    result = payroll_batch_service.adjust_payroll_in_batch(
        db, batch_id, payroll_id, adjustments, request.notes, adjusted_by="system"
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/payrolls/{payroll_id}/flag-mismatch")
def flag_payroll_mismatch(
    batch_id: int,
    payroll_id: int,
    request: FlagMismatchRequest,
    db: Session = Depends(get_db),
):
    """Flag a payroll as having a 3rd party draft mismatch."""
    result = payroll_batch_service.flag_mismatch(
        db, batch_id, payroll_id, request.tp_draft_amount, request.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.post("/{batch_id}/request-invoice")
def request_invoice(
    batch_id: int,
    request: RequestInvoiceRequest,
    db: Session = Depends(get_db),
):
    """Request invoice from 3rd party or freelancer."""
    result = payroll_batch_service.request_invoice(db, batch_id, request.deadline_days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/finance-approve")
def finance_approve_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """Finance approves the received invoice."""
    # TODO: Get actual user ID from auth token
    result = payroll_batch_service.finance_approve(db, batch_id, reviewed_by="system")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/finance-reject")
def finance_reject_batch(
    batch_id: int,
    request: FinanceRejectRequest,
    db: Session = Depends(get_db),
):
    """Finance rejects the invoice and requests an update."""
    # TODO: Get actual user ID from auth token
    result = payroll_batch_service.finance_request_update(
        db, batch_id, request.notes, reviewed_by="system"
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.put("/{batch_id}/mark-paid")
def mark_batch_paid(
    batch_id: int,
    request: MarkPaidRequest,
    db: Session = Depends(get_db),
):
    """Mark batch as paid."""
    # TODO: Get actual user ID from auth token
    result = payroll_batch_service.mark_paid(db, batch_id, request.payment_reference, paid_by="system")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.post("/{batch_id}/generate-payslips")
def generate_payslips(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """Generate payslips for freelancer/WPS batch (no 3rd party invoice needed)."""
    result = payroll_batch_service.generate_payslips_for_batch(db, batch_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Generate actual payslip PDFs and send emails for each payroll
    payroll_ids = result.get("payroll_ids", [])
    generated = []
    for pid in payroll_ids:
        payroll = db.query(Payroll).filter(Payroll.id == pid).first()
        if not payroll:
            continue
        contractor = db.query(Contractor).filter(Contractor.id == payroll.contractor_id).first()
        if not contractor:
            continue

        try:
            from app.utils.payroll_pdf import generate_payslip_pdf
            payslip_buffer = generate_payslip_pdf(payroll=payroll, contractor=contractor)
            # Send payslip email
            parts = [contractor.first_name, contractor.surname]
            contractor_name = " ".join(p for p in parts if p) or "Unknown"
            from app.routes.payroll import _send_payslip_to_contractor
            _send_payslip_to_contractor(contractor, contractor_name, payroll, payslip_buffer.getvalue())
            generated.append(pid)
        except Exception as e:
            print(f"Error generating payslip for payroll {pid}: {e}")

    db.commit()
    return {"message": f"Payslips generated for {len(generated)} payrolls", "generated": generated}


# --- Public endpoints (no auth) for 3rd party / freelancer invoice upload ---

@router.post("/invoice-upload/{token}")
def upload_invoice(
    token: str,
    invoice_url: str = Query(..., description="URL of the uploaded invoice file"),
    db: Session = Depends(get_db),
):
    """Public endpoint: 3rd party or freelancer uploads their invoice."""
    result = payroll_batch_service.receive_invoice(db, token, invoice_url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.get("/invoice-upload/{token}")
def get_upload_info(token: str, db: Session = Depends(get_db)):
    """Public endpoint: Get batch info for the upload page."""
    batch = db.query(PayrollBatch).filter(
        PayrollBatch.tp_invoice_upload_token == token
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Invalid or expired upload link")

    if batch.tp_invoice_token_expiry and batch.tp_invoice_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Upload link has expired")

    return {
        "batch_id": batch.id,
        "period": batch.period,
        "client_name": batch.client_name,
        "route_label": batch.route_label,
        "third_party_name": batch.third_party_name,
        "contractor_count": batch.contractor_count,
        "total_payable": batch.total_payable,
        "currency": batch.currency,
        "status": batch.status.value,
        "invoice_deadline": batch.invoice_deadline.isoformat() if batch.invoice_deadline else None,
        "already_uploaded": batch.tp_invoice_url is not None,
    }
