"""
Reports API Routes - Sales, Purchases, Expenses, Inventory, VAT Reports
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import (
    SalesInvoice, SalesInvoiceItem, PurchaseBill, PurchaseBillItem,
    Expense, OtherIncome, Product, Customer, Vendor, LedgerEntry,
    Account, AccountType, Business
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/sales")
async def get_sales_report(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get sales report with summary and top customers"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    # Base query for invoices
    query = db.query(SalesInvoice).filter(
        SalesInvoice.business_id == business_id,
        SalesInvoice.branch_id == branch_id,
        SalesInvoice.invoice_date >= start_date,
        SalesInvoice.invoice_date <= end_date
    )
    
    invoices = query.all()
    
    # Calculate totals
    total_sales = sum(inv.total_amount or Decimal("0") for inv in invoices)
    total_invoices = len(invoices)
    outstanding = sum(
        (inv.total_amount or Decimal("0")) - (inv.paid_amount or Decimal("0"))
        for inv in invoices
    )
    collected = sum(inv.paid_amount or Decimal("0") for inv in invoices)
    
    # Top customers by sales
    top_customers_query = db.query(
        Customer.id,
        Customer.name,
        func.count(SalesInvoice.id).label('invoice_count'),
        func.sum(SalesInvoice.total_amount).label('total_sales')
    ).join(
        SalesInvoice, Customer.id == SalesInvoice.customer_id
    ).filter(
        SalesInvoice.business_id == business_id,
        SalesInvoice.branch_id == branch_id,
        SalesInvoice.invoice_date >= start_date,
        SalesInvoice.invoice_date <= end_date
    ).group_by(Customer.id).order_by(
        func.sum(SalesInvoice.total_amount).desc()
    ).limit(10).all()
    
    top_customers = []
    for cust in top_customers_query:
        top_customers.append({
            'id': cust.id,
            'name': cust.name,
            'total_sales': float(cust.total_sales or 0),
            'invoice_count': cust.invoice_count
        })
    
    # Sales by date for chart
    sales_by_date = db.query(
        SalesInvoice.invoice_date,
        func.sum(SalesInvoice.total_amount).label('daily_total')
    ).filter(
        SalesInvoice.business_id == business_id,
        SalesInvoice.branch_id == branch_id,
        SalesInvoice.invoice_date >= start_date,
        SalesInvoice.invoice_date <= end_date
    ).group_by(SalesInvoice.invoice_date).order_by(
        SalesInvoice.invoice_date
    ).all()
    
    daily_sales = []
    for sale in sales_by_date:
        daily_sales.append({
            'date': sale.invoice_date.isoformat(),
            'total': float(sale.daily_total or 0)
        })
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_sales': float(total_sales),
        'total_invoices': total_invoices,
        'outstanding': float(outstanding),
        'collected': float(collected),
        'top_customers': top_customers,
        'daily_sales': daily_sales,
        'invoices': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'customer_name': inv.customer.name if inv.customer else None,
            'total_amount': float(inv.total_amount or 0),
            'paid_amount': float(inv.paid_amount or 0),
            'status': inv.status
        } for inv in invoices]
    }


@router.get("/purchases")
async def get_purchases_report(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get purchases report with summary and top vendors"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    query = db.query(PurchaseBill).filter(
        PurchaseBill.business_id == business_id,
        PurchaseBill.branch_id == branch_id,
        PurchaseBill.bill_date >= start_date,
        PurchaseBill.bill_date <= end_date
    )
    
    bills = query.all()
    
    total_purchases = sum(bill.total_amount or Decimal("0") for bill in bills)
    total_bills = len(bills)
    outstanding = sum(
        (bill.total_amount or Decimal("0")) - (bill.paid_amount or Decimal("0"))
        for bill in bills
    )
    paid = sum(bill.paid_amount or Decimal("0") for bill in bills)
    
    # Top vendors
    top_vendors_query = db.query(
        Vendor.id,
        Vendor.name,
        func.count(PurchaseBill.id).label('bill_count'),
        func.sum(PurchaseBill.total_amount).label('total_purchases')
    ).join(
        PurchaseBill, Vendor.id == PurchaseBill.vendor_id
    ).filter(
        PurchaseBill.business_id == business_id,
        PurchaseBill.branch_id == branch_id,
        PurchaseBill.bill_date >= start_date,
        PurchaseBill.bill_date <= end_date
    ).group_by(Vendor.id).order_by(
        func.sum(PurchaseBill.total_amount).desc()
    ).limit(10).all()
    
    top_vendors = []
    for vendor in top_vendors_query:
        top_vendors.append({
            'id': vendor.id,
            'name': vendor.name,
            'total_purchases': float(vendor.total_purchases or 0),
            'bill_count': vendor.bill_count
        })
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_purchases': float(total_purchases),
        'total_bills': total_bills,
        'outstanding': float(outstanding),
        'paid': float(paid),
        'top_vendors': top_vendors,
        'bills': [{
            'id': bill.id,
            'bill_number': bill.bill_number,
            'bill_date': bill.bill_date.isoformat() if bill.bill_date else None,
            'vendor_name': bill.vendor.name if bill.vendor else None,
            'total_amount': float(bill.total_amount or 0),
            'paid_amount': float(bill.paid_amount or 0),
            'status': bill.status
        } for bill in bills]
    }


@router.get("/expenses")
async def get_expenses_report(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get expenses report by category"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    query = db.query(Expense).filter(
        Expense.business_id == business_id,
        Expense.branch_id == branch_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    )
    
    expenses = query.all()
    
    total_expenses = sum(exp.amount or Decimal("0") for exp in expenses)
    total_vat = sum(exp.vat_amount or Decimal("0") for exp in expenses)
    
    # By category
    by_category = db.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.business_id == business_id,
        Expense.branch_id == branch_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Expense.category).order_by(
        func.sum(Expense.amount).desc()
    ).all()
    
    categories = []
    for cat in by_category:
        categories.append({
            'category': cat.category,
            'total': float(cat.total or 0),
            'count': cat.count
        })
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_expenses': float(total_expenses),
        'total_vat': float(total_vat),
        'expense_count': len(expenses),
        'by_category': categories,
        'expenses': [{
            'id': exp.id,
            'expense_number': exp.expense_number,
            'expense_date': exp.expense_date.isoformat() if exp.expense_date else None,
            'category': exp.category,
            'description': exp.description,
            'amount': float(exp.amount or 0),
            'vendor_name': exp.vendor.name if exp.vendor else None
        } for exp in expenses]
    }


@router.get("/inventory")
async def get_inventory_report(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get inventory report with stock levels and valuation"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    products = db.query(Product).filter(
        Product.business_id == business_id,
        Product.branch_id == branch_id
    ).all()
    
    total_value = Decimal("0")
    low_stock = []
    out_of_stock = []
    
    product_list = []
    for product in products:
        quantity = product.stock_quantity or Decimal("0")
        value = quantity * (product.purchase_price or Decimal("0"))
        total_value += value
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'quantity': float(quantity),
            'unit': product.unit,
            'purchase_price': float(product.purchase_price or 0),
            'sales_price': float(product.sales_price or 0),
            'value': float(value),
            'reorder_level': float(product.reorder_level or 0),
            'category': product.category.name if product.category else None
        }
        product_list.append(product_data)
        
        if quantity <= 0:
            out_of_stock.append(product_data)
        elif product.reorder_level and quantity <= product.reorder_level:
            low_stock.append(product_data)
    
    return {
        'total_products': len(products),
        'total_value': float(total_value),
        'low_stock_count': len(low_stock),
        'out_of_stock_count': len(out_of_stock),
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'products': product_list
    }


@router.get("/vat")
async def get_vat_report(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get VAT report - VAT collected vs VAT paid"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    # VAT collected from sales
    sales_vat = db.query(
        func.sum(SalesInvoice.vat_amount)
    ).filter(
        SalesInvoice.business_id == business_id,
        SalesInvoice.branch_id == branch_id,
        SalesInvoice.invoice_date >= start_date,
        SalesInvoice.invoice_date <= end_date
    ).scalar() or Decimal("0")
    
    # VAT paid on purchases
    purchase_vat = db.query(
        func.sum(PurchaseBill.vat_amount)
    ).filter(
        PurchaseBill.business_id == business_id,
        PurchaseBill.branch_id == branch_id,
        PurchaseBill.bill_date >= start_date,
        PurchaseBill.bill_date <= end_date
    ).scalar() or Decimal("0")
    
    # VAT on expenses
    expense_vat = db.query(
        func.sum(Expense.vat_amount)
    ).filter(
        Expense.business_id == business_id,
        Expense.branch_id == branch_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or Decimal("0")
    
    total_vat_paid = purchase_vat + expense_vat
    net_vat = sales_vat - total_vat_paid
    
    # Detailed breakdown
    sales_invoices = db.query(SalesInvoice).filter(
        SalesInvoice.business_id == business_id,
        SalesInvoice.branch_id == branch_id,
        SalesInvoice.invoice_date >= start_date,
        SalesInvoice.invoice_date <= end_date,
        SalesInvoice.vat_amount > 0
    ).all()
    
    purchase_bills = db.query(PurchaseBill).filter(
        PurchaseBill.business_id == business_id,
        PurchaseBill.branch_id == branch_id,
        PurchaseBill.bill_date >= start_date,
        PurchaseBill.bill_date <= end_date,
        PurchaseBill.vat_amount > 0
    ).all()
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'vat_collected': float(sales_vat),
        'vat_paid_purchases': float(purchase_vat),
        'vat_paid_expenses': float(expense_vat),
        'total_vat_paid': float(total_vat_paid),
        'net_vat': float(net_vat),
        'vat_payable': float(net_vat) if net_vat > 0 else 0,
        'vat_receivable': float(abs(net_vat)) if net_vat < 0 else 0,
        'sales_with_vat': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'customer': inv.customer.name if inv.customer else None,
            'sub_total': float(inv.sub_total or 0),
            'vat_amount': float(inv.vat_amount or 0)
        } for inv in sales_invoices],
        'purchases_with_vat': [{
            'id': bill.id,
            'bill_number': bill.bill_number,
            'date': bill.bill_date.isoformat() if bill.bill_date else None,
            'vendor': bill.vendor.name if bill.vendor else None,
            'sub_total': float(bill.sub_total or 0),
            'vat_amount': float(bill.vat_amount or 0)
        } for bill in purchase_bills]
    }


@router.get("/trial-balance")
async def get_trial_balance_report(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get trial balance report"""
    from app.services.accounting_service import ReportService
    
    if not as_of_date:
        as_of_date = date.today()
    
    report_service = ReportService(db)
    data = report_service.get_trial_balance(
        current_user.business_id,
        current_user.selected_branch.id,
        as_of_date
    )
    
    result = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    
    for item in data:
        account = item.get('account')
        debit = item.get('debit', Decimal("0"))
        credit = item.get('credit', Decimal("0"))
        total_debit += debit
        total_credit += credit
        
        result.append({
            'account_id': account.id if account else None,
            'account_code': account.code if account else None,
            'account_name': account.name if account else None,
            'account_type': account.type if account and account.type else None,
            'debit': float(debit),
            'credit': float(credit),
            'balance': float(item.get('balance', 0))
        })
    
    return {
        'as_of_date': as_of_date.isoformat(),
        'accounts': result,
        'total_debit': float(total_debit),
        'total_credit': float(total_credit),
        'is_balanced': abs(total_debit - total_credit) < Decimal("0.01")
    }


@router.get("/other-income")
async def get_other_income_report(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get other income report"""
    branch_id = current_user.selected_branch.id
    business_id = current_user.business_id
    
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    incomes = db.query(OtherIncome).filter(
        OtherIncome.business_id == business_id,
        OtherIncome.branch_id == branch_id,
        OtherIncome.income_date >= start_date,
        OtherIncome.income_date <= end_date
    ).all()
    
    total_income = sum(inc.amount or Decimal("0") for inc in incomes)
    
    # By category
    by_category = db.query(
        OtherIncome.category,
        func.sum(OtherIncome.amount).label('total'),
        func.count(OtherIncome.id).label('count')
    ).filter(
        OtherIncome.business_id == business_id,
        OtherIncome.branch_id == branch_id,
        OtherIncome.income_date >= start_date,
        OtherIncome.income_date <= end_date
    ).group_by(OtherIncome.category).all()
    
    categories = []
    for cat in by_category:
        categories.append({
            'category': cat.category,
            'total': float(cat.total or 0),
            'count': cat.count
        })
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_income': float(total_income),
        'income_count': len(incomes),
        'by_category': categories,
        'incomes': [{
            'id': inc.id,
            'income_number': inc.income_number,
            'income_date': inc.income_date.isoformat() if inc.income_date else None,
            'category': inc.category,
            'description': inc.description,
            'amount': float(inc.amount or 0),
            'customer_name': inc.customer.name if inc.customer else None
        } for inc in incomes]
    }
