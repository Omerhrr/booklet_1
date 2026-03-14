"""
Audit Log Views - View System Activity
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import api_request, login_required, permission_required
from datetime import date

bp = Blueprint('audit', __name__, url_prefix='/audit')


@bp.route('')
@login_required
@permission_required('settings:view')
def audit_logs():
    """List audit logs with filters"""
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')
    status = request.args.get('status')
    
    # Build params
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if user_id:
        params['user_id'] = user_id
    if action:
        params['action'] = action
    if resource_type:
        params['resource_type'] = resource_type
    if status:
        params['status'] = status
    
    # Get audit logs
    logs, status_code = api_request('GET', '/audit-logs', params=params if params else None)
    
    # Ensure logs is a list
    if not isinstance(logs, list):
        logs = []
    
    # Get available actions for filter dropdown
    actions_response, _ = api_request('GET', '/audit-logs/actions')
    available_actions = actions_response.get('actions', []) if isinstance(actions_response, dict) else []
    
    # Get summary
    summary, _ = api_request('GET', '/audit-logs/summary', params={'start_date': start_date, 'end_date': end_date} if start_date or end_date else None)
    if not isinstance(summary, dict):
        summary = {}
    
    # Get users for filter
    users, _ = api_request('GET', '/settings/users')
    if not isinstance(users, list):
        users = []
    
    return render_template('audit/logs.html',
                          title='Audit Logs',
                          logs=logs,
                          available_actions=available_actions,
                          summary=summary,
                          users=users,
                          filters={
                              'start_date': start_date,
                              'end_date': end_date,
                              'user_id': user_id,
                              'action': action,
                              'resource_type': resource_type,
                              'status': status
                          })


@bp.route('/<int:log_id>')
@login_required
@permission_required('settings:view')
def log_detail(log_id):
    """View audit log detail"""
    log, status_code = api_request('GET', f'/audit-logs/{log_id}')
    
    if status_code != 200 or not isinstance(log, dict):
        flash('Audit log not found', 'error')
        return redirect(url_for('audit.audit_logs'))
    
    return render_template('audit/detail.html',
                          title=f'Audit Log #{log_id}',
                          log=log)


@bp.route('/resource/<resource_type>/<int:resource_id>')
@login_required
@permission_required('settings:view')
def resource_history(resource_type, resource_id):
    """View audit history for a specific resource"""
    logs, status_code = api_request('GET', f'/audit-logs/resource/{resource_type}/{resource_id}')
    
    if not isinstance(logs, list):
        logs = []
    
    return render_template('audit/resource_history.html',
                          title=f'{resource_type} History',
                          logs=logs,
                          resource_type=resource_type,
                          resource_id=resource_id)


@bp.route('/user/<int:user_id>')
@login_required
@permission_required('settings:view')
def user_history(user_id):
    """View audit history for a specific user"""
    logs, status_code = api_request('GET', f'/audit-logs/user/{user_id}')
    
    if not isinstance(logs, list):
        logs = []
    
    # Get user info
    users, _ = api_request('GET', '/settings/users')
    user = None
    if isinstance(users, list):
        user = next((u for u in users if u.get('id') == user_id), None)
    
    return render_template('audit/user_history.html',
                          title=f'User Activity',
                          logs=logs,
                          user=user)


@bp.route('/login-history')
@login_required
@permission_required('settings:view')
def login_history():
    """View recent login activity"""
    logs, status_code = api_request('GET', '/audit-logs/recent-logins')
    
    if not isinstance(logs, list):
        logs = []
    
    return render_template('audit/login_history.html',
                          title='Login History',
                          logs=logs)
