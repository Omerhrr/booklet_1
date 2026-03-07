"""
Budgets Views
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from app import api_request, login_required, permission_required

bp = Blueprint('budgets', __name__, url_prefix='/budgets')


@bp.route('')
@login_required
@permission_required('budgets:view')
def list_budgets():
    """List all budgets"""
    fiscal_year = request.args.get('fiscal_year', '')
    
    params = {}
    if fiscal_year:
        params['fiscal_year'] = fiscal_year
    
    budgets, status = api_request('GET', '/budgets', params=params if params else None)
    
    if status != 200:
        budgets = []
    
    # Get available fiscal years for filter
    years_data, _ = api_request('GET', '/budgets/fiscal-years')
    fiscal_years = years_data.get('fiscal_years', []) if years_data else []
    
    # Calculate totals
    total_budgeted = sum(b.get('total_budgeted', 0) for b in budgets) if budgets else 0
    
    return render_template('budgets/budgets.html',
                          title='Budgets',
                          budgets=budgets,
                          fiscal_years=fiscal_years,
                          selected_year=fiscal_year,
                          total_budgeted=total_budgeted)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('budgets:create')
def new_budget():
    """Create new budget"""
    if request.method == 'GET':
        # Get accounts for budgeting (Revenue and Expense accounts)
        accounts_data, _ = api_request('GET', '/budgets/available-accounts')
        accounts = accounts_data.get('accounts', []) if accounts_data else []
        
        current_year = date.today().year
        
        return render_template('budgets/budget_form.html',
                              title='New Budget',
                              accounts=accounts,
                              current_year=current_year)
    
    # POST - Create budget
    # Collect budget items
    items = []
    account_ids = request.form.getlist('account_id[]')
    amounts = request.form.getlist('amount[]')
    months = request.form.getlist('month[]')
    
    for i, account_id in enumerate(account_ids):
        if account_id and amounts[i]:
            items.append({
                'account_id': int(account_id),
                'amount': float(amounts[i]),
                'month': int(months[i]) if months[i] else None
            })
    
    data = {
        'name': request.form.get('name'),
        'fiscal_year': int(request.form.get('fiscal_year')),
        'description': request.form.get('description'),
        'items': items
    }
    
    response, status = api_request('POST', '/budgets', data=data)
    
    if status == 200:
        flash('Budget created successfully', 'success')
        return redirect(url_for('budgets.view_budget', budget_id=response.get('id')))
    
    error = response.get('detail', 'Failed to create budget') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('budgets.new_budget'))


@bp.route('/<int:budget_id>')
@login_required
@permission_required('budgets:view')
def view_budget(budget_id):
    """View budget details"""
    budget, status = api_request('GET', f'/budgets/{budget_id}')
    
    if status != 200:
        flash('Budget not found', 'error')
        return redirect(url_for('budgets.list_budgets'))
    
    # Group items by account type
    revenue_items = [item for item in budget.get('items', []) if item.get('account_type') == 'Revenue']
    expense_items = [item for item in budget.get('items', []) if item.get('account_type') == 'Expense']
    
    total_revenue = sum(item.get('amount', 0) for item in revenue_items)
    total_expense = sum(item.get('amount', 0) for item in expense_items)
    net_budget = total_revenue - total_expense
    
    return render_template('budgets/budget_detail.html',
                          title=f"Budget: {budget.get('name', '')}",
                          budget=budget,
                          revenue_items=revenue_items,
                          expense_items=expense_items,
                          total_revenue=total_revenue,
                          total_expense=total_expense,
                          net_budget=net_budget)


@bp.route('/<int:budget_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('budgets:edit')
def edit_budget(budget_id):
    """Edit budget"""
    budget, status = api_request('GET', f'/budgets/{budget_id}')
    
    if status != 200:
        flash('Budget not found', 'error')
        return redirect(url_for('budgets.list_budgets'))
    
    if request.method == 'GET':
        # Get accounts for budgeting
        accounts_data, _ = api_request('GET', '/budgets/available-accounts')
        accounts = accounts_data.get('accounts', []) if accounts_data else []
        
        return render_template('budgets/budget_form.html',
                              title='Edit Budget',
                              budget=budget,
                              accounts=accounts,
                              current_year=date.today().year)
    
    # POST - Update budget
    # Collect budget items
    items = []
    account_ids = request.form.getlist('account_id[]')
    amounts = request.form.getlist('amount[]')
    months = request.form.getlist('month[]')
    
    for i, account_id in enumerate(account_ids):
        if account_id and amounts[i]:
            items.append({
                'account_id': int(account_id),
                'amount': float(amounts[i]),
                'month': int(months[i]) if months[i] else None
            })
    
    data = {
        'name': request.form.get('name'),
        'fiscal_year': int(request.form.get('fiscal_year')),
        'description': request.form.get('description'),
        'items': items
    }
    
    response, status = api_request('PUT', f'/budgets/{budget_id}', data=data)
    
    if status == 200:
        flash('Budget updated successfully', 'success')
        return redirect(url_for('budgets.view_budget', budget_id=budget_id))
    
    error = response.get('detail', 'Failed to update budget') if response else 'Failed'
    flash(error, 'error')
    return redirect(url_for('budgets.edit_budget', budget_id=budget_id))


@bp.route('/<int:budget_id>/delete', methods=['POST'])
@login_required
@permission_required('budgets:delete')
def delete_budget(budget_id):
    """Delete budget"""
    response, status = api_request('DELETE', f'/budgets/{budget_id}')
    
    if status == 200:
        flash('Budget deleted successfully', 'success')
    else:
        error = response.get('detail', 'Failed to delete budget') if response else 'Failed'
        flash(error, 'error')
    
    return redirect(url_for('budgets.list_budgets'))


@bp.route('/<int:budget_id>/vs-actual')
@login_required
@permission_required('budgets:view')
def budget_vs_actual(budget_id):
    """View budget vs actual comparison"""
    month = request.args.get('month', '')
    
    params = {}
    if month:
        params['month'] = month
    
    budget, budget_status = api_request('GET', f'/budgets/{budget_id}')
    comparison, status = api_request('GET', f'/budgets/{budget_id}/vs-actual', params=params if params else None)
    
    if budget_status != 200 or status != 200:
        flash('Budget not found', 'error')
        return redirect(url_for('budgets.list_budgets'))
    
    # Group items by type
    items = comparison.get('items', [])
    revenue_items = [item for item in items if item.get('account_type') == 'Revenue']
    expense_items = [item for item in items if item.get('account_type') == 'Expense']
    
    # Calculate totals
    total_budgeted_revenue = sum(item.get('budgeted', 0) for item in revenue_items)
    total_actual_revenue = sum(item.get('actual', 0) for item in revenue_items)
    total_budgeted_expense = sum(item.get('budgeted', 0) for item in expense_items)
    total_actual_expense = sum(item.get('actual', 0) for item in expense_items)
    
    return render_template('budgets/budget_vs_actual.html',
                          title=f"Budget vs Actual: {budget.get('name', '')}",
                          budget=budget,
                          comparison=comparison,
                          revenue_items=revenue_items,
                          expense_items=expense_items,
                          total_budgeted_revenue=total_budgeted_revenue,
                          total_actual_revenue=total_actual_revenue,
                          total_budgeted_expense=total_budgeted_expense,
                          total_actual_expense=total_actual_expense,
                          selected_month=month)


@bp.route('/<int:budget_id>/monthly')
@login_required
@permission_required('budgets:view')
def monthly_budget(budget_id):
    """View monthly budget breakdown"""
    budget, status = api_request('GET', f'/budgets/{budget_id}')
    monthly_data, monthly_status = api_request('GET', f'/budgets/{budget_id}/monthly')
    
    if status != 200 or monthly_status != 200:
        flash('Budget not found', 'error')
        return redirect(url_for('budgets.list_budgets'))
    
    return render_template('budgets/monthly.html',
                          title=f"Monthly Budget: {budget.get('name', '')}",
                          budget=budget,
                          monthly=monthly_data.get('monthly', []))


@bp.route('/api/accounts')
@login_required
def api_accounts():
    """API endpoint to get available accounts"""
    accounts_data, _ = api_request('GET', '/budgets/available-accounts')
    accounts = accounts_data.get('accounts', []) if accounts_data else []
    return jsonify(accounts)
