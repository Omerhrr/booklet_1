"""
Banking Service - Bank Accounts, Fund Transfers, Reconciliation
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from datetime import date
from app.models import BankAccount, FundTransfer, LedgerEntry, Account, JournalVoucher
from app.schemas import BankAccountCreate, FundTransferCreate


class BankAccountService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, account_id: int, business_id: int) -> Optional[BankAccount]:
        return self.db.query(BankAccount).options(
            joinedload(BankAccount.chart_of_account)
        ).filter(
            BankAccount.id == account_id,
            BankAccount.business_id == business_id
        ).first()

    def get_by_branch(self, branch_id: int, business_id: int) -> List[BankAccount]:
        return self.db.query(BankAccount).options(
            joinedload(BankAccount.chart_of_account)
        ).filter(
            BankAccount.branch_id == branch_id,
            BankAccount.business_id == business_id
        ).order_by(BankAccount.account_name).all()

    def get_all_by_business(self, business_id: int) -> List[BankAccount]:
        return self.db.query(BankAccount).options(
            joinedload(BankAccount.chart_of_account)
        ).filter(
            BankAccount.business_id == business_id
        ).order_by(BankAccount.account_name).all()

    def create(self, account_data: BankAccountCreate, branch_id: int, business_id: int) -> BankAccount:
        opening_balance = account_data.opening_balance or Decimal("0")

        account = BankAccount(
            account_name=account_data.account_name,
            bank_name=account_data.bank_name,
            account_number=account_data.account_number,
            currency=account_data.currency,
            opening_balance=opening_balance,
            current_balance=opening_balance,
            chart_of_account_id=account_data.chart_of_account_id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(account)
        self.db.flush()

        # Create journal entry for opening balance if > 0
        if opening_balance > 0 and account_data.chart_of_account_id:
            self._create_opening_balance_entry(
                account=account,
                opening_balance=opening_balance,
                business_id=business_id,
                branch_id=branch_id
            )

        return account

    def _create_opening_balance_entry(self, account: BankAccount, opening_balance: Decimal,
                                       business_id: int, branch_id: int) -> None:
        """Create journal entry for bank account opening balance"""
        from app.models import CashBookEntry
        
        # Find or get Opening Balance Equity account
        equity_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Opening Balance Equity"
        ).first()

        # Fallback to Owner's Equity if Opening Balance Equity doesn't exist
        if not equity_account:
            equity_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name == "Owner's Equity"
            ).first()

        # Fallback to Retained Earnings
        if not equity_account:
            equity_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name == "Retained Earnings"
            ).first()

        # Last resort: find any equity account
        if not equity_account:
            equity_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.type == "Equity"
            ).first()

        if not equity_account:
            # Create Opening Balance Equity account if nothing exists
            equity_account = Account(
                name="Opening Balance Equity",
                code="3200",
                type="Equity",
                is_system_account=True,
                business_id=business_id
            )
            self.db.add(equity_account)
            self.db.flush()

        # Create journal voucher
        voucher = JournalVoucher(
            voucher_number=self._get_next_journal_number(business_id),
            transaction_date=date.today(),
            description=f"Opening Balance - {account.account_name}",
            reference=f"BANK-{account.id}",
            branch_id=branch_id,
            business_id=business_id,
            is_posted=True
        )
        self.db.add(voucher)
        self.db.flush()

        # Debit the Bank account (increase asset)
        debit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=f"Opening Balance - {account.account_name}",
            debit=opening_balance,
            credit=Decimal("0"),
            account_id=account.chart_of_account_id,
            bank_account_id=account.id,  # Link directly to this bank account
            journal_voucher_id=voucher.id,
            branch_id=branch_id
        )
        self.db.add(debit_entry)

        # Credit the Opening Balance Equity account
        credit_entry = LedgerEntry(
            transaction_date=date.today(),
            description=f"Opening Balance - {account.account_name}",
            debit=Decimal("0"),
            credit=opening_balance,
            account_id=equity_account.id,
            journal_voucher_id=voucher.id,
            branch_id=branch_id
        )
        self.db.add(credit_entry)
        self.db.flush()
        
        # Create Cash Book Entry for the opening balance
        # Generate entry number
        prefix = "CR"  # Cash Receipt for opening balance
        last_cb_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == business_id,
            CashBookEntry.entry_number.like(f'{prefix}-%')
        ).order_by(CashBookEntry.id.desc()).first()
        
        if last_cb_entry:
            try:
                num = int(last_cb_entry.entry_number.replace(f'{prefix}-', ''))
                cb_entry_number = f'{prefix}-{num + 1:05d}'
            except ValueError:
                cb_entry_number = f'{prefix}-00001'
        else:
            cb_entry_number = f'{prefix}-00001'
        
        # Create cash book entry
        cashbook_entry = CashBookEntry(
            entry_number=cb_entry_number,
            entry_date=date.today(),
            entry_type="receipt",
            account_id=account.chart_of_account_id,
            account_type="bank",
            amount=opening_balance,
            balance_after=opening_balance,
            description=f"Opening Balance - {account.account_name}",
            reference=f"BANK-{account.id}",
            payee_payer=account.bank_name or "Opening Balance",
            source_type="opening_balance",
            source_id=account.id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(cashbook_entry)
        self.db.flush()

    def _get_next_journal_number(self, business_id: int) -> str:
        """Get next journal voucher number"""
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
    
    def update_balance(self, account_id: int, amount: Decimal, is_debit: bool = True) -> Optional[BankAccount]:
        """Update account balance"""
        account = self.db.query(BankAccount).get(account_id)
        if not account:
            return None
        
        if is_debit:
            account.current_balance += amount
        else:
            account.current_balance -= amount
        
        self.db.flush()
        return account
    
    def deposit(self, account_id: int, business_id: int, amount: Decimal, 
               description: str = None) -> BankAccount:
        """Make a deposit to bank account"""
        account = self.get_by_id(account_id, business_id)
        if not account:
            raise ValueError("Account not found")
        
        account.current_balance += amount
        
        # Create ledger entry
        if account.chart_of_account_id:
            entry = LedgerEntry(
                transaction_date=date.today(),
                description=description or "Bank Deposit",
                debit=amount,
                credit=Decimal("0"),
                account_id=account.chart_of_account_id,
                branch_id=account.branch_id
            )
            self.db.add(entry)
        
        self.db.flush()
        return account
    
    def withdraw(self, account_id: int, business_id: int, amount: Decimal,
                description: str = None) -> BankAccount:
        """Make a withdrawal from bank account"""
        account = self.get_by_id(account_id, business_id)
        if not account:
            raise ValueError("Account not found")
        
        if account.current_balance < amount:
            raise ValueError("Insufficient funds")
        
        account.current_balance -= amount
        
        # Create ledger entry
        if account.chart_of_account_id:
            entry = LedgerEntry(
                transaction_date=date.today(),
                description=description or "Bank Withdrawal",
                debit=Decimal("0"),
                credit=amount,
                account_id=account.chart_of_account_id,
                branch_id=account.branch_id
            )
            self.db.add(entry)
        
        self.db.flush()
        return account
    
    def reconcile(self, account_id: int, business_id: int, statement_balance: Decimal,
                 reconciliation_date: date = None) -> Dict:
        """Perform bank reconciliation"""
        account = self.get_by_id(account_id, business_id)
        if not account:
            raise ValueError("Account not found")
        
        difference = statement_balance - account.current_balance
        
        account.last_reconciliation_date = reconciliation_date or date.today()
        account.last_reconciliation_balance = statement_balance
        
        self.db.flush()
        
        return {
            "account": account,
            "book_balance": account.current_balance,
            "statement_balance": statement_balance,
            "difference": difference,
            "reconciliation_date": account.last_reconciliation_date
        }
    
    def delete(self, account_id: int, business_id: int) -> bool:
        account = self.get_by_id(account_id, business_id)
        if not account:
            return False

        # Check for transfers
        has_transfers = self.db.query(FundTransfer).filter(
            (FundTransfer.from_account_id == account_id) |
            (FundTransfer.to_account_id == account_id)
        ).first()

        if has_transfers:
            return False

        # Delete associated ledger entries for this bank account
        self.db.query(LedgerEntry).filter(
            LedgerEntry.bank_account_id == account_id
        ).delete()

        self.db.delete(account)
        return True


class FundTransferService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, transfer_id: int, business_id: int) -> Optional[FundTransfer]:
        return self.db.query(FundTransfer).filter(
            FundTransfer.id == transfer_id,
            FundTransfer.business_id == business_id
        ).first()
    
    def get_by_branch(self, branch_id: int, business_id: int) -> List[FundTransfer]:
        return self.db.query(FundTransfer).filter(
            FundTransfer.branch_id == branch_id,
            FundTransfer.business_id == business_id
        ).order_by(FundTransfer.transfer_date.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_transfer = self.db.query(FundTransfer).filter(
            FundTransfer.business_id == business_id
        ).order_by(FundTransfer.id.desc()).first()
        
        if last_transfer:
            try:
                num = int(last_transfer.transfer_number.replace("FT-", ""))
                return f"FT-{num + 1:05d}"
            except ValueError:
                pass
        
        return "FT-00001"
    
    def _get_account_info(self, account_id: int, account_type: str, business_id: int) -> Dict:
        """Get account info for transfer - handles both bank and cash accounts
        
        Args:
            account_id: For bank accounts, this can be either:
                       - The COA account ID (chart_of_account_id) - preferred
                       - The bank account ID itself (fallback for legacy data)
                       For cash accounts, this is the COA account ID
            account_type: "bank" or "cash"
            business_id: Business ID for security
        """
        if account_type == "bank":
            # First try to find by chart_of_account_id (preferred)
            bank_account = self.db.query(BankAccount).filter(
                BankAccount.chart_of_account_id == account_id,
                BankAccount.business_id == business_id
            ).first()
            
            # Fallback: try to find by bank account ID directly
            if not bank_account:
                bank_account = self.db.query(BankAccount).filter(
                    BankAccount.id == account_id,
                    BankAccount.business_id == business_id
                ).first()
            
            if not bank_account:
                raise ValueError(f"Bank account with ID {account_id} not found")
            
            # If bank account has no chart_of_account_id, we can't process the transfer
            if not bank_account.chart_of_account_id:
                raise ValueError(
                    f"Bank account '{bank_account.account_name}' is not properly linked to Chart of Accounts. "
                    "Please run database migration or recreate the bank account."
                )
            
            return {
                'id': bank_account.id,
                'type': 'bank',
                'name': bank_account.account_name,
                'coa_id': bank_account.chart_of_account_id,
                'bank_account': bank_account
            }
        else:
            # account_type == "cash", account_id is COA Account.id
            coa_account = self.db.query(Account).filter(
                Account.id == account_id,
                Account.business_id == business_id
            ).first()
            if not coa_account:
                raise ValueError(f"Cash account {account_id} not found")
            
            return {
                'id': coa_account.id,
                'type': 'cash',
                'name': coa_account.name,
                'coa_id': coa_account.id,
                'bank_account': None
            }
    
    def create(self, transfer_data: FundTransferCreate, branch_id: int, business_id: int) -> FundTransfer:
        """Create a fund transfer between accounts (bank or cash)"""
        from_type = transfer_data.from_account_type or "bank"
        to_type = transfer_data.to_account_type or "bank"
        
        # Validate that source and destination are different
        if transfer_data.from_account_id == transfer_data.to_account_id and from_type == to_type:
            raise ValueError("Cannot transfer funds to the same account")
        
        # Get account info for both accounts
        from_info = self._get_account_info(transfer_data.from_account_id, from_type, business_id)
        to_info = self._get_account_info(transfer_data.to_account_id, to_type, business_id)
        
        # Also validate that COA accounts are different (same COA = same account)
        if from_info['coa_id'] and to_info['coa_id'] and from_info['coa_id'] == to_info['coa_id']:
            raise ValueError("Cannot transfer funds to the same account")
        
        # Check sufficient funds for source account
        if from_info['coa_id']:
            balance_result = self.db.query(
                func.sum(LedgerEntry.debit - LedgerEntry.credit)
            ).filter(
                LedgerEntry.account_id == from_info['coa_id'],
                LedgerEntry.branch_id == branch_id
            ).scalar()
            available_balance = float(balance_result) if balance_result else 0.0
        else:
            available_balance = 0.0
        
        if available_balance < float(transfer_data.amount):
            raise ValueError(f"Insufficient funds in source account. Available: {available_balance:.2f}")
        
        # Create transfer record
        transfer = FundTransfer(
            transfer_number=self.get_next_number(business_id),
            transfer_date=transfer_data.transfer_date,
            amount=transfer_data.amount,
            description=transfer_data.description,
            reference=transfer_data.reference,
            from_account_id=transfer_data.from_account_id,
            from_account_type=from_type,
            from_account_name=from_info['name'],
            to_account_id=transfer_data.to_account_id,
            to_account_type=to_type,
            to_account_name=to_info['name'],
            from_coa_id=from_info['coa_id'],
            to_coa_id=to_info['coa_id'],
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(transfer)
        
        # Create ledger entries
        if from_info['coa_id']:
            from_entry = LedgerEntry(
                transaction_date=transfer_data.transfer_date,
                description=f"Transfer to {to_info['name']}",
                reference=transfer_data.reference,
                debit=Decimal("0"),
                credit=transfer_data.amount,
                account_id=from_info['coa_id'],
                branch_id=branch_id
            )
            self.db.add(from_entry)
        
        if to_info['coa_id']:
            to_entry = LedgerEntry(
                transaction_date=transfer_data.transfer_date,
                description=f"Transfer from {from_info['name']}",
                reference=transfer_data.reference,
                debit=transfer_data.amount,
                credit=Decimal("0"),
                account_id=to_info['coa_id'],
                branch_id=branch_id
            )
            self.db.add(to_entry)
        
        # Create CashBook entries for transfers
        self._create_transfer_cashbook_entries(
            transfer, from_info, to_info, transfer_data.amount, 
            transfer_data.transfer_date, branch_id, business_id
        )
        
        self.db.flush()
        return transfer
    
    def _create_transfer_cashbook_entries(self, transfer: FundTransfer, from_info: Dict, 
                                           to_info: Dict, amount: Decimal, transfer_date: date,
                                           branch_id: int, business_id: int):
        """Create CashBook entries for fund transfer"""
        from app.models import CashBookEntry
        from sqlalchemy import func as sql_func
        
        # Create OUT entry for source account
        if from_info['coa_id']:
            # Get current balance
            current_balance = self.db.query(
                sql_func.sum(CashBookEntry.amount)
            ).filter(
                CashBookEntry.account_id == from_info['coa_id'],
                CashBookEntry.branch_id == branch_id,
                CashBookEntry.business_id == business_id,
                CashBookEntry.entry_type == 'receipt'
            ).scalar() or Decimal("0")
            
            payments = self.db.query(
                sql_func.sum(CashBookEntry.amount)
            ).filter(
                CashBookEntry.account_id == from_info['coa_id'],
                CashBookEntry.branch_id == branch_id,
                CashBookEntry.business_id == business_id,
                CashBookEntry.entry_type == 'payment'
            ).scalar() or Decimal("0")
            
            balance_after = current_balance - payments - amount
            
            # Generate entry number
            prefix = "TR"
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
            
            out_entry = CashBookEntry(
                entry_number=entry_number,
                entry_date=transfer_date,
                entry_type="payment",
                account_id=from_info['coa_id'],
                account_type=from_info['type'],
                amount=amount,
                balance_after=balance_after,
                description=f"Transfer to {to_info['name']}",
                reference=transfer.transfer_number,
                payee_payer=to_info['name'],
                source_type="fund_transfer",
                source_id=transfer.id,
                is_transfer=True,
                transfer_direction='out',
                branch_id=branch_id,
                business_id=business_id
            )
            self.db.add(out_entry)
        
        # Create IN entry for destination account
        if to_info['coa_id']:
            # Get current balance
            current_balance = self.db.query(
                sql_func.sum(CashBookEntry.amount)
            ).filter(
                CashBookEntry.account_id == to_info['coa_id'],
                CashBookEntry.branch_id == branch_id,
                CashBookEntry.business_id == business_id,
                CashBookEntry.entry_type == 'receipt'
            ).scalar() or Decimal("0")
            
            payments = self.db.query(
                sql_func.sum(CashBookEntry.amount)
            ).filter(
                CashBookEntry.account_id == to_info['coa_id'],
                CashBookEntry.branch_id == branch_id,
                CashBookEntry.business_id == business_id,
                CashBookEntry.entry_type == 'payment'
            ).scalar() or Decimal("0")
            
            balance_after = current_balance - payments + amount
            
            # Generate entry number for IN
            prefix_in = "TR"
            last_entry_in = self.db.query(CashBookEntry).filter(
                CashBookEntry.business_id == business_id,
                CashBookEntry.entry_number.like(f'{prefix_in}-%')
            ).order_by(CashBookEntry.id.desc()).first()
            
            if last_entry_in:
                try:
                    num = int(last_entry_in.entry_number.replace(f'{prefix_in}-', ''))
                    entry_number_in = f'{prefix_in}-{num + 1:05d}'
                except ValueError:
                    entry_number_in = f'{prefix_in}-00001'
            else:
                entry_number_in = f'{prefix_in}-00001'
            
            in_entry = CashBookEntry(
                entry_number=entry_number_in,
                entry_date=transfer_date,
                entry_type="receipt",
                account_id=to_info['coa_id'],
                account_type=to_info['type'],
                amount=amount,
                balance_after=balance_after,
                description=f"Transfer from {from_info['name']}",
                reference=transfer.transfer_number,
                payee_payer=from_info['name'],
                source_type="fund_transfer",
                source_id=transfer.id,
                is_transfer=True,
                transfer_direction='in',
                branch_id=branch_id,
                business_id=business_id
            )
            self.db.add(in_entry)
    
    def get_transfer_history(self, account_id: int, business_id: int, 
                            start_date: date = None, end_date: date = None) -> List[FundTransfer]:
        """Get transfer history for an account"""
        query = self.db.query(FundTransfer).filter(
            FundTransfer.business_id == business_id,
            (FundTransfer.from_account_id == account_id) | 
            (FundTransfer.to_account_id == account_id)
        )
        
        if start_date:
            query = query.filter(FundTransfer.transfer_date >= start_date)
        if end_date:
            query = query.filter(FundTransfer.transfer_date <= end_date)
        
        return query.order_by(FundTransfer.transfer_date.desc()).all()
