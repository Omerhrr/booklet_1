"""
Analytics API Routes - Data Analysis and Visualization
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
import json
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user, PlanFeatureChecker
from app.models import Analysis, Dashboard, SavedFilter
from app.services.analytics_service import AnalyticsService, DataSource

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(PlanFeatureChecker("analytics"))])
logger = logging.getLogger(__name__)


# ==================== SCHEMAS ====================

class FilterCondition(BaseModel):
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, like, in, between
    value: Any


class OrderByClause(BaseModel):
    field: str
    direction: str = 'asc'  # asc, desc


class QueryRequest(BaseModel):
    data_source: str
    columns: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    group_by: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None  # {field: aggregation_type}
    order_by: Optional[List[OrderByClause]] = None
    limit: Optional[int] = 100


class AnalysisCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data_source: str
    columns: List[str]
    filters: Optional[List[Dict]] = None
    group_by: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None
    order_by: Optional[List[Dict]] = None
    chart_type: str = 'table'
    chart_config: Optional[Dict] = None
    is_shared: bool = False


class AnalysisUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[List[str]] = None
    filters: Optional[List[Dict]] = None
    group_by: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None
    order_by: Optional[List[Dict]] = None
    chart_type: Optional[str] = None
    chart_config: Optional[Dict] = None
    is_shared: Optional[bool] = None
    is_favorite: Optional[bool] = None


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    layout: Optional[List[Dict]] = None
    widgets: Optional[List[Dict]] = None
    is_shared: bool = False


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[List[Dict]] = None
    widgets: Optional[List[Dict]] = None
    is_default: Optional[bool] = None
    is_shared: Optional[bool] = None


class SavedFilterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data_source: str
    filter_config: List[Dict]


# ==================== DATA SOURCE ENDPOINTS ====================

@router.get("/sources")
async def get_data_sources(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get list of available data sources"""
    analytics_service = AnalyticsService(db)
    sources = analytics_service.get_data_sources()
    return {"sources": sources}


@router.get("/sources/{source_id}/fields")
async def get_data_source_fields(
    source_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get available fields for a data source"""
    analytics_service = AnalyticsService(db)
    fields = analytics_service.get_data_source_fields(source_id)
    if not fields:
        raise HTTPException(status_code=404, detail="Data source not found")
    return fields


# ==================== QUERY ENDPOINTS ====================

@router.post("/query")
async def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Execute an analytics query"""
    analytics_service = AnalyticsService(db)
    
    # Convert filters to dict format
    filters = None
    if request.filters:
        filters = [f.model_dump() for f in request.filters]
    
    # Convert order_by to dict format
    order_by = None
    if request.order_by:
        order_by = [o.model_dump() for o in request.order_by]
    
    # Get branch_id from user's selected branch
    branch_id = None
    if hasattr(current_user, '_selected_branch') and current_user._selected_branch is not None:
        branch_id = getattr(current_user._selected_branch, 'id', None)
    
    try:
        results, metadata = analytics_service.execute_query(
            data_source=request.data_source,
            columns=request.columns,
            filters=filters,
            group_by=request.group_by,
            aggregations=request.aggregations,
            order_by=order_by,
            limit=request.limit,
            branch_id=branch_id,
            business_id=current_user.business_id
        )
        
        return {
            "success": True,
            "results": results,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sources/{source_id}/summary")
async def get_summary_stats(
    source_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get summary statistics for a data source"""
    analytics_service = AnalyticsService(db)
    
    # Determine date field based on source
    date_field_map = {
        DataSource.SALES: 'invoice_date',
        DataSource.PURCHASES: 'bill_date',
        DataSource.EXPENSES: 'expense_date',
        DataSource.OTHER_INCOME: 'income_date',
        DataSource.CASHBOOK: 'entry_date',
        DataSource.LEDGER: 'transaction_date',
        DataSource.PAYROLL: 'pay_period_start',
        DataSource.FIXED_ASSETS: 'purchase_date',
    }
    
    # Get branch_id from user's selected branch
    branch_id = None
    if hasattr(current_user, '_selected_branch') and current_user._selected_branch is not None:
        branch_id = getattr(current_user._selected_branch, 'id', None)
    
    stats = analytics_service.get_summary_stats(
        data_source=source_id,
        branch_id=branch_id,
        business_id=current_user.business_id,
        date_field=date_field_map.get(source_id),
        start_date=start_date,
        end_date=end_date
    )
    
    return {"success": True, "stats": stats}


# ==================== SAVED ANALYSES ====================

@router.get("/analyses")
async def list_analyses(
    data_source: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List saved analyses"""
    from sqlalchemy import or_
    
    query = db.query(Analysis).filter(
        Analysis.business_id == current_user.business_id
    )
    
    # Show own analyses or shared ones
    query = query.filter(
        or_(
            Analysis.created_by == current_user.id,
            Analysis.is_shared.is_(True)
        )
    )
    
    if data_source:
        query = query.filter(Analysis.data_source == data_source)
    if is_favorite is not None:
        query = query.filter(Analysis.is_favorite.is_(is_favorite))
    
    analyses = query.order_by(Analysis.updated_at.desc()).all()
    
    return {
        "analyses": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "data_source": a.data_source,
                "chart_type": a.chart_type,
                "is_shared": a.is_shared,
                "is_favorite": a.is_favorite,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None
            }
            for a in analyses
        ]
    }


@router.post("/analyses")
async def create_analysis(
    request: AnalysisCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a saved analysis"""
    branch_id = None
    if hasattr(current_user, '_selected_branch') and current_user._selected_branch is not None:
        branch_id = getattr(current_user._selected_branch, 'id', None)
    
    analysis = Analysis(
        name=request.name,
        description=request.description,
        data_source=request.data_source,
        columns=json.dumps(request.columns),
        filters=json.dumps(request.filters) if request.filters else None,
        group_by=json.dumps(request.group_by) if request.group_by else None,
        aggregations=json.dumps(request.aggregations) if request.aggregations else None,
        order_by=json.dumps(request.order_by) if request.order_by else None,
        chart_type=request.chart_type,
        chart_config=json.dumps(request.chart_config) if request.chart_config else None,
        is_shared=request.is_shared,
        created_by=current_user.id,
        branch_id=branch_id,
        business_id=current_user.business_id
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return {"success": True, "id": analysis.id, "message": "Analysis created"}


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a saved analysis with data"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.business_id == current_user.business_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Parse JSON fields
    columns = json.loads(analysis.columns) if analysis.columns else []
    filters = json.loads(analysis.filters) if analysis.filters else None
    group_by = json.loads(analysis.group_by) if analysis.group_by else None
    aggregations = json.loads(analysis.aggregations) if analysis.aggregations else None
    order_by = json.loads(analysis.order_by) if analysis.order_by else None
    chart_config = json.loads(analysis.chart_config) if analysis.chart_config else None
    
    # Execute the query
    analytics_service = AnalyticsService(db)
    try:
        results, metadata = analytics_service.execute_query(
            data_source=analysis.data_source,
            columns=columns,
            filters=filters,
            group_by=group_by,
            aggregations=aggregations,
            order_by=order_by,
            limit=1000,
            branch_id=analysis.branch_id,
            business_id=analysis.business_id
        )
    except Exception as e:
        logger.error(f"Analysis query error: {e}")
        results = []
        metadata = {}
    
    return {
        "analysis": {
            "id": analysis.id,
            "name": analysis.name,
            "description": analysis.description,
            "data_source": analysis.data_source,
            "columns": columns,
            "filters": filters,
            "group_by": group_by,
            "aggregations": aggregations,
            "order_by": order_by,
            "chart_type": analysis.chart_type,
            "chart_config": chart_config,
            "is_shared": analysis.is_shared,
            "is_favorite": analysis.is_favorite,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        },
        "results": results,
        "metadata": metadata
    }


@router.put("/analyses/{analysis_id}")
async def update_analysis(
    analysis_id: int,
    request: AnalysisUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a saved analysis"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.business_id == current_user.business_id,
        Analysis.created_by == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or no permission")
    
    if request.name is not None:
        analysis.name = request.name
    if request.description is not None:
        analysis.description = request.description
    if request.columns is not None:
        analysis.columns = json.dumps(request.columns)
    if request.filters is not None:
        analysis.filters = json.dumps(request.filters)
    if request.group_by is not None:
        analysis.group_by = json.dumps(request.group_by)
    if request.aggregations is not None:
        analysis.aggregations = json.dumps(request.aggregations)
    if request.order_by is not None:
        analysis.order_by = json.dumps(request.order_by)
    if request.chart_type is not None:
        analysis.chart_type = request.chart_type
    if request.chart_config is not None:
        analysis.chart_config = json.dumps(request.chart_config)
    if request.is_shared is not None:
        analysis.is_shared = request.is_shared
    if request.is_favorite is not None:
        analysis.is_favorite = request.is_favorite
    
    db.commit()
    
    return {"success": True, "message": "Analysis updated"}


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a saved analysis"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.business_id == current_user.business_id,
        Analysis.created_by == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or no permission")
    
    db.delete(analysis)
    db.commit()
    
    return {"success": True, "message": "Analysis deleted"}


@router.post("/analyses/{analysis_id}/favorite")
async def toggle_analysis_favorite(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle favorite status of an analysis"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.business_id == current_user.business_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis.is_favorite = not analysis.is_favorite
    db.commit()
    
    return {"success": True, "is_favorite": analysis.is_favorite}


# ==================== DASHBOARDS ====================

@router.get("/dashboards")
async def list_dashboards(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List dashboards"""
    from sqlalchemy import or_
    
    query = db.query(Dashboard).filter(
        Dashboard.business_id == current_user.business_id
    )
    
    # Show own dashboards or shared ones
    query = query.filter(
        or_(
            Dashboard.created_by == current_user.id,
            Dashboard.is_shared.is_(True)
        )
    )
    
    dashboards = query.order_by(Dashboard.updated_at.desc()).all()
    
    return {
        "dashboards": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "is_default": d.is_default,
                "is_shared": d.is_shared,
                "widget_count": len(json.loads(d.widgets)) if d.widgets else 0,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in dashboards
        ]
    }


@router.post("/dashboards")
async def create_dashboard(
    request: DashboardCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new dashboard"""
    branch_id = None
    if hasattr(current_user, '_selected_branch') and current_user._selected_branch is not None:
        branch_id = getattr(current_user._selected_branch, 'id', None)
    
    dashboard = Dashboard(
        name=request.name,
        description=request.description,
        layout=json.dumps(request.layout) if request.layout else None,
        widgets=json.dumps(request.widgets) if request.widgets else None,
        is_shared=request.is_shared,
        created_by=current_user.id,
        branch_id=branch_id,
        business_id=current_user.business_id
    )
    
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    
    return {"success": True, "id": dashboard.id, "message": "Dashboard created"}


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a dashboard with widgets and data"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id,
        Dashboard.business_id == current_user.business_id
    ).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    layout = json.loads(dashboard.layout) if dashboard.layout else []
    widgets = json.loads(dashboard.widgets) if dashboard.widgets else []
    
    # Get data for each widget (analysis)
    analytics_service = AnalyticsService(db)
    widgets_with_data = []
    
    for widget in widgets:
        analysis_id = widget.get('analysis_id')
        if analysis_id:
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                try:
                    results, metadata = analytics_service.execute_query(
                        data_source=analysis.data_source,
                        columns=json.loads(analysis.columns) if analysis.columns else [],
                        filters=json.loads(analysis.filters) if analysis.filters else None,
                        group_by=json.loads(analysis.group_by) if analysis.group_by else None,
                        aggregations=json.loads(analysis.aggregations) if analysis.aggregations else None,
                        limit=100,
                        branch_id=analysis.branch_id,
                        business_id=analysis.business_id
                    )
                except:
                    results = []
                
                widget['data'] = results
                widget['analysis_name'] = analysis.name
                widget['chart_type'] = analysis.chart_type
                widget['chart_config'] = json.loads(analysis.chart_config) if analysis.chart_config else None
        
        widgets_with_data.append(widget)
    
    return {
        "dashboard": {
            "id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "layout": layout,
            "widgets": widgets_with_data,
            "is_default": dashboard.is_default,
            "is_shared": dashboard.is_shared,
            "created_at": dashboard.created_at.isoformat() if dashboard.created_at else None
        }
    }


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: int,
    request: DashboardUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a dashboard"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id,
        Dashboard.business_id == current_user.business_id,
        Dashboard.created_by == current_user.id
    ).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no permission")
    
    if request.name is not None:
        dashboard.name = request.name
    if request.description is not None:
        dashboard.description = request.description
    if request.layout is not None:
        dashboard.layout = json.dumps(request.layout)
    if request.widgets is not None:
        dashboard.widgets = json.dumps(request.widgets)
    if request.is_default is not None:
        dashboard.is_default = request.is_default
    if request.is_shared is not None:
        dashboard.is_shared = request.is_shared
    
    db.commit()
    
    return {"success": True, "message": "Dashboard updated"}


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a dashboard"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id,
        Dashboard.business_id == current_user.business_id,
        Dashboard.created_by == current_user.id
    ).first()
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or no permission")
    
    db.delete(dashboard)
    db.commit()
    
    return {"success": True, "message": "Dashboard deleted"}


# ==================== SAVED FILTERS ====================

@router.get("/filters")
async def list_saved_filters(
    data_source: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List saved filters"""
    query = db.query(SavedFilter).filter(
        SavedFilter.business_id == current_user.business_id,
        SavedFilter.created_by == current_user.id
    )
    
    if data_source:
        query = query.filter(SavedFilter.data_source == data_source)
    
    filters = query.all()
    
    return {
        "filters": [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
                "data_source": f.data_source,
                "filter_config": json.loads(f.filter_config) if f.filter_config else [],
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in filters
        ]
    }


@router.post("/filters")
async def create_saved_filter(
    request: SavedFilterCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a saved filter"""
    branch_id = None
    if hasattr(current_user, '_selected_branch') and current_user._selected_branch is not None:
        branch_id = getattr(current_user._selected_branch, 'id', None)
    
    saved_filter = SavedFilter(
        name=request.name,
        description=request.description,
        data_source=request.data_source,
        filter_config=json.dumps(request.filter_config),
        created_by=current_user.id,
        branch_id=branch_id,
        business_id=current_user.business_id
    )
    
    db.add(saved_filter)
    db.commit()
    db.refresh(saved_filter)
    
    return {"success": True, "id": saved_filter.id, "message": "Filter saved"}


@router.delete("/filters/{filter_id}")
async def delete_saved_filter(
    filter_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a saved filter"""
    saved_filter = db.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.business_id == current_user.business_id,
        SavedFilter.created_by == current_user.id
    ).first()
    
    if not saved_filter:
        raise HTTPException(status_code=404, detail="Filter not found or no permission")
    
    db.delete(saved_filter)
    db.commit()
    
    return {"success": True, "message": "Filter deleted"}
