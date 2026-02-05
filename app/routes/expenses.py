from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime

from app.database import get_db
from app.models.expense import Expense, ExpenseStatus
from app.models.contractor import Contractor
from app.models.user import UserRole
from app.utils.auth import get_current_active_user, require_role
from app.services import expense_service

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])


def _format_expense_response(expense: Expense, contractor: Optional[Contractor] = None) -> dict:
    contractor_name = None
    if contractor:
        contractor_name = f"{contractor.first_name} {contractor.surname}"
    return {
        "id": expense.id,
        "contractor_id": expense.contractor_id,
        "contractor_name": contractor_name,
        "date": str(expense.date),
        "month": expense.month,
        "year": expense.year,
        "month_number": expense.month_number,
        "category": expense.category.value if hasattr(expense.category, 'value') else expense.category,
        "description": expense.description,
        "amount": expense.amount,
        "currency": expense.currency,
        "receipt_url": expense.receipt_url,
        "status": expense.status.value if hasattr(expense.status, 'value') else expense.status,
        "rejection_reason": expense.rejection_reason,
        "submitted_at": expense.submitted_at,
        "reviewed_at": expense.reviewed_at,
        "reviewed_by": expense.reviewed_by,
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
    }


@router.post("/")
async def create_expense(
    date: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    receipt: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit a new expense. Contractors submit for themselves."""
    # Determine contractor_id from user
    contractor_id = current_user.contractor_id
    if not contractor_id:
        raise HTTPException(status_code=400, detail="No contractor profile linked to this user")

    # Verify contractor exists
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    # Derive currency from contractor profile (CDS form data > contractor.currency > route-based default)
    cds = contractor.cds_form_data or {}
    currency = cds.get("currency") or contractor.currency or "AED"
    # Fallback based on onboarding route if currency is still default
    if currency == "AED" and contractor.onboarding_route:
        route = contractor.onboarding_route
        route_val = route.value if hasattr(route, 'value') else str(route)
        if route_val in ("saudi",):
            currency = "SAR"

    # Parse the date
    try:
        expense_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    expense = await expense_service.create_expense(
        db=db,
        contractor_id=contractor_id,
        date=expense_date,
        category=category,
        description=description,
        amount=amount,
        currency=currency,
        receipt_file=receipt,
    )

    return _format_expense_response(expense, contractor)


@router.get("/")
def list_expenses(
    month: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    contractor_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List expenses.
    - Contractors see only their own expenses.
    - Admin/Superadmin see all (can filter by contractor_id).
    """
    is_admin = current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]

    if is_admin:
        filter_contractor_id = contractor_id
    else:
        filter_contractor_id = current_user.contractor_id
        if not filter_contractor_id:
            return {"expenses": [], "total": 0, "total_amount": 0, "approved_amount": 0, "pending_amount": 0, "rejected_amount": 0}

    expenses = expense_service.get_expenses(
        db=db,
        contractor_id=filter_contractor_id,
        month=month,
        year=year,
        status=status,
    )

    # Apply category filter if provided
    if category:
        expenses = [e for e in expenses if (e.category.value if hasattr(e.category, 'value') else e.category) == category]

    # Batch load contractors for name display
    contractor_ids = {e.contractor_id for e in expenses}
    contractors_map = {}
    if contractor_ids:
        contractors = db.query(Contractor).filter(Contractor.id.in_(contractor_ids)).all()
        contractors_map = {c.id: c for c in contractors}

    result = []
    total_amount = 0
    approved_amount = 0
    pending_amount = 0
    rejected_amount = 0

    for e in expenses:
        contractor = contractors_map.get(e.contractor_id)
        result.append(_format_expense_response(e, contractor))

        total_amount += e.amount
        status_val = e.status.value if hasattr(e.status, 'value') else e.status
        if status_val == "approved":
            approved_amount += e.amount
        elif status_val == "pending":
            pending_amount += e.amount
        elif status_val == "rejected":
            rejected_amount += e.amount

    return {
        "expenses": result,
        "total": len(result),
        "total_amount": round(total_amount, 2),
        "approved_amount": round(approved_amount, 2),
        "pending_amount": round(pending_amount, 2),
        "rejected_amount": round(rejected_amount, 2),
    }


@router.get("/summary")
def get_expenses_summary(
    month: Optional[str] = None,
    year: Optional[int] = None,
    current_user=Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Aggregated expense stats for admin dashboard."""
    query = db.query(Expense)
    if month:
        query = query.filter(Expense.month == month)
    if year:
        query = query.filter(Expense.year == year)

    expenses = query.all()

    pending_count = sum(1 for e in expenses if e.status == ExpenseStatus.PENDING)
    pending_amount = sum(e.amount for e in expenses if e.status == ExpenseStatus.PENDING)
    approved_count = sum(1 for e in expenses if e.status == ExpenseStatus.APPROVED)
    approved_amount = sum(e.amount for e in expenses if e.status == ExpenseStatus.APPROVED)
    rejected_count = sum(1 for e in expenses if e.status == ExpenseStatus.REJECTED)
    rejected_amount = sum(e.amount for e in expenses if e.status == ExpenseStatus.REJECTED)

    return {
        "pending_count": pending_count,
        "pending_amount": round(pending_amount, 2),
        "approved_count": approved_count,
        "approved_amount": round(approved_amount, 2),
        "rejected_count": rejected_count,
        "rejected_amount": round(rejected_amount, 2),
        "total_count": len(expenses),
        "total_amount": round(sum(e.amount for e in expenses), 2),
    }


@router.get("/{expense_id}")
def get_expense(
    expense_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a single expense. Owner or Admin can view."""
    expense = expense_service.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    is_admin = current_user.role in [UserRole.SUPERADMIN, UserRole.ADMIN]
    is_owner = current_user.contractor_id == expense.contractor_id

    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")

    contractor = db.query(Contractor).filter(Contractor.id == expense.contractor_id).first()
    return _format_expense_response(expense, contractor)


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a pending expense. Only owner can delete, and only if status is PENDING."""
    expense = expense_service.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    is_owner = current_user.contractor_id == expense.contractor_id
    if not is_owner:
        raise HTTPException(status_code=403, detail="Only the expense owner can delete it")

    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending expenses can be deleted")

    expense_service.delete_expense(db, expense_id)
    return {"message": "Expense deleted successfully"}


@router.put("/{expense_id}/approve")
def approve_expense(
    expense_id: int,
    current_user=Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Approve an expense. Admin/Superadmin only."""
    expense = expense_service.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending expenses can be approved")

    updated = expense_service.approve_expense(db, expense_id, current_user.id)
    contractor = db.query(Contractor).filter(Contractor.id == updated.contractor_id).first()
    return _format_expense_response(updated, contractor)


@router.put("/{expense_id}/reject")
def reject_expense(
    expense_id: int,
    reason: str = Form(""),
    current_user=Depends(require_role([UserRole.SUPERADMIN, UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    """Reject an expense with a reason. Admin/Superadmin only."""
    expense = expense_service.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending expenses can be rejected")

    if not reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    updated = expense_service.reject_expense(db, expense_id, current_user.id, reason)
    contractor = db.query(Contractor).filter(Contractor.id == updated.contractor_id).first()
    return _format_expense_response(updated, contractor)
