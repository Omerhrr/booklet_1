"""
Blog Views - Blog Listing and Posts
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import api_request, generate_csrf_token

bp = Blueprint('blog', __name__)


@bp.route('')
@bp.route('/')
def index():
    """Blog listing page"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    tag = request.args.get('tag')
    
    params = {'page': page}
    if category:
        params['category'] = category
    if tag:
        params['tag'] = tag
    
    result, _ = api_request('GET', '/saas/blog', params=params)
    posts = result.get('posts', [])
    total = result.get('total', 0)
    per_page = result.get('per_page', 10)
    
    # Get categories for sidebar
    categories_result, _ = api_request('GET', '/saas/blog/categories')
    categories = categories_result.get('categories', [])
    
    # Get recent posts for sidebar
    recent_result, _ = api_request('GET', '/saas/blog?published_only=true&limit=5')
    recent_posts = recent_result.get('posts', [])
    
    return render_template('blog/index.html',
                          title='Blog - Booklet',
                          posts=posts,
                          categories=categories,
                          recent_posts=recent_posts,
                          current_category=category,
                          current_tag=tag,
                          page=page,
                          total=total,
                          per_page=per_page,
                          csrf_token=generate_csrf_token)


@bp.route('/<slug>')
def post(slug):
    """Individual blog post"""
    result, status_code = api_request('GET', f'/saas/blog/{slug}')
    
    if status_code != 200:
        flash('Post not found.', 'error')
        return redirect(url_for('blog.index'))
    
    post = result.get('post', {})
    
    # Get related posts
    related_result, _ = api_request('GET', '/saas/blog/related', params={
        'post_id': post.get('id'),
        'limit': 3
    })
    related_posts = related_result.get('posts', [])
    
    return render_template('blog/post.html',
                          title=f"{post.get('title', 'Blog Post')} - Booklet",
                          post=post,
                          related_posts=related_posts,
                          csrf_token=generate_csrf_token)


@bp.route('/category/<category>')
def by_category(category):
    """Posts by category"""
    return redirect(url_for('blog.index', category=category))


@bp.route('/tag/<tag>')
def by_tag(tag):
    """Posts by tag"""
    return redirect(url_for('blog.index', tag=tag))
