"""
Public Views - Homepage, Pricing, Features, Contact
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import api_request, generate_csrf_token
from datetime import datetime

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    """Homepage - Marketing landing page"""
    # Get plans for pricing preview
    result, _ = api_request('GET', '/saas/plans')
    plans = result.get('plans', [])
    
    # Get featured blog posts
    blog_result, _ = api_request('GET', '/saas/blog?published_only=true&limit=3')
    posts = blog_result.get('posts', [])
    
    # Get website content
    content_result, _ = api_request('GET', '/saas/content')
    content = content_result.get('content', {})
    
    return render_template('public/index.html',
                          title='Booklet - Smart Business Management',
                          plans=plans,
                          posts=posts,
                          content=content,
                          csrf_token=generate_csrf_token)


@bp.route('/pricing')
def pricing():
    """Pricing page with plan comparison"""
    result, _ = api_request('GET', '/saas/plans')
    plans = result.get('plans', [])
    
    # Get FAQs
    faq_result, _ = api_request('GET', '/saas/content/faqs')
    faqs = faq_result.get('faqs', [])
    
    return render_template('public/pricing.html',
                          title='Pricing - Booklet',
                          plans=plans,
                          faqs=faqs,
                          csrf_token=generate_csrf_token)


@bp.route('/features')
def features():
    """Features page"""
    # Get features content
    result, _ = api_request('GET', '/saas/content/features')
    features = result.get('features', [])
    
    return render_template('public/features.html',
                          title='Features - Booklet',
                          features=features,
                          csrf_token=generate_csrf_token)


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with form"""
    if request.method == 'POST':
        # Validate CSRF
        if not request.form.get('csrf_token') == session.get('_csrf_token'):
            flash('Invalid request. Please try again.', 'error')
            return redirect(url_for('public.contact'))
        
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'subject': request.form.get('subject'),
            'message': request.form.get('message')
        }
        
        result, status_code = api_request('POST', '/saas/contact', data=data)
        
        if status_code == 200:
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('public.contact'))
        else:
            flash(result.get('detail', 'Failed to send message. Please try again.'), 'error')
    
    return render_template('public/contact.html',
                          title='Contact Us - Booklet',
                          csrf_token=generate_csrf_token)


@bp.route('/about')
def about():
    """About page"""
    return render_template('public/about.html',
                          title='About Us - Booklet',
                          csrf_token=generate_csrf_token)


@bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('public/privacy.html',
                          title='Privacy Policy - Booklet',
                          csrf_token=generate_csrf_token)


@bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('public/terms.html',
                          title='Terms of Service - Booklet',
                          csrf_token=generate_csrf_token)
