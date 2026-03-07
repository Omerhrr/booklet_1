"""
Booklet SaaS Website - Marketing, Registration, Billing
"""
from flask import Flask, session, g, request, redirect, url_for, flash, jsonify, current_app
from flask_bcrypt import Bcrypt
import httpx
import os
from datetime import datetime
from functools import wraps

# Initialize extensions
bcrypt = Bcrypt()


def create_app():
    """Create Flask application factory"""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'booklet-website-secret-key-change-in-production')
    app.config['API_BASE_URL'] = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    app.config['ERP_URL'] = os.environ.get('ERP_URL', 'http://localhost:5000')
    
    # Initialize extensions
    bcrypt.init_app(app)
    
    # Register blueprints
    from app.views.public import bp as public_bp
    from app.views.auth import bp as auth_bp
    from app.views.dashboard import bp as dashboard_bp
    from app.views.blog import bp as blog_bp
    from app.views.admin import bp as admin_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Template filters
    @app.template_filter('currency')
    def currency_filter(value, symbol='$'):
        """Format number as currency"""
        try:
            return f"{symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return f"{symbol}0.00"
    
    @app.template_filter('date')
    def date_filter(value, format='%b %d, %Y'):
        """Format date"""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime(format)
        return value
    
    @app.template_filter('truncate_words')
    def truncate_words_filter(value, num=20):
        """Truncate text to specified number of words"""
        if not value:
            return ''
        words = value.split()
        if len(words) <= num:
            return value
        return ' '.join(words[:num]) + '...'
    
    # Context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.context_processor
    def inject_settings():
        return {
            'site_name': 'Booklet',
            'site_tagline': 'Smart Business Management',
            'erp_url': app.config['ERP_URL']
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return app.render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return app.render_template('errors/500.html'), 500
    
    return app


# ==================== API HELPER ====================

def api_request(method, endpoint, data=None, params=None, files=None):
    """Make API request to backend"""
    api_url = current_app.config.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    url = f"{api_url}{endpoint}"
    
    headers = {}
    if session.get('access_token'):
        headers['Authorization'] = f"Bearer {session.get('access_token')}"
    
    try:
        if method.upper() == 'GET':
            response = httpx.get(url, params=params, headers=headers, timeout=30.0)
        elif method.upper() == 'POST':
            if files:
                response = httpx.post(url, data=data, files=files, headers=headers, timeout=30.0)
            else:
                response = httpx.post(url, json=data, headers=headers, timeout=30.0)
        elif method.upper() == 'PUT':
            response = httpx.put(url, json=data, headers=headers, timeout=30.0)
        elif method.upper() == 'DELETE':
            response = httpx.delete(url, headers=headers, timeout=30.0)
        else:
            return None, 405
        
        return response.json() if response.content else {}, response.status_code
    except httpx.RequestError as e:
        print(f"API Request Error: {e}")
        return {'detail': 'Unable to connect to server'}, 503
    except Exception as e:
        print(f"API Error: {e}")
        return {'detail': 'An error occurred'}, 500


# ==================== DECORATORS ====================

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require user to be admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        if not session.get('is_website_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('public.index'))
        return f(*args, **kwargs)
    return decorated_function


def subscription_required(f):
    """Require active subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        if not session.get('subscription_active'):
            flash('Active subscription required.', 'error')
            return redirect(url_for('dashboard.subscription'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== HELPERS ====================

def get_current_user():
    """Get current logged in user"""
    if not session.get('user_id'):
        return None
    return {
        'id': session.get('user_id'),
        'email': session.get('email'),
        'name': session.get('name'),
        'is_website_admin': session.get('is_website_admin', False),
        'business_id': session.get('business_id'),
        'subscription_active': session.get('subscription_active', False)
    }


def get_plans():
    """Get all available subscription plans"""
    result, _ = api_request('GET', '/saas/plans')
    return result.get('plans', [])


def get_blog_posts(published_only=True, limit=None):
    """Get blog posts"""
    params = {'published_only': published_only}
    if limit:
        params['limit'] = limit
    result, _ = api_request('GET', '/saas/blog', params=params)
    return result.get('posts', [])


# ==================== CSRF PROTECTION ====================

def generate_csrf_token():
    """Generate CSRF token"""
    if '_csrf_token' not in session:
        import secrets
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token):
    """Validate CSRF token"""
    return token == session.get('_csrf_token')


# Create a Flask app instance for the module level functions
app = create_app()
