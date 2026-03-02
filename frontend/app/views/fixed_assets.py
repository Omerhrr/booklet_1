"""
Fixed Assets Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import api_request, login_required, permission_required
from datetime import date

fixed_assets_bp = Blueprint('fixed_assets', __name__, url_prefix='/fixed-assets')


@fixed_assets_bp.route('')
@login_required
@permission_required('accounting:view')
def fixed_assets_list():
    """List all fixed assets"""
    # Get filter parameters
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    
    params = {}
    if status:
        params['status'] = status
    if category:
        params['category'] = category
    
    assets, status_code = api_request('GET', '/fixed-assets', params=params if params else None)
    
    if status_code != 200:
        assets = []
    
    # Get summary
    summary, _ = api_request('GET', '/fixed-assets/summary')
    
    # Get categories
    categories_data, _ = api_request('GET', '/fixed-assets/categories')
    categories = categories_data if categories_data else []
    
    return render_template('fixed_assets/list.html', 
                          title='Fixed Assets',
                          assets=assets,
                          summary=summary or {},
                          categories=categories)


@fixed_assets_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('accounting:create')
def create_fixed_asset():
    """Create new fixed asset"""
    if request.method == 'GET':
        # Get vendors
        vendors, _ = api_request('GET', '/crm/vendors')
        
        # Get accounts
        accounts, _ = api_request('GET', '/accounting/accounts')
        
        # Filter accounts by type
        asset_accounts = [a for a in (accounts or []) if a.get('type') == 'Asset']
        expense_accounts = [a for a in (accounts or []) if a.get('type') == 'Expense']
        
        return render_template('fixed_assets/form.html', 
                              title='New Fixed Asset',
                              vendors=vendors or [],
                              asset_accounts=asset_accounts,
                              expense_accounts=expense_accounts,
                              today=date.today().isoformat())
    
    # POST - Create fixed asset
    data = {
        'name': request.form.get('name'),
        'asset_code': request.form.get('asset_code') or None,
        'description': request.form.get('description') or None,
        'category': request.form.get('category') or None,
        'location': request.form.get('location') or None,
        'purchase_date': request.form.get('purchase_date'),
        'purchase_cost': float(request.form.get('purchase_cost', 0)),
        'salvage_value': float(request.form.get('salvage_value', 0)),
        'useful_life_years': int(request.form.get('useful_life_years', 5)),
        'depreciation_method': request.form.get('depreciation_method', 'straight_line'),
        'depreciation_rate': float(request.form.get('depreciation_rate', 0)) if request.form.get('depreciation_rate') else None,
        'vendor_id': int(request.form.get('vendor_id')) if request.form.get('vendor_id') else None,
        'asset_account_id': int(request.form.get('asset_account_id')) if request.form.get('asset_account_id') else None,
        'depreciation_account_id': int(request.form.get('depreciation_account_id')) if request.form.get('depreciation_account_id') else None,
        'expense_account_id': int(request.form.get('expense_account_id')) if request.form.get('expense_account_id') else None,
        'warranty_expiry': request.form.get('warranty_expiry') or None,
        'insurance_policy': request.form.get('insurance_policy') or None,
        'insurance_expiry': request.form.get('insurance_expiry') or None,
    }
    
    response, status_code = api_request('POST', '/fixed-assets', data=data)
    
    if status_code == 200:
        flash('Fixed asset created successfully!', 'success')
        return redirect(url_for('fixed_assets.fixed_asset_detail', asset_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create fixed asset') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('fixed_assets.create_fixed_asset'))


@fixed_assets_bp.route('/<int:asset_id>')
@login_required
@permission_required('accounting:view')
def fixed_asset_detail(asset_id):
    """View fixed asset details"""
    asset, status_code = api_request('GET', f'/fixed-assets/{asset_id}')
    
    if status_code != 200:
        flash('Fixed asset not found', 'error')
        return redirect(url_for('fixed_assets.fixed_assets_list'))
    
    # Get depreciation history
    depreciation_history, _ = api_request('GET', f'/fixed-assets/{asset_id}/depreciation-history')
    
    return render_template('fixed_assets/detail.html', 
                          title=f"Fixed Asset - {asset.get('name', '')}",
                          asset=asset,
                          depreciation_history=depreciation_history or [])


@fixed_assets_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('accounting:edit')
def edit_fixed_asset(asset_id):
    """Edit fixed asset"""
    asset, status_code = api_request('GET', f'/fixed-assets/{asset_id}')
    
    if status_code != 200:
        flash('Fixed asset not found', 'error')
        return redirect(url_for('fixed_assets.fixed_assets_list'))
    
    if request.method == 'GET':
        vendors, _ = api_request('GET', '/crm/vendors')
        accounts, _ = api_request('GET', '/accounting/accounts')
        
        asset_accounts = [a for a in (accounts or []) if a.get('type') == 'Asset']
        expense_accounts = [a for a in (accounts or []) if a.get('type') == 'Expense']
        
        return render_template('fixed_assets/form.html',
                              title='Edit Fixed Asset',
                              asset=asset,
                              vendors=vendors or [],
                              asset_accounts=asset_accounts,
                              expense_accounts=expense_accounts,
                              today=date.today().isoformat())
    
    # POST - Update fixed asset
    data = {
        'name': request.form.get('name'),
        'asset_code': request.form.get('asset_code') or None,
        'description': request.form.get('description') or None,
        'category': request.form.get('category') or None,
        'location': request.form.get('location') or None,
        'salvage_value': float(request.form.get('salvage_value', 0)),
        'useful_life_years': int(request.form.get('useful_life_years', 5)),
        'depreciation_method': request.form.get('depreciation_method', 'straight_line'),
        'depreciation_rate': float(request.form.get('depreciation_rate', 0)) if request.form.get('depreciation_rate') else None,
        'warranty_expiry': request.form.get('warranty_expiry') or None,
        'insurance_policy': request.form.get('insurance_policy') or None,
        'insurance_expiry': request.form.get('insurance_expiry') or None,
    }
    
    response, status_code = api_request('PUT', f'/fixed-assets/{asset_id}', data=data)
    
    if status_code == 200:
        flash('Fixed asset updated successfully', 'success')
        return redirect(url_for('fixed_assets.fixed_asset_detail', asset_id=asset_id))
    
    error = response.get('detail', 'Failed to update fixed asset') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('fixed_assets.edit_fixed_asset', asset_id=asset_id))


@fixed_assets_bp.route('/<int:asset_id>/depreciate', methods=['POST'])
@login_required
@permission_required('accounting:edit')
def record_depreciation(asset_id):
    """Record depreciation for an asset"""
    data = {
        'amount': float(request.form.get('amount', 0)),
        'depreciation_date': request.form.get('depreciation_date') or date.today().isoformat(),
        'description': request.form.get('description') or None
    }
    
    response, status_code = api_request('POST', f'/fixed-assets/{asset_id}/depreciate', data=data)
    
    if status_code == 200:
        result = response
        flash(f'Depreciation of {result.get("depreciation_amount", 0)} recorded. Book value: {result.get("book_value", 0)}', 'success')
    else:
        error = response.get('detail', 'Failed to record depreciation') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('fixed_assets.fixed_asset_detail', asset_id=asset_id))


@fixed_assets_bp.route('/<int:asset_id>/dispose', methods=['POST'])
@login_required
@permission_required('accounting:edit')
def dispose_asset(asset_id):
    """Dispose of an asset"""
    data = {
        'disposal_date': request.form.get('disposal_date') or date.today().isoformat(),
        'disposal_amount': float(request.form.get('disposal_amount', 0)),
        'disposal_reason': request.form.get('disposal_reason') or None
    }
    
    response, status_code = api_request('POST', f'/fixed-assets/{asset_id}/dispose', data=data)
    
    if status_code == 200:
        flash('Asset disposed successfully!', 'success')
        return redirect(url_for('fixed_assets.fixed_assets_list'))
    
    error = response.get('detail', 'Failed to dispose asset') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('fixed_assets.fixed_asset_detail', asset_id=asset_id))


@fixed_assets_bp.route('/<int:asset_id>/write-off', methods=['POST'])
@login_required
@permission_required('accounting:edit')
def write_off_asset(asset_id):
    """Write off an asset"""
    data = {
        'write_off_date': request.form.get('write_off_date') or date.today().isoformat(),
        'reason': request.form.get('reason') or None
    }
    
    response, status_code = api_request('POST', f'/fixed-assets/{asset_id}/write-off', data=data)
    
    if status_code == 200:
        flash('Asset written off successfully!', 'success')
        return redirect(url_for('fixed_assets.fixed_assets_list'))
    
    error = response.get('detail', 'Failed to write off asset') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('fixed_assets.fixed_asset_detail', asset_id=asset_id))


@fixed_assets_bp.route('/<int:asset_id>/delete', methods=['POST'])
@login_required
@permission_required('accounting:delete')
def delete_fixed_asset(asset_id):
    """Delete fixed asset"""
    response, status_code = api_request('DELETE', f'/fixed-assets/{asset_id}')
    
    if status_code == 200:
        flash('Fixed asset deleted successfully', 'success')
    else:
        error = response.get('detail', 'Failed to delete fixed asset') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('fixed_assets.fixed_assets_list'))


@fixed_assets_bp.route('/bulk-depreciation', methods=['POST'])
@login_required
@permission_required('accounting:edit')
def bulk_depreciation():
    """Run bulk depreciation for multiple assets"""
    data = {
        'depreciation_date': request.form.get('depreciation_date') or date.today().isoformat(),
        'period_start': request.form.get('period_start') or date.today().isoformat(),
        'period_end': request.form.get('period_end') or date.today().isoformat(),
        'description': request.form.get('description') or None
    }
    
    asset_ids = request.form.getlist('asset_ids')
    if asset_ids:
        data['asset_ids'] = [int(aid) for aid in asset_ids]
    
    response, status_code = api_request('POST', '/fixed-assets/bulk-depreciation', data=data)
    
    if status_code == 200:
        result = response
        flash(f'Depreciation recorded for {len(result.get("results", []))} assets', 'success')
    else:
        error = response.get('detail', 'Failed to run bulk depreciation') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('fixed_assets.fixed_assets_list'))
