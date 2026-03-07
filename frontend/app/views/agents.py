"""
Agent Views - Automation, Audit, and Doc Wizard
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app import api_request, login_required, permission_required
from datetime import datetime
import json

bp = Blueprint('agents', __name__, url_prefix='/agents')


# ==================== AGENT DASHBOARD ====================

@bp.route('')
@login_required
def index():
    """Agent dashboard - overview of all agents"""
    # Get agent configurations
    configs, _ = api_request('GET', '/agents/configurations')
    
    # Get recent executions
    executions, _ = api_request('GET', '/agents/executions?limit=10')
    
    # Get open findings
    findings, _ = api_request('GET', '/agents/findings?status=open&limit=10')
    
    # Get agent types
    types, _ = api_request('GET', '/agents/types')
    
    return render_template('agents/index.html',
                          title='Agents',
                          configurations=configs.get('configurations', []),
                          executions=executions.get('executions', []),
                          findings=findings.get('findings', []),
                          agent_types=types.get('types', []))


# ==================== AUTOMATION AGENT ====================

@bp.route('/automation')
@login_required
@permission_required('agents:use')
def automation():
    """Automation agent dashboard"""
    # Get configuration
    config, _ = api_request('GET', '/agents/configurations/automation')
    
    # Get recent executions
    executions, _ = api_request('GET', '/agents/executions?agent_type=automation&limit=20')
    
    return render_template('agents/automation.html',
                          title='Automation Agent',
                          config=config,
                          executions=executions.get('executions', []))


@bp.route('/automation/run', methods=['POST'])
@login_required
@permission_required('agents:use')
def run_automation():
    """Run the automation agent"""
    result, status_code = api_request('POST', '/agents/automation/run')
    
    if status_code == 200:
        flash(f"Automation completed: {result.get('message', 'Done')}", 'success')
    else:
        flash(result.get('detail', 'Failed to run automation'), 'error')
    
    return redirect(url_for('agents.automation'))


# ==================== AUDIT AGENT ====================

@bp.route('/audit')
@login_required
@permission_required('agents:use')
def audit():
    """Audit agent dashboard"""
    # Get configuration
    config, _ = api_request('GET', '/agents/configurations/audit')
    
    # Get recent executions
    executions, _ = api_request('GET', '/agents/executions?agent_type=audit&limit=20')
    
    # Get findings summary
    findings_summary = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'open': 0
    }
    
    findings, _ = api_request('GET', '/agents/findings?limit=100')
    for f in findings.get('findings', []):
        severity = f.get('severity', 'medium')
        if severity in findings_summary:
            findings_summary[severity] += 1
        if f.get('resolution_status') == 'open':
            findings_summary['open'] += 1
    
    return render_template('agents/audit.html',
                          title='Audit Agent',
                          config=config,
                          executions=executions.get('executions', []),
                          findings_summary=findings_summary)


@bp.route('/audit/run', methods=['POST'])
@login_required
@permission_required('agents:use')
def run_audit():
    """Run the audit agent"""
    branch_id = request.form.get('branch_id', type=int)
    send_email = request.form.get('send_email') == 'on'
    
    params = []
    if branch_id:
        params.append(f'branch_id={branch_id}')
    params.append(f'send_email={str(send_email).lower()}')
    
    result, status_code = api_request('POST', f'/agents/audit/run?{"&".join(params)}')
    
    if status_code == 200:
        flash(f"Audit completed: Processed {result.get('records_processed', 0)} records, found {result.get('records_flagged', 0)} issues", 'success')
    else:
        flash(result.get('detail', 'Failed to run audit'), 'error')
    
    return redirect(url_for('agents.audit'))


# ==================== DOC WIZARD ====================

@bp.route('/wizard')
@login_required
@permission_required('doc_wizard:use')
def wizard():
    """Doc Wizard interface"""
    # Get user's recent sessions
    sessions, _ = api_request('GET', '/agents/wizard/sessions?limit=10')
    
    return render_template('agents/wizard.html',
                          title='Doc Wizard',
                          sessions=sessions.get('sessions', []))


@bp.route('/wizard/session', methods=['POST'])
@login_required
@permission_required('doc_wizard:use')
def create_wizard_session():
    """Create a new Doc Wizard session"""
    data = {
        'issue_type': request.form.get('issue_type'),
        'description': request.form.get('description')
    }
    
    result, status_code = api_request('POST', '/agents/wizard/sessions', data=data)
    
    if status_code == 200:
        return jsonify({
            'success': True,
            'session_id': result.get('session_id'),
            'guidance': result.get('guidance'),
            'suggested_actions': result.get('suggested_actions')
        })
    else:
        return jsonify({'success': False, 'error': result.get('detail', 'Failed to create session')}), 400


@bp.route('/wizard/session/<int:session_id>')
@login_required
@permission_required('doc_wizard:use')
def get_wizard_session(session_id):
    """Get a Doc Wizard session"""
    result, status_code = api_request('GET', f'/agents/wizard/sessions/{session_id}')
    
    if status_code == 200:
        return jsonify(result)
    else:
        return jsonify({'error': result.get('detail', 'Session not found')}), 404


@bp.route('/wizard/session/<int:session_id>/message', methods=['POST'])
@login_required
@permission_required('doc_wizard:use')
def add_wizard_message(session_id):
    """Add a message to a Doc Wizard session"""
    data = {
        'content': request.json.get('content')
    }
    
    result, status_code = api_request('POST', f'/agents/wizard/sessions/{session_id}/messages', data=data)
    
    if status_code == 200:
        return jsonify(result)
    else:
        return jsonify({'error': result.get('detail', 'Failed to add message')}), 400


@bp.route('/wizard/session/<int:session_id>/resolve', methods=['POST'])
@login_required
@permission_required('doc_wizard:use')
def resolve_wizard_session(session_id):
    """Resolve a Doc Wizard session"""
    resolution_summary = request.form.get('resolution_summary', 'Issue resolved')
    
    result, status_code = api_request('POST', f'/agents/wizard/sessions/{session_id}/resolve?resolution_summary={resolution_summary}')
    
    if status_code == 200:
        flash('Session resolved successfully', 'success')
    else:
        flash(result.get('detail', 'Failed to resolve session'), 'error')
    
    return redirect(url_for('agents.wizard'))


# ==================== FINDINGS ====================

@bp.route('/findings')
@login_required
@permission_required('agents:view_findings')
def findings():
    """View all agent findings"""
    severity = request.args.get('severity')
    status_filter = request.args.get('status')
    
    params = []
    if severity:
        params.append(f'severity={severity}')
    if status_filter:
        params.append(f'status={status_filter}')
    
    findings_result, _ = api_request('GET', f'/agents/findings?{"&".join(params)}' if params else '/agents/findings?limit=100')
    
    return render_template('agents/findings.html',
                          title='Agent Findings',
                          findings=findings_result.get('findings', []),
                          severity_filter=severity,
                          status_filter=status_filter)


@bp.route('/findings/<int:finding_id>/resolve', methods=['POST'])
@login_required
@permission_required('agents:view_findings')
def resolve_finding(finding_id):
    """Resolve or dismiss a finding"""
    data = {
        'resolution_notes': request.form.get('resolution_notes'),
        'dismiss': request.form.get('dismiss') == 'true'
    }
    
    result, status_code = api_request('POST', f'/agents/findings/{finding_id}/resolve', data=data)
    
    if status_code == 200:
        flash('Finding resolved', 'success')
    else:
        flash(result.get('detail', 'Failed to resolve finding'), 'error')
    
    return redirect(url_for('agents.findings'))


# ==================== SETTINGS ====================

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('agents:configure')
def settings():
    """Configure agents"""
    if request.method == 'POST':
        agent_type = request.form.get('agent_type')
        
        # Parse email recipients
        email_recipients = []
        email_str = request.form.get('email_recipients', '')
        if email_str:
            email_recipients = [e.strip() for e in email_str.split(',') if e.strip()]
        
        data = {
            'agent_type': agent_type,
            'schedule_enabled': request.form.get('schedule_enabled') == 'on',
            'schedule_cron': request.form.get('schedule_cron') or None,
            'email_recipients': email_recipients,
            'email_enabled': request.form.get('email_enabled') == 'on',
            'is_enabled': request.form.get('is_enabled') == 'on'
        }
        
        result, status_code = api_request('POST', '/agents/configurations', data=data)
        
        if status_code == 200:
            flash(f'{agent_type.title()} agent configuration saved', 'success')
        else:
            flash(result.get('detail', 'Failed to save configuration'), 'error')
        
        return redirect(url_for('agents.settings'))
    
    # Get all configurations
    configs, _ = api_request('GET', '/agents/configurations')
    agent_types, _ = api_request('GET', '/agents/types')
    
    # Build a dict of configurations by type
    config_by_type = {}
    for c in configs.get('configurations', []):
        config_by_type[c['agent_type']] = c
    
    return render_template('agents/settings.html',
                          title='Agent Settings',
                          configurations=config_by_type,
                          agent_types=agent_types.get('types', []))


# ==================== EXECUTION DETAILS ====================

@bp.route('/executions/<int:execution_id>')
@login_required
def execution_detail(execution_id):
    """View execution details"""
    result, status_code = api_request('GET', f'/agents/executions/{execution_id}')
    
    if status_code != 200:
        flash('Execution not found', 'error')
        return redirect(url_for('agents.index'))
    
    execution = result.get('execution', {})
    
    return render_template('agents/execution_detail.html',
                          title=f'Execution #{execution_id}',
                          execution=execution)
