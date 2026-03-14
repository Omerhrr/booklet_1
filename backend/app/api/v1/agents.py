"""
Agent API Routes - Automation, Audit, and Doc Wizard Agents
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import logging
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user, PlanFeatureChecker
from app.models import User, AgentConfiguration, AgentExecution, AgentFinding, AgentType, AgentStatus
from app.services.agent_service import (
    AgentService, AutomationAgentService, AuditAgentService, DocWizardService
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/agents", tags=["Agents"], dependencies=[Depends(PlanFeatureChecker("agents"))])
logger = logging.getLogger(__name__)


# ==================== SCHEMAS ====================

class AgentConfigCreate(BaseModel):
    agent_type: str  # automation, audit, doc_wizard
    config: Optional[Dict] = None
    schedule_enabled: bool = False
    schedule_cron: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    email_enabled: bool = False
    is_enabled: bool = True


class AgentConfigUpdate(BaseModel):
    config: Optional[Dict] = None
    schedule_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    email_enabled: Optional[bool] = None
    is_enabled: Optional[bool] = None


class DocWizardMessageCreate(BaseModel):
    content: str


class FindingResolve(BaseModel):
    resolution_notes: Optional[str] = None
    dismiss: bool = False


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/configurations")
async def list_configurations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all agent configurations for the business"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'settings:edit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage agents"
        )
    
    service = AgentService(db)
    configs = service.get_all_configurations(current_user.business_id)
    
    return {
        "configurations": [
            {
                "id": c.id,
                "agent_type": c.agent_type,
                "config": json.loads(c.config) if c.config else None,
                "schedule_enabled": c.schedule_enabled,
                "schedule_cron": c.schedule_cron,
                "email_recipients": json.loads(c.email_recipients) if c.email_recipients else [],
                "email_enabled": c.email_enabled,
                "is_enabled": c.is_enabled,
                "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None,
                "next_run_at": c.next_run_at.isoformat() if c.next_run_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in configs
        ]
    }


@router.get("/configurations/{agent_type}")
async def get_configuration(
    agent_type: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get configuration for a specific agent type"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'settings:edit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage agents"
        )
    
    service = AgentService(db)
    config = service.get_configuration(current_user.business_id, agent_type)
    
    if not config:
        return {
            "configured": False,
            "agent_type": agent_type,
            "is_enabled": False,
            "schedule_enabled": False,
            "email_enabled": False
        }
    
    return {
        "configured": True,
        "id": config.id,
        "agent_type": config.agent_type,
        "config": json.loads(config.config) if config.config else None,
        "schedule_enabled": config.schedule_enabled,
        "schedule_cron": config.schedule_cron,
        "email_recipients": json.loads(config.email_recipients) if config.email_recipients else [],
        "email_enabled": config.email_enabled,
        "is_enabled": config.is_enabled,
        "last_run_at": config.last_run_at.isoformat() if config.last_run_at else None,
        "next_run_at": config.next_run_at.isoformat() if config.next_run_at else None
    }


@router.post("/configurations")
async def create_configuration(
    request: AgentConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create or update agent configuration"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'settings:edit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage agents"
        )
    
    service = AgentService(db)
    
    config = service.create_or_update_configuration(
        business_id=current_user.business_id,
        agent_type=request.agent_type,
        config=request.config,
        schedule_enabled=request.schedule_enabled,
        schedule_cron=request.schedule_cron,
        email_recipients=request.email_recipients,
        email_enabled=request.email_enabled,
        is_enabled=request.is_enabled
    )
    
    return {
        "success": True,
        "id": config.id,
        "message": f"{request.agent_type} agent configuration saved"
    }


@router.patch("/configurations/{agent_type}")
async def update_configuration(
    agent_type: str,
    request: AgentConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update agent configuration"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'settings:edit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage agents"
        )
    
    service = AgentService(db)
    config = service.get_configuration(current_user.business_id, agent_type)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    
    update_data = request.model_dump(exclude_unset=True)
    
    if 'config' in update_data and update_data['config']:
        config.config = json.dumps(update_data['config'])
    if 'schedule_enabled' in update_data:
        config.schedule_enabled = update_data['schedule_enabled']
    if 'schedule_cron' in update_data:
        config.schedule_cron = update_data['schedule_cron']
    if 'email_recipients' in update_data:
        config.email_recipients = json.dumps(update_data['email_recipients'])
    if 'email_enabled' in update_data:
        config.email_enabled = update_data['email_enabled']
    if 'is_enabled' in update_data:
        config.is_enabled = update_data['is_enabled']
    
    db.commit()
    
    return {"success": True, "message": "Configuration updated"}


# ==================== EXECUTION ENDPOINTS ====================

@router.post("/automation/run")
async def run_automation_agent(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Run the automation agent manually"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'settings:edit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to run agents"
        )
    
    service = AutomationAgentService(db)
    
    try:
        execution = service.run_automations(current_user.business_id, current_user.id)
        
        return {
            "success": True,
            "execution_id": execution.id,
            "status": execution.status,
            "message": "Automation agent completed"
        }
    except Exception as e:
        logger.error(f"Automation agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/audit/run")
async def run_audit_agent(
    background_tasks: BackgroundTasks,
    branch_id: Optional[int] = None,
    send_email: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Run the audit agent manually"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'reports:view'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to run audit agent"
        )
    
    service = AuditAgentService(db)
    
    try:
        execution = await service.run_audit(
            business_id=current_user.business_id,
            branch_id=branch_id,
            send_email=send_email
        )
        
        return {
            "success": True,
            "execution_id": execution.id,
            "status": execution.status,
            "report_path": execution.report_path,
            "records_processed": execution.records_processed,
            "records_flagged": execution.records_flagged,
            "message": "Audit agent completed"
        }
    except Exception as e:
        logger.error(f"Audit agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/executions")
async def list_executions(
    agent_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List agent executions"""
    service = AgentService(db)
    executions = service.get_executions(
        business_id=current_user.business_id,
        agent_type=agent_type,
        status=status_filter,
        limit=limit
    )
    
    return {
        "executions": [
            {
                "id": e.id,
                "agent_type": e.agent_configuration.agent_type if e.agent_configuration else None,
                "status": e.status,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "result_summary": e.result_summary,
                "records_processed": e.records_processed,
                "records_flagged": e.records_flagged,
                "error_message": e.error_message,
                "report_path": e.report_path
            }
            for e in executions
        ]
    }


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get execution details"""
    execution = db.query(AgentExecution).filter(
        AgentExecution.id == execution_id,
        AgentExecution.business_id == current_user.business_id
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    return {
        "execution": {
            "id": execution.id,
            "agent_type": execution.agent_configuration.agent_type if execution.agent_configuration else None,
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "result_summary": execution.result_summary,
            "result_details": json.loads(execution.result_details) if execution.result_details else None,
            "records_processed": execution.records_processed,
            "records_created": execution.records_created,
            "records_updated": execution.records_updated,
            "records_flagged": execution.records_flagged,
            "error_message": execution.error_message,
            "report_path": execution.report_path
        }
    }


# ==================== FINDINGS ENDPOINTS ====================

@router.get("/findings")
async def list_findings(
    severity: Optional[str] = None,
    resolution_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List agent findings"""
    service = AgentService(db)
    findings = service.get_findings(
        business_id=current_user.business_id,
        severity=severity,
        resolution_status=resolution_status,
        limit=limit
    )
    
    return {
        "findings": [
            {
                "id": f.id,
                "finding_type": f.finding_type,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "related_model": f.related_model,
                "related_record_id": f.related_record_id,
                "resolution_status": f.resolution_status,
                "resolution_notes": f.resolution_notes,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None
            }
            for f in findings
        ]
    }


@router.post("/findings/{finding_id}/resolve")
async def resolve_finding(
    finding_id: int,
    request: FindingResolve,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Resolve or dismiss a finding"""
    service = AgentService(db)
    
    try:
        finding = service.resolve_finding(
            finding_id=finding_id,
            resolved_by=current_user.id,
            resolution_notes=request.resolution_notes,
            dismiss=request.dismiss
        )
        
        return {
            "success": True,
            "resolution_status": finding.resolution_status,
            "message": "Finding resolved" if not request.dismiss else "Finding dismissed"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== DOC WIZARD ENDPOINTS ====================

@router.post("/wizard/sessions")
async def create_wizard_session(
    issue_type: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new Doc Wizard session"""
    service = DocWizardService(db)
    
    session = service.create_session(
        business_id=current_user.business_id,
        user_id=current_user.id,
        issue_type=issue_type,
        description=description
    )
    
    # Analyze the issue if description provided
    guidance = None
    suggested_actions = None
    if description:
        guidance, suggested_actions = service.analyze_issue(description)
        
        # Add assistant's response
        service.add_message(
            session_id=session.id,
            role='assistant',
            content=guidance,
            suggested_actions=suggested_actions
        )
    
    return {
        "session_id": session.id,
        "guidance": guidance,
        "suggested_actions": suggested_actions
    }


@router.get("/wizard/sessions")
async def list_wizard_sessions(
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List user's Doc Wizard sessions"""
    service = DocWizardService(db)
    sessions = service.get_user_sessions(
        user_id=current_user.id,
        business_id=current_user.business_id,
        limit=limit
    )
    
    return {
        "sessions": [
            {
                "id": s.id,
                "issue_type": s.issue_type,
                "description": s.description,
                "resolved": s.resolved,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in sessions
        ]
    }


@router.get("/wizard/sessions/{session_id}")
async def get_wizard_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get Doc Wizard session with messages"""
    service = DocWizardService(db)
    session = service.get_session(session_id)
    
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    messages = service.get_session_messages(session_id)
    
    return {
        "session": {
            "id": session.id,
            "issue_type": session.issue_type,
            "description": session.description,
            "resolved": session.resolved,
            "resolution_summary": session.resolution_summary,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "suggested_actions": json.loads(m.suggested_actions) if m.suggested_actions else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }
    }


@router.post("/wizard/sessions/{session_id}/messages")
async def add_wizard_message(
    session_id: int,
    request: DocWizardMessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Add a message to a Doc Wizard session"""
    service = DocWizardService(db)
    session = service.get_session(session_id)
    
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already resolved"
        )
    
    # Add user message
    service.add_message(
        session_id=session_id,
        role='user',
        content=request.content
    )
    
    # Analyze and respond
    guidance, suggested_actions = service.analyze_issue(request.content)
    
    # Add assistant response
    assistant_msg = service.add_message(
        session_id=session_id,
        role='assistant',
        content=guidance,
        suggested_actions=suggested_actions
    )
    
    return {
        "message": {
            "id": assistant_msg.id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "suggested_actions": suggested_actions
        }
    }


@router.post("/wizard/sessions/{session_id}/resolve")
async def resolve_wizard_session(
    session_id: int,
    resolution_summary: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Mark a Doc Wizard session as resolved"""
    service = DocWizardService(db)
    
    try:
        session = service.resolve_session(session_id, resolution_summary)
        return {
            "success": True,
            "message": "Session resolved"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== AGENT INFO ====================

@router.get("/types")
async def get_agent_types():
    """Get available agent types"""
    return {
        "types": [
            {
                "id": "automation",
                "name": "Automation Agent",
                "description": "Runs automated tasks like bad debt analysis, depreciation, and overdue detection",
                "capabilities": [
                    "Bad debt analysis and write-off",
                    "Depreciation calculation",
                    "Overdue invoice detection",
                    "Automated status updates"
                ]
            },
            {
                "id": "audit",
                "name": "Audit Agent",
                "description": "Comprehensive business auditing with PDF reports and email notifications",
                "capabilities": [
                    "Ledger balance verification",
                    "Invoice reconciliation checks",
                    "Inventory discrepancy detection",
                    "Audit log review",
                    "Branch comparison",
                    "PDF report generation",
                    "Email notifications"
                ]
            },
            {
                "id": "doc_wizard",
                "name": "Doc Wizard",
                "description": "Interactive guide for fixing accounting and data issues",
                "capabilities": [
                    "Sales vs Purchase corrections",
                    "Duplicate entry resolution",
                    "Wrong account corrections",
                    "Reconciliation assistance",
                    "Step-by-step guidance"
                ]
            }
        ]
    }
