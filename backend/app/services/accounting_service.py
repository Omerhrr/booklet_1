"""
Accounting Service - Chart of Accounts, Journal Vouchers, Ledger
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from datetime import date
from app.models import (
    Account, AccountType, JournalVoucher, LedgerEntry, 
    Budget, BudgetItem, Business
)
from app.schemas import (
    AccountCreate, AccountUpdate, JournalVoucherCreate,
    BudgetCreate
)


class AccountService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, account_id: int, business_id: int) -> Optional[Account]:
        return self.db.query(Account).filter(
            Account.id == account_id,
            Account.business_id == business_id
        ).first()
    
    def get_by_code(self, code: str, business_id: int) -> Optional[Account]:
        return self.db.query(Account).filter(
            Account.code == code,
            Account.business_id == business_id
        ).first()
    
    def get_by_business(self, business_id: int, include_inactive: bool = False) -> List[Account]:
        query = self.db.query(Account).filter(Account.business_id == business_id)
        if not include_inactive:
            query = query.filter(Account.is_active == True)
        return query.order_by(Account.code).all()
    
    def get_by_type(self, business_id: int, account_type) -> List[Account]:
        # Handle both enum and string types
        type_value = account_type.value if hasattr(account_type, 'value') else str(account_type)
        return self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.type.ilike(type_value),
            Account.is_active == True
        ).order_by(Account.code).all()
    
    def create(self, account_data: AccountCreate, business_id: int) -> Account:
        # Handle type - convert enum to string if needed
        account_type = account_data.type
        if hasattr(account_type, 'value'):
            account_type = account_type.value
        
        # Check for duplicate code if provided
        if account_data.code:
            existing = self.get_by_code(account_data.code, business_id)
            if existing:
                raise ValueError(f"Account with code '{account_data.code}' already exists")
        
        # Check for duplicate name
        existing_name = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == account_data.name
        ).first()
        if existing_name:
            raise ValueError(f"Account with name '{account_data.name}' already exists")
        
        account = Account(
            name=account_data.name,
            code=account_data.code,
            type=account_type,
            description=account_data.description,
            parent_id=account_data.parent_id,
            business_id=business_id
        )
        self.db.add(account)
        self.db.flush()
        return account
    
    def update(self, account_id: int, business_id: int, account_data: AccountUpdate) -> Optional[Account]:
        account = self.get_by_id(account_id, business_id)
        if not account:
            return None
        
        update_data = account_data.model_dump(exclude_unset=True)
        
        # Check for duplicate code if being updated
        if 'code' in update_data and update_data['code']:
            existing = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.code == update_data['code'],
                Account.id != account_id
            ).first()
            if existing:
                raise ValueError(f"Account with code '{update_data['code']}' already exists")
        
        # Check for duplicate name if being updated
        if 'name' in update_data and update_data['name']:
            existing_name = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name == update_data['name'],
                Account.id != account_id
            ).first()
            if existing_name:
                raise ValueError(f"Account with name '{update_data['name']}' already exists")
        
        for key, value in update_data.items():
            setattr(account, key, value)
        
        self.db.flush()
        return account
    
    def get_balance(self, account_id: int, branch_id: int = None) -> Decimal:
        """Calculate account balance from ledger entries, optionally filtered by branch"""
        query = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(LedgerEntry.account_id == account_id)
        
        if branch_id:
            query = query.filter(LedgerEntry.branch_id == branch_id)
        
        result = query.scalar()
        return result or Decimal("0")
    
    def get_with_balance(self, account_id: int, business_id: int, branch_id: int = None) -> Optional[Dict]:
        account = self.get_by_id(account_id, business_id)
        if not account:
            return None
        
        balance = self.get_balance(account_id, branch_id)
        
        # For liability, equity, revenue accounts, credit balance is positive
        account_type_lower = account.type.lower() if account.type else ''
        if account_type_lower in ['liability', 'equity', 'revenue']:
            balance = -balance
        
        return {
            "account": {
                "id": account.id,
                "name": account.name,
                "code": account.code,
                "type": account.type,
                "description": account.description,
                "is_system_account": account.is_system_account,
                "is_active": account.is_active,
                "parent_id": account.parent_id,
                "business_id": account.business_id,
                "created_at": account.created_at.isoformat() if account.created_at else None
            },
            "balance": float(balance)
        }
    
    def delete(self, account_id: int, business_id: int) -> bool:
        account = self.get_by_id(account_id, business_id)
        if not account or account.is_system_account:
            return False
        
        # Check for ledger entries
        has_entries = self.db.query(LedgerEntry).filter(
            LedgerEntry.account_id == account_id
        ).first()
        
        if has_entries:
            account.is_active = False
        else:
            self.db.delete(account)
        
        return True


class JournalVoucherService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, voucher_id: int, business_id: int) -> Optional[JournalVoucher]:
        return self.db.query(JournalVoucher).options(
            joinedload(JournalVoucher.ledger_entries).joinedload(LedgerEntry.account)
        ).filter(
            JournalVoucher.id == voucher_id,
            JournalVoucher.business_id == business_id
        ).first()
    
    def get_by_branch(self, branch_id: int, business_id: int) -> List[JournalVoucher]:
        return self.db.query(JournalVoucher).filter(
            JournalVoucher.branch_id == branch_id,
            JournalVoucher.business_id == business_id
        ).order_by(JournalVoucher.created_at.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_voucher = self.db.query(JournalVoucher).filter(
            JournalVoucher.business_id == business_id
        ).order_by(JournalVoucher.id.desc()).first()
        
        if last_voucher:
            try:
                num = int(last_voucher.voucher_number.replace("JV-", ""))
                return f"JV-{num + 1:05d}"
            except ValueError:
                pass
        
        return "JV-00001"
    
    def create(self, voucher_data: JournalVoucherCreate, business_id: int, branch_id: int, user_id: int) -> JournalVoucher:
        # Validate that debits equal credits
        total_debit = sum(line.debit for line in voucher_data.lines)
        total_credit = sum(line.credit for line in voucher_data.lines)
        
        if total_debit != total_credit:
            raise ValueError("Debits must equal credits")
        
        voucher = JournalVoucher(
            voucher_number=self.get_next_number(business_id),
            transaction_date=voucher_data.transaction_date,
            description=voucher_data.description,
            reference=voucher_data.reference,
            branch_id=branch_id,
            business_id=business_id,
            created_by=user_id
        )
        self.db.add(voucher)
        self.db.flush()
        
        # Create ledger entries
        for line in voucher_data.lines:
            entry = LedgerEntry(
                transaction_date=voucher_data.transaction_date,
                description=line.description,
                account_id=line.account_id,
                debit=line.debit,
                credit=line.credit,
                journal_voucher_id=voucher.id,
                branch_id=branch_id
            )
            self.db.add(entry)
        
        self.db.flush()
        return voucher
    
    def post(self, voucher_id: int, business_id: int) -> Optional[JournalVoucher]:
        """Post a journal voucher (make it permanent)"""
        voucher = self.get_by_id(voucher_id, business_id)
        if not voucher or voucher.is_posted:
            return None
        
        voucher.is_posted = True
        self.db.flush()
        return voucher


class BudgetService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, budget_id: int, business_id: int) -> Optional[Budget]:
        return self.db.query(Budget).options(
            joinedload(Budget.items).joinedload(BudgetItem.account)
        ).filter(
            Budget.id == budget_id,
            Budget.business_id == business_id
        ).first()
    
    def get_by_business(self, business_id: int) -> List[Budget]:
        return self.db.query(Budget).filter(
            Budget.business_id == business_id
        ).order_by(Budget.fiscal_year.desc()).all()
    
    def create(self, budget_data: BudgetCreate, business_id: int) -> Budget:
        budget = Budget(
            name=budget_data.name,
            fiscal_year=budget_data.fiscal_year,
            description=budget_data.description,
            business_id=business_id
        )
        self.db.add(budget)
        self.db.flush()
        return budget
    
    def add_item(self, budget_id: int, account_id: int, amount: Decimal, month: int = None) -> BudgetItem:
        item = BudgetItem(
            budget_id=budget_id,
            account_id=account_id,
            amount=amount,
            month=month
        )
        self.db.add(item)
        self.db.flush()
        return item
    
    def get_budget_vs_actual(self, budget_id: int, business_id: int) -> Dict:
        """Compare budget vs actual figures"""
        budget = self.get_by_id(budget_id, business_id)
        if not budget:
            return None
        
        result = []
        for item in budget.items:
            # Calculate actual from ledger
            actual = self.db.query(
                func.sum(LedgerEntry.debit - LedgerEntry.credit)
            ).filter(
                LedgerEntry.account_id == item.account_id,
                func.extract('year', LedgerEntry.transaction_date) == budget.fiscal_year
            ).scalar() or Decimal("0")
            
            result.append({
                "account": item.account,
                "budgeted": item.amount,
                "actual": actual,
                "variance": item.amount - actual
            })
        
        return {
            "budget": budget,
            "items": result
        }


class ReportService:
    """Financial reports service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_trial_balance(self, business_id: int, branch_id: int = None, as_of_date: date = None) -> List[Dict]:
        """Generate trial balance report"""
        accounts = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.is_active == True
        ).all()
        
        result = []
        for account in accounts:
            query = self.db.query(
                func.sum(LedgerEntry.debit).label("total_debit"),
                func.sum(LedgerEntry.credit).label("total_credit")
            ).filter(LedgerEntry.account_id == account.id)
            
            if branch_id:
                query = query.filter(LedgerEntry.branch_id == branch_id)
            if as_of_date:
                query = query.filter(LedgerEntry.transaction_date <= as_of_date)
            
            totals = query.first()
            
            debit = totals.total_debit or Decimal("0")
            credit = totals.total_credit or Decimal("0")
            balance = debit - credit
            
            if balance != 0:
                result.append({
                    "account": account,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance
                })
        
        return result
    
    def get_balance_sheet(self, business_id: int, branch_id: int = None, as_of_date: date = None) -> Dict:
        """Generate balance sheet in standard Statement of Financial Position format"""
        
        # Helper to get account balance
        def get_account_balance(account_id: int) -> Decimal:
            query = self.db.query(
                func.sum(LedgerEntry.debit - LedgerEntry.credit)
            ).filter(LedgerEntry.account_id == account_id)
            
            if branch_id:
                query = query.filter(LedgerEntry.branch_id == branch_id)
            if as_of_date:
                query = query.filter(LedgerEntry.transaction_date <= as_of_date)
            
            return query.scalar() or Decimal("0")
        
        # Helper to find account by name pattern
        def find_account_by_pattern(patterns: list, account_type: str = None):
            """Find account by name patterns (case insensitive)"""
            from sqlalchemy import or_
            
            query = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.is_active == True
            )
            
            # Add pattern filters
            pattern_filters = [Account.name.ilike(f"%{p}%") for p in patterns]
            query = query.filter(or_(*pattern_filters))
            
            if account_type:
                query = query.filter(Account.type.ilike(account_type))
            
            return query.first()
        
        # Helper to get balance by account patterns
        def get_balance_by_patterns(patterns: list, account_type: str = None) -> Decimal:
            """Get balance by finding account with matching name patterns"""
            from sqlalchemy import or_
            
            query = self.db.query(
                func.sum(LedgerEntry.debit - LedgerEntry.credit)
            ).join(Account).filter(
                Account.business_id == business_id,
                Account.is_active == True
            )
            
            pattern_filters = [Account.name.ilike(f"%{p}%") for p in patterns]
            query = query.filter(or_(*pattern_filters))
            
            if account_type:
                query = query.filter(Account.type.ilike(account_type))
            if branch_id:
                query = query.filter(LedgerEntry.branch_id == branch_id)
            if as_of_date:
                query = query.filter(LedgerEntry.transaction_date <= as_of_date)
            
            return query.scalar() or Decimal("0")
        
        # Helper to get all accounts of a type
        def get_accounts_by_type(account_type: str, exclude_patterns: list = None):
            from sqlalchemy import and_, not_, or_
            
            query = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.is_active == True,
                Account.type.ilike(account_type)
            )
            
            if exclude_patterns:
                exclude_filters = [Account.name.ilike(f"%{p}%") for p in exclude_patterns]
                query = query.filter(not_(or_(*exclude_filters)))
            
            return query.all()
        
        # ========== NON-CURRENT ASSETS ==========
        # Fixed Assets (cost)
        fixed_assets_cost = get_balance_by_patterns(
            ['fixed asset', 'property', 'plant', 'equipment', 'vehicle', 'building', 'machinery', 'furniture', 'computer', 'leasehold'],
            'asset'
        )
        
        # Accumulated Depreciation
        accumulated_depreciation = get_balance_by_patterns(
            ['accumulated depreciation', 'depreciation'],
            'asset'
        )
        
        # Net Book Value
        net_book_value = fixed_assets_cost + accumulated_depreciation  # depreciation is negative (contra-asset)
        
        # Other Non-Current Assets (intangible, long-term investments, etc.)
        other_non_current = get_balance_by_patterns(
            ['intangible', 'goodwill', 'patent', 'trademark', 'copyright', 'long-term investment'],
            'asset'
        )
        
        total_non_current_assets = net_book_value + other_non_current
        
        # ========== CURRENT ASSETS ==========
        # Inventory
        inventory = get_balance_by_patterns(
            ['inventory', 'stock', 'merchandise'],
            'asset'
        )
        
        # Accounts Receivable
        accounts_receivable = get_balance_by_patterns(
            ['accounts receivable', 'receivable', 'debtor', 'trade receivable', 'a/r'],
            'asset'
        )
        
        # VAT Receivable (Input VAT)
        vat_receivable = get_balance_by_patterns(
            ['vat receivable', 'input vat', 'vat input', 'vat credit'],
            'asset'
        )
        
        # Cash & Bank (includes cash accounts and bank accounts)
        cash_and_bank = get_balance_by_patterns(
            ['cash', 'bank', 'petty cash'],
            'asset'
        )
        
        # Other Current Assets (prepayments, deposits, etc.)
        other_current_assets = get_balance_by_patterns(
            ['prepaid', 'prepayment', 'deposit', 'advance', 'accrued income'],
            'asset'
        )
        
        # Vendor Advances (prepayments to vendors)
        vendor_advances = get_balance_by_patterns(
            ['vendor advance', 'supplier advance'],
            'asset'
        )
        
        total_current_assets = inventory + accounts_receivable + vat_receivable + cash_and_bank + other_current_assets + vendor_advances
        
        # ========== TOTAL ASSETS ==========
        total_assets = total_non_current_assets + total_current_assets
        
        # ========== LIABILITIES ==========
        # Accounts Payable
        accounts_payable = get_balance_by_patterns(
            ['accounts payable', 'payable', 'creditor', 'trade payable', 'a/p'],
            'liability'
        )
        
        # Payroll Liabilities
        payroll_liabilities = get_balance_by_patterns(
            ['payroll liability', 'salary payable', 'wages payable', 'payroll'],
            'liability'
        )
        
        # PAYE Payable
        paye_payable = get_balance_by_patterns(
            ['paye', 'pay as you earn', 'income tax payable'],
            'liability'
        )
        
        # Pension Payable
        pension_payable = get_balance_by_patterns(
            ['pension', 'provident fund', 'retirement'],
            'liability'
        )
        
        # VAT Payable (Output VAT)
        vat_payable = get_balance_by_patterns(
            ['vat payable', 'output vat', 'vat output', 'vat liability'],
            'liability'
        )
        
        # Customer Advances (deferred revenue)
        customer_advances = get_balance_by_patterns(
            ['customer advance', 'deferred revenue', 'unearned revenue', 'deposit received'],
            'liability'
        )
        
        # Other Liabilities
        other_liabilities = get_balance_by_patterns(
            ['accrued expense', 'other liability', 'loan payable', 'note payable'],
            'liability'
        )
        
        total_liabilities = accounts_payable + payroll_liabilities + paye_payable + pension_payable + vat_payable + customer_advances + other_liabilities
        
        # ========== EQUITY ==========
        # Owner's Equity / Capital
        owners_equity = get_balance_by_patterns(
            ["owner's equity", 'owner equity', 'capital', 'owner capital', 'member capital'],
            'equity'
        )
        
        # Retained Earnings
        retained_earnings = get_balance_by_patterns(
            ['retained earnings', 'retained earning'],
            'equity'
        )
        
        # Opening Balance Equity
        opening_balance_equity = get_balance_by_patterns(
            ['opening balance equity'],
            'equity'
        )
        
        # Current Period Earnings (Net Income)
        current_period_earnings = Decimal("0")
        
        # Calculate net income for current period
        revenue_balance = Decimal("0")
        expense_balance = Decimal("0")
        
        for account in get_accounts_by_type('revenue'):
            balance = get_account_balance(account.id)
            revenue_balance += balance
        
        for account in get_accounts_by_type('expense'):
            balance = get_account_balance(account.id)
            expense_balance += balance
        
        current_period_earnings = revenue_balance - expense_balance
        
        total_equity = owners_equity + retained_earnings + opening_balance_equity + current_period_earnings
        
        # ========== TOTAL EQUITY & LIABILITIES ==========
        total_equity_and_liabilities = total_equity + total_liabilities
        
        return {
            # Non-Current Assets
            "non_current_assets": {
                "fixed_assets_cost": fixed_assets_cost,
                "accumulated_depreciation": accumulated_depreciation,
                "net_book_value": net_book_value,
                "other_non_current": other_non_current,
                "total": total_non_current_assets
            },
            # Current Assets
            "current_assets": {
                "inventory": inventory,
                "accounts_receivable": accounts_receivable,
                "vat_receivable": vat_receivable,
                "cash_and_bank": cash_and_bank,
                "other_current_assets": other_current_assets,
                "vendor_advances": vendor_advances,
                "total": total_current_assets
            },
            "total_assets": total_assets,
            # Liabilities
            "liabilities": {
                "accounts_payable": accounts_payable,
                "payroll_liabilities": payroll_liabilities,
                "paye_payable": paye_payable,
                "pension_payable": pension_payable,
                "vat_payable": vat_payable,
                "customer_advances": customer_advances,
                "other_liabilities": other_liabilities,
                "total": total_liabilities
            },
            # Equity
            "equity": {
                "owners_equity": owners_equity,
                "retained_earnings": retained_earnings,
                "opening_balance_equity": opening_balance_equity,
                "current_period_earnings": current_period_earnings,
                "total": total_equity
            },
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "total_equity_and_liabilities": total_equity_and_liabilities,
            "as_of_date": as_of_date or date.today(),
            
            # Keep legacy format for backwards compatibility
            "assets": [],
            "liabilities_list": [],
            "equity_list": []
        }
    
    def get_income_statement(self, business_id: int, branch_id: int = None, start_date: date = None, end_date: date = None) -> Dict:
        """Generate income statement (Profit & Loss)"""
        revenue = []
        expenses = []
        
        accounts = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.is_active == True,
            Account.type.ilike('Revenue') | Account.type.ilike('Expense')
        ).all()
        
        for account in accounts:
            query = self.db.query(
                func.sum(LedgerEntry.credit - LedgerEntry.debit).label("balance")
            ).filter(
                LedgerEntry.account_id == account.id
            )
            
            if branch_id:
                query = query.filter(LedgerEntry.branch_id == branch_id)
            if start_date:
                query = query.filter(LedgerEntry.transaction_date >= start_date)
            if end_date:
                query = query.filter(LedgerEntry.transaction_date <= end_date)
            
            balance = query.scalar() or Decimal("0")
            
            if balance == 0:
                continue
            
            item = {"account": account, "balance": abs(balance)}
            
            account_type_lower = account.type.lower() if account.type else ''
            if account_type_lower == 'revenue':
                revenue.append(item)
            elif account_type_lower == 'expense':
                expenses.append(item)
        
        total_revenue = sum(item["balance"] for item in revenue)
        total_expenses = sum(item["balance"] for item in expenses)
        net_income = total_revenue - total_expenses
        
        return {
            "revenue": revenue,
            "expenses": expenses,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def get_general_ledger(self, business_id: int, branch_id: int = None, account_id: int = None, 
                          start_date: date = None, end_date: date = None) -> List[Dict]:
        """Generate general ledger report"""
        query = self.db.query(LedgerEntry).options(
            joinedload(LedgerEntry.account)
        ).join(Account).filter(
            Account.business_id == business_id
        )
        
        if branch_id:
            query = query.filter(LedgerEntry.branch_id == branch_id)
        if account_id:
            query = query.filter(LedgerEntry.account_id == account_id)
        if start_date:
            query = query.filter(LedgerEntry.transaction_date >= start_date)
        if end_date:
            query = query.filter(LedgerEntry.transaction_date <= end_date)
        
        entries = query.order_by(LedgerEntry.transaction_date, LedgerEntry.id).all()
        
        result = []
        running_balance = Decimal("0")
        
        for entry in entries:
            running_balance += entry.debit - entry.credit
            result.append({
                "entry": entry,
                "balance": running_balance
            })
        
        return result
