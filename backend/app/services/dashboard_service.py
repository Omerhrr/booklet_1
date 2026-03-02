"""
Dashboard Service - Analytics and Reporting
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from decimal import Decimal
from datetime import date, timedelta
from app.models import (
    SalesInvoice, PurchaseBill, Expense, Customer, Vendor, Product,
    LedgerEntry, Account, OtherIncome, Employee, CreditNote, DebitNote,
    BankAccount, Payment
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_stats(self, business_id: int, branch_id: int) -> Dict:
        """Get main dashboard statistics"""
        
        # Get date range for this month
        today = date.today()
        month_start = today.replace(day=1)
        
        # Get date range for last month (for comparison)
        if today.month == 1:
            last_month_start = date(today.year - 1, 12, 1)
        else:
            last_month_start = date(today.year, today.month - 1, 1)
        last_month_end = month_start - timedelta(days=1)
        
        # Total Sales (this month) - net of credit notes
        sales_result = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.invoice_date >= month_start
        ).scalar() or Decimal("0")
        
        # Subtract credit notes
        credit_notes_result = self.db.query(func.sum(CreditNote.total_amount)).filter(
            CreditNote.business_id == business_id,
            CreditNote.branch_id == branch_id,
            CreditNote.credit_note_date >= month_start
        ).scalar() or Decimal("0")
        
        net_sales = sales_result - credit_notes_result
        
        # Last month sales for comparison
        last_month_sales = self.db.query(func.sum(SalesInvoice.total_amount)).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.invoice_date >= last_month_start,
            SalesInvoice.invoice_date <= last_month_end
        ).scalar() or Decimal("0")
        last_month_credit_notes = self.db.query(func.sum(CreditNote.total_amount)).filter(
            CreditNote.business_id == business_id,
            CreditNote.branch_id == branch_id,
            CreditNote.credit_note_date >= last_month_start,
            CreditNote.credit_note_date <= last_month_end
        ).scalar() or Decimal("0")
        last_month_net_sales = last_month_sales - last_month_credit_notes
        
        # Calculate sales growth percentage
        if last_month_net_sales > 0:
            sales_growth = ((net_sales - last_month_net_sales) / last_month_net_sales) * 100
        else:
            sales_growth = Decimal("100") if net_sales > 0 else Decimal("0")
        
        # Total Purchases (this month) - net of debit notes
        purchases_result = self.db.query(func.sum(PurchaseBill.total_amount)).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.bill_date >= month_start
        ).scalar() or Decimal("0")
        
        # Subtract debit notes
        debit_notes_result = self.db.query(func.sum(DebitNote.total_amount)).filter(
            DebitNote.business_id == business_id,
            DebitNote.branch_id == branch_id,
            DebitNote.debit_note_date >= month_start
        ).scalar() or Decimal("0")
        
        net_purchases = purchases_result - debit_notes_result
        
        # Last month purchases for comparison
        last_month_purchases = self.db.query(func.sum(PurchaseBill.total_amount)).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.bill_date >= last_month_start,
            PurchaseBill.bill_date <= last_month_end
        ).scalar() or Decimal("0")
        last_month_debit_notes = self.db.query(func.sum(DebitNote.total_amount)).filter(
            DebitNote.business_id == business_id,
            DebitNote.branch_id == branch_id,
            DebitNote.debit_note_date >= last_month_start,
            DebitNote.debit_note_date <= last_month_end
        ).scalar() or Decimal("0")
        last_month_net_purchases = last_month_purchases - last_month_debit_notes
        
        if last_month_net_purchases > 0:
            purchases_growth = ((net_purchases - last_month_net_purchases) / last_month_net_purchases) * 100
        else:
            purchases_growth = Decimal("100") if net_purchases > 0 else Decimal("0")
        
        # Total Expenses (this month)
        expenses_result = self.db.query(func.sum(Expense.amount)).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id,
            Expense.expense_date >= month_start
        ).scalar() or Decimal("0")
        
        # Last month expenses
        last_month_expenses = self.db.query(func.sum(Expense.amount)).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id,
            Expense.expense_date >= last_month_start,
            Expense.expense_date <= last_month_end
        ).scalar() or Decimal("0")
        
        if last_month_expenses > 0:
            expenses_growth = ((expenses_result - last_month_expenses) / last_month_expenses) * 100
        else:
            expenses_growth = Decimal("100") if expenses_result > 0 else Decimal("0")
        
        # Total Other Income (this month)
        other_income_result = self.db.query(func.sum(OtherIncome.amount)).filter(
            OtherIncome.business_id == business_id,
            OtherIncome.branch_id == branch_id,
            OtherIncome.income_date >= month_start
        ).scalar() or Decimal("0")
        
        # Total Receivables
        receivables_result = self.db.query(func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount)).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.status.in_(["Unpaid", "Partial", "Overdue", "pending", "Pending"])
        ).scalar() or Decimal("0")
        
        # Total Payables
        payables_result = self.db.query(func.sum(PurchaseBill.total_amount - PurchaseBill.paid_amount)).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.status.in_(["Unpaid", "Partial", "Overdue", "pending", "Pending"])
        ).scalar() or Decimal("0")
        
        # Cash Balance - Get all cash/bank accounts (Asset type accounts that are cash or bank)
        cash_balance = Decimal("0")
        
        # Method 1: Get bank accounts linked to COA
        bank_accounts = self.db.query(BankAccount).filter(
            BankAccount.business_id == business_id,
            BankAccount.branch_id == branch_id
        ).all()
        
        for ba in bank_accounts:
            if ba.chart_of_account_id:
                balance = self._get_account_balance(ba.chart_of_account_id, branch_id)
                cash_balance += balance
        
        # Method 2: Get cash accounts from COA (Asset accounts with cash in name but not linked to bank accounts)
        bank_coa_ids = [ba.chart_of_account_id for ba in bank_accounts if ba.chart_of_account_id]
        cash_accounts = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.type == "Asset",
            Account.is_active == True,
            ~Account.id.in_(bank_coa_ids)  # Exclude already counted bank accounts
        ).filter(
            (Account.name.ilike('%cash%') | Account.name.ilike('%petty%'))
        ).all()
        
        for account in cash_accounts:
            balance = self._get_account_balance(account.id, branch_id)
            cash_balance += balance
        
        # Gross Profit = Net Sales - Net Purchases (simplified, actual COGS would be better)
        gross_profit = net_sales - net_purchases
        gross_profit_margin = (gross_profit / net_sales * 100) if net_sales > 0 else Decimal("0")
        
        # Net Profit = Gross Profit - Expenses
        net_profit = gross_profit - expenses_result + other_income_result
        net_profit_margin = (net_profit / net_sales * 100) if net_sales > 0 else Decimal("0")
        
        # Counts
        total_customers = self.db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.branch_id == branch_id,
            Customer.is_active == True
        ).count()
        
        total_vendors = self.db.query(Vendor).filter(
            Vendor.business_id == business_id,
            Vendor.branch_id == branch_id,
            Vendor.is_active == True
        ).count()
        
        total_products = self.db.query(Product).filter(
            Product.business_id == business_id,
            Product.branch_id == branch_id,
            Product.is_active == True
        ).count()
        
        total_employees = self.db.query(Employee).filter(
            Employee.business_id == business_id,
            Employee.branch_id == branch_id,
            Employee.is_active == True
        ).count()
        
        # Low stock products
        low_stock = self.db.query(Product).filter(
            Product.business_id == business_id,
            Product.branch_id == branch_id,
            Product.is_active == True,
            Product.stock_quantity <= Product.reorder_level
        ).count()
        
        # Invoices count this month
        invoices_count = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.invoice_date >= month_start
        ).count()
        
        # Bills count this month
        bills_count = self.db.query(PurchaseBill).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.bill_date >= month_start
        ).count()
        
        # Overdue invoices count
        overdue_invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.status == "Overdue"
        ).count()
        
        return {
            "total_sales": net_sales,
            "total_purchases": net_purchases,
            "total_expenses": expenses_result,
            "total_other_income": other_income_result,
            "total_receivables": receivables_result,
            "total_payables": payables_result,
            "cash_balance": cash_balance,
            "gross_profit": gross_profit,
            "gross_profit_margin": gross_profit_margin,
            "net_profit": net_profit,
            "net_profit_margin": net_profit_margin,
            "total_customers": total_customers,
            "total_vendors": total_vendors,
            "total_products": total_products,
            "total_employees": total_employees,
            "low_stock_products": low_stock,
            "invoices_count": invoices_count,
            "bills_count": bills_count,
            "overdue_invoices": overdue_invoices,
            "sales_growth": sales_growth,
            "purchases_growth": purchases_growth,
            "expenses_growth": expenses_growth
        }
    
    def _get_account_balance(self, account_id: int, branch_id: int = None) -> Decimal:
        """Calculate account balance from ledger entries, optionally filtered by branch"""
        query = self.db.query(
            func.sum(LedgerEntry.debit - LedgerEntry.credit)
        ).filter(LedgerEntry.account_id == account_id)
        
        if branch_id:
            query = query.filter(LedgerEntry.branch_id == branch_id)
        
        result = query.scalar()
        return result or Decimal("0")
    
    def get_sales_chart(self, business_id: int, branch_id: int, days: int = 30) -> Dict:
        """Get sales data for chart"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        results = self.db.query(
            SalesInvoice.invoice_date,
            func.sum(SalesInvoice.total_amount)
        ).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.invoice_date >= start_date
        ).group_by(SalesInvoice.invoice_date).all()
        
        # Fill in missing dates
        date_dict = {r[0]: r[1] for r in results}
        labels = []
        values = []
        
        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.strftime("%Y-%m-%d"))
            values.append(date_dict.get(current_date, Decimal("0")))
            current_date += timedelta(days=1)
        
        return {"labels": labels, "values": values}
    
    def get_expense_chart(self, business_id: int, branch_id: int, days: int = 30) -> Dict:
        """Get expense data for chart"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        results = self.db.query(
            Expense.expense_date,
            func.sum(Expense.amount)
        ).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id,
            Expense.expense_date >= start_date
        ).group_by(Expense.expense_date).all()
        
        date_dict = {r[0]: r[1] for r in results}
        labels = []
        values = []
        
        current_date = start_date
        while current_date <= end_date:
            labels.append(current_date.strftime("%Y-%m-%d"))
            values.append(date_dict.get(current_date, Decimal("0")))
            current_date += timedelta(days=1)
        
        return {"labels": labels, "values": values}
    
    def get_receivables_aging(self, business_id: int, branch_id: int) -> Dict:
        """Get accounts receivable aging report"""
        today = date.today()
        
        invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.status.in_(["Unpaid", "Partial", "Overdue", "pending", "Pending"])
        ).all()
        
        aging = {
            "current": Decimal("0"),
            "days_30": Decimal("0"),
            "days_60": Decimal("0"),
            "days_90": Decimal("0"),
            "over_90": Decimal("0"),
            "total": Decimal("0")
        }
        
        for invoice in invoices:
            days_overdue = (today - invoice.due_date).days if invoice.due_date else 0
            # Outstanding = Total - Paid - Returned (credit notes)
            returned_amount = invoice.returned_amount or Decimal("0")
            outstanding = invoice.total_amount - invoice.paid_amount - returned_amount
            
            # Skip if no outstanding balance
            if outstanding <= 0:
                continue
            
            if days_overdue <= 0:
                aging["current"] += outstanding
            elif days_overdue <= 30:
                aging["days_30"] += outstanding
            elif days_overdue <= 60:
                aging["days_60"] += outstanding
            elif days_overdue <= 90:
                aging["days_90"] += outstanding
            else:
                aging["over_90"] += outstanding
            
            aging["total"] += outstanding
        
        return aging
    
    def get_payables_aging(self, business_id: int, branch_id: int) -> Dict:
        """Get accounts payable aging report"""
        today = date.today()
        
        bills = self.db.query(PurchaseBill).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.status.in_(["Unpaid", "Partial", "Overdue", "pending", "Pending"])
        ).all()
        
        aging = {
            "current": Decimal("0"),
            "days_30": Decimal("0"),
            "days_60": Decimal("0"),
            "days_90": Decimal("0"),
            "over_90": Decimal("0"),
            "total": Decimal("0")
        }
        
        for bill in bills:
            days_overdue = (today - bill.due_date).days if bill.due_date else 0
            # Outstanding = Total - Paid - Returned (debit notes)
            returned_amount = bill.returned_amount or Decimal("0")
            outstanding = bill.total_amount - bill.paid_amount - returned_amount
            
            # Skip if no outstanding balance
            if outstanding <= 0:
                continue
            
            if days_overdue <= 0:
                aging["current"] += outstanding
            elif days_overdue <= 30:
                aging["days_30"] += outstanding
            elif days_overdue <= 60:
                aging["days_60"] += outstanding
            elif days_overdue <= 90:
                aging["days_90"] += outstanding
            else:
                aging["over_90"] += outstanding
            
            aging["total"] += outstanding
        
        return aging
    
    def get_recent_transactions(self, business_id: int, branch_id: int, limit: int = 10) -> List[Dict]:
        """Get recent transactions across all types"""
        transactions = []
        
        # Recent Sales Invoices
        recent_invoices = self.db.query(SalesInvoice).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id
        ).order_by(SalesInvoice.created_at.desc()).limit(limit).all()
        
        for inv in recent_invoices:
            transactions.append({
                "type": "sales_invoice",
                "number": inv.invoice_number,
                "date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                "amount": float(inv.total_amount),
                "party": inv.customer.name if inv.customer else "Unknown",
                "status": inv.status,
                "url": f"/sales/{inv.id}"
            })
        
        # Recent Purchase Bills
        recent_bills = self.db.query(PurchaseBill).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id
        ).order_by(PurchaseBill.created_at.desc()).limit(limit).all()
        
        for bill in recent_bills:
            transactions.append({
                "type": "purchase_bill",
                "number": bill.bill_number,
                "date": bill.bill_date.isoformat() if bill.bill_date else None,
                "amount": float(bill.total_amount),
                "party": bill.vendor.name if bill.vendor else "Unknown",
                "status": bill.status,
                "url": f"/purchases/{bill.id}"
            })
        
        # Recent Expenses
        recent_expenses = self.db.query(Expense).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id
        ).order_by(Expense.created_at.desc()).limit(limit).all()
        
        for exp in recent_expenses:
            transactions.append({
                "type": "expense",
                "number": exp.expense_number,
                "date": exp.expense_date.isoformat() if exp.expense_date else None,
                "amount": float(exp.amount),
                "party": exp.vendor.name if exp.vendor else exp.category,
                "status": "paid",
                "url": f"/expenses/{exp.id}"
            })
        
        # Sort by date and return top items
        transactions.sort(key=lambda x: x['date'] or '', reverse=True)
        return transactions[:limit]
    
    def get_top_products(self, business_id: int, branch_id: int, limit: int = 5) -> List[Dict]:
        """Get top selling products by revenue"""
        from app.models import SalesInvoiceItem
        
        today = date.today()
        month_start = today.replace(day=1)
        
        # Query top products by total sales value
        results = self.db.query(
            Product.id,
            Product.name,
            Product.sku,
            func.sum(SalesInvoiceItem.quantity).label('total_qty'),
            func.sum(SalesInvoiceItem.quantity * SalesInvoiceItem.price).label('total_revenue')
        ).join(
            SalesInvoiceItem, SalesInvoiceItem.product_id == Product.id
        ).join(
            SalesInvoice, SalesInvoice.id == SalesInvoiceItem.sales_invoice_id
        ).filter(
            Product.business_id == business_id,
            Product.branch_id == branch_id,
            SalesInvoice.invoice_date >= month_start
        ).group_by(
            Product.id, Product.name, Product.sku
        ).order_by(
            func.sum(SalesInvoiceItem.quantity * SalesInvoiceItem.price).desc()
        ).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "sku": r.sku,
                "quantity": float(r.total_qty or 0),
                "revenue": float(r.total_revenue or 0)
            }
            for r in results
        ]
    
    def get_top_customers(self, business_id: int, branch_id: int, limit: int = 5) -> List[Dict]:
        """Get top customers by revenue"""
        today = date.today()
        month_start = today.replace(day=1)
        
        results = self.db.query(
            Customer.id,
            Customer.name,
            func.sum(SalesInvoice.total_amount).label('total_purchases'),
            func.count(SalesInvoice.id).label('invoice_count')
        ).join(
            SalesInvoice, SalesInvoice.customer_id == Customer.id
        ).filter(
            Customer.business_id == business_id,
            Customer.branch_id == branch_id,
            SalesInvoice.invoice_date >= month_start
        ).group_by(
            Customer.id, Customer.name
        ).order_by(
            func.sum(SalesInvoice.total_amount).desc()
        ).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "total_purchases": float(r.total_purchases or 0),
                "invoice_count": r.invoice_count
            }
            for r in results
        ]
    
    def get_expense_breakdown(self, business_id: int, branch_id: int) -> Dict:
        """Get expense breakdown by category"""
        today = date.today()
        month_start = today.replace(day=1)
        
        results = self.db.query(
            Expense.category,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id,
            Expense.expense_date >= month_start
        ).group_by(
            Expense.category
        ).order_by(
            func.sum(Expense.amount).desc()
        ).all()
        
        return {
            "labels": [r.category for r in results],
            "values": [float(r.total or 0) for r in results]
        }
    
    def get_full_dashboard(self, business_id: int, branch_id: int) -> Dict:
        """Get all dashboard data"""
        return {
            "stats": self.get_stats(business_id, branch_id),
            "sales_chart": self.get_sales_chart(business_id, branch_id),
            "expense_chart": self.get_expense_chart(business_id, branch_id),
            "receivables_aging": self.get_receivables_aging(business_id, branch_id),
            "payables_aging": self.get_payables_aging(business_id, branch_id),
            "recent_transactions": self.get_recent_transactions(business_id, branch_id),
            "top_products": self.get_top_products(business_id, branch_id),
            "top_customers": self.get_top_customers(business_id, branch_id),
            "expense_breakdown": self.get_expense_breakdown(business_id, branch_id)
        }
