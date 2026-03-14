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
    sub_result, _ = api_request('GET', f'/saas/subscription?business_id={business_id}')
    subscription = sub_result.get('subscription', {})
    
    # Get business info (use /settings/business without ID - backend uses current user's business)
    business_result, _ = api_request('GET', '/settings/business')
    business = business_result if business_result else {}
    
    # Get recent payments
    payments_result, _ = api_request('GET', f'/saas/payments?business_id={business_id}&limit=5')
    payments = payments_result.get('payments', [])
    
    # Get usage stats
    usage_result, _ = api_request('GET', f'/saas/usage?business_id={business_id}')
    usage = usage_result.get('usage', {})
    
    # Get software logins (users for this business)
    logins_result, _ = api_request('GET', f'/saas/software-logins?business_id={business_id}')
    software_logins = logins_result.get('logins', [])
    
    return render_template('dashboard/index.html',
                          title='Dashboard - Booklet',
                          subscription=subscription,
                          business=business,
                          payments=payments,
                          usage=usage,
                          software_logins=software_logins,
                          csrf_token=generate_csrf_token)


@bp.route('/billing')
@login_required
def billing():
    """Billing and payment history"""
    business_id = session.get('business_id')
    
    # Get payments
    payments_result, _ = api_request('GET', f'/saas/payments?business_id={business_id}')
    payments = payments_result.get('payments', [])
    
    # Get subscription
    sub_result, _ = api_request('GET', f'/saas/subscription?business_id={business_id}')
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
    business_id = session.get('business_id')
    
    # Get current subscription
    sub_result, _ = api_request('GET', f'/saas/subscription?business_id={business_id}')
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
    business_id = session.get('business_id')
    
    if request.method == 'POST':
        plan_slug = request.form.get('plan_slug')
        billing_cycle = request.form.get('billing_cycle', 'monthly')
        
        result, status_code = api_request('POST', '/saas/subscription/upgrade', data={
            'plan_slug': plan_slug,
            'billing_cycle': billing_cycle,
            'business_id': business_id
        })
        
        if status_code == 200:
            flash('Subscription upgraded successfully!', 'success')
            return redirect(url_for('dashboard.subscription'))
        else:
            flash(result.get('detail', 'Failed to upgrade subscription.'), 'error')
    
    # Get current subscription
    sub_result, _ = api_request('GET', f'/saas/subscription?business_id={business_id}')
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
    business_id = session.get('business_id')
    
    result, status_code = api_request('POST', '/saas/subscription/cancel', data={
        'business_id': business_id
    })
    
    if status_code == 200:
        flash('Subscription cancelled. You can continue using Booklet until the end of your billing period.', 'success')
    else:
        flash(result.get('detail', 'Failed to cancel subscription.'), 'error')
    
    return redirect(url_for('dashboard.subscription'))


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Account settings"""
    business_id = session.get('business_id')
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'business_id': business_id
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
    account_result, _ = api_request('GET', f'/saas/account?business_id={business_id}')
    account = account_result.get('account', {})
    
    return render_template('dashboard/settings.html',
                          title='Account Settings - Booklet',
                          account=account,
                          csrf_token=generate_csrf_token)


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password"""
    business_id = session.get('business_id')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    result, status_code = api_request('POST', '/saas/account/change-password', data={
        'current_password': current_password,
        'new_password': new_password,
        'business_id': business_id
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
