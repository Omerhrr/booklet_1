"""
Purchases Views
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from app import api_request, login_required, permission_required
import json

bp = Blueprint('purchases', __name__, url_prefix='/purchases')


@bp.route('/bills')
@login_required
@permission_required('bills:view')
def list_bills():
    """List all purchase bills"""
    status_filter = request.args.get('status')
    params = {'status': status_filter} if status_filter else {}
    
    bills, status = api_request('GET', '/purchases/bills', params=params)
    
    if status != 200:
        bills = []
    
    return render_template('purchases/bills.html', title='Purchase Bills', bills=bills)


@bp.route('/bills/new', methods=['GET', 'POST'])
@login_required
@permission_required('bills:create')
def new_bill():
    """Create new purchase bill"""
    if request.method == 'GET':
        vendors, _ = api_request('GET', '/crm/vendors')
        products, _ = api_request('GET', '/inventory/products')
        business, _ = api_request('GET', '/settings/business')
        
        return render_template('purchases/bill_form.html',
                              title='New Purchase Bill',
                              vendors=vendors or [],
                              products=products or [],
                              vat_rate=business.get('vat_rate', 0) if business else 0)
    
    # POST
    items_json = request.form.get('items_json', '[]')
    
    data = {
        'vendor_id': request.form.get('vendor_id'),
        'bill_date': request.form.get('bill_date'),
        'due_date': request.form.get('due_date'),
        'bill_number': request.form.get('bill_number'),
        'notes': request.form.get('notes'),
        'items': json.loads(items_json)
    }
    
    response, status = api_request('POST', '/purchases/bills', data=data)
    
    if status == 200:
        flash('Purchase bill created successfully', 'success')
        return redirect(url_for('purchases.view_bill', bill_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create bill') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('purchases.new_bill'))


@bp.route('/bills/<int:bill_id>')
@login_required
@permission_required('bills:view')
def view_bill(bill_id):
    """View purchase bill"""
    bill, status = api_request('GET', f'/purchases/bills/{bill_id}')
    
    if status != 200:
        flash('Bill not found', 'error')
        return redirect(url_for('purchases.list_bills'))
    
    # Get payment accounts for the payment form
    payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
    
    return render_template('purchases/bill_detail.html',
                          title=f"Bill {bill.get('bill_number', '')}",
                          bill=bill,
                          payment_accounts=payment_accounts or [])


@bp.route('/bills/<int:bill_id>/payment', methods=['POST'])
@login_required
@permission_required('bills:edit')
def record_payment(bill_id):
    """Record payment for bill"""
    data = {
        'bill_id': bill_id,
        'payment_date': request.form.get('payment_date'),
        'amount': request.form.get('amount'),
        'payment_account_id': request.form.get('payment_account_id'),
        'bank_account_id': request.form.get('bank_account_id') or None,
        'account_type': request.form.get('account_type', 'cash'),
        'reference': request.form.get('reference')
    }

    response, status = api_request('POST', f'/purchases/bills/{bill_id}/payment', data=data)

    if status == 200:
        flash('Payment recorded successfully', 'success')
        return redirect(url_for('purchases.view_bill', bill_id=bill_id))

    error = response.get('detail', 'Failed to record payment') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('purchases.view_bill', bill_id=bill_id))


# ==================== DEBIT NOTES ====================

@bp.route('/debit-notes')
@login_required
@permission_required('debit_notes:view')
def list_debit_notes():
    """List all debit notes"""
    debit_notes, status = api_request('GET', '/purchases/debit-notes')
    
    if status != 200:
        debit_notes = []
    
    return render_template('purchases/debit_notes.html', title='Debit Notes', debit_notes=debit_notes)


@bp.route('/debit-notes/<int:debit_note_id>')
@login_required
@permission_required('debit_notes:view')
def view_debit_note(debit_note_id):
    """View debit note"""
    debit_note, status = api_request('GET', f'/purchases/debit-notes/{debit_note_id}')
    
    if status != 200:
        flash('Debit note not found', 'error')
        return redirect(url_for('purchases.list_debit_notes'))
    
    return render_template('purchases/debit_note_detail.html',
                          title=f"Debit Note {debit_note.get('debit_note_number', '')}",
                          debit_note=debit_note)


@bp.route('/bills/<int:bill_id>/debit-note', methods=['GET', 'POST'])
@login_required
@permission_required('debit_notes:create')
def create_debit_note(bill_id):
    """Create debit note from bill"""
    bill, status = api_request('GET', f'/purchases/bills/{bill_id}')
    
    if status != 200:
        flash('Bill not found', 'error')
        return redirect(url_for('purchases.list_bills'))
    
    if request.method == 'GET':
        return render_template('purchases/debit_note_form.html',
                              title=f'Create Debit Note for {bill.get("bill_number", "")}',
                              bill=bill,
                              today=date.today().isoformat())
    
    # POST - Create debit note
    items_to_return = []
    item_index = 0
    while f'items[{item_index}][item_id]' in request.form:
        quantity = float(request.form.get(f'items[{item_index}][quantity]', 0))
        if quantity > 0:
            items_to_return.append({
                'original_item_id': int(request.form.get(f'items[{item_index}][item_id]')),
                'product_id': int(request.form.get(f'items[{item_index}][product_id]')),
                'quantity': quantity,
                'price': float(request.form.get(f'items[{item_index}][price]', 0))
            })
        item_index += 1
    
    if not items_to_return:
        flash('Please select at least one item to return', 'error')
        return redirect(url_for('purchases.create_debit_note', bill_id=bill_id))
    
    data = {
        'bill_id': bill_id,
        'items_to_return': items_to_return,
        'debit_note_date': request.form.get('debit_note_date'),
        'reason': request.form.get('reason', 'Purchase Return')
    }
    
    response, status = api_request('POST', '/purchases/debit-notes', data=data)
    
    if status == 200:
        flash('Debit note created successfully', 'success')
        return redirect(url_for('purchases.view_debit_note', debit_note_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create debit note') if response else 'Failed to create debit note'
    flash(error, 'error')
    return redirect(url_for('purchases.create_debit_note', bill_id=bill_id))


@bp.route('/debit-notes/<int:debit_note_id>/apply', methods=['POST'])
@login_required
@permission_required('debit_notes:edit')
def apply_debit_note(debit_note_id):
    """Apply debit note to bill"""
    response, status = api_request('POST', f'/purchases/debit-notes/{debit_note_id}/apply')
    
    if status == 200:
        flash('Debit note applied to bill successfully', 'success')
        return redirect(url_for('purchases.view_debit_note', debit_note_id=debit_note_id))
    
    error = response.get('detail', 'Failed to apply debit note') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('purchases.view_debit_note', debit_note_id=debit_note_id))
