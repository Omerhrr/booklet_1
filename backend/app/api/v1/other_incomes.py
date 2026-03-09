"""
Other Income API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import OtherIncomeCreate, OtherIncomeResponse
from app.services.other_income_service import OtherIncomeService

router = APIRouter(prefix="/other-incomes", tags=["Other Income"])


@router.get("")
async def list_other_incomes(
    category: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all other incomes for current branch"""
    income_service = OtherIncomeService(db)
    incomes = income_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        category,
        start_date,
        end_date
    )
    
    # Build response with additional fields
    result = []
    for inc in incomes:
        result.append({
            'id': inc.id,
            'income_number': inc.income_number,
            'income_date': inc.income_date.isoformat() if inc.income_date else None,
            'category': inc.category,
            'description': inc.description,
            'sub_total': float(inc.sub_total) if inc.sub_total else 0.0,
            'vat_amount': float(inc.vat_amount) if inc.vat_amount else 0.0,
            'amount': float(inc.amount) if inc.amount else 0.0,
            'customer_id': inc.customer_id,
            'customer_name': inc.customer.name if inc.customer else None,
            'received_in_account_id': inc.received_in_account_id,
            'received_in_account_name': inc.received_in_account.name if inc.received_in_account else None,
            'income_account_id': inc.income_account_id,
            'income_account_name': inc.income_account.name if inc.income_account else None,
            'branch_id': inc.branch_id,
            'business_id': inc.business_id,
            'created_at': inc.created_at.isoformat() if inc.created_at else None
        })
    
    return result


@router.post("", response_model=OtherIncomeResponse, dependencies=[Depends(PermissionChecker(["other_income:create"]))])
async def create_other_income(
    income_data: OtherIncomeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new other income"""
    income_service = OtherIncomeService(db)
    try:
        income = income_service.create(
            income_data,
            current_user.business_id,
            current_user.selected_branch.id
        )
        db.commit()
        return income
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
async def list_income_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List income categories"""
    income_service = OtherIncomeService(db)
    categories = income_service.get_categories(current_user.business_id)
    
    # Add common categories if empty
    if not categories:
        categories = [
            "Interest Income",
            "Rental Income",
            "Dividend Income",
            "Commission Income",
            "Service Fees",
            "Consulting Fees",
            "Refunds Received",
            "Asset Sale",
            "Miscellaneous Income"
        ]
    
    return {"categories": categories}


@router.get("/summary")
async def get_income_summary(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get income summary by category"""
    income_service = OtherIncomeService(db)
    return income_service.get_income_summary(
        current_user.business_id,
        current_user.selected_branch.id,
        start_date,
        end_date
    )


@router.get("/next-number")
async def get_next_income_number(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get next income number"""
    income_service = OtherIncomeService(db)
    return {"next_number": income_service.get_next_number(current_user.business_id)}


@router.get("/{income_id}")
async def get_other_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get other income by ID"""
    income_service = OtherIncomeService(db)
    income = income_service.get_by_id(
        income_id,
        current_user.business_id,
        current_user.selected_branch.id
    )
    
    if not income:
        raise HTTPException(status_code=404, detail="Other income not found")
    
    return {
        'id': income.id,
        'income_number': income.income_number,
        'income_date': income.income_date.isoformat() if income.income_date else None,
        'category': income.category,
        'description': income.description,
        'sub_total': float(income.sub_total) if income.sub_total else 0.0,
        'vat_amount': float(income.vat_amount) if income.vat_amount else 0.0,
        'amount': float(income.amount) if income.amount else 0.0,
        'customer_id': income.customer_id,
        'customer_name': income.customer.name if income.customer else None,
        'received_in_account_id': income.received_in_account_id,
        'received_in_account_name': income.received_in_account.name if income.received_in_account else None,
        'income_account_id': income.income_account_id,
        'income_account_name': income.income_account.name if income.income_account else None,
        'branch_id': income.branch_id,
        'business_id': income.business_id,
        'created_at': income.created_at.isoformat() if income.created_at else None
    }


@router.put("/{income_id}", response_model=OtherIncomeResponse, dependencies=[Depends(PermissionChecker(["other_income:edit"]))])
async def update_other_income(
    income_id: int,
    income_data: OtherIncomeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update an other income"""
    income_service = OtherIncomeService(db)
    try:
        income = income_service.update(
            income_id,
            current_user.business_id,
            current_user.selected_branch.id,
            income_data
        )
        if not income:
            raise HTTPException(status_code=404, detail="Other income not found")
        db.commit()
        return income
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{income_id}", dependencies=[Depends(PermissionChecker(["other_income:delete"]))])
async def delete_other_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an other income"""
    income_service = OtherIncomeService(db)
    if not income_service.delete(
        income_id,
        current_user.business_id,
        current_user.selected_branch.id
    ):
        raise HTTPException(status_code=404, detail="Other income not found")
    db.commit()
    return {"message": "Other income deleted successfully"}
