"""
Auth Views - Login, Register, Password Reset
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import api_request, generate_csrf_token, bcrypt
import secrets
from datetime import datetime
import httpx

bp = Blueprint('auth', __name__)


@bp.route('/auto-login', methods=['GET'])
def auto_login():
    """Auto-login with JWT token from ERP backend"""
    token = request.args.get('token')
    
    if not token:
        flash('Invalid login link.', 'error')
        return redirect(url_for('auth.login'))
    
    # Verify token with backend API
    result, status_code = api_request('POST', '/saas/auth/verify-token', data={
        'token': token
    })
    
    if status_code == 200:
        user = result.get('user', {})
        plan = result.get('plan', {})
        session.permanent = True
        
        # Set user session
        session['user_id'] = user.get('id')
        session['email'] = user.get('email')
        session['name'] = user.get('name')
        session['username'] = user.get('username')
        session['access_token'] = result.get('access_token')
        session['business_id'] = user.get('business_id')
        session['is_superuser'] = user.get('is_superuser', False)
        session['is_website_admin'] = user.get('is_website_admin', False)
        session['subscription_active'] = user.get('subscription_active', False)
        
        # Store plan limits for feature restrictions
        session['plan_limits'] = {
            'max_branches': plan.get('max_branches', 1),
            'max_users': plan.get('max_users', 5),
            'includes_agents': plan.get('includes_agents', False),
            'slug': plan.get('slug', 'basic')
        }
        
        flash(f'Welcome, {user.get("name", "User")}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    else:
        flash(result.get('detail', 'Invalid or expired login link.'), 'error')
        return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Validate CSRF
        if not request.form.get('csrf_token') == session.get('_csrf_token'):
            flash('Invalid request. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Call API to authenticate
        result, status_code = api_request('POST', '/saas/auth/login', data={
            'email': email,
            'password': password
        })
        
        if status_code == 200:
            # Set session
            user = result.get('user', {})
            session['user_id'] = user.get('id')
            session['email'] = user.get('email')
            session['name'] = user.get('name')
            session['access_token'] = result.get('access_token')
            session['business_id'] = user.get('business_id')
            session['is_website_admin'] = user.get('is_website_admin', False)
            session['subscription_active'] = user.get('subscription_active', False)
            
            flash(f'Welcome back, {user.get("name", "User")}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash(result.get('detail', 'Invalid email or password.'), 'error')
    
    return render_template('auth/login.html',
                          title='Login - Booklet',
                          csrf_token=generate_csrf_token)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page - Step 1: Account creation"""
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    
    # Get selected plan from URL
    plan_slug = request.args.get('plan', 'basic')
    
    # Get all plans
    result, _ = api_request('GET', '/saas/plans')
    plans = result.get('plans', [])
    selected_plan = next((p for p in plans if p.get('slug') == plan_slug), plans[0] if plans else None)
    
    if request.method == 'POST':
        # Validate CSRF
        if not request.form.get('csrf_token') == session.get('_csrf_token'):
            flash('Invalid request. Please try again.', 'error')
            return redirect(url_for('auth.register', plan=plan_slug))
        
        # Store registration data in session for step 2
        session['registration'] = {
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'name': request.form.get('name'),
            'plan_slug': request.form.get('plan_slug', plan_slug)
        }
        
        # Validate passwords match
        if request.form.get('password') != request.form.get('confirm_password'):
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register', plan=plan_slug))
        
        return redirect(url_for('auth.setup_business'))
    
    return render_template('auth/register.html',
                          title='Create Account - Booklet',
                          plans=plans,
                          selected_plan=selected_plan,
                          csrf_token=generate_csrf_token)


@bp.route('/setup-business', methods=['GET', 'POST'])
def setup_business():
    """Registration page - Step 2: Business setup"""
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    
    registration = session.get('registration')
    if not registration:
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        # Validate CSRF
        if not request.form.get('csrf_token') == session.get('_csrf_token'):
            flash('Invalid request. Please try again.', 'error')
            return redirect(url_for('auth.setup_business'))
        
        # Prepare registration data
        data = {
            'user': {
                'email': registration.get('email'),
                'password': registration.get('password'),
                'name': registration.get('name')
            },
            'business': {
                'name': request.form.get('business_name'),
                'type': request.form.get('business_type'),
                'currency': request.form.get('currency', 'USD'),
                'timezone': request.form.get('timezone', 'UTC'),
                'country': request.form.get('country', 'US')
            },
            'plan_slug': registration.get('plan_slug', 'basic'),
            'billing_cycle': request.form.get('billing_cycle', 'monthly')
        }
        
        # Call API to create business and user
        result, status_code = api_request('POST', '/saas/register', data=data)
        
        if status_code == 200:
            # Clear registration session
            session.pop('registration', None)
            
            # Set user session
            user = result.get('user', {})
            session['user_id'] = user.get('id')
            session['email'] = user.get('email')
            session['name'] = user.get('name')
            session['access_token'] = result.get('access_token')
            session['business_id'] = user.get('business_id')
            session['subscription_active'] = True
            
            flash('Account created successfully! Welcome to Booklet.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash(result.get('detail', 'Failed to create account. Please try again.'), 'error')
    
    # Get countries and currencies
    countries = [
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('NG', 'Nigeria'),
        ('KE', 'Kenya'),
        ('ZA', 'South Africa'),
        ('GH', 'Ghana'),
    ]
    
    currencies = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar ($)'),
        ('AUD', 'Australian Dollar ($)'),
        ('NGN', 'Nigerian Naira (₦)'),
        ('KES', 'Kenyan Shilling (KSh)'),
        ('ZAR', 'South African Rand (R)'),
        ('GHS', 'Ghanaian Cedi (₵)'),
    ]
    
    timezones = [
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time (US)'),
        ('America/Chicago', 'Central Time (US)'),
        ('America/Denver', 'Mountain Time (US)'),
        ('America/Los_Angeles', 'Pacific Time (US)'),
        ('Europe/London', 'London (GMT)'),
        ('Europe/Berlin', 'Berlin (CET)'),
        ('Africa/Lagos', 'Lagos (WAT)'),
        ('Africa/Nairobi', 'Nairobi (EAT)'),
    ]
    
    return render_template('auth/setup_business.html',
                          title='Setup Your Business - Booklet',
                          registration=registration,
                          countries=countries,
                          currencies=currencies,
                          timezones=timezones,
                          csrf_token=generate_csrf_token)


@bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('public.index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        result, status_code = api_request('POST', '/saas/auth/forgot-password', data={
            'email': email
        })
        
        if status_code == 200:
            flash('If an account with that email exists, you will receive a password reset link.', 'success')
        else:
            flash('If an account with that email exists, you will receive a password reset link.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html',
                          title='Forgot Password - Booklet',
                          csrf_token=generate_csrf_token)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page"""
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        result, status_code = api_request('POST', '/saas/auth/reset-password', data={
            'token': token,
            'password': password
        })
        
        if status_code == 200:
            flash('Password reset successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result.get('detail', 'Invalid or expired reset link.'), 'error')
    
    return render_template('auth/reset_password.html',
                          title='Reset Password - Booklet',
                          token=token,
                          csrf_token=generate_csrf_token)
