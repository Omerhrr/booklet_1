"""
Cash Book Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app import api_request, login_required, permission_required
from datetime import date, timedelta

cashbook_bp = Blueprint('cashbook', __name__, url_prefix='/cashbook')


@cashbook_bp.route('')
@login_required
@permission_required('accounting:view')
def cashbook_list():
    """List cash book entries"""
    # Get query parameters
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    account_id = request.args.get('account_id', '')
    entry_type = request.args.get('entry_type', '')
    
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    if account_id:
        params['account_id'] = account_id
    if entry_type:
        params['entry_type'] = entry_type
    
    # Get entries
    entries, status_code = api_request('GET', '/cashbook', params=params)
    
    if status_code != 200:
        entries = []
    
    # Get summary
    summaries, _ = api_request('GET', '/cashbook/summary', params=params)
    
    # Get payment accounts
    payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
    
    # Get currency from session
    currency = session.get('branch_currency', '$')
    
    return render_template('cashbook/list.html',
                          title='Cash Book',
                          cash_book_entries=entries,
                          summaries=summaries or [],
                          payment_accounts=payment_accounts or [],
                          start_date=start_date,
                          end_date=end_date,
                          selected_account=int(account_id) if account_id else None,
                          selected_entry_type=entry_type,
                          total_entries=len(entries),
                          currency=currency)


@cashbook_bp.route('/cash-flow')
@login_required
@permission_required('accounting:view')
def cash_flow():
    """Get cash flow summary"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    summary, status_code = api_request('GET', '/cashbook/cash-flow', params=params if params else None)
    
    if status_code != 200:
        return jsonify({'error': 'Failed to get cash flow summary'}), 500
    
    return jsonify(summary)


@cashbook_bp.route('/account/<int:account_id>')
@login_required
@permission_required('accounting:view')
def account_transactions(account_id):
    """Get transactions for a specific account"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    result, status_code = api_request('GET', f'/cashbook/account/{account_id}', params=params if params else None)
    
    if status_code != 200:
        flash('Account not found', 'error')
        return redirect(url_for('cashbook.cashbook_list'))
    
    return render_template('cashbook/account_transactions.html',
                          title=f"Account Transactions",
                          account=result.get('account', {}),
                          summary=result.get('summary', {}),
                          entries=result.get('entries', []))


@cashbook_bp.route('/entry/<int:entry_id>')
@login_required
@permission_required('accounting:view')
def entry_detail(entry_id):
    """Get a single cash book entry"""
    entry, status_code = api_request('GET', f'/cashbook/entry/{entry_id}')
    
    if status_code != 200:
        flash('Entry not found', 'error')
        return redirect(url_for('cashbook.cashbook_list'))
    
    return render_template('cashbook/entry_detail.html',
                          title=f"Cash Book Entry",
                          entry=entry)


@cashbook_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('accounting:create')
def create_entry():
    """Create a manual cash book entry"""
    if request.method == 'GET':
        payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
        customers, _ = api_request('GET', '/cashbook/customers-with-balance')
        vendors, _ = api_request('GET', '/cashbook/vendors-with-balance')
        
        # Get currency from session
        currency = session.get('branch_currency', '$')
        
        return render_template('cashbook/form.html',
                              title='New Cash Book Entry',
                              payment_accounts=payment_accounts or [],
                              customers=customers or [],
                              vendors=vendors or [],
                              today=date.today().isoformat(),
                              currency=currency)
    
    # POST - Create entry
    # Check if this is a fund account request
    fund_type = request.form.get('fund_type')
    if fund_type in ['customer', 'vendor']:
        return fund_account()
    
    data = {
        'entry_date': request.form.get('entry_date'),
        'entry_type': request.form.get('entry_type'),
        'account_id': int(request.form.get('account_id')),
        'account_type': request.form.get('account_type', 'cash'),
        'amount': float(request.form.get('amount', 0)),
        'description': request.form.get('description') or None,
        'reference': request.form.get('reference') or None,
        'payee_payer': request.form.get('payee_payer') or None,
    }
    
    response, status_code = api_request('POST', '/cashbook', data=data)
    
    if status_code == 200:
        flash('Cash book entry created successfully', 'success')
        return redirect(url_for('cashbook.cashbook_list'))
    
    error = response.get('detail', 'Failed to create entry') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('cashbook.create_entry'))


def fund_account():
    """Fund a customer or vendor account"""
    fund_type = request.form.get('fund_type')
    entity_id = request.form.get('entity_id')
    amount = request.form.get('amount')
    payment_account_id = request.form.get('payment_account_id')
    bank_account_id = request.form.get('bank_account_id')  # Bank account ID if funding from bank
    description = request.form.get('description')
    reference = request.form.get('reference')
    
    if not entity_id or not amount or not payment_account_id:
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('cashbook.create_entry'))
    
    data = {
        'entity_type': fund_type,
        'entity_id': int(entity_id),
        'amount': float(amount),
        'payment_account_id': int(payment_account_id),
        'bank_account_id': int(bank_account_id) if bank_account_id else None,
        'description': description or None,
        'reference': reference or None
    }
    
    response, status_code = api_request('POST', '/cashbook/fund-account', data=data)
    
    if status_code == 200:
        flash(response.get('message', f'{fund_type.title()} account funded successfully'), 'success')
        return redirect(url_for('cashbook.cashbook_list'))
    
    error = response.get('detail', 'Failed to fund account') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('cashbook.create_entry'))


@cashbook_bp.route('/entry/<int:entry_id>/delete', methods=['POST'])
@login_required
@permission_required('accounting:delete')
def delete_entry(entry_id):
    """Delete a manual cash book entry"""
    response, status_code = api_request('DELETE', f'/cashbook/entry/{entry_id}')
    
    if status_code == 200:
        flash('Entry deleted successfully', 'success')
    else:
        error = response.get('detail', 'Cannot delete entry') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('cashbook.cashbook_list'))


@cashbook_bp.route('/reconcile/<int:account_id>', methods=['POST'])
@login_required
@permission_required('accounting:edit')
def reconcile_account(account_id):
    """Reconcile cash book with ledger for an account"""
    as_of_date = request.form.get('as_of_date') or date.today().isoformat()
    
    result, status_code = api_request('POST', f'/cashbook/reconcile/{account_id}', 
                                       params={'as_of_date': as_of_date})
    
    if status_code == 200:
        return jsonify(result)
    
    return jsonify({'error': 'Reconciliation failed'}), 500
