"""
Sales Service - Invoices, Credit Notes, Payments
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from datetime import date
from app.models import SalesInvoice, SalesInvoiceItem, CreditNote, CreditNoteItem, LedgerEntry, Account, Product, Customer, BadDebt
from app.schemas import SalesInvoiceCreate, SalesInvoiceUpdate


class SalesService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, invoice_id: int, business_id: int, branch_id: int = None) -> Optional[SalesInvoice]:
        query = self.db.query(SalesInvoice).options(
            joinedload(SalesInvoice.items).joinedload(SalesInvoiceItem.product),
            joinedload(SalesInvoice.customer)
        ).filter(
            SalesInvoice.id == invoice_id,
            SalesInvoice.business_id == business_id
        )
        if branch_id:
            query = query.filter(SalesInvoice.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, status: str = None) -> List[SalesInvoice]:
        query = self.db.query(SalesInvoice).options(
            joinedload(SalesInvoice.customer)
        ).filter(
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.business_id == business_id
        )
        if status:
            query = query.filter(SalesInvoice.status == status)
        return query.order_by(SalesInvoice.created_at.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        """Generate next invoice number"""
        last_invoice = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id
        ).order_by(SalesInvoice.id.desc()).first()
        
        if last_invoice:
            try:
                num = int(last_invoice.invoice_number.replace("INV-", ""))
                return f"INV-{num + 1:05d}"
            except ValueError:
                pass
        
        return "INV-00001"
    
    def calculate_totals(self, items: List[dict], vat_rate: Decimal = Decimal("0")) -> dict:
        """Calculate invoice totals"""
        sub_total = sum(item["quantity"] * item["price"] for item in items)
        vat_amount = sub_total * (vat_rate / 100) if vat_rate else Decimal("0")
        total = sub_total + vat_amount
        return {
            "sub_total": sub_total,
            "vat_amount": vat_amount,
            "total_amount": total
        }
    
    def _check_credit_limit(self, customer: Customer, new_invoice_total: Decimal, business_id: int):
        """
        Check if customer has sufficient credit limit for this transaction.
        
        Calculates current outstanding balance (unpaid invoices) and compares
        against the customer's credit limit.
        
        Raises ValueError if credit limit would be exceeded.
        """
        # If customer has no credit limit set (0), allow unlimited credit
        if not customer.credit_limit or customer.credit_limit <= 0:
            return
        
        # Calculate current outstanding balance
        # Sum of all unpaid invoices minus any pre-paid balance
        from sqlalchemy import func
        
        unpaid_invoices_total = self.db.query(
            func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount)
        ).filter(
            SalesInvoice.customer_id == customer.id,
            SalesInvoice.business_id == business_id,
            SalesInvoice.status.in_(["Unpaid", "Partial", "Pending"])
        ).scalar() or Decimal("0")
        
        # Subtract any pre-paid balance customer has
        prepaid_balance = customer.account_balance or Decimal("0")
        current_outstanding = max(unpaid_invoices_total - prepaid_balance, Decimal("0"))
        
        # Calculate available credit
        available_credit = customer.credit_limit - current_outstanding
        
        # Check if new invoice would exceed limit
        if new_invoice_total > available_credit:
            raise ValueError(
                f"Credit limit exceeded for customer '{customer.name}'. "
                f"Credit limit: {customer.credit_limit}, "
                f"Current outstanding: {current_outstanding}, "
                f"Available credit: {available_credit}, "
                f"Invoice total: {new_invoice_total}"
            )
    
    def create(self, invoice_data: SalesInvoiceCreate, business_id: int, branch_id: int, vat_rate: Decimal = Decimal("0")) -> SalesInvoice:
        from app.models import Customer
        from collections import defaultdict
        
        # Aggregate quantities by product first to handle multiple line items of same product
        product_quantities = defaultdict(Decimal)
        for item_data in invoice_data.items:
            product_quantities[item_data.product_id] += item_data.quantity
        
        # Validate stock availability for aggregated quantities
        for product_id, total_qty in product_quantities.items():
            product = self.db.query(Product).get(product_id)
            if product:
                if product.stock_quantity < total_qty:
                    raise ValueError(f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {total_qty}")
        
        # Calculate totals
        items_data = [{"quantity": item.quantity, "price": item.price} for item in invoice_data.items]
        totals = self.calculate_totals(items_data, vat_rate)
        
        # Check customer credit limit
        customer = self.db.query(Customer).filter(Customer.id == invoice_data.customer_id).first()
        if customer:
            self._check_credit_limit(customer, totals["total_amount"], business_id)
        
        # Create invoice
        invoice = SalesInvoice(
            invoice_number=self.get_next_number(business_id),
            customer_id=invoice_data.customer_id,
            invoice_date=invoice_data.invoice_date,
            due_date=invoice_data.due_date,
            notes=invoice_data.notes,
            sub_total=totals["sub_total"],
            vat_amount=totals["vat_amount"],
            total_amount=totals["total_amount"],
            paid_amount=Decimal("0"),
            status="Unpaid",
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(invoice)
        self.db.flush()
        
        # Store product costs for COGS calculation
        product_costs = {}
        
        # Create items
        for item_data in invoice_data.items:
            item = SalesInvoiceItem(
                sales_invoice_id=invoice.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=item_data.price,
                returned_quantity=Decimal("0")
            )
            self.db.add(item)
            
            # Update product stock and store cost
            product = self.db.query(Product).get(item_data.product_id)
            if product:
                product.stock_quantity -= item_data.quantity
                product_costs[item_data.product_id] = {
                    'quantity': item_data.quantity,
                    'purchase_price': product.purchase_price or Decimal("0")
                }
        
        # Create ledger entries
        self._create_ledger_entries(invoice, product_costs)
        
        # Auto-deduct from customer account balance if they have pre-paid funds
        customer = self.db.query(Customer).filter(Customer.id == invoice_data.customer_id).first()
        if customer and customer.account_balance and customer.account_balance > 0:
            self._apply_customer_balance(invoice, customer)
        
        self.db.flush()
        return invoice
    
    def _apply_customer_balance(self, invoice: SalesInvoice, customer: Customer):
        """Apply customer's pre-paid balance to the invoice
        
        Note: This is an internal accounting adjustment - NOT a cash transaction.
        Money was already received when customer funded their account.
        We only create ledger entries, not CashBookEntry.
        """
        from datetime import date as today_date
        
        # Determine how much to apply
        amount_to_apply = min(customer.account_balance, invoice.total_amount - invoice.paid_amount)
        
        if amount_to_apply <= 0:
            return
        
        # Update customer balance
        customer.account_balance -= amount_to_apply
        
        # Update invoice paid amount and status
        invoice.paid_amount += amount_to_apply
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = "Paid"
        elif invoice.paid_amount > 0:
            invoice.status = "Partial"
        
        # Get the Customer Advances account (liability account)
        customer_advances_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name.ilike('%Customer Advance%')
        ).first()
        
        # Get Accounts Receivable account
        receivable_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        if customer_advances_account and receivable_account:
            # Debit Customer Advances (reduce liability - we owe less to customer)
            debit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Applied customer advance to Invoice {invoice.invoice_number}",
                debit=amount_to_apply,
                credit=Decimal("0"),
                account_id=customer_advances_account.id,
                customer_id=customer.id,
                sales_invoice_id=invoice.id,
                branch_id=invoice.branch_id
            )
            self.db.add(debit_entry)
            
            # Credit Accounts Receivable (reduce asset - customer owes less)
            credit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Applied customer advance to Invoice {invoice.invoice_number}",
                debit=Decimal("0"),
                credit=amount_to_apply,
                account_id=receivable_account.id,
                customer_id=customer.id,
                sales_invoice_id=invoice.id,
                branch_id=invoice.branch_id
            )
            self.db.add(credit_entry)
        
        # Note: No CashBookEntry is created here because this is NOT a cash transaction.
        # The money was already recorded in CashBook when the customer funded their account.
        # This is just an internal adjustment between liability (Customer Advances) and asset (AR).
    
    def _create_ledger_entries(self, invoice: SalesInvoice, product_costs: dict = None):
        """Create double-entry ledger entries for invoice"""
        # Get accounts
        receivable_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        sales_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name == "Sales Revenue"
        ).first()
        
        inventory_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name == "Inventory"
        ).first()
        
        cogs_account = self.db.query(Account).filter(
            Account.business_id == invoice.business_id,
            Account.name == "Cost of Goods Sold"
        ).first()
        
        if not receivable_account or not sales_account:
            return
        
        # Debit Accounts Receivable
        debit_entry = LedgerEntry(
            transaction_date=invoice.invoice_date,
            description=f"Invoice {invoice.invoice_number}",
            debit=invoice.total_amount,
            credit=Decimal("0"),
            account_id=receivable_account.id,
            customer_id=invoice.customer_id,
            sales_invoice_id=invoice.id,
            branch_id=invoice.branch_id
        )
        self.db.add(debit_entry)
        
        # Credit Sales Revenue
        credit_entry = LedgerEntry(
            transaction_date=invoice.invoice_date,
            description=f"Invoice {invoice.invoice_number}",
            debit=Decimal("0"),
            credit=invoice.sub_total,
            account_id=sales_account.id,
            customer_id=invoice.customer_id,
            sales_invoice_id=invoice.id,
            branch_id=invoice.branch_id
        )
        self.db.add(credit_entry)
        
        # Credit VAT Payable if applicable
        if invoice.vat_amount > 0:
            vat_account = self.db.query(Account).filter(
                Account.business_id == invoice.business_id,
                Account.name == "VAT Payable"
            ).first()
            
            if vat_account:
                vat_entry = LedgerEntry(
                    transaction_date=invoice.invoice_date,
                    description=f"VAT for Invoice {invoice.invoice_number}",
                    debit=Decimal("0"),
                    credit=invoice.vat_amount,
                    account_id=vat_account.id,
                    customer_id=invoice.customer_id,
                    sales_invoice_id=invoice.id,
                    branch_id=invoice.branch_id
                )
                self.db.add(vat_entry)
        
        # Create COGS and Inventory entries based on product costs
        if product_costs and inventory_account and cogs_account:
            total_cogs = Decimal("0")
            
            for product_id, cost_info in product_costs.items():
                item_cost = Decimal(str(cost_info['purchase_price'])) * Decimal(str(cost_info['quantity']))
                total_cogs += item_cost
            
            if total_cogs > 0:
                # Debit COGS (expense increases)
                cogs_entry = LedgerEntry(
                    transaction_date=invoice.invoice_date,
                    description=f"COGS for Invoice {invoice.invoice_number}",
                    debit=total_cogs,
                    credit=Decimal("0"),
                    account_id=cogs_account.id,
                    customer_id=invoice.customer_id,
                    sales_invoice_id=invoice.id,
                    branch_id=invoice.branch_id
                )
                self.db.add(cogs_entry)
                
                # Credit Inventory (asset decreases)
                inventory_entry = LedgerEntry(
                    transaction_date=invoice.invoice_date,
                    description=f"Inventory reduction for Invoice {invoice.invoice_number}",
                    debit=Decimal("0"),
                    credit=total_cogs,
                    account_id=inventory_account.id,
                    customer_id=invoice.customer_id,
                    sales_invoice_id=invoice.id,
                    branch_id=invoice.branch_id
                )
                self.db.add(inventory_entry)
    
    def record_payment(self, invoice_id: int, payment_data: dict, business_id: int) -> SalesInvoice:
        invoice = self.get_by_id(invoice_id, business_id)
        if not invoice:
            raise ValueError("Invoice not found")

        amount = payment_data["amount"]
        payment_account_id = payment_data["payment_account_id"]
        payment_date = payment_data["payment_date"]
        bank_account_id = payment_data.get("bank_account_id")  # May be None for cash accounts

        # Get accounts
        cash_account = self.db.query(Account).filter(
            Account.id == payment_account_id,
            Account.business_id == business_id
        ).first()

        receivable_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Accounts Receivable"
        ).first()

        # Validate accounts exist
        if not cash_account:
            raise ValueError(f"Payment account not found. Please select a valid cash/bank account.")

        if not receivable_account:
            raise ValueError(f"Accounts Receivable account not found. Please check your Chart of Accounts setup.")

        # Calculate effective balance (total - paid - returned)
        returned_amount = invoice.returned_amount or Decimal("0")
        effective_total = invoice.total_amount - returned_amount
        
        # Validate payment doesn't exceed outstanding balance
        outstanding_balance = effective_total - invoice.paid_amount
        if amount > outstanding_balance:
            raise ValueError(
                f"Payment amount ({amount:.2f}) exceeds outstanding balance ({outstanding_balance:.2f}). "
                f"Total: {invoice.total_amount:.2f}, Already Paid: {invoice.paid_amount:.2f}, Returned: {returned_amount:.2f}"
            )
        
        # Update invoice
        invoice.paid_amount += amount
        # Status is based on effective total (total - returns)
        if invoice.paid_amount >= effective_total:
            invoice.status = "Paid"
        elif invoice.paid_amount > 0:
            invoice.status = "Partial"

        # Debit Cash/Bank (increase asset)
        # Include bank_account_id if this is a bank payment
        debit_entry = LedgerEntry(
            transaction_date=payment_date,
            description=f"Payment for Invoice {invoice.invoice_number}",
            debit=amount,
            credit=Decimal("0"),
            account_id=cash_account.id,
            bank_account_id=int(bank_account_id) if bank_account_id else None,
            customer_id=invoice.customer_id,
            sales_invoice_id=invoice.id,
            branch_id=invoice.branch_id
        )
        self.db.add(debit_entry)

        # Credit Accounts Receivable (decrease receivable)
        credit_entry = LedgerEntry(
            transaction_date=payment_date,
            description=f"Payment for Invoice {invoice.invoice_number}",
            debit=Decimal("0"),
            credit=amount,
            account_id=receivable_account.id,
            customer_id=invoice.customer_id,
            sales_invoice_id=invoice.id,
            branch_id=invoice.branch_id
        )
        self.db.add(credit_entry)

        # Create Cash Book Entry
        self._create_cashbook_entry(invoice, amount, payment_account_id, cash_account, payment_date, bank_account_id)

        self.db.flush()
        return invoice
    
    def _create_cashbook_entry(self, invoice: SalesInvoice, amount: Decimal,
                                payment_account_id: int, cash_account: Account, payment_date: date,
                                bank_account_id: int = None):
        """Create a cash book entry for invoice payment"""
        from app.models import CashBookEntry
        from app.services.cashbook_service import CashBookService
        from app.schemas import CashBookEntryCreate
        
        # Determine account type (cash or bank)
        account_type = "cash"
        if hasattr(cash_account, 'bank_accounts') and cash_account.bank_accounts:
            account_type = "bank"
        elif cash_account.name and 'bank' in cash_account.name.lower():
            account_type = "bank"
        
        # Get current balance from ledger
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        current_balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == cash_account.id,
            LE.branch_id == invoice.branch_id
        ).scalar() or Decimal("0")
        
        # Generate entry number
        prefix = "CR"  # Cash Receipt
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == invoice.business_id,
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
            entry_date=payment_date,
            entry_type="receipt",
            account_id=cash_account.id,
            account_type=account_type,
            amount=amount,
            balance_after=current_balance + amount,
            description=f"Payment from {invoice.customer.name if invoice.customer else 'Customer'} - Invoice {invoice.invoice_number}",
            reference=invoice.invoice_number,
            payee_payer=invoice.customer.name if invoice.customer else None,
            source_type="sales_payment",
            source_id=invoice.id,
            branch_id=invoice.branch_id,
            business_id=invoice.business_id
        )
        self.db.add(cashbook_entry)
    
    def write_off(self, invoice_id: int, business_id: int, write_off_date: date, reason: str = None, user_id: int = None) -> SalesInvoice:
        """
        Write off an unpaid invoice as bad debt.
        
        This creates:
        1. A BadDebt record for tracking
        2. Ledger entries: Debit Bad Debt Expense, Credit Accounts Receivable
        
        Args:
            invoice_id: The invoice to write off
            business_id: Business ID for security
            write_off_date: Date of the write-off
            reason: Optional reason for the write-off
            user_id: Optional user ID who performed the write-off
            
        Returns:
            The updated invoice with status 'Written Off'
        """
        invoice = self.get_by_id(invoice_id, business_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        remaining = invoice.total_amount - invoice.paid_amount
        if remaining <= 0:
            raise ValueError("Invoice already paid in full")
        
        # Check if already written off
        if invoice.status == "Written Off":
            raise ValueError("Invoice is already written off")
        
        # Get or create Bad Debt Expense account
        bad_debt_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Bad Debt Expense"
        ).first()
        
        if not bad_debt_account:
            # Try alternate names
            bad_debt_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name.ilike('%bad%debt%')
            ).first()
        
        if not bad_debt_account:
            # Fallback to Doubtful Accounts Expense
            bad_debt_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name.ilike('%doubtful%')
            ).first()
        
        if not bad_debt_account:
            # Last resort: Operating Expenses
            bad_debt_account = self.db.query(Account).filter(
                Account.business_id == business_id,
                Account.name == "Operating Expenses"
            ).first()
        
        # Get Accounts Receivable account
        receivable_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        if not receivable_account:
            raise ValueError("Accounts Receivable account not found. Please check your Chart of Accounts setup.")
        
        # Generate bad debt number
        last_bad_debt = self.db.query(BadDebt).filter(
            BadDebt.business_id == business_id
        ).order_by(BadDebt.id.desc()).first()
        
        if last_bad_debt:
            try:
                num = int(last_bad_debt.bad_debt_number.replace("BD-", ""))
                bad_debt_number = f"BD-{num + 1:05d}"
            except ValueError:
                bad_debt_number = f"BD-{1:05d}"
        else:
            bad_debt_number = "BD-00001"
        
        # Create BadDebt record
        bad_debt_record = BadDebt(
            bad_debt_number=bad_debt_number,
            write_off_date=write_off_date,
            amount=remaining,
            reason=reason or f"Write-off for invoice {invoice.invoice_number}",
            status='written_off',
            sales_invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            bad_debt_account_id=bad_debt_account.id if bad_debt_account else None,
            branch_id=invoice.branch_id,
            business_id=business_id,
            created_by=user_id
        )
        self.db.add(bad_debt_record)
        self.db.flush()
        
        # Create ledger entries
        if bad_debt_account:
            # Debit Bad Debt Expense (expense increases)
            debit_entry = LedgerEntry(
                transaction_date=write_off_date,
                description=f"Bad debt write-off for Invoice {invoice.invoice_number}" + (f" - {reason}" if reason else ""),
                debit=remaining,
                credit=Decimal("0"),
                account_id=bad_debt_account.id,
                customer_id=invoice.customer_id,
                sales_invoice_id=invoice.id,
                bad_debt_id=bad_debt_record.id,
                branch_id=invoice.branch_id
            )
            self.db.add(debit_entry)
        
        # Credit Accounts Receivable (asset decreases)
        credit_entry = LedgerEntry(
            transaction_date=write_off_date,
            description=f"Bad debt write-off for Invoice {invoice.invoice_number}" + (f" - {reason}" if reason else ""),
            debit=Decimal("0"),
            credit=remaining,
            account_id=receivable_account.id,
            customer_id=invoice.customer_id,
            sales_invoice_id=invoice.id,
            bad_debt_id=bad_debt_record.id,
            branch_id=invoice.branch_id
        )
        self.db.add(credit_entry)
        
        # Update invoice status
        invoice.status = "Written Off"
        
        self.db.flush()
        return invoice


class CreditNoteService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, credit_note_id: int, business_id: int, branch_id: int = None) -> Optional[CreditNote]:
        query = self.db.query(CreditNote).options(
            joinedload(CreditNote.items).joinedload(CreditNoteItem.product),
            joinedload(CreditNote.customer)
        ).filter(
            CreditNote.id == credit_note_id,
            CreditNote.business_id == business_id
        )
        if branch_id:
            query = query.filter(CreditNote.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int) -> List[CreditNote]:
        return self.db.query(CreditNote).options(
            joinedload(CreditNote.customer)
        ).filter(
            CreditNote.business_id == business_id,
            CreditNote.branch_id == branch_id
        ).order_by(CreditNote.created_at.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_cn = self.db.query(CreditNote).filter(
            CreditNote.business_id == business_id
        ).order_by(CreditNote.id.desc()).first()
        
        if last_cn:
            try:
                num = int(last_cn.credit_note_number.replace("CN-", ""))
                return f"CN-{num + 1:05d}"
            except ValueError:
                pass
        
        return "CN-00001"
    
    def create_for_invoice(self, original_invoice: SalesInvoice, items_to_return: List[dict], credit_note_date: date, reason: str = "Invoice Return") -> CreditNote:
        """Create credit note for invoice return"""
        total_amount = sum(item["quantity"] * item["price"] for item in items_to_return)
        
        credit_note = CreditNote(
            credit_note_number=self.get_next_number(original_invoice.business_id),
            credit_note_date=credit_note_date,
            total_amount=total_amount,
            reason=reason,
            status='open',
            sales_invoice_id=original_invoice.id,
            customer_id=original_invoice.customer_id,
            business_id=original_invoice.business_id,
            branch_id=original_invoice.branch_id
        )
        self.db.add(credit_note)
        self.db.flush()
        
        for item_data in items_to_return:
            cn_item = CreditNoteItem(
                credit_note_id=credit_note.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                original_item_id=item_data.get("original_item_id")
            )
            self.db.add(cn_item)
            
            # Update product stock - when customer returns goods, inventory increases
            product = self.db.query(Product).get(item_data["product_id"])
            if product:
                product.stock_quantity += item_data["quantity"]
            
            # Update returned quantity on original item
            orig_item = self.db.query(SalesInvoiceItem).get(item_data.get("original_item_id"))
            if orig_item:
                orig_item.returned_quantity += item_data["quantity"]
        
        # Create ledger entries for credit note
        self._create_credit_note_ledger_entries(credit_note, original_invoice)
        
        self.db.flush()
        return credit_note
    
    def _create_credit_note_ledger_entries(self, credit_note: CreditNote, original_invoice: SalesInvoice):
        """Create double-entry ledger entries for credit note (sales return)"""
        # Get accounts - try by name first, then by code as fallback
        receivable_account = self.db.query(Account).filter(
            Account.business_id == credit_note.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        if not receivable_account:
            # Fallback to code-based lookup
            receivable_account = self.db.query(Account).filter(
                Account.business_id == credit_note.business_id,
                Account.code == "1200"
            ).first()
        
        sales_account = self.db.query(Account).filter(
            Account.business_id == credit_note.business_id,
            Account.name == "Sales Revenue"
        ).first()
        
        if not sales_account:
            # Fallback to code-based lookup
            sales_account = self.db.query(Account).filter(
                Account.business_id == credit_note.business_id,
                Account.code == "4000"
            ).first()
        
        if not receivable_account or not sales_account:
            print(f"Warning: Could not find accounts for credit note ledger entries. "
                  f"AR found: {receivable_account is not None}, Sales found: {sales_account is not None}")
            return
        
        # Credit Accounts Receivable (reduce receivable - customer owes less)
        credit_entry = LedgerEntry(
            transaction_date=credit_note.credit_note_date,
            description=f"Credit Note {credit_note.credit_note_number} - Sales Return",
            debit=Decimal("0"),
            credit=credit_note.total_amount,
            account_id=receivable_account.id,
            customer_id=credit_note.customer_id,
            credit_note_id=credit_note.id,
            branch_id=credit_note.branch_id
        )
        self.db.add(credit_entry)
        
        # Debit Sales Revenue (reduce sales - reverse the sale)
        debit_entry = LedgerEntry(
            transaction_date=credit_note.credit_note_date,
            description=f"Credit Note {credit_note.credit_note_number} - Sales Return",
            debit=credit_note.total_amount,
            credit=Decimal("0"),
            account_id=sales_account.id,
            customer_id=credit_note.customer_id,
            credit_note_id=credit_note.id,
            branch_id=credit_note.branch_id
        )
        self.db.add(debit_entry)
        
        print(f"Created ledger entries for Credit Note {credit_note.credit_note_number}: "
              f"Credit AR {credit_note.total_amount}, Debit Sales {credit_note.total_amount}")
    
    def apply_credit_note(self, credit_note_id: int, business_id: int, refund_method: str = 'none',
                          refund_account_id: int = None, refund_date: date = None) -> CreditNote:
        """
        Apply a credit note to reduce the invoice balance.
        
        For paid invoices, this handles the refund:
        - 'none': Just track the return, no refund needed (invoice had outstanding balance)
        - 'customer_balance': Add refund amount to customer's pre-paid balance
        - 'cash_refund': Issue a cash/bank payment to customer
        
        Args:
            credit_note_id: The credit note to apply
            business_id: Business ID for security
            refund_method: How to handle refund ('none', 'customer_balance', 'cash_refund')
            refund_account_id: Cash/bank account for cash refund
            refund_date: Date for refund transaction
        """
        credit_note = self.db.query(CreditNote).filter(
            CreditNote.id == credit_note_id,
            CreditNote.business_id == business_id
        ).first()
        
        if not credit_note:
            raise ValueError("Credit note not found")
        
        if credit_note.status and credit_note.status != 'open':
            raise ValueError(f"Credit note is already {credit_note.status}")
        
        # Get the original invoice
        invoice = self.db.query(SalesInvoice).get(credit_note.sales_invoice_id)
        if not invoice:
            raise ValueError("Original invoice not found")
        
        # Get customer
        customer = self.db.query(Customer).get(credit_note.customer_id)
        
        # Track previous returns to calculate refundable amount correctly
        previous_returned = invoice.returned_amount or Decimal("0.00")
        
        # Update invoice returned_amount (track returns separately from payments)
        if not hasattr(invoice, 'returned_amount') or invoice.returned_amount is None:
            invoice.returned_amount = Decimal("0.00")
        invoice.returned_amount += credit_note.total_amount
        
        # Calculate the effective balance: total - paid - returned
        effective_balance = invoice.total_amount - invoice.paid_amount - invoice.returned_amount
        
        # Calculate refundable amount for paid invoices
        # If customer paid more than what they now owe (after returns), they're owed a refund
        refund_amount = Decimal("0.00")
        if invoice.paid_amount > 0:
            # How much of this credit note's value was already paid for?
            # Refund = min(credit_note_amount, paid_amount - previous_returns)
            paid_before_this_return = invoice.paid_amount - previous_returned
            if paid_before_this_return > 0:
                refund_amount = min(credit_note.total_amount, paid_before_this_return)
        
        # Handle refund if applicable
        if refund_amount > 0 and refund_method != 'none':
            if refund_method == 'customer_balance':
                # Add to customer's pre-paid balance
                self._refund_to_customer_balance(credit_note, invoice, customer, refund_amount)
            elif refund_method == 'cash_refund':
                # Issue cash/bank refund
                if not refund_account_id:
                    raise ValueError("Refund account is required for cash refunds")
                if not refund_date:
                    refund_date = date.today()
                self._refund_to_cash_account(credit_note, invoice, customer, refund_amount, 
                                            refund_account_id, refund_date)
        
        # Update invoice status based on effective balance
        if effective_balance <= 0:
            invoice.status = "Returned"  # All items returned or balance is zero
        elif invoice.returned_amount > 0 or invoice.paid_amount > 0:
            invoice.status = "Partial"  # Partially paid or returned
        else:
            invoice.status = "Unpaid"
        
        # Mark credit note as applied
        credit_note.status = 'applied'
        
        self.db.flush()
        return credit_note
    
    def _refund_to_customer_balance(self, credit_note: CreditNote, invoice: SalesInvoice,
                                    customer: Customer, refund_amount: Decimal):
        """
        Add refund amount to customer's pre-paid balance.
        
        This is NOT a cash transaction - money stays with the business.
        The customer can use this balance for future purchases.
        """
        from datetime import date as today_date
        
        # Update customer balance
        customer.account_balance = (customer.account_balance or Decimal("0.00")) + refund_amount
        
        # Get the Customer Advances account (liability account)
        customer_advances_account = self.db.query(Account).filter(
            Account.business_id == credit_note.business_id,
            Account.name.ilike('%Customer Advance%')
        ).first()
        
        # Get Accounts Receivable account
        receivable_account = self.db.query(Account).filter(
            Account.business_id == credit_note.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        if customer_advances_account and receivable_account:
            # Credit Customer Advances (increase liability - we owe more to customer)
            credit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Refund from Credit Note {credit_note.credit_note_number} - Added to customer balance",
                debit=Decimal("0"),
                credit=refund_amount,
                account_id=customer_advances_account.id,
                customer_id=customer.id,
                credit_note_id=credit_note.id,
                branch_id=credit_note.branch_id
            )
            self.db.add(credit_entry)
            
            # Debit Accounts Receivable (reduce AR since we owe customer)
            debit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Refund from Credit Note {credit_note.credit_note_number} - Added to customer balance",
                debit=refund_amount,
                credit=Decimal("0"),
                account_id=receivable_account.id,
                customer_id=customer.id,
                credit_note_id=credit_note.id,
                branch_id=credit_note.branch_id
            )
            self.db.add(debit_entry)
    
    def _refund_to_cash_account(self, credit_note: CreditNote, invoice: SalesInvoice,
                                customer: Customer, refund_amount: Decimal,
                                refund_account_id: int, refund_date: date):
        """
        Issue a cash/bank refund to the customer.
        
        This creates:
        1. Ledger entries (Credit Cash/Bank, Debit Accounts Receivable)
        2. CashBook entry (payment out)
        """
        from app.models import CashBookEntry
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        # Get the refund account
        refund_account = self.db.query(Account).filter(
            Account.id == refund_account_id,
            Account.business_id == credit_note.business_id
        ).first()
        
        if not refund_account:
            raise ValueError("Refund account not found")
        
        # Get Accounts Receivable account
        receivable_account = self.db.query(Account).filter(
            Account.business_id == credit_note.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        if not receivable_account:
            raise ValueError("Accounts Receivable account not found")
        
        # Check if refund account has sufficient balance before processing refund
        current_balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == refund_account.id,
            LE.branch_id == credit_note.branch_id
        ).scalar() or Decimal("0")
        
        if current_balance < refund_amount:
            raise ValueError(
                f"Insufficient funds in '{refund_account.name}' for refund. "
                f"Available balance: {float(current_balance):,.2f}, "
                f"Refund amount: {float(refund_amount):,.2f}"
            )
        
        # Credit Cash/Bank (decrease asset - money going out)
        credit_entry = LedgerEntry(
            transaction_date=refund_date,
            description=f"Refund for Credit Note {credit_note.credit_note_number} - Cash refund to customer",
            debit=Decimal("0"),
            credit=refund_amount,
            account_id=refund_account.id,
            customer_id=customer.id if customer else None,
            credit_note_id=credit_note.id,
            branch_id=credit_note.branch_id
        )
        self.db.add(credit_entry)
        
        # Debit Accounts Receivable (reduce receivable)
        debit_entry = LedgerEntry(
            transaction_date=refund_date,
            description=f"Refund for Credit Note {credit_note.credit_note_number} - Cash refund to customer",
            debit=refund_amount,
            credit=Decimal("0"),
            account_id=receivable_account.id,
            customer_id=customer.id if customer else None,
            credit_note_id=credit_note.id,
            branch_id=credit_note.branch_id
        )
        self.db.add(debit_entry)
        
        # Create CashBook Entry (payment out)
        # Determine account type
        account_type = "cash"
        if refund_account.name and 'bank' in refund_account.name.lower():
            account_type = "bank"
        
        # Check if there's a bank account linked
        bank_account_id = None
        if account_type == "bank":
            from app.models import BankAccount
            bank_account = self.db.query(BankAccount).filter(
                BankAccount.account_id == refund_account.id
            ).first()
            if bank_account:
                bank_account_id = bank_account.id
        
        # Get current balance
        current_balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == refund_account.id,
            LE.branch_id == credit_note.branch_id
        ).scalar() or Decimal("0")
        
        # Generate entry number
        prefix = "CP"  # Cash Payment
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == credit_note.business_id,
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
        
        # Create cash book entry (payment out)
        cashbook_entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=refund_date,
            entry_type="payment",
            account_id=refund_account.id,
            account_type=account_type,
            amount=refund_amount,
            balance_after=current_balance - refund_amount,
            description=f"Refund to {customer.name if customer else 'Customer'} - Credit Note {credit_note.credit_note_number}",
            reference=credit_note.credit_note_number,
            payee_payer=customer.name if customer else None,
            source_type="credit_note_refund",
            source_id=credit_note.id,
            branch_id=credit_note.branch_id,
            business_id=credit_note.business_id
        )
        self.db.add(cashbook_entry)
        
        # Track refund amount on credit note
        credit_note.refund_amount = refund_amount
        credit_note.refund_method = 'cash'
        credit_note.refund_date = refund_date
