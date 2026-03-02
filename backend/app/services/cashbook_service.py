"""
Cash Book Service - Central Hub for Cash/Bank Transactions
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from decimal import Decimal
from datetime import date, timedelta
from app.models import (
    CashBookEntry, Account, LedgerEntry, BankAccount,
    FundTransfer, Payment
)
from app.schemas import CashBookEntryCreate


class CashBookService:
    """Service for managing cash book entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_next_entry_number(self, business_id: int, entry_type: str) -> str:
        """Generate next entry number"""
        prefix = {
            "receipt": "CR",
            "payment": "CP",
            "transfer": "CT",
            "adjustment": "CA"
        }.get(entry_type, "CB")
        
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == business_id,
            CashBookEntry.entry_number.like(f'{prefix}-%')
        ).order_by(CashBookEntry.id.desc()).first()
        
        if last_entry:
            try:
                num = int(last_entry.entry_number.replace(f'{prefix}-', ''))
                return f'{prefix}-{num + 1:05d}'
            except ValueError:
                pass
        
        return f'{prefix}-00001'
    
    def create_entry(self, entry_data: CashBookEntryCreate, business_id: int, 
                    branch_id: int, user_id: int = None) -> CashBookEntry:
        """Create a cash book entry"""
        # Get current balance for the account
        current_balance = self._get_account_balance(entry_data.account_id, branch_id)
        
        # For payments and transfers out, check if sufficient balance exists
        if entry_data.entry_type == "payment" or (entry_data.entry_type == "transfer" and entry_data.transfer_direction == "out"):
            if current_balance < entry_data.amount:
                # Get account name for error message
                account = self.db.query(Account).filter(Account.id == entry_data.account_id).first()
                account_name = account.name if account else f"Account {entry_data.account_id}"
                raise ValueError(
                    f"Insufficient funds in '{account_name}'. "
                    f"Available balance: {float(current_balance):,.2f}, "
                    f"Transaction amount: {float(entry_data.amount):,.2f}"
                )
        
        # Calculate balance after entry
        if entry_data.entry_type in ["receipt", "transfer"] and entry_data.transfer_direction == "in":
            balance_after = current_balance + entry_data.amount
        elif entry_data.entry_type in ["payment", "transfer"] and entry_data.transfer_direction == "out":
            balance_after = current_balance - entry_data.amount
        else:
            # Default: receipt increases, payment decreases
            if entry_data.entry_type == "receipt":
                balance_after = current_balance + entry_data.amount
            elif entry_data.entry_type == "payment":
                balance_after = current_balance - entry_data.amount
            else:
                balance_after = current_balance
        
        entry_number = self.get_next_entry_number(business_id, entry_data.entry_type)
        
        entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=entry_data.entry_date,
            entry_type=entry_data.entry_type,
            account_id=entry_data.account_id,
            account_type=entry_data.account_type,
            amount=entry_data.amount,
            balance_after=balance_after,
            description=entry_data.description,
            reference=entry_data.reference,
            payee_payer=entry_data.payee_payer,
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            branch_id=branch_id,
            business_id=business_id,
            created_by=user_id
        )
        self.db.add(entry)
        self.db.flush()
        return entry
    
    def create_from_payment(self, payment: Payment, account_id: int, 
                           account_type: str, branch_id: int, business_id: int) -> CashBookEntry:
        """Create cash book entry from a sales payment"""
        invoice = payment.sales_invoice
        
        entry_data = CashBookEntryCreate(
            entry_date=payment.payment_date,
            entry_type="receipt",
            account_id=account_id,
            account_type=account_type,
            amount=payment.amount,
            description=f"Payment from {invoice.customer.name} - Invoice {invoice.invoice_number}",
            reference=payment.payment_number,
            payee_payer=invoice.customer.name,
            source_type="sales_payment",
            source_id=payment.id
        )
        return self.create_entry(entry_data, business_id, branch_id)
    
    def create_from_expense(self, expense, business_id: int, branch_id: int) -> CashBookEntry:
        """Create cash book entry from an expense"""
        entry_data = CashBookEntryCreate(
            entry_date=expense.expense_date,
            entry_type="payment",
            account_id=expense.paid_from_account_id,
            account_type="cash",  # Could be bank too
            amount=expense.amount,
            description=f"Expense: {expense.category} - {expense.description or ''}",
            reference=expense.expense_number,
            payee_payer=expense.vendor.name if expense.vendor else None,
            source_type="expense",
            source_id=expense.id
        )
        return self.create_entry(entry_data, business_id, branch_id)
    
    def create_from_other_income(self, income, business_id: int, branch_id: int) -> CashBookEntry:
        """Create cash book entry from other income"""
        entry_data = CashBookEntryCreate(
            entry_date=income.income_date,
            entry_type="receipt",
            account_id=income.received_in_account_id,
            account_type="cash",
            amount=income.amount,
            description=f"Income: {income.category} - {income.description or ''}",
            reference=income.income_number,
            payee_payer=income.customer.name if income.customer else None,
            source_type="other_income",
            source_id=income.id
        )
        return self.create_entry(entry_data, business_id, branch_id)
    
    def create_from_transfer(self, transfer: FundTransfer, direction: str,
                            business_id: int, branch_id: int) -> CashBookEntry:
        """Create cash book entry from fund transfer"""
        if direction == "out":
            account_id = transfer.from_coa_id
            account_type = transfer.from_account_type
            payee = transfer.to_account_name
        else:
            account_id = transfer.to_coa_id
            account_type = transfer.to_account_type
            payee = transfer.from_account_name
        
        entry_data = CashBookEntryCreate(
            entry_date=transfer.transfer_date,
            entry_type="transfer",
            account_id=account_id,
            account_type=account_type,
            amount=transfer.amount,
            description=f"Transfer: {transfer.description or ''}",
            reference=transfer.transfer_number,
            payee_payer=payee,
            source_type="transfer",
            source_id=transfer.id
        )
        entry = self.create_entry(entry_data, business_id, branch_id)
        entry.is_transfer = True
        entry.transfer_id = transfer.id
        entry.transfer_direction = direction
        self.db.flush()
        return entry
    
    def get_entries(self, business_id: int, branch_id: int = None,
                   start_date: date = None, end_date: date = None,
                   account_id: int = None, entry_type: str = None,
                   limit: int = 100, offset: int = 0) -> List[CashBookEntry]:
        """Get cash book entries with filters"""
        query = self.db.query(CashBookEntry).options(
            joinedload(CashBookEntry.account),
            joinedload(CashBookEntry.created_by_user)
        ).filter(CashBookEntry.business_id == business_id)
        
        if branch_id:
            query = query.filter(CashBookEntry.branch_id == branch_id)
        if start_date:
            query = query.filter(CashBookEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(CashBookEntry.entry_date <= end_date)
        if account_id:
            query = query.filter(CashBookEntry.account_id == account_id)
        if entry_type:
            query = query.filter(CashBookEntry.entry_type == entry_type)
        
        return query.order_by(
            CashBookEntry.entry_date.desc(),
            CashBookEntry.id.desc()
        ).offset(offset).limit(limit).all()
    
    def get_entry_by_id(self, entry_id: int, business_id: int) -> Optional[CashBookEntry]:
        """Get a single cash book entry"""
        return self.db.query(CashBookEntry).options(
            joinedload(CashBookEntry.account),
            joinedload(CashBookEntry.created_by_user),
            joinedload(CashBookEntry.transfer)
        ).filter(
            CashBookEntry.id == entry_id,
            CashBookEntry.business_id == business_id
        ).first()
    
    def _get_account_balance(self, account_id: int, branch_id: int = None) -> Decimal:
        """Get current balance for an account from ledger entries"""
        query = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(LedgerEntry.account_id == account_id)
        
        if branch_id:
            query = query.filter(LedgerEntry.branch_id == branch_id)
        
        result = query.scalar()
        return result or Decimal("0")
    
    def get_account_summary(self, account_id: int, account_name: str,
                           account_type: str, branch_id: int,
                           start_date: date = None, end_date: date = None,
                           bank_account_id: int = None,
                           bank_opening_balance: Decimal = None) -> Dict:
        """Get summary for a specific account
        
        Args:
            account_id: Chart of Account ID
            account_name: Display name for the account
            account_type: 'bank' or 'cash'
            branch_id: Branch ID filter
            start_date: Start date for the period
            end_date: End date for the period
            bank_account_id: Optional BankAccount ID for filtering ledger entries
            bank_opening_balance: Optional opening balance from BankAccount record
        """
        # Get opening balance (balance before start_date)
        opening_balance = Decimal("0")
        ledger_balance_before = Decimal("0")  # Initialize for later use
        
        # For bank accounts with stored opening balance, use it as the base
        if bank_opening_balance is not None and bank_account_id is not None:
            opening_balance = bank_opening_balance
        
        if start_date:
            # Query ledger entries before start_date
            # For bank accounts, filter by bank_account_id to get only this account's entries
            query = self.db.query(
                func.sum(LedgerEntry.debit - LedgerEntry.credit)
            ).filter(
                LedgerEntry.account_id == account_id,
                LedgerEntry.transaction_date < start_date
            )
            if branch_id:
                query = query.filter(LedgerEntry.branch_id == branch_id)
            if bank_account_id:
                query = query.filter(LedgerEntry.bank_account_id == bank_account_id)
            
            ledger_balance_before = query.scalar() or Decimal("0")
            
            # For bank accounts: use the greater of stored opening_balance or ledger balance
            # This handles cases where opening balance was recorded after start_date
            if bank_opening_balance is not None and bank_account_id is not None:
                # If ledger has entries before start_date, use that (more accurate)
                # Otherwise fall back to stored opening balance
                if ledger_balance_before > Decimal("0"):
                    opening_balance = ledger_balance_before
                # else: keep the stored bank_opening_balance
            else:
                # For cash accounts, just use ledger balance
                opening_balance = ledger_balance_before
        
        # Get entries for the period
        query = self.db.query(CashBookEntry).filter(
            CashBookEntry.account_id == account_id
        )
        if branch_id:
            query = query.filter(CashBookEntry.branch_id == branch_id)
        if start_date:
            query = query.filter(CashBookEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(CashBookEntry.entry_date <= end_date)
        
        entries = query.all()
        
        # For bank accounts with stored opening balance, we need to check if the
        # opening balance entry falls within this period and exclude it to avoid double counting
        exclude_opening_balance = False
        if bank_opening_balance is not None and bank_opening_balance > 0 and bank_account_id is not None:
            # Check if opening balance entry exists in this period
            opening_entry_in_period = any(
                e.source_type == "opening_balance" and 
                e.entry_type == "receipt" 
                for e in entries
            )
            # If opening balance entry is in the period, we exclude it from receipts
            # because we already included it in the opening_balance value
            exclude_opening_balance = opening_entry_in_period and (ledger_balance_before == Decimal("0"))
        
        # Calculate receipts and payments
        total_receipts = sum(e.amount for e in entries if (
            e.entry_type == "receipt" or 
            (e.entry_type == "transfer" and e.transfer_direction == "in")
        ) and (not exclude_opening_balance or e.source_type != "opening_balance"))
        
        total_payments = sum(e.amount for e in entries if (
            e.entry_type == "payment" or 
            (e.entry_type == "transfer" and e.transfer_direction == "out")
        ))
        
        closing_balance = opening_balance + total_receipts - total_payments
        
        return {
            "account_id": account_id,
            "account_name": account_name,
            "account_type": account_type,
            "opening_balance": opening_balance,
            "total_receipts": total_receipts,
            "total_payments": total_payments,
            "closing_balance": closing_balance,
            "entries_count": len(entries)
        }
    
    def get_cash_book_summary(self, business_id: int, branch_id: int = None,
                             start_date: date = None, end_date: date = None) -> List[Dict]:
        """Get summary for all cash/bank accounts"""
        summaries = []
        
        # Get all payment accounts (bank + cash)
        from app.services.banking_service import BankAccountService
        bank_service = BankAccountService(self.db)
        
        # Get bank accounts
        bank_accounts = bank_service.get_all_by_business(business_id)
        for ba in bank_accounts:
            if branch_id and ba.branch_id != branch_id:
                continue
            if ba.chart_of_account_id:
                summary = self.get_account_summary(
                    ba.chart_of_account_id,
                    ba.account_name,
                    "bank",
                    branch_id or ba.branch_id,
                    start_date,
                    end_date,
                    bank_account_id=ba.id,
                    bank_opening_balance=ba.opening_balance
                )
                summaries.append(summary)
        
        # Get cash accounts from COA
        cash_accounts = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name.ilike('%cash%'),
            Account.is_active == True
        ).all()
        
        for ca in cash_accounts:
            # Skip if already covered by bank accounts
            if any(ba.chart_of_account_id == ca.id for ba in bank_accounts):
                continue
            
            summary = self.get_account_summary(
                ca.id,
                ca.name,
                "cash",
                branch_id,
                start_date,
                end_date
            )
            summaries.append(summary)
        
        return summaries
    
    def get_cash_flow_summary(self, business_id: int, branch_id: int = None,
                             start_date: date = None, end_date: date = None) -> Dict:
        """Get overall cash flow summary"""
        query = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == business_id
        )
        
        if branch_id:
            query = query.filter(CashBookEntry.branch_id == branch_id)
        if start_date:
            query = query.filter(CashBookEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(CashBookEntry.entry_date <= end_date)
        
        entries = query.all()
        
        # Group by source type
        by_source = {}
        for entry in entries:
            source = entry.source_type or "manual"
            if source not in by_source:
                by_source[source] = {
                    "receipts": Decimal("0"),
                    "payments": Decimal("0"),
                    "count": 0
                }
            
            if entry.entry_type in ["receipt"] or (entry.entry_type == "transfer" and entry.transfer_direction == "in"):
                by_source[source]["receipts"] += entry.amount
            elif entry.entry_type in ["payment"] or (entry.entry_type == "transfer" and entry.transfer_direction == "out"):
                by_source[source]["payments"] += entry.amount
            by_source[source]["count"] += 1
        
        # Total receipts and payments
        total_receipts = sum(e.amount for e in entries if e.entry_type == "receipt" or 
                           (e.entry_type == "transfer" and e.transfer_direction == "in"))
        total_payments = sum(e.amount for e in entries if e.entry_type == "payment" or 
                           (e.entry_type == "transfer" and e.transfer_direction == "out"))
        
        return {
            "total_receipts": total_receipts,
            "total_payments": total_payments,
            "net_cash_flow": total_receipts - total_payments,
            "total_entries": len(entries),
            "by_source": by_source,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    def delete_entry(self, entry_id: int, business_id: int) -> bool:
        """Delete a cash book entry (only manual entries)"""
        entry = self.get_entry_by_id(entry_id, business_id)
        if not entry:
            return False
        
        # Only allow deletion of manual entries
        if entry.source_type and entry.source_type != "manual":
            return False
        
        self.db.delete(entry)
        return True
    
    def reconcile_with_ledger(self, account_id: int, branch_id: int,
                             as_of_date: date = None) -> Dict:
        """Reconcile cash book with ledger entries"""
        # Get ledger balance
        ledger_query = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(LedgerEntry.account_id == account_id)
        
        if branch_id:
            ledger_query = ledger_query.filter(LedgerEntry.branch_id == branch_id)
        if as_of_date:
            ledger_query = ledger_query.filter(LedgerEntry.transaction_date <= as_of_date)
        
        ledger_balance = ledger_query.scalar() or Decimal("0")
        
        # Get cash book balance
        cb_query = self.db.query(CashBookEntry).filter(
            CashBookEntry.account_id == account_id
        )
        
        if branch_id:
            cb_query = cb_query.filter(CashBookEntry.branch_id == branch_id)
        if as_of_date:
            cb_query = cb_query.filter(CashBookEntry.entry_date <= as_of_date)
        
        entries = cb_query.order_by(CashBookEntry.entry_date.desc()).first()
        cash_book_balance = entries.balance_after if entries else Decimal("0")
        
        return {
            "account_id": account_id,
            "as_of_date": as_of_date,
            "ledger_balance": ledger_balance,
            "cash_book_balance": cash_book_balance,
            "difference": ledger_balance - cash_book_balance,
            "is_reconciled": ledger_balance == cash_book_balance
        }
