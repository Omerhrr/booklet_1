"""
Fiscal Year API Routes - Manage accounting periods and year-end processes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.services.fiscal_year_service import (
    FiscalYearService, OpeningBalanceService, BankReconciliationAdjustmentService
)

router = APIRouter(prefix="/fiscal-year", tags=["Fiscal Year"])


# ==================== SCHEMAS ====================

class FiscalYearCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    auto_create_periods: bool = True
    period_type: str = Field(default="monthly", pattern="^(monthly|quarterly)$")


class FiscalYearResponse(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_closed: bool
    closed_at: Optional[str] = None
    business_id: int
    created_at: str
    
    class Config:
        from_attributes = True


class FiscalPeriodResponse(BaseModel):
    id: int
    fiscal_year_id: int
    period_number: int
    name: str
    start_date: date
    end_date: date
    is_adjustment_period: bool
    is_closed: bool
    closed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class OpeningBalanceCreate(BaseModel):
    fiscal_year_id: int
    account_id: int
    debit: Decimal = Field(default=Decimal("0.00"), ge=0)
    credit: Decimal = Field(default=Decimal("0.00"), ge=0)
    description: Optional[str] = None


class OpeningBalanceResponse(BaseModel):
    id: int
    entry_number: str
    entry_date: date
    fiscal_year_id: int
    account_id: int
    account_name: Optional[str] = None
    debit: Decimal
    credit: Decimal
    description: Optional[str]
    is_posted: bool
    business_id: int
    
    class Config:
        from_attributes = True


class BulkOpeningBalanceCreate(BaseModel):
    fiscal_year_id: int
    balances: List[dict]  # [{"account_id": 1, "debit": 100, "credit": 0}, ...]


class BankAdjustmentCreate(BaseModel):
    bank_account_id: int
    adjustment_type: str = Field(..., pattern="^(bank_charge|interest|error_correction|other)$")
    amount: Decimal = Field(..., gt=0)
    direction: str = Field(..., pattern="^(debit|credit)$")
    adjustment_date: Optional[date] = None
    description: Optional[str] = None
    reference: Optional[str] = None


class BankAdjustmentResponse(BaseModel):
    id: int
    adjustment_number: str
    adjustment_date: date
    bank_account_id: int
    adjustment_type: str
    amount: Decimal
    direction: str
    description: Optional[str]
    reference: Optional[str]
    business_id: int
    
    class Config:
        from_attributes = True


# ==================== FISCAL YEAR ENDPOINTS ====================

@router.get("")
async def list_fiscal_years(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all fiscal years for the business"""
    service = FiscalYearService(db)
    fiscal_years = service.get_by_business(current_user.business_id)

    result = []
    for fy in fiscal_years:
        result.append({
            "id": fy.id,
            "name": fy.name,
            "start_date": fy.start_date.isoformat(),
            "end_date": fy.end_date.isoformat(),
            "is_current": fy.is_current,
            "is_closed": fy.is_closed,
            "closed_at": fy.closed_at.isoformat() if fy.closed_at else None,
            "business_id": fy.business_id,
            "created_at": fy.created_at.isoformat() if fy.created_at else None,
            "periods_count": len(fy.periods) if fy.periods else 0
        })

    return result


@router.get("/current")
async def get_current_fiscal_year(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get the current active fiscal year"""
    service = FiscalYearService(db)
    fiscal_year = service.get_current(current_user.business_id)
    
    if not fiscal_year:
        return {"fiscal_year": None, "message": "No active fiscal year found"}
    
    return {
        "id": fiscal_year.id,
        "name": fiscal_year.name,
        "start_date": fiscal_year.start_date.isoformat(),
        "end_date": fiscal_year.end_date.isoformat(),
        "is_current": fiscal_year.is_current,
        "is_closed": fiscal_year.is_closed,
        "periods_count": len(fiscal_year.periods) if fiscal_year.periods else 0
    }


@router.post("", dependencies=[Depends(PermissionChecker(["fiscal_year:create"]))])
async def create_fiscal_year(
    fiscal_year_data: FiscalYearCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new fiscal year with optional automatic period creation"""
    service = FiscalYearService(db)

    try:
        fiscal_year = service.create(
            name=fiscal_year_data.name,
            start_date=fiscal_year_data.start_date,
            end_date=fiscal_year_data.end_date,
            business_id=current_user.business_id,
            auto_create_periods=fiscal_year_data.auto_create_periods,
            period_type=fiscal_year_data.period_type
        )
        db.commit()
        return {
            "id": fiscal_year.id,
            "name": fiscal_year.name,
            "start_date": fiscal_year.start_date.isoformat(),
            "end_date": fiscal_year.end_date.isoformat(),
            "is_current": fiscal_year.is_current,
            "is_closed": fiscal_year.is_closed,
            "closed_at": fiscal_year.closed_at.isoformat() if fiscal_year.closed_at else None,
            "business_id": fiscal_year.business_id,
            "created_at": fiscal_year.created_at.isoformat() if fiscal_year.created_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{fiscal_year_id}")
async def get_fiscal_year(
    fiscal_year_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get fiscal year details with periods"""
    service = FiscalYearService(db)
    fiscal_year = service.get_by_id(fiscal_year_id, current_user.business_id)
    
    if not fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    
    periods = []
    for p in fiscal_year.periods:
        periods.append({
            "id": p.id,
            "period_number": p.period_number,
            "name": p.name,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "is_adjustment_period": p.is_adjustment_period,
            "is_closed": p.is_closed,
            "closed_at": p.closed_at.isoformat() if p.closed_at else None
        })
    
    return {
        "id": fiscal_year.id,
        "name": fiscal_year.name,
        "start_date": fiscal_year.start_date.isoformat(),
        "end_date": fiscal_year.end_date.isoformat(),
        "is_current": fiscal_year.is_current,
        "is_closed": fiscal_year.is_closed,
        "closed_at": fiscal_year.closed_at.isoformat() if fiscal_year.closed_at else None,
        "periods": periods,
        "business_id": fiscal_year.business_id,
        "created_at": fiscal_year.created_at.isoformat()
    }


@router.post("/{fiscal_year_id}/set-current", dependencies=[Depends(PermissionChecker(["fiscal_year:edit"]))])
async def set_current_fiscal_year(
    fiscal_year_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Set a fiscal year as the current active year"""
    service = FiscalYearService(db)
    
    try:
        fiscal_year = service.set_current(fiscal_year_id, current_user.business_id)
        db.commit()
        return {"message": f"Fiscal year '{fiscal_year.name}' set as current", "fiscal_year_id": fiscal_year.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{fiscal_year_id}/close", dependencies=[Depends(PermissionChecker(["fiscal_year:close"]))])
async def close_fiscal_year(
    fiscal_year_id: int,
    close_income_summary: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Close a fiscal year and optionally close temporary accounts"""
    service = FiscalYearService(db)
    
    try:
        fiscal_year = service.close_year(
            fiscal_year_id,
            current_user.business_id,
            current_user.id,
            close_income_summary=close_income_summary
        )
        db.commit()
        return {
            "message": f"Fiscal year '{fiscal_year.name}' closed successfully",
            "fiscal_year_id": fiscal_year.id,
            "closed_at": fiscal_year.closed_at.isoformat() if fiscal_year.closed_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/periods/{period_id}/close", dependencies=[Depends(PermissionChecker(["fiscal_year:close"]))])
async def close_fiscal_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Close a specific fiscal period"""
    service = FiscalYearService(db)
    
    try:
        period = service.close_period(period_id, current_user.business_id, current_user.id)
        db.commit()
        return {"message": f"Period '{period.name}' closed successfully", "period_id": period.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== OPENING BALANCE ENDPOINTS ====================

@router.get("/{fiscal_year_id}/opening-balances")
async def list_opening_balances(
    fiscal_year_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all opening balance entries for a fiscal year"""
    service = OpeningBalanceService(db)
    entries = service.get_by_fiscal_year(fiscal_year_id, current_user.business_id)
    
    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat(),
            "fiscal_year_id": entry.fiscal_year_id,
            "account_id": entry.account_id,
            "account_name": entry.account.name if entry.account else None,
            "debit": float(entry.debit),
            "credit": float(entry.credit),
            "description": entry.description,
            "is_posted": entry.is_posted,
            "business_id": entry.business_id
        })
    
    return result


@router.post("/opening-balances", dependencies=[Depends(PermissionChecker(["fiscal_year:create"]))])
async def create_opening_balance(
    balance_data: OpeningBalanceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create an opening balance entry for an account"""
    service = OpeningBalanceService(db)
    
    try:
        entry = service.create_entry(
            fiscal_year_id=balance_data.fiscal_year_id,
            account_id=balance_data.account_id,
            debit=balance_data.debit,
            credit=balance_data.credit,
            business_id=current_user.business_id,
            branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
            description=balance_data.description,
            user_id=current_user.id
        )
        db.commit()
        
        return {
            "id": entry.id,
            "entry_number": entry.entry_number,
            "account_id": entry.account_id,
            "debit": float(entry.debit),
            "credit": float(entry.credit),
            "is_posted": entry.is_posted
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/opening-balances/bulk", dependencies=[Depends(PermissionChecker(["fiscal_year:create"]))])
async def create_bulk_opening_balances(
    balance_data: BulkOpeningBalanceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create multiple opening balance entries from trial balance import"""
    service = OpeningBalanceService(db)
    
    try:
        entries = service.create_from_trial_balance(
            fiscal_year_id=balance_data.fiscal_year_id,
            balances=balance_data.balances,
            business_id=current_user.business_id,
            branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
            user_id=current_user.id
        )
        db.commit()
        
        return {
            "message": f"Created {len(entries)} opening balance entries",
            "count": len(entries)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{fiscal_year_id}/opening-balances/post", dependencies=[Depends(PermissionChecker(["fiscal_year:create"]))])
async def post_opening_balances(
    fiscal_year_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Post all opening balance entries for a fiscal year"""
    service = OpeningBalanceService(db)
    
    try:
        success = service.post_entries(fiscal_year_id, current_user.business_id, current_user.id)
        db.commit()
        
        if success:
            return {"message": "Opening balances posted successfully"}
        else:
            return {"message": "No unposted entries found"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== BANK RECONCILIATION ADJUSTMENTS ====================

@router.post("/bank-adjustments", dependencies=[Depends(PermissionChecker(["bank:reconcile"]))])
async def create_bank_adjustment(
    adjustment_data: BankAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a bank reconciliation adjustment entry"""
    service = BankReconciliationAdjustmentService(db)
    
    try:
        adjustment = service.create_adjustment(
            bank_account_id=adjustment_data.bank_account_id,
            adjustment_type=adjustment_data.adjustment_type,
            amount=adjustment_data.amount,
            direction=adjustment_data.direction,
            business_id=current_user.business_id,
            branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
            adjustment_date=adjustment_data.adjustment_date,
            description=adjustment_data.description,
            reference=adjustment_data.reference,
            user_id=current_user.id
        )
        db.commit()
        
        return {
            "id": adjustment.id,
            "adjustment_number": adjustment.adjustment_number,
            "adjustment_type": adjustment.adjustment_type,
            "amount": float(adjustment.amount),
            "direction": adjustment.direction,
            "message": "Bank adjustment created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bank-adjustments/{bank_account_id}")
async def list_bank_adjustments(
    bank_account_id: int,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List bank reconciliation adjustments for a bank account"""
    service = BankReconciliationAdjustmentService(db)
    
    adjustments = service.get_by_bank_account(
        bank_account_id,
        current_user.business_id,
        start_date,
        end_date
    )
    
    result = []
    for adj in adjustments:
        result.append({
            "id": adj.id,
            "adjustment_number": adj.adjustment_number,
            "adjustment_date": adj.adjustment_date.isoformat(),
            "adjustment_type": adj.adjustment_type,
            "amount": float(adj.amount),
            "direction": adj.direction,
            "description": adj.description,
            "reference": adj.reference,
            "created_at": adj.created_at.isoformat() if adj.created_at else None
        })
    
    return result
