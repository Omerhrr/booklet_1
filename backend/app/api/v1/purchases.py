"""
Purchases API Routes - Bills and Debit Notes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    PurchaseBillCreate, PurchaseBillResponse, PurchaseBillWithItems,
    DebitNoteCreate, RecordBillPaymentRequest, ApplyDebitNoteRequest
)
from app.services.purchase_service import PurchaseService, DebitNoteService

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.get("/bills")
async def list_bills(
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all purchase bills"""
    purchase_service = PurchaseService(db)
    bills = purchase_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        status
    )
    # Add vendor_name to each bill
    result = []
    for bill in bills:
        bill_dict = PurchaseBillResponse.model_validate(bill).model_dump()
        bill_dict['vendor_name'] = bill.vendor.name if bill.vendor else 'N/A'
        result.append(bill_dict)
    return result


@router.post("/bills", response_model=PurchaseBillWithItems, dependencies=[Depends(PermissionChecker(["purchases:create"]))])
async def create_bill(
    bill_data: PurchaseBillCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new purchase bill"""
    purchase_service = PurchaseService(db)
    vat_rate = current_user.business.vat_rate if current_user.business.is_vat_registered else 0
    
    bill = purchase_service.create(
        bill_data,
        current_user.business_id,
        current_user.selected_branch.id,
        vat_rate
    )
    db.commit()
    return bill


@router.get("/bills/{bill_id}")
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get purchase bill by ID"""
    purchase_service = PurchaseService(db)
    bill = purchase_service.get_by_id(
        bill_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Convert to dict with additional fields
    bill_dict = PurchaseBillWithItems.model_validate(bill).model_dump()
    bill_dict['vendor_name'] = bill.vendor.name if bill.vendor else 'N/A'
    
    # Add product_name to each item
    items = []
    for item in bill.items:
        item_dict = {
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'N/A',
            'quantity': float(item.quantity),
            'returned_quantity': float(item.returned_quantity or 0),
            'price': float(item.price),
            'total': float(item.quantity * item.price)
        }
        items.append(item_dict)
    bill_dict['items'] = items
    
    # Ensure returned_amount is included
    if 'returned_amount' not in bill_dict or bill_dict.get('returned_amount') is None:
        bill_dict['returned_amount'] = 0.0
    
    return bill_dict


@router.post("/bills/{bill_id}/payment", dependencies=[Depends(PermissionChecker(["purchases:edit"]))])
async def record_bill_payment(
    bill_id: int,
    payment_data: RecordBillPaymentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record payment for purchase bill"""
    purchase_service = PurchaseService(db)
    try:
        bill = purchase_service.record_payment(
            bill_id,
            {
                "amount": payment_data.amount,
                "payment_account_id": payment_data.payment_account_id,
                "payment_date": payment_data.payment_date,
                "bank_account_id": payment_data.bank_account_id,
                "reference": payment_data.reference
            },
            current_user.business_id
        )
        db.commit()
        return {"message": "Payment recorded", "bill": PurchaseBillResponse.model_validate(bill)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/next-number")
async def get_next_bill_number(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get next bill number"""
    purchase_service = PurchaseService(db)
    return {"next_number": purchase_service.get_next_number(current_user.business_id)}


# Debit Notes
@router.get("/debit-notes")
async def list_debit_notes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all debit notes"""
    dn_service = DebitNoteService(db)
    debit_notes = dn_service.get_by_branch(current_user.selected_branch.id, current_user.business_id)
    
    # Build response with vendor name
    result = []
    for dn in debit_notes:
        result.append({
            'id': dn.id,
            'debit_note_number': dn.debit_note_number,
            'debit_note_date': dn.debit_note_date.isoformat() if dn.debit_note_date else None,
            'total_amount': float(dn.total_amount),
            'reason': dn.reason,
            'purchase_bill_id': dn.purchase_bill_id,
            'bill_number': dn.purchase_bill.bill_number if dn.purchase_bill else 'N/A',
            'vendor_name': dn.purchase_bill.vendor.name if dn.purchase_bill and dn.purchase_bill.vendor else 'N/A',
            'created_at': dn.created_at.isoformat() if dn.created_at else None
        })
    return result


@router.get("/debit-notes/{debit_note_id}")
async def get_debit_note(
    debit_note_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get debit note by ID"""
    from decimal import Decimal as D
    
    dn_service = DebitNoteService(db)
    dn = dn_service.get_by_id(
        debit_note_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not dn:
        raise HTTPException(status_code=404, detail="Debit note not found")
    
    # Build detailed response
    items = []
    for item in dn.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'N/A',
            'quantity': float(item.quantity),
            'price': float(item.price),
            'total': float(item.quantity * item.price)
        })
    
    vendor = dn.purchase_bill.vendor if dn.purchase_bill else None
    
    # Get bill payment info for refund calculation
    bill_payment_info = None
    if dn.purchase_bill:
        bill = dn.purchase_bill
        refundable_amount = D("0.00")
        if bill.paid_amount and bill.paid_amount > 0:
            # Calculate how much was paid for the returned items
            previous_returns = bill.returned_amount or D("0.00")
            if dn.status == 'open':
                # For open debit notes, show potential refund
                paid_before_this_return = bill.paid_amount - previous_returns
                if paid_before_this_return > 0:
                    refundable_amount = min(dn.total_amount, paid_before_this_return)
        
        bill_payment_info = {
            'bill_number': bill.bill_number,
            'total_amount': float(bill.total_amount),
            'paid_amount': float(bill.paid_amount or 0),
            'returned_amount': float(bill.returned_amount or 0),
            'status': bill.status,
            'refundable_amount': float(refundable_amount)
        }
    
    return {
        'id': dn.id,
        'debit_note_number': dn.debit_note_number,
        'debit_note_date': dn.debit_note_date.isoformat() if dn.debit_note_date else None,
        'total_amount': float(dn.total_amount),
        'reason': dn.reason,
        'status': dn.status or 'open',
        'refund_amount': float(dn.refund_amount or 0),
        'refund_method': dn.refund_method,
        'refund_date': dn.refund_date.isoformat() if dn.refund_date else None,
        'purchase_bill_id': dn.purchase_bill_id,
        'bill_number': dn.purchase_bill.bill_number if dn.purchase_bill else 'N/A',
        'bill_payment_info': bill_payment_info,
        'vendor_id': dn.vendor_id,
        'vendor_name': vendor.name if vendor else 'N/A',
        'vendor_email': vendor.email if vendor else None,
        'vendor_phone': vendor.phone if vendor else None,
        'vendor_address': vendor.address if vendor else None,
        'items': items,
        'created_at': dn.created_at.isoformat() if dn.created_at else None
    }


@router.post("/debit-notes", dependencies=[Depends(PermissionChecker(["debit_notes:create"]))])
async def create_debit_note(
    debit_note_data: DebitNoteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create debit note for purchase return"""
    purchase_service = PurchaseService(db)
    dn_service = DebitNoteService(db)
    
    bill = purchase_service.get_by_id(
        debit_note_data.bill_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Convert items to dict format for service
    items_to_return = [
        {
            'original_item_id': item.original_item_id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price
        }
        for item in debit_note_data.items_to_return
    ]
    
    try:
        dn = dn_service.create_for_bill(
            bill, 
            items_to_return, 
            debit_note_data.debit_note_date,
            debit_note_data.reason
        )
        db.commit()
        return {
            'id': dn.id,
            'debit_note_number': dn.debit_note_number,
            'debit_note_date': dn.debit_note_date.isoformat(),
            'total_amount': float(dn.total_amount),
            'reason': dn.reason,
            'status': dn.status,
            'bill_number': bill.bill_number,
            'vendor_name': bill.vendor.name if bill.vendor else 'N/A'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/debit-notes/{debit_note_id}/apply", dependencies=[Depends(PermissionChecker(["debit_notes:edit"]))])
async def apply_debit_note(
    debit_note_id: int,
    apply_data: ApplyDebitNoteRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Apply debit note to reduce bill balance.
    
    For paid bills, you can optionally:
    - Add refund to vendor's pre-paid balance (refund_method='vendor_balance')
    - Receive cash/bank refund (refund_method='cash_refund', requires refund_account_id)
    """
    dn_service = DebitNoteService(db)
    
    try:
        # Get default values if no data provided
        refund_method = apply_data.refund_method if apply_data else 'none'
        refund_account_id = apply_data.refund_account_id if apply_data else None
        refund_date = apply_data.refund_date if apply_data else None
        
        dn = dn_service.apply_debit_note(
            debit_note_id, 
            current_user.business_id,
            refund_method=refund_method,
            refund_account_id=refund_account_id,
            refund_date=refund_date
        )
        db.commit()
        
        # Get the bill to return updated status
        purchase_service = PurchaseService(db)
        bill = purchase_service.get_by_id(dn.purchase_bill_id, current_user.business_id)
        
        return {
            "message": "Debit note applied successfully",
            "debit_note_id": dn.id,
            "debit_note_number": dn.debit_note_number,
            "applied_amount": float(dn.total_amount),
            "status": dn.status,
            "refund_amount": float(dn.refund_amount or 0),
            "refund_method": dn.refund_method,
            "bill_id": bill.id if bill else None,
            "bill_status": bill.status if bill else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
