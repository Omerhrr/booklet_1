"""
Dashboard Views - User Dashboard, Billing, Subscription Management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import api_request, generate_csrf_token, login_required
from datetime import datetime

bp = Blueprint('dashboard', __name__)


@bp.route('')
@bp.route('/')
@login_required
def index():
    """User dashboard home"""
    user_id = session.get('user_id')
    business_id = session.get('business_id')
    
    # Get subscription info
    sub_result, _ = api_request('GET', '/saas/subscription')
    subscription = sub_result.get('subscription', {})
    
    # Get business info
    business_result, _ = api_request('GET', f'/settings/business/{business_id}')
    business = business_result.get('business', {})
    
    # Get recent payments
    payments_result, _ = api_request('GET', '/saas/payments?limit=5')
    payments = payments_result.get('payments', [])
    
    # Get usage stats
    usage_result, _ = api_request('GET', '/saas/usage')
    usage = usage_result.get('usage', {})
    
    return render_template('dashboard/index.html',
                          title='Dashboard - Booklet',
                          subscription=subscription,
                          business=business,
                          payments=payments,
                          usage=usage,
                          csrf_token=generate_csrf_token)


@bp.route('/billing')
@login_required
def billing():
    """Billing and payment history"""
    # Get payments
    payments_result, _ = api_request('GET', '/saas/payments')
    payments = payments_result.get('payments', [])
    
    # Get subscription
    sub_result, _ = api_request('GET', '/saas/subscription')
    subscription = sub_result.get('subscription', {})
    
    return render_template('dashboard/billing.html',
                          title='Billing - Booklet',
                          payments=payments,
                          subscription=subscription,
                          csrf_token=generate_csrf_token)


@bp.route('/subscription')
@login_required
def subscription():
    """Subscription management"""
    # Get current subscription
    sub_result, _ = api_request('GET', '/saas/subscription')
    current_sub = sub_result.get('subscription', {})
    
    # Get all plans
    plans_result, _ = api_request('GET', '/saas/plans')
    plans = plans_result.get('plans', [])
    
    return render_template('dashboard/subscription.html',
                          title='Subscription - Booklet',
                          current_subscription=current_sub,
                          plans=plans,
                          csrf_token=generate_csrf_token)


@bp.route('/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade():
    """Upgrade subscription"""
    if request.method == 'POST':
        plan_slug = request.form.get('plan_slug')
        billing_cycle = request.form.get('billing_cycle', 'monthly')
        
        result, status_code = api_request('POST', '/saas/subscription/upgrade', data={
            'plan_slug': plan_slug,
            'billing_cycle': billing_cycle
        })
        
        if status_code == 200:
            flash('Subscription upgraded successfully!', 'success')
            return redirect(url_for('dashboard.subscription'))
        else:
            flash(result.get('detail', 'Failed to upgrade subscription.'), 'error')
    
    # Get current subscription
    sub_result, _ = api_request('GET', '/saas/subscription')
    current_sub = sub_result.get('subscription', {})
    
    # Get plan to upgrade to
    plan_slug = request.args.get('plan')
    plans_result, _ = api_request('GET', '/saas/plans')
    plans = plans_result.get('plans', [])
    target_plan = next((p for p in plans if p.get('slug') == plan_slug), None)
    
    return render_template('dashboard/upgrade.html',
                          title='Upgrade Plan - Booklet',
                          current_subscription=current_sub,
                          target_plan=target_plan,
                          csrf_token=generate_csrf_token)


@bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription"""
    result, status_code = api_request('POST', '/saas/subscription/cancel')
    
    if status_code == 200:
        flash('Subscription cancelled. You can continue using Booklet until the end of your billing period.', 'success')
    else:
        flash(result.get('detail', 'Failed to cancel subscription.'), 'error')
    
    return redirect(url_for('dashboard.subscription'))


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Account settings"""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email')
        }
        
        result, status_code = api_request('PUT', '/saas/account', data=data)
        
        if status_code == 200:
            session['name'] = data['name']
            session['email'] = data['email']
            flash('Account updated successfully.', 'success')
        else:
            flash(result.get('detail', 'Failed to update account.'), 'error')
        
        return redirect(url_for('dashboard.settings'))
    
    # Get account info
    account_result, _ = api_request('GET', '/saas/account')
    account = account_result.get('account', {})
    
    return render_template('dashboard/settings.html',
                          title='Account Settings - Booklet',
                          account=account,
                          csrf_token=generate_csrf_token)


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    result, status_code = api_request('POST', '/saas/account/change-password', data={
        'current_password': current_password,
        'new_password': new_password
    })
    
    if status_code == 200:
        flash('Password changed successfully.', 'success')
    else:
        flash(result.get('detail', 'Failed to change password.'), 'error')
    
    return redirect(url_for('dashboard.settings'))


@bp.route('/go-to-app')
@login_required
def go_to_app():
    """Redirect to ERP application"""
    erp_url = current_app.config.get('ERP_URL', 'http://localhost:5000')
    access_token = session.get('access_token')
    
    # Redirect with token for auto-login
    return redirect(f"{erp_url}/auto-login?token={access_token}")
