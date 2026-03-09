"""
Security Module - Authentication & Authorization
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current authenticated user from JWT token.
    Supports both Authorization header and cookies.
    """
    from app.services.user_service import UserService
    
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    
    # Fall back to cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(db)
    user = user_service.get_user_with_relations(username=username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced dependency that attaches branch information to the user.
    """
    from app.services.business_service import BranchService
    
    branch_service = BranchService(db)
    
    # Get accessible branches
    if current_user.is_superuser:
        accessible_branches = branch_service.get_branches_by_business(current_user.business_id)
    else:
        accessible_branches = [assignment.branch for assignment in current_user.roles]
    
    if not accessible_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any branch"
        )
    
    # Get selected branch from cookie or default
    selected_branch_id = request.cookies.get("selected_branch_id")
    selected_branch = None
    
    if selected_branch_id:
        try:
            selected_branch_id = int(selected_branch_id)
            selected_branch = next(
                (b for b in accessible_branches if b.id == selected_branch_id), 
                None
            )
        except (ValueError, TypeError):
            pass
    
    if not selected_branch:
        # Default to first branch or default branch for superusers
        selected_branch = next(
            (b for b in accessible_branches if b.is_default),
            accessible_branches[0]
        )
    
    # Store branches info in a way that doesn't require property setter
    # Using _prefix for "private" attributes that won't conflict with model
    current_user._accessible_branches = accessible_branches
    current_user._selected_branch = selected_branch
    
    return current_user


class PermissionChecker:
    """Dependency for checking user permissions"""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = set(required_permissions)
    
    def __call__(self, user = Depends(get_current_active_user), db: Session = Depends(get_db)):
        # Superusers have all permissions
        if user.is_superuser:
            return
        
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(db)
        user_permissions = permission_service.get_user_permissions(user)
        
        if not self.required_permissions.issubset(user_permissions):
            missing = self.required_permissions - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing)}"
            )


class PlanFeatureChecker:
    """Dependency for checking plan-based feature access
    
    Plan limits apply to ALL users including superusers.
    This enforces subscription-based feature restrictions.
    """
    
    # Feature availability by plan slug
    FEATURE_PLANS = {
        'agents': ['premium', 'advanced', 'enterprise'],
        'ai': ['premium', 'advanced', 'enterprise'],
        'analytics': ['premium', 'advanced', 'enterprise'],
        'hr': ['premium', 'advanced', 'enterprise'],
        'budgets': ['premium', 'advanced', 'enterprise'],
        'fixed_assets': ['premium', 'advanced', 'enterprise'],
    }
    
    def __init__(self, feature: str):
        """Initialize with the feature to check
        
        Args:
            feature: Feature name (agents, ai, analytics, hr, budgets, fixed_assets)
        """
        self.feature = feature
    
    def __call__(self, user = Depends(get_current_active_user), db: Session = Depends(get_db)):
        from app.models import Subscription, SubscriptionPlan
        
        # Get subscription and plan
        subscription = db.query(Subscription).filter(
            Subscription.business_id == user.business_id
        ).first()
        
        plan_slug = 'basic'  # Default to most restrictive
        if subscription and subscription.status == 'active':
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            if plan:
                plan_slug = plan.slug
        
        # Check if feature is available in current plan
        allowed_plans = self.FEATURE_PLANS.get(self.feature, [])
        if plan_slug not in allowed_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{self.feature}' requires a Premium plan or higher. Please upgrade your subscription."
            )


class PlanLimitChecker:
    """Dependency for checking plan-based resource limits
    
    Checks if the business has reached its limit for branches or users.
    """
    
    def __init__(self, resource_type: str):
        """Initialize with resource type to check
        
        Args:
            resource_type: 'branches' or 'users'
        """
        self.resource_type = resource_type
    
    def __call__(self, user = Depends(get_current_active_user), db: Session = Depends(get_db)):
        from app.models import Subscription, SubscriptionPlan, Branch, User
        
        # Get subscription and plan limits
        subscription = db.query(Subscription).filter(
            Subscription.business_id == user.business_id
        ).first()
        
        max_limit = 1 if self.resource_type == 'branches' else 5  # Basic defaults
        if subscription and subscription.status == 'active':
            plan = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            if plan:
                if self.resource_type == 'branches':
                    max_limit = plan.max_branches
                elif self.resource_type == 'users':
                    max_limit = plan.max_users
        
        # Count current usage
        if self.resource_type == 'branches':
            current_count = db.query(Branch).filter(
                Branch.business_id == user.business_id
            ).count()
        elif self.resource_type == 'users':
            current_count = db.query(User).filter(
                User.business_id == user.business_id
            ).count()
        else:
            current_count = 0
        
        if current_count >= max_limit:
            resource_name = self.resource_type.capitalize()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your plan allows a maximum of {max_limit} {resource_name.lower()}. You currently have {current_count}. Please upgrade your plan."
            )
