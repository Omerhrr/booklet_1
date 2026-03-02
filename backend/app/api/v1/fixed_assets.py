"""
Fixed Assets API Routes - Comprehensive Fixed Asset Management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.schemas import (
    FixedAssetCreate, FixedAssetUpdate, FixedAssetResponse, FixedAssetWithDetails,
    DepreciationRequest, DepreciationRecordResponse, BulkDepreciationRequest,
    DisposalRequest, WriteOffRequest
)
from app.services.fixed_assets_service import FixedAssetService

router = APIRouter(prefix="/fixed-assets", tags=["Fixed Assets"])


@router.get("")
async def list_fixed_assets(
    include_inactive: bool = False,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all fixed assets"""
    asset_service = FixedAssetService(db)
    assets = asset_service.get_by_business(
        current_user.business_id,
        branch_id=current_user.selected_branch.id if current_user.selected_branch else None,
        include_inactive=include_inactive,
        status=status
    )
    
    # Build response with additional details
    result = []
    for asset in assets:
        if category and asset.category != category:
            continue
        
        result.append({
            "id": asset.id,
            "name": asset.name,
            "asset_code": asset.asset_code,
            "description": asset.description,
            "category": asset.category,
            "location": asset.location,
            "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
            "purchase_cost": float(asset.purchase_cost) if asset.purchase_cost else 0.0,
            "salvage_value": float(asset.salvage_value) if asset.salvage_value else 0.0,
            "useful_life_years": asset.useful_life_years,
            "depreciation_method": asset.depreciation_method,
            "accumulated_depreciation": float(asset.accumulated_depreciation) if asset.accumulated_depreciation else 0.0,
            "book_value": float(asset.book_value) if asset.book_value else 0.0,
            "last_depreciation_date": asset.last_depreciation_date.isoformat() if asset.last_depreciation_date else None,
            "status": asset.status,
            "vendor_name": asset.vendor.name if asset.vendor else None,
            "annual_depreciation": float(asset.annual_depreciation),
            "remaining_life": asset.remaining_life,
            "branch_id": asset.branch_id,
            "business_id": asset.business_id,
            "is_active": asset.is_active,
            "created_at": asset.created_at.isoformat() if asset.created_at else None
        })
    
    return result


@router.post("", response_model=FixedAssetResponse, dependencies=[Depends(PermissionChecker(["accounting:create"]))])
async def create_fixed_asset(
    asset_data: FixedAssetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new fixed asset"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    asset = asset_service.create(asset_data, current_user.business_id, branch_id)
    db.commit()
    return asset


@router.get("/summary")
async def get_assets_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get summary of fixed assets"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    summary = asset_service.get_asset_summary(current_user.business_id, branch_id)
    
    # Convert Decimal to float for JSON
    return {
        "total_assets": summary["total_assets"],
        "total_cost": float(summary["total_cost"]),
        "total_accumulated_depreciation": float(summary["total_accumulated_depreciation"]),
        "total_book_value": float(summary["total_book_value"]),
        "by_category": {
            cat: {
                "count": data["count"],
                "total_cost": float(data["total_cost"]),
                "total_accumulated_dep": float(data["total_accumulated_dep"]),
                "total_book_value": float(data["total_book_value"])
            }
            for cat, data in summary["by_category"].items()
        },
        "by_status": summary["by_status"]
    }


@router.get("/categories")
async def get_asset_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get list of asset categories used"""
    from app.models import FixedAsset
    from sqlalchemy import distinct
    
    categories = db.query(distinct(FixedAsset.category)).filter(
        FixedAsset.business_id == current_user.business_id,
        FixedAsset.category.isnot(None)
    ).all()
    
    return [c[0] for c in categories if c[0]]


@router.get("/{asset_id}")
async def get_fixed_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get fixed asset by ID with details"""
    asset_service = FixedAssetService(db)
    asset = asset_service.get_by_id(asset_id, current_user.business_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    
    return {
        "id": asset.id,
        "name": asset.name,
        "asset_code": asset.asset_code,
        "description": asset.description,
        "category": asset.category,
        "location": asset.location,
        "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
        "purchase_cost": float(asset.purchase_cost) if asset.purchase_cost else 0.0,
        "vendor_id": asset.vendor_id,
        "vendor_name": asset.vendor.name if asset.vendor else None,
        "salvage_value": float(asset.salvage_value) if asset.salvage_value else 0.0,
        "useful_life_years": asset.useful_life_years,
        "depreciation_method": asset.depreciation_method,
        "depreciation_rate": float(asset.depreciation_rate) if asset.depreciation_rate else 0.0,
        "accumulated_depreciation": float(asset.accumulated_depreciation) if asset.accumulated_depreciation else 0.0,
        "book_value": float(asset.book_value) if asset.book_value else 0.0,
        "last_depreciation_date": asset.last_depreciation_date.isoformat() if asset.last_depreciation_date else None,
        "status": asset.status,
        "disposal_date": asset.disposal_date.isoformat() if asset.disposal_date else None,
        "disposal_amount": float(asset.disposal_amount) if asset.disposal_amount else None,
        "disposal_reason": asset.disposal_reason,
        "warranty_expiry": asset.warranty_expiry.isoformat() if asset.warranty_expiry else None,
        "insurance_policy": asset.insurance_policy,
        "insurance_expiry": asset.insurance_expiry.isoformat() if asset.insurance_expiry else None,
        "asset_account_id": asset.asset_account_id,
        "asset_account_name": asset.asset_account.name if asset.asset_account else None,
        "depreciation_account_id": asset.depreciation_account_id,
        "depreciation_account_name": asset.depreciation_account.name if asset.depreciation_account else None,
        "expense_account_id": asset.expense_account_id,
        "expense_account_name": asset.expense_account.name if asset.expense_account else None,
        "annual_depreciation": float(asset.annual_depreciation),
        "remaining_life": asset.remaining_life,
        "branch_id": asset.branch_id,
        "business_id": asset.business_id,
        "is_active": asset.is_active,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
    }


@router.put("/{asset_id}", response_model=FixedAssetResponse, dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def update_fixed_asset(
    asset_id: int,
    asset_data: FixedAssetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update fixed asset"""
    asset_service = FixedAssetService(db)
    asset = asset_service.update(asset_id, current_user.business_id, asset_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    db.commit()
    return asset


@router.delete("/{asset_id}", dependencies=[Depends(PermissionChecker(["accounting:delete"]))])
async def delete_fixed_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete fixed asset (soft delete if has depreciation records)"""
    asset_service = FixedAssetService(db)
    if not asset_service.delete(asset_id, current_user.business_id):
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    db.commit()
    return {"message": "Fixed asset deleted"}


# ==================== DEPRECIATION ====================

@router.post("/{asset_id}/depreciate", dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def record_depreciation(
    asset_id: int,
    depreciation_data: DepreciationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Record depreciation for an asset"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    asset = asset_service.record_depreciation(
        asset_id, 
        current_user.business_id, 
        depreciation_data,
        user_id=current_user.id,
        branch_id=branch_id
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found or not active")
    db.commit()
    return {
        "message": "Depreciation recorded",
        "asset_id": asset.id,
        "depreciation_amount": float(depreciation_data.amount),
        "accumulated_depreciation": float(asset.accumulated_depreciation),
        "book_value": float(asset.book_value),
        "status": asset.status
    }


@router.post("/bulk-depreciation", dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def bulk_depreciation(
    data: BulkDepreciationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Run depreciation for multiple or all active assets"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    results = asset_service.bulk_depreciation(
        current_user.business_id,
        data,
        user_id=current_user.id,
        branch_id=branch_id
    )
    db.commit()
    return {
        "message": f"Depreciation recorded for {len(results)} assets",
        "results": results
    }


@router.get("/{asset_id}/depreciation-history")
async def get_depreciation_history(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get depreciation history for an asset"""
    asset_service = FixedAssetService(db)
    records = asset_service.get_depreciation_history(asset_id, current_user.business_id)
    
    return [{
        "id": r.id,
        "depreciation_date": r.depreciation_date.isoformat() if r.depreciation_date else None,
        "period_start": r.period_start.isoformat() if r.period_start else None,
        "period_end": r.period_end.isoformat() if r.period_end else None,
        "amount": float(r.amount) if r.amount else 0.0,
        "method": r.method,
        "description": r.description,
        "journal_voucher_id": r.journal_voucher_id,
        "created_at": r.created_at.isoformat() if r.created_at else None
    } for r in records]


# ==================== DISPOSAL & WRITE-OFF ====================

@router.post("/{asset_id}/dispose", dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def dispose_asset(
    asset_id: int,
    disposal_data: DisposalRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Dispose of an asset"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    asset = asset_service.dispose(
        asset_id,
        current_user.business_id,
        disposal_data,
        user_id=current_user.id,
        branch_id=branch_id
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    db.commit()
    return {
        "message": "Asset disposed",
        "asset_id": asset.id,
        "disposal_date": asset.disposal_date.isoformat() if asset.disposal_date else None,
        "disposal_amount": float(asset.disposal_amount) if asset.disposal_amount else 0.0,
        "book_value_at_disposal": float(asset.book_value)
    }


@router.post("/{asset_id}/write-off", dependencies=[Depends(PermissionChecker(["accounting:edit"]))])
async def write_off_asset(
    asset_id: int,
    write_off_data: WriteOffRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Write off an asset"""
    asset_service = FixedAssetService(db)
    branch_id = current_user.selected_branch.id if current_user.selected_branch else None
    asset = asset_service.write_off(
        asset_id,
        current_user.business_id,
        write_off_data,
        user_id=current_user.id,
        branch_id=branch_id
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    db.commit()
    return {
        "message": "Asset written off",
        "asset_id": asset.id,
        "write_off_date": asset.disposal_date.isoformat() if asset.disposal_date else None,
        "book_value_written_off": float(asset.book_value)
    }
