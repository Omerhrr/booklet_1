"""
Analytics Views - Data Analysis and Visualization Hub
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import api_request, login_required, permission_required, plan_feature_required
from datetime import date
import json

bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@bp.before_request
@login_required
def check_analytics_feature():
    """Check if Analytics feature is available for the current plan"""
    from flask import abort, session
    plan_limits = session.get('plan_limits', {'slug': 'basic'})
    plan_slug = plan_limits.get('slug', 'basic')
    if plan_slug not in ['premium', 'advanced', 'enterprise']:
        abort(403)


@bp.route('')
@login_required
@permission_required('reports:view')
def hub():
    """Analytics hub - main page"""
    # Get data sources
    sources, _ = api_request('GET', '/analytics/sources')
    
    # Get recent analyses
    analyses, _ = api_request('GET', '/analytics/analyses')
    
    # Get dashboards
    dashboards, _ = api_request('GET', '/analytics/dashboards')
    
    return render_template('analytics/hub.html',
                          title='Analytics Hub',
                          sources=sources.get('sources', []) if isinstance(sources, dict) else [],
                          analyses=analyses.get('analyses', []) if isinstance(analyses, dict) else [],
                          dashboards=dashboards.get('dashboards', []) if isinstance(dashboards, dict) else [])


@bp.route('/query')
@login_required
@permission_required('reports:view')
def query_builder():
    """Query builder interface"""
    # Get data source from params
    data_source = request.args.get('source', 'sales')
    
    # Get available data sources
    sources, _ = api_request('GET', '/analytics/sources')
    
    # Get fields for selected data source
    fields, _ = api_request('GET', f'/analytics/sources/{data_source}/fields')
    
    # Get saved filters for this data source
    filters, _ = api_request('GET', f'/analytics/filters?data_source={data_source}')
    
    return render_template('analytics/query.html',
                          title='Query Builder',
                          data_source=data_source,
                          sources=sources.get('sources', []) if isinstance(sources, dict) else [],
                          fields=fields if isinstance(fields, dict) else {},
                          saved_filters=filters.get('filters', []) if isinstance(filters, dict) else [])


@bp.route('/execute', methods=['POST'])
@login_required
@permission_required('reports:view')
def execute_query():
    """Execute analytics query"""
    try:
        data = request.get_json()
        
        result, status_code = api_request('POST', '/analytics/query', data=data)
        
        if status_code == 200:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('detail', 'Query failed')}), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/sources/<source_id>/fields')
@login_required
@permission_required('reports:view')
def get_source_fields(source_id):
    """Get fields for a data source (API endpoint for JavaScript)"""
    fields, status_code = api_request('GET', f'/analytics/sources/{source_id}/fields')
    
    if status_code == 200:
        return jsonify(fields)
    else:
        return jsonify({'error': fields.get('detail', 'Failed to load fields')}), status_code


@bp.route('/analyses')
@login_required
@permission_required('reports:view')
def saved_analyses():
    """List saved analyses"""
    data_source = request.args.get('source')
    
    params = {}
    if data_source:
        params['data_source'] = data_source
    
    analyses, _ = api_request('GET', '/analytics/analyses', params=params if params else None)
    
    return render_template('analytics/saved.html',
                          title='Saved Analyses',
                          analyses=analyses.get('analyses', []) if isinstance(analyses, dict) else [])


@bp.route('/analyses/new', methods=['GET', 'POST'])
@login_required
@permission_required('reports:view')
def new_analysis():
    """Create new analysis"""
    if request.method == 'POST':
        # Handle JSON request (from query builder)
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form data (from analysis form)
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'data_source': request.form.get('data_source'),
                'columns': json.loads(request.form.get('columns', '[]')),
                'filters': json.loads(request.form.get('filters', 'null')),
                'group_by': json.loads(request.form.get('group_by', 'null')),
                'aggregations': json.loads(request.form.get('aggregations', 'null')),
                'order_by': json.loads(request.form.get('order_by', 'null')),
                'chart_type': request.form.get('chart_type', 'table'),
                'chart_config': json.loads(request.form.get('chart_config', 'null')),
                'is_shared': request.form.get('is_shared') == 'on'
            }
        
        result, status_code = api_request('POST', '/analytics/analyses', data=data)
        
        if status_code == 200:
            # Return JSON for AJAX requests, redirect for form submissions
            if request.is_json:
                return jsonify({'success': True, 'id': result.get('id')})
            flash('Analysis saved successfully', 'success')
            return redirect(url_for('analytics.view_analysis', analysis_id=result.get('id')))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': result.get('detail', 'Failed to save analysis')}), 400
            flash(result.get('detail', 'Failed to save analysis'), 'error')
    
    # GET request - show form
    sources, _ = api_request('GET', '/analytics/sources')
    data_source = request.args.get('source', 'sales')
    fields, _ = api_request('GET', f'/analytics/sources/{data_source}/fields')
    
    return render_template('analytics/analysis_form.html',
                          title='New Analysis',
                          sources=sources.get('sources', []) if isinstance(sources, dict) else [],
                          data_source=data_source,
                          fields=fields if isinstance(fields, dict) else {},
                          analysis=None)


@bp.route('/analyses/<int:analysis_id>')
@login_required
@permission_required('reports:view')
def view_analysis(analysis_id):
    """View analysis with results"""
    result, status_code = api_request('GET', f'/analytics/analyses/{analysis_id}')
    
    if status_code != 200:
        flash('Analysis not found', 'error')
        return redirect(url_for('analytics.saved_analyses'))
    
    analysis = result.get('analysis', {})
    results = result.get('results', [])
    metadata = result.get('metadata', {})
    
    return render_template('analytics/view_analysis.html',
                          title=analysis.get('name', 'Analysis'),
                          analysis=analysis,
                          results=results,
                          metadata=metadata)


@bp.route('/analyses/<int:analysis_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('reports:view')
def edit_analysis(analysis_id):
    """Edit analysis"""
    if request.method == 'POST':
        data = {}
        if request.form.get('name'):
            data['name'] = request.form.get('name')
        if request.form.get('description'):
            data['description'] = request.form.get('description')
        if request.form.get('columns'):
            data['columns'] = json.loads(request.form.get('columns'))
        if request.form.get('chart_type'):
            data['chart_type'] = request.form.get('chart_type')
        
        result, status_code = api_request('PUT', f'/analytics/analyses/{analysis_id}', data=data)
        
        if status_code == 200:
            flash('Analysis updated', 'success')
            return redirect(url_for('analytics.view_analysis', analysis_id=analysis_id))
        else:
            flash(result.get('detail', 'Failed to update'), 'error')
    
    # GET request
    result, _ = api_request('GET', f'/analytics/analyses/{analysis_id}')
    analysis = result.get('analysis', {})
    
    sources, _ = api_request('GET', '/analytics/sources')
    fields, _ = api_request('GET', f'/analytics/sources/{analysis.get("data_source", "sales")}/fields')
    
    return render_template('analytics/analysis_form.html',
                          title='Edit Analysis',
                          sources=sources.get('sources', []) if isinstance(sources, dict) else [],
                          data_source=analysis.get('data_source', 'sales'),
                          fields=fields if isinstance(fields, dict) else {},
                          analysis=analysis)


@bp.route('/analyses/<int:analysis_id>/delete', methods=['POST'])
@login_required
@permission_required('reports:view')
def delete_analysis(analysis_id):
    """Delete analysis"""
    result, status_code = api_request('DELETE', f'/analytics/analyses/{analysis_id}')
    
    if status_code == 200:
        flash('Analysis deleted', 'success')
    else:
        flash(result.get('detail', 'Failed to delete'), 'error')
    
    return redirect(url_for('analytics.saved_analyses'))


@bp.route('/analyses/<int:analysis_id>/favorite', methods=['POST'])
@login_required
@permission_required('reports:view')
def toggle_favorite(analysis_id):
    """Toggle analysis favorite status"""
    result, status_code = api_request('POST', f'/analytics/analyses/{analysis_id}/favorite')
    
    if status_code == 200:
        return jsonify({'success': True, 'is_favorite': result.get('is_favorite', False)})
    else:
        return jsonify({'success': False, 'error': result.get('detail', 'Failed to toggle favorite')}), status_code


# ==================== DASHBOARDS ====================

@bp.route('/dashboards')
@login_required
@permission_required('reports:view')
def list_dashboards():
    """List dashboards"""
    dashboards, _ = api_request('GET', '/analytics/dashboards')
    
    return render_template('analytics/dashboards.html',
                          title='Dashboards',
                          dashboards=dashboards.get('dashboards', []) if isinstance(dashboards, dict) else [])


@bp.route('/dashboards/new', methods=['GET', 'POST'])
@login_required
@permission_required('reports:view')
def new_dashboard():
    """Create new dashboard"""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'layout': json.loads(request.form.get('layout', '[]')),
            'widgets': json.loads(request.form.get('widgets', '[]')),
            'is_shared': request.form.get('is_shared') == 'on'
        }
        
        result, status_code = api_request('POST', '/analytics/dashboards', data=data)
        
        if status_code == 200:
            flash('Dashboard created', 'success')
            return redirect(url_for('analytics.view_dashboard', dashboard_id=result.get('id')))
        else:
            flash(result.get('detail', 'Failed to create dashboard'), 'error')
    
    # Get analyses for widget selection
    analyses, _ = api_request('GET', '/analytics/analyses')
    
    return render_template('analytics/dashboard_form.html',
                          title='New Dashboard',
                          analyses=analyses.get('analyses', []) if isinstance(analyses, dict) else [],
                          dashboard=None)


@bp.route('/dashboards/<int:dashboard_id>')
@login_required
@permission_required('reports:view')
def view_dashboard(dashboard_id):
    """View dashboard"""
    result, status_code = api_request('GET', f'/analytics/dashboards/{dashboard_id}')
    
    if status_code != 200:
        flash('Dashboard not found', 'error')
        return redirect(url_for('analytics.list_dashboards'))
    
    dashboard = result.get('dashboard', {})
    
    return render_template('analytics/view_dashboard.html',
                          title=dashboard.get('name', 'Dashboard'),
                          dashboard=dashboard)


@bp.route('/dashboards/<int:dashboard_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('reports:view')
def edit_dashboard(dashboard_id):
    """Edit dashboard"""
    if request.method == 'POST':
        try:
            widgets_str = request.form.get('widgets', '[]')
            layout_str = request.form.get('layout', '[]')
            
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'layout': json.loads(layout_str) if layout_str else [],
                'widgets': json.loads(widgets_str) if widgets_str else []
            }
        except json.JSONDecodeError as e:
            flash(f'Invalid data format: {str(e)}', 'error')
            result, _ = api_request('GET', f'/analytics/dashboards/{dashboard_id}')
            dashboard = result.get('dashboard', {})
            # Strip data field from widgets for editing
            if dashboard.get('widgets'):
                dashboard['widgets'] = [
                    {k: v for k, v in w.items() if k != 'data'}
                    for w in dashboard['widgets']
                ]
            analyses, _ = api_request('GET', '/analytics/analyses')
            return render_template('analytics/dashboard_form.html',
                                  title='Edit Dashboard',
                                  analyses=analyses.get('analyses', []) if isinstance(analyses, dict) else [],
                                  dashboard=dashboard)
        
        result, status_code = api_request('PUT', f'/analytics/dashboards/{dashboard_id}', data=data)
        
        if status_code == 200:
            flash('Dashboard updated', 'success')
            return redirect(url_for('analytics.view_dashboard', dashboard_id=dashboard_id))
        else:
            flash(result.get('detail', 'Failed to update'), 'error')
    
    # GET request
    result, _ = api_request('GET', f'/analytics/dashboards/{dashboard_id}')
    dashboard = result.get('dashboard', {})
    
    # Strip data field from widgets for editing - we only need the config, not the query results
    if dashboard.get('widgets'):
        dashboard['widgets'] = [
            {k: v for k, v in w.items() if k != 'data'}
            for w in dashboard['widgets']
        ]
    
    analyses, _ = api_request('GET', '/analytics/analyses')
    
    return render_template('analytics/dashboard_form.html',
                          title='Edit Dashboard',
                          analyses=analyses.get('analyses', []) if isinstance(analyses, dict) else [],
                          dashboard=dashboard)


@bp.route('/dashboards/<int:dashboard_id>/delete', methods=['POST'])
@login_required
@permission_required('reports:view')
def delete_dashboard(dashboard_id):
    """Delete dashboard"""
    result, status_code = api_request('DELETE', f'/analytics/dashboards/{dashboard_id}')
    
    if status_code == 200:
        flash('Dashboard deleted', 'success')
    else:
        flash(result.get('detail', 'Failed to delete'), 'error')
    
    return redirect(url_for('analytics.list_dashboards'))


# ==================== FILTERS ====================

@bp.route('/filters/save', methods=['POST'])
@login_required
@permission_required('reports:view')
def save_filter():
    """Save filter set"""
    data = {
        'name': request.form.get('name'),
        'description': request.form.get('description'),
        'data_source': request.form.get('data_source'),
        'filter_config': json.loads(request.form.get('filter_config', '[]'))
    }
    
    result, status_code = api_request('POST', '/analytics/filters', data=data)
    
    if status_code == 200:
        return jsonify({'success': True, 'id': result.get('id')})
    else:
        return jsonify({'success': False, 'error': result.get('detail')}), status_code
