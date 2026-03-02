"""
Fixed Assets Service - Comprehensive Fixed Asset Management
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from decimal import Decimal
from datetime import date
from app.models import (
    FixedAsset, DepreciationRecord, AssetStatus,
    JournalVoucher, LedgerEntry, Account, Vendor
)
from app.schemas import (
    FixedAssetCreate, FixedAssetUpdate,
    DepreciationRequest, BulkDepreciationRequest,
    DisposalRequest, WriteOffRequest
)


class FixedAssetService:
    """Service for managing fixed assets"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, asset_id: int, business_id: int) -> Optional[FixedAsset]:
        return self.db.query(FixedAsset).options(
            joinedload(FixedAsset.vendor),
            joinedload(FixedAsset.asset_account),
            joinedload(FixedAsset.depreciation_account),
            joinedload(FixedAsset.expense_account),
            joinedload(FixedAsset.branch)
        ).filter(
            FixedAsset.id == asset_id,
            FixedAsset.business_id == business_id
        ).first()
    
    def get_by_business(self, business_id: int, branch_id: int = None, 
                       include_inactive: bool = False, status: str = None) -> List[FixedAsset]:
        query = self.db.query(FixedAsset).options(
            joinedload(FixedAsset.vendor),
            joinedload(FixedAsset.asset_account)
        ).filter(FixedAsset.business_id == business_id)
        
        if branch_id:
            query = query.filter(FixedAsset.branch_id == branch_id)
        
        if not include_inactive:
            query = query.filter(FixedAsset.is_active == True)
        
        if status:
            query = query.filter(FixedAsset.status == status)
        
        return query.order_by(FixedAsset.created_at.desc()).all()
    
    def get_next_asset_code(self, business_id: int) -> str:
        """Generate next asset code"""
        last_asset = self.db.query(FixedAsset).filter(
            FixedAsset.business_id == business_id,
            FixedAsset.asset_code.like('FA-%')
        ).order_by(FixedAsset.id.desc()).first()
        
        if last_asset and last_asset.asset_code:
            try:
                num = int(last_asset.asset_code.replace('FA-', ''))
                return f'FA-{num + 1:05d}'
            except ValueError:
                pass
        
        return 'FA-00001'
    
    def create(self, asset_data: FixedAssetCreate, business_id: int, branch_id: int = None) -> FixedAsset:
        """Create a new fixed asset"""
        # Generate asset code if not provided
        asset_code = asset_data.asset_code
        if not asset_code:
            asset_code = self.get_next_asset_code(business_id)
        
        asset = FixedAsset(
            name=asset_data.name,
            asset_code=asset_code,
            description=asset_data.description,
            category=asset_data.category,
            location=asset_data.location,
            purchase_date=asset_data.purchase_date,
            purchase_cost=asset_data.purchase_cost,
            vendor_id=asset_data.vendor_id,
            salvage_value=asset_data.salvage_value,
            useful_life_years=asset_data.useful_life_years,
            depreciation_method=asset_data.depreciation_method,
            depreciation_rate=asset_data.depreciation_rate,
            warranty_expiry=asset_data.warranty_expiry,
            insurance_policy=asset_data.insurance_policy,
            insurance_expiry=asset_data.insurance_expiry,
            accumulated_depreciation=Decimal("0"),
            book_value=asset_data.purchase_cost,
            status=AssetStatus.ACTIVE.value,
            asset_account_id=asset_data.asset_account_id,
            depreciation_account_id=asset_data.depreciation_account_id,
            expense_account_id=asset_data.expense_account_id,
            branch_id=asset_data.branch_id or branch_id,
            business_id=business_id
        )
        self.db.add(asset)
        self.db.flush()
        return asset
    
    def update(self, asset_id: int, business_id: int, asset_data: FixedAssetUpdate) -> Optional[FixedAsset]:
        """Update fixed asset"""
        asset = self.get_by_id(asset_id, business_id)
        if not asset:
            return None
        
        update_data = asset_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)
        
        self.db.flush()
        return asset
    
    def calculate_depreciation(self, asset: FixedAsset) -> Decimal:
        """Calculate depreciation amount based on method"""
        if asset.status != AssetStatus.ACTIVE.value:
            return Decimal("0")
        
        if asset.depreciation_method == "straight_line":
            depreciable_amount = asset.purchase_cost - asset.salvage_value
            remaining_value = depreciable_amount - asset.accumulated_depreciation
            if remaining_value <= 0:
                return Decimal("0")
            annual_dep = depreciable_amount / asset.useful_life_years if asset.useful_life_years > 0 else Decimal("0")
            return min(annual_dep, remaining_value)
        
        elif asset.depreciation_method == "declining_balance":
            rate = (asset.depreciation_rate or Decimal("20")) / 100
            dep_amount = asset.book_value * rate
            # Don't depreciate below salvage value
            if asset.book_value - dep_amount < asset.salvage_value:
                dep_amount = asset.book_value - asset.salvage_value
            return max(dep_amount, Decimal("0"))
        
        return Decimal("0")
    
    def record_depreciation(self, asset_id: int, business_id: int, 
                          depreciation_data: DepreciationRequest, 
                          user_id: int = None, branch_id: int = None) -> Optional[FixedAsset]:
        """Record depreciation for an asset"""
        asset = self.get_by_id(asset_id, business_id)
        if not asset or asset.status != AssetStatus.ACTIVE.value:
            return None
        
        amount = depreciation_data.amount
        depreciation_date = depreciation_data.depreciation_date or date.today()
        
        # Check if depreciating would go below salvage value
        if asset.accumulated_depreciation + amount > (asset.purchase_cost - asset.salvage_value):
            amount = (asset.purchase_cost - asset.salvage_value) - asset.accumulated_depreciation
        
        if amount <= 0:
            return asset
        
        # Create depreciation record
        dep_record = DepreciationRecord(
            asset_id=asset.id,
            depreciation_date=depreciation_date,
            period_start=depreciation_date,
            period_end=depreciation_date,
            amount=amount,
            method=asset.depreciation_method,
            description=depreciation_data.description or f"Depreciation for {asset.name}",
            branch_id=branch_id or asset.branch_id,
            business_id=business_id
        )
        self.db.add(dep_record)
        
        # Update asset
        asset.accumulated_depreciation += amount
        asset.book_value = asset.purchase_cost - asset.accumulated_depreciation
        asset.last_depreciation_date = depreciation_date
        
        # Check if fully depreciated
        if asset.book_value <= asset.salvage_value:
            asset.status = AssetStatus.FULLY_DEPRECIATED.value
        
        # Create journal entries if accounts are set
        if asset.expense_account_id and asset.depreciation_account_id:
            self._create_depreciation_journal(asset, amount, depreciation_date, branch_id, user_id)
        
        self.db.flush()
        return asset
    
    def _create_depreciation_journal(self, asset: FixedAsset, amount: Decimal, 
                                    depreciation_date: date, branch_id: int, user_id: int):
        """Create journal entry for depreciation"""
        # Create journal voucher
        jv_number = self._get_next_jv_number(asset.business_id)
        jv = JournalVoucher(
            voucher_number=jv_number,
            transaction_date=depreciation_date,
            description=f"Depreciation - {asset.name}",
            reference=f"DEP-{asset.asset_code}",
            is_posted=True,
            branch_id=branch_id or asset.branch_id,
            business_id=asset.business_id,
            created_by=user_id
        )
        self.db.add(jv)
        self.db.flush()
        
        # Debit depreciation expense
        expense_entry = LedgerEntry(
            transaction_date=depreciation_date,
            description=f"Depreciation expense - {asset.name}",
            debit=amount,
            credit=Decimal("0"),
            account_id=asset.expense_account_id,
            journal_voucher_id=jv.id,
            branch_id=branch_id or asset.branch_id
        )
        self.db.add(expense_entry)
        
        # Credit accumulated depreciation
        acc_dep_entry = LedgerEntry(
            transaction_date=depreciation_date,
            description=f"Accumulated depreciation - {asset.name}",
            debit=Decimal("0"),
            credit=amount,
            account_id=asset.depreciation_account_id,
            journal_voucher_id=jv.id,
            branch_id=branch_id or asset.branch_id
        )
        self.db.add(acc_dep_entry)
    
    def _get_next_jv_number(self, business_id: int) -> str:
        last_jv = self.db.query(JournalVoucher).filter(
            JournalVoucher.business_id == business_id
        ).order_by(JournalVoucher.id.desc()).first()
        
        if last_jv:
            try:
                num = int(last_jv.voucher_number.replace("JV-", ""))
                return f"JV-{num + 1:05d}"
            except ValueError:
                pass
        return "JV-00001"
    
    def bulk_depreciation(self, business_id: int, data: BulkDepreciationRequest,
                         user_id: int = None, branch_id: int = None) -> List[Dict]:
        """Run depreciation for multiple assets"""
        results = []
        
        # Get assets to depreciate
        query = self.db.query(FixedAsset).filter(
            FixedAsset.business_id == business_id,
            FixedAsset.status == AssetStatus.ACTIVE.value,
            FixedAsset.is_active == True
        )
        
        if data.asset_ids:
            query = query.filter(FixedAsset.id.in_(data.asset_ids))
        
        assets = query.all()
        
        for asset in assets:
            calculated_amount = self.calculate_depreciation(asset)
            if calculated_amount > 0:
                dep_data = DepreciationRequest(
                    amount=calculated_amount,
                    depreciation_date=data.depreciation_date,
                    description=data.description or f"Bulk depreciation - {asset.name}"
                )
                self.record_depreciation(
                    asset.id, business_id, dep_data, user_id, branch_id or asset.branch_id
                )
                results.append({
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "asset_code": asset.asset_code,
                    "depreciation_amount": float(calculated_amount),
                    "book_value": float(asset.book_value)
                })
        
        self.db.flush()
        return results
    
    def dispose(self, asset_id: int, business_id: int, disposal_data: DisposalRequest,
               user_id: int = None, branch_id: int = None) -> Optional[FixedAsset]:
        """Dispose of an asset"""
        asset = self.get_by_id(asset_id, business_id)
        if not asset:
            return None
        
        asset.status = AssetStatus.DISPOSED.value
        asset.disposal_date = disposal_data.disposal_date
        asset.disposal_amount = disposal_data.disposal_amount
        asset.disposal_reason = disposal_data.disposal_reason
        asset.is_active = False
        
        # Create journal entries for disposal if accounts are set
        if asset.asset_account_id and asset.disposal_amount:
            self._create_disposal_journal(asset, branch_id, user_id)
        
        self.db.flush()
        return asset
    
    def _create_disposal_journal(self, asset: FixedAsset, branch_id: int, user_id: int):
        """Create journal entries for asset disposal"""
        jv_number = self._get_next_jv_number(asset.business_id)
        jv = JournalVoucher(
            voucher_number=jv_number,
            transaction_date=asset.disposal_date,
            description=f"Asset Disposal - {asset.name}",
            reference=f"DISP-{asset.asset_code}",
            is_posted=True,
            branch_id=branch_id or asset.branch_id,
            business_id=asset.business_id,
            created_by=user_id
        )
        self.db.add(jv)
        self.db.flush()
        
        # Credit the asset account (remove asset)
        LedgerEntry(
            transaction_date=asset.disposal_date,
            description=f"Asset disposed - {asset.name}",
            debit=Decimal("0"),
            credit=asset.purchase_cost,
            account_id=asset.asset_account_id,
            journal_voucher_id=jv.id,
            branch_id=branch_id or asset.branch_id
        )
        
        # Debit accumulated depreciation
        if asset.accumulated_depreciation > 0 and asset.depreciation_account_id:
            LedgerEntry(
                transaction_date=asset.disposal_date,
                description=f"Remove accumulated depreciation - {asset.name}",
                debit=asset.accumulated_depreciation,
                credit=Decimal("0"),
                account_id=asset.depreciation_account_id,
                journal_voucher_id=jv.id,
                branch_id=branch_id or asset.branch_id
            )
        
        # Debit cash/receivable for disposal amount
        if asset.disposal_amount > 0:
            # Find cash account or use asset account
            LedgerEntry(
                transaction_date=asset.disposal_date,
                description=f"Disposal proceeds - {asset.name}",
                debit=asset.disposal_amount,
                credit=Decimal("0"),
                account_id=asset.asset_account_id,  # Should be cash/bank account
                journal_voucher_id=jv.id,
                branch_id=branch_id or asset.branch_id
            )
    
    def write_off(self, asset_id: int, business_id: int, write_off_data: WriteOffRequest,
                 user_id: int = None, branch_id: int = None) -> Optional[FixedAsset]:
        """Write off an asset"""
        asset = self.get_by_id(asset_id, business_id)
        if not asset:
            return None
        
        asset.status = AssetStatus.WRITTEN_OFF.value
        asset.disposal_date = write_off_data.write_off_date
        asset.disposal_amount = Decimal("0")
        asset.disposal_reason = write_off_data.reason or "Written off"
        asset.is_active = False
        
        # Create journal entries for write-off
        if asset.asset_account_id:
            self._create_write_off_journal(asset, branch_id, user_id)
        
        self.db.flush()
        return asset
    
    def _create_write_off_journal(self, asset: FixedAsset, branch_id: int, user_id: int):
        """Create journal entries for asset write-off"""
        jv_number = self._get_next_jv_number(asset.business_id)
        jv = JournalVoucher(
            voucher_number=jv_number,
            transaction_date=asset.disposal_date,
            description=f"Asset Write-off - {asset.name}",
            reference=f"WO-{asset.asset_code}",
            is_posted=True,
            branch_id=branch_id or asset.branch_id,
            business_id=asset.business_id,
            created_by=user_id
        )
        self.db.add(jv)
        self.db.flush()
        
        # Credit the asset account
        LedgerEntry(
            transaction_date=asset.disposal_date,
            description=f"Asset written off - {asset.name}",
            debit=Decimal("0"),
            credit=asset.purchase_cost,
            account_id=asset.asset_account_id,
            journal_voucher_id=jv.id,
            branch_id=branch_id or asset.branch_id
        )
        
        # Debit accumulated depreciation
        if asset.accumulated_depreciation > 0 and asset.depreciation_account_id:
            LedgerEntry(
                transaction_date=asset.disposal_date,
                description=f"Remove accumulated depreciation - {asset.name}",
                debit=asset.accumulated_depreciation,
                credit=Decimal("0"),
                account_id=asset.depreciation_account_id,
                journal_voucher_id=jv.id,
                branch_id=branch_id or asset.branch_id
            )
        
        # Debit loss on write-off (book value)
        if asset.book_value > 0 and asset.expense_account_id:
            LedgerEntry(
                transaction_date=asset.disposal_date,
                description=f"Loss on asset write-off - {asset.name}",
                debit=asset.book_value,
                credit=Decimal("0"),
                account_id=asset.expense_account_id,
                journal_voucher_id=jv.id,
                branch_id=branch_id or asset.branch_id
            )
    
    def get_depreciation_history(self, asset_id: int, business_id: int) -> List[DepreciationRecord]:
        """Get depreciation history for an asset"""
        return self.db.query(DepreciationRecord).filter(
            DepreciationRecord.asset_id == asset_id,
            DepreciationRecord.business_id == business_id
        ).order_by(DepreciationRecord.depreciation_date.desc()).all()
    
    def get_asset_summary(self, business_id: int, branch_id: int = None) -> Dict:
        """Get summary of fixed assets"""
        query = self.db.query(FixedAsset).filter(
            FixedAsset.business_id == business_id,
            FixedAsset.is_active == True
        )
        
        if branch_id:
            query = query.filter(FixedAsset.branch_id == branch_id)
        
        assets = query.all()
        
        total_cost = sum(a.purchase_cost for a in assets)
        total_accumulated_dep = sum(a.accumulated_depreciation for a in assets)
        total_book_value = sum(a.book_value for a in assets)
        
        by_category = {}
        for asset in assets:
            cat = asset.category or "Uncategorized"
            if cat not in by_category:
                by_category[cat] = {
                    "count": 0,
                    "total_cost": Decimal("0"),
                    "total_accumulated_dep": Decimal("0"),
                    "total_book_value": Decimal("0")
                }
            by_category[cat]["count"] += 1
            by_category[cat]["total_cost"] += asset.purchase_cost
            by_category[cat]["total_accumulated_dep"] += asset.accumulated_depreciation
            by_category[cat]["total_book_value"] += asset.book_value
        
        return {
            "total_assets": len(assets),
            "total_cost": total_cost,
            "total_accumulated_depreciation": total_accumulated_dep,
            "total_book_value": total_book_value,
            "by_category": by_category,
            "by_status": {
                status: len([a for a in assets if a.status == status])
                for status in [s.value for s in AssetStatus]
            }
        }
    
    def delete(self, asset_id: int, business_id: int) -> bool:
        """Delete an asset (only if no depreciation records)"""
        asset = self.get_by_id(asset_id, business_id)
        if not asset:
            return False
        
        # Check for depreciation records
        has_records = self.db.query(DepreciationRecord).filter(
            DepreciationRecord.asset_id == asset_id
        ).first()
        
        if has_records:
            # Soft delete
            asset.is_active = False
        else:
            self.db.delete(asset)
        
        return True
