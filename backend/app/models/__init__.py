"""
SQLAlchemy Models for ERP System
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Numeric,
    ForeignKey, Enum, Table, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import enum

from app.core.database import Base


# ==================== ENUMS ====================

class AccountType(enum.Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PayFrequency(enum.Enum):
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    BI_WEEKLY = "Bi-Weekly"


class PlanType(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# ==================== ASSOCIATION TABLES ====================

class RolePermission(Base):
    """Association table for Role-Permission many-to-many"""
    __tablename__ = 'role_permissions'
    
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role = relationship("Role", back_populates="permission_links")
    permission = relationship("Permission", back_populates="role_links")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )


class UserBranchRole(Base):
    """Association table for User-Branch-Role many-to-many"""
    __tablename__ = 'user_branch_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    branch = relationship("Branch", back_populates="user_assignments")
    role = relationship("Role", back_populates="user_assignments")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'branch_id', 'role_id', name='uq_user_branch_role'),
    )


# ==================== CORE MODELS ====================

class Business(Base):
    """Business/Company entity"""
    __tablename__ = 'businesses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), default=PlanType.FREE.value)
    is_vat_registered = Column(Boolean, default=False)
    vat_rate = Column(Numeric(5, 2), default=Decimal("0.00"))
    logo_url = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    tax_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="business", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="business", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="business", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="business", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="business", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="business", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    sales_invoices = relationship("SalesInvoice", back_populates="business", cascade="all, delete-orphan")
    purchase_bills = relationship("PurchaseBill", back_populates="business", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="business", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="business", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="business", cascade="all, delete-orphan")
    journal_vouchers = relationship("JournalVoucher", back_populates="business", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="business", cascade="all, delete-orphan")
    fixed_assets = relationship("FixedAsset", back_populates="business", cascade="all, delete-orphan")


class User(Base):
    """User account"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="users")
    roles = relationship("UserBranchRole", back_populates="user", cascade="all, delete-orphan")
    stock_adjustments = relationship("StockAdjustment", back_populates="user")
    created_invoices = relationship("SalesInvoice", back_populates="created_by_user")
    created_bills = relationship("PurchaseBill", back_populates="created_by_user")
    journal_vouchers = relationship("JournalVoucher", back_populates="created_by_user")
    
    @property
    def accessible_branches(self):
        return [assignment.branch for assignment in self.roles]
    
    @property
    def selected_branch(self):
        """Return the user's selected branch, or default/first accessible branch.
        
        Priority:
        1. _selected_branch set by get_current_active_user (admin-selected via cookie)
        2. Default branch from accessible branches
        3. First accessible branch
        """
        # Check if a branch was explicitly selected (for admin branch switching)
        if hasattr(self, '_selected_branch') and self._selected_branch is not None:
            return self._selected_branch
        
        branches = self.accessible_branches
        if not branches:
            return None
        # Return default branch if exists, otherwise first accessible
        for branch in branches:
            if branch.is_default:
                return branch
        return branches[0]


class Branch(Base):
    """Business branch/location"""
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    currency = Column(String(10), default="USD")
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="branches")
    user_assignments = relationship("UserBranchRole", back_populates="branch", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="branch")
    vendors = relationship("Vendor", back_populates="branch")
    categories = relationship("Category", back_populates="branch")
    products = relationship("Product", back_populates="branch")
    sales_invoices = relationship("SalesInvoice", back_populates="branch")
    purchase_bills = relationship("PurchaseBill", back_populates="branch")
    expenses = relationship("Expense", back_populates="branch")
    employees = relationship("Employee", back_populates="branch")
    bank_accounts = relationship("BankAccount", back_populates="branch")
    journal_vouchers = relationship("JournalVoucher", back_populates="branch")
    
    __table_args__ = (
        Index('ix_branches_business_id', 'business_id'),
    )


class Permission(Base):
    """System permission"""
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role_links = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class Role(Base):
    """User role"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="roles")
    permission_links = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_assignments = relationship("UserBranchRole", back_populates="role", cascade="all, delete-orphan")
    
    @property
    def permissions(self):
        return [link.permission for link in self.permission_links]
    
    @property
    def permission_ids(self):
        return [link.permission_id for link in self.permission_links]


# ==================== ACCOUNTING MODELS ====================

class Account(Base):
    """Chart of Accounts"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=True)
    type = Column(String(50), nullable=False)  # Store as string to avoid enum mapping issues
    description = Column(Text, nullable=True)
    is_system_account = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="accounts")
    parent = relationship("Account", remote_side=[id], backref="children")
    bank_accounts = relationship("BankAccount", back_populates="chart_of_account")
    ledger_entries = relationship("LedgerEntry", back_populates="account")
    budget_items = relationship("BudgetItem", back_populates="account")
    
    @property
    def account_type(self):
        """Return the AccountType enum for this account"""
        # Handle both "ASSET" and "Asset" formats
        type_map = {
            'asset': AccountType.ASSET,
            'liability': AccountType.LIABILITY,
            'equity': AccountType.EQUITY,
            'revenue': AccountType.REVENUE,
            'expense': AccountType.EXPENSE,
        }
        return type_map.get(self.type.lower(), None)
    
    __table_args__ = (
        Index('ix_accounts_business_id', 'business_id'),
        Index('ix_accounts_code', 'code'),
    )


class JournalVoucher(Base):
    """Journal voucher for manual journal entries"""
    __tablename__ = 'journal_vouchers'
    
    id = Column(Integer, primary_key=True)
    voucher_number = Column(String(50), nullable=False)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    is_posted = Column(Boolean, default=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="journal_vouchers")
    business = relationship("Business", back_populates="journal_vouchers")
    created_by_user = relationship("User", back_populates="journal_vouchers")
    ledger_entries = relationship("LedgerEntry", back_populates="journal_voucher", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('voucher_number', 'business_id', name='uq_journal_voucher_number'),
    )


class LedgerEntry(Base):
    """General ledger entry"""
    __tablename__ = 'ledger_entries'
    
    id = Column(Integer, primary_key=True)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    credit = Column(Numeric(15, 2), default=Decimal("0.00"))
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    journal_voucher_id = Column(Integer, ForeignKey('journal_vouchers.id', ondelete='CASCADE'), nullable=True)
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='SET NULL'), nullable=True)
    purchase_bill_id = Column(Integer, ForeignKey('purchase_bills.id', ondelete='SET NULL'), nullable=True)
    credit_note_id = Column(Integer, ForeignKey('credit_notes.id', ondelete='SET NULL'), nullable=True)
    debit_note_id = Column(Integer, ForeignKey('debit_notes.id', ondelete='SET NULL'), nullable=True)
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete='SET NULL'), nullable=True)
    other_income_id = Column(Integer, ForeignKey('other_incomes.id', ondelete='SET NULL'), nullable=True)
    closing_entry_id = Column(Integer, ForeignKey('closing_entries.id', ondelete='SET NULL'), nullable=True)
    bad_debt_id = Column(Integer, ForeignKey('bad_debts.id', ondelete='SET NULL'), nullable=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="ledger_entries")
    journal_voucher = relationship("JournalVoucher", back_populates="ledger_entries")
    sales_invoice = relationship("SalesInvoice", back_populates="ledger_entries")
    purchase_bill = relationship("PurchaseBill", back_populates="ledger_entries")
    credit_note = relationship("CreditNote", back_populates="ledger_entries")
    debit_note = relationship("DebitNote", back_populates="ledger_entries")
    expense = relationship("Expense", back_populates="ledger_entries")
    other_income = relationship("OtherIncome", back_populates="ledger_entries")
    closing_entry = relationship("ClosingEntry", back_populates="ledger_entries")
    bad_debt = relationship("BadDebt", back_populates="ledger_entries")
    bank_account = relationship("BankAccount")
    customer = relationship("Customer", back_populates="ledger_entries")
    vendor = relationship("Vendor", back_populates="ledger_entries")
    branch = relationship("Branch")

    __table_args__ = (
        Index('ix_ledger_entries_account_id', 'account_id'),
        Index('ix_ledger_entries_transaction_date', 'transaction_date'),
        Index('ix_ledger_entries_bank_account_id', 'bank_account_id'),
    )


# ==================== CRM MODELS ====================

class Customer(Base):
    """Customer"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    credit_limit = Column(Numeric(15, 2), default=Decimal("0.00"))
    account_balance = Column(Numeric(15, 2), default=Decimal("0.00"))  # Pre-paid/advance balance
    is_active = Column(Boolean, default=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="customers")
    business = relationship("Business", back_populates="customers")
    sales_invoices = relationship("SalesInvoice", back_populates="customer")
    ledger_entries = relationship("LedgerEntry", back_populates="customer")
    
    __table_args__ = (
        Index('ix_customers_business_id', 'business_id'),
    )


class Vendor(Base):
    """Vendor/Supplier"""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    account_balance = Column(Numeric(15, 2), default=Decimal("0.00"))  # Pre-paid/advance balance
    is_active = Column(Boolean, default=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="vendors")
    business = relationship("Business", back_populates="vendors")
    purchase_bills = relationship("PurchaseBill", back_populates="vendor")
    ledger_entries = relationship("LedgerEntry", back_populates="vendor")
    
    __table_args__ = (
        Index('ix_vendors_business_id', 'business_id'),
    )


# ==================== INVENTORY MODELS ====================

class Category(Base):
    """Product category"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="categories")
    business = relationship("Business", back_populates="categories")
    products = relationship("Product", back_populates="category")
    
    __table_args__ = (
        Index('ix_categories_business_id', 'business_id'),
    )


class Product(Base):
    """Product/Item"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    unit = Column(String(20), default="pcs")
    purchase_price = Column(Numeric(15, 2), default=Decimal("0.00"))
    sales_price = Column(Numeric(15, 2), default=Decimal("0.00"))
    opening_stock = Column(Numeric(15, 2), default=Decimal("0.00"))
    stock_quantity = Column(Numeric(15, 2), default=Decimal("0.00"))
    reorder_level = Column(Numeric(15, 2), default=Decimal("0.00"))
    is_active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    branch = relationship("Branch", back_populates="products")
    business = relationship("Business", back_populates="products")
    stock_adjustments = relationship("StockAdjustment", back_populates="product")
    sales_invoice_items = relationship("SalesInvoiceItem", back_populates="product")
    purchase_bill_items = relationship("PurchaseBillItem", back_populates="product")
    
    __table_args__ = (
        Index('ix_products_business_id', 'business_id'),
        Index('ix_products_sku', 'sku'),
    )


class StockAdjustment(Base):
    """Stock adjustment record"""
    __tablename__ = 'stock_adjustments'
    
    id = Column(Integer, primary_key=True)
    quantity_change = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="stock_adjustments")
    user = relationship("User", back_populates="stock_adjustments")


# ==================== SALES MODELS ====================

class SalesInvoice(Base):
    """Sales Invoice"""
    __tablename__ = 'sales_invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    sub_total = Column(Numeric(15, 2), default=Decimal("0.00"))
    vat_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    returned_amount = Column(Numeric(15, 2), default=Decimal("0.00"))  # Amount returned via credit notes
    status = Column(String(20), default=InvoiceStatus.PENDING.value)
    notes = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales_invoices")
    branch = relationship("Branch", back_populates="sales_invoices")
    business = relationship("Business", back_populates="sales_invoices")
    created_by_user = relationship("User", back_populates="created_invoices")
    items = relationship("SalesInvoiceItem", back_populates="sales_invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sales_invoice", cascade="all, delete-orphan")
    credit_notes = relationship("CreditNote", back_populates="sales_invoice", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="sales_invoice")
    
    __table_args__ = (
        UniqueConstraint('invoice_number', 'business_id', name='uq_sales_invoice_number'),
        Index('ix_sales_invoices_business_id', 'business_id'),
    )


class SalesInvoiceItem(Base):
    """Sales Invoice Line Item"""
    __tablename__ = 'sales_invoice_items'
    
    id = Column(Integer, primary_key=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    returned_quantity = Column(Numeric(15, 2), default=Decimal("0.00"))
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="sales_invoice_items")
    sales_invoice = relationship("SalesInvoice", back_populates="items")
    
    @property
    def total(self):
        return self.quantity * self.price


class Payment(Base):
    """Payment received"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    payment_number = Column(String(50), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(String(100), nullable=True)
    payment_method = Column(String(50), default="cash")
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_invoice = relationship("SalesInvoice", back_populates="payments")
    account = relationship("Account")


class CreditNote(Base):
    """Credit Note for sales returns"""
    __tablename__ = 'credit_notes'
    
    id = Column(Integer, primary_key=True)
    credit_note_number = Column(String(50), nullable=False)
    credit_note_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    reason = Column(Text, nullable=True)
    status = Column(String(20), default='open')  # open, applied, closed
    # Refund tracking for paid invoices
    refund_amount = Column(Numeric(15, 2), default=Decimal("0.00"))  # Amount refunded to customer
    refund_method = Column(String(20), nullable=True)  # 'customer_balance', 'cash'
    refund_date = Column(Date, nullable=True)
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_invoice = relationship("SalesInvoice", back_populates="credit_notes")
    customer = relationship("Customer")
    branch = relationship("Branch")
    business = relationship("Business")
    items = relationship("CreditNoteItem", back_populates="credit_note", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="credit_note")
    
    __table_args__ = (
        UniqueConstraint('credit_note_number', 'business_id', name='uq_credit_note_number'),
    )


class CreditNoteItem(Base):
    """Credit Note Line Item"""
    __tablename__ = 'credit_note_items'
    
    id = Column(Integer, primary_key=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    credit_note_id = Column(Integer, ForeignKey('credit_notes.id', ondelete='CASCADE'), nullable=False)
    original_item_id = Column(Integer, ForeignKey('sales_invoice_items.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    credit_note = relationship("CreditNote", back_populates="items")
    original_item = relationship("SalesInvoiceItem")
    
    @property
    def total(self):
        return self.quantity * self.price


# ==================== PURCHASES MODELS ====================

class PurchaseBill(Base):
    """Purchase Bill"""
    __tablename__ = 'purchase_bills'
    
    id = Column(Integer, primary_key=True)
    bill_number = Column(String(50), nullable=False)
    vendor_bill_number = Column(String(100), nullable=True)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    sub_total = Column(Numeric(15, 2), default=Decimal("0.00"))
    vat_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    returned_amount = Column(Numeric(15, 2), default=Decimal("0.00"))  # Amount returned via debit notes
    status = Column(String(20), default=InvoiceStatus.PENDING.value)
    notes = Column(Text, nullable=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id', ondelete='CASCADE'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_bills")
    branch = relationship("Branch", back_populates="purchase_bills")
    business = relationship("Business", back_populates="purchase_bills")
    created_by_user = relationship("User", back_populates="created_bills")
    items = relationship("PurchaseBillItem", back_populates="purchase_bill", cascade="all, delete-orphan")
    debit_notes = relationship("DebitNote", back_populates="purchase_bill", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="purchase_bill")
    
    __table_args__ = (
        UniqueConstraint('bill_number', 'business_id', name='uq_purchase_bill_number'),
        Index('ix_purchase_bills_business_id', 'business_id'),
    )


class PurchaseBillItem(Base):
    """Purchase Bill Line Item"""
    __tablename__ = 'purchase_bill_items'
    
    id = Column(Integer, primary_key=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    returned_quantity = Column(Numeric(15, 2), default=Decimal("0.00"))
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    purchase_bill_id = Column(Integer, ForeignKey('purchase_bills.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="purchase_bill_items")
    purchase_bill = relationship("PurchaseBill", back_populates="items")
    
    @property
    def total(self):
        return self.quantity * self.price


class DebitNote(Base):
    """Debit Note for purchase returns"""
    __tablename__ = 'debit_notes'
    
    id = Column(Integer, primary_key=True)
    debit_note_number = Column(String(50), nullable=False)
    debit_note_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    reason = Column(Text, nullable=True)
    status = Column(String(20), default='open')  # open, applied, closed
    # Refund tracking for paid bills
    refund_amount = Column(Numeric(15, 2), default=Decimal("0.00"))  # Amount refunded from vendor
    refund_method = Column(String(20), nullable=True)  # 'vendor_balance', 'cash'
    refund_date = Column(Date, nullable=True)
    purchase_bill_id = Column(Integer, ForeignKey('purchase_bills.id', ondelete='CASCADE'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    purchase_bill = relationship("PurchaseBill", back_populates="debit_notes")
    vendor = relationship("Vendor")
    branch = relationship("Branch")
    business = relationship("Business")
    items = relationship("DebitNoteItem", back_populates="debit_note", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="debit_note")
    
    __table_args__ = (
        UniqueConstraint('debit_note_number', 'business_id', name='uq_debit_note_number'),
    )


class DebitNoteItem(Base):
    """Debit Note Line Item"""
    __tablename__ = 'debit_note_items'
    
    id = Column(Integer, primary_key=True)
    quantity = Column(Numeric(15, 2), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    debit_note_id = Column(Integer, ForeignKey('debit_notes.id', ondelete='CASCADE'), nullable=False)
    original_item_id = Column(Integer, ForeignKey('purchase_bill_items.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    debit_note = relationship("DebitNote", back_populates="items")
    original_item = relationship("PurchaseBillItem")
    
    @property
    def total(self):
        return self.quantity * self.price


# ==================== EXPENSES ====================

class Expense(Base):
    """Expense record"""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    expense_number = Column(String(50), nullable=False)
    expense_date = Column(Date, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sub_total = Column(Numeric(15, 2), default=Decimal("0.00"))
    vat_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    vendor_id = Column(Integer, ForeignKey('vendors.id', ondelete='SET NULL'), nullable=True)
    paid_from_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    expense_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="expenses")
    business = relationship("Business", back_populates="expenses")
    vendor = relationship("Vendor")
    paid_from_account = relationship("Account", foreign_keys=[paid_from_account_id])
    expense_account = relationship("Account", foreign_keys=[expense_account_id])
    ledger_entries = relationship("LedgerEntry", back_populates="expense")
    
    __table_args__ = (
        UniqueConstraint('expense_number', 'business_id', name='uq_expense_number'),
    )


# ==================== OTHER INCOME ====================

class OtherIncome(Base):
    """Other Income record (non-sales income like interest, rent, dividends)"""
    __tablename__ = 'other_incomes'
    
    id = Column(Integer, primary_key=True)
    income_number = Column(String(50), nullable=False)
    income_date = Column(Date, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sub_total = Column(Numeric(15, 2), default=Decimal("0.00"))
    vat_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    received_in_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    income_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch")
    business = relationship("Business")
    customer = relationship("Customer")
    received_in_account = relationship("Account", foreign_keys=[received_in_account_id])
    income_account = relationship("Account", foreign_keys=[income_account_id])
    ledger_entries = relationship("LedgerEntry", back_populates="other_income")
    
    __table_args__ = (
        UniqueConstraint('income_number', 'business_id', name='uq_income_number'),
    )


# ==================== HR MODELS ====================

class Employee(Base):
    """Employee"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="employees")
    business = relationship("Business", back_populates="employees")
    payroll_config = relationship("PayrollConfig", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    payslips = relationship("Payslip", back_populates="employee", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_employees_business_id', 'business_id'),
    )


class PayrollConfig(Base):
    """Employee payroll configuration"""
    __tablename__ = 'payroll_configs'
    
    id = Column(Integer, primary_key=True)
    gross_salary = Column(Numeric(15, 2), default=Decimal("0.00"))
    pay_frequency = Column(String(20), default="Monthly")
    paye_rate = Column(Numeric(5, 2), default=Decimal("0.00"))
    pension_employee_rate = Column(Numeric(5, 2), default=Decimal("0.00"))
    pension_employer_rate = Column(Numeric(5, 2), default=Decimal("0.00"))
    other_deductions = Column(Numeric(15, 2), default=Decimal("0.00"))
    other_allowances = Column(Numeric(15, 2), default=Decimal("0.00"))
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="payroll_config")


class Payslip(Base):
    """Employee payslip"""
    __tablename__ = 'payslips'
    
    id = Column(Integer, primary_key=True)
    payslip_number = Column(String(50), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    basic_salary = Column(Numeric(15, 2), default=Decimal("0.00"))
    allowances = Column(Numeric(15, 2), default=Decimal("0.00"))
    gross_salary = Column(Numeric(15, 2), default=Decimal("0.00"))
    paye_deduction = Column(Numeric(15, 2), default=Decimal("0.00"))
    pension_employee = Column(Numeric(15, 2), default=Decimal("0.00"))
    pension_employer = Column(Numeric(15, 2), default=Decimal("0.00"))
    other_deductions = Column(Numeric(15, 2), default=Decimal("0.00"))
    total_deductions = Column(Numeric(15, 2), default=Decimal("0.00"))
    net_salary = Column(Numeric(15, 2), default=Decimal("0.00"))
    status = Column(String(20), default='pending')  # pending, paid, cancelled
    paid_date = Column(Date, nullable=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="payslips")
    business = relationship("Business")
    
    # Property aliases for template compatibility
    @property
    def paye(self):
        return self.paye_deduction
    
    @property
    def pension_deduction(self):
        return self.pension_employee
    
    @property
    def employee_name(self):
        return self.employee.full_name if self.employee else 'N/A'
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    __table_args__ = (
        UniqueConstraint('payslip_number', 'business_id', name='uq_payslip_number'),
    )


# ==================== BANKING MODELS ====================

class BankAccount(Base):
    """Bank Account"""
    __tablename__ = 'bank_accounts'
    
    id = Column(Integer, primary_key=True)
    account_name = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=True)
    account_number = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD")
    opening_balance = Column(Numeric(15, 2), default=Decimal("0.00"))
    current_balance = Column(Numeric(15, 2), default=Decimal("0.00"))
    last_reconciliation_date = Column(Date, nullable=True)
    last_reconciliation_balance = Column(Numeric(15, 2), nullable=True)
    chart_of_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chart_of_account = relationship("Account", back_populates="bank_accounts")
    branch = relationship("Branch", back_populates="bank_accounts")
    business = relationship("Business", back_populates="bank_accounts")
    
    __table_args__ = (
        Index('ix_bank_accounts_business_id', 'business_id'),
    )


class FundTransfer(Base):
    """Fund transfer between payment accounts (bank accounts or cash accounts)"""
    __tablename__ = 'fund_transfers'
    
    id = Column(Integer, primary_key=True)
    transfer_number = Column(String(50), nullable=False)
    transfer_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    # Source account - can be bank account or COA account (for cash)
    from_account_id = Column(Integer, nullable=False)  # Bank account ID or COA account ID
    from_account_type = Column(String(20), default='bank')  # 'bank' or 'cash'
    from_account_name = Column(String(255), nullable=True)  # Store name for display
    # Destination account - can be bank account or COA account (for cash)
    to_account_id = Column(Integer, nullable=False)  # Bank account ID or COA account ID
    to_account_type = Column(String(20), default='bank')  # 'bank' or 'cash'
    to_account_name = Column(String(255), nullable=True)  # Store name for display
    # COA account IDs for ledger entries
    from_coa_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    to_coa_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_coa_account = relationship("Account", foreign_keys=[from_coa_id])
    to_coa_account = relationship("Account", foreign_keys=[to_coa_id])
    branch = relationship("Branch")
    business = relationship("Business")
    
    __table_args__ = (
        UniqueConstraint('transfer_number', 'business_id', name='uq_fund_transfer_number'),
    )


# ==================== BUDGETING ====================

class Budget(Base):
    """Budget"""
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="budgets")
    items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('name', 'fiscal_year', 'business_id', name='uq_budget_name_year'),
    )


class BudgetItem(Base):
    """Budget line item"""
    __tablename__ = 'budget_items'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    month = Column(Integer, nullable=True)  # 1-12 for monthly, null for annual
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    budget_id = Column(Integer, ForeignKey('budgets.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="budget_items")
    budget = relationship("Budget", back_populates="items")


# ==================== FIXED ASSETS ====================

class AssetStatus(enum.Enum):
    ACTIVE = "active"
    DISPOSED = "disposed"
    WRITTEN_OFF = "written_off"
    FULLY_DEPRECIATED = "fully_depreciated"


class FixedAsset(Base):
    """Fixed Asset"""
    __tablename__ = 'fixed_assets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    asset_code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Equipment, Vehicle, Furniture, etc.
    location = Column(String(255), nullable=True)  # Physical location of asset
    
    # Purchase Information
    purchase_date = Column(Date, nullable=False)
    purchase_cost = Column(Numeric(15, 2), default=Decimal("0.00"))
    vendor_id = Column(Integer, ForeignKey('vendors.id', ondelete='SET NULL'), nullable=True)
    
    # Depreciation
    salvage_value = Column(Numeric(15, 2), default=Decimal("0.00"))
    useful_life_years = Column(Integer, default=5)
    depreciation_method = Column(String(50), default="straight_line")  # straight_line, declining_balance
    depreciation_rate = Column(Numeric(5, 2), default=Decimal("0.00"))  # For declining balance
    accumulated_depreciation = Column(Numeric(15, 2), default=Decimal("0.00"))
    book_value = Column(Numeric(15, 2), default=Decimal("0.00"))
    last_depreciation_date = Column(Date, nullable=True)
    
    # Status & Disposal
    status = Column(String(20), default=AssetStatus.ACTIVE.value)  # active, disposed, written_off, fully_depreciated
    disposal_date = Column(Date, nullable=True)
    disposal_amount = Column(Numeric(15, 2), nullable=True)
    disposal_reason = Column(Text, nullable=True)
    
    # Warranty
    warranty_expiry = Column(Date, nullable=True)
    
    # Insurance
    insurance_policy = Column(String(100), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    
    # Account linkage
    asset_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)  # Fixed Asset account
    depreciation_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)  # Accumulated Depreciation
    expense_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)  # Depreciation Expense
    
    # Branch & Business
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset_account = relationship("Account", foreign_keys=[asset_account_id])
    depreciation_account = relationship("Account", foreign_keys=[depreciation_account_id])
    expense_account = relationship("Account", foreign_keys=[expense_account_id])
    vendor = relationship("Vendor")
    branch = relationship("Branch")
    business = relationship("Business", back_populates="fixed_assets")
    depreciation_records = relationship("DepreciationRecord", back_populates="asset", cascade="all, delete-orphan")
    
    @property
    def annual_depreciation(self):
        """Calculate annual depreciation based on method"""
        if self.depreciation_method == "straight_line":
            depreciable_amount = self.purchase_cost - self.salvage_value
            return depreciable_amount / self.useful_life_years if self.useful_life_years > 0 else Decimal("0")
        elif self.depreciation_method == "declining_balance":
            rate = self.depreciation_rate / 100 if self.depreciation_rate else Decimal("20")
            return self.book_value * rate
        return Decimal("0")
    
    @property
    def remaining_life(self):
        """Calculate remaining useful life in years"""
        if self.accumulated_depreciation >= (self.purchase_cost - self.salvage_value):
            return 0
        annual_dep = self.annual_depreciation
        if annual_dep > 0:
            remaining_value = self.purchase_cost - self.salvage_value - self.accumulated_depreciation
            return max(0, int(remaining_value / annual_dep))
        return self.useful_life_years
    
    __table_args__ = (
        Index('ix_fixed_assets_business_id', 'business_id'),
        Index('ix_fixed_assets_branch_id', 'branch_id'),
        Index('ix_fixed_assets_status', 'status'),
    )


class DepreciationRecord(Base):
    """Depreciation Record for Fixed Assets"""
    __tablename__ = 'depreciation_records'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('fixed_assets.id', ondelete='CASCADE'), nullable=False)
    depreciation_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    method = Column(String(50), default="straight_line")
    description = Column(Text, nullable=True)
    
    # Journal entry linkage
    journal_voucher_id = Column(Integer, ForeignKey('journal_vouchers.id', ondelete='SET NULL'), nullable=True)
    
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = relationship("FixedAsset", back_populates="depreciation_records")
    journal_voucher = relationship("JournalVoucher")
    branch = relationship("Branch")
    business = relationship("Business")
    
    __table_args__ = (
        Index('ix_depreciation_records_asset_id', 'asset_id'),
        Index('ix_depreciation_records_date', 'depreciation_date'),
    )


# ==================== CASH BOOK ====================

class CashBookEntry(Base):
    """Cash Book Entry - Central hub for all cash/bank transactions"""
    __tablename__ = 'cash_book_entries'
    
    id = Column(Integer, primary_key=True)
    entry_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)
    entry_type = Column(String(20), nullable=False)  # receipt, payment, transfer, adjustment
    
    # Account information
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)  # Cash/Bank account
    account_type = Column(String(20), default='cash')  # cash, bank
    
    # Amount
    amount = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=True)  # Running balance after this entry
    
    # Description & Reference
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)
    payee_payer = Column(String(255), nullable=True)  # Who received/paid
    
    # Source linkage - what created this entry
    source_type = Column(String(50), nullable=True)  # sales_payment, purchase_payment, expense, income, transfer, manual
    source_id = Column(Integer, nullable=True)  # ID of the source document
    
    # For transfers
    transfer_id = Column(Integer, ForeignKey('fund_transfers.id', ondelete='SET NULL'), nullable=True)
    is_transfer = Column(Boolean, default=False)
    transfer_direction = Column(String(10), nullable=True)  # in, out
    
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account")
    transfer = relationship("FundTransfer")
    branch = relationship("Branch")
    business = relationship("Business")
    created_by_user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('entry_number', 'business_id', name='uq_cash_book_entry_number'),
        Index('ix_cash_book_entries_date', 'entry_date'),
        Index('ix_cash_book_entries_account', 'account_id'),
        Index('ix_cash_book_entries_type', 'entry_type'),
    )


# ==================== AUDIT LOG ====================

class AuditLog(Base):
    """Audit trail for sensitive operations"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Who performed the action
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = Column(String(100), nullable=True)  # Store username in case user is deleted
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # What action was performed
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(100), nullable=False)  # Model name: Invoice, Payment, User, etc.
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    
    # Where (business context)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'), nullable=True)
    
    # Details
    description = Column(Text, nullable=True)  # Human-readable description
    old_values = Column(Text, nullable=True)  # JSON string of old values (for updates)
    new_values = Column(Text, nullable=True)  # JSON string of new values
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)  # API endpoint
    
    # Status
    status = Column(String(20), default='success')  # success, failure, error
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="audit_logs")
    business = relationship("Business")
    branch = relationship("Branch")
    
    __table_args__ = (
        Index('ix_audit_logs_timestamp', 'timestamp'),
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_business_id', 'business_id'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_logs_action', 'action'),
    )


# ==================== FISCAL YEAR MANAGEMENT ====================

class FiscalYear(Base):
    """Fiscal Year for accounting periods"""
    __tablename__ = 'fiscal_years'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # e.g., "FY 2024", "2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business")
    periods = relationship("FiscalPeriod", back_populates="fiscal_year", cascade="all, delete-orphan")
    closed_by_user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('name', 'business_id', name='uq_fiscal_year_name'),
        Index('ix_fiscal_years_business_id', 'business_id'),
        Index('ix_fiscal_years_dates', 'start_date', 'end_date'),
    )


class FiscalPeriod(Base):
    """Fiscal Period (month/quarter within a fiscal year)"""
    __tablename__ = 'fiscal_periods'
    
    id = Column(Integer, primary_key=True)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False)
    period_number = Column(Integer, nullable=False)  # 1-12 for months, 1-4 for quarters
    name = Column(String(50), nullable=False)  # e.g., "January 2024", "Q1 2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_adjustment_period = Column(Boolean, default=False)  # Year-end adjustment period
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="periods")
    closed_by_user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_number', name='uq_fiscal_period_number'),
        Index('ix_fiscal_periods_dates', 'start_date', 'end_date'),
    )


class OpeningBalanceEntry(Base):
    """Opening Balance Entry for setting up initial account balances"""
    __tablename__ = 'opening_balance_entries'
    
    id = Column(Integer, primary_key=True)
    entry_number = Column(String(50), nullable=False)
    entry_date = Column(Date, nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    debit = Column(Numeric(15, 2), default=Decimal("0.00"))
    credit = Column(Numeric(15, 2), default=Decimal("0.00"))
    description = Column(Text, nullable=True)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    posted_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='SET NULL'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fiscal_year = relationship("FiscalYear")
    account = relationship("Account")
    branch = relationship("Branch")
    business = relationship("Business")
    created_by_user = relationship("User", foreign_keys=[created_by])
    posted_by_user = relationship("User", foreign_keys=[posted_by])
    
    __table_args__ = (
        UniqueConstraint('entry_number', 'business_id', name='uq_opening_balance_number'),
        Index('ix_opening_balances_business_id', 'business_id'),
        Index('ix_opening_balances_account', 'account_id'),
    )


class ClosingEntry(Base):
    """Year-end closing entry for temporary accounts"""
    __tablename__ = 'closing_entries'
    
    id = Column(Integer, primary_key=True)
    entry_number = Column(String(50), nullable=False)
    closing_date = Column(Date, nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey('fiscal_years.id', ondelete='CASCADE'), nullable=False)
    entry_type = Column(String(50), nullable=False)  # revenue_close, expense_close, income_summary, retained_earnings
    description = Column(Text, nullable=True)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    posted_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fiscal_year = relationship("FiscalYear")
    ledger_entries = relationship("LedgerEntry", back_populates="closing_entry")
    business = relationship("Business")
    posted_by_user = relationship("User", foreign_keys=[posted_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        UniqueConstraint('entry_number', 'business_id', name='uq_closing_entry_number'),
        Index('ix_closing_entries_business_id', 'business_id'),
    )


class BankReconciliationAdjustment(Base):
    """Bank reconciliation adjustment entries"""
    __tablename__ = 'bank_reconciliation_adjustments'
    
    id = Column(Integer, primary_key=True)
    adjustment_number = Column(String(50), nullable=False)
    adjustment_date = Column(Date, nullable=False)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'), nullable=False)
    adjustment_type = Column(String(50), nullable=False)  # bank_charge, interest, error_correction, other
    amount = Column(Numeric(15, 2), nullable=False)
    direction = Column(String(10), nullable=False)  # debit (decrease), credit (increase)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # Bank reference number
    reconciliation_id = Column(Integer, nullable=True)  # Link to reconciliation session if applicable
    journal_voucher_id = Column(Integer, ForeignKey('journal_vouchers.id', ondelete='SET NULL'), nullable=True)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bank_account = relationship("BankAccount")
    journal_voucher = relationship("JournalVoucher")
    branch = relationship("Branch")
    business = relationship("Business")
    created_by_user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('adjustment_number', 'business_id', name='uq_bank_adjustment_number'),
        Index('ix_bank_adjustments_bank_account', 'bank_account_id'),
        Index('ix_bank_adjustments_date', 'adjustment_date'),
    )


# ==================== BAD DEBT MANAGEMENT ====================

class BadDebt(Base):
    """Bad Debt record for tracking written-off receivables"""
    __tablename__ = 'bad_debts'
    
    id = Column(Integer, primary_key=True)
    bad_debt_number = Column(String(50), nullable=False)
    write_off_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default='written_off')  # written_off, recovered, partial_recovery
    
    # Source document
    sales_invoice_id = Column(Integer, ForeignKey('sales_invoices.id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    
    # Recovery tracking
    recovered_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    recovery_date = Column(Date, nullable=True)
    
    # Account linkage
    bad_debt_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    
    # Approval tracking
    approved_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    business_id = Column(Integer, ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales_invoice = relationship("SalesInvoice")
    customer = relationship("Customer")
    bad_debt_account = relationship("Account")
    branch = relationship("Branch")
    business = relationship("Business")
    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    ledger_entries = relationship("LedgerEntry", back_populates="bad_debt")
    
    @property
    def remaining_amount(self):
        """Calculate remaining unrecovered amount"""
        return self.amount - (self.recovered_amount or Decimal("0.00"))
    
    __table_args__ = (
        UniqueConstraint('bad_debt_number', 'business_id', name='uq_bad_debt_number'),
        Index('ix_bad_debts_business_id', 'business_id'),
        Index('ix_bad_debts_customer_id', 'customer_id'),
        Index('ix_bad_debts_date', 'write_off_date'),
        Index('ix_bad_debts_status', 'status'),
    )


# ==================== EXPORT ALL MODELS ====================

__all__ = [
    # Enums
    'AccountType', 'InvoiceStatus', 'PayFrequency', 'PlanType', 'AssetStatus',
    # Association Tables
    'RolePermission', 'UserBranchRole',
    # Core Models
    'Business', 'User', 'Branch', 'Permission', 'Role',
    # Accounting
    'Account', 'JournalVoucher', 'LedgerEntry',
    # Fiscal Year Management
    'FiscalYear', 'FiscalPeriod', 'OpeningBalanceEntry', 'ClosingEntry',
    # Bank Reconciliation
    'BankReconciliationAdjustment',
    # Bad Debt
    'BadDebt',
    # CRM
    'Customer', 'Vendor',
    # Inventory
    'Category', 'Product', 'StockAdjustment',
    # Sales
    'SalesInvoice', 'SalesInvoiceItem', 'Payment', 'CreditNote', 'CreditNoteItem',
    # Purchases
    'PurchaseBill', 'PurchaseBillItem', 'DebitNote', 'DebitNoteItem',
    # Expenses
    'Expense',
    # Other Income
    'OtherIncome',
    # HR
    'Employee', 'PayrollConfig', 'Payslip',
    # Banking
    'BankAccount', 'FundTransfer',
    # Budgeting
    'Budget', 'BudgetItem',
    # Fixed Assets
    'FixedAsset', 'DepreciationRecord',
    # Cash Book
    'CashBookEntry',
    # Audit
    'AuditLog',
]
