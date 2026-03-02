"""
Inventory Service - Products, Categories, Stock Management
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from datetime import date
from app.models import Product, Category, StockAdjustment
from app.schemas import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate, StockAdjustmentCreate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, category_id: int, branch_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(
            Category.id == category_id,
            Category.branch_id == branch_id
        ).first()
    
    def get_by_branch(self, branch_id: int) -> List[Category]:
        return self.db.query(Category).filter(Category.branch_id == branch_id).all()
    
    def create(self, category_data: CategoryCreate, branch_id: int, business_id: int) -> Category:
        category = Category(
            name=category_data.name,
            description=category_data.description,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(category)
        self.db.flush()
        return category
    
    def update(self, category_id: int, branch_id: int, category_data: CategoryUpdate) -> Optional[Category]:
        category = self.get_by_id(category_id, branch_id)
        if not category:
            return None
        
        update_data = category_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        self.db.flush()
        return category
    
    def delete(self, category_id: int, branch_id: int) -> bool:
        category = self.get_by_id(category_id, branch_id)
        if not category:
            return False
        
        # Check for products
        has_products = self.db.query(Product).filter(Product.category_id == category_id).first()
        if has_products:
            return False
        
        self.db.delete(category)
        return True


class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, product_id: int, branch_id: int = None, business_id: int = None) -> Optional[Product]:
        query = self.db.query(Product).options(joinedload(Product.category))
        if branch_id:
            query = query.filter(Product.branch_id == branch_id)
        if business_id:
            query = query.filter(Product.business_id == business_id)
        return query.filter(Product.id == product_id).first()
    
    def get_by_sku(self, sku: str, branch_id: int, business_id: int = None) -> Optional[Product]:
        query = self.db.query(Product).filter(
            Product.sku == sku,
            Product.branch_id == branch_id
        )
        if business_id:
            query = query.filter(Product.business_id == business_id)
        return query.first()
    
    def is_sku_unique(self, sku: str, business_id: int, exclude_product_id: int = None) -> bool:
        """Check if SKU is unique within the business"""
        if not sku:
            return True  # Empty SKU is allowed
        query = self.db.query(Product).filter(
            Product.sku == sku,
            Product.business_id == business_id
        )
        if exclude_product_id:
            query = query.filter(Product.id != exclude_product_id)
        return query.first() is None
    
    def get_by_branch(self, branch_id: int, include_inactive: bool = False) -> List[Product]:
        query = self.db.query(Product).options(joinedload(Product.category)).filter(
            Product.branch_id == branch_id
        )
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        return query.all()
    
    def get_low_stock(self, branch_id: int) -> List[Product]:
        """Get products below reorder level"""
        return self.db.query(Product).filter(
            Product.branch_id == branch_id,
            Product.is_active == True,
            Product.stock_quantity <= Product.reorder_level
        ).all()
    
    def create(self, product_data: ProductCreate, branch_id: int, business_id: int) -> Product:
        # Validate SKU uniqueness if provided
        if product_data.sku and not self.is_sku_unique(product_data.sku, business_id):
            raise ValueError(f"Product with SKU '{product_data.sku}' already exists in this business")
        
        # Validate prices are not negative
        if product_data.purchase_price is not None and product_data.purchase_price < 0:
            raise ValueError("Purchase price cannot be negative")
        if product_data.sales_price is not None and product_data.sales_price < 0:
            raise ValueError("Sales price cannot be negative")
        
        # Validate stock quantities
        if product_data.opening_stock is not None and product_data.opening_stock < 0:
            raise ValueError("Opening stock cannot be negative")
        if product_data.reorder_level is not None and product_data.reorder_level < 0:
            raise ValueError("Reorder level cannot be negative")
        
        product = Product(
            name=product_data.name,
            sku=product_data.sku,
            description=product_data.description,
            unit=product_data.unit,
            purchase_price=product_data.purchase_price or Decimal("0"),
            sales_price=product_data.sales_price or Decimal("0"),
            opening_stock=product_data.opening_stock or Decimal("0"),
            stock_quantity=product_data.opening_stock or Decimal("0"),
            reorder_level=product_data.reorder_level or Decimal("0"),
            category_id=product_data.category_id,
            branch_id=branch_id,
            business_id=business_id
        )
        self.db.add(product)
        self.db.flush()
        return product
    
    def update(self, product_id: int, branch_id: int, product_data: ProductUpdate, business_id: int = None) -> Optional[Product]:
        product = self.get_by_id(product_id, branch_id, business_id)
        if not product:
            return None
        
        update_data = product_data.model_dump(exclude_unset=True)
        
        # Validate SKU uniqueness if being updated
        if 'sku' in update_data and update_data['sku'] and business_id:
            if not self.is_sku_unique(update_data['sku'], business_id, exclude_product_id=product_id):
                raise ValueError(f"Product with SKU '{update_data['sku']}' already exists in this business")
        
        # Validate prices are not negative
        if 'purchase_price' in update_data and update_data['purchase_price'] is not None and update_data['purchase_price'] < 0:
            raise ValueError("Purchase price cannot be negative")
        if 'sales_price' in update_data and update_data['sales_price'] is not None and update_data['sales_price'] < 0:
            raise ValueError("Sales price cannot be negative")
        
        # Validate stock quantities
        if 'reorder_level' in update_data and update_data['reorder_level'] is not None and update_data['reorder_level'] < 0:
            raise ValueError("Reorder level cannot be negative")
        
        for key, value in update_data.items():
            setattr(product, key, value)
        
        self.db.flush()
        return product
    
    def adjust_stock(self, product_id: int, adjustment_data: StockAdjustmentCreate, user_id: int) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        # Update stock quantity
        new_quantity = product.stock_quantity + adjustment_data.quantity_change
        if new_quantity < 0:
            raise ValueError("Stock cannot be negative")
        
        product.stock_quantity = new_quantity
        
        # Create adjustment record
        adjustment = StockAdjustment(
            product_id=product_id,
            quantity_change=adjustment_data.quantity_change,
            reason=adjustment_data.reason,
            user_id=user_id
        )
        self.db.add(adjustment)
        self.db.flush()
        
        return product
    
    def delete(self, product_id: int, branch_id: int) -> bool:
        product = self.get_by_id(product_id, branch_id)
        if not product:
            return False
        
        # Check for transaction history
        has_transactions = self.db.query(StockAdjustment).filter(
            StockAdjustment.product_id == product_id
        ).first()
        
        if has_transactions:
            product.is_active = False
        else:
            self.db.delete(product)
        
        return True
    
    def get_adjustments(self, branch_id: int, limit: int = 50) -> List[dict]:
        """Get stock adjustments for a branch"""
        from sqlalchemy import desc
        adjustments = self.db.query(StockAdjustment).join(Product).filter(
            Product.branch_id == branch_id
        ).order_by(desc(StockAdjustment.created_at)).limit(limit).all()
        
        result = []
        for adj in adjustments:
            result.append({
                'id': adj.id,
                'product_id': adj.product_id,
                'product_name': adj.product.name if adj.product else 'Unknown',
                'product_sku': adj.product.sku if adj.product else None,
                'quantity_change': float(adj.quantity_change),
                'reason': adj.reason,
                'user_name': adj.user.full_name or adj.user.username if adj.user else 'System',
                'created_at': adj.created_at.strftime('%Y-%m-%d %H:%M') if adj.created_at else None
            })
        return result
