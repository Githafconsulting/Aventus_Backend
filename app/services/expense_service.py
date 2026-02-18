from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import UploadFile

from app.models.expense import Expense, ExpenseStatus, ExpenseCategory
from app.models.contractor import Contractor
from app.utils.storage import storage


async def create_expense(
    db: Session,
    contractor_id: str,
    date: datetime,
    category: str,
    description: str,
    amount: float,
    receipt_file: UploadFile,
    currency: str = "AED",
) -> Expense:
    # Parse month from date
    expense_date = date if hasattr(date, 'year') else datetime.strptime(str(date), "%Y-%m-%d")
    month_str = expense_date.strftime("%B %Y")

    receipt_url = await storage.upload_document(
        file=receipt_file,
        contractor_id=contractor_id,
        document_type="expense_receipt",
    )

    expense = Expense(
        contractor_id=contractor_id,
        date=expense_date,
        month=month_str,
        category=category,
        description=description,
        amount=amount,
        currency=currency,
        receipt_url=receipt_url,
        status=ExpenseStatus.PENDING,
        submitted_at=datetime.utcnow(),
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expenses(
    db: Session,
    contractor_id: Optional[str] = None,
    month: Optional[str] = None,
    year: Optional[int] = None,
    month_number: Optional[int] = None,
    status: Optional[str] = None,
) -> List[Expense]:
    query = db.query(Expense)

    if contractor_id:
        query = query.filter(Expense.contractor_id == contractor_id)
    if month:
        query = query.filter(Expense.month == month)
    if year:
        query = query.filter(Expense.year == year)
    if month_number:
        query = query.filter(Expense.month_number == month_number)
    if status:
        try:
            status_enum = ExpenseStatus(status)
            query = query.filter(Expense.status == status_enum)
        except ValueError:
            pass

    return query.order_by(Expense.submitted_at.desc()).all()


def get_expense_by_id(db: Session, expense_id: int) -> Optional[Expense]:
    return db.query(Expense).filter(Expense.id == expense_id).first()


def approve_expense(db: Session, expense_id: int, reviewer_id: str) -> Optional[Expense]:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None

    expense.status = ExpenseStatus.APPROVED
    expense.reviewed_at = datetime.utcnow()
    expense.reviewed_by = reviewer_id
    expense.rejection_reason = None

    db.commit()
    db.refresh(expense)
    return expense


def reject_expense(db: Session, expense_id: int, reviewer_id: str, reason: str) -> Optional[Expense]:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None

    expense.status = ExpenseStatus.REJECTED
    expense.reviewed_at = datetime.utcnow()
    expense.reviewed_by = reviewer_id
    expense.rejection_reason = reason

    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return False

    if expense.status != ExpenseStatus.PENDING:
        return False

    db.delete(expense)
    db.commit()
    return True


def get_approved_expenses_total(
    db: Session, contractor_id: str, month_number: int, year: int
) -> float:
    result = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.contractor_id == contractor_id,
            Expense.month_number == month_number,
            Expense.year == year,
            Expense.status == ExpenseStatus.APPROVED,
        )
        .scalar()
    )
    return float(result)
