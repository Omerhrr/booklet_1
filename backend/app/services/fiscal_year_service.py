"""
Fiscal Year Service - Manage accounting periods and year-end processes
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from app.models import (
    FiscalYear, FiscalPeriod, OpeningBalanceEntry, ClosingEntry,
    Account, LedgerEntry, JournalVoucher, Business,
    BankReconciliationAdjustment, BankAccount
)


class FiscalYearService:
    """Service for managing fiscal years and periods"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, fiscal_year_id: int, business_id: int) -> Optional[FiscalYear]:
        return self.db.query(FiscalYear).options(
            joinedload(FiscalYear.periods)
        ).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.business_id == business_id
        ).first()
    
    def get_by_business(self, business_id: int) -> List[FiscalYear]:
        return self.db.query(FiscalYear).options(
            joinedload(FiscalYear.periods)
        ).filter(
            FiscalYear.business_id == business_id
        ).order_by(FiscalYear.start_date.desc()).all()
    
    def get_current(self, business_id: int) -> Optional[FiscalYear]:
        return self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id,
            FiscalYear.is_current == True,
            FiscalYear.is_closed == False
        ).first()
    
    def get_by_date(self, business_id: int, target_date: date) -> Optional[FiscalYear]:
        """Get the fiscal year that contains the given date"""
        return self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id,
            FiscalYear.start_date <= target_date,
            FiscalYear.end_date >= target_date
        ).first()
    
    def create(self, name: str, start_date: date, end_date: date, 
               business_id: int, auto_create_periods: bool = True,
               period_type: str = 'monthly') -> FiscalYear:
        """Create a new fiscal year with optional automatic period creation"""
        
        # Validate date range
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        # Check for overlapping fiscal years
        overlapping = self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id,
            and_(
                FiscalYear.start_date < end_date,
                FiscalYear.end_date > start_date
            )
        ).first()
        
        if overlapping:
            raise ValueError(f"Fiscal year overlaps with existing fiscal year: {overlapping.name}")
        
        # Check if this is the first fiscal year
        existing_years = self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id
        ).count()
        
        is_first = existing_years == 0
        
        fiscal_year = FiscalYear(
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_current=is_first,  # First fiscal year is automatically current
            business_id=business_id
        )
        self.db.add(fiscal_year)
        self.db.flush()
        
        # Auto-create periods if requested
        if auto_create_periods:
            self._create_periods(fiscal_year, period_type)
        
        return fiscal_year
    
    def _create_periods(self, fiscal_year: FiscalYear, period_type: str = 'monthly'):
        """Create fiscal periods for the fiscal year"""
        periods = []
        
        if period_type == 'monthly':
            # Create 12 monthly periods
            current_date = fiscal_year.start_date
            period_num = 1
            
            while current_date < fiscal_year.end_date:
                # Calculate month end
                month_end = current_date + relativedelta(months=1) - relativedelta(days=1)
                if month_end > fiscal_year.end_date:
                    month_end = fiscal_year.end_date
                
                period = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id,
                    period_number=period_num,
                    name=current_date.strftime("%B %Y"),
                    start_date=current_date,
                    end_date=month_end,
                    is_adjustment_period=False
                )
                periods.append(period)
                
                current_date = month_end + relativedelta(days=1)
                period_num += 1
        
        elif period_type == 'quarterly':
            # Create 4 quarterly periods
            current_date = fiscal_year.start_date
            for q in range(1, 5):
                quarter_end = current_date + relativedelta(months=3) - relativedelta(days=1)
                if quarter_end > fiscal_year.end_date:
                    quarter_end = fiscal_year.end_date
                
                period = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id,
                    period_number=q,
                    name=f"Q{q} {fiscal_year.name}",
                    start_date=current_date,
                    end_date=quarter_end,
                    is_adjustment_period=False
                )
                periods.append(period)
                
                current_date = quarter_end + relativedelta(days=1)
        
        # Add adjustment period at year end
        adjustment_period = FiscalPeriod(
            fiscal_year_id=fiscal_year.id,
            period_number=len(periods) + 1,
            name=f"Year-End Adjustments {fiscal_year.name}",
            start_date=fiscal_year.end_date,
            end_date=fiscal_year.end_date,
            is_adjustment_period=True
        )
        periods.append(adjustment_period)
        
        self.db.add_all(periods)
        self.db.flush()
        
        return periods
    
    def set_current(self, fiscal_year_id: int, business_id: int) -> FiscalYear:
        """Set a fiscal year as the current active year"""
        fiscal_year = self.get_by_id(fiscal_year_id, business_id)
        if not fiscal_year:
            raise ValueError("Fiscal year not found")
        
        if fiscal_year.is_closed:
            raise ValueError("Cannot set a closed fiscal year as current")
        
        # Unset current flag on all other fiscal years
        self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id
        ).update({"is_current": False})
        
        fiscal_year.is_current = True
        self.db.flush()
        
        return fiscal_year
    
    def close_period(self, period_id: int, business_id: int, user_id: int) -> FiscalPeriod:
        """Close a fiscal period"""
        period = self.db.query(FiscalPeriod).join(FiscalYear).filter(
            FiscalPeriod.id == period_id,
            FiscalYear.business_id == business_id
        ).first()
        
        if not period:
            raise ValueError("Period not found")
        
        if period.is_closed:
            raise ValueError("Period is already closed")
        
        period.is_closed = True
        period.closed_at = datetime.utcnow()
        period.closed_by = user_id
        
        self.db.flush()
        return period
    
    def close_year(self, fiscal_year_id: int, business_id: int, user_id: int,
                   close_income_summary: bool = True) -> FiscalYear:
        """Close a fiscal year and optionally transfer income/expense to retained earnings"""
        fiscal_year = self.get_by_id(fiscal_year_id, business_id)
        if not fiscal_year:
            raise ValueError("Fiscal year not found")
        
        if fiscal_year.is_closed:
            raise ValueError("Fiscal year is already closed")
        
        # Close all open periods
        for period in fiscal_year.periods:
            if not period.is_closed:
                period.is_closed = True
                period.closed_at = datetime.utcnow()
                period.closed_by = user_id
        
        # Close income and expense accounts if requested
        if close_income_summary:
            self._close_temporary_accounts(fiscal_year, user_id)
        
        fiscal_year.is_closed = True
        fiscal_year.is_current = False
        fiscal_year.closed_at = datetime.utcnow()
        fiscal_year.closed_by = user_id
        
        # Set next fiscal year as current if exists
        next_year = self.db.query(FiscalYear).filter(
            FiscalYear.business_id == business_id,
            FiscalYear.start_date > fiscal_year.end_date
        ).order_by(FiscalYear.start_date).first()
        
        if next_year:
            next_year.is_current = True
        
        self.db.flush()
        return fiscal_year
    
    def _close_temporary_accounts(self, fiscal_year: FiscalYear, user_id: int):
        """Close revenue and expense accounts by transferring balances to retained earnings"""
        
        # Get all revenue accounts
        revenue_accounts = self.db.query(Account).filter(
            Account.business_id == fiscal_year.business_id,
            Account.type == "Revenue"
        ).all()
        
        # Get all expense accounts
        expense_accounts = self.db.query(Account).filter(
            Account.business_id == fiscal_year.business_id,
            Account.type == "Expense"
        ).all()
        
        # Calculate net income
        total_revenue = Decimal("0")
        total_expense = Decimal("0")
        
        closing_entries = []
        
        # Close revenue accounts (debit to zero out credit balance)
        for account in revenue_accounts:
            balance = self._get_account_balance_in_period(
                account.id, fiscal_year.start_date, fiscal_year.end_date
            )
            if balance != 0:
                # Revenue has credit balance, debit to close
                entry = ClosingEntry(
                    entry_number=self._get_next_closing_number(fiscal_year.business_id),
                    closing_date=fiscal_year.end_date,
                    fiscal_year_id=fiscal_year.id,
                    entry_type="revenue_close",
                    description=f"Close revenue account: {account.name}",
                    business_id=fiscal_year.business_id,
                    created_by=user_id
                )
                self.db.add(entry)
                self.db.flush()
                
                # Create ledger entry
                ledger_entry = LedgerEntry(
                    transaction_date=fiscal_year.end_date,
                    description=f"Close {account.name}",
                    account_id=account.id,
                    debit=abs(balance),  # Debit to close credit balance
                    credit=0,
                    closing_entry_id=entry.id,
                    business_id=fiscal_year.business_id
                )
                self.db.add(ledger_entry)
                total_revenue += abs(balance)
        
        # Close expense accounts (credit to zero out debit balance)
        for account in expense_accounts:
            balance = self._get_account_balance_in_period(
                account.id, fiscal_year.start_date, fiscal_year.end_date
            )
            if balance != 0:
                # Expense has debit balance, credit to close
                entry = ClosingEntry(
                    entry_number=self._get_next_closing_number(fiscal_year.business_id),
                    closing_date=fiscal_year.end_date,
                    fiscal_year_id=fiscal_year.id,
                    entry_type="expense_close",
                    description=f"Close expense account: {account.name}",
                    business_id=fiscal_year.business_id,
                    created_by=user_id
                )
                self.db.add(entry)
                self.db.flush()
                
                # Create ledger entry
                ledger_entry = LedgerEntry(
                    transaction_date=fiscal_year.end_date,
                    description=f"Close {account.name}",
                    account_id=account.id,
                    debit=0,
                    credit=abs(balance),  # Credit to close debit balance
                    closing_entry_id=entry.id,
                    business_id=fiscal_year.business_id
                )
                self.db.add(ledger_entry)
                total_expense += abs(balance)
        
        # Transfer net income to retained earnings
        net_income = total_revenue - total_expense
        if net_income != 0:
            # Get or create retained earnings account
            retained_earnings = self.db.query(Account).filter(
                Account.business_id == fiscal_year.business_id,
                Account.name == "Retained Earnings"
            ).first()
            
            if not retained_earnings:
                retained_earnings = Account(
                    name="Retained Earnings",
                    code="3300",
                    type="Equity",
                    description="Accumulated earnings retained in the business",
                    business_id=fiscal_year.business_id
                )
                self.db.add(retained_earnings)
                self.db.flush()
            
            entry = ClosingEntry(
                entry_number=self._get_next_closing_number(fiscal_year.business_id),
                closing_date=fiscal_year.end_date,
                fiscal_year_id=fiscal_year.id,
                entry_type="retained_earnings",
                description=f"Transfer net income to retained earnings",
                business_id=fiscal_year.business_id,
                created_by=user_id
            )
            self.db.add(entry)
            self.db.flush()
            
            # If net income is positive, credit retained earnings
            if net_income > 0:
                ledger_entry = LedgerEntry(
                    transaction_date=fiscal_year.end_date,
                    description="Net income transferred to retained earnings",
                    account_id=retained_earnings.id,
                    debit=0,
                    credit=net_income,
                    closing_entry_id=entry.id,
                    business_id=fiscal_year.business_id
                )
            else:
                # If net loss, debit retained earnings
                ledger_entry = LedgerEntry(
                    transaction_date=fiscal_year.end_date,
                    description="Net loss transferred to retained earnings",
                    account_id=retained_earnings.id,
                    debit=abs(net_income),
                    credit=0,
                    closing_entry_id=entry.id,
                    business_id=fiscal_year.business_id
                )
            self.db.add(ledger_entry)
    
    def _get_account_balance_in_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        """Get account balance for a specific period"""
        result = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(
            LedgerEntry.account_id == account_id,
            LedgerEntry.transaction_date >= start_date,
            LedgerEntry.transaction_date <= end_date
        ).scalar()
        
        return result or Decimal("0")
    
    def _get_next_closing_number(self, business_id: int) -> str:
        """Generate next closing entry number"""
        last_entry = self.db.query(ClosingEntry).filter(
            ClosingEntry.business_id == business_id
        ).order_by(ClosingEntry.id.desc()).first()
        
        if last_entry:
            try:
                num = int(last_entry.entry_number.replace("CE-", ""))
                return f"CE-{num + 1:05d}"
            except ValueError:
                pass
        
        return "CE-00001"


class OpeningBalanceService:
    """Service for managing opening balance entries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_fiscal_year(self, fiscal_year_id: int, business_id: int) -> List[OpeningBalanceEntry]:
        return self.db.query(OpeningBalanceEntry).options(
            joinedload(OpeningBalanceEntry.account)
        ).filter(
            OpeningBalanceEntry.fiscal_year_id == fiscal_year_id,
            OpeningBalanceEntry.business_id == business_id
        ).all()
    
    def create_entry(self, fiscal_year_id: int, account_id: int, 
                     debit: Decimal, credit: Decimal,
                     business_id: int, branch_id: int = None,
                     description: str = None, user_id: int = None) -> OpeningBalanceEntry:
        """Create an opening balance entry for an account"""
        
        # Validate fiscal year exists and is not closed
        fiscal_year = self.db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.business_id == business_id
        ).first()
        
        if not fiscal_year:
            raise ValueError("Fiscal year not found")
        
        if fiscal_year.is_closed:
            raise ValueError("Cannot create opening balance for a closed fiscal year")
        
        # Validate account exists and is of correct type
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.business_id == business_id
        ).first()
        
        if not account:
            raise ValueError("Account not found")
        
        # Check if entry already exists for this account in this fiscal year
        existing = self.db.query(OpeningBalanceEntry).filter(
            OpeningBalanceEntry.fiscal_year_id == fiscal_year_id,
            OpeningBalanceEntry.account_id == account_id,
            OpeningBalanceEntry.business_id == business_id
        ).first()
        
        if existing:
            raise ValueError(f"Opening balance already exists for account {account.name}")
        
        entry = OpeningBalanceEntry(
            entry_number=self._get_next_number(business_id),
            entry_date=fiscal_year.start_date,
            fiscal_year_id=fiscal_year_id,
            account_id=account_id,
            debit=debit,
            credit=credit,
            description=description or f"Opening balance for {account.name}",
            business_id=business_id,
            branch_id=branch_id,
            created_by=user_id
        )
        self.db.add(entry)
        self.db.flush()
        
        return entry
    
    def create_from_trial_balance(self, fiscal_year_id: int, 
                                   balances: List[Dict], 
                                   business_id: int, 
                                   branch_id: int = None,
                                   user_id: int = None) -> List[OpeningBalanceEntry]:
        """Create opening balance entries from a trial balance import"""
        entries = []
        
        for balance_data in balances:
            account_id = balance_data.get('account_id')
            debit = Decimal(str(balance_data.get('debit', 0)))
            credit = Decimal(str(balance_data.get('credit', 0)))
            description = balance_data.get('description')
            
            try:
                entry = self.create_entry(
                    fiscal_year_id=fiscal_year_id,
                    account_id=account_id,
                    debit=debit,
                    credit=credit,
                    business_id=business_id,
                    branch_id=branch_id,
                    description=description,
                    user_id=user_id
                )
                entries.append(entry)
            except ValueError as e:
                # Skip duplicate entries or log error
                continue
        
        return entries
    
    def post_entries(self, fiscal_year_id: int, business_id: int, user_id: int) -> bool:
        """Post all opening balance entries for a fiscal year"""
        
        entries = self.db.query(OpeningBalanceEntry).filter(
            OpeningBalanceEntry.fiscal_year_id == fiscal_year_id,
            OpeningBalanceEntry.business_id == business_id,
            OpeningBalanceEntry.is_posted == False
        ).all()
        
        if not entries:
            return False
        
        # Validate that debits equal credits
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        
        if total_debit != total_credit:
            raise ValueError(
                f"Opening balances do not balance. "
                f"Total Debit: {total_debit}, Total Credit: {total_credit}"
            )
        
        # Create ledger entries
        for entry in entries:
            ledger_entry = LedgerEntry(
                transaction_date=entry.entry_date,
                description=entry.description,
                account_id=entry.account_id,
                debit=entry.debit,
                credit=entry.credit,
                branch_id=entry.branch_id,
                business_id=entry.business_id
            )
            self.db.add(ledger_entry)
            
            entry.is_posted = True
            entry.posted_at = datetime.utcnow()
            entry.posted_by = user_id
        
        self.db.flush()
        return True
    
    def _get_next_number(self, business_id: int) -> str:
        """Generate next opening balance entry number"""
        last_entry = self.db.query(OpeningBalanceEntry).filter(
            OpeningBalanceEntry.business_id == business_id
        ).order_by(OpeningBalanceEntry.id.desc()).first()
        
        if last_entry:
            try:
                num = int(last_entry.entry_number.replace("OB-", ""))
                return f"OB-{num + 1:05d}"
            except ValueError:
                pass
        
        return "OB-00001"


class BankReconciliationAdjustmentService:
    """Service for bank reconciliation adjustments"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_bank_account(self, bank_account_id: int, business_id: int,
                            start_date: date = None, end_date: date = None) -> List:
        from app.models import BankReconciliationAdjustment
        
        query = self.db.query(BankReconciliationAdjustment).filter(
            BankReconciliationAdjustment.bank_account_id == bank_account_id,
            BankReconciliationAdjustment.business_id == business_id
        )
        
        if start_date:
            query = query.filter(BankReconciliationAdjustment.adjustment_date >= start_date)
        if end_date:
            query = query.filter(BankReconciliationAdjustment.adjustment_date <= end_date)
        
        return query.order_by(BankReconciliationAdjustment.adjustment_date.desc()).all()
    
    def create_adjustment(self, bank_account_id: int, adjustment_type: str,
                          amount: Decimal, direction: str,
                          business_id: int, branch_id: int,
                          adjustment_date: date = None,
                          description: str = None, reference: str = None,
                          user_id: int = None) -> BankReconciliationAdjustment:
        """Create a bank reconciliation adjustment"""
        from app.models import BankReconciliationAdjustment, BankAccount
        
        # Validate bank account
        bank_account = self.db.query(BankAccount).filter(
            BankAccount.id == bank_account_id,
            BankAccount.business_id == business_id
        ).first()
        
        if not bank_account:
            raise ValueError("Bank account not found")
        
        if direction not in ['debit', 'credit']:
            raise ValueError("Direction must be 'debit' or 'credit'")
        
        if adjustment_type not in ['bank_charge', 'interest', 'error_correction', 'other']:
            raise ValueError("Invalid adjustment type")
        
        adjustment = BankReconciliationAdjustment(
            adjustment_number=self._get_next_number(business_id),
            adjustment_date=adjustment_date or date.today(),
            bank_account_id=bank_account_id,
            adjustment_type=adjustment_type,
            amount=amount,
            direction=direction,
            description=description,
            reference=reference,
            business_id=business_id,
            branch_id=branch_id,
            created_by=user_id
        )
        self.db.add(adjustment)
        self.db.flush()
        
        # Create ledger entry
        self._create_ledger_entry(adjustment, bank_account)
        
        return adjustment
    
    def _create_ledger_entry(self, adjustment, bank_account):
        """Create ledger entry for the adjustment"""
        from app.models import LedgerEntry
        
        # Get appropriate expense/income account based on adjustment type
        if adjustment.adjustment_type == 'bank_charge':
            expense_account = self.db.query(Account).filter(
                Account.business_id == adjustment.business_id,
                Account.name.ilike('%Bank Charge%')
            ).first()
            
            if not expense_account:
                expense_account = Account(
                    name="Bank Charges",
                    code="6100",
                    type="Expense",
                    description="Bank charges and fees",
                    business_id=adjustment.business_id
                )
                self.db.add(expense_account)
                self.db.flush()
            
            contra_account = expense_account
            
        elif adjustment.adjustment_type == 'interest':
            income_account = self.db.query(Account).filter(
                Account.business_id == adjustment.business_id,
                Account.name.ilike('%Interest Income%')
            ).first()
            
            if not income_account:
                income_account = Account(
                    name="Interest Income",
                    code="4200",
                    type="Revenue",
                    description="Interest earned on bank accounts",
                    business_id=adjustment.business_id
                )
                self.db.add(income_account)
                self.db.flush()
            
            contra_account = income_account
        else:
            # For error_correction and other, use suspense account
            suspense_account = self.db.query(Account).filter(
                Account.business_id == adjustment.business_id,
                Account.name.ilike('%Suspense%')
            ).first()
            
            if not suspense_account:
                suspense_account = Account(
                    name="Suspense Account",
                    code="1999",
                    type="Asset",
                    description="Temporary suspense account for reconciliations",
                    business_id=adjustment.business_id
                )
                self.db.add(suspense_account)
                self.db.flush()
            
            contra_account = suspense_account
        
        # Create journal entries
        if adjustment.direction == 'debit':
            # Debit bank account, credit contra account
            entries = [
                LedgerEntry(
                    transaction_date=adjustment.adjustment_date,
                    description=adjustment.description or f"Bank adjustment: {adjustment.adjustment_type}",
                    account_id=bank_account.chart_of_account_id,
                    debit=adjustment.amount,
                    credit=0,
                    branch_id=adjustment.branch_id,
                    business_id=adjustment.business_id
                ),
                LedgerEntry(
                    transaction_date=adjustment.adjustment_date,
                    description=adjustment.description or f"Bank adjustment: {adjustment.adjustment_type}",
                    account_id=contra_account.id,
                    debit=0,
                    credit=adjustment.amount,
                    branch_id=adjustment.branch_id,
                    business_id=adjustment.business_id
                )
            ]
        else:
            # Credit bank account, debit contra account
            entries = [
                LedgerEntry(
                    transaction_date=adjustment.adjustment_date,
                    description=adjustment.description or f"Bank adjustment: {adjustment.adjustment_type}",
                    account_id=bank_account.chart_of_account_id,
                    debit=0,
                    credit=adjustment.amount,
                    branch_id=adjustment.branch_id,
                    business_id=adjustment.business_id
                ),
                LedgerEntry(
                    transaction_date=adjustment.adjustment_date,
                    description=adjustment.description or f"Bank adjustment: {adjustment.adjustment_type}",
                    account_id=contra_account.id,
                    debit=adjustment.amount,
                    credit=0,
                    branch_id=adjustment.branch_id,
                    business_id=adjustment.business_id
                )
            ]
        
        self.db.add_all(entries)
        self.db.flush()
    
    def _get_next_number(self, business_id: int) -> str:
        """Generate next adjustment number"""
        from app.models import BankReconciliationAdjustment
        
        last_adj = self.db.query(BankReconciliationAdjustment).filter(
            BankReconciliationAdjustment.business_id == business_id
        ).order_by(BankReconciliationAdjustment.id.desc()).first()
        
        if last_adj:
            try:
                num = int(last_adj.adjustment_number.replace("BA-", ""))
                return f"BA-{num + 1:05d}"
            except ValueError:
                pass
        
        return "BA-00001"
