"""
Cash Book API Routes - Central Hub for Cash/Bank Transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    CashBookEntryCreate, CashBookEntryResponse, CashBookEntryWithAccount,
    CashBookSummary, CashBookFilter, FundAccountRequest, MessageResponse
)
from app.services.cashbook_service import CashBookService

router = APIRouter(prefix="/cashbook", tags=["Cash Book"])


@router.get("")
async def list_cash_book_entries(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[int] = None,
    entry_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List cash book entries with optional filters"""
    cashbook_service = CashBookService(db)
    entries = cashbook_service.get_entries(
        current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        entry_type=entry_type,
        limit=limit,
        offset=offset
    )
    
    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "entry_type": entry.entry_type,
            "account_id": entry.account_id,
            "account_name": entry.account.name if entry.account else None,
            "account_type": entry.account_type,
            "amount": float(entry.amount) if entry.amount else 0.0,
            "balance_after": float(entry.balance_after) if entry.balance_after else None,
            "description": entry.description,
            "reference": entry.reference,
            "payee_payer": entry.payee_payer,
            "source_type": entry.source_type,
            "source_id": entry.source_id,
            "is_transfer": entry.is_transfer,
            "transfer_direction": entry.transfer_direction,
            "created_by_name": entry.created_by_user.full_name if entry.created_by_user else None,
            "created_at": entry.created_at.isoformat() if entry.created_at else None
        })
    
    return result


@router.post("", response_model=CashBookEntryResponse, dependencies=[Depends(PermissionChecker(["accounting:create"]))])
async def create_cash_book_entry(
    entry_data: CashBookEntryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a manual cash book entry"""
    cashbook_service = CashBookService(db)
    entry = cashbook_service.create_entry(
        entry_data,
        current_user.business_id,
        current_user.selected_branch.id if current_user.selected_branch else None,
        current_user.id
    )
    db.commit()
    return entry


@router.get("/summary")
async def get_cash_book_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get summary for all cash/bank accounts"""
    cashbook_service = CashBookService(db)
    summaries = cashbook_service.get_cash_book_summary(
        current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        start_date=start_date,
        end_date=end_date
    )
    
    result = []
    for summary in summaries:
        result.append({
            "account_id": summary["account_id"],
            "account_name": summary["account_name"],
            "account_type": summary["account_type"],
            "opening_balance": float(summary["opening_balance"]),
            "total_receipts": float(summary["total_receipts"]),
            "total_payments": float(summary["total_payments"]),
            "closing_balance": float(summary["closing_balance"]),
            "entries_count": summary["entries_count"]
        })
    
    return result


@router.get("/cash-flow")
async def get_cash_flow_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get overall cash flow summary"""
    cashbook_service = CashBookService(db)
    summary = cashbook_service.get_cash_flow_summary(
        current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        start_date=start_date,
        end_date=end_date
    )
    
    # Convert Decimal to float
    by_source = {}
    for source, data in summary["by_source"].items():
        by_source[source] = {
            "receipts": float(data["receipts"]),
            "payments": float(data["payments"]),
            "count": data["count"]
        }
    
    return {
        "total_receipts": float(summary["total_receipts"]),
        "total_payments": float(summary["total_payments"]),
        "net_cash_flow": float(summary["net_cash_flow"]),
        "total_entries": summary["total_entries"],
        "by_source": by_source,
        "period": summary["period"]
    }


@router.get("/account/{account_id}")
async def get_account_transactions(
    account_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get transactions for a specific account"""
    cashbook_service = CashBookService(db)
    entries = cashbook_service.get_entries(
        current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        limit=limit,
        offset=offset
    )
    
    # Get account summary
    from app.models import Account
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.business_id == current_user.business_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    summary = cashbook_service.get_account_summary(
        account_id,
        account.name,
        "cash",
        current_user.selected_branch.id if current_user.selected_branch else None,
        start_date,
        end_date
    )
    
    result = [{
        "id": e.id,
        "entry_number": e.entry_number,
        "entry_date": e.entry_date.isoformat() if e.entry_date else None,
        "entry_type": e.entry_type,
        "amount": float(e.amount) if e.amount else 0.0,
        "balance_after": float(e.balance_after) if e.balance_after else None,
        "description": e.description,
        "reference": e.reference,
        "payee_payer": e.payee_payer,
        "source_type": e.source_type,
        "created_at": e.created_at.isoformat() if e.created_at else None
    } for e in entries]
    
    return {
        "account": {
            "id": account.id,
            "name": account.name,
            "code": account.code
        },
        "summary": {
            "opening_balance": float(summary["opening_balance"]),
            "total_receipts": float(summary["total_receipts"]),
            "total_payments": float(summary["total_payments"]),
            "closing_balance": float(summary["closing_balance"])
        },
        "entries": result
    }


@router.get("/entry/{entry_id}")
async def get_cash_book_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a single cash book entry"""
    cashbook_service = CashBookService(db)
    entry = cashbook_service.get_entry_by_id(entry_id, current_user.business_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return {
        "id": entry.id,
        "entry_number": entry.entry_number,
        "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
        "entry_type": entry.entry_type,
        "account_id": entry.account_id,
        "account_name": entry.account.name if entry.account else None,
        "account_type": entry.account_type,
        "amount": float(entry.amount) if entry.amount else 0.0,
        "balance_after": float(entry.balance_after) if entry.balance_after else None,
        "description": entry.description,
        "reference": entry.reference,
        "payee_payer": entry.payee_payer,
        "source_type": entry.source_type,
        "source_id": entry.source_id,
        "is_transfer": entry.is_transfer,
        "transfer_id": entry.transfer_id,
        "transfer_direction": entry.transfer_direction,
        "branch_id": entry.branch_id,
        "business_id": entry.business_id,
        "created_by_name": entry.created_by_user.full_name if entry.created_by_user else None,
        "created_at": entry.created_at.isoformat() if entry.created_at else None
    }


@router.delete("/entry/{entry_id}", dependencies=[Depends(PermissionChecker(["accounting:delete"]))])
async def delete_cash_book_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a manual cash book entry"""
    cashbook_service = CashBookService(db)
    if not cashbook_service.delete_entry(entry_id, current_user.business_id):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete entry. Either not found or linked to another transaction."
        )
    db.commit()
    return {"message": "Entry deleted"}


@router.post("/reconcile/{account_id}")
async def reconcile_account(
    account_id: int,
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Reconcile cash book with ledger for an account"""
    cashbook_service = CashBookService(db)
    result = cashbook_service.reconcile_with_ledger(
        account_id,
        current_user.selected_branch.id if current_user.selected_branch else None,
        as_of_date or date.today()
    )
    
    return {
        "account_id": result["account_id"],
        "as_of_date": result["as_of_date"].isoformat() if result["as_of_date"] else None,
        "ledger_balance": float(result["ledger_balance"]),
        "cash_book_balance": float(result["cash_book_balance"]),
        "difference": float(result["difference"]),
        "is_reconciled": result["is_reconciled"]
    }


@router.post("/fund-account", dependencies=[Depends(PermissionChecker(["accounting:create"]))])
async def fund_customer_vendor_account(
    fund_data: FundAccountRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Fund a customer or vendor account with advance payment.
    
    This allows customers to deposit money before making purchases,
    or vendors to receive advance payments before we make purchases.
    
    When an invoice/bill is created, the system will automatically
    check the account balance and deduct from it.
    """
    from app.models import Customer, Vendor, Account, CashBookEntry, LedgerEntry
    from sqlalchemy import func
    
    if not current_user.selected_branch:
        raise HTTPException(status_code=400, detail="No branch selected. Please select a branch first.")
    
    branch_id = current_user.selected_branch.id
    
    # Validate payment account exists
    payment_account = db.query(Account).filter(
        Account.id == fund_data.payment_account_id,
        Account.business_id == current_user.business_id
    ).first()
    
    if not payment_account:
        raise HTTPException(status_code=404, detail="Payment account not found")
    
    # Get current balance from payment account
    current_balance = db.query(
        func.sum(LedgerEntry.debit - LedgerEntry.credit)
    ).filter(
        LedgerEntry.account_id == payment_account.id,
        LedgerEntry.branch_id == branch_id
    ).scalar() or Decimal("0")
    
    # For vendor funding (we're paying out), check we have sufficient funds
    # For customer funding (we're receiving money), no need to check balance
    if fund_data.entity_type == "vendor" and current_balance < fund_data.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient funds in payment account. Available: {float(current_balance)}"
        )
    
    entity_name = None
    entity_id = None
    
    if fund_data.entity_type == "customer":
        # Validate customer exists
        customer = db.query(Customer).filter(
            Customer.id == fund_data.entity_id,
            Customer.business_id == current_user.business_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update customer account balance (increase = credit with us)
        customer.account_balance = (customer.account_balance or Decimal("0")) + fund_data.amount
        entity_name = customer.name
        entity_id = customer.id
        
        # Create ledger entry - credit customer advances (liability)
        # Get or create Customer Advances account
        advances_account = db.query(Account).filter(
            Account.business_id == current_user.business_id,
            Account.name.ilike("%Customer Advance%")
        ).first()
        
        if not advances_account:
            # Create the account if it doesn't exist
            from datetime import datetime
            advances_account = Account(
                name="Customer Advances",
                code="2200",
                type="Liability",
                description="Advance payments from customers",
                business_id=current_user.business_id,
                is_system_account=False,
                created_at=datetime.utcnow()
            )
            db.add(advances_account)
            db.flush()
        
        # Debit cash/bank (increase asset - customer is giving us money)
        debit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=fund_data.description or f"Advance payment from {customer.name}",
            debit=fund_data.amount,
            credit=Decimal("0"),
            account_id=payment_account.id,
            bank_account_id=fund_data.bank_account_id,  # Link to specific bank account
            customer_id=customer.id,
            branch_id=branch_id
        )
        db.add(debit_entry)
        
        # Credit customer advances (increase liability - we owe the customer)
        credit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=fund_data.description or f"Advance payment from {customer.name}",
            debit=Decimal("0"),
            credit=fund_data.amount,
            account_id=advances_account.id,
            customer_id=customer.id,
            branch_id=branch_id
        )
        db.add(credit_entry)
        
    elif fund_data.entity_type == "vendor":
        # Validate vendor exists
        vendor = db.query(Vendor).filter(
            Vendor.id == fund_data.entity_id,
            Vendor.business_id == current_user.business_id
        ).first()
        
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Update vendor account balance (increase = we prepaid them, asset)
        vendor.account_balance = (vendor.account_balance or Decimal("0")) + fund_data.amount
        entity_name = vendor.name
        entity_id = vendor.id
        
        # Create ledger entry - debit vendor advances (asset)
        # Get or create Vendor Advances account
        advances_account = db.query(Account).filter(
            Account.business_id == current_user.business_id,
            Account.name.ilike("%Vendor Advance%")
        ).first()
        
        if not advances_account:
            # Create the account if it doesn't exist
            from datetime import datetime as dt
            advances_account = Account(
                name="Vendor Advances",
                code="1350",
                type="Asset",
                description="Advance payments to vendors",
                business_id=current_user.business_id,
                is_system_account=False,
                created_at=dt.utcnow()
            )
            db.add(advances_account)
            db.flush()
        
        # Debit vendor advances (increase asset - we have credit with vendor)
        debit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=fund_data.description or f"Advance payment to {vendor.name}",
            debit=fund_data.amount,
            credit=Decimal("0"),
            account_id=advances_account.id,
            vendor_id=vendor.id,
            branch_id=branch_id
        )
        db.add(debit_entry)
        
        # Credit cash/bank (decrease asset - we paid out money)
        credit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=fund_data.description or f"Advance payment to {vendor.name}",
            debit=Decimal("0"),
            credit=fund_data.amount,
            account_id=payment_account.id,
            bank_account_id=fund_data.bank_account_id,  # Link to specific bank account
            vendor_id=vendor.id,
            branch_id=branch_id
        )
        db.add(credit_entry)
    
    # Create cash book entry
    entry_type = "payment" if fund_data.entity_type == "vendor" else "receipt"
    prefix = "CR" if entry_type == "receipt" else "CP"
    
    last_entry = db.query(CashBookEntry).filter(
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_number.like(f'{prefix}-%')
    ).order_by(CashBookEntry.id.desc()).first()
    
    if last_entry:
        try:
            num = int(last_entry.entry_number.replace(f'{prefix}-', ''))
            entry_number = f'{prefix}-{num + 1:05d}'
        except ValueError:
            entry_number = f'{prefix}-00001'
    else:
        entry_number = f'{prefix}-00001'
    
    # Calculate new balance after entry
    new_balance = current_balance - fund_data.amount if entry_type == "payment" else current_balance + fund_data.amount
    
    # Determine if payment account is a bank account
    account_type = "cash"
    bank_account_id = None
    
    # Check if this account is linked to a bank account
    from app.models import BankAccount
    linked_bank = db.query(BankAccount).filter(
        BankAccount.chart_of_account_id == payment_account.id,
        BankAccount.business_id == current_user.business_id
    ).first()
    
    if linked_bank:
        account_type = "bank"
        bank_account_id = linked_bank.id
    
    cashbook_entry = CashBookEntry(
        entry_number=entry_number,
        entry_date=date.today(),
        entry_type=entry_type,
        account_id=payment_account.id,
        account_type=account_type,
        amount=fund_data.amount,
        balance_after=new_balance,
        description=fund_data.description or f"Fund {fund_data.entity_type} account - {entity_name}",
        reference=fund_data.reference,
        payee_payer=entity_name,
        source_type=f"{fund_data.entity_type}_advance",
        source_id=entity_id,
        branch_id=branch_id,
        business_id=current_user.business_id
    )
    db.add(cashbook_entry)
    
    db.commit()
    
    return {
        "message": f"Successfully funded {fund_data.entity_type} account with {float(fund_data.amount)}",
        "success": True
    }


@router.get("/customers-with-balance")
async def get_customers_with_balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customers with their account balances for funding"""
    from app.models import Customer
    
    customers = db.query(Customer).filter(
        Customer.business_id == current_user.business_id,
        Customer.branch_id == current_user.selected_branch.id if current_user.selected_branch else None,
        Customer.is_active == True
    ).all()
    
    return [{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "account_balance": float(c.account_balance or 0)
    } for c in customers]


@router.get("/vendors-with-balance")
async def get_vendors_with_balance(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendors with their account balances for funding"""
    from app.models import Vendor
    
    vendors = db.query(Vendor).filter(
        Vendor.business_id == current_user.business_id,
        Vendor.branch_id == current_user.selected_branch.id if current_user.selected_branch else None,
        Vendor.is_active == True
    ).all()
    
    return [{
        "id": v.id,
        "name": v.name,
        "email": v.email,
        "phone": v.phone,
        "account_balance": float(v.account_balance or 0)
    } for v in vendors]
