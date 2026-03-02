"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, get_current_user
from app.core.config import settings
from app.schemas import LoginRequest, SignupRequest, Token, UserResponse, MessageResponse
from app.services.user_service import UserService
from app.services.business_service import BusinessService, BranchService
from app.services.permission_service import RoleService, seed_permissions, PermissionService
from app.services.audit_service import AuditService, AuditAction

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    else:
        ip_address = "unknown"
    
    user_agent = request.headers.get("User-Agent", "")[:500]
    return ip_address, user_agent


@router.post("/signup", response_model=dict)
async def signup(
    signup_data: SignupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new business and admin user"""
    user_service = UserService(db)
    business_service = BusinessService(db)
    branch_service = BranchService(db)
    role_service = RoleService(db)
    audit_service = AuditService(db)
    
    ip_address, user_agent = get_client_info(request)
    
    # Check if username exists
    if user_service.get_by_username(signup_data.username):
        audit_service.log(
            action=AuditAction.CREATE,
            resource_type="User",
            description=f"Signup failed: username '{signup_data.username}' already exists",
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/signup",
            status="failure",
            error_message="Username already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if user_service.get_by_email(signup_data.email):
        audit_service.log(
            action=AuditAction.CREATE,
            resource_type="User",
            description=f"Signup failed: email '{signup_data.email}' already exists",
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/signup",
            status="failure",
            error_message="Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create business
        business = business_service.create(signup_data.model_dump(include={"business_name"}))
        
        # Seed permissions if needed
        seed_permissions(db)
        
        # Create default admin role
        admin_role = role_service.create_default_roles_for_business(business.id)
        
        # Create user
        user_data = {
            "username": signup_data.username,
            "email": signup_data.email,
            "password": signup_data.password
        }
        user = user_service.create(user_data, business.id, is_superuser=True)
        
        # Create default branch
        branch = branch_service.create(
            {"name": "Main Branch", "currency": "USD"},
            business.id,
            is_default=True
        )
        
        # Assign role to user
        user_service.assign_role(user.id, branch.id, admin_role.id)
        
        # Create default chart of accounts
        business_service.create_default_chart_of_accounts(business.id)
        
        # Log successful signup
        audit_service.log(
            action=AuditAction.USER_CREATED,
            resource_type="User",
            resource_id=user.id,
            description=f"New user '{user.username}' signed up with business '{business.name}'",
            user_id=user.id,
            username=user.username,
            business_id=business.id,
            branch_id=branch.id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/signup",
            new_values={"username": user.username, "email": user.email, "business_name": business.name}
        )
        
        db.commit()
        
        # Create token
        access_token = create_access_token(
            data={"sub": user.username, "business_id": business.id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "business_id": business.id
            }
        }
        
    except Exception as e:
        db.rollback()
        # Log the actual error but don't expose it to the user
        import logging
        logging.error(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again later."
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    ip_address, user_agent = get_client_info(request)
    
    user = user_service.get_by_username(login_data.username)
    
    if not user or not user_service.verify_password(user, login_data.password):
        # Log failed login attempt
        audit_service.log(
            action=AuditAction.LOGIN_FAILED,
            resource_type="User",
            description=f"Failed login attempt for username '{login_data.username}'",
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/login",
            status="failure",
            error_message="Invalid credentials"
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        audit_service.log(
            action=AuditAction.LOGIN_FAILED,
            resource_type="User",
            resource_id=user.id,
            description=f"Login attempt for disabled account '{user.username}'",
            user_id=user.id,
            username=user.username,
            business_id=user.business_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/login",
            status="failure",
            error_message="Account is disabled"
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "business_id": user.business_id},
        expires_delta=access_token_expires
    )
    
    # Log successful login
    audit_service.log(
        action=AuditAction.LOGIN,
        resource_type="User",
        resource_id=user.id,
        description=f"User '{user.username}' logged in successfully",
        user_id=user.id,
        username=user.username,
        business_id=user.business_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method="POST",
        request_path="/api/v1/auth/login"
    )
    
    db.commit()
    
    # Set cookie with security settings
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        samesite="lax",
        secure=settings.is_production  # Only secure in production
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout and clear token"""
    audit_service = AuditService(db)
    ip_address, user_agent = get_client_info(request)
    
    # Log logout
    if current_user:
        audit_service.log(
            action=AuditAction.LOGOUT,
            resource_type="User",
            resource_id=current_user.id,
            description=f"User '{current_user.username}' logged out",
            user_id=current_user.id,
            username=current_user.username,
            business_id=current_user.business_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method="POST",
            request_path="/api/v1/auth/logout"
        )
        db.commit()
    
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user info"""
    return current_user


@router.get("/permissions")
async def get_user_permissions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's permissions"""
    if current_user.is_superuser:
        # Superusers have all permissions
        permission_service = PermissionService(db)
        all_perms = permission_service.get_all_permissions()
        return {"permissions": [p.name for p in all_perms], "is_superuser": True, "user_id": current_user.id}
    
    permission_service = PermissionService(db)
    user_permissions = permission_service.get_user_permissions(current_user)
    
    # Debug info
    debug_info = {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_superuser": current_user.is_superuser,
        "roles_count": len(current_user.roles) if current_user.roles else 0,
        "roles": []
    }
    
    if current_user.roles:
        for ur in current_user.roles:
            role_info = {
                "role_id": ur.role_id,
                "role_name": ur.role.name if ur.role else None,
                "branch_id": ur.branch_id
            }
            if ur.role and hasattr(ur.role, 'permission_links'):
                role_info["permissions_count"] = len(ur.role.permission_links) if ur.role.permission_links else 0
            debug_info["roles"].append(role_info)
    
    return {
        "permissions": list(user_permissions), 
        "is_superuser": False,
        "debug": debug_info
    }
