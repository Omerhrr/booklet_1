"""
Other Income Service - Manage non-sales income (interest, rent, dividends, etc.)
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models import OtherIncome, Account, AccountType, LedgerEntry, Customer, CashBookEntry


class OtherIncomeService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, income_id: int, business_id: int, branch_id: int = None) -> Optional[OtherIncome]:
        """Get other income by ID"""
        query = self.db.query(OtherIncome).filter(
            OtherIncome.id == income_id,
            OtherIncome.business_id == business_id
        )
        if branch_id:
            query = query.filter(OtherIncome.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, category: str = None, 
                      start_date: date = None, end_date: date = None) -> List[OtherIncome]:
        """Get all other incomes for a branch with optional filters"""
        query = self.db.query(OtherIncome).filter(
            OtherIncome.branch_id == branch_id,
            OtherIncome.business_id == business_id
        )
        
        if category:
            query = query.filter(OtherIncome.category.ilike(f"%{category}%"))
        if start_date:
            query = query.filter(OtherIncome.income_date >= start_date)
        if end_date:
            query = query.filter(OtherIncome.income_date <= end_date)
        
        return query.order_by(OtherIncome.income_date.desc(), OtherIncome.id.desc()).all()
    
    def get_by_business(self, business_id: int) -> List[OtherIncome]:
        """Get all other incomes for a business"""
        query = self.db.query(OtherIncome).filter(OtherIncome.business_id == business_id)
        return query.order_by(OtherIncome.income_date.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        """Get next income number"""
        last_income = self.db.query(OtherIncome).filter(
            OtherIncome.business_id == business_id
        ).order_by(OtherIncome.id.desc()).first()
        
        if last_income:
            try:
                num = int(last_income.income_number.replace("INC-", ""))
                return f"INC-{num + 1:05d}"
            except ValueError:
                pass
        
        return "INC-00001"
    
    def create(self, income_data, business_id: int, branch_id: int) -> OtherIncome:
        """Create a new other income with ledger entries and cash book entry"""
        # Calculate total amount
        sub_total = income_data.sub_total
        vat_amount = income_data.vat_amount or Decimal("0.00")
        total_amount = sub_total + vat_amount
        
        # Get income account (revenue type account to record the income)
        income_account = self.db.query(Account).filter(
            Account.id == income_data.income_account_id,
            Account.business_id == business_id
        ).first()
        
        if not income_account:
            raise ValueError("Invalid income account")
        
        # Get receiving account (cash/bank account to receive funds)
        receiving_account = self.db.query(Account).filter(
            Account.id == income_data.received_in_account_id,
            Account.business_id == business_id
        ).first()
        
        if not receiving_account:
            raise ValueError("Invalid receiving account")
        
        # Create other income record
        income = OtherIncome(
            income_number=self.get_next_number(business_id),
            income_date=income_data.income_date,
            category=income_data.category,
            description=income_data.description,
            sub_total=sub_total,
            vat_amount=vat_amount,
            amount=total_amount,
            customer_id=income_data.customer_id,
            received_in_account_id=income_data.received_in_account_id,
            income_account_id=income_data.income_account_id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(income)
        self.db.flush()
        
        # Create ledger entries for double-entry accounting
        # Debit the receiving account (increases cash/bank)
        debit_entry = LedgerEntry(
            transaction_date=income_data.income_date,
            description=f"Income: {income_data.category} - {income_data.description or ''}",
            reference=income.income_number,
            debit=total_amount,
            credit=Decimal("0.00"),
            account_id=income_data.received_in_account_id,
            other_income_id=income.id,
            branch_id=branch_id
        )
        self.db.add(debit_entry)
        
        # Credit the income account (increases revenue)
        credit_entry = LedgerEntry(
            transaction_date=income_data.income_date,
            description=f"Income: {income_data.category} - {income_data.description or ''}",
            reference=income.income_number,
            debit=Decimal("0.00"),
            credit=total_amount,
            account_id=income_data.income_account_id,
            other_income_id=income.id,
            branch_id=branch_id
        )
        self.db.add(credit_entry)
        
        # Create CashBook entry
        self._create_cashbook_entry(income, receiving_account, branch_id, business_id)
        
        self.db.flush()
        return income
    
    def _create_cashbook_entry(self, income: OtherIncome, receiving_account: Account, 
                               branch_id: int, business_id: int):
        """Create a cash book entry for other income"""
        from app.models import CashBookEntry
        from sqlalchemy import func as sql_func
        
        # Determine account type (cash or bank)
        account_type = "cash"
        if hasattr(receiving_account, 'bank_accounts') and receiving_account.bank_accounts:
            account_type = "bank"
        elif receiving_account.name and 'bank' in receiving_account.name.lower():
            account_type = "bank"
        
        # Get current balance from ledger
        current_balance = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(
            LedgerEntry.account_id == receiving_account.id,
            LedgerEntry.branch_id == branch_id
        ).scalar() or Decimal("0")
        
        # Generate entry number
        prefix = "CR"  # Cash Receipt
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
        
        # Create cash book entry
        cashbook_entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=income.income_date,
            entry_type="receipt",
            account_id=receiving_account.id,
            account_type=account_type,
            amount=income.amount,
            balance_after=current_balance,
            description=f"Other Income: {income.category} - {income.description or ''}",
            reference=income.income_number,
            payee_payer=income.customer.name if income.customer else income.category,
            source_type="other_income",
            source_id=income.id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(cashbook_entry)
    
    def update(self, income_id: int, business_id: int, branch_id: int, income_data) -> Optional[OtherIncome]:
        """Update an other income"""
        income = self.get_by_id(income_id, business_id, branch_id)
        if not income:
            return None
        
        # Update fields
        income.income_date = income_data.income_date
        income.category = income_data.category
        income.description = income_data.description
        income.sub_total = income_data.sub_total
        income.vat_amount = income_data.vat_amount or Decimal("0.00")
        income.amount = income_data.sub_total + (income_data.vat_amount or Decimal("0.00"))
        income.customer_id = income_data.customer_id
        income.received_in_account_id = income_data.received_in_account_id
        income.income_account_id = income_data.income_account_id
        
        self.db.flush()
        return income
    
    def delete(self, income_id: int, business_id: int, branch_id: int = None) -> bool:
        """Delete an other income"""
        income = self.get_by_id(income_id, business_id, branch_id)
        if not income:
            return False
        
        # Delete associated ledger entries
        self.db.query(LedgerEntry).filter(LedgerEntry.other_income_id == income.id).delete()
        
        self.db.delete(income)
        return True
    
    def get_categories(self, business_id: int) -> List[str]:
        """Get list of income categories used by the business"""
        results = self.db.query(OtherIncome.category).filter(
            OtherIncome.business_id == business_id
        ).distinct().all()
        return [r[0] for r in results]
    
    def get_income_summary(self, business_id: int, branch_id: int, 
                           start_date: date = None, end_date: date = None) -> Dict:
        """Get income summary by category"""
        query = self.db.query(
            OtherIncome.category,
            func.sum(OtherIncome.amount).label("total")
        ).filter(
            OtherIncome.business_id == business_id,
            OtherIncome.branch_id == branch_id
        )
        
        if start_date:
            query = query.filter(OtherIncome.income_date >= start_date)
        if end_date:
            query = query.filter(OtherIncome.income_date <= end_date)
        
        results = query.group_by(OtherIncome.category).all()
        
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
    
    def get_customer(self, customer_id: int, business_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.business_id == business_id
        ).first()
