"""
AI Assistant Views - Chat Interface and Settings
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, abort
from app import api_request, login_required, permission_required
import json

bp = Blueprint('ai', __name__, url_prefix='/ai')


@bp.before_request
@login_required
def check_ai_feature():
    """Check if AI feature is available for the current plan"""
    plan_limits = session.get('plan_limits', {'slug': 'basic', 'includes_agents': False})
    plan_slug = plan_limits.get('slug', 'basic')
    includes_agents = plan_limits.get('includes_agents', False)
    if plan_slug not in ['premium', 'advanced', 'enterprise'] and not includes_agents:
        abort(403)


@bp.route('')
@login_required
def index():
    """AI assistant main page - chat interface"""
    # Get current conversation or create new
    conversation_id = request.args.get('conversation', type=int)
    
    # Get user's conversations
    conversations, _ = api_request('GET', '/ai/conversations')
    
    # Get providers for info
    providers, _ = api_request('GET', '/ai/providers')
    
    return render_template('ai/chat.html',
                          title='AI Assistant',
                          conversations=conversations.get('conversations', []) if isinstance(conversations, dict) else [],
                          current_conversation=conversation_id,
                          providers=providers.get('providers', []) if isinstance(providers, dict) else [])


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """AI settings configuration (admin only)"""
    if request.method == 'POST':
        # Get form data and clean up empty strings
        api_key = request.form.get('api_key', '').strip()
        
        data = {
            'provider': request.form.get('provider', 'zai'),
            'api_endpoint': request.form.get('api_endpoint') or None,
            'model_name': request.form.get('model_name') or None,
            'max_tokens': int(request.form.get('max_tokens', 4096)),
            'temperature': float(request.form.get('temperature', 0.7)),
            'is_enabled': request.form.get('is_enabled') == 'on',
            'allow_data_access': request.form.get('allow_data_access') == 'on',
            'daily_request_limit': int(request.form.get('daily_request_limit', 1000)),
            'monthly_request_limit': int(request.form.get('monthly_request_limit', 30000))
        }
        
        # Only include api_key if provided (not empty)
        if api_key:
            data['api_key'] = api_key
        
        result, status_code = api_request('POST', '/ai/settings', data=data)
        
        if status_code == 200:
            flash('AI settings saved successfully', 'success')
        else:
            error_msg = result.get('detail', 'Failed to save settings')
            if status_code == 403:
                error_msg = 'You need AI configuration permissions. Click "Fix Permissions" below.'
            elif status_code == 400:
                # Parse validation error
                if isinstance(result.get('detail'), list):
                    errors = [e.get('msg', str(e)) for e in result.get('detail', [])]
                    error_msg = 'Validation error: ' + ', '.join(errors)
                else:
                    error_msg = result.get('detail', 'Invalid data provided')
            flash(error_msg, 'error')
    
    # Get current settings
    settings_data, status_code = api_request('GET', '/ai/settings')
    
    # If 403, try to fix permissions automatically
    permission_error = False
    if status_code == 403:
        permission_error = True
        # Try fixing permissions
        fix_result, _ = api_request('POST', '/ai/fix-permissions')
        if fix_result.get('success'):
            # Retry getting settings
            settings_data, status_code = api_request('GET', '/ai/settings')
            if status_code == 200:
                permission_error = False
                flash('Permissions fixed automatically. You can now configure AI settings.', 'success')
    
    # Get available providers
    providers, _ = api_request('GET', '/ai/providers')
    
    return render_template('ai/settings.html',
                          title='AI Settings',
                          settings=settings_data if isinstance(settings_data, dict) else {},
                          providers=providers.get('providers', []) if isinstance(providers, dict) else [],
                          permission_error=permission_error)


@bp.route('/usage')
@login_required
def usage():
    """AI usage statistics"""
    days = request.args.get('days', 30, type=int)
    
    usage_data, _ = api_request('GET', f'/ai/usage?days={days}')
    
    return render_template('ai/usage.html',
                          title='AI Usage',
                          usage=usage_data if isinstance(usage_data, dict) else {},
                          days=days)


# ==================== API PROXY ENDPOINTS ====================

@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Proxy chat requests to backend API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        # Ensure message is a string
        message = data.get('message')
        if not isinstance(message, str):
            return jsonify({'error': 'Message must be a string'}), 400
        
        # Clean the data
        clean_data = {
            'message': str(message).strip(),
            'conversation_id': data.get('conversation_id')
        }
        
        result, status_code = api_request('POST', '/ai/chat', data=clean_data)
        
        # Debug logging
        current_app.logger.info(f"AI Chat - Status: {status_code}, Result type: {type(result)}")
        if isinstance(result, dict) and 'error' in result:
            current_app.logger.error(f"AI Chat Error: {result}")
        
        # Handle different response types
        if result is None:
            return jsonify({'error': 'No response from AI service'}), 502
        
        if isinstance(result, dict):
            # If there's an error from backend, pass it through
            if 'error' in result and status_code != 200:
                return jsonify(result), status_code
            return jsonify(result), status_code
        else:
            return jsonify({'error': 'Invalid response from AI service'}), 502
            
    except Exception as e:
        current_app.logger.exception(f"AI Chat Exception: {str(e)}")
        return jsonify({'error': f'Failed to connect to AI service: {str(e)}'}), 500


@bp.route('/conversations')
@login_required
def get_conversations():
    """Get conversations list"""
    include_archived = request.args.get('archived', 'false').lower() == 'true'
    
    result, status_code = api_request('GET', f'/ai/conversations?include_archived={include_archived}')
    
    return jsonify(result), status_code


@bp.route('/conversations/<int:conversation_id>')
@login_required
def get_conversation(conversation_id):
    """Get conversation messages"""
    limit = request.args.get('limit', 50, type=int)
    
    result, status_code = api_request('GET', f'/ai/conversations/{conversation_id}?limit={limit}')
    
    return jsonify(result), status_code


@bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation"""
    result, status_code = api_request('DELETE', f'/ai/conversations/{conversation_id}')
    
    return jsonify(result), status_code


@bp.route('/conversations/<int:conversation_id>/archive', methods=['PATCH'])
@login_required
def archive_conversation(conversation_id):
    """Archive/unarchive a conversation"""
    result, status_code = api_request('PATCH', f'/ai/conversations/{conversation_id}/archive')
    
    return jsonify(result), status_code


@bp.route('/fix-permissions', methods=['POST'])
@login_required
def fix_permissions():
    """Fix AI permissions for current user"""
    result, status_code = api_request('POST', '/ai/fix-permissions')
    
    return jsonify(result), status_code
