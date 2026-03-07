"""
Audit Log API Routes - View System Activity Logs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.core.security import get_current_active_user, PermissionChecker
from app.models import AuditLog, User
from app.services.audit_service import AuditService, AuditAction

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


# ==================== SCHEMAS ====================

class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[int]
    description: Optional[str]
    business_id: Optional[int]
    branch_id: Optional[int]
    status: str
    request_method: Optional[str]
    request_path: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogDetail(AuditLogResponse):
    old_values: Optional[dict]
    new_values: Optional[dict]
    user_agent: Optional[str]
    error_message: Optional[str]


class AuditSummaryResponse(BaseModel):
    total_events: int
    create_count: int
    update_count: int
    delete_count: int
    login_count: int
    other_count: int
    unique_users: int


# ==================== ENDPOINTS ====================


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List audit logs with optional filters"""
    query = db.query(AuditLog).filter(
        AuditLog.business_id == current_user.business_id
    )
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp < end_date)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if status:
        query = query.filter(AuditLog.status == status)
    
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    return logs


@router.get("/{log_id}", response_model=AuditLogDetail)
async def get_audit_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed audit log by ID"""
    import json
    
    log = db.query(AuditLog).filter(
        AuditLog.id == log_id,
        AuditLog.business_id == current_user.business_id
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    # Parse JSON values
    old_values = None
    new_values = None
    
    if log.old_values:
        try:
            old_values = json.loads(log.old_values)
        except:
            pass
    
    if log.new_values:
        try:
            new_values = json.loads(log.new_values)
        except:
            pass
    
    return AuditLogDetail(
        id=log.id,
        timestamp=log.timestamp,
        user_id=log.user_id,
        username=log.username,
        ip_address=log.ip_address,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        description=log.description,
        business_id=log.business_id,
        branch_id=log.branch_id,
        status=log.status,
        request_method=log.request_method,
        request_path=log.request_path,
        old_values=old_values,
        new_values=new_values,
        user_agent=log.user_agent,
        error_message=log.error_message
    )


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get audit summary statistics"""
    query = db.query(AuditLog).filter(
        AuditLog.business_id == current_user.business_id
    )
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp < end_date)
    
    logs = query.all()
    
    # Calculate summary counts
    create_count = sum(1 for log in logs if log.action == AuditAction.CREATE)
    update_count = sum(1 for log in logs if log.action == AuditAction.UPDATE)
    delete_count = sum(1 for log in logs if log.action == AuditAction.DELETE)
    login_count = sum(1 for log in logs if log.action in [AuditAction.LOGIN, AuditAction.LOGOUT, AuditAction.LOGIN_FAILED])
    other_count = len(logs) - create_count - update_count - delete_count - login_count
    unique_users = len(set(log.user_id for log in logs if log.user_id))
    
    return AuditSummaryResponse(
        total_events=len(logs),
        create_count=create_count,
        update_count=update_count,
        delete_count=delete_count,
        login_count=login_count,
        other_count=other_count,
        unique_users=unique_users
    )


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditLogResponse])
async def get_resource_audit_history(
    resource_type: str,
    resource_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get audit history for a specific resource"""
    audit_service = AuditService(db)
    logs = audit_service.get_by_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        business_id=current_user.business_id,
        limit=limit
    )
    
    return logs


@router.get("/user/{user_id}", response_model=List[AuditLogResponse])
async def get_user_audit_history(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get audit logs for a specific user"""
    audit_service = AuditService(db)
    logs = audit_service.get_by_user(
        user_id=user_id,
        business_id=current_user.business_id,
        limit=limit
    )
    
    return logs


@router.get("/recent-logins", response_model=List[AuditLogResponse])
async def get_recent_logins(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get recent login activity"""
    audit_service = AuditService(db)
    logs = audit_service.get_recent_logins(
        business_id=current_user.business_id,
        limit=limit
    )
    
    return logs


@router.get("/actions")
async def get_available_actions():
    """Get list of available audit actions"""
    return {
        "actions": [
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
            AuditAction.LOGIN_FAILED,
            AuditAction.PASSWORD_CHANGE,
            AuditAction.CREATE,
            AuditAction.UPDATE,
            AuditAction.DELETE,
            AuditAction.PAYMENT_RECEIVED,
            AuditAction.PAYMENT_MADE,
            AuditAction.INVOICE_FINALIZED,
            AuditAction.BILL_PAID,
            AuditAction.JOURNAL_POSTED,
            AuditAction.TRANSFER_COMPLETED,
            AuditAction.EXPENSE_RECORDED,
            AuditAction.USER_CREATED,
            AuditAction.USER_UPDATED,
            AuditAction.USER_DELETED,
            AuditAction.ROLE_ASSIGNED,
            AuditAction.SETTINGS_CHANGED,
        ]
    }
