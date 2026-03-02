"""
Sales API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    SalesInvoiceCreate, SalesInvoiceResponse, SalesInvoiceWithItems,
    RecordPaymentRequest, CreditNoteCreate, ApplyCreditNoteRequest, WriteOffRequest
)
from app.services.sales_service import SalesService, CreditNoteService

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/invoices")
async def list_invoices(
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all sales invoices"""
    sales_service = SalesService(db)
    invoices = sales_service.get_by_branch(
        current_user.selected_branch.id,
        current_user.business_id,
        status
    )
    # Add customer_name to each invoice
    result = []
    for invoice in invoices:
        invoice_dict = SalesInvoiceResponse.model_validate(invoice).model_dump()
        invoice_dict['customer_name'] = invoice.customer.name if invoice.customer else 'N/A'
        result.append(invoice_dict)
    return result


@router.post("/invoices", response_model=SalesInvoiceWithItems, dependencies=[Depends(PermissionChecker(["sales:create"]))])
async def create_invoice(
    invoice_data: SalesInvoiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new sales invoice"""
    sales_service = SalesService(db)
    vat_rate = current_user.business.vat_rate if current_user.business.is_vat_registered else 0
    
    invoice = sales_service.create(
        invoice_data,
        current_user.business_id,
        current_user.selected_branch.id,
        vat_rate
    )
    db.commit()
    return invoice


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get sales invoice by ID"""
    sales_service = SalesService(db)
    invoice = sales_service.get_by_id(
        invoice_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Convert to dict with additional fields
    invoice_dict = SalesInvoiceWithItems.model_validate(invoice).model_dump()
    invoice_dict['customer_name'] = invoice.customer.name if invoice.customer else 'N/A'
    invoice_dict['customer_email'] = invoice.customer.email if invoice.customer else None
    
    # Add product_name to each item
    items = []
    for item in invoice.items:
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
    invoice_dict['items'] = items
    
    # Ensure returned_amount is included
    if 'returned_amount' not in invoice_dict or invoice_dict.get('returned_amount') is None:
        invoice_dict['returned_amount'] = 0.0
    
    return invoice_dict


@router.post("/invoices/{invoice_id}/payment", dependencies=[Depends(PermissionChecker(["sales:edit"]))])
async def record_payment(
    invoice_id: int,
    payment_data: RecordPaymentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record payment for invoice"""
    sales_service = SalesService(db)
    try:
        invoice = sales_service.record_payment(
            invoice_id,
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
        return {"message": "Payment recorded", "invoice": SalesInvoiceResponse.model_validate(invoice)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoices/{invoice_id}/write-off", dependencies=[Depends(PermissionChecker(["sales:delete"]))])
async def write_off_invoice(
    invoice_id: int,
    write_off_data: WriteOffRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Write off unpaid invoice as bad debt"""
    sales_service = SalesService(db)
    try:
        invoice = sales_service.write_off(
            invoice_id, 
            current_user.business_id, 
            write_off_data.write_off_date,
            reason=write_off_data.reason,
            user_id=current_user.id
        )
        db.commit()
        return {"message": "Invoice written off", "invoice": SalesInvoiceResponse.model_validate(invoice)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/next-number")
async def get_next_invoice_number(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get next invoice number"""
    sales_service = SalesService(db)
    return {"next_number": sales_service.get_next_number(current_user.business_id)}


# Credit Notes
@router.get("/credit-notes")
async def list_credit_notes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all credit notes"""
    cn_service = CreditNoteService(db)
    credit_notes = cn_service.get_by_branch(current_user.selected_branch.id, current_user.business_id)
    
    # Add customer_name to each credit note
    result = []
    for cn in credit_notes:
        cn_dict = {
            'id': cn.id,
            'credit_note_number': cn.credit_note_number,
            'credit_note_date': cn.credit_note_date.isoformat() if cn.credit_note_date else None,
            'total_amount': float(cn.total_amount),
            'reason': cn.reason,
            'status': cn.status or 'open',
            'sales_invoice_id': cn.sales_invoice_id,
            'customer_id': cn.customer_id,
            'customer_name': cn.customer.name if cn.customer else 'N/A',
            'created_at': cn.created_at.isoformat() if cn.created_at else None
        }
        result.append(cn_dict)
    return result


@router.get("/credit-notes/{credit_note_id}")
async def get_credit_note(
    credit_note_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get credit note by ID"""
    cn_service = CreditNoteService(db)
    cn = cn_service.get_by_id(
        credit_note_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    
    # Build detailed response
    items = []
    for item in cn.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'N/A',
            'quantity': float(item.quantity),
            'price': float(item.price),
            'total': float(item.quantity * item.price)
        })
    
    # Get invoice payment info for refund calculation
    invoice_payment_info = None
    if cn.sales_invoice:
        invoice = cn.sales_invoice
        refundable_amount = Decimal("0.00")
        if invoice.paid_amount and invoice.paid_amount > 0:
            # Calculate how much was paid for the returned items
            # Refundable = min(credit_note_amount, paid_amount - previous_returns)
            previous_returns = invoice.returned_amount or Decimal("0.00")
            if cn.status == 'open':
                # For open credit notes, show potential refund
                paid_before_this_return = invoice.paid_amount - previous_returns
                if paid_before_this_return > 0:
                    refundable_amount = min(cn.total_amount, paid_before_this_return)
        
        invoice_payment_info = {
            'invoice_number': invoice.invoice_number,
            'total_amount': float(invoice.total_amount),
            'paid_amount': float(invoice.paid_amount or 0),
            'returned_amount': float(invoice.returned_amount or 0),
            'status': invoice.status,
            'refundable_amount': float(refundable_amount)
        }
    
    return {
        'id': cn.id,
        'credit_note_number': cn.credit_note_number,
        'credit_note_date': cn.credit_note_date.isoformat() if cn.credit_note_date else None,
        'total_amount': float(cn.total_amount),
        'reason': cn.reason,
        'status': cn.status or 'open',
        'refund_amount': float(cn.refund_amount or 0),
        'refund_method': cn.refund_method,
        'refund_date': cn.refund_date.isoformat() if cn.refund_date else None,
        'sales_invoice_id': cn.sales_invoice_id,
        'invoice_number': cn.sales_invoice.invoice_number if cn.sales_invoice else None,
        'invoice_payment_info': invoice_payment_info,
        'customer_id': cn.customer_id,
        'customer_name': cn.customer.name if cn.customer else 'N/A',
        'customer_email': cn.customer.email if cn.customer else None,
        'customer_phone': cn.customer.phone if cn.customer else None,
        'customer_address': cn.customer.address if cn.customer else None,
        'items': items,
        'created_at': cn.created_at.isoformat() if cn.created_at else None
    }


@router.post("/credit-notes", dependencies=[Depends(PermissionChecker(["credit_notes:create"]))])
async def create_credit_note(
    credit_note_data: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create credit note for invoice return"""
    sales_service = SalesService(db)
    cn_service = CreditNoteService(db)
    
    invoice = sales_service.get_by_id(
        credit_note_data.invoice_id, 
        current_user.business_id,
        current_user.selected_branch.id
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Convert items to dict format for service
    items_to_return = [
        {
            'original_item_id': item.original_item_id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price
        }
        for item in credit_note_data.items_to_return
    ]
    
    cn = cn_service.create_for_invoice(invoice, items_to_return, credit_note_data.credit_note_date, credit_note_data.reason)
    db.commit()
    return {
        'id': cn.id,
        'credit_note_number': cn.credit_note_number,
        'credit_note_date': cn.credit_note_date.isoformat(),
        'total_amount': float(cn.total_amount),
        'reason': cn.reason,
        'status': cn.status or 'open',
        'customer_id': cn.customer_id,
        'customer_name': cn.customer.name if cn.customer else 'N/A'
    }


@router.post("/credit-notes/{credit_note_id}/apply", dependencies=[Depends(PermissionChecker(["credit_notes:edit"]))])
async def apply_credit_note(
    credit_note_id: int,
    apply_data: ApplyCreditNoteRequest = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Apply credit note to reduce invoice balance.
    
    For paid invoices, you can optionally:
    - Add refund to customer's pre-paid balance (refund_method='customer_balance')
    - Issue a cash/bank refund (refund_method='cash_refund', requires refund_account_id)
    """
    cn_service = CreditNoteService(db)
    
    try:
        # Get default values if no data provided
        refund_method = apply_data.refund_method if apply_data else 'none'
        refund_account_id = apply_data.refund_account_id if apply_data else None
        refund_date = apply_data.refund_date if apply_data else None
        
        cn = cn_service.apply_credit_note(
            credit_note_id, 
            current_user.business_id,
            refund_method=refund_method,
            refund_account_id=refund_account_id,
            refund_date=refund_date
        )
        db.commit()
        
        # Get the invoice to return updated status
        sales_service = SalesService(db)
        invoice = sales_service.get_by_id(cn.sales_invoice_id, current_user.business_id)
        
        return {
            "message": "Credit note applied successfully",
            "credit_note_id": cn.id,
            "credit_note_number": cn.credit_note_number,
            "applied_amount": float(cn.total_amount),
            "status": cn.status,
            "refund_amount": float(cn.refund_amount or 0),
            "refund_method": cn.refund_method,
            "invoice_id": invoice.id if invoice else None,
            "invoice_status": invoice.status if invoice else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== BAD DEBTS ====================

@router.get("/bad-debts")
async def list_bad_debts(
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all bad debts for reporting"""
    from app.models import BadDebt
    from sqlalchemy.orm import joinedload
    
    query = db.query(BadDebt).options(
        joinedload(BadDebt.customer),
        joinedload(BadDebt.sales_invoice)
    ).filter(
        BadDebt.business_id == current_user.business_id,
        BadDebt.branch_id == current_user.selected_branch.id
    )
    
    if status:
        query = query.filter(BadDebt.status == status)
    
    bad_debts = query.order_by(BadDebt.write_off_date.desc()).all()
    
    result = []
    for bd in bad_debts:
        result.append({
            'id': bd.id,
            'bad_debt_number': bd.bad_debt_number,
            'write_off_date': bd.write_off_date.isoformat() if bd.write_off_date else None,
            'amount': float(bd.amount),
            'recovered_amount': float(bd.recovered_amount or 0),
            'remaining_amount': float(bd.remaining_amount),
            'reason': bd.reason,
            'status': bd.status,
            'sales_invoice_id': bd.sales_invoice_id,
            'invoice_number': bd.sales_invoice.invoice_number if bd.sales_invoice else None,
            'customer_id': bd.customer_id,
            'customer_name': bd.customer.name if bd.customer else 'N/A',
            'created_at': bd.created_at.isoformat() if bd.created_at else None
        })
    return result


@router.get("/bad-debts/{bad_debt_id}")
async def get_bad_debt(
    bad_debt_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get bad debt details"""
    from app.models import BadDebt
    from sqlalchemy.orm import joinedload
    
    bd = db.query(BadDebt).options(
        joinedload(BadDebt.customer),
        joinedload(BadDebt.sales_invoice),
        joinedload(BadDebt.ledger_entries)
    ).filter(
        BadDebt.id == bad_debt_id,
        BadDebt.business_id == current_user.business_id
    ).first()
    
    if not bd:
        raise HTTPException(status_code=404, detail="Bad debt record not found")
    
    return {
        'id': bd.id,
        'bad_debt_number': bd.bad_debt_number,
        'write_off_date': bd.write_off_date.isoformat() if bd.write_off_date else None,
        'amount': float(bd.amount),
        'recovered_amount': float(bd.recovered_amount or 0),
        'remaining_amount': float(bd.remaining_amount),
        'reason': bd.reason,
        'status': bd.status,
        'recovery_date': bd.recovery_date.isoformat() if bd.recovery_date else None,
        'sales_invoice_id': bd.sales_invoice_id,
        'invoice_number': bd.sales_invoice.invoice_number if bd.sales_invoice else None,
        'customer_id': bd.customer_id,
        'customer_name': bd.customer.name if bd.customer else 'N/A',
        'customer_email': bd.customer.email if bd.customer else None,
        'customer_phone': bd.customer.phone if bd.customer else None,
        'created_at': bd.created_at.isoformat() if bd.created_at else None,
        'created_by_user': bd.created_by_user.full_name if bd.created_by_user else None
    }


@router.get("/bad-debts/summary")
async def get_bad_debt_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get bad debt summary statistics"""
    from app.models import BadDebt
    from sqlalchemy import func
    
    # Total bad debts
    total_bad_debts = db.query(
        func.sum(BadDebt.amount)
    ).filter(
        BadDebt.business_id == current_user.business_id,
        BadDebt.branch_id == current_user.selected_branch.id
    ).scalar() or 0
    
    # Total recovered
    total_recovered = db.query(
        func.sum(BadDebt.recovered_amount)
    ).filter(
        BadDebt.business_id == current_user.business_id,
        BadDebt.branch_id == current_user.selected_branch.id
    ).scalar() or 0
    
    # Count by status
    status_counts = db.query(
        BadDebt.status,
        func.count(BadDebt.id)
    ).filter(
        BadDebt.business_id == current_user.business_id,
        BadDebt.branch_id == current_user.selected_branch.id
    ).group_by(BadDebt.status).all()
    
    status_breakdown = {status: count for status, count in status_counts}
    
    return {
        'total_bad_debts': float(total_bad_debts),
        'total_recovered': float(total_recovered),
        'total_outstanding': float(total_bad_debts - total_recovered),
        'status_breakdown': status_breakdown,
        'count': sum(status_breakdown.values())
    }
