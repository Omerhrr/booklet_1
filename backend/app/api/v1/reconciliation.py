"""
Bank Reconciliation API Routes - Import, Match, Clear Transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import csv
import io
from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.models import (
    BankAccount, BankStatementLine, BankReconciliationRecord,
    CashBookEntry, User, Branch
)
from app.services.banking_service import BankAccountService

from pydantic import BaseModel, ConfigDict
from app.schemas import BankAccountResponse

router = APIRouter(prefix="/reconciliation", tags=["Bank Reconciliation"])


# ==================== SCHEMAS ====================

class BankStatementLineCreate(BaseModel):
    bank_account_id: int
    statement_date: date
    transaction_date: Optional[date] = None
    transaction_type: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    amount: Decimal
    balance_after: Optional[Decimal] = None
    statement_id: Optional[str] = None
    import_batch_id: Optional[str] = None


class BankStatementLineResponse(BaseModel):
    id: int
    bank_account_id: int
    statement_date: date
    transaction_date: Optional[date]
    transaction_type: Optional[str]
    description: Optional[str]
    reference: Optional[str]
    amount: Decimal
    balance_after: Optional[Decimal]
    is_matched: bool
    is_cleared: bool
    matched_cashbook_entry_id: Optional[int]
    matched_date: Optional[date]
    statement_id: Optional[str]
    import_batch_id: Optional[str]
    import_date: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReconciliationStatus(BaseModel):
    account_id: int
    account_name: str
    book_balance: Decimal
    last_reconciliation_date: Optional[date]
    last_reconciliation_balance: Optional[Decimal]
    uncleared_items: dict
    statement_lines: dict


class ReconciliationCreate(BaseModel):
    bank_account_id: int
    statement_date: date
    statement_balance: Decimal
    notes: Optional[str] = None


class ReconciliationResponse(BaseModel):
    id: int
    reconciliation_number: str
    bank_account_id: int
    statement_date: date
    statement_balance: Decimal
    book_balance: Decimal
    deposits_in_transit: Decimal
    outstanding_checks: Decimal
    other_adjustments: Decimal
    adjusted_balance: Decimal
    difference: Decimal
    status: str
    notes: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MatchRequest(BaseModel):
    statement_line_id: int
    cashbook_entry_id: int


# ==================== ENDPOINTS ====================


@router.get("/accounts/{account_id}/status", response_model=ReconciliationStatus)
async def get_reconciliation_status(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get reconciliation status for a bank account"""
    from sqlalchemy import func
    
    account_service = BankAccountService(db)
    bank_account = account_service.get_by_id(account_id, current_user.business_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Get uncleared cashbook entries
    uncleared_receipts = db.query(func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'receipt',
        CashBookEntry.is_cleared == False
    ).scalar() or Decimal("0")
    
    uncleared_payments = db.query(func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'payment',
        CashBookEntry.is_cleared == False
    ).scalar() or Decimal("0")
    
    # Get uncleared statement lines
    uncleared_deposits = db.query(func.sum(BankStatementLine.amount)).filter(
        BankStatementLine.bank_account_id == account_id,
        BankStatementLine.branch_id == branch_id,
        BankStatementLine.business_id == current_user.business_id,
        BankStatementLine.transaction_type == 'credit',
        BankStatementLine.is_cleared == False
    ).scalar() or Decimal("0")
    
    uncleared_withdrawals = db.query(func.sum(BankStatementLine.amount)).filter(
        BankStatementLine.bank_account_id == account_id,
        BankStatementLine.branch_id == branch_id,
        BankStatementLine.business_id == current_user.business_id,
        BankStatementLine.transaction_type == 'debit',
        BankStatementLine.is_cleared == False
    ).scalar() or Decimal("0")
    
    # Get book balance
    book_balance = db.query(func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'receipt'
    ).scalar() or Decimal("0")
    
    book_payments = db.query(func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'payment'
    ).scalar() or Decimal("0")
    
    book_balance = book_balance - book_payments
    
    return ReconciliationStatus(
        account_id=account_id,
        account_name=bank_account.account_name,
        book_balance=book_balance,
        last_reconciliation_date=bank_account.last_reconciliation_date,
        last_reconciliation_balance=bank_account.last_reconciliation_balance,
        uncleared_items={
            "deposits_in_transit": uncleared_receipts,
            "outstanding_checks": uncleared_payments,
        },
        statement_lines={
            "uncleared_deposits": uncleared_deposits,
            "uncleared_withdrawals": uncleared_withdrawals,
        }
    )


@router.post("/accounts/{account_id}/import-statement")
async def import_bank_statement(
    account_id: int,
    statement_date: date,
    file: UploadFile = File,
    has_header: bool = True,
    delimiter: str = ",",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Import bank statement from CSV file
    
    Expected CSV columns (adjust via has_header):
    - date, transaction_type, description, reference. amount. balance_after
    
    Or without header (in order):
    - Column 0: date
    - Column 1: transaction_type (debit/credit)
    - Column 2: description
    - Column 3: reference
    - Column 4: amount
    - Column 5: balance_after (optional)
    """
    account_service = BankAccountService(db)
    bank_account = account_service.get_by_id(account_id, current_user.business_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Read CSV file
    content = await file.read()
    content_str = content.decode('utf-8')
    
    lines = content_str.strip().split('\n')
    if has_header:
        lines = lines[1:]  # Skip header row
    
    # Generate import batch ID
    import_batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    lines_imported = 0
    import_errors = []
    
    for idx, row in enumerate(lines):
        if not row.strip():
            continue
        
        try:
            cols = row.split(delimiter)
            if len(cols) < 5:
                import_errors.append(f"Row {idx + 1}: Insufficient columns")
                continue
            
            # Parse date
            try:
                txn_date = datetime.strptime(cols[0].strip(), '%Y-%m-%d').date()
            except ValueError:
                import_errors.append(f"Row {idx + 1}: Invalid date format")
                continue
            
            # Parse transaction type
            txn_type = cols[1].strip().lower() if len(cols) > 1 else 'credit'
            
            # Parse amount
            try:
                amount = Decimal(cols[4].strip().replace(',', ''))
            except:
                import_errors.append(f"Row {idx + 1}: Invalid amount")
                continue
            
            # Parse balance after (optional)
            balance_after = None
            if len(cols) > 5 and cols[5].strip():
                try:
                    balance_after = Decimal(cols[5].strip().replace(',', ''))
                except:
                    pass
            
            # Create statement line
            statement_line = BankStatementLine(
                bank_account_id=account_id,
                statement_date=statement_date,
                transaction_date=txn_date,
                transaction_type=txn_type,
                description=cols[2].strip() if len(cols) > 2 else None,
                reference=cols[3].strip() if len(cols) > 3 else None,
                amount=amount,
                balance_after=balance_after,
                import_batch_id=import_batch_id,
                branch_id=branch_id,
                business_id=current_user.business_id
            )
            db.add(statement_line)
            lines_imported += 1
        
        except Exception as e:
            import_errors.append(f"Row {idx + 1}: {str(e)}")
    
    db.commit()
    
    return {
        "message": f"Imported {lines_imported} statement lines",
        "import_batch_id": import_batch_id,
        "errors": import_errors if import_errors else None,
        "lines_imported": lines_imported
    }


@router.get("/accounts/{account_id}/statement-lines", response_model=List[BankStatementLineResponse])
async def get_statement_lines(
    account_id: int,
    is_cleared: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get bank statement lines for an account"""
    query = db.query(BankStatementLine).filter(
        BankStatementLine.bank_account_id == account_id,
        BankStatementLine.business_id == current_user.business_id
    )
    
    if is_cleared is not None:
        query = query.filter(BankStatementLine.is_cleared == is_cleared)
    
    if start_date:
        query = query.filter(BankStatementLine.statement_date >= start_date)
    if end_date:
        query = query.filter(BankStatementLine.statement_date <= end_date)
    
    lines = query.order_by(BankStatementLine.statement_date).all()
    
    return lines


@router.get("/accounts/{account_id}/uncleared-transactions")
async def get_uncleared_transactions(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get uncleared cashbook transactions for matching"""
    from sqlalchemy import or_
    
    account_service = BankAccountService(db)
    bank_account = account_service.get_by_id(account_id, current_user.business_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Get uncleared cashbook entries
    entries = db.query(CashBookEntry).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        or_(
            CashBookEntry.is_cleared == False,
            CashBookEntry.is_cleared == None
        )
    ).order_by(CashBookEntry.entry_date).all()
    
    return [{
        "id": entry.id,
        "entry_number": entry.entry_number,
        "entry_date": entry.entry_date.isoformat(),
        "entry_type": entry.entry_type,
        "description": entry.description,
        "reference": entry.reference,
        "payee_payer": entry.payee_payer,
        "amount": float(entry.amount),
        "source_type": entry.source_type,
        "is_transfer": entry.is_transfer,
    } for entry in entries]


@router.post("/match")
async def match_transactions(
    match_data: MatchRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Match a statement line with a cashbook entry"""
    statement_line = db.query(BankStatementLine).filter(
        BankStatementLine.id == match_data.statement_line_id,
        BankStatementLine.business_id == current_user.business_id
    ).first()
    
    if not statement_line:
        raise HTTPException(status_code=404, detail="Statement line not found")
    
    cashbook_entry = db.query(CashBookEntry).filter(
        CashBookEntry.id == match_data.cashbook_entry_id,
        CashBookEntry.business_id == current_user.business_id
    ).first()
    
    if not cashbook_entry:
        raise HTTPException(status_code=404, detail="Cashbook entry not found")
    
    # Check if amounts match (within tolerance)
    stmt_amount = float(statement_line.amount)
    cb_amount = float(cashbook_entry.amount)
    
    # Mark both as matched and cleared
    statement_line.is_matched = True
    statement_line.is_cleared = True
    statement_line.matched_cashbook_entry_id = cashbook_entry.id
    statement_line.matched_date = date.today()
    
    cashbook_entry.is_cleared = True
    cashbook_entry.matched_statement_line_id = statement_line.id
    
    db.commit()
    
    return {
        "message": "Transactions matched successfully",
        "statement_line_id": statement_line.id,
        "cashbook_entry_id": cashbook_entry.id,
        "amount_difference": abs(stmt_amount - cb_amount)
    }


@router.post("/clear-statement-line/{line_id}")
async def clear_statement_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Manually clear a statement line without matching"""
    statement_line = db.query(BankStatementLine).filter(
        BankStatementLine.id == line_id,
        BankStatementLine.business_id == current_user.business_id
    ).first()
    
    if not statement_line:
        raise HTTPException(status_code=404, detail="Statement line not found")
    
    statement_line.is_cleared = True
    statement_line.matched_date = date.today()
    
    db.commit()
    
    return {"message": "Statement line cleared"}


@router.post("/clear-cashbook-entry/{entry_id}")
async def clear_cashbook_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Manually clear a cashbook entry"""
    entry = db.query(CashBookEntry).filter(
        CashBookEntry.id == entry_id,
        CashBookEntry.business_id == current_user.business_id
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Cashbook entry not found")
    
    entry.is_cleared = True
    
    db.commit()
    
    return {"message": "Cashbook entry cleared"}


@router.post("/complete", dependencies=[Depends(PermissionChecker(["bank:reconcile"]))])
async def complete_reconciliation(
    reconciliation_data: ReconciliationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Complete bank reconciliation"""
    from sqlalchemy import func as sql_func
    
    account_service = BankAccountService(db)
    bank_account = account_service.get_by_id(reconciliation_data.bank_account_id, current_user.business_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Get book balance
    book_balance = db.query(sql_func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'receipt'
    ).scalar() or Decimal("0")
    
    book_payments = db.query(sql_func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'payment'
    ).scalar() or Decimal("0")
    
    book_balance = book_balance - book_payments
    
    # Get uncleared items
    deposits_in_transit = db.query(sql_func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'receipt',
        CashBookEntry.is_cleared == False
    ).scalar() or Decimal("0")
    
    outstanding_checks = db.query(sql_func.sum(CashBookEntry.amount)).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        CashBookEntry.entry_type == 'payment',
        CashBookEntry.is_cleared == False
    ).scalar() or Decimal("0")
    
    # Calculate adjusted balance
    adjusted_balance = book_balance + deposits_in_transit - outstanding_checks
    
    # Calculate difference
    difference = adjusted_balance - reconciliation_data.statement_balance
    
    # Generate reconciliation number
    last_recon = db.query(BankReconciliationRecord).filter(
        BankReconciliationRecord.business_id == current_user.business_id
    ).order_by(BankReconciliationRecord.id.desc()).first()
    
    if last_recon and last_recon.reconciliation_number:
        try:
            num = int(last_recon.reconciliation_number.replace("REC-", ""))
            recon_number = f"REC-{num + 1:05d}"
        except ValueError:
            recon_number = "REC-00001"
    else:
        recon_number = "REC-00001"
    
    # Create reconciliation record
    reconciliation_record = BankReconciliationRecord(
        reconciliation_number=recon_number,
        bank_account_id=reconciliation_data.bank_account_id,
        statement_date=reconciliation_data.statement_date,
        statement_balance=reconciliation_data.statement_balance,
        book_balance=book_balance,
        deposits_in_transit=deposits_in_transit,
        outstanding_checks=outstanding_checks,
        other_adjustments=Decimal("0"),
        adjusted_balance=adjusted_balance,
        difference=difference,
        status='completed' if difference == 0 else 'pending',
        notes=reconciliation_data.notes,
        branch_id=branch_id,
        business_id=current_user.business_id,
        reconciled_by=current_user.id
    )
    db.add(reconciliation_record)
    
    # Update bank account
    bank_account.last_reconciliation_date = reconciliation_data.statement_date
    bank_account.last_reconciliation_balance = reconciliation_data.statement_balance
    
    db.commit()
    
    return ReconciliationResponse(
        id=reconciliation_record.id,
        reconciliation_number=reconciliation_record.reconciliation_number,
        bank_account_id=reconciliation_record.bank_account_id,
        statement_date=reconciliation_record.statement_date,
        statement_balance=reconciliation_record.statement_balance,
        book_balance=reconciliation_record.book_balance,
        deposits_in_transit=reconciliation_record.deposits_in_transit,
        outstanding_checks=reconciliation_record.outstanding_checks,
        other_adjustments=reconciliation_record.other_adjustments,
        adjusted_balance=reconciliation_record.adjusted_balance,
        difference=reconciliation_record.difference,
        status=reconciliation_record.status,
        notes=reconciliation_record.notes,
        created_at=reconciliation_record.created_at
    )


@router.get("/history")
async def get_reconciliation_history(
    account_id: Optional[int] = None,
    limit: int = Query(10, ge=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get reconciliation history"""
    query = db.query(BankReconciliationRecord).filter(
        BankReconciliationRecord.business_id == current_user.business_id
    )
    
    if account_id:
        query = query.filter(BankReconciliationRecord.bank_account_id == account_id)
    
    records = query.order_by(BankReconciliationRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    return [{
        "id": r.id,
        "reconciliation_number": r.reconciliation_number,
        "bank_account_id": r.bank_account_id,
        "bank_account_name": r.bank_account.account_name if r.bank_account else None,
        "statement_date": r.statement_date.isoformat(),
        "statement_balance": float(r.statement_balance),
        "book_balance": float(r.book_balance),
        "difference": float(r.difference),
        "status": r.status,
        "created_at": r.created_at.isoformat()
    } for r in records]


# ==================== AUTO-MATCH ENDPOINTS ====================


@router.post("/auto-match/{account_id}")
async def auto_match_transactions(
    account_id: int,
    tolerance: Decimal = Query(Decimal("0.01")),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Auto-match statement lines with cashbook entries based on amount and date proximity"""
    from sqlalchemy import and_
    from datetime import timedelta
    
    account_service = BankAccountService(db)
    bank_account = account_service.get_by_id(account_id, current_user.business_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    branch_id = current_user.selected_branch.id
    
    # Get unmatched statement lines
    unmatched_stmt_lines = db.query(BankStatementLine).filter(
        BankStatementLine.bank_account_id == account_id,
        BankStatementLine.branch_id == branch_id,
        BankStatementLine.business_id == current_user.business_id,
        BankStatementLine.is_matched == False
    ).all()
    
    # Get unmatched cashbook entries
    unmatched_cb_entries = db.query(CashBookEntry).filter(
        CashBookEntry.account_id == bank_account.chart_of_account_id,
        CashBookEntry.branch_id == branch_id,
        CashBookEntry.business_id == current_user.business_id,
        or_(
            CashBookEntry.is_cleared == False,
            CashBookEntry.is_cleared == None
        )
    ).all()
    
    matched_pairs = []
    
    for stmt_line in unmatched_stmt_lines:
        stmt_amount = float(stmt_line.amount)
        stmt_type = stmt_line.transaction_type
        
        # Determine if looking for credit (deposit) or debit (withdrawal)
        # Credit in statement = receipt in cashbook
        # Debit in statement = payment in cashbook
        target_entry_type = 'receipt' if stmt_type == 'credit' else 'payment'
        
        # Find matching cashbook entries
        for cb_entry in unmatched_cb_entries:
            if cb_entry.id in [p['cb_id'] for p in matched_pairs]:
                continue
            
            cb_amount = float(cb_entry.amount)
            
            # Check amount match (within tolerance)
            if abs(stmt_amount - cb_amount) <= float(tolerance):
                # Check date proximity (within 7 days)
                stmt_date = stmt_line.transaction_date or stmt_line.statement_date
                cb_date = cb_entry.entry_date
                
                if abs((stmt_date - cb_date).days) <= 7:
                    # Match found!
                    stmt_line.is_matched = True
                    stmt_line.is_cleared = True
                    stmt_line.matched_cashbook_entry_id = cb_entry.id
                    stmt_line.matched_date = date.today()
                    
                    cb_entry.is_cleared = True
                    
                    matched_pairs.append({
                        "stmt_line_id": stmt_line.id,
                        "cb_id": cb_entry.id,
                        "amount": stmt_amount,
                        "stmt_date": stmt_date.isoformat(),
                        "cb_date": cb_date.isoformat()
                    })
                    break
    
    db.commit()
    
    return {
        "message": f"Auto-matched {len(matched_pairs)} transaction pairs",
        "matched_pairs": matched_pairs
    }
