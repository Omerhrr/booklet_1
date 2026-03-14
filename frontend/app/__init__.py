"""
Flask Frontend Application
"""
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# Initialize app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['BACKEND_URL'] = os.getenv('BACKEND_URL', 'http://localhost:8000')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CSRF Protection - Configure for HTMX
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens
csrf = CSRFProtect(app)


# ==================== HELPERS ====================

def get_backend_url(endpoint):
    """Get full backend URL"""
    return f"{app.config['BACKEND_URL']}/api/v1{endpoint}"


def api_request(method, endpoint, data=None, params=None, include_auth=True):
    """Make request to backend API"""
    url = get_backend_url(endpoint)
    headers = {'Content-Type': 'application/json'}
    
    # Build cookies dict
    cookies = {}
    if include_auth and 'access_token' in session:
        headers['Authorization'] = f"Bearer {session['access_token']}"
        cookies['access_token'] = session.get('access_token')
        
        # Include selected_branch_id cookie for branch switching (for admins)
        if 'selected_branch_id' in session:
            cookies['selected_branch_id'] = str(session['selected_branch_id'])
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, cookies=cookies)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, cookies=cookies)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, cookies=cookies)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, cookies=cookies)
        else:
            return None, "Invalid method"
        
        # Try to parse as JSON, handle HTML error pages
        if response.content:
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return response.json(), response.status_code
            else:
                # Response is not JSON (probably HTML error page)
                return {'error': f'Server returned non-JSON response (status {response.status_code})', 
                        'detail': response.text[:500] if response.text else 'No response content'}, response.status_code
        return {}, response.status_code
    except requests.exceptions.ConnectionError:
        return None, "Backend connection error"
    except Exception as e:
        return None, str(e)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def permission_required(*permissions):
    """Decorator to require specific permissions.
    User must have at least one of the specified permissions.
    Superusers bypass this check.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Superusers have all permissions
            if session.get('is_superuser', False):
                return f(*args, **kwargs)
            
            # Check if user has any of the required permissions
            user_permissions = session.get('permissions', [])
            if not user_permissions:
                user_permissions = []
            
            # Check if user has at least one required permission
            has_access = any(perm in user_permissions for perm in permissions)
            
            if not has_access:
                from flask import abort
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def plan_feature_required(feature):
    """Decorator to require a specific plan feature.
    
    Plan limits apply to ALL users including superusers.
    This enforces subscription-based feature restrictions.
    
    Args:
        feature: Feature name (agents, ai, analytics, hr, budgets, fixed_assets)
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            plan_limits = session.get('plan_limits', {
                'max_branches': 1,
                'max_users': 5,
                'includes_agents': False,
                'slug': 'basic'
            })
            
            plan_slug = plan_limits.get('slug', 'basic')
            
            # Feature availability by plan slug
            features = {
                'agents': plan_limits.get('includes_agents', False),
                'ai': plan_limits.get('includes_agents', False),  # AI requires agents
                'analytics': plan_slug in ['premium', 'advanced', 'enterprise'],
                'hr': plan_slug in ['premium', 'advanced', 'enterprise'],
                'budgets': plan_slug in ['premium', 'advanced', 'enterprise'],
                'fixed_assets': plan_slug in ['premium', 'advanced', 'enterprise'],
            }
            
            has_feature = features.get(feature, True)
            
            if not has_feature:
                # Return 403 with upgrade message
                from flask import abort
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current user from session/API"""
    if 'access_token' not in session:
        return None
    
    # Cache user in session
    if 'user_data' in session:
        return session['user_data']
    
    user_data, status = api_request('GET', '/auth/me')
    if status == 200:
        session['user_data'] = user_data
        return user_data
    return None


@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    plan_limits = session.get('plan_limits', {
        'max_branches': 1,
        'max_users': 5,
        'includes_agents': False,
        'slug': 'basic'
    })
    
    def has_plan_feature(feature):
        """Check if the current plan includes a feature
        
        Plan restrictions apply to ALL users including superusers.
        Superuser only bypasses permission checks, NOT plan limits.
        """
        plan_slug = plan_limits.get('slug', 'basic')
        
        # Feature availability by plan
        features = {
            'agents': plan_limits.get('includes_agents', False),
            'ai': plan_limits.get('includes_agents', False),  # AI requires agents
            'analytics': plan_slug in ['premium', 'advanced', 'enterprise'],
            'hr': plan_slug in ['premium', 'advanced', 'enterprise'],
            'budgets': plan_slug in ['premium', 'advanced', 'enterprise'],
            'fixed_assets': plan_slug in ['premium', 'advanced', 'enterprise'],
        }
        
        return features.get(feature, True)
    
    def can_create_branch():
        """Check if business can create more branches"""
        branches = session.get('branches', [])
        return len(branches) < plan_limits.get('max_branches', 1)
    
    def can_create_user():
        """Check if business can create more users"""
        # This is approximate - actual count should come from API
        return True  # Will be validated on backend
    
    def has_permission(perm):
        """Check if user has a specific permission.
        
        Note: Plan restrictions are enforced separately via has_plan_feature().
        Permissions are already filtered during login based on plan.
        Superusers still respect plan limits.
        """
        return perm in session.get('permissions', [])
    
    def has_permission_or_superuser(perm):
        """Check permission with superuser bypass (for non-plan-restricted features only).
        
        WARNING: Use has_permission() for premium features as plan limits apply to ALL users.
        """
        return perm in session.get('permissions', []) or session.get('is_superuser', False)
    
    def get_business_id():
        """Get current business ID from session"""
        return session.get('business_id')
    
    return {
        'current_user': get_current_user(),
        'app_name': 'Booklet ERP',
        'current_year': __import__('datetime').datetime.now().year,
        'has_permission': has_permission,
        'has_permission_or_superuser': has_permission_or_superuser,
        'debug_permissions': lambda: session.get('permissions', []),
        'plan_limits': plan_limits,
        'has_plan_feature': has_plan_feature,
        'can_create_branch': can_create_branch,
        'can_create_user': can_create_user,
        'get_business_id': get_business_id,
        'business_id': session.get('business_id'),
    }


# Currency symbol mapping
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


@app.template_filter('currency')
def currency_filter(value, symbol=None):
    """Format number as currency using branch currency with proper symbol"""
    # Get currency code from session
    currency_code = session.get('branch_currency', 'USD')
    
    # If symbol not provided, get the proper symbol for the currency code
    if symbol is None:
        # Check if branch_currency is already a symbol or a code
        if currency_code in CURRENCY_SYMBOLS:
            symbol = CURRENCY_SYMBOLS[currency_code]
        elif len(currency_code) == 1 or currency_code not in ['USD', 'NGN', 'EUR', 'GBP', 'JPY', 'CNY', 'INR', 'AUD', 'CAD', 'CHF', 'ZAR', 'KES', 'GHS', 'AED', 'SAR']:
            # Already a symbol or unknown code, use as-is
            symbol = currency_code
        else:
            symbol = currency_code
    
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


@app.template_filter('to_float')
def to_float_filter(value, default=0):
    """Convert value to float, with default for invalid values"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


@app.template_filter('date')
def date_filter(value, format='%Y-%m-%d'):
    """Format date"""
    try:
        if value:
            return __import__('datetime').datetime.strptime(str(value), '%Y-%m-%d').strftime(format)
    except ValueError:
        pass
    return value


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('shared/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('shared/500.html'), 500


@app.errorhandler(403)
def forbidden(error):
    return render_template('shared/403.html'), 403


# ==================== REGISTER BLUEPRINTS ====================

from app.views import auth, dashboard, crm, inventory, sales, purchases, accounting, hr, banking, reports, settings, expenses, other_incomes, budgets, fixed_assets, cashbook, audit, analytics, ai, agents

app.register_blueprint(auth.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(crm.bp)
app.register_blueprint(inventory.bp)
app.register_blueprint(sales.bp)
app.register_blueprint(purchases.bp)
app.register_blueprint(accounting.bp)
app.register_blueprint(hr.bp)
app.register_blueprint(banking.bp)
app.register_blueprint(reports.bp)
app.register_blueprint(settings.bp)
app.register_blueprint(expenses.bp)
app.register_blueprint(other_incomes.bp)
app.register_blueprint(budgets.bp)
app.register_blueprint(fixed_assets.fixed_assets_bp)
app.register_blueprint(cashbook.cashbook_bp)
app.register_blueprint(audit.bp)
app.register_blueprint(analytics.bp)
app.register_blueprint(ai.bp)
app.register_blueprint(agents.bp)


# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    """Root route"""
    if 'access_token' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@app.route('/auto-login')
def auto_login():
    """Auto-login using JWT token from website"""
    token = request.args.get('token')
    next_page = request.args.get('next')
    
    if not token:
        return redirect(url_for('auth.login'))
    
    # Verify token with backend API
    url = get_backend_url('/saas/auth/verify-token')
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json={'token': token}, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            plan = data.get('plan', {})
            access_token = data.get('access_token')
            
            # Set session
            session['access_token'] = access_token
            session['username'] = user.get('username') or user.get('email')
            session['user_data'] = user
            session['is_superuser'] = user.get('is_superuser', False)
            session['business_id'] = user.get('business_id')  # Store business_id
            
            # Store plan limits for feature restrictions
            plan_slug = plan.get('slug', 'basic')
            session['plan_limits'] = {
                'max_branches': plan.get('max_branches', 1),
                'max_users': plan.get('max_users', 5),
                'includes_agents': plan.get('includes_agents', False),
                'slug': plan_slug
            }
            
            # Fetch user permissions (already filtered by plan in backend)
            perms_response = requests.get(
                get_backend_url('/auth/permissions'),
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if perms_response.status_code == 200:
                perms_data = perms_response.json()
                # Store permissions (already filtered by backend based on plan)
                session['permissions'] = perms_data.get('permissions', [])
                
                # Update business_id and plan_slug from API response if available
                api_business_id = perms_data.get('business_id')
                api_plan_slug = perms_data.get('plan_slug')
                
                if api_business_id:
                    session['business_id'] = api_business_id
                
                if api_plan_slug:
                    session['plan_limits']['slug'] = api_plan_slug
            
            # Fetch branches for branch selector
            branches_response = requests.get(
                get_backend_url('/settings/branches'),
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if branches_response.status_code == 200:
                branches = branches_response.json()
                if branches and isinstance(branches, list):
                    session['branches'] = branches
                    default_branch = next(
                        (b for b in branches if b.get('is_default')), 
                        branches[0] if branches else None
                    )
                    if default_branch:
                        session['selected_branch_id'] = default_branch.get('id')
                        session['selected_branch_name'] = default_branch.get('name')
                        session['branch_currency'] = default_branch.get('currency', '$')
            
            # Fetch business settings
            business_response = requests.get(
                get_backend_url('/settings/business'),
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if business_response.status_code == 200:
                business_settings = business_response.json()
                session['business_name'] = business_settings.get('name', 'Company')
            
            # Redirect to next page or dashboard
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            # Token verification failed
            return redirect(url_for('auth.login'))
    
    except Exception as e:
        print(f"Auto-login error: {e}")
        return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
