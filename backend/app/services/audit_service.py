"""
Audit Logging Service
Provides comprehensive audit trail for sensitive operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json
import logging

from app.models import AuditLog

logger = logging.getLogger(__name__)


class AuditAction:
    """Constants for audit actions"""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"
    
    # CRUD Operations
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    
    # Financial Operations
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    PAYMENT_MADE = "PAYMENT_MADE"
    INVOICE_FINALIZED = "INVOICE_FINALIZED"
    BILL_PAID = "BILL_PAID"
    JOURNAL_POSTED = "JOURNAL_POSTED"
    TRANSFER_COMPLETED = "TRANSFER_COMPLETED"
    EXPENSE_RECORDED = "EXPENSE_RECORDED"
    
    # HR Operations
    EMPLOYEE_HIRED = "EMPLOYEE_HIRED"
    EMPLOYEE_TERMINATED = "EMPLOYEE_TERMINATED"
    PAYROLL_RUN = "PAYROLL_RUN"
    PAYSLIP_GENERATED = "PAYSLIP_GENERATED"
    
    # User Management
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    
    # Settings
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    BRANCH_CREATED = "BRANCH_CREATED"


class AuditService:
    """Service for recording and retrieving audit logs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        business_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            action: The action being performed (use AuditAction constants)
            resource_type: Type of resource being affected (e.g., 'Invoice', 'Payment')
            resource_id: ID of the affected resource
            description: Human-readable description of the action
            old_values: Dictionary of values before the change (for updates)
            new_values: Dictionary of values after the change
            user_id: ID of the user performing the action
            username: Username (stored separately in case user is deleted)
            business_id: Business context
            branch_id: Branch context
            ip_address: Client IP address
            user_agent: Client user agent string
            request_method: HTTP method (GET, POST, PUT, DELETE)
            request_path: API endpoint path
            status: 'success', 'failure', or 'error'
            error_message: Error message if status is not success
            
        Returns:
            The created AuditLog instance
        """
        try:
            # Convert dict values to JSON strings
            old_values_json = json.dumps(old_values, default=str) if old_values else None
            new_values_json = json.dumps(new_values, default=str) if new_values else None
            
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                old_values=old_values_json,
                new_values=new_values_json,
                user_id=user_id,
                username=username,
                business_id=business_id,
                branch_id=branch_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                status=status,
                error_message=error_message
            )
            
            self.db.add(audit_log)
            self.db.flush()  # Flush to get the ID without committing
            
            logger.info(
                f"Audit: {action} {resource_type}(id={resource_id}) by user={username} "
                f"business={business_id} branch={branch_id} status={status}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit logging should not break the main operation
            return None
    
    def get_by_id(self, log_id: int, business_id: int) -> Optional[AuditLog]:
        """Get a specific audit log by ID"""
        return self.db.query(AuditLog).filter(
            AuditLog.id == log_id,
            AuditLog.business_id == business_id
        ).first()
    
    def get_by_business(
        self,
        business_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit logs for a business with optional filters.
        
        Args:
            business_id: Business to filter by
            start_date: Filter logs from this date
            end_date: Filter logs until this date
            user_id: Filter by user
            action: Filter by action type
            resource_type: Filter by resource type
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of AuditLog instances
        """
        query = self.db.query(AuditLog).filter(
            AuditLog.business_id == business_id
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
        
        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    def get_by_resource(
        self,
        resource_type: str,
        resource_id: int,
        business_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit history for a specific resource"""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
            AuditLog.business_id == business_id
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    def get_by_user(
        self,
        user_id: int,
        business_id: int,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.business_id == business_id
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    def get_recent_logins(
        self,
        business_id: int,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get recent login activity"""
        return self.db.query(AuditLog).filter(
            AuditLog.business_id == business_id,
            AuditLog.action.in_([AuditAction.LOGIN, AuditAction.LOGOUT, AuditAction.LOGIN_FAILED])
        ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    def get_summary(
        self,
        business_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get audit summary statistics"""
        query = self.db.query(AuditLog).filter(
            AuditLog.business_id == business_id
        )
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp < end_date)
        
        logs = query.all()
        
        # Calculate summary
        summary = {
            'total_actions': len(logs),
            'by_action': {},
            'by_resource_type': {},
            'by_status': {'success': 0, 'failure': 0, 'error': 0},
            'unique_users': set(),
        }
        
        for log in logs:
            # By action
            if log.action not in summary['by_action']:
                summary['by_action'][log.action] = 0
            summary['by_action'][log.action] += 1
            
            # By resource type
            if log.resource_type not in summary['by_resource_type']:
                summary['by_resource_type'][log.resource_type] = 0
            summary['by_resource_type'][log.resource_type] += 1
            
            # By status
            if log.status in summary['by_status']:
                summary['by_status'][log.status] += 1
            
            # Unique users
            if log.user_id:
                summary['unique_users'].add(log.user_id)
        
        summary['unique_users'] = len(summary['unique_users'])
        
        return summary


def audit_log(
    action: str,
    resource_type: str,
    description: Optional[str] = None,
    old_values_func: Optional[callable] = None,
    new_values_func: Optional[callable] = None
):
    """
    Decorator for automatic audit logging of endpoint operations.
    
    Usage:
        @audit_log(
            action=AuditAction.CREATE,
            resource_type="Invoice",
            description="Created sales invoice"
        )
        async def create_invoice(...):
            ...
    
    Args:
        action: The action being performed
        resource_type: Type of resource being affected
        description: Optional description (can include placeholders like {invoice_id})
        old_values_func: Optional function to extract old values (receives kwargs)
        new_values_func: Optional function to extract new values (receives result)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract common parameters from kwargs or function signature
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            # Get old values before operation (if provided)
            old_values = None
            if old_values_func and db:
                try:
                    old_values = old_values_func(**kwargs)
                except Exception as e:
                    logger.warning(f"Failed to get old values for audit: {e}")
            
            # Get request info
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None
            
            if request:
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    ip_address = forwarded.split(",")[0].strip()
                elif request.client:
                    ip_address = request.client.host
                    
                user_agent = request.headers.get("User-Agent", "")[:500]
                request_method = request.method
                request_path = str(request.url.path)
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Get new values after operation (if provided)
                new_values = None
                if new_values_func:
                    try:
                        new_values = new_values_func(result)
                    except Exception as e:
                        logger.warning(f"Failed to get new values for audit: {e}")
                
                # Determine resource_id from result
                resource_id = None
                if result and hasattr(result, 'id'):
                    resource_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    resource_id = result['id']
                
                # Create audit log
                if db and current_user:
                    audit_service = AuditService(db)
                    audit_service.log(
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        description=description,
                        old_values=old_values,
                        new_values=new_values,
                        user_id=current_user.id,
                        username=current_user.username,
                        business_id=current_user.business_id,
                        branch_id=getattr(current_user, '_selected_branch', {}).id if hasattr(current_user, '_selected_branch') and current_user._selected_branch else None,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_method=request_method,
                        request_path=request_path,
                        status="success"
                    )
                
                return result
                
            except Exception as e:
                # Log the error
                if db and current_user:
                    audit_service = AuditService(db)
                    audit_service.log(
                        action=action,
                        resource_type=resource_type,
                        description=f"Failed: {str(e)}",
                        user_id=current_user.id,
                        username=current_user.username,
                        business_id=current_user.business_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        request_method=request_method,
                        request_path=request_path,
                        status="error",
                        error_message=str(e)
                    )
                raise
        
        return wrapper
    return decorator
