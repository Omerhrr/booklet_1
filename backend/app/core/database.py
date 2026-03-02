"""
Database Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from app.core.config import settings

# Get the properly formatted database URL
db_url = settings.database_url

# Create engine
engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models to register them with Base
    from app.models import (
        Business, User, Branch, Permission, Role, UserBranchRole, RolePermission,
        Account, JournalVoucher, LedgerEntry, Budget, BudgetItem, FixedAsset,
        Customer, Vendor, Category, Product, StockAdjustment,
        SalesInvoice, SalesInvoiceItem, Payment, CreditNote, CreditNoteItem,
        PurchaseBill, PurchaseBillItem, DebitNote, DebitNoteItem,
        Employee, PayrollConfig, Payslip, BankAccount, FundTransfer, Expense,
        OtherIncome, AuditLog
    )
    Base.metadata.create_all(bind=engine)
