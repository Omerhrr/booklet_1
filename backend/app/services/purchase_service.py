"""
Purchases Service - Bills, Debit Notes
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from datetime import date
from app.models import PurchaseBill, PurchaseBillItem, DebitNote, DebitNoteItem, LedgerEntry, Account, Product, Vendor
from app.schemas import PurchaseBillCreate


class PurchaseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, bill_id: int, business_id: int, branch_id: int = None) -> Optional[PurchaseBill]:
        query = self.db.query(PurchaseBill).options(
            joinedload(PurchaseBill.items).joinedload(PurchaseBillItem.product),
            joinedload(PurchaseBill.vendor)
        ).filter(
            PurchaseBill.id == bill_id,
            PurchaseBill.business_id == business_id
        )
        if branch_id:
            query = query.filter(PurchaseBill.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, status: str = None) -> List[PurchaseBill]:
        query = self.db.query(PurchaseBill).options(
            joinedload(PurchaseBill.vendor)
        ).filter(
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.business_id == business_id
        )
        if status:
            query = query.filter(PurchaseBill.status == status)
        return query.order_by(PurchaseBill.created_at.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_bill = self.db.query(PurchaseBill).filter(
            PurchaseBill.business_id == business_id
        ).order_by(PurchaseBill.id.desc()).first()
        
        if last_bill:
            try:
                num = int(last_bill.bill_number.replace("PO-", ""))
                return f"PO-{num + 1:05d}"
            except ValueError:
                pass
        
        return "PO-00001"
    
    def create(self, bill_data: PurchaseBillCreate, business_id: int, branch_id: int, vat_rate: Decimal = Decimal("0")) -> PurchaseBill:
        from app.models import Vendor, CashBookEntry
        from datetime import date as today_date
        
        # Calculate totals
        sub_total = sum(item.quantity * item.price for item in bill_data.items)
        vat_amount = sub_total * (vat_rate / 100) if vat_rate else Decimal("0")
        total_amount = sub_total + vat_amount
        
        # Create bill
        bill = PurchaseBill(
            bill_number=bill_data.bill_number or self.get_next_number(business_id),
            vendor_id=bill_data.vendor_id,
            bill_date=bill_data.bill_date,
            due_date=bill_data.due_date,
            notes=bill_data.notes,
            sub_total=sub_total,
            vat_amount=vat_amount,
            total_amount=total_amount,
            paid_amount=Decimal("0"),
            status="Unpaid",
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(bill)
        self.db.flush()
        
        # Create items
        for item_data in bill_data.items:
            item = PurchaseBillItem(
                purchase_bill_id=bill.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=item_data.price,
                returned_quantity=Decimal("0")
            )
            self.db.add(item)
            
            # Update product stock
            product = self.db.query(Product).get(item_data.product_id)
            if product:
                product.stock_quantity += item_data.quantity
        
        # Create ledger entries
        self._create_ledger_entries(bill)
        
        # Auto-deduct from vendor account balance if we have pre-paid funds with them
        vendor = self.db.query(Vendor).filter(Vendor.id == bill_data.vendor_id).first()
        if vendor and vendor.account_balance and vendor.account_balance > 0:
            self._apply_vendor_balance(bill, vendor)
        
        self.db.flush()
        return bill
    
    def _apply_vendor_balance(self, bill: PurchaseBill, vendor: Vendor):
        """Apply vendor's pre-paid balance to the bill
        
        Note: This is an internal accounting adjustment - NOT a cash transaction.
        Money was already paid when we funded the vendor's account.
        We only create ledger entries, not CashBookEntry.
        """
        from datetime import date as today_date
        
        # Determine how much to apply
        amount_to_apply = min(vendor.account_balance, bill.total_amount - bill.paid_amount)
        
        if amount_to_apply <= 0:
            return
        
        # Update vendor balance
        vendor.account_balance -= amount_to_apply
        
        # Update bill paid amount and status
        bill.paid_amount += amount_to_apply
        if bill.paid_amount >= bill.total_amount:
            bill.status = "Paid"
        elif bill.paid_amount > 0:
            bill.status = "Partial"
        
        # Get the Vendor Advances account (asset account)
        vendor_advances_account = self.db.query(Account).filter(
            Account.business_id == bill.business_id,
            Account.name.ilike('%Vendor Advance%')
        ).first()
        
        # Get Accounts Payable account
        payable_account = self.db.query(Account).filter(
            Account.business_id == bill.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        if vendor_advances_account and payable_account:
            # Debit Accounts Payable (reduce liability - we owe less)
            debit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Applied vendor advance to Bill {bill.bill_number}",
                debit=amount_to_apply,
                credit=Decimal("0"),
                account_id=payable_account.id,
                vendor_id=vendor.id,
                purchase_bill_id=bill.id,
                branch_id=bill.branch_id
            )
            self.db.add(debit_entry)
            
            # Credit Vendor Advances (reduce asset - we used our prepayment)
            credit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Applied vendor advance to Bill {bill.bill_number}",
                debit=Decimal("0"),
                credit=amount_to_apply,
                account_id=vendor_advances_account.id,
                vendor_id=vendor.id,
                purchase_bill_id=bill.id,
                branch_id=bill.branch_id
            )
            self.db.add(credit_entry)
        
        # Note: No CashBookEntry is created here because this is NOT a cash transaction.
        # The money was already recorded in CashBook when we funded the vendor's account.
        # This is just an internal adjustment between asset (Vendor Advances) and liability (AP).
    
    def _create_ledger_entries(self, bill: PurchaseBill):
        """Create double-entry ledger entries for purchase bill"""
        # Get accounts
        payable_account = self.db.query(Account).filter(
            Account.business_id == bill.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        inventory_account = self.db.query(Account).filter(
            Account.business_id == bill.business_id,
            Account.name == "Inventory"
        ).first()
        
        if not payable_account or not inventory_account:
            return
        
        # Debit Inventory
        debit_entry = LedgerEntry(
            transaction_date=bill.bill_date,
            description=f"Purchase Bill {bill.bill_number}",
            debit=bill.sub_total,
            credit=Decimal("0"),
            account_id=inventory_account.id,
            vendor_id=bill.vendor_id,
            purchase_bill_id=bill.id,
            branch_id=bill.branch_id
        )
        self.db.add(debit_entry)
        
        # Credit Accounts Payable
        credit_entry = LedgerEntry(
            transaction_date=bill.bill_date,
            description=f"Purchase Bill {bill.bill_number}",
            debit=Decimal("0"),
            credit=bill.total_amount,
            account_id=payable_account.id,
            vendor_id=bill.vendor_id,
            purchase_bill_id=bill.id,
            branch_id=bill.branch_id
        )
        self.db.add(credit_entry)
        
        # Debit VAT Receivable if applicable
        if bill.vat_amount > 0:
            vat_account = self.db.query(Account).filter(
                Account.business_id == bill.business_id,
                Account.name == "VAT Payable"
            ).first()
            
            if vat_account:
                vat_entry = LedgerEntry(
                    transaction_date=bill.bill_date,
                    description=f"VAT for Purchase Bill {bill.bill_number}",
                    debit=bill.vat_amount,
                    credit=Decimal("0"),
                    account_id=vat_account.id,
                    vendor_id=bill.vendor_id,
                    purchase_bill_id=bill.id,
                    branch_id=bill.branch_id
                )
                self.db.add(vat_entry)
    
    def _get_account_balance(self, account_id: int, branch_id: int) -> Decimal:
        """Get current balance of a cash/bank account from ledger entries"""
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == account_id,
            LE.branch_id == branch_id
        ).scalar() or Decimal("0")
        
        return balance
    
    def record_payment(self, bill_id: int, payment_data: dict, business_id: int) -> PurchaseBill:
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        bill = self.get_by_id(bill_id, business_id)
        if not bill:
            raise ValueError("Bill not found")

        amount = payment_data["amount"]
        payment_account_id = payment_data["payment_account_id"]
        payment_date = payment_data["payment_date"]
        bank_account_id = payment_data.get("bank_account_id")  # May be None for cash accounts

        # Get accounts
        cash_account = self.db.query(Account).filter(
            Account.id == payment_account_id,
            Account.business_id == business_id
        ).first()

        payable_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Accounts Payable"
        ).first()

        # Validate accounts exist
        if not cash_account:
            raise ValueError(f"Payment account not found. Please select a valid cash/bank account.")

        if not payable_account:
            raise ValueError(f"Accounts Payable account not found. Please check your Chart of Accounts setup.")
        
        # Check if account has sufficient balance before processing payment
        current_balance = self._get_account_balance(cash_account.id, bill.branch_id)
        if current_balance < amount:
            raise ValueError(
                f"Insufficient funds in '{cash_account.name}'. "
                f"Available balance: {float(current_balance):,.2f}, "
                f"Payment amount: {float(amount):,.2f}"
            )

        # Calculate effective balance (total - paid - returned)
        returned_amount = bill.returned_amount or Decimal("0")
        effective_total = bill.total_amount - returned_amount
        
        # Validate payment doesn't exceed outstanding balance
        outstanding_balance = effective_total - bill.paid_amount
        if amount > outstanding_balance:
            raise ValueError(
                f"Payment amount ({amount:.2f}) exceeds outstanding balance ({outstanding_balance:.2f}). "
                f"Total: {bill.total_amount:.2f}, Already Paid: {bill.paid_amount:.2f}, Returned: {returned_amount:.2f}"
            )

        # Update bill
        bill.paid_amount += amount
        # Status is based on effective total (total - returns)
        if bill.paid_amount >= effective_total:
            bill.status = "Paid"
        elif bill.paid_amount > 0:
            bill.status = "Partial"

        # Debit Accounts Payable (decrease liability)
        debit_entry = LedgerEntry(
            transaction_date=payment_date,
            description=f"Payment for Bill {bill.bill_number}",
            debit=amount,
            credit=Decimal("0"),
            account_id=payable_account.id,
            vendor_id=bill.vendor_id,
            purchase_bill_id=bill.id,
            branch_id=bill.branch_id
        )
        self.db.add(debit_entry)

        # Credit Cash/Bank (decrease asset)
        # Include bank_account_id if this is a bank payment
        credit_entry = LedgerEntry(
            transaction_date=payment_date,
            description=f"Payment for Bill {bill.bill_number}",
            debit=Decimal("0"),
            credit=amount,
            account_id=cash_account.id,
            bank_account_id=int(bank_account_id) if bank_account_id else None,
            vendor_id=bill.vendor_id,
            purchase_bill_id=bill.id,
            branch_id=bill.branch_id
        )
        self.db.add(credit_entry)

        # Create Cash Book Entry
        self._create_cashbook_entry(bill, amount, payment_account_id, cash_account, payment_date, bank_account_id)

        self.db.flush()
        return bill
    
    def _create_cashbook_entry(self, bill: PurchaseBill, amount: Decimal,
                                payment_account_id: int, cash_account: Account, payment_date: date,
                                bank_account_id: int = None):
        """Create a cash book entry for bill payment"""
        from app.models import CashBookEntry
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        # Determine account type (cash or bank)
        account_type = "cash"
        if hasattr(cash_account, 'bank_accounts') and cash_account.bank_accounts:
            account_type = "bank"
        elif cash_account.name and 'bank' in cash_account.name.lower():
            account_type = "bank"
        
        # Get current balance from ledger
        current_balance = self.db.query(
            func.sum(LE.debit - LE.credit)
        ).filter(
            LE.account_id == cash_account.id,
            LE.branch_id == bill.branch_id
        ).scalar() or Decimal("0")
        
        # Generate entry number
        prefix = "CP"  # Cash Payment
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == bill.business_id,
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
            entry_type="payment",
            account_id=cash_account.id,
            account_type=account_type,
            amount=amount,
            balance_after=current_balance - amount,
            description=f"Payment to {bill.vendor.name if bill.vendor else 'Vendor'} - Bill {bill.bill_number}",
            reference=bill.bill_number,
            payee_payer=bill.vendor.name if bill.vendor else None,
            source_type="purchase_payment",
            source_id=bill.id,
            branch_id=bill.branch_id,
            business_id=bill.business_id
        )
        self.db.add(cashbook_entry)


class DebitNoteService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, debit_note_id: int, business_id: int, branch_id: int = None) -> Optional[DebitNote]:
        query = self.db.query(DebitNote).options(
            joinedload(DebitNote.items).joinedload(DebitNoteItem.product),
            joinedload(DebitNote.purchase_bill).joinedload(PurchaseBill.vendor)
        ).filter(
            DebitNote.id == debit_note_id,
            DebitNote.business_id == business_id
        )
        if branch_id:
            query = query.filter(DebitNote.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int) -> List[DebitNote]:
        return self.db.query(DebitNote).options(
            joinedload(DebitNote.purchase_bill).joinedload(PurchaseBill.vendor)
        ).filter(
            DebitNote.business_id == business_id,
            DebitNote.branch_id == branch_id
        ).order_by(DebitNote.created_at.desc()).all()
    
    def get_next_number(self, business_id: int) -> str:
        last_dn = self.db.query(DebitNote).filter(
            DebitNote.business_id == business_id
        ).order_by(DebitNote.id.desc()).first()
        
        if last_dn:
            try:
                num = int(last_dn.debit_note_number.replace("DN-", ""))
                return f"DN-{num + 1:05d}"
            except ValueError:
                pass
        
        return "DN-00001"
    
    def create_for_bill(self, original_bill: PurchaseBill, items_to_return: List[dict], debit_note_date: date, reason: str = "Purchase Return") -> DebitNote:
        """
        Create a debit note for returning goods to vendor.
        
        This will:
        1. Reduce inventory for returned items
        2. Update returned_quantity on original purchase bill items
        3. Create the debit note record with vendor_id and status
        """
        total_amount = sum(item["quantity"] * item["price"] for item in items_to_return)
        
        debit_note = DebitNote(
            debit_note_number=self.get_next_number(original_bill.business_id),
            debit_note_date=debit_note_date,
            total_amount=total_amount,
            reason=reason,
            status='open',
            purchase_bill_id=original_bill.id,
            vendor_id=original_bill.vendor_id,
            branch_id=original_bill.branch_id,
            business_id=original_bill.business_id
        )
        self.db.add(debit_note)
        self.db.flush()
        
        for item_data in items_to_return:
            # Create debit note item with original_item_id
            dn_item = DebitNoteItem(
                debit_note_id=debit_note.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"],
                original_item_id=item_data.get("original_item_id")
            )
            self.db.add(dn_item)
            
            # Reduce product stock - when returning goods to vendor, inventory decreases
            product = self.db.query(Product).get(item_data["product_id"])
            if product:
                if product.stock_quantity < item_data["quantity"]:
                    raise ValueError(f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Trying to return: {item_data['quantity']}")
                product.stock_quantity -= item_data["quantity"]
            
            # Update returned quantity on original purchase bill item
            orig_item = self.db.query(PurchaseBillItem).get(item_data.get("original_item_id"))
            if orig_item:
                orig_item.returned_quantity += item_data["quantity"]
        
        # Create ledger entries for the debit note
        self._create_debit_note_ledger_entries(debit_note, original_bill)
        
        self.db.flush()
        return debit_note
    
    def _create_debit_note_ledger_entries(self, debit_note: DebitNote, original_bill: PurchaseBill):
        """Create double-entry ledger entries for debit note (purchase return)"""
        # Get accounts - try by name first, then by code as fallback
        payable_account = self.db.query(Account).filter(
            Account.business_id == debit_note.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        if not payable_account:
            # Fallback to code-based lookup
            payable_account = self.db.query(Account).filter(
                Account.business_id == debit_note.business_id,
                Account.code == "2000"
            ).first()
        
        inventory_account = self.db.query(Account).filter(
            Account.business_id == debit_note.business_id,
            Account.name == "Inventory"
        ).first()
        
        if not inventory_account:
            # Fallback to code-based lookup
            inventory_account = self.db.query(Account).filter(
                Account.business_id == debit_note.business_id,
                Account.code == "1300"
            ).first()
        
        if not payable_account or not inventory_account:
            print(f"Warning: Could not find accounts for debit note ledger entries. "
                  f"AP found: {payable_account is not None}, Inventory found: {inventory_account is not None}")
            return
        
        # Debit Accounts Payable (reduce liability - we owe vendor less)
        debit_entry = LedgerEntry(
            transaction_date=debit_note.debit_note_date,
            description=f"Debit Note {debit_note.debit_note_number} - Return to Vendor",
            debit=debit_note.total_amount,
            credit=Decimal("0"),
            account_id=payable_account.id,
            vendor_id=debit_note.vendor_id,
            debit_note_id=debit_note.id,
            branch_id=debit_note.branch_id
        )
        self.db.add(debit_entry)
        
        # Credit Inventory (reduce asset - goods returned to vendor)
        credit_entry = LedgerEntry(
            transaction_date=debit_note.debit_note_date,
            description=f"Debit Note {debit_note.debit_note_number} - Return to Vendor",
            debit=Decimal("0"),
            credit=debit_note.total_amount,
            account_id=inventory_account.id,
            vendor_id=debit_note.vendor_id,
            debit_note_id=debit_note.id,
            branch_id=debit_note.branch_id
        )
        self.db.add(credit_entry)
        
        print(f"Created ledger entries for Debit Note {debit_note.debit_note_number}: "
              f"Debit AP {debit_note.total_amount}, Credit Inventory {debit_note.total_amount}")
    
    def apply_debit_note(self, debit_note_id: int, business_id: int, refund_method: str = 'none',
                         refund_account_id: int = None, refund_date: date = None) -> DebitNote:
        """
        Apply a debit note to reduce the bill balance.
        
        For paid bills, this handles the refund:
        - 'none': Just track the return, no refund needed (bill had outstanding balance)
        - 'vendor_balance': Add refund amount to vendor's pre-paid balance (we have credit with them)
        - 'cash_refund': Receive cash/bank refund from vendor
        
        Args:
            debit_note_id: The debit note to apply
            business_id: Business ID for security
            refund_method: How to handle refund ('none', 'vendor_balance', 'cash_refund')
            refund_account_id: Cash/bank account for cash refund
            refund_date: Date for refund transaction
        """
        debit_note = self.db.query(DebitNote).filter(
            DebitNote.id == debit_note_id,
            DebitNote.business_id == business_id
        ).first()
        
        if not debit_note:
            raise ValueError("Debit note not found")
        
        if debit_note.status != 'open':
            raise ValueError(f"Debit note is already {debit_note.status}")
        
        # Get the original bill
        bill = self.db.query(PurchaseBill).get(debit_note.purchase_bill_id)
        if not bill:
            raise ValueError("Original bill not found")
        
        # Get vendor
        vendor = self.db.query(Vendor).get(debit_note.vendor_id)
        
        # Track previous returns to calculate refundable amount correctly
        previous_returned = bill.returned_amount or Decimal("0.00")
        
        # Update bill returned_amount (track returns separately from payments)
        if not hasattr(bill, 'returned_amount') or bill.returned_amount is None:
            bill.returned_amount = Decimal("0.00")
        bill.returned_amount += debit_note.total_amount
        
        # Calculate the effective balance: total - paid - returned
        effective_balance = bill.total_amount - bill.paid_amount - bill.returned_amount
        
        # Calculate refundable amount for paid bills
        # If we paid more than what we now owe (after returns), vendor owes us a refund
        refund_amount = Decimal("0.00")
        if bill.paid_amount > 0:
            # How much of this debit note's value was already paid for?
            # Refund = min(debit_note_amount, paid_amount - previous_returns)
            paid_before_this_return = bill.paid_amount - previous_returned
            if paid_before_this_return > 0:
                refund_amount = min(debit_note.total_amount, paid_before_this_return)
        
        # Handle refund if applicable
        if refund_amount > 0 and refund_method != 'none':
            if refund_method == 'vendor_balance':
                # Add to vendor's pre-paid balance (we have credit with them)
                self._refund_to_vendor_balance(debit_note, bill, vendor, refund_amount)
            elif refund_method == 'cash_refund':
                # Receive cash/bank refund from vendor
                if not refund_account_id:
                    raise ValueError("Refund account is required for cash refunds")
                if not refund_date:
                    refund_date = date.today()
                self._refund_to_cash_account(debit_note, bill, vendor, refund_amount, 
                                            refund_account_id, refund_date)
        
        # Update bill status based on effective balance
        if effective_balance <= 0:
            bill.status = "Returned"  # All items returned or balance is zero
        elif bill.returned_amount > 0 or bill.paid_amount > 0:
            bill.status = "Partial"  # Partially paid or returned
        else:
            bill.status = "Unpaid"
        
        # Mark debit note as applied
        debit_note.status = 'applied'
        
        self.db.flush()
        return debit_note
    
    def _refund_to_vendor_balance(self, debit_note: DebitNote, bill: PurchaseBill,
                                  vendor: Vendor, refund_amount: Decimal):
        """
        Add refund amount to vendor's pre-paid balance.
        
        This is NOT a cash transaction - we're getting store credit with the vendor.
        The business can use this balance for future purchases from this vendor.
        """
        from datetime import date as today_date
        
        # Update vendor balance
        vendor.account_balance = (vendor.account_balance or Decimal("0.00")) + refund_amount
        
        # Get the Vendor Advances account (asset account)
        vendor_advances_account = self.db.query(Account).filter(
            Account.business_id == debit_note.business_id,
            Account.name.ilike('%Vendor Advance%')
        ).first()
        
        # Get Accounts Payable account
        payable_account = self.db.query(Account).filter(
            Account.business_id == debit_note.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        if vendor_advances_account and payable_account:
            # Debit Vendor Advances (increase asset - we have more credit with vendor)
            debit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Refund from Debit Note {debit_note.debit_note_number} - Added to vendor balance",
                debit=refund_amount,
                credit=Decimal("0"),
                account_id=vendor_advances_account.id,
                vendor_id=vendor.id,
                debit_note_id=debit_note.id,
                branch_id=debit_note.branch_id
            )
            self.db.add(debit_entry)
            
            # Credit Accounts Payable (reduce liability further since we're getting credit)
            credit_entry = LedgerEntry(
                transaction_date=today_date.today(),
                description=f"Refund from Debit Note {debit_note.debit_note_number} - Added to vendor balance",
                debit=Decimal("0"),
                credit=refund_amount,
                account_id=payable_account.id,
                vendor_id=vendor.id,
                debit_note_id=debit_note.id,
                branch_id=debit_note.branch_id
            )
            self.db.add(credit_entry)
    
    def _refund_to_cash_account(self, debit_note: DebitNote, bill: PurchaseBill,
                                vendor: Vendor, refund_amount: Decimal,
                                refund_account_id: int, refund_date: date):
        """
        Receive a cash/bank refund from the vendor.
        
        This creates:
        1. Ledger entries (Debit Cash/Bank, Credit Accounts Payable)
        2. CashBook entry (receipt)
        """
        from app.models import CashBookEntry
        from sqlalchemy import func
        from app.models import LedgerEntry as LE
        
        # Get the refund account
        refund_account = self.db.query(Account).filter(
            Account.id == refund_account_id,
            Account.business_id == debit_note.business_id
        ).first()
        
        if not refund_account:
            raise ValueError("Refund account not found")
        
        # Get Accounts Payable account
        payable_account = self.db.query(Account).filter(
            Account.business_id == debit_note.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        if not payable_account:
            raise ValueError("Accounts Payable account not found")
        
        # Debit Cash/Bank (increase asset - money coming in)
        debit_entry = LedgerEntry(
            transaction_date=refund_date,
            description=f"Refund from Vendor for Debit Note {debit_note.debit_note_number}",
            debit=refund_amount,
            credit=Decimal("0"),
            account_id=refund_account.id,
            vendor_id=vendor.id if vendor else None,
            debit_note_id=debit_note.id,
            branch_id=debit_note.branch_id
        )
        self.db.add(debit_entry)
        
        # Credit Accounts Payable (reduce liability)
        credit_entry = LedgerEntry(
            transaction_date=refund_date,
            description=f"Refund from Vendor for Debit Note {debit_note.debit_note_number}",
            debit=Decimal("0"),
            credit=refund_amount,
            account_id=payable_account.id,
            vendor_id=vendor.id if vendor else None,
            debit_note_id=debit_note.id,
            branch_id=debit_note.branch_id
        )
        self.db.add(credit_entry)
        
        # Create CashBook Entry (receipt)
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
            LE.branch_id == debit_note.branch_id
        ).scalar() or Decimal("0")
        
        # Generate entry number
        prefix = "CR"  # Cash Receipt
        last_entry = self.db.query(CashBookEntry).filter(
            CashBookEntry.business_id == debit_note.business_id,
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
        
        # Create cash book entry (receipt)
        cashbook_entry = CashBookEntry(
            entry_number=entry_number,
            entry_date=refund_date,
            entry_type="receipt",
            account_id=refund_account.id,
            account_type=account_type,
            amount=refund_amount,
            balance_after=current_balance + refund_amount,
            description=f"Refund from {vendor.name if vendor else 'Vendor'} - Debit Note {debit_note.debit_note_number}",
            reference=debit_note.debit_note_number,
            payee_payer=vendor.name if vendor else None,
            source_type="debit_note_refund",
            source_id=debit_note.id,
            branch_id=debit_note.branch_id,
            business_id=debit_note.business_id
        )
        self.db.add(cashbook_entry)
        
        # Track refund amount on debit note
        debit_note.refund_amount = refund_amount
        debit_note.refund_method = 'cash'
        debit_note.refund_date = refund_date
