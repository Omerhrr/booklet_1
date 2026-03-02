"""
Accounting API Routes - Chart of Accounts, Journal Vouchers, Reports
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    AccountCreate, AccountUpdate, AccountResponse,
    JournalVoucherCreate, JournalVoucherResponse,
    BudgetCreate, BudgetItem
)
from app.services.accounting_service import (
    AccountService, JournalVoucherService, BudgetService, ReportService
)

router = APIRouter(prefix="/accounting", tags=["Accounting"])


# ==================== CHART OF ACCOUNTS ====================

@router.get("/accounts", response_model=List[AccountResponse])
async def list_accounts(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all accounts"""
    account_service = AccountService(db)
    return account_service.get_by_business(current_user.business_id, include_inactive)


@router.post("/accounts", response_model=AccountResponse, dependencies=[Depends(PermissionChecker(["accounting:create"]))])
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new account"""
    account_service = AccountService(db)
    account = account_service.create(account_data, current_user.business_id)
    db.commit()
    return account


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get account by ID"""
    account_service = AccountService(db)
    account = account_service.get_by_id(account_id, current_user.business_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse, dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update account"""
    account_service = AccountService(db)
    account = account_service.update(account_id, current_user.business_id, account_data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.commit()
    return account


@router.delete("/accounts/{account_id}", dependencies=[Depends(PermissionChecker(["accounting:delete"]))])
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete account"""
    account_service = AccountService(db)
    if not account_service.delete(account_id, current_user.business_id):
        raise HTTPException(status_code=400, detail="Cannot delete system account or account with entries")
    db.commit()
    return {"message": "Account deleted"}


@router.get("/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get account balance"""
    account_service = AccountService(db)
    result = account_service.get_with_balance(
        account_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return result


@router.get("/accounts/{account_id}/ledger")
async def get_account_ledger(
    account_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get ledger entries for an account"""
    from app.models import LedgerEntry, Account as AccountModel
    from sqlalchemy.orm import joinedload
    from decimal import Decimal
    
    # Verify account exists and belongs to business
    account = db.query(AccountModel).filter(
        AccountModel.id == account_id,
        AccountModel.business_id == current_user.business_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Get ledger entries ordered by date (newest first for display)
    entries_query = db.query(LedgerEntry).options(
        joinedload(LedgerEntry.account)
    ).filter(
        LedgerEntry.account_id == account_id
    )
    
    # Filter by branch
    if branch_id:
        entries_query = entries_query.filter(LedgerEntry.branch_id == branch_id)
    
    entries = entries_query.order_by(LedgerEntry.transaction_date.desc(), LedgerEntry.id.desc()).limit(limit).all()
    
    # Get all entries to calculate correct running balance (in chronological order)
    all_entries_query = db.query(LedgerEntry).filter(
        LedgerEntry.account_id == account_id
    )
    if branch_id:
        all_entries_query = all_entries_query.filter(LedgerEntry.branch_id == branch_id)
    
    all_entries = all_entries_query.order_by(LedgerEntry.transaction_date, LedgerEntry.id).all()
    
    # Calculate running balance
    running_balance = Decimal("0")
    balance_map = {}
    for e in all_entries:
        running_balance += (e.debit or Decimal("0")) - (e.credit or Decimal("0"))
        balance_map[e.id] = float(running_balance)
    
    # Build result with entries
    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "transaction_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
            "description": entry.description or "",
            "reference": entry.reference or "",
            "debit": float(entry.debit) if entry.debit else 0.0,
            "credit": float(entry.credit) if entry.credit else 0.0,
            "balance": balance_map.get(entry.id, 0.0)
        })
    
    return {
        "account_id": account_id,
        "account_name": account.name,
        "account_code": account.code,
        "entries": result
    }


# ==================== JOURNAL VOUCHERS ====================

@router.get("/journal-vouchers", response_model=List[JournalVoucherResponse])
async def list_journal_vouchers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all journal vouchers"""
    jv_service = JournalVoucherService(db)
    return jv_service.get_by_branch(current_user.selected_branch.id, current_user.business_id)


# Alias for frontend compatibility
@router.get("/journal", response_model=List[JournalVoucherResponse])
async def list_journal_vouchers_alias(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all journal vouchers (alias)"""
    jv_service = JournalVoucherService(db)
    return jv_service.get_by_branch(current_user.selected_branch.id, current_user.business_id)


@router.post("/journal-vouchers", response_model=JournalVoucherResponse, dependencies=[Depends(PermissionChecker(["journal:create"]))])
async def create_journal_voucher(
    voucher_data: JournalVoucherCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new journal voucher"""
    jv_service = JournalVoucherService(db)
    try:
        voucher = jv_service.create(
            voucher_data,
            current_user.business_id,
            current_user.selected_branch.id,
            current_user.id
        )
        db.commit()
        return voucher
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Alias POST for frontend compatibility
@router.post("/journal", response_model=JournalVoucherResponse, dependencies=[Depends(PermissionChecker(["journal:create"]))])
async def create_journal_voucher_alias(
    voucher_data: JournalVoucherCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new journal voucher (alias)"""
    jv_service = JournalVoucherService(db)
    try:
        voucher = jv_service.create(
            voucher_data,
            current_user.business_id,
            current_user.selected_branch.id,
            current_user.id
        )
        db.commit()
        return voucher
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journal-vouchers/{voucher_id}", response_model=JournalVoucherResponse)
async def get_journal_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get journal voucher by ID"""
    jv_service = JournalVoucherService(db)
    voucher = jv_service.get_by_id(voucher_id, current_user.business_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Journal voucher not found")
    return voucher


# Journal detail with ledger entries
@router.get("/journal/{voucher_id}")
async def get_journal_voucher_detail(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get journal voucher by ID with ledger entries"""
    jv_service = JournalVoucherService(db)
    voucher = jv_service.get_by_id(voucher_id, current_user.business_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Journal voucher not found")
    
    # Build response with ledger entries
    entries = []
    for entry in voucher.ledger_entries:
        entries.append({
            'id': entry.id,
            'account_id': entry.account_id,
            'account_name': entry.account.name if entry.account else None,
            'account_code': entry.account.code if entry.account else None,
            'description': entry.description,
            'debit': float(entry.debit) if entry.debit else 0.0,
            'credit': float(entry.credit) if entry.credit else 0.0
        })
    
    return {
        'id': voucher.id,
        'voucher_number': voucher.voucher_number,
        'transaction_date': voucher.transaction_date.isoformat() if voucher.transaction_date else None,
        'description': voucher.description,
        'reference': voucher.reference,
        'is_posted': voucher.is_posted,
        'branch_id': voucher.branch_id,
        'business_id': voucher.business_id,
        'created_at': voucher.created_at.isoformat() if voucher.created_at else None,
        'ledger_entries': entries
    }


@router.post("/journal-vouchers/{voucher_id}/post", dependencies=[Depends(PermissionChecker(["journal:create"]))])
async def post_journal_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Post journal voucher"""
    jv_service = JournalVoucherService(db)
    voucher = jv_service.post(voucher_id, current_user.business_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Journal voucher not found")
    db.commit()
    return {"message": "Journal voucher posted"}


# ==================== BUDGETS ====================

@router.get("/budgets")
async def list_budgets(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all budgets"""
    budget_service = BudgetService(db)
    return budget_service.get_by_business(current_user.business_id)


@router.post("/budgets", dependencies=[Depends(PermissionChecker(["budgeting:create"]))])
async def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new budget"""
    budget_service = BudgetService(db)
    budget = budget_service.create(budget_data, current_user.business_id)
    db.commit()
    return budget


@router.get("/budgets/{budget_id}")
async def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get budget by ID"""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.business_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.get("/budgets/{budget_id}/vs-actual")
async def get_budget_vs_actual(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get budget vs actual comparison"""
    budget_service = BudgetService(db)
    result = budget_service.get_budget_vs_actual(budget_id, current_user.business_id)
    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")
    return result


# ==================== REPORTS ====================

@router.get("/reports/trial-balance")
async def get_trial_balance(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get trial balance report"""
    report_service = ReportService(db)
    data = report_service.get_trial_balance(
        current_user.business_id, 
        current_user.selected_branch.id,
        as_of_date
    )
    
    # Serialize for JSON response
    result = []
    for item in data:
        account = item.get('account')
        result.append({
            'account_id': account.id if account else None,
            'account_code': account.code if account else None,
            'account_name': account.name if account else None,
            'account_type': account.type if account and account.type else None,
            'debit': float(item.get('debit', 0)),
            'credit': float(item.get('credit', 0)),
            'balance': float(item.get('balance', 0))
        })
    
    return result


@router.get("/reports/balance-sheet")
async def get_balance_sheet(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get balance sheet report in Statement of Financial Position format"""
    report_service = ReportService(db)
    data = report_service.get_balance_sheet(
        current_user.business_id,
        current_user.selected_branch.id,
        as_of_date
    )
    
    def serialize_decimal(value):
        """Convert Decimal to float for JSON serialization"""
        return float(value) if value is not None else 0.0
    
    return {
        # Non-Current Assets
        'non_current_assets': {
            'fixed_assets_cost': serialize_decimal(data['non_current_assets']['fixed_assets_cost']),
            'accumulated_depreciation': serialize_decimal(data['non_current_assets']['accumulated_depreciation']),
            'net_book_value': serialize_decimal(data['non_current_assets']['net_book_value']),
            'other_non_current': serialize_decimal(data['non_current_assets']['other_non_current']),
            'total': serialize_decimal(data['non_current_assets']['total'])
        },
        # Current Assets
        'current_assets': {
            'inventory': serialize_decimal(data['current_assets']['inventory']),
            'accounts_receivable': serialize_decimal(data['current_assets']['accounts_receivable']),
            'vat_receivable': serialize_decimal(data['current_assets']['vat_receivable']),
            'cash_and_bank': serialize_decimal(data['current_assets']['cash_and_bank']),
            'other_current_assets': serialize_decimal(data['current_assets']['other_current_assets']),
            'vendor_advances': serialize_decimal(data['current_assets']['vendor_advances']),
            'total': serialize_decimal(data['current_assets']['total'])
        },
        'total_assets': serialize_decimal(data['total_assets']),
        # Liabilities
        'liabilities': {
            'accounts_payable': serialize_decimal(data['liabilities']['accounts_payable']),
            'payroll_liabilities': serialize_decimal(data['liabilities']['payroll_liabilities']),
            'paye_payable': serialize_decimal(data['liabilities']['paye_payable']),
            'pension_payable': serialize_decimal(data['liabilities']['pension_payable']),
            'vat_payable': serialize_decimal(data['liabilities']['vat_payable']),
            'customer_advances': serialize_decimal(data['liabilities']['customer_advances']),
            'other_liabilities': serialize_decimal(data['liabilities']['other_liabilities']),
            'total': serialize_decimal(data['liabilities']['total'])
        },
        # Equity
        'equity': {
            'owners_equity': serialize_decimal(data['equity']['owners_equity']),
            'retained_earnings': serialize_decimal(data['equity']['retained_earnings']),
            'opening_balance_equity': serialize_decimal(data['equity']['opening_balance_equity']),
            'current_period_earnings': serialize_decimal(data['equity']['current_period_earnings']),
            'total': serialize_decimal(data['equity']['total'])
        },
        'total_liabilities': serialize_decimal(data['total_liabilities']),
        'total_equity': serialize_decimal(data['total_equity']),
        'total_equity_and_liabilities': serialize_decimal(data['total_equity_and_liabilities']),
        'as_of_date': data.get('as_of_date').isoformat() if data.get('as_of_date') else None
    }


@router.get("/reports/income-statement")
async def get_income_statement(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get income statement (P&L) report"""
    report_service = ReportService(db)
    data = report_service.get_income_statement(
        current_user.business_id,
        current_user.selected_branch.id,
        start_date,
        end_date
    )
    
    def serialize_items(items):
        result = []
        for item in items:
            account = item.get('account')
            result.append({
                'account_id': account.id if account else None,
                'account_code': account.code if account else None,
                'account_name': account.name if account else None,
                'balance': float(item.get('balance', 0))
            })
        return result
    
    return {
        'revenue': serialize_items(data.get('revenue', [])),
        'expenses': serialize_items(data.get('expenses', [])),
        'total_revenue': float(data.get('total_revenue', 0)),
        'total_expenses': float(data.get('total_expenses', 0)),
        'net_income': float(data.get('net_income', 0)),
        'start_date': data.get('start_date').isoformat() if data.get('start_date') else None,
        'end_date': data.get('end_date').isoformat() if data.get('end_date') else None
    }


@router.get("/reports/general-ledger")
async def get_general_ledger(
    account_id: int = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get general ledger report with per-account running balances"""
    report_service = ReportService(db)
    data = report_service.get_general_ledger(
        current_user.business_id,
        current_user.selected_branch.id,
        account_id,
        start_date,
        end_date
    )
    
    # Get summary statistics
    summary = report_service.get_general_ledger_summary(
        current_user.business_id,
        current_user.selected_branch.id,
        account_id,
        start_date,
        end_date
    )
    
    # Serialize for JSON response
    result = []
    for item in data:
        entry = item.get('entry')
        account_info = item.get('account_info', {})
        is_opening = item.get('is_opening', False)
        
        result.append({
            'id': entry.id if entry else None,
            'transaction_date': entry.transaction_date.isoformat() if entry and entry.transaction_date else None,
            'account_id': account_info.get('id'),
            'account_code': account_info.get('code', ''),
            'account_name': account_info.get('name', ''),
            'account_type': account_info.get('type', ''),
            'description': entry.description if entry else None,
            'reference': entry.reference if entry else None,
            'debit': float(entry.debit) if entry and entry.debit else 0.0,
            'credit': float(entry.credit) if entry and entry.credit else 0.0,
            'balance': float(item.get('balance', 0)),
            'is_opening': is_opening
        })
    
    return {
        'entries': result,
        'summary': summary
    }
