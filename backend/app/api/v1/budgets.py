"""
Budgets API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import BudgetCreate, BudgetResponse, BudgetItemCreate
from app.services.accounting_service import BudgetService, AccountService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("")
async def list_budgets(
    fiscal_year: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all budgets for current business"""
    budget_service = BudgetService(db)
    budgets = budget_service.get_by_business(current_user.business_id)
    
    # Filter by fiscal year if provided
    if fiscal_year:
        budgets = [b for b in budgets if b.fiscal_year == fiscal_year]
    
    # Build response
    result = []
    for budget in budgets:
        # Calculate total budgeted amount
        total_budgeted = sum(float(item.amount) for item in budget.items)
        
        result.append({
            'id': budget.id,
            'name': budget.name,
            'fiscal_year': budget.fiscal_year,
            'description': budget.description,
            'is_active': budget.is_active,
            'total_items': len(budget.items),
            'total_budgeted': total_budgeted,
            'business_id': budget.business_id,
            'created_at': budget.created_at.isoformat() if budget.created_at else None,
            'updated_at': budget.updated_at.isoformat() if budget.updated_at else None
        })
    
    return result


@router.post("", response_model=BudgetResponse, dependencies=[Depends(PermissionChecker(["budgets:create"]))])
async def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new budget"""
    budget_service = BudgetService(db)
    
    # Check if budget with same name and fiscal year exists
    existing = db.query(budget_service.get_by_business(current_user.business_id))
    for b in budget_service.get_by_business(current_user.business_id):
        if b.name == budget_data.name and b.fiscal_year == budget_data.fiscal_year:
            raise HTTPException(status_code=400, detail="Budget with this name and fiscal year already exists")
    
    try:
        budget = budget_service.create(budget_data, current_user.business_id)
        
        # Add budget items if provided
        for item in budget_data.items:
            budget_service.add_item(
                budget_id=budget.id,
                account_id=item.account_id,
                amount=item.amount,
                month=item.month
            )
        
        db.commit()
        return budget
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fiscal-years")
async def list_fiscal_years(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List fiscal years that have budgets"""
    budget_service = BudgetService(db)
    budgets = budget_service.get_by_business(current_user.business_id)
    
    years = sorted(list(set(b.fiscal_year for b in budgets)), reverse=True)
    
    # Add current year and next year if not present
    current_year = date.today().year
    if current_year not in years:
        years.insert(0, current_year)
    if current_year + 1 not in years:
        years.insert(0, current_year + 1)
    
    return {"fiscal_years": years}


@router.get("/available-accounts")
async def get_available_accounts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get accounts available for budgeting (Revenue and Expense accounts)"""
    account_service = AccountService(db)
    
    revenue_accounts = account_service.get_by_type(current_user.business_id, "Revenue")
    expense_accounts = account_service.get_by_type(current_user.business_id, "Expense")
    
    result = []
    for acc in revenue_accounts:
        result.append({
            'id': acc.id,
            'code': acc.code,
            'name': acc.name,
            'type': 'Revenue'
        })
    for acc in expense_accounts:
        result.append({
            'id': acc.id,
            'code': acc.code,
            'name': acc.name,
            'type': 'Expense'
        })
    
    return {"accounts": result}


@router.get("/{budget_id}")
async def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get budget by ID with items"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Build items response
    items = []
    for item in budget.items:
        items.append({
            'id': item.id,
            'account_id': item.account_id,
            'account_code': item.account.code if item.account else None,
            'account_name': item.account.name if item.account else None,
            'account_type': item.account.type if item.account else None,
            'amount': float(item.amount) if item.amount else 0.0,
            'month': item.month
        })
    
    return {
        'id': budget.id,
        'name': budget.name,
        'fiscal_year': budget.fiscal_year,
        'description': budget.description,
        'is_active': budget.is_active,
        'items': items,
        'business_id': budget.business_id,
        'created_at': budget.created_at.isoformat() if budget.created_at else None,
        'updated_at': budget.updated_at.isoformat() if budget.updated_at else None
    }


@router.put("/{budget_id}", response_model=BudgetResponse, dependencies=[Depends(PermissionChecker(["budgets:edit"]))])
async def update_budget(
    budget_id: int,
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a budget"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    try:
        # Update basic info
        budget.name = budget_data.name
        budget.fiscal_year = budget_data.fiscal_year
        budget.description = budget_data.description
        
        # Remove existing items
        from app.models import BudgetItem
        db.query(BudgetItem).filter(BudgetItem.budget_id == budget_id).delete()
        
        # Add new items
        for item in budget_data.items:
            budget_service.add_item(
                budget_id=budget.id,
                account_id=item.account_id,
                amount=item.amount,
                month=item.month
            )
        
        db.commit()
        return budget
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{budget_id}", dependencies=[Depends(PermissionChecker(["budgets:delete"]))])
async def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a budget"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}


@router.post("/{budget_id}/items", dependencies=[Depends(PermissionChecker(["budgets:edit"]))])
async def add_budget_item(
    budget_id: int,
    item_data: BudgetItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Add an item to a budget"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    item = budget_service.add_item(
        budget_id=budget_id,
        account_id=item_data.account_id,
        amount=item_data.amount,
        month=item_data.month
    )
    
    db.commit()
    return {
        'id': item.id,
        'budget_id': item.budget_id,
        'account_id': item.account_id,
        'amount': float(item.amount),
        'month': item.month
    }


@router.delete("/{budget_id}/items/{item_id}", dependencies=[Depends(PermissionChecker(["budgets:edit"]))])
async def delete_budget_item(
    budget_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a budget item"""
    from app.models import BudgetItem
    
    item = db.query(BudgetItem).join(BudgetItem.budget).filter(
        BudgetItem.id == item_id,
        BudgetItem.budget_id == budget_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Budget item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Budget item deleted successfully"}


@router.get("/{budget_id}/vs-actual")
async def get_budget_vs_actual(
    budget_id: int,
    month: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Compare budget vs actual figures"""
    budget_service = BudgetService(db)
    result = budget_service.get_budget_vs_actual(budget_id, current_user.business_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Filter by month if provided
    items = result['items']
    if month:
        items = [item for item in items if item.get('month') == month or item.get('month') is None]
    
    # Build response
    response_items = []
    for item in items:
        account = item['account']
        budgeted = item['budgeted']
        actual = item['actual']
        variance = item['variance']
        
        response_items.append({
            'account_id': account.id,
            'account_code': account.code,
            'account_name': account.name,
            'account_type': account.type if account.type else None,
            'budgeted': float(budgeted),
            'actual': float(actual),
            'variance': float(variance),
            'variance_percent': float(abs(variance) / budgeted * 100) if budgeted != 0 else 0
        })
    
    return {
        'budget': {
            'id': result['budget'].id,
            'name': result['budget'].name,
            'fiscal_year': result['budget'].fiscal_year,
            'description': result['budget'].description
        },
        'items': response_items
    }


@router.get("/{budget_id}/monthly")
async def get_monthly_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get monthly breakdown of budget"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Group items by month
    monthly_data = {}
    for month_num in range(1, 13):
        monthly_data[month_num] = {
            'month': month_num,
            'month_name': date(2000, month_num, 1).strftime('%B'),
            'items': [],
            'total_budgeted': 0.0
        }
    
    for item in budget.items:
        if item.month:
            monthly_data[item.month]['items'].append({
                'account_id': item.account_id,
                'account_name': item.account.name if item.account else None,
                'amount': float(item.amount)
            })
            monthly_data[item.month]['total_budgeted'] += float(item.amount)
    
    return {
        'budget': {
            'id': budget.id,
            'name': budget.name,
            'fiscal_year': budget.fiscal_year
        },
        'monthly': list(monthly_data.values())
    }
