"""
Other Income Views
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from app import api_request, login_required, permission_required

bp = Blueprint('other_incomes', __name__, url_prefix='/other-incomes')


@bp.route('')
@login_required
@permission_required('other_income:view')
def list_other_incomes():
    """List all other incomes"""
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
    
    incomes, status = api_request('GET', '/other-incomes', params=params if params else None)
    
    if status != 200:
        incomes = []
    
    # Get categories for filter dropdown
    categories_data, _ = api_request('GET', '/other-incomes/categories')
    categories = categories_data.get('categories', []) if categories_data else []
    
    # Calculate totals
    total_amount = sum(inc.get('amount', 0) for inc in incomes) if incomes else 0
    
    return render_template('other_incomes/list.html',
                          title='Other Income',
                          incomes=incomes,
                          categories=categories,
                          selected_category=category,
                          start_date=start_date,
                          end_date=end_date,
                          total_amount=total_amount)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('other_income:create')
def new_other_income():
    """Create new other income"""
    if request.method == 'GET':
        # Get data for form
        customers, _ = api_request('GET', '/crm/customers')
        accounts, _ = api_request('GET', '/accounting/accounts')
        payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
        categories_data, _ = api_request('GET', '/other-incomes/categories')
        next_number, _ = api_request('GET', '/other-incomes/next-number')
        
        categories = categories_data.get('categories', []) if categories_data else []
        
        # Filter accounts - revenue accounts for income_account_id
        income_accounts = [a for a in (accounts or []) if a.get('type') == 'Revenue']
        
        return render_template('other_incomes/form.html',
                              title='New Other Income',
                              customers=customers or [],
                              payment_accounts=payment_accounts or [],
                              income_accounts=income_accounts,
                              categories=categories,
                              next_number=next_number.get('next_number', 'INC-00001') if next_number else 'INC-00001',
                              today=date.today().isoformat())
    
    # POST - Create other income
    data = {
        'income_date': request.form.get('income_date'),
        'category': request.form.get('category'),
        'description': request.form.get('description'),
        'sub_total': float(request.form.get('sub_total', 0)),
        'vat_amount': float(request.form.get('vat_amount', 0)),
        'received_in_account_id': int(request.form.get('received_in_account_id')),
        'income_account_id': int(request.form.get('income_account_id')),
        'customer_id': int(request.form.get('customer_id')) if request.form.get('customer_id') else None
    }
    
    response, status = api_request('POST', '/other-incomes', data=data)
    
    if status == 200:
        flash('Income recorded successfully', 'success')
        return redirect(url_for('other_incomes.view_other_income', income_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create income') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('other_incomes.new_other_income'))


@bp.route('/<int:income_id>')
@login_required
@permission_required('other_income:view')
def view_other_income(income_id):
    """View other income details"""
    income, status = api_request('GET', f'/other-incomes/{income_id}')
    
    if status != 200:
        flash('Income record not found', 'error')
        return redirect(url_for('other_incomes.list_other_incomes'))
    
    return render_template('other_incomes/detail.html',
                          title=f"Income {income.get('income_number', '')}",
                          income=income)


@bp.route('/<int:income_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('other_income:edit')
def edit_other_income(income_id):
    """Edit other income"""
    income, status = api_request('GET', f'/other-incomes/{income_id}')
    
    if status != 200:
        flash('Income record not found', 'error')
        return redirect(url_for('other_incomes.list_other_incomes'))
    
    if request.method == 'GET':
        customers, _ = api_request('GET', '/crm/customers')
        accounts, _ = api_request('GET', '/accounting/accounts')
        payment_accounts, _ = api_request('GET', '/banking/payment-accounts')
        categories_data, _ = api_request('GET', '/other-incomes/categories')
        
        categories = categories_data.get('categories', []) if categories_data else []
        income_accounts = [a for a in (accounts or []) if a.get('type') == 'Revenue']
        
        return render_template('other_incomes/form.html',
                              title='Edit Other Income',
                              income=income,
                              customers=customers or [],
                              payment_accounts=payment_accounts or [],
                              income_accounts=income_accounts,
                              categories=categories,
                              today=date.today().isoformat())
    
    # POST - Update other income
    data = {
        'income_date': request.form.get('income_date'),
        'category': request.form.get('category'),
        'description': request.form.get('description'),
        'sub_total': float(request.form.get('sub_total', 0)),
        'vat_amount': float(request.form.get('vat_amount', 0)),
        'received_in_account_id': int(request.form.get('received_in_account_id')),
        'income_account_id': int(request.form.get('income_account_id')),
        'customer_id': int(request.form.get('customer_id')) if request.form.get('customer_id') else None
    }
    
    response, status = api_request('PUT', f'/other-incomes/{income_id}', data=data)
    
    if status == 200:
        flash('Income updated successfully', 'success')
        return redirect(url_for('other_incomes.view_other_income', income_id=income_id))
    
    error = response.get('detail', 'Failed to update income') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('other_incomes.edit_other_income', income_id=income_id))


@bp.route('/<int:income_id>/delete', methods=['POST'])
@login_required
@permission_required('other_income:delete')
def delete_other_income(income_id):
    """Delete other income"""
    response, status = api_request('DELETE', f'/other-incomes/{income_id}')
    
    if status == 200:
        flash('Income record deleted successfully', 'success')
    else:
        error = response.get('detail', 'Failed to delete income') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('other_incomes.list_other_incomes'))
