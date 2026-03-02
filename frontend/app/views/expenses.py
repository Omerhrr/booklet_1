"""
Expenses Views
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from app import api_request, login_required, permission_required


def safe_float(value, default=0.0):
    """Safely convert form value to float, handling empty strings."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

bp = Blueprint('expenses', __name__, url_prefix='/expenses')


@bp.route('')
@login_required
@permission_required('expenses:view')
def list_expenses():
    """List all expenses"""
    # Get filter parameters
    category = request.args.get('category', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build API URL with filters
    params = {}
    if category:
        params['category'] = category
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    expenses, status = api_request('GET', '/expenses', params=params if params else None)
    
    if status != 200:
        expenses = []
    
    # Get categories for filter dropdown
    categories_data, _ = api_request('GET', '/expenses/categories')
    categories = categories_data.get('categories', []) if categories_data else []
    
    # Calculate totals
    total_amount = sum(exp.get('amount', 0) for exp in expenses) if expenses else 0
    
    return render_template('expenses/list.html',
                          title='Expenses',
                          expenses=expenses,
                          categories=categories,
                          selected_category=category,
                          start_date=start_date,
                          end_date=end_date,
                          total_amount=total_amount)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('expenses:create')
def new_expense():
    """Create new expense"""
    if request.method == 'GET':
        # Get data for form
        vendors, _ = api_request('GET', '/crm/vendors')
        accounts, accounts_status = api_request('GET', '/accounting/accounts')
        payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
        categories_data, _ = api_request('GET', '/expenses/categories')
        next_number, _ = api_request('GET', '/expenses/next-number')
        
        categories = categories_data.get('categories', []) if categories_data else []
        
        # Filter accounts - expense accounts for expense_account_id
        # Handle both dict and string responses from API
        if accounts_status == 200 and isinstance(accounts, list):
            expense_accounts = [a for a in accounts if isinstance(a, dict) and a.get('type') == 'Expense']
        else:
            expense_accounts = []
        
        return render_template('expenses/form.html',
                              title='New Expense',
                              vendors=vendors or [],
                              payment_accounts=payment_accounts or [],
                              expense_accounts=expense_accounts,
                              categories=categories,
                              next_number=next_number.get('next_number', 'EXP-00001') if next_number else 'EXP-00001',
                              today=date.today().isoformat())
    
    # POST - Create expense
    data = {
        'expense_date': request.form.get('expense_date'),
        'category': request.form.get('category'),
        'description': request.form.get('description'),
        'sub_total': safe_float(request.form.get('sub_total')),
        'vat_amount': safe_float(request.form.get('vat_amount')),
        'paid_from_account_id': int(request.form.get('paid_from_account_id')),
        'expense_account_id': int(request.form.get('expense_account_id')),
        'vendor_id': int(request.form.get('vendor_id')) if request.form.get('vendor_id') else None
    }
    
    response, status = api_request('POST', '/expenses', data=data)
    
    if status == 200:
        flash('Expense recorded successfully', 'success')
        return redirect(url_for('expenses.view_expense', expense_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create expense') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('expenses.new_expense'))


@bp.route('/<int:expense_id>')
@login_required
@permission_required('expenses:view')
def view_expense(expense_id):
    """View expense details"""
    expense, status = api_request('GET', f'/expenses/{expense_id}')
    
    if status != 200:
        flash('Expense not found', 'error')
        return redirect(url_for('expenses.list_expenses'))
    
    return render_template('expenses/detail.html',
                          title=f"Expense {expense.get('expense_number', '')}",
                          expense=expense)


@bp.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('expenses:edit')
def edit_expense(expense_id):
    """Edit expense"""
    expense, status = api_request('GET', f'/expenses/{expense_id}')
    
    if status != 200:
        flash('Expense not found', 'error')
        return redirect(url_for('expenses.list_expenses'))
    
    if request.method == 'GET':
        vendors, _ = api_request('GET', '/crm/vendors')
        accounts, accounts_status = api_request('GET', '/accounting/accounts')
        payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
        categories_data, _ = api_request('GET', '/expenses/categories')
        
        categories = categories_data.get('categories', []) if categories_data else []
        # Handle both dict and string responses from API
        if accounts_status == 200 and isinstance(accounts, list):
            expense_accounts = [a for a in accounts if isinstance(a, dict) and a.get('type') == 'Expense']
        else:
            expense_accounts = []
        
        return render_template('expenses/form.html',
                              title='Edit Expense',
                              expense=expense,
                              vendors=vendors or [],
                              payment_accounts=payment_accounts or [],
                              expense_accounts=expense_accounts,
                              categories=categories,
                              today=date.today().isoformat())
    
    # POST - Update expense
    data = {
        'expense_date': request.form.get('expense_date'),
        'category': request.form.get('category'),
        'description': request.form.get('description'),
        'sub_total': safe_float(request.form.get('sub_total')),
        'vat_amount': safe_float(request.form.get('vat_amount')),
        'paid_from_account_id': int(request.form.get('paid_from_account_id')),
        'expense_account_id': int(request.form.get('expense_account_id')),
        'vendor_id': int(request.form.get('vendor_id')) if request.form.get('vendor_id') else None
    }
    
    response, status = api_request('PUT', f'/expenses/{expense_id}', data=data)
    
    if status == 200:
        flash('Expense updated successfully', 'success')
        return redirect(url_for('expenses.view_expense', expense_id=expense_id))
    
    error = response.get('detail', 'Failed to update expense') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('expenses.edit_expense', expense_id=expense_id))


@bp.route('/<int:expense_id>/delete', methods=['POST'])
@login_required
@permission_required('expenses:delete')
def delete_expense(expense_id):
    """Delete expense"""
    response, status = api_request('DELETE', f'/expenses/{expense_id}')
    
    if status == 200:
        flash('Expense deleted successfully', 'success')
    else:
        error = response.get('detail', 'Failed to delete expense') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('expenses.list_expenses'))


@bp.route('/summary')
@login_required
@permission_required('expenses:view')
def expense_summary():
    """Get expense summary by category"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    summary, status = api_request('GET', '/expenses/summary', params=params if params else None)
    
    if status != 200:
        summary = {'categories': [], 'total': 0}
    
    return render_template('expenses/summary.html',
                          title='Expense Summary',
                          summary=summary,
                          start_date=start_date,
                          end_date=end_date)
