"""
Dashboard Service - Analytics and Reporting
"""
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
from datetime import date, timedelta
from app.models import (
    SalesInvoice, PurchaseBill, Expense, Customer, Vendor, Product,
    LedgerEntry, Account
)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_stats(self, business_id: int, branch_id: int) -> Dict:
        """Get main dashboard statistics"""
        
        # Get date range for this month
        today = date.today()
        month_start = today.replace(day=1)
        
        # Total Sales (this month) - net of credit notes
        from app.models import CreditNote
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
        
        # Total Purchases (this month) - net of debit notes
        from app.models import DebitNote
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
        
        # Total Expenses (this month)
        expenses_result = self.db.query(func.sum(Expense.amount)).filter(
            Expense.business_id == business_id,
            Expense.branch_id == branch_id,
            Expense.expense_date >= month_start
        ).scalar() or Decimal("0")
        
        # Total Receivables
        receivables_result = self.db.query(func.sum(SalesInvoice.total_amount - SalesInvoice.paid_amount)).filter(
            SalesInvoice.business_id == business_id,
            SalesInvoice.branch_id == branch_id,
            SalesInvoice.status.in_(["Unpaid", "Partial", "Overdue"])
        ).scalar() or Decimal("0")
        
        # Total Payables
        payables_result = self.db.query(func.sum(PurchaseBill.total_amount - PurchaseBill.paid_amount)).filter(
            PurchaseBill.business_id == business_id,
            PurchaseBill.branch_id == branch_id,
            PurchaseBill.status.in_(["Unpaid", "Partial", "Overdue"])
        ).scalar() or Decimal("0")
        
        # Cash Balance - Get all cash/bank accounts (Asset type accounts that are cash or bank)
        # Look for accounts with type=Asset and name containing 'Cash' or 'Bank', or by category
        from app.models import BankAccount
        
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
        
        # Low stock products
        low_stock = self.db.query(Product).filter(
            Product.business_id == business_id,
            Product.branch_id == branch_id,
            Product.is_active == True,
            Product.stock_quantity <= Product.reorder_level
        ).count()
        
        return {
            "total_sales": net_sales,
            "total_purchases": net_purchases,
            "total_expenses": expenses_result,
            "total_receivables": receivables_result,
            "total_payables": payables_result,
            "cash_balance": cash_balance,
            "total_customers": total_customers,
            "total_vendors": total_vendors,
            "total_products": total_products,
            "low_stock_products": low_stock
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
    
    def get_full_dashboard(self, business_id: int, branch_id: int) -> Dict:
        """Get all dashboard data"""
        return {
            "stats": self.get_stats(business_id, branch_id),
            "sales_chart": self.get_sales_chart(business_id, branch_id),
            "expense_chart": self.get_expense_chart(business_id, branch_id),
            "receivables_aging": self.get_receivables_aging(business_id, branch_id),
            "payables_aging": self.get_payables_aging(business_id, branch_id)
        }
