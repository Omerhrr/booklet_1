"""
Analytics Service - Query Builder and Data Aggregation
Provides powerful data analysis capabilities across all modules
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, extract, case
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import logging

from app.models import (
    SalesInvoice, SalesInvoiceItem, PurchaseBill, PurchaseBillItem,
    Customer, Vendor, Product, Category, Expense, OtherIncome,
    Employee, Payslip, Account, LedgerEntry, BankAccount, CashBookEntry,
    FixedAsset, Branch, Business
)

logger = logging.getLogger(__name__)


class DataSource:
    """Constants for available data sources"""
    SALES = 'sales'
    PURCHASES = 'purchases'
    INVENTORY = 'inventory'
    CASHBOOK = 'cashbook'
    LEDGER = 'ledger'
    EXPENSES = 'expenses'
    OTHER_INCOME = 'other_income'
    PAYROLL = 'payroll'
    FIXED_ASSETS = 'fixed_assets'
    CUSTOMERS = 'customers'
    VENDORS = 'vendors'


class FieldType:
    """Field type constants"""
    DIMENSION = 'dimension'  # Categorical fields for grouping
    MEASURE = 'measure'      # Numeric fields for aggregation
    DATE = 'date'           # Date fields


class AggregationType:
    """Aggregation function types"""
    SUM = 'sum'
    COUNT = 'count'
    AVG = 'avg'
    MIN = 'min'
    MAX = 'max'
    COUNT_DISTINCT = 'count_distinct'


# Data source configurations with available fields
DATA_SOURCE_CONFIG = {
    DataSource.SALES: {
        'name': 'Sales',
        'model': SalesInvoice,
        'fields': {
            # Dimensions
            'invoice_date': {'type': FieldType.DATE, 'label': 'Invoice Date'},
            'due_date': {'type': FieldType.DATE, 'label': 'Due Date'},
            'status': {'type': FieldType.DIMENSION, 'label': 'Status'},
            'customer_id': {'type': FieldType.DIMENSION, 'label': 'Customer', 'relation': 'customer.name'},
            'customer_name': {'type': FieldType.DIMENSION, 'label': 'Customer Name'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'invoice_number': {'type': FieldType.DIMENSION, 'label': 'Invoice Number'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'invoice_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'invoice_date'},
            'quarter': {'type': FieldType.DIMENSION, 'label': 'Quarter', 'extract': 'quarter', 'from': 'invoice_date'},
            'weekday': {'type': FieldType.DIMENSION, 'label': 'Day of Week', 'extract': 'dow', 'from': 'invoice_date'},
            # Measures
            'sub_total': {'type': FieldType.MEASURE, 'label': 'Sub Total'},
            'vat_amount': {'type': FieldType.MEASURE, 'label': 'VAT Amount'},
            'total_amount': {'type': FieldType.MEASURE, 'label': 'Total Amount'},
            'paid_amount': {'type': FieldType.MEASURE, 'label': 'Paid Amount'},
            'balance_due': {'type': FieldType.MEASURE, 'label': 'Balance Due', 'computed': 'total_amount - paid_amount'},
            'invoice_count': {'type': FieldType.MEASURE, 'label': 'Invoice Count', 'aggregate': 'count'},
        }
    },
    DataSource.PURCHASES: {
        'name': 'Purchases',
        'model': PurchaseBill,
        'fields': {
            # Dimensions
            'bill_date': {'type': FieldType.DATE, 'label': 'Bill Date'},
            'due_date': {'type': FieldType.DATE, 'label': 'Due Date'},
            'status': {'type': FieldType.DIMENSION, 'label': 'Status'},
            'vendor_id': {'type': FieldType.DIMENSION, 'label': 'Vendor', 'relation': 'vendor.name'},
            'vendor_name': {'type': FieldType.DIMENSION, 'label': 'Vendor Name'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'bill_number': {'type': FieldType.DIMENSION, 'label': 'Bill Number'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'bill_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'bill_date'},
            'quarter': {'type': FieldType.DIMENSION, 'label': 'Quarter', 'extract': 'quarter', 'from': 'bill_date'},
            # Measures
            'sub_total': {'type': FieldType.MEASURE, 'label': 'Sub Total'},
            'vat_amount': {'type': FieldType.MEASURE, 'label': 'VAT Amount'},
            'total_amount': {'type': FieldType.MEASURE, 'label': 'Total Amount'},
            'paid_amount': {'type': FieldType.MEASURE, 'label': 'Paid Amount'},
            'balance_due': {'type': FieldType.MEASURE, 'label': 'Balance Due', 'computed': 'total_amount - paid_amount'},
            'bill_count': {'type': FieldType.MEASURE, 'label': 'Bill Count', 'aggregate': 'count'},
        }
    },
    DataSource.INVENTORY: {
        'name': 'Inventory',
        'model': Product,
        'fields': {
            # Dimensions
            'name': {'type': FieldType.DIMENSION, 'label': 'Product Name'},
            'sku': {'type': FieldType.DIMENSION, 'label': 'SKU'},
            'category_id': {'type': FieldType.DIMENSION, 'label': 'Category', 'relation': 'category.name'},
            'category_name': {'type': FieldType.DIMENSION, 'label': 'Category Name'},
            'unit': {'type': FieldType.DIMENSION, 'label': 'Unit'},
            'is_active': {'type': FieldType.DIMENSION, 'label': 'Active'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            # Measures
            'stock_quantity': {'type': FieldType.MEASURE, 'label': 'Stock Quantity'},
            'opening_stock': {'type': FieldType.MEASURE, 'label': 'Opening Stock'},
            'reorder_level': {'type': FieldType.MEASURE, 'label': 'Reorder Level'},
            'purchase_price': {'type': FieldType.MEASURE, 'label': 'Purchase Price'},
            'sales_price': {'type': FieldType.MEASURE, 'label': 'Sales Price'},
            'stock_value': {'type': FieldType.MEASURE, 'label': 'Stock Value', 'computed': 'stock_quantity * purchase_price'},
            'product_count': {'type': FieldType.MEASURE, 'label': 'Product Count', 'aggregate': 'count'},
        }
    },
    DataSource.EXPENSES: {
        'name': 'Expenses',
        'model': Expense,
        'fields': {
            # Dimensions
            'expense_date': {'type': FieldType.DATE, 'label': 'Expense Date'},
            'category': {'type': FieldType.DIMENSION, 'label': 'Category'},
            'vendor_id': {'type': FieldType.DIMENSION, 'label': 'Vendor'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'expense_number': {'type': FieldType.DIMENSION, 'label': 'Expense Number'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'expense_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'expense_date'},
            # Measures
            'sub_total': {'type': FieldType.MEASURE, 'label': 'Sub Total'},
            'vat_amount': {'type': FieldType.MEASURE, 'label': 'VAT Amount'},
            'amount': {'type': FieldType.MEASURE, 'label': 'Amount'},
            'expense_count': {'type': FieldType.MEASURE, 'label': 'Expense Count', 'aggregate': 'count'},
        }
    },
    DataSource.OTHER_INCOME: {
        'name': 'Other Income',
        'model': OtherIncome,
        'fields': {
            # Dimensions
            'income_date': {'type': FieldType.DATE, 'label': 'Income Date'},
            'category': {'type': FieldType.DIMENSION, 'label': 'Category'},
            'customer_id': {'type': FieldType.DIMENSION, 'label': 'Customer'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'income_number': {'type': FieldType.DIMENSION, 'label': 'Income Number'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'income_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'income_date'},
            # Measures
            'sub_total': {'type': FieldType.MEASURE, 'label': 'Sub Total'},
            'vat_amount': {'type': FieldType.MEASURE, 'label': 'VAT Amount'},
            'amount': {'type': FieldType.MEASURE, 'label': 'Amount'},
            'income_count': {'type': FieldType.MEASURE, 'label': 'Income Count', 'aggregate': 'count'},
        }
    },
    DataSource.CASHBOOK: {
        'name': 'Cash Book',
        'model': CashBookEntry,
        'fields': {
            # Dimensions
            'entry_date': {'type': FieldType.DATE, 'label': 'Entry Date'},
            'entry_type': {'type': FieldType.DIMENSION, 'label': 'Entry Type'},
            'account_id': {'type': FieldType.DIMENSION, 'label': 'Account'},
            'source_type': {'type': FieldType.DIMENSION, 'label': 'Source Type'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'entry_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'entry_date'},
            # Measures
            'amount': {'type': FieldType.MEASURE, 'label': 'Amount'},
            'receipt_amount': {'type': FieldType.MEASURE, 'label': 'Receipt Amount', 'computed': "CASE WHEN entry_type = 'receipt' THEN amount ELSE 0 END"},
            'payment_amount': {'type': FieldType.MEASURE, 'label': 'Payment Amount', 'computed': "CASE WHEN entry_type = 'payment' THEN amount ELSE 0 END"},
            'entry_count': {'type': FieldType.MEASURE, 'label': 'Entry Count', 'aggregate': 'count'},
        }
    },
    DataSource.LEDGER: {
        'name': 'General Ledger',
        'model': LedgerEntry,
        'fields': {
            # Dimensions
            'transaction_date': {'type': FieldType.DATE, 'label': 'Transaction Date'},
            'account_id': {'type': FieldType.DIMENSION, 'label': 'Account'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'transaction_date'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'transaction_date'},
            # Measures
            'debit': {'type': FieldType.MEASURE, 'label': 'Debit'},
            'credit': {'type': FieldType.MEASURE, 'label': 'Credit'},
            'net_amount': {'type': FieldType.MEASURE, 'label': 'Net Amount', 'computed': 'debit - credit'},
            'entry_count': {'type': FieldType.MEASURE, 'label': 'Entry Count', 'aggregate': 'count'},
        }
    },
    DataSource.PAYROLL: {
        'name': 'Payroll',
        'model': Payslip,
        'fields': {
            # Dimensions
            'pay_period_start': {'type': FieldType.DATE, 'label': 'Pay Period Start'},
            'pay_period_end': {'type': FieldType.DATE, 'label': 'Pay Period End'},
            'employee_id': {'type': FieldType.DIMENSION, 'label': 'Employee'},
            'department': {'type': FieldType.DIMENSION, 'label': 'Department'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'status': {'type': FieldType.DIMENSION, 'label': 'Status'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'pay_period_start'},
            'month': {'type': FieldType.DIMENSION, 'label': 'Month', 'extract': 'month', 'from': 'pay_period_start'},
            # Measures
            'gross_salary': {'type': FieldType.MEASURE, 'label': 'Gross Salary'},
            'net_salary': {'type': FieldType.MEASURE, 'label': 'Net Salary'},
            'paye_deduction': {'type': FieldType.MEASURE, 'label': 'PAYE'},
            'pension_employee': {'type': FieldType.MEASURE, 'label': 'Employee Pension'},
            'pension_employer': {'type': FieldType.MEASURE, 'label': 'Employer Pension'},
            'total_deductions': {'type': FieldType.MEASURE, 'label': 'Total Deductions'},
            'payslip_count': {'type': FieldType.MEASURE, 'label': 'Payslip Count', 'aggregate': 'count'},
        }
    },
    DataSource.FIXED_ASSETS: {
        'name': 'Fixed Assets',
        'model': FixedAsset,
        'fields': {
            # Dimensions
            'name': {'type': FieldType.DIMENSION, 'label': 'Asset Name'},
            'asset_code': {'type': FieldType.DIMENSION, 'label': 'Asset Code'},
            'category': {'type': FieldType.DIMENSION, 'label': 'Category'},
            'status': {'type': FieldType.DIMENSION, 'label': 'Status'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'purchase_date': {'type': FieldType.DATE, 'label': 'Purchase Date'},
            'year': {'type': FieldType.DIMENSION, 'label': 'Year', 'extract': 'year', 'from': 'purchase_date'},
            # Measures
            'purchase_cost': {'type': FieldType.MEASURE, 'label': 'Purchase Cost'},
            'salvage_value': {'type': FieldType.MEASURE, 'label': 'Salvage Value'},
            'accumulated_depreciation': {'type': FieldType.MEASURE, 'label': 'Accumulated Depreciation'},
            'book_value': {'type': FieldType.MEASURE, 'label': 'Book Value'},
            'asset_count': {'type': FieldType.MEASURE, 'label': 'Asset Count', 'aggregate': 'count'},
        }
    },
    DataSource.CUSTOMERS: {
        'name': 'Customers',
        'model': Customer,
        'fields': {
            # Dimensions
            'name': {'type': FieldType.DIMENSION, 'label': 'Customer Name'},
            'email': {'type': FieldType.DIMENSION, 'label': 'Email'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'is_active': {'type': FieldType.DIMENSION, 'label': 'Active'},
            # Measures
            'credit_limit': {'type': FieldType.MEASURE, 'label': 'Credit Limit'},
            'account_balance': {'type': FieldType.MEASURE, 'label': 'Account Balance'},
            'customer_count': {'type': FieldType.MEASURE, 'label': 'Customer Count', 'aggregate': 'count'},
        }
    },
    DataSource.VENDORS: {
        'name': 'Vendors',
        'model': Vendor,
        'fields': {
            # Dimensions
            'name': {'type': FieldType.DIMENSION, 'label': 'Vendor Name'},
            'email': {'type': FieldType.DIMENSION, 'label': 'Email'},
            'branch_id': {'type': FieldType.DIMENSION, 'label': 'Branch'},
            'is_active': {'type': FieldType.DIMENSION, 'label': 'Active'},
            # Measures
            'account_balance': {'type': FieldType.MEASURE, 'label': 'Account Balance'},
            'vendor_count': {'type': FieldType.MEASURE, 'label': 'Vendor Count', 'aggregate': 'count'},
        }
    },
}


class AnalyticsService:
    """Service for building and executing analytics queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get list of available data sources"""
        return [
            {
                'id': source_id,
                'name': config['name'],
                'field_count': len(config['fields'])
            }
            for source_id, config in DATA_SOURCE_CONFIG.items()
        ]
    
    def get_data_source_fields(self, data_source: str) -> Dict[str, Any]:
        """Get available fields for a data source"""
        if data_source not in DATA_SOURCE_CONFIG:
            return {}
        
        config = DATA_SOURCE_CONFIG[data_source]
        
        # Group fields by type
        dimensions = []
        measures = []
        date_fields = []
        
        for field_id, field_config in config['fields'].items():
            field_info = {
                'id': field_id,
                'label': field_config['label'],
                'type': field_config['type']
            }
            
            if field_config['type'] == FieldType.DIMENSION:
                dimensions.append(field_info)
            elif field_config['type'] == FieldType.MEASURE:
                measures.append(field_info)
            elif field_config['type'] == FieldType.DATE:
                date_fields.append(field_info)
        
        return {
            'name': config['name'],
            'dimensions': dimensions,
            'measures': measures,
            'date_fields': date_fields,
            'all_fields': config['fields']
        }
    
    def execute_query(
        self,
        data_source: str,
        columns: List[str],
        filters: Optional[List[Dict]] = None,
        group_by: Optional[List[str]] = None,
        aggregations: Optional[Dict[str, str]] = None,
        order_by: Optional[List[Dict]] = None,
        limit: Optional[int] = None,
        branch_id: Optional[int] = None,
        business_id: Optional[int] = None
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Execute an analytics query and return results with metadata.
        
        Args:
            data_source: Data source ID (sales, purchases, etc.)
            columns: List of column names to select
            filters: List of filter conditions [{field, operator, value}]
            group_by: List of fields to group by
            aggregations: Dict of {field: aggregation_type}
            order_by: List of {field, direction} for sorting
            limit: Maximum number of results
            branch_id: Filter by branch
            business_id: Filter by business
        
        Returns:
            Tuple of (results list, query metadata)
        """
        if data_source not in DATA_SOURCE_CONFIG:
            raise ValueError(f"Unknown data source: {data_source}")
        
        config = DATA_SOURCE_CONFIG[data_source]
        model = config['model']
        
        # Build base query
        query = self.db.query(model)
        
        # Apply business filter (required)
        if business_id:
            query = query.filter(model.business_id == business_id)
        
        # Apply branch filter
        if branch_id:
            query = query.filter(model.branch_id == branch_id)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, model, filters, config['fields'])
        
        # Apply grouping and aggregations
        if group_by or aggregations:
            query = self._apply_grouping(query, model, group_by, aggregations, config['fields'])
        else:
            # Simple select
            query = self._apply_columns(query, model, columns, config['fields'])
        
        # Apply ordering
        if order_by:
            for order in order_by:
                field = order.get('field')
                direction = order.get('direction', 'asc')
                if field and hasattr(model, field):
                    if direction == 'desc':
                        query = query.order_by(desc(getattr(model, field)))
                    else:
                        query = query.order_by(asc(getattr(model, field)))
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        # Execute query
        try:
            results = query.all()
            
            # Convert to list of dicts
            if group_by or aggregations:
                # Grouped/aggregated results come as Row objects with labeled columns
                # Build proper column names matching the labels used in _apply_grouping
                agg_column_names = []
                if aggregations:
                    for field, agg_type in aggregations.items():
                        if agg_type == AggregationType.SUM:
                            agg_column_names.append(f'{field}_sum')
                        elif agg_type == AggregationType.COUNT:
                            agg_column_names.append(f'{field}_count')
                        elif agg_type == AggregationType.AVG:
                            agg_column_names.append(f'{field}_avg')
                        elif agg_type == AggregationType.MIN:
                            agg_column_names.append(f'{field}_min')
                        elif agg_type == AggregationType.MAX:
                            agg_column_names.append(f'{field}_max')
                        elif agg_type == AggregationType.COUNT_DISTINCT:
                            agg_column_names.append(f'{field}_distinct')
                
                column_names = (group_by or []) + agg_column_names
                results = [dict(zip(column_names, row)) for row in results]
            else:
                # Simple select - use _model_to_dict which handles Row objects
                results = [self._model_to_dict(r) for r in results]
            
            # Convert datetime/decimal to string for JSON serialization
            results = self._serialize_results(results)
            
            metadata = {
                'data_source': data_source,
                'row_count': len(results),
                'columns': columns or list(config['fields'].keys()),
                'group_by': group_by,
                'aggregations': aggregations
            }
            
            return results, metadata
            
        except Exception as e:
            logger.error(f"Analytics query error: {e}")
            raise
    
    def _apply_filters(self, query, model, filters: List[Dict], fields_config: Dict):
        """Apply filter conditions to query"""
        for f in filters:
            field = f.get('field')
            operator = f.get('operator', 'eq')
            value = f.get('value')
            
            if not field or value is None:
                continue
            
            # Handle date fields
            field_config = fields_config.get(field, {})
            if field_config.get('extract'):
                # Extracted field (year, month, etc.)
                extract_type = field_config['extract']
                from_field = field_config['from']
                column = extract(extract_type, getattr(model, from_field))
            elif hasattr(model, field):
                column = getattr(model, field)
            else:
                continue
            
            # Apply operator
            if operator == 'eq':
                query = query.filter(column == value)
            elif operator == 'ne':
                query = query.filter(column != value)
            elif operator == 'gt':
                query = query.filter(column > value)
            elif operator == 'gte':
                query = query.filter(column >= value)
            elif operator == 'lt':
                query = query.filter(column < value)
            elif operator == 'lte':
                query = query.filter(column <= value)
            elif operator == 'like':
                query = query.filter(column.ilike(f'%{value}%'))
            elif operator == 'in':
                if isinstance(value, list):
                    query = query.filter(column.in_(value))
            elif operator == 'between':
                if isinstance(value, list) and len(value) == 2:
                    query = query.filter(column.between(value[0], value[1]))
        
        return query
    
    def _apply_columns(self, query, model, columns: List[str], fields_config: Dict):
        """Apply column selection to query"""
        if not columns:
            # Return all columns if none specified
            return query
        
        select_columns = []
        for field in columns:
            field_config = fields_config.get(field, {})
            if field_config.get('extract'):
                # Extracted field (year, month, etc.)
                extract_type = field_config['extract']
                from_field = field_config['from']
                select_columns.append(extract(extract_type, getattr(model, from_field)).label(field))
            elif hasattr(model, field):
                select_columns.append(getattr(model, field).label(field))
        
        if select_columns:
            query = query.with_entities(*select_columns)
        
        return query
    
    def _apply_grouping(self, query, model, group_by: List[str], aggregations: Dict[str, str], fields_config: Dict):
        """Apply grouping and aggregations to query"""
        select_columns = []
        
        # Add group by columns
        if group_by:
            for field in group_by:
                field_config = fields_config.get(field, {})
                if field_config.get('extract'):
                    extract_type = field_config['extract']
                    from_field = field_config['from']
                    select_columns.append(extract(extract_type, getattr(model, from_field)).label(field))
                elif hasattr(model, field):
                    select_columns.append(getattr(model, field).label(field))
            
            query = query.group_by(*select_columns)
        
        # Add aggregation columns
        if aggregations:
            for field, agg_type in aggregations.items():
                if not hasattr(model, field):
                    continue
                
                column = getattr(model, field)
                
                if agg_type == AggregationType.SUM:
                    select_columns.append(func.sum(column).label(f'{field}_sum'))
                elif agg_type == AggregationType.COUNT:
                    select_columns.append(func.count(column).label(f'{field}_count'))
                elif agg_type == AggregationType.AVG:
                    select_columns.append(func.avg(column).label(f'{field}_avg'))
                elif agg_type == AggregationType.MIN:
                    select_columns.append(func.min(column).label(f'{field}_min'))
                elif agg_type == AggregationType.MAX:
                    select_columns.append(func.max(column).label(f'{field}_max'))
                elif agg_type == AggregationType.COUNT_DISTINCT:
                    select_columns.append(func.count(column.distinct()).label(f'{field}_distinct'))
        
        if select_columns:
            query = query.with_entities(*select_columns)
        
        return query
    
    def _model_to_dict(self, model_or_row) -> Dict:
        """Convert SQLAlchemy model or Row object to dictionary"""
        result = {}
        
        try:
            # Check if it's a Row object (from with_entities) - SQLAlchemy 1.4+/2.0
            if hasattr(model_or_row, '_mapping'):
                # SQLAlchemy 2.0 style Row with _mapping - most reliable
                result = dict(model_or_row._mapping)
            elif hasattr(model_or_row, '_fields'):
                # It's a Row object with _fields attribute
                # Use _asdict() if available, otherwise build manually
                if hasattr(model_or_row, '_asdict'):
                    result = model_or_row._asdict()
                else:
                    # Build dict from _fields using attribute access
                    for key in model_or_row._fields:
                        result[key] = getattr(model_or_row, key, None)
            elif hasattr(model_or_row, '__table__'):
                # It's a full model instance
                for column in model_or_row.__table__.columns:
                    value = getattr(model_or_row, column.name)
                    result[column.name] = value
            elif isinstance(model_or_row, dict):
                # Already a dict
                result = model_or_row
            else:
                # Last resort: try to iterate or use _asdict
                if hasattr(model_or_row, '_asdict'):
                    result = model_or_row._asdict()
                else:
                    try:
                        for key, value in model_or_row.items():
                            result[key] = value
                    except (TypeError, AttributeError):
                        pass
        except Exception as e:
            logger.warning(f"Error converting to dict: {e}")
            # Return empty dict on error
            pass
        
        return result
    
    def _serialize_results(self, results: List[Dict]) -> List[Dict]:
        """Serialize results for JSON response"""
        serialized = []
        for row in results:
            new_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    new_row[key] = value.isoformat()
                elif isinstance(value, date):
                    new_row[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    new_row[key] = float(value)
                elif value is None:
                    new_row[key] = None
                else:
                    new_row[key] = value
            serialized.append(new_row)
        return serialized
    
    def get_summary_stats(
        self,
        data_source: str,
        branch_id: Optional[int] = None,
        business_id: Optional[int] = None,
        date_field: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary statistics for a data source"""
        if data_source not in DATA_SOURCE_CONFIG:
            return {}
        
        config = DATA_SOURCE_CONFIG[data_source]
        model = config['model']
        
        query = self.db.query(model)
        
        if business_id:
            query = query.filter(model.business_id == business_id)
        if branch_id:
            query = query.filter(model.branch_id == branch_id)
        if date_field and start_date:
            query = query.filter(getattr(model, date_field) >= start_date)
        if date_field and end_date:
            query = query.filter(getattr(model, date_field) <= end_date)
        
        # Count records
        count = query.count()
        
        # Get measure field stats
        stats = {'count': count}
        
        for field_id, field_config in config['fields'].items():
            if field_config['type'] == FieldType.MEASURE and hasattr(model, field_id):
                column = getattr(model, field_id)
                result = self.db.query(
                    func.sum(column).label('sum'),
                    func.avg(column).label('avg'),
                    func.min(column).label('min'),
                    func.max(column).label('max')
                ).filter(model.business_id == business_id).first() if business_id else None
                
                if result:
                    stats[field_id] = {
                        'sum': float(result.sum or 0),
                        'avg': float(result.avg or 0),
                        'min': float(result.min or 0),
                        'max': float(result.max or 0)
                    }
        
        return stats
