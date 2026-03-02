"""
Inventory API Routes - Products and Categories
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, StockAdjustmentCreate,
    CategoryCreate, CategoryUpdate, CategoryResponse
)
from app.services.inventory_service import ProductService, CategoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ==================== CATEGORIES ====================

@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all categories for current branch"""
    category_service = CategoryService(db)
    categories = category_service.get_by_branch(current_user.selected_branch.id)
    
    # Add product count to each category
    result = []
    for cat in categories:
        cat_dict = {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'branch_id': cat.branch_id,
            'business_id': cat.business_id,
            'created_at': cat.created_at.isoformat() if cat.created_at else None,
            'product_count': len(cat.products) if hasattr(cat, 'products') and cat.products else 0
        }
        result.append(cat_dict)
    return result


@router.post("/categories", response_model=CategoryResponse, dependencies=[Depends(PermissionChecker(["inventory:create"]))])
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new category"""
    category_service = CategoryService(db)
    category = category_service.create(
        category_data,
        current_user.selected_branch.id,
        current_user.business_id
    )
    db.commit()
    return category


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get category by ID"""
    category_service = CategoryService(db)
    category = category_service.get_by_id(category_id, current_user.selected_branch.id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse, dependencies=[Depends(PermissionChecker(["inventory:edit"]))])
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update category"""
    category_service = CategoryService(db)
    category = category_service.update(category_id, current_user.selected_branch.id, category_data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.commit()
    return category


@router.delete("/categories/{category_id}", dependencies=[Depends(PermissionChecker(["inventory:delete"]))])
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete category"""
    category_service = CategoryService(db)
    if not category_service.delete(category_id, current_user.selected_branch.id):
        raise HTTPException(status_code=400, detail="Cannot delete category with products")
    db.commit()
    return {"message": "Category deleted successfully"}


# ==================== PRODUCTS ====================

@router.get("/products")
async def list_products(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all products for current branch"""
    product_service = ProductService(db)
    products = product_service.get_by_branch(current_user.selected_branch.id, include_inactive)
    
    # Convert to dict with category info
    result = []
    for p in products:
        p_dict = {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'description': p.description,
            'unit': p.unit,
            'purchase_price': float(p.purchase_price),
            'sales_price': float(p.sales_price),
            'opening_stock': float(p.opening_stock),
            'stock_quantity': float(p.stock_quantity),
            'reorder_level': float(p.reorder_level),
            'is_active': p.is_active,
            'category_id': p.category_id,
            'branch_id': p.branch_id,
            'business_id': p.business_id,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'category': {'id': p.category.id, 'name': p.category.name} if p.category else None
        }
        result.append(p_dict)
    return result


@router.get("/products/low-stock")
async def list_low_stock_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List products below reorder level"""
    product_service = ProductService(db)
    products = product_service.get_low_stock(current_user.selected_branch.id)
    
    result = []
    for p in products:
        p_dict = {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'description': p.description,
            'unit': p.unit,
            'purchase_price': float(p.purchase_price),
            'sales_price': float(p.sales_price),
            'opening_stock': float(p.opening_stock),
            'stock_quantity': float(p.stock_quantity),
            'reorder_level': float(p.reorder_level),
            'is_active': p.is_active,
            'category_id': p.category_id,
            'branch_id': p.branch_id,
            'business_id': p.business_id,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'category': {'id': p.category.id, 'name': p.category.name} if p.category else None
        }
        result.append(p_dict)
    return result


@router.post("/products", response_model=ProductResponse, dependencies=[Depends(PermissionChecker(["inventory:create"]))])
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new product"""
    product_service = ProductService(db)
    product = product_service.create(
        product_data,
        current_user.selected_branch.id,
        current_user.business_id
    )
    db.commit()
    return product


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get product by ID"""
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id, current_user.selected_branch.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'description': product.description,
        'unit': product.unit,
        'purchase_price': float(product.purchase_price),
        'sales_price': float(product.sales_price),
        'opening_stock': float(product.opening_stock),
        'stock_quantity': float(product.stock_quantity),
        'reorder_level': float(product.reorder_level),
        'is_active': product.is_active,
        'category_id': product.category_id,
        'branch_id': product.branch_id,
        'business_id': product.business_id,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'category': {'id': product.category.id, 'name': product.category.name} if product.category else None
    }


@router.post("/products/{product_id}/toggle-status", dependencies=[Depends(PermissionChecker(["inventory:edit"]))])
async def toggle_product_status(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle product active status"""
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id, current_user.selected_branch.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = not product.is_active
    db.commit()
    return {"message": f"Product {'activated' if product.is_active else 'deactivated'}", "is_active": product.is_active}


@router.put("/products/{product_id}", response_model=ProductResponse, dependencies=[Depends(PermissionChecker(["inventory:edit"]))])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update product"""
    product_service = ProductService(db)
    product = product_service.update(product_id, current_user.selected_branch.id, product_data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.commit()
    return product


@router.delete("/products/{product_id}", dependencies=[Depends(PermissionChecker(["inventory:delete"]))])
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete product"""
    product_service = ProductService(db)
    if not product_service.delete(product_id, current_user.selected_branch.id):
        raise HTTPException(status_code=404, detail="Product not found")
    db.commit()
    return {"message": "Product deleted successfully"}


@router.post("/products/{product_id}/adjust-stock", response_model=ProductResponse, dependencies=[Depends(PermissionChecker(["inventory:adjust_stock"]))])
async def adjust_product_stock(
    product_id: int,
    adjustment_data: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Adjust product stock"""
    product_service = ProductService(db)
    try:
        product = product_service.adjust_stock(product_id, adjustment_data, current_user.id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        db.commit()
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stock-adjustments")
async def list_stock_adjustments(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List stock adjustments for current branch"""
    product_service = ProductService(db)
    return product_service.get_adjustments(current_user.selected_branch.id, limit)


# ==================== INVENTORY VALUATION ====================

@router.get("/valuation")
async def get_inventory_valuation(
    method: str = "fifo",
    category_id: int = None,
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get inventory valuation report using specified method.
    
    Methods:
    - fifo: First-In, First-Out
    - weighted_average: Weighted Average Cost
    """
    from app.services.inventory_valuation_service import InventoryValuationService
    
    if method not in ['fifo', 'weighted_average']:
        raise HTTPException(status_code=400, detail="Method must be 'fifo' or 'weighted_average'")
    
    valuation_service = InventoryValuationService(db)
    report = valuation_service.get_inventory_valuation_report(
        business_id=current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        method=method,
        category_id=category_id,
        as_of_date=as_of_date
    )
    
    return report


@router.get("/products/{product_id}/valuation")
async def get_product_valuation(
    product_id: int,
    method: str = "fifo",
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get inventory valuation for a specific product"""
    from app.services.inventory_valuation_service import InventoryValuationService
    
    if method not in ['fifo', 'weighted_average']:
        raise HTTPException(status_code=400, detail="Method must be 'fifo' or 'weighted_average'")
    
    valuation_service = InventoryValuationService(db)
    value_info = valuation_service.calculate_inventory_value(
        product_id=product_id,
        business_id=current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        method=method,
        as_of_date=as_of_date
    )
    
    if "error" in value_info:
        raise HTTPException(status_code=404, detail=value_info["error"])
    
    return value_info


@router.get("/products/{product_id}/movements")
async def get_product_movements(
    product_id: int,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get inventory movement history for a product"""
    from app.services.inventory_valuation_service import InventoryMovementService
    
    movement_service = InventoryMovementService(db)
    movements = movement_service.get_product_movements(
        product_id=product_id,
        business_id=current_user.business_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return movements


@router.get("/valuation-summary")
async def get_valuation_summary(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a summary of inventory valuation by category"""
    from app.services.inventory_valuation_service import InventoryValuationService
    from app.models import Category, Product
    
    valuation_service = InventoryValuationService(db)
    
    # Get all categories with products
    categories = db.query(Category).filter(
        Category.business_id == current_user.business_id
    ).all()
    
    summary = []
    total_value_fifo = Decimal("0")
    total_value_avg = Decimal("0")
    
    for category in categories:
        products = db.query(Product).filter(
            Product.category_id == category.id,
            Product.is_active == True,
            Product.stock_quantity > 0
        ).all()
        
        category_value_fifo = Decimal("0")
        category_value_avg = Decimal("0")
        product_count = 0
        
        for product in products:
            fifo_value = valuation_service.calculate_inventory_value(
                product.id,
                current_user.business_id,
                current_user.selected_branch.id if current_user.selected_branch else None,
                'fifo',
                as_of_date
            )
            avg_value = valuation_service.calculate_inventory_value(
                product.id,
                current_user.business_id,
                current_user.selected_branch.id if current_user.selected_branch else None,
                'weighted_average',
                as_of_date
            )
            
            if "error" not in fifo_value:
                category_value_fifo += Decimal(str(fifo_value.get("total_value", 0)))
            if "error" not in avg_value:
                category_value_avg += Decimal(str(avg_value.get("total_value", 0)))
            product_count += 1
        
        if product_count > 0:
            summary.append({
                "category_id": category.id,
                "category_name": category.name,
                "product_count": product_count,
                "value_fifo": float(category_value_fifo),
                "value_weighted_average": float(category_value_avg)
            })
            
            total_value_fifo += category_value_fifo
            total_value_avg += category_value_avg
    
    # Products without category
    uncategorized_products = db.query(Product).filter(
        Product.business_id == current_user.business_id,
        Product.category_id == None,
        Product.is_active == True,
        Product.stock_quantity > 0
    ).all()
    
    uncategorized_value_fifo = Decimal("0")
    uncategorized_value_avg = Decimal("0")
    
    for product in uncategorized_products:
        fifo_value = valuation_service.calculate_inventory_value(
            product.id,
            current_user.business_id,
            current_user.selected_branch.id if current_user.selected_branch else None,
            'fifo',
            as_of_date
        )
        avg_value = valuation_service.calculate_inventory_value(
            product.id,
            current_user.business_id,
            current_user.selected_branch.id if current_user.selected_branch else None,
            'weighted_average',
            as_of_date
        )
        
        if "error" not in fifo_value:
            uncategorized_value_fifo += Decimal(str(fifo_value.get("total_value", 0)))
        if "error" not in avg_value:
            uncategorized_value_avg += Decimal(str(avg_value.get("total_value", 0)))
    
    if uncategorized_products:
        summary.append({
            "category_id": None,
            "category_name": "Uncategorized",
            "product_count": len(uncategorized_products),
            "value_fifo": float(uncategorized_value_fifo),
            "value_weighted_average": float(uncategorized_value_avg)
        })
        
        total_value_fifo += uncategorized_value_fifo
        total_value_avg += uncategorized_value_avg
    
    return {
        "as_of_date": as_of_date.isoformat() if as_of_date else date.today().isoformat(),
        "by_category": summary,
        "totals": {
            "total_value_fifo": float(total_value_fifo),
            "total_value_weighted_average": float(total_value_avg)
        }
    }
