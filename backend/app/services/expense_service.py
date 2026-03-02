"""
Expense Service - Manage business expenses
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models import Expense, Account, AccountType, LedgerEntry, Vendor


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_account_balance(self, account_id: int, branch_id: int) -> Decimal:
        """Get current balance of a cash/bank account from ledger entries"""
        from app.models import LedgerEntry as LE
        
        balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == account_id,
            LE.branch_id == branch_id
        ).scalar() or Decimal("0")
        
        return balance
    
    def get_by_id(self, expense_id: int, business_id: int, branch_id: int = None) -> Optional[Expense]:
        """Get expense by ID"""
        query = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.business_id == business_id
        )
        if branch_id:
            query = query.filter(Expense.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, category: str = None, 
                      start_date: date = None, end_date: date = None) -> List[Expense]:
        """Get all expenses for a branch with optional filters"""
        query = self.db.query(Expense).filter(
            Expense.branch_id == branch_id,
            Expense.business_id == business_id
        )
        
        if category:
            query = query.filter(Expense.category.ilike(f"%{category}%"))
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        return query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()
    
    def get_by_business(self, business_id: int, include_inactive: bool = True) -> List[Expense]:
        """Get all expenses for a business"""
        query = self.db.query(Expense).filter(Expense.business_id == business_id)
        return query.order_by(Expense.expense_date.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        """Get next expense number"""
        last_expense = self.db.query(Expense).filter(
            Expense.business_id == business_id
        ).order_by(Expense.id.desc()).first()
        
        if last_expense:
            try:
                num = int(last_expense.expense_number.replace("EXP-", ""))
                return f"EXP-{num + 1:05d}"
            except ValueError:
                pass
        
        return "EXP-00001"
    
    def create(self, expense_data, business_id: int, branch_id: int) -> Expense:
        """Create a new expense with ledger entries"""
        # Calculate total amount
        sub_total = expense_data.sub_total
        vat_amount = expense_data.vat_amount or Decimal("0.00")
        total_amount = sub_total + vat_amount
        
        # Get expense account (expense type account to record the expense)
        expense_account = self.db.query(Account).filter(
            Account.id == expense_data.expense_account_id,
            Account.business_id == business_id
        ).first()
        
        if not expense_account:
            raise ValueError("Invalid expense account")
        
        # Get payment account (cash/bank account to deduct from)
        payment_account = self.db.query(Account).filter(
            Account.id == expense_data.paid_from_account_id,
            Account.business_id == business_id
        ).first()
        
        if not payment_account:
            raise ValueError("Invalid payment account")
        
        # Check if payment account has sufficient balance
        current_balance = self._get_account_balance(payment_account.id, branch_id)
        if current_balance < total_amount:
            raise ValueError(
                f"Insufficient funds in '{payment_account.name}'. "
                f"Available balance: {float(current_balance):,.2f}, "
                f"Expense amount: {float(total_amount):,.2f}"
            )
        
        # Create expense record
        expense = Expense(
            expense_number=self.get_next_number(business_id),
            expense_date=expense_data.expense_date,
            category=expense_data.category,
            description=expense_data.description,
            sub_total=sub_total,
            vat_amount=vat_amount,
            amount=total_amount,
            vendor_id=expense_data.vendor_id,
            paid_from_account_id=expense_data.paid_from_account_id,
            expense_account_id=expense_data.expense_account_id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(expense)
        self.db.flush()
        
        # Create ledger entries for double-entry accounting
        # Debit the expense account for sub_total only (increases expense)
        debit_entry = LedgerEntry(
            transaction_date=expense_data.expense_date,
            description=f"Expense: {expense_data.category} - {expense_data.description or ''}",
            reference=expense.expense_number,
            debit=sub_total,  # Only sub_total, not total
            credit=Decimal("0.00"),
            account_id=expense_data.expense_account_id,
            expense_id=expense.id,
            branch_id=branch_id
        )
        self.db.add(debit_entry)
        
        # If VAT exists, debit VAT Receivable account
        if vat_amount > 0:
            vat_account = self._get_or_create_vat_account(business_id, branch_id)
            vat_entry = LedgerEntry(
                transaction_date=expense_data.expense_date,
                description=f"VAT on Expense: {expense_data.category}",
                reference=expense.expense_number,
                debit=vat_amount,
                credit=Decimal("0.00"),
                account_id=vat_account.id,
                expense_id=expense.id,
                branch_id=branch_id
            )
            self.db.add(vat_entry)
        
        # Credit the payment account (decreases cash/bank)
        credit_entry = LedgerEntry(
            transaction_date=expense_data.expense_date,
            description=f"Expense: {expense_data.category} - {expense_data.description or ''}",
            reference=expense.expense_number,
            debit=Decimal("0.00"),
            credit=total_amount,
            account_id=expense_data.paid_from_account_id,
            expense_id=expense.id,
            branch_id=branch_id
        )
        self.db.add(credit_entry)
        
        # Create CashBook entry for the expense
        self._create_cashbook_entry(expense, payment_account, branch_id, business_id)
        
        self.db.flush()
        return expense
    
    def _get_or_create_vat_account(self, business_id: int, branch_id: int) -> Account:
        """Get or create VAT Receivable account"""
        vat_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "VAT Receivable"
        ).first()
        
        if not vat_account:
            vat_account = Account(
                name="VAT Receivable",
                code="1300",
                type="Asset",
                description="VAT recoverable on purchases",
                business_id=business_id,
                is_active=True
            )
            self.db.add(vat_account)
            self.db.flush()
        
        return vat_account
    
    def _create_cashbook_entry(self, expense: Expense, payment_account: Account, 
                                branch_id: int, business_id: int):
        """Create a cash book entry for expense payment"""
        from app.models import CashBookEntry
        from sqlalchemy import func as sql_func
        
        # Determine account type (cash or bank)
        account_type = "cash"
        if hasattr(payment_account, 'bank_accounts') and payment_account.bank_accounts:
            account_type = "bank"
        elif payment_account.name and 'bank' in payment_account.name.lower():
            account_type = "bank"
        
        # Get current balance
        receipts = self.db.query(
            sql_func.sum(CashBookEntry.amount)
        ).filter(
            CashBookEntry.account_id == payment_account.id,
            CashBookEntry.branch_id == branch_id,
            CashBookEntry.business_id == business_id,
            CashBookEntry.entry_type == 'receipt'
        ).scalar() or Decimal("0")
        
        payments = self.db.query(
            sql_func.sum(CashBookEntry.amount)
        ).filter(
            CashBookEntry.account_id == payment_account.id,
            CashBookEntry.branch_id == branch_id,
            CashBookEntry.business_id == business_id,
            CashBookEntry.entry_type == 'payment'
        ).scalar() or Decimal("0")
        
        balance_after = receipts - payments - expense.amount
        
        # Generate entry number
        prefix = "CP"  # Cash Payment
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == business_id,
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
        
        cashbook_entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=expense.expense_date,
            entry_type="payment",
            account_id=payment_account.id,
            account_type=account_type,
            amount=expense.amount,
            balance_after=balance_after,
            description=f"Expense: {expense.category} - {expense.description or ''}",
            reference=expense.expense_number,
            payee_payer=expense.vendor.name if expense.vendor else expense.category,
            source_type="expense",
            source_id=expense.id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(cashbook_entry)
    
    def update(self, expense_id: int, business_id: int, branch_id: int, expense_data) -> Optional[Expense]:
        """Update an expense and its ledger entries"""
        expense = self.get_by_id(expense_id, business_id, branch_id)
        if not expense:
            return None
        
        # Calculate new totals
        new_sub_total = expense_data.sub_total
        new_vat = expense_data.vat_amount or Decimal("0.00")
        new_total = new_sub_total + new_vat
        
        # Check if payment account has sufficient balance for the new amount
        payment_account = self.db.query(Account).filter(
            Account.id == expense_data.paid_from_account_id,
            Account.business_id == business_id
        ).first()
        
        if not payment_account:
            raise ValueError("Invalid payment account")
        
        # Calculate the difference in amount
        amount_difference = new_total - expense.amount
        
        if amount_difference > 0:
            # Need to check if there's enough balance for the increase
            current_balance = self._get_account_balance(payment_account.id, branch_id)
            if current_balance < amount_difference:
                raise ValueError(
                    f"Insufficient funds for the increase. "
                    f"Additional amount: {float(amount_difference):,.2f}, "
                    f"Available balance: {float(current_balance):,.2f}"
                )
        
        # Delete old ledger entries
        self.db.query(LedgerEntry).filter(LedgerEntry.expense_id == expense.id).delete()
        
        # Delete old cashbook entry if exists
        from app.models import CashBookEntry
        self.db.query(CashBookEntry).filter(
            CashBookEntry.source_type == "expense",
            CashBookEntry.source_id == expense.id
        ).delete()
        
        # Update expense fields
        expense.expense_date = expense_data.expense_date
        expense.category = expense_data.category
        expense.description = expense_data.description
        expense.sub_total = new_sub_total
        expense.vat_amount = new_vat
        expense.amount = new_total
        expense.vendor_id = expense_data.vendor_id
        expense.paid_from_account_id = expense_data.paid_from_account_id
        expense.expense_account_id = expense_data.expense_account_id
        
        # Recreate ledger entries
        # Debit expense account
        debit_entry = LedgerEntry(
            transaction_date=expense_data.expense_date,
            description=f"Expense: {expense_data.category} - {expense_data.description or ''}",
            reference=expense.expense_number,
            debit=new_sub_total,
            credit=Decimal("0.00"),
            account_id=expense_data.expense_account_id,
            expense_id=expense.id,
            branch_id=branch_id
        )
        self.db.add(debit_entry)
        
        # If VAT exists, debit VAT Receivable account
        if new_vat > 0:
            vat_account = self._get_or_create_vat_account(business_id, branch_id)
            vat_entry = LedgerEntry(
                transaction_date=expense_data.expense_date,
                description=f"VAT on Expense: {expense_data.category}",
                reference=expense.expense_number,
                debit=new_vat,
                credit=Decimal("0.00"),
                account_id=vat_account.id,
                expense_id=expense.id,
                branch_id=branch_id
            )
            self.db.add(vat_entry)
        
        # Credit payment account
        credit_entry = LedgerEntry(
            transaction_date=expense_data.expense_date,
            description=f"Expense: {expense_data.category} - {expense_data.description or ''}",
            reference=expense.expense_number,
            debit=Decimal("0.00"),
            credit=new_total,
            account_id=expense_data.paid_from_account_id,
            expense_id=expense.id,
            branch_id=branch_id
        )
        self.db.add(credit_entry)
        
        # Recreate cashbook entry
        self._create_cashbook_entry(expense, payment_account, branch_id, business_id)
        
        self.db.flush()
        return expense
    
    def delete(self, expense_id: int, business_id: int, branch_id: int = None) -> bool:
        """Delete an expense"""
        expense = self.get_by_id(expense_id, business_id, branch_id)
        if not expense:
            return False
        
        # Delete associated ledger entries
        self.db.query(LedgerEntry).filter(LedgerEntry.expense_id == expense.id).delete()
        
        self.db.delete(expense)
        return True
    
    def get_categories(self, business_id: int) -> List[str]:
        """Get list of expense categories used by the business"""
        results = self.db.query(Expense.category).filter(
            Expense.business_id == business_id
        ).distinct().all()
        return [r[0] for r in results]
    
    def get_expense_summary(self, business_id: int, branch_id: int, 
                            start_date: date = None, end_date: date = None) -> Dict:
        """Get expense summary by category"""
        query = self.db.query(
            Expense.category,
            func.sum(Expense.amount).label("total")
        ).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id
        )
        
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        results = query.group_by(Expense.category).all()
        
        categories = []
        total = Decimal("0.00")
        for r in results:
            categories.append({
                "category": r.category,
                "total": float(r.total)
            })
            total += r.total
        
        return {
            "categories": categories,
            "total": float(total)
        }
    
    def get_vendor(self, vendor_id: int, business_id: int) -> Optional[Vendor]:
        """Get vendor by ID"""
        return self.db.query(Vendor).filter(
            Vendor.id == vendor_id,
            Vendor.business_id == business_id
        ).first()
