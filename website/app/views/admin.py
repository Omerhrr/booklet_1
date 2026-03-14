"""
Admin Views - Website Administration
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import api_request, generate_csrf_token, admin_required
from datetime import datetime

bp = Blueprint('admin', __name__)


@bp.route('')
@bp.route('/')
@admin_required
def index():
    """Admin dashboard"""
    # Get stats
    stats_result, _ = api_request('GET', '/saas/admin/stats')
    stats = stats_result.get('stats', {})
    
    # Get recent registrations
    registrations_result, _ = api_request('GET', '/saas/admin/registrations?limit=5')
    registrations = registrations_result.get('registrations', [])
    
    # Get recent contact submissions
    contacts_result, _ = api_request('GET', '/saas/contact?limit=5')
    contacts = contacts_result.get('submissions', [])
    
    return render_template('admin/index.html',
                          title='Admin Dashboard - Booklet',
                          stats=stats,
                          registrations=registrations,
                          contacts=contacts,
                          csrf_token=generate_csrf_token)


# ==================== BLOG MANAGEMENT ====================

@bp.route('/blog')
@admin_required
def blog_list():
    """List all blog posts"""
    result, _ = api_request('GET', '/saas/blog?all=true')
    posts = result.get('posts', [])
    
    return render_template('admin/blog/index.html',
                          title='Blog Management - Admin',
                          posts=posts,
                          csrf_token=generate_csrf_token)


@bp.route('/blog/new', methods=['GET', 'POST'])
@admin_required
def blog_new():
    """Create new blog post"""
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'slug': request.form.get('slug'),
            'excerpt': request.form.get('excerpt'),
            'content': request.form.get('content'),
            'category': request.form.get('category'),
            'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else [],
            'is_published': request.form.get('is_published') == 'on',
            'meta_title': request.form.get('meta_title'),
            'meta_description': request.form.get('meta_description')
        }
        
        result, status_code = api_request('POST', '/saas/blog', data=data)
        
        if status_code == 200:
            flash('Blog post created successfully.', 'success')
            return redirect(url_for('admin.blog_list'))
        else:
            flash(result.get('detail', 'Failed to create post.'), 'error')
    
    return render_template('admin/blog/form.html',
                          title='New Blog Post - Admin',
                          post=None,
                          csrf_token=generate_csrf_token)


@bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@admin_required
def blog_edit(post_id):
    """Edit blog post"""
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'slug': request.form.get('slug'),
            'excerpt': request.form.get('excerpt'),
            'content': request.form.get('content'),
            'category': request.form.get('category'),
            'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else [],
            'is_published': request.form.get('is_published') == 'on',
            'meta_title': request.form.get('meta_title'),
            'meta_description': request.form.get('meta_description')
        }
        
        result, status_code = api_request('PUT', f'/saas/blog/{post_id}', data=data)
        
        if status_code == 200:
            flash('Blog post updated successfully.', 'success')
            return redirect(url_for('admin.blog_list'))
        else:
            flash(result.get('detail', 'Failed to update post.'), 'error')
    
    # Get post
    result, _ = api_request('GET', f'/saas/blog/id/{post_id}')
    post = result.get('post', {})
    
    return render_template('admin/blog/form.html',
                          title='Edit Blog Post - Admin',
                          post=post,
                          csrf_token=generate_csrf_token)


@bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@admin_required
def blog_delete(post_id):
    """Delete blog post"""
    result, status_code = api_request('DELETE', f'/saas/blog/{post_id}')
    
    if status_code == 200:
        flash('Blog post deleted.', 'success')
    else:
        flash(result.get('detail', 'Failed to delete post.'), 'error')
    
    return redirect(url_for('admin.blog_list'))


# ==================== PLAN MANAGEMENT ====================

@bp.route('/plans')
@admin_required
def plans_list():
    """List and manage subscription plans"""
    result, _ = api_request('GET', '/saas/plans')
    plans = result.get('plans', [])
    
    return render_template('admin/plans/index.html',
                          title='Plans Management - Admin',
                          plans=plans,
                          csrf_token=generate_csrf_token)


@bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@admin_required
def plan_edit(plan_id):
    """Edit subscription plan"""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'max_branches': request.form.get('max_branches', type=int),
            'max_users': request.form.get('max_users', type=int),
            'includes_agents': request.form.get('includes_agents') == 'on',
            'monthly_price': request.form.get('monthly_price', type=float),
            'yearly_price': request.form.get('yearly_price', type=float),
            'features': request.form.get('features', '').split('\n') if request.form.get('features') else [],
            'is_active': request.form.get('is_active') == 'on',
            'display_order': request.form.get('display_order', type=int, default=0)
        }
        
        result, status_code = api_request('PUT', f'/saas/plans/{plan_id}', data=data)
        
        if status_code == 200:
            flash('Plan updated successfully.', 'success')
            return redirect(url_for('admin.plans_list'))
        else:
            flash(result.get('detail', 'Failed to update plan.'), 'error')
    
    # Get plan
    result, _ = api_request('GET', f'/saas/plans/{plan_id}')
    plan = result.get('plan', {})
    
    return render_template('admin/plans/form.html',
                          title='Edit Plan - Admin',
                          plan=plan,
                          csrf_token=generate_csrf_token)


# ==================== USER MANAGEMENT ====================

@bp.route('/users')
@admin_required
def users_list():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    
    params = {'page': page}
    if search:
        params['search'] = search
    
    result, _ = api_request('GET', '/saas/admin/users', params=params)
    users = result.get('users', [])
    total = result.get('total', 0)
    
    return render_template('admin/users/index.html',
                          title='Users Management - Admin',
                          users=users,
                          page=page,
                          total=total,
                          search=search,
                          csrf_token=generate_csrf_token)


@bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail"""
    result, _ = api_request('GET', f'/saas/admin/users/{user_id}')
    user = result.get('user', {})
    
    return render_template('admin/users/detail.html',
                          title='User Details - Admin',
                          user=user,
                          csrf_token=generate_csrf_token)


# ==================== CONTENT MANAGEMENT ====================

@bp.route('/content')
@admin_required
def content_list():
    """Website content management"""
    result, _ = api_request('GET', '/saas/content')
    content = result.get('content', {})
    
    return render_template('admin/content/index.html',
                          title='Content Management - Admin',
                          content=content,
                          csrf_token=generate_csrf_token)


@bp.route('/content/<section>', methods=['GET', 'POST'])
@admin_required
def content_edit(section):
    """Edit website content section"""
    if request.method == 'POST':
        data = {}
        for key in request.form:
            if key != 'csrf_token':
                data[key] = request.form.get(key)
        
        result, status_code = api_request('PUT', f'/saas/content/{section}', data=data)
        
        if status_code == 200:
            flash('Content updated successfully.', 'success')
            return redirect(url_for('admin.content_list'))
        else:
            flash(result.get('detail', 'Failed to update content.'), 'error')
    
    # Get content
    result, _ = api_request('GET', f'/saas/content/{section}')
    content = result.get('content', {})
    
    return render_template('admin/content/form.html',
                          title=f'Edit {section.title()} - Admin',
                          section=section,
                          content=content,
                          csrf_token=generate_csrf_token)


# ==================== CONTACT SUBMISSIONS ====================

@bp.route('/contacts')
@admin_required
def contacts_list():
    """List contact submissions"""
    status = request.args.get('status')
    
    params = {}
    if status:
        params['status'] = status
    
    result, _ = api_request('GET', '/saas/contact', params=params)
    submissions = result.get('submissions', [])
    
    return render_template('admin/contacts/index.html',
                          title='Contact Submissions - Admin',
                          submissions=submissions,
                          status_filter=status,
                          csrf_token=generate_csrf_token)


@bp.route('/contacts/<int:contact_id>/reply', methods=['POST'])
@admin_required
def contact_reply(contact_id):
    """Reply to contact submission"""
    data = {
        'message': request.form.get('message')
    }
    
    result, status_code = api_request('POST', f'/saas/contact/{contact_id}/reply', data=data)
    
    if status_code == 200:
        flash('Reply sent successfully.', 'success')
    else:
        flash(result.get('detail', 'Failed to send reply.'), 'error')
    
    return redirect(url_for('admin.contacts_list'))


@bp.route('/contacts/<int:contact_id>/status', methods=['POST'])
@admin_required
def contact_status(contact_id):
    """Update contact submission status"""
    status = request.form.get('status')
    
    result, status_code = api_request('PUT', f'/saas/contact/{contact_id}', data={'status': status})
    
    if status_code == 200:
        flash('Status updated.', 'success')
    else:
        flash(result.get('detail', 'Failed to update status.'), 'error')
    
    return redirect(url_for('admin.contacts_list'))
