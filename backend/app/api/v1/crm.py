"""
CRM API Routes - Customers and Vendors
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    VendorCreate, VendorUpdate, VendorResponse, MessageResponse
)
from app.services.crm_service import CustomerService, VendorService

router = APIRouter(prefix="/crm", tags=["CRM"])


# ==================== CUSTOMERS ====================

@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all customers for current branch"""
    customer_service = CustomerService(db)
    return customer_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        include_inactive
    )


@router.post("/customers", response_model=CustomerResponse, dependencies=[Depends(PermissionChecker(["customers:create"]))])
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new customer"""
    customer_service = CustomerService(db)
    customer = customer_service.create(
        customer_data, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    db.commit()
    return customer


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customer by ID with balance"""
    customer_service = CustomerService(db)
    customer = customer_service.get_by_id(
        customer_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get balance
    balance = customer_service.get_balance(customer_id)
    outstanding_balance = balance.get("outstanding_balance", 0) if balance else 0
    
    # Get outstanding invoices count
    from app.models import SalesInvoice
    from sqlalchemy import func
    outstanding_invoices = db.query(SalesInvoice).filter(
        SalesInvoice.customer_id == customer_id,
        SalesInvoice.status.in_(['Unpaid', 'Partial', 'pending', 'partial'])
    ).count()
    
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "tax_id": customer.tax_id,
        "credit_limit": float(customer.credit_limit) if customer.credit_limit else 0,
        "account_balance": float(customer.account_balance) if customer.account_balance else 0,
        "is_active": customer.is_active,
        "branch_id": customer.branch_id,
        "business_id": customer.business_id,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "outstanding_balance": float(outstanding_balance),
        "outstanding_invoices": outstanding_invoices
    }


@router.put("/customers/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(PermissionChecker(["customers:edit"]))])
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update customer"""
    customer_service = CustomerService(db)
    customer = customer_service.update(
        customer_id, 
        current_user.business_id, 
        customer_data,
        current_user.selected_branch.id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.commit()
    return customer


@router.delete("/customers/{customer_id}", dependencies=[Depends(PermissionChecker(["customers:delete"]))])
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete customer"""
    customer_service = CustomerService(db)
    if not customer_service.delete(
        customer_id, 
        current_user.business_id,
        current_user.selected_branch.id
    ):
        raise HTTPException(status_code=404, detail="Customer not found")
    db.commit()
    return {"message": "Customer deleted successfully"}


@router.get("/customers/{customer_id}/balance")
async def get_customer_balance(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customer outstanding balance with details"""
    customer_service = CustomerService(db)
    return customer_service.get_balance(customer_id)


@router.get("/customers/{customer_id}/invoices")
async def get_customer_invoices(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customer invoices"""
    customer_service = CustomerService(db)
    invoices = customer_service.get_invoices(customer_id, current_user.business_id)
    
    # Serialize invoices
    result = []
    for inv in invoices:
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "total_amount": float(inv.total_amount) if inv.total_amount else 0,
            "paid_amount": float(inv.paid_amount) if inv.paid_amount else 0,
            "returned_amount": float(inv.returned_amount) if inv.returned_amount else 0,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        })
    
    return result


@router.get("/customers/{customer_id}/credit-notes")
async def get_customer_credit_notes(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customer credit notes"""
    customer_service = CustomerService(db)
    credit_notes = customer_service.get_credit_notes(customer_id, current_user.business_id)
    return credit_notes


@router.get("/customers/{customer_id}/payments")
async def get_customer_payments(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get customer payment history"""
    from app.models import Payment, CashBookEntry, SalesInvoice, LedgerEntry, Account
    from sqlalchemy import func
    
    # Get all payments for this customer's invoices
    payments = db.query(Payment).join(
        SalesInvoice, Payment.sales_invoice_id == SalesInvoice.id
    ).filter(
        SalesInvoice.customer_id == customer_id,
        SalesInvoice.business_id == current_user.business_id
    ).order_by(Payment.payment_date.desc()).all()
    
    result = []
    for p in payments:
        invoice = db.query(SalesInvoice).filter(SalesInvoice.id == p.sales_invoice_id).first()
        result.append({
            "id": p.id,
            "payment_number": p.payment_number,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "amount": float(p.amount) if p.amount else 0,
            "payment_method": p.payment_method,
            "reference": p.reference,
            "invoice_id": p.sales_invoice_id,
            "invoice_number": invoice.invoice_number if invoice else None,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    
    # Also get cashbook entries for customer advance payments
    advance_entries = db.query(CashBookEntry).filter(
        CashBookEntry.source_type == "customer_advance",
        CashBookEntry.business_id == current_user.business_id
    ).all()
    
    # Get customer advance payments from ledger entries
    customer_advance_account = db.query(Account).filter(
        Account.business_id == current_user.business_id,
        Account.name.ilike('%Customer Advance%')
    ).first()
    
    if customer_advance_account:
        advance_ledger_entries = db.query(LedgerEntry).filter(
            LedgerEntry.account_id == customer_advance_account.id,
            LedgerEntry.customer_id == customer_id,
            LedgerEntry.branch_id == current_user.selected_branch.id
        ).order_by(LedgerEntry.transaction_date.desc()).all()
        
        for entry in advance_ledger_entries:
            if entry.debit and entry.debit > 0:
                # This is an advance being used
                result.append({
                    "id": f"advance-{entry.id}",
                    "payment_number": "ADV-USED",
                    "payment_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                    "amount": float(entry.debit),
                    "payment_method": "Advance Balance",
                    "reference": entry.description,
                    "invoice_id": entry.sales_invoice_id,
                    "invoice_number": None,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "type": "advance_used"
                })
            elif entry.credit and entry.credit > 0:
                # This is an advance received
                result.append({
                    "id": f"advance-{entry.id}",
                    "payment_number": "ADV-RECV",
                    "payment_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                    "amount": float(entry.credit),
                    "payment_method": "Advance Payment",
                    "reference": entry.description,
                    "invoice_id": None,
                    "invoice_number": None,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "type": "advance_received"
                })
    
    # Sort by date descending
    result.sort(key=lambda x: x['payment_date'] if x['payment_date'] else '', reverse=True)
    
    return result


@router.post("/customers/{customer_id}/toggle-status", dependencies=[Depends(PermissionChecker(["customers:edit"]))])
async def toggle_customer_status(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle customer active status"""
    customer_service = CustomerService(db)
    customer = customer_service.get_by_id(
        customer_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.is_active = not customer.is_active
    db.commit()
    return {"message": f"Customer {'activated' if customer.is_active else 'deactivated'}", "is_active": customer.is_active}


# ==================== VENDORS ====================

@router.get("/vendors", response_model=List[VendorResponse])
async def list_vendors(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all vendors for current branch"""
    vendor_service = VendorService(db)
    return vendor_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        include_inactive
    )


@router.post("/vendors", response_model=VendorResponse, dependencies=[Depends(PermissionChecker(["vendors:create"]))])
async def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new vendor"""
    vendor_service = VendorService(db)
    vendor = vendor_service.create(
        vendor_data, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    db.commit()
    return vendor


@router.get("/vendors/{vendor_id}")
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendor by ID with balance"""
    vendor_service = VendorService(db)
    vendor = vendor_service.get_by_id(
        vendor_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Get balance
    balance = vendor_service.get_balance(vendor_id)
    outstanding_balance = balance.get("outstanding_balance", 0) if balance else 0
    
    # Get outstanding bills count
    from app.models import PurchaseBill
    outstanding_bills = db.query(PurchaseBill).filter(
        PurchaseBill.vendor_id == vendor_id,
        PurchaseBill.status.in_(['Unpaid', 'Partial', 'pending', 'partial'])
    ).count()
    
    return {
        "id": vendor.id,
        "name": vendor.name,
        "email": vendor.email,
        "phone": vendor.phone,
        "address": vendor.address,
        "tax_id": vendor.tax_id,
        "account_balance": float(vendor.account_balance) if vendor.account_balance else 0,
        "is_active": vendor.is_active,
        "branch_id": vendor.branch_id,
        "business_id": vendor.business_id,
        "created_at": vendor.created_at.isoformat() if vendor.created_at else None,
        "outstanding_balance": float(outstanding_balance),
        "outstanding_bills": outstanding_bills
    }


@router.put("/vendors/{vendor_id}", response_model=VendorResponse, dependencies=[Depends(PermissionChecker(["vendors:edit"]))])
async def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update vendor"""
    vendor_service = VendorService(db)
    vendor = vendor_service.update(
        vendor_id, 
        current_user.business_id, 
        vendor_data,
        current_user.selected_branch.id
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.commit()
    return vendor


@router.delete("/vendors/{vendor_id}", dependencies=[Depends(PermissionChecker(["vendors:delete"]))])
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete vendor"""
    vendor_service = VendorService(db)
    if not vendor_service.delete(
        vendor_id, 
        current_user.business_id,
        current_user.selected_branch.id
    ):
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.commit()
    return {"message": "Vendor deleted successfully"}


@router.get("/vendors/{vendor_id}/balance")
async def get_vendor_balance(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendor outstanding balance with details"""
    vendor_service = VendorService(db)
    return vendor_service.get_balance(vendor_id)


@router.get("/vendors/{vendor_id}/bills")
async def get_vendor_bills(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendor bills"""
    vendor_service = VendorService(db)
    bills = vendor_service.get_bills(vendor_id, current_user.business_id)
    
    # Serialize bills
    result = []
    for bill in bills:
        result.append({
            "id": bill.id,
            "bill_number": bill.bill_number,
            "bill_date": bill.bill_date.isoformat() if bill.bill_date else None,
            "due_date": bill.due_date.isoformat() if bill.due_date else None,
            "total_amount": float(bill.total_amount) if bill.total_amount else 0,
            "paid_amount": float(bill.paid_amount) if bill.paid_amount else 0,
            "returned_amount": float(bill.returned_amount) if bill.returned_amount else 0,
            "status": bill.status,
            "created_at": bill.created_at.isoformat() if bill.created_at else None
        })
    
    return result


@router.get("/vendors/{vendor_id}/debit-notes")
async def get_vendor_debit_notes(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendor debit notes"""
    vendor_service = VendorService(db)
    debit_notes = vendor_service.get_debit_notes(vendor_id, current_user.business_id)
    return debit_notes


@router.get("/vendors/{vendor_id}/payments")
async def get_vendor_payments(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get vendor payment history"""
    from app.models import LedgerEntry, Account, PurchaseBill, CashBookEntry
    
    result = []
    
    # Get ledger entries for payments made to this vendor
    # Look for credits to accounts payable (which reduce what we owe)
    payable_account = db.query(Account).filter(
        Account.business_id == current_user.business_id,
        Account.name == "Accounts Payable"
    ).first()
    
    if payable_account:
        # Get all ledger entries that credit accounts payable for this vendor
        # These represent payments made to reduce what we owe
        payment_entries = db.query(LedgerEntry).filter(
            LedgerEntry.account_id == payable_account.id,
            LedgerEntry.vendor_id == vendor_id,
            LedgerEntry.branch_id == current_user.selected_branch.id,
            LedgerEntry.debit > 0  # Debit to AP means we paid down the liability
        ).order_by(LedgerEntry.transaction_date.desc()).all()
        
        for entry in payment_entries:
            bill = None
            if entry.purchase_bill_id:
                bill = db.query(PurchaseBill).filter(PurchaseBill.id == entry.purchase_bill_id).first()
            
            result.append({
                "id": f"payment-{entry.id}",
                "payment_number": entry.reference or f"PAY-{entry.id}",
                "payment_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                "amount": float(entry.debit),
                "payment_method": "Bill Payment",
                "reference": entry.description,
                "bill_id": entry.purchase_bill_id,
                "bill_number": bill.bill_number if bill else None,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "type": "bill_payment"
            })
    
    # Get vendor advance payments
    vendor_advance_account = db.query(Account).filter(
        Account.business_id == current_user.business_id,
        Account.name.ilike('%Vendor Advance%')
    ).first()
    
    if vendor_advance_account:
        advance_ledger_entries = db.query(LedgerEntry).filter(
            LedgerEntry.account_id == vendor_advance_account.id,
            LedgerEntry.vendor_id == vendor_id,
            LedgerEntry.branch_id == current_user.selected_branch.id
        ).order_by(LedgerEntry.transaction_date.desc()).all()
        
        for entry in advance_ledger_entries:
            if entry.debit and entry.debit > 0:
                # This is an advance payment made to vendor
                result.append({
                    "id": f"advance-{entry.id}",
                    "payment_number": "ADV-PAID",
                    "payment_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                    "amount": float(entry.debit),
                    "payment_method": "Advance Payment",
                    "reference": entry.description,
                    "bill_id": None,
                    "bill_number": None,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "type": "advance_paid"
                })
            elif entry.credit and entry.credit > 0:
                # This is an advance being used
                bill = None
                if entry.purchase_bill_id:
                    bill = db.query(PurchaseBill).filter(PurchaseBill.id == entry.purchase_bill_id).first()
                result.append({
                    "id": f"advance-{entry.id}",
                    "payment_number": "ADV-USED",
                    "payment_date": entry.transaction_date.isoformat() if entry.transaction_date else None,
                    "amount": float(entry.credit),
                    "payment_method": "Advance Applied",
                    "reference": entry.description,
                    "bill_id": entry.purchase_bill_id,
                    "bill_number": bill.bill_number if bill else None,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "type": "advance_used"
                })
    
    # Sort by date descending
    result.sort(key=lambda x: x['payment_date'] if x['payment_date'] else '', reverse=True)
    
    return result


@router.post("/vendors/{vendor_id}/toggle-status", dependencies=[Depends(PermissionChecker(["vendors:edit"]))])
async def toggle_vendor_status(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle vendor active status"""
    vendor_service = VendorService(db)
    vendor = vendor_service.get_by_id(
        vendor_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_active = not vendor.is_active
    db.commit()
    return {"message": f"Vendor {'activated' if vendor.is_active else 'deactivated'}", "is_active": vendor.is_active}
