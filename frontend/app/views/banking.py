"""
Banking Views
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import api_request, login_required, permission_required

bp = Blueprint('banking', __name__, url_prefix='/banking')

# Currency code to symbol mapping
CURRENCY_SYMBOLS = {
    'USD': '$',
    'NGN': '₦',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'CNY': '¥',
    'INR': '₹',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'Fr',
    'ZAR': 'R',
    'KES': 'KSh',
    'GHS': '₵',
    'AED': 'د.إ',
    'SAR': '﷼',
}


def get_currency_symbol():
    """Get currency symbol from session currency code"""
    currency_code = session.get('branch_currency', 'USD')
    return CURRENCY_SYMBOLS.get(currency_code, currency_code)


@bp.route('/accounts')
@login_required
@permission_required('banking:view')
def list_accounts():
    """List all bank accounts"""
    accounts, status = api_request('GET', '/banking/accounts')

    if status != 200:
        accounts = []

    return render_template('banking/accounts.html', title='Bank Accounts', accounts=accounts)


@bp.route('/accounts/new', methods=['GET', 'POST'])
@login_required
@permission_required('banking:create')
def new_account():
    """Create new bank account"""
    currency_symbol = get_currency_symbol()

    if request.method == 'GET':
        coa_accounts, _ = api_request('GET', '/accounting/accounts')
        return render_template('banking/account_form.html', title='New Bank Account', coa_accounts=coa_accounts or [], currency_symbol=currency_symbol)

    data = {
        'account_name': request.form.get('account_name'),
        'bank_name': request.form.get('bank_name'),
        'account_number': request.form.get('account_number'),
        'currency': request.form.get('currency', 'USD'),
        'chart_of_account_id': request.form.get('chart_of_account_id') or None,
        'opening_balance': request.form.get('opening_balance', '0')
    }

    response, status = api_request('POST', '/banking/accounts', data=data)

    if status == 200:
        flash('Bank account created', 'success')
        return redirect(url_for('banking.list_accounts'))

    error = response.get('detail', 'Failed to create bank account') if response else 'Failed'
    flash(error, 'error')
    coa_accounts, _ = api_request('GET', '/accounting/accounts')
    return render_template('banking/account_form.html', title='New Bank Account', coa_accounts=coa_accounts or [], currency_symbol=currency_symbol)


@bp.route('/accounts/<int:account_id>')
@login_required
@permission_required('banking:view')
def view_account(account_id):
    """View bank account details"""
    account, status = api_request('GET', f'/banking/accounts/{account_id}')

    if status != 200:
        flash('Account not found', 'error')
        return redirect(url_for('banking.list_accounts'))

    # Get date filters from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Build query params for API call
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    # Fetch transactions for this account
    transactions_data, _ = api_request('GET', f'/banking/accounts/{account_id}/transactions', params=params if params else None)

    # Handle the new response format (dict with transactions key)
    if isinstance(transactions_data, dict):
        transactions = transactions_data.get('transactions', [])
    else:
        transactions = transactions_data or []

    return render_template('banking/account_detail.html',
                          title=account.get('account_name', 'Bank Account'),
                          account=account,
                          transactions=transactions,
                          start_date=start_date,
                          end_date=end_date)


@bp.route('/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
@permission_required('banking:create')
def delete_account(account_id):
    """Delete a bank account"""
    response, status = api_request('DELETE', f'/banking/accounts/{account_id}')

    if status == 200:
        flash('Bank account deleted', 'success')
    else:
        error = response.get('detail', 'Failed to delete bank account') if response else 'Failed to delete'
        flash(error, 'error')

    return redirect(url_for('banking.list_accounts'))


@bp.route('/transfers')
@login_required
@permission_required('banking:view')
def transfers():
    """Fund transfers"""
    transfers, status = api_request('GET', '/banking/transfers')
    # Use payment accounts which includes both bank and cash accounts
    payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
    
    if status != 200:
        transfers = []
    
    return render_template('banking/transfers.html', title='Fund Transfers', transfers=transfers, payment_accounts=payment_accounts or [])


@bp.route('/transfers/new', methods=['POST'])
@login_required
@permission_required('banking:create')
def new_transfer():
    """Create fund transfer"""
    # Get account type from the form
    from_account_type = request.form.get('from_account_type', 'bank')
    to_account_type = request.form.get('to_account_type', 'bank')
    
    # Get amount and convert to float
    amount_str = request.form.get('amount')
    try:
        amount = float(amount_str) if amount_str else 0
    except ValueError:
        flash('Invalid amount', 'error')
        return redirect(url_for('banking.transfers'))
    
    if amount <= 0:
        flash('Amount must be greater than 0', 'error')
        return redirect(url_for('banking.transfers'))
    
    data = {
        'transfer_date': request.form.get('transfer_date'),
        'amount': amount,
        'from_account_id': int(request.form.get('from_account_id')),
        'to_account_id': int(request.form.get('to_account_id')),
        'from_account_type': from_account_type,
        'to_account_type': to_account_type,
        'description': request.form.get('description') or None,
        'reference': request.form.get('reference') or None
    }
    
    response, status = api_request('POST', '/banking/transfers', data=data)
    
    if status == 200:
        flash('Transfer completed', 'success')
        return redirect(url_for('banking.transfers'))
    
    error = response.get('detail', 'Failed to create transfer') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('banking.transfers'))


@bp.route('/reconciliation')
@login_required
@permission_required('banking:view')
def reconciliation():
    """Bank Reconciliation - Enhanced with matching and clearing"""
    accounts, status = api_request('GET', '/banking/accounts')
    selected_account = None
    recon_status = None
    statement_lines = []
    uncleared_transactions = []
    recon_history = []
    
    account_id = request.args.get('account_id')
    if account_id:
        # Get selected account details
        selected_account, acc_status = api_request('GET', f'/banking/accounts/{account_id}')
        if acc_status == 200:
            # Get reconciliation status
            recon_status, _ = api_request('GET', f'/reconciliation/accounts/{account_id}/status')
            # Get statement lines (uncleared)
            statement_lines, _ = api_request('GET', f'/reconciliation/accounts/{account_id}/statement-lines', params={'is_cleared': 'false'})
            # Get uncleared cashbook transactions
            uncleared_transactions, _ = api_request('GET', f'/reconciliation/accounts/{account_id}/uncleared-transactions')
            # Get reconciliation history
            recon_history, _ = api_request('GET', f'/reconciliation/history', params={'account_id': account_id, 'limit': 5})
    
    from datetime import date
    today = date.today().isoformat()
    
    return render_template('banking/reconciliation.html', 
                          title='Bank Reconciliation', 
                          accounts=accounts or [],
                          selected_account=selected_account,
                          recon_status=recon_status,
                          statement_lines=statement_lines or [],
                          uncleared_transactions=uncleared_transactions or [],
                          recon_history=recon_history or [],
                          today=today)


@bp.route('/reconciliation/<int:account_id>/process', methods=['POST'])
@login_required
@permission_required('banking:create')
def process_reconciliation(account_id):
    """Process bank reconciliation"""
    statement_date = request.form.get('statement_date')
    statement_balance = request.form.get('statement_balance')
    notes = request.form.get('notes')
    
    if not statement_date or not statement_balance:
        flash('Please provide both statement date and balance', 'error')
        return redirect(url_for('banking.reconciliation', account_id=account_id))
    
    data = {
        'bank_account_id': account_id,
        'statement_date': statement_date,
        'statement_balance': float(statement_balance),
        'notes': notes or None
    }
    
    response, status = api_request('POST', '/reconciliation/complete', data=data)
    
    if status == 200:
        flash('Reconciliation completed successfully', 'success')
    else:
        error = response.get('detail', 'Failed to complete reconciliation') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/reconciliation/<int:account_id>/import', methods=['POST'])
@login_required
@permission_required('banking:create')
def import_statement(account_id):
    """Import bank statement CSV"""
    if 'statement_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('banking.reconciliation', account_id=account_id))
    
    file = request.files['statement_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('banking.reconciliation', account_id=account_id))
    
    statement_date = request.form.get('statement_date')
    has_header = request.form.get('has_header', 'true') == 'true'
    
    # Read file content
    content = file.read().decode('utf-8')
    
    # Import statement - simplified approach using string content
    # Note: This uses a simple text-based import since we're using api_request helper
    import requests
    from flask import session
    
    backend_url = f"http://localhost:8000/api/v1/reconciliation/accounts/{account_id}/import-statement"
    headers = {
        'Authorization': f"Bearer {session.get('access_token')}"
    }
    
    files = {'file': (file.filename, content, 'text/csv')}
    params = {
        'statement_date': statement_date,
        'has_header': str(has_header).lower()
    }
    
    try:
        response = requests.post(backend_url, headers=headers, files=files, params=params)
        if response.status_code == 200:
            result = response.json()
            flash(result.get('message', 'Statement imported'), 'success')
        else:
            error = response.json().get('detail', 'Import failed')
            flash(error, 'error')
    except Exception as e:
        flash(f'Import failed: {str(e)}', 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/reconciliation/match', methods=['POST'])
@login_required
@permission_required('banking:create')
def match_transactions():
    """Match statement line with cashbook entry"""
    statement_line_id = request.form.get('statement_line_id')
    cashbook_entry_id = request.form.get('cashbook_entry_id')
    account_id = request.form.get('account_id')
    
    data = {
        'statement_line_id': int(statement_line_id),
        'cashbook_entry_id': int(cashbook_entry_id)
    }
    
    response, status = api_request('POST', '/reconciliation/match', data=data)
    
    if status == 200:
        flash('Transactions matched successfully', 'success')
    else:
        error = response.get('detail', 'Failed to match transactions') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/reconciliation/auto-match/<int:account_id>', methods=['POST'])
@login_required
@permission_required('banking:create')
def auto_match_transactions(account_id):
    """Auto-match transactions"""
    response, status = api_request('POST', f'/reconciliation/auto-match/{account_id}')
    
    if status == 200:
        result = response
        flash(f"Auto-matched {len(result.get('matched_pairs', []))} transaction pairs", 'success')
    else:
        error = response.get('detail', 'Auto-match failed') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/reconciliation/clear-statement-line/<int:line_id>', methods=['POST'])
@login_required
@permission_required('banking:create')
def clear_statement_line(line_id):
    """Manually clear a statement line"""
    account_id = request.form.get('account_id')
    
    response, status = api_request('POST', f'/reconciliation/clear-statement-line/{line_id}')
    
    if status == 200:
        flash('Statement line cleared', 'success')
    else:
        flash('Failed to clear statement line', 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/reconciliation/clear-cashbook-entry/<int:entry_id>', methods=['POST'])
@login_required
@permission_required('banking:create')
def clear_cashbook_entry(entry_id):
    """Manually clear a cashbook entry"""
    account_id = request.form.get('account_id')
    
    response, status = api_request('POST', f'/reconciliation/clear-cashbook-entry/{entry_id}')
    
    if status == 200:
        flash('Cashbook entry cleared', 'success')
    else:
        flash('Failed to clear cashbook entry', 'error')
    
    return redirect(url_for('banking.reconciliation', account_id=account_id))


@bp.route('/accounts/<int:account_id>/statement/pdf')
@login_required
@permission_required('banking:view')
def download_statement_pdf(account_id):
    """Download PDF bank statement"""
    import requests
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build URL with query params
    backend_url = f"{request.scheme}://{request.host.replace('5000', '8000')}"
    url = f"{backend_url}/api/v1/banking/accounts/{account_id}/statement/pdf"
    
    params = []
    if start_date:
        params.append(f"start_date={start_date}")
    if end_date:
        params.append(f"end_date={end_date}")
    if params:
        url += "?" + "&".join(params)
    
    # Get access token from session
    headers = {
        'Authorization': f"Bearer {session.get('access_token')}"
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        return response.content, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': response.headers.get('Content-Disposition', 'attachment')
        }
    except Exception as e:
        flash('Failed to generate PDF', 'error')
        return redirect(url_for('banking.view_account', account_id=account_id))


@bp.route('/accounts/<int:account_id>/statement/excel')
@login_required
@permission_required('banking:view')
def download_statement_excel(account_id):
    """Download Excel bank statement"""
    import requests
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build URL with query params
    backend_url = f"{request.scheme}://{request.host.replace('5000', '8000')}"
    url = f"{backend_url}/api/v1/banking/accounts/{account_id}/statement/excel"
    
    params = []
    if start_date:
        params.append(f"start_date={start_date}")
    if end_date:
        params.append(f"end_date={end_date}")
    if params:
        url += "?" + "&".join(params)
    
    # Get access token from session
    headers = {
        'Authorization': f"Bearer {session.get('access_token')}"
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        return response.content, 200, {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': response.headers.get('Content-Disposition', 'attachment')
        }
    except Exception as e:
        flash('Failed to generate Excel', 'error')
        return redirect(url_for('banking.view_account', account_id=account_id))
