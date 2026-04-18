"""
Expenses API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime as dt

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.models import Expense, Business
from app.schemas import ExpenseCreate, ExpenseResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("")
async def list_expenses(
    category: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all expenses for current branch"""
    expense_service = ExpenseService(db)
    expenses = expense_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        category,
        start_date,
        end_date,
    )

    # Build response with additional fields
    result = []
    for exp in expenses:
        result.append(
            {
                "id": exp.id,
                "expense_number": exp.expense_number,
                "expense_date": exp.expense_date.isoformat()
                if exp.expense_date
                else None,
                "category": exp.category,
                "description": exp.description,
                "sub_total": float(exp.sub_total) if exp.sub_total else 0.0,
                "vat_amount": float(exp.vat_amount) if exp.vat_amount else 0.0,
                "amount": float(exp.amount) if exp.amount else 0.0,
                "vendor_id": exp.vendor_id,
                "vendor_name": exp.vendor.name if exp.vendor else None,
                "paid_from_account_id": exp.paid_from_account_id,
                "paid_from_account_name": exp.paid_from_account.name
                if exp.paid_from_account
                else None,
                "expense_account_id": exp.expense_account_id,
                "expense_account_name": exp.expense_account.name
                if exp.expense_account
                else None,
                "branch_id": exp.branch_id,
                "business_id": exp.business_id,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
            }
        )

    return result


@router.post(
    "",
    response_model=ExpenseResponse,
    dependencies=[Depends(PermissionChecker(["expenses:create"]))],
)
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new expense"""
    expense_service = ExpenseService(db)
    try:
        expense = expense_service.create(
            expense_data, current_user.business_id, current_user.selected_branch.id
        )
        db.commit()
        return expense
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
async def list_expense_categories(
    db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """List expense categories"""
    expense_service = ExpenseService(db)
    categories = expense_service.get_categories(current_user.business_id)

    # Add common categories if empty
    if not categories:
        categories = [
            "Office Supplies",
            "Utilities",
            "Rent",
            "Salaries",
            "Marketing",
            "Travel",
            "Insurance",
            "Maintenance",
            "Professional Services",
            "Miscellaneous",
        ]

    return {"categories": categories}


@router.get("/summary")
async def get_expense_summary(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Get expense summary by category"""
    expense_service = ExpenseService(db)
    return expense_service.get_expense_summary(
        current_user.business_id, current_user.selected_branch.id, start_date, end_date
    )


@router.get("/next-number")
async def get_next_expense_number(
    db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """Get next expense number"""
    expense_service = ExpenseService(db)
    return {"next_number": expense_service.get_next_number(current_user.business_id)}


@router.get("/export/pdf")
def export_expenses_pdf(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export expenses to PDF"""
    try:
        from weasyprint import HTML
        from fastapi.responses import Response as FastAPIResponse
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF export not available - weasyprint not installed",
        )

    query = db.query(Expense).filter(
        Expense.business_id == current_user.business_id,
        Expense.branch_id == current_user.selected_branch.id,
    )

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(
            Expense.expense_date >= dt.strptime(start_date, "%Y-%m-%d").date()
        )
    if end_date:
        query = query.filter(
            Expense.expense_date <= dt.strptime(end_date, "%Y-%m-%d").date()
        )

    expenses = query.order_by(Expense.expense_date.desc()).all()
    business = (
        db.query(Business).filter(Business.id == current_user.business_id).first()
    )

    html_content = f"""
    <html><head><style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #2563eb; color: white; }}
    .total {{ font-weight: bold; text-align: right; padding: 10px; }}
    </style></head><body>
    <h1>Expenses Report</h1>
    <p>Business: {business.name if business else "N/A"}</p>
    <p>Generated: {date.today().isoformat()}</p>
    <table>
        <tr><th>Date</th><th>Number</th><th>Category</th><th>Description</th><th>Amount</th></tr>
    """

    total = 0
    for exp in expenses:
        html_content += f"<tr><td>{exp.expense_date}</td><td>{exp.expense_number}</td><td>{exp.category}</td><td>{exp.description or ''}</td><td>{exp.amount}</td></tr>"
        total += float(exp.amount) if exp.amount else 0

    html_content += f"</table><div class='total'>Total: {total:.2f}</div></body></html>"

    pdf = HTML(string=html_content).write_pdf()

    return FastAPIResponse(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=expenses_report_{date.today()}.pdf"
        },
    )


@router.get("/{expense_id}")
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Get expense by ID"""
    expense_service = ExpenseService(db)
    expense = expense_service.get_by_id(
        expense_id, current_user.business_id, current_user.selected_branch.id
    )

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {
        "id": expense.id,
        "expense_number": expense.expense_number,
        "expense_date": expense.expense_date.isoformat()
        if expense.expense_date
        else None,
        "category": expense.category,
        "description": expense.description,
        "sub_total": float(expense.sub_total) if expense.sub_total else 0.0,
        "vat_amount": float(expense.vat_amount) if expense.vat_amount else 0.0,
        "amount": float(expense.amount) if expense.amount else 0.0,
        "vendor_id": expense.vendor_id,
        "vendor_name": expense.vendor.name if expense.vendor else None,
        "paid_from_account_id": expense.paid_from_account_id,
        "paid_from_account_name": expense.paid_from_account.name
        if expense.paid_from_account
        else None,
        "expense_account_id": expense.expense_account_id,
        "expense_account_name": expense.expense_account.name
        if expense.expense_account
        else None,
        "branch_id": expense.branch_id,
        "business_id": expense.business_id,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
    }


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    dependencies=[Depends(PermissionChecker(["expenses:edit"]))],
)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Update an expense"""
    expense_service = ExpenseService(db)
    try:
        expense = expense_service.update(
            expense_id,
            current_user.business_id,
            current_user.selected_branch.id,
            expense_data,
        )
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        db.commit()
        return expense
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{expense_id}", dependencies=[Depends(PermissionChecker(["expenses:delete"]))]
)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Delete an expense"""
    expense_service = ExpenseService(db)
    if not expense_service.delete(
        expense_id, current_user.business_id, current_user.selected_branch.id
    ):
        raise HTTPException(status_code=404, detail="Expense not found")
    db.commit()
    return {"message": "Expense deleted successfully"}
