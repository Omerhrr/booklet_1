"""
CRM Service - Business Logic for Customers and Vendors
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from app.models import Customer, Vendor, SalesInvoice, PurchaseBill, LedgerEntry, CreditNote, DebitNote, Account
from app.schemas import CustomerCreate, CustomerUpdate, VendorCreate, VendorUpdate


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, customer_id: int, business_id: int, branch_id: int = None) -> Optional[Customer]:
        query = self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.business_id == business_id
        )
        if branch_id:
            query = query.filter(Customer.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, include_inactive: bool = False) -> List[Customer]:
        query = self.db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.branch_id == branch_id
        )
        if not include_inactive:
            query = query.filter(Customer.is_active == True)
        return query.all()
    
    def get_all_by_business(self, business_id: int) -> List[Customer]:
        return self.db.query(Customer).filter(Customer.business_id == business_id).all()
    
    def create(self, customer_data: CustomerCreate, business_id: int, branch_id: int) -> Customer:
        customer = Customer(
            name=customer_data.name,
            email=customer_data.email,
            phone=customer_data.phone,
            address=customer_data.address,
            tax_id=customer_data.tax_id,
            credit_limit=customer_data.credit_limit,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(customer)
        self.db.flush()
        return customer
    
    def update(self, customer_id: int, business_id: int, customer_data: CustomerUpdate, branch_id: int = None) -> Optional[Customer]:
        customer = self.get_by_id(customer_id, business_id, branch_id)
        if not customer:
            return None
        
        update_data = customer_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer, key, value)
        
        self.db.flush()
        return customer
    
    def delete(self, customer_id: int, business_id: int, branch_id: int = None) -> bool:
        customer = self.get_by_id(customer_id, business_id, branch_id)
        if not customer:
            return False
        
        # Check for related invoices
        has_invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.customer_id == customer_id
        ).first()
        
        if has_invoices:
            # Soft delete instead
            customer.is_active = False
        else:
            self.db.delete(customer)
        
        return True
    
    def get_balance(self, customer_id: int) -> dict:
        """Calculate customer's outstanding balance with details"""
        # Get customer first with null check
        customer = self.db.query(Customer).get(customer_id)
        if not customer:
            return {
                "outstanding_balance": Decimal("0.00"),
                "outstanding_invoices": 0,
                "credit_notes": 0
            }
        
        # Get Accounts Receivable account
        receivable_account = self.db.query(Account).filter(
            Account.business_id == customer.business_id,
            Account.name == "Accounts Receivable"
        ).first()
        
        # Calculate balance from ledger entries (only AR account entries)
        balance = Decimal("0.00")
        if receivable_account:
            result = self.db.query(LedgerEntry).filter(
                LedgerEntry.customer_id == customer_id,
                LedgerEntry.account_id == receivable_account.id
            ).all()
            
            for entry in result:
                # For AR: debit increases asset, credit decreases it
                balance += entry.debit - entry.credit
        
        # Count outstanding invoices
        outstanding_invoices = self.db.query(func.count(SalesInvoice.id)).filter(
            SalesInvoice.customer_id == customer_id,
            SalesInvoice.status.in_(["Unpaid", "Partial", "Pending"])
        ).scalar() or 0
        
        # Count credit notes
        credit_notes_count = self.db.query(func.count(CreditNote.id)).filter(
            CreditNote.customer_id == customer_id
        ).scalar() or 0
        
        return {
            "outstanding_balance": balance,
            "outstanding_invoices": outstanding_invoices,
            "credit_notes": credit_notes_count
        }
    
    def get_invoices(self, customer_id: int, business_id: int) -> List[SalesInvoice]:
        """Get all invoices for a customer"""
        return self.db.query(SalesInvoice).filter(
            SalesInvoice.customer_id == customer_id,
            SalesInvoice.business_id == business_id
        ).order_by(SalesInvoice.created_at.desc()).limit(20).all()
    
    def get_credit_notes(self, customer_id: int, business_id: int) -> List[CreditNote]:
        """Get all credit notes for a customer"""
        return self.db.query(CreditNote).filter(
            CreditNote.customer_id == customer_id,
            CreditNote.business_id == business_id
        ).order_by(CreditNote.created_at.desc()).limit(20).all()
    
    def get_with_balance(self, customer_id: int, business_id: int) -> dict:
        customer = self.get_by_id(customer_id, business_id)
        if not customer:
            return None
        
        balance = self.get_balance(customer_id)
        
        return {
            **customer.__dict__,
            "total_outstanding": balance["outstanding_balance"]
        }


class VendorService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, vendor_id: int, business_id: int, branch_id: int = None) -> Optional[Vendor]:
        query = self.db.query(Vendor).filter(
            Vendor.id == vendor_id,
            Vendor.business_id == business_id
        )
        if branch_id:
            query = query.filter(Vendor.branch_id == branch_id)
        return query.first()
    
    def get_by_branch(self, branch_id: int, business_id: int, include_inactive: bool = False) -> List[Vendor]:
        query = self.db.query(Vendor).filter(
            Vendor.business_id == business_id,
            Vendor.branch_id == branch_id
        )
        if not include_inactive:
            query = query.filter(Vendor.is_active == True)
        return query.all()
    
    def get_all_by_business(self, business_id: int) -> List[Vendor]:
        return self.db.query(Vendor).filter(Vendor.business_id == business_id).all()
    
    def create(self, vendor_data: VendorCreate, business_id: int, branch_id: int) -> Vendor:
        vendor = Vendor(
            name=vendor_data.name,
            email=vendor_data.email,
            phone=vendor_data.phone,
            address=vendor_data.address,
            tax_id=vendor_data.tax_id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(vendor)
        self.db.flush()
        return vendor
    
    def update(self, vendor_id: int, business_id: int, vendor_data: VendorUpdate, branch_id: int = None) -> Optional[Vendor]:
        vendor = self.get_by_id(vendor_id, business_id, branch_id)
        if not vendor:
            return None
        
        update_data = vendor_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vendor, key, value)
        
        self.db.flush()
        return vendor
    
    def delete(self, vendor_id: int, business_id: int, branch_id: int = None) -> bool:
        vendor = self.get_by_id(vendor_id, business_id, branch_id)
        if not vendor:
            return False
        
        # Check for related bills
        has_bills = self.db.query(PurchaseBill).filter(
            PurchaseBill.vendor_id == vendor_id
        ).first()
        
        if has_bills:
            vendor.is_active = False
        else:
            self.db.delete(vendor)
        
        return True
    
    def get_balance(self, vendor_id: int) -> dict:
        """Calculate vendor's outstanding balance with details"""
        # Get vendor first with null check
        vendor = self.db.query(Vendor).get(vendor_id)
        if not vendor:
            return {
                "outstanding_balance": Decimal("0.00"),
                "outstanding_bills": 0,
                "debit_notes": 0
            }
        
        # Get Accounts Payable account
        payable_account = self.db.query(Account).filter(
            Account.business_id == vendor.business_id,
            Account.name == "Accounts Payable"
        ).first()
        
        # Calculate balance from ledger entries (only AP account entries)
        balance = Decimal("0.00")
        if payable_account:
            result = self.db.query(LedgerEntry).filter(
                LedgerEntry.vendor_id == vendor_id,
                LedgerEntry.account_id == payable_account.id
            ).all()
            
            for entry in result:
                # For AP: credit increases liability, debit decreases it
                balance += entry.credit - entry.debit
        
        # Count outstanding bills
        outstanding_bills = self.db.query(func.count(PurchaseBill.id)).filter(
            PurchaseBill.vendor_id == vendor_id,
            PurchaseBill.status.in_(["Unpaid", "Partial", "Pending"])
        ).scalar() or 0
        
        # Count debit notes
        debit_notes_count = self.db.query(func.count(DebitNote.id)).filter(
            DebitNote.vendor_id == vendor_id
        ).scalar() or 0
        
        return {
            "outstanding_balance": balance,
            "outstanding_bills": outstanding_bills,
            "debit_notes": debit_notes_count
        }
    
    def get_bills(self, vendor_id: int, business_id: int) -> List[PurchaseBill]:
        """Get all bills for a vendor"""
        return self.db.query(PurchaseBill).filter(
            PurchaseBill.vendor_id == vendor_id,
            PurchaseBill.business_id == business_id
        ).order_by(PurchaseBill.created_at.desc()).limit(20).all()
    
    def get_debit_notes(self, vendor_id: int, business_id: int) -> List[DebitNote]:
        """Get all debit notes for a vendor"""
        return self.db.query(DebitNote).filter(
            DebitNote.vendor_id == vendor_id,
            DebitNote.business_id == business_id
        ).order_by(DebitNote.created_at.desc()).limit(20).all()
