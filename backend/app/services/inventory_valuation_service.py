"""
Inventory Valuation Service - FIFO and Weighted Average Cost Methods
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from decimal import Decimal
from datetime import date
from app.models import Product, PurchaseBillItem, SalesInvoiceItem, LedgerEntry, Account, AccountType


class InventoryCostLayer:
    """Represents a cost layer for FIFO inventory tracking"""
    def __init__(self, quantity: Decimal, unit_cost: Decimal, date: date, reference: str):
        self.quantity = quantity
        self.unit_cost = unit_cost
        self.date = date
        self.reference = reference


class InventoryValuationService:
    """Service for calculating inventory values using different methods"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_fifo_cost(self, product_id: int, business_id: int, branch_id: int,
                            quantity: Decimal, as_of_date: date = None) -> Decimal:
        """
        Calculate the cost of goods sold using FIFO method.
        
        For FIFO (First-In, First-Out), we assume that the oldest inventory is sold first.
        Returns the total cost for the given quantity.
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get all purchase items for this product up to the given date
        purchase_items = self.db.query(PurchaseBillItem).join(
            PurchaseBillItem.purchase_bill
        ).options(
            joinedload(PurchaseBillItem.purchase_bill)
        ).filter(
            PurchaseBillItem.product_id == product_id,
            PurchaseBill.purchase_bill.business_id == business_id,
            PurchaseBill.purchase_bill.bill_date <= as_of_date
        ).order_by(PurchaseBill.purchase_bill.bill_date, PurchaseBillItem.id).all()
        
        # Build cost layers from purchases
        cost_layers: List[InventoryCostLayer] = []
        
        for item in purchase_items:
            net_quantity = item.quantity - (item.returned_quantity or Decimal("0"))
            if net_quantity > 0:
                unit_cost = item.price  # Use purchase price as unit cost
                cost_layers.append(InventoryCostLayer(
                    quantity=net_quantity,
                    unit_cost=unit_cost,
                    date=item.purchase_bill.bill_date,
                    reference=item.purchase_bill.bill_number
                ))
        
        # Get sales items to consume layers
        sales_items = self.db.query(SalesInvoiceItem).join(
            SalesInvoiceItem.sales_invoice
        ).filter(
            SalesInvoiceItem.product_id == product_id,
            SalesInvoice.sales_invoice.business_id == business_id,
            SalesInvoice.sales_invoice.invoice_date <= as_of_date
        ).order_by(SalesInvoice.sales_invoice.invoice_date, SalesInvoiceItem.id).all()
        
        # Consume layers based on sales (FIFO)
        for sale in sales_items:
            remaining_to_consume = sale.quantity - (sale.returned_quantity or Decimal("0"))
            
            for layer in cost_layers:
                if remaining_to_consume <= 0:
                    break
                if layer.quantity > 0:
                    consume_amount = min(layer.quantity, remaining_to_consume)
                    layer.quantity -= consume_amount
                    remaining_to_consume -= consume_amount
        
        # Calculate remaining inventory value
        remaining_quantity = Decimal("0")
        remaining_value = Decimal("0")
        
        for layer in cost_layers:
            if layer.quantity > 0:
                remaining_quantity += layer.quantity
                remaining_value += layer.quantity * layer.unit_cost
        
        # Calculate cost for the requested quantity
        cost = Decimal("0")
        remaining_to_cost = quantity
        
        for layer in cost_layers:
            if remaining_to_cost <= 0:
                break
            if layer.quantity > 0:
                use_amount = min(layer.quantity, remaining_to_cost)
                cost += use_amount * layer.unit_cost
                remaining_to_cost -= use_amount
        
        return cost
    
    def calculate_weighted_average_cost(self, product_id: int, business_id: int,
                                        as_of_date: date = None) -> Decimal:
        """
        Calculate the weighted average cost of inventory.
        
        For Weighted Average, the cost per unit is calculated as:
        (Total Cost of Goods Available) / (Total Units Available)
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get all purchase items for this product up to the given date
        purchase_items = self.db.query(PurchaseBillItem).join(
            PurchaseBillItem.purchase_bill
        ).filter(
            PurchaseBillItem.product_id == product_id,
            PurchaseBill.purchase_bill.business_id == business_id,
            PurchaseBill.purchase_bill.bill_date <= as_of_date
        ).all()
        
        # Calculate total quantity and total cost
        total_quantity = Decimal("0")
        total_cost = Decimal("0")
        
        for item in purchase_items:
            net_quantity = item.quantity - (item.returned_quantity or Decimal("0"))
            if net_quantity > 0:
                total_quantity += net_quantity
                total_cost += net_quantity * item.price
        
        # Get sales items to get remaining quantity
        sales_items = self.db.query(SalesInvoiceItem).join(
            SalesInvoiceItem.sales_invoice
        ).filter(
            SalesInvoiceItem.product_id == product_id,
            SalesInvoice.sales_invoice.business_id == business_id,
            SalesInvoice.sales_invoice.invoice_date <= as_of_date
        ).all()
        
        sold_quantity = Decimal("0")
        for sale in sales_items:
            sold_quantity += sale.quantity - (sale.returned_quantity or Decimal("0"))
        
        remaining_quantity = total_quantity - sold_quantity
        
        # Calculate weighted average cost per unit
        if total_quantity > 0:
            average_cost_per_unit = total_cost / total_quantity
        else:
            average_cost_per_unit = Decimal("0")
        
        return average_cost_per_unit
    
    def calculate_inventory_value(self, product_id: int, business_id: int, branch_id: int,
                                  method: str = 'fifo', as_of_date: date = None) -> Dict:
        """
        Calculate the inventory value for a product using the specified method.
        
        Args:
            product_id: The product ID
            business_id: The business ID
            branch_id: The branch ID
            method: 'fifo' or 'weighted_average'
            as_of_date: The date for which to calculate the value
        
        Returns:
            Dict with quantity, unit_cost, total_value, and method
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.business_id == business_id
        ).first()
        
        if not product:
            return {"error": "Product not found"}
        
        current_quantity = product.stock_quantity
        
        if method == 'fifo':
            # For FIFO, we need to track layers
            unit_cost = self._get_fifo_unit_cost(product_id, business_id, as_of_date)
        else:  # weighted_average
            unit_cost = self.calculate_weighted_average_cost(product_id, business_id, as_of_date)
        
        total_value = current_quantity * unit_cost
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "quantity": float(current_quantity),
            "unit_cost": float(unit_cost),
            "total_value": float(total_value),
            "method": method,
            "as_of_date": as_of_date.isoformat()
        }
    
    def _get_fifo_unit_cost(self, product_id: int, business_id: int, as_of_date: date) -> Decimal:
        """Get the average unit cost for remaining inventory using FIFO"""
        # Get all purchase items for this product up to the given date
        purchase_items = self.db.query(PurchaseBillItem).join(
            PurchaseBillItem.purchase_bill
        ).options(
            joinedload(PurchaseBillItem.purchase_bill)
        ).filter(
            PurchaseBillItem.product_id == product_id,
            PurchaseBill.purchase_bill.business_id == business_id,
            PurchaseBill.purchase_bill.bill_date <= as_of_date
        ).order_by(PurchaseBill.purchase_bill.bill_date, PurchaseBillItem.id).all()
        
        # Build and consume layers
        cost_layers = []
        
        for item in purchase_items:
            net_quantity = item.quantity - (item.returned_quantity or Decimal("0"))
            if net_quantity > 0:
                cost_layers.append({
                    "quantity": net_quantity,
                    "unit_cost": item.price
                })
        
        # Get sales items to consume layers
        sales_items = self.db.query(SalesInvoiceItem).join(
            SalesInvoiceItem.sales_invoice
        ).filter(
            SalesInvoiceItem.product_id == product_id,
            SalesInvoice.sales_invoice.business_id == business_id,
            SalesInvoice.sales_invoice.invoice_date <= as_of_date
        ).order_by(SalesInvoice.sales_invoice.invoice_date, SalesInvoiceItem.id).all()
        
        for sale in sales_items:
            remaining = sale.quantity - (sale.returned_quantity or Decimal("0"))
            
            for layer in cost_layers:
                if remaining <= 0:
                    break
                if layer["quantity"] > 0:
                    consume = min(layer["quantity"], remaining)
                    layer["quantity"] -= consume
                    remaining -= consume
        
        # Calculate weighted average of remaining layers
        total_value = Decimal("0")
        total_quantity = Decimal("0")
        
        for layer in cost_layers:
            if layer["quantity"] > 0:
                total_value += layer["quantity"] * layer["unit_cost"]
                total_quantity += layer["quantity"]
        
        if total_quantity > 0:
            return total_value / total_quantity
        return Decimal("0")
    
    def get_inventory_valuation_report(self, business_id: int, branch_id: int,
                                       method: str = 'fifo', 
                                       category_id: int = None,
                                       as_of_date: date = None) -> Dict:
        """
        Generate an inventory valuation report for all products or a specific category.
        
        Returns total inventory value broken down by product.
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        query = self.db.query(Product).filter(
            Product.business_id == business_id,
            Product.is_active == True,
            Product.stock_quantity > 0
        )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        products = query.all()
        
        items = []
        total_value = Decimal("0")
        total_quantity = Decimal("0")
        
        for product in products:
            value_info = self.calculate_inventory_value(
                product.id, business_id, branch_id, method, as_of_date
            )
            
            if "error" not in value_info:
                items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "sku": product.sku,
                    "category": product.category.name if product.category else None,
                    "quantity": value_info["quantity"],
                    "unit_cost": value_info["unit_cost"],
                    "total_value": value_info["total_value"],
                    "purchase_price": float(product.purchase_price),
                    "sales_price": float(product.sales_price)
                })
                total_value += Decimal(str(value_info["total_value"]))
                total_quantity += Decimal(str(value_info["quantity"]))
        
        return {
            "as_of_date": as_of_date.isoformat(),
            "valuation_method": method,
            "items": items,
            "summary": {
                "total_products": len(items),
                "total_quantity": float(total_quantity),
                "total_value": float(total_value)
            }
        }
    
    def calculate_cogs_for_sale(self, product_id: int, quantity: Decimal,
                                business_id: int, method: str = 'fifo') -> Decimal:
        """
        Calculate the Cost of Goods Sold for a specific sale quantity.
        
        This is used when creating a sales invoice to determine the COGS amount.
        """
        if method == 'fifo':
            return self.calculate_fifo_cost(product_id, business_id, None, quantity)
        else:
            avg_cost = self.calculate_weighted_average_cost(product_id, business_id)
            return quantity * avg_cost
    
    def create_inventory_ledger_entries(self, product_id: int, quantity_change: Decimal,
                                        transaction_type: str, transaction_date: date,
                                        business_id: int, branch_id: int,
                                        reference: str = None, 
                                        method: str = 'fifo') -> List[LedgerEntry]:
        """
        Create inventory and COGS ledger entries for a transaction.
        
        Args:
            product_id: The product being transacted
            quantity_change: Positive for purchases, negative for sales
            transaction_type: 'purchase', 'sale', or 'adjustment'
            transaction_date: Date of transaction
            business_id: Business ID
            branch_id: Branch ID
            reference: Reference number (invoice/bill number)
            method: Valuation method
        
        Returns:
            List of LedgerEntry objects (not yet saved to DB)
        """
        product = self.db.query(Product).filter(
            Product.id == product_id,
            Product.business_id == business_id
        ).first()
        
        if not product:
            raise ValueError("Product not found")
        
        # Get inventory and COGS accounts
        inventory_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Inventory"
        ).first()
        
        cogs_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name == "Cost of Goods Sold"
        ).first()
        
        cash_account = self.db.query(Account).filter(
            Account.business_id == business_id,
            Account.name.ilike("%Cash%")
        ).first()
        
        entries = []
        
        if quantity_change > 0:
            # Purchase - increase inventory
            unit_cost = product.purchase_price or Decimal("0")
            total_cost = abs(quantity_change) * unit_cost
            
            if inventory_account:
                entries.append(LedgerEntry(
                    transaction_date=transaction_date,
                    description=f"Inventory purchase - {product.name} ({reference or 'Manual'})",
                    debit=total_cost,
                    credit=Decimal("0"),
                    account_id=inventory_account.id,
                    branch_id=branch_id,
                    business_id=business_id
                ))
        else:
            # Sale - record COGS
            sold_quantity = abs(quantity_change)
            cogs_amount = self.calculate_cogs_for_sale(
                product_id, sold_quantity, business_id, method
            )
            
            if cogs_account and inventory_account:
                # Debit COGS
                entries.append(LedgerEntry(
                    transaction_date=transaction_date,
                    description=f"COGS - {product.name} ({reference or 'Sale'})",
                    debit=cogs_amount,
                    credit=Decimal("0"),
                    account_id=cogs_account.id,
                    branch_id=branch_id,
                    business_id=business_id
                ))
                
                # Credit Inventory
                entries.append(LedgerEntry(
                    transaction_date=transaction_date,
                    description=f"Inventory reduction - {product.name} ({reference or 'Sale'})",
                    debit=Decimal("0"),
                    credit=cogs_amount,
                    account_id=inventory_account.id,
                    branch_id=branch_id,
                    business_id=business_id
                ))
        
        return entries


class InventoryMovementService:
    """Service for tracking inventory movements and cost layers"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_product_movements(self, product_id: int, business_id: int,
                              start_date: date = None, end_date: date = None) -> List[Dict]:
        """
        Get all inventory movements for a product within a date range.
        
        Returns list of movements with quantity, cost, and running balance.
        """
        from app.models import PurchaseBill, SalesInvoice
        
        movements = []
        running_quantity = Decimal("0")
        running_value = Decimal("0")
        
        # Get purchases
        purchases = self.db.query(PurchaseBillItem).join(
            PurchaseBillItem.purchase_bill
        ).options(
            joinedload(PurchaseBillItem.purchase_bill),
            joinedload(PurchaseBillItem.product)
        ).filter(
            PurchaseBillItem.product_id == product_id,
            PurchaseBill.purchase_bill.business_id == business_id
        )
        
        if start_date:
            purchases = purchases.filter(PurchaseBill.purchase_bill.bill_date >= start_date)
        if end_date:
            purchases = purchases.filter(PurchaseBill.purchase_bill.bill_date <= end_date)
        
        for item in purchases.all():
            net_qty = item.quantity - (item.returned_quantity or Decimal("0"))
            if net_qty > 0:
                cost = net_qty * item.price
                running_quantity += net_qty
                running_value += cost
                
                movements.append({
                    "date": item.purchase_bill.bill_date.isoformat(),
                    "type": "purchase",
                    "reference": item.purchase_bill.bill_number,
                    "quantity_in": float(net_qty),
                    "quantity_out": 0,
                    "unit_cost": float(item.price),
                    "total_cost": float(cost),
                    "balance_quantity": float(running_quantity),
                    "balance_value": float(running_value)
                })
        
        # Get sales
        sales = self.db.query(SalesInvoiceItem).join(
            SalesInvoiceItem.sales_invoice
        ).options(
            joinedload(SalesInvoiceItem.sales_invoice),
            joinedload(SalesInvoiceItem.product)
        ).filter(
            SalesInvoiceItem.product_id == product_id,
            SalesInvoice.sales_invoice.business_id == business_id
        )
        
        if start_date:
            sales = sales.filter(SalesInvoice.sales_invoice.invoice_date >= start_date)
        if end_date:
            sales = sales.filter(SalesInvoice.sales_invoice.invoice_date <= end_date)
        
        # Get average cost for COGS calculation
        valuation_service = InventoryValuationService(self.db)
        avg_cost = valuation_service.calculate_weighted_average_cost(product_id, business_id)
        
        for item in sales.all():
            net_qty = item.quantity - (item.returned_quantity or Decimal("0"))
            if net_qty > 0:
                cost = net_qty * avg_cost
                running_quantity -= net_qty
                running_value -= cost
                
                movements.append({
                    "date": item.sales_invoice.invoice_date.isoformat(),
                    "type": "sale",
                    "reference": item.sales_invoice.invoice_number,
                    "quantity_in": 0,
                    "quantity_out": float(net_qty),
                    "unit_cost": float(avg_cost),
                    "total_cost": float(cost),
                    "balance_quantity": float(running_quantity),
                    "balance_value": float(running_value)
                })
        
        # Sort by date
        movements.sort(key=lambda x: x["date"])
        
        return movements
