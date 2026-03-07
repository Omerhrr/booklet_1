"""
SaaS API Routes - Plans, Subscriptions, Blog, Website Content
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
import json
import secrets

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models import (
    User, Business, Branch, Role, Permission, RolePermission, UserBranchRole,
    SubscriptionPlan, Subscription, PaymentHistory, BlogPost, WebsiteContent, 
    ContactSubmission, WebsiteUser, Account, AccountType
)
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/saas", tags=["SaaS"])


# ==================== PYDANTIC SCHEMAS ====================

class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    max_branches: int
    max_users: int
    includes_agents: bool
    monthly_price: float
    yearly_price: float
    features: List[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: int
    plan: Optional[PlanResponse]
    status: str
    billing_cycle: str
    current_period_end: Optional[date]
    
    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    user: dict
    business: dict
    plan_slug: str = "basic"
    billing_cycle: str = "monthly"


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = None
    message: str


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    is_published: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


# ==================== PLANS ====================

@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    """Get all active subscription plans"""
    plans = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.is_active == True
    ).order_by(SubscriptionPlan.display_order).all()
    
    return {
        "plans": [{
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "max_branches": p.max_branches,
            "max_users": p.max_users,
            "includes_agents": p.includes_agents,
            "monthly_price": float(p.monthly_price),
            "yearly_price": float(p.yearly_price),
            "features": json.loads(p.features) if p.features else [],
            "is_active": p.is_active
        } for p in plans]
    }


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a specific plan"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "slug": plan.slug,
            "max_branches": plan.max_branches,
            "max_users": plan.max_users,
            "includes_agents": plan.includes_agents,
            "monthly_price": float(plan.monthly_price),
            "yearly_price": float(plan.yearly_price),
            "features": json.loads(plan.features) if plan.features else [],
            "is_active": plan.is_active
        }
    }


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: dict, db: Session = Depends(get_db)):
    """Update a subscription plan"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    for key, value in data.items():
        if key == 'features' and isinstance(value, list):
            value = json.dumps(value)
        if hasattr(plan, key):
            setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    
    return {"message": "Plan updated", "plan_id": plan.id}


# ==================== SUBSCRIPTION ====================

@router.get("/subscription")
def get_subscription(business_id: int = None, db: Session = Depends(get_db)):
    """Get subscription for a business"""
    if not business_id:
        return {"subscription": None}
    
    subscription = db.query(Subscription).filter(
        Subscription.business_id == business_id
    ).first()
    
    if not subscription:
        return {"subscription": None}
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    
    return {
        "subscription": {
            "id": subscription.id,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "slug": plan.slug,
                "max_branches": plan.max_branches,
                "max_users": plan.max_users,
                "includes_agents": plan.includes_agents,
                "monthly_price": float(plan.monthly_price),
                "yearly_price": float(plan.yearly_price),
                "features": json.loads(plan.features) if plan.features else []
            } if plan else None
        }
    }


# ==================== REGISTRATION ====================

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new business and user (bypassing payment for testing)"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.user.get('email')).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Get the plan
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == data.plan_slug).first()
    if not plan:
        # Create default plan if not exists
        plan = create_default_plan(db, data.plan_slug)
    
    # Create business
    business = Business(
        name=data.business.get('name'),
        email=data.user.get('email'),
        plan=plan.slug if plan else 'basic'
    )
    db.add(business)
    db.flush()
    
    # Create user
    username = data.user.get('email').split('@')[0]
    # Ensure unique username
    counter = 1
    original_username = username
    while db.query(User).filter(User.username == username).first():
        username = f"{original_username}{counter}"
        counter += 1
    
    user = User(
        username=username,
        email=data.user.get('email'),
        hashed_password=get_password_hash(data.user.get('password')),
        full_name=data.user.get('name'),
        business_id=business.id,
        is_superuser=True  # First user is superuser
    )
    db.add(user)
    db.flush()
    
    # Create default branch
    branch = Branch(
        name="Main Branch",
        currency=data.business.get('currency', 'USD'),
        is_default=True,
        business_id=business.id
    )
    db.add(branch)
    db.flush()
    
    # Create owner role
    owner_role = Role(
        name="Owner",
        description="Business owner with full access",
        is_system=True,
        business_id=business.id
    )
    db.add(owner_role)
    db.flush()
    
    # Get all permissions and assign to owner
    permissions = db.query(Permission).all()
    for perm in permissions:
        role_perm = RolePermission(
            role_id=owner_role.id,
            permission_id=perm.id
        )
        db.add(role_perm)
    
    # Assign role to user
    user_branch_role = UserBranchRole(
        user_id=user.id,
        branch_id=branch.id,
        role_id=owner_role.id
    )
    db.add(user_branch_role)
    
    # Create subscription
    subscription = Subscription(
        business_id=business.id,
        plan_id=plan.id,
        status='active',
        billing_cycle=data.billing_cycle,
        current_period_start=date.today(),
        current_period_end=date.today() + timedelta(days=30 if data.billing_cycle == 'monthly' else 365)
    )
    db.add(subscription)
    
    # Create default chart of accounts
    create_default_accounts(db, business.id, branch.id)
    
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "business_id": business.id,
            "is_website_admin": False,
            "subscription_active": True
        },
        "access_token": access_token
    }


def create_default_plan(db: Session, slug: str):
    """Create default subscription plan"""
    plans_data = {
        'basic': {
            'name': 'Basic',
            'max_branches': 1,
            'max_users': 5,
            'includes_agents': False,
            'monthly_price': 29.00,
            'yearly_price': 290.00,
            'features': ['Core Accounting', 'Invoicing', 'Reports', 'CRM', 'Inventory']
        },
        'premium': {
            'name': 'Premium',
            'max_branches': 5,
            'max_users': 25,
            'includes_agents': True,
            'monthly_price': 79.00,
            'yearly_price': 790.00,
            'features': ['Everything in Basic', 'AI Agents', 'Analytics Hub', 'HR & Payroll', 'Priority Support']
        },
        'advanced': {
            'name': 'Advanced',
            'max_branches': 10,
            'max_users': 50,
            'includes_agents': True,
            'monthly_price': 149.00,
            'yearly_price': 1490.00,
            'features': ['Everything in Premium', 'API Access', 'Custom Reports', 'Dedicated Support']
        },
        'enterprise': {
            'name': 'Enterprise',
            'max_branches': 999999,
            'max_users': 999999,
            'includes_agents': True,
            'monthly_price': 0.00,
            'yearly_price': 0.00,
            'features': ['Unlimited Everything', 'Custom Integrations', 'SLA Guarantee', 'Dedicated Account Manager']
        }
    }
    
    data = plans_data.get(slug, plans_data['basic'])
    plan = SubscriptionPlan(
        name=data['name'],
        slug=slug,
        max_branches=data['max_branches'],
        max_users=data['max_users'],
        includes_agents=data['includes_agents'],
        monthly_price=Decimal(str(data['monthly_price'])),
        yearly_price=Decimal(str(data['yearly_price'])),
        features=json.dumps(data['features'])
    )
    db.add(plan)
    db.flush()
    return plan


def create_default_accounts(db: Session, business_id: int, branch_id: int):
    """Create default chart of accounts"""
    default_accounts = [
        # Assets
        {'code': '1000', 'name': 'Cash', 'type': 'Asset', 'is_system_account': True},
        {'code': '1100', 'name': 'Accounts Receivable', 'type': 'Asset', 'is_system_account': True},
        {'code': '1200', 'name': 'Inventory', 'type': 'Asset', 'is_system_account': True},
        {'code': '1300', 'name': 'VAT Receivable', 'type': 'Asset', 'is_system_account': True},
        {'code': '1500', 'name': 'Fixed Assets', 'type': 'Asset', 'is_system_account': True},
        {'code': '1600', 'name': 'Accumulated Depreciation', 'type': 'Asset', 'is_system_account': True},
        
        # Liabilities
        {'code': '2000', 'name': 'Accounts Payable', 'type': 'Liability', 'is_system_account': True},
        {'code': '2100', 'name': 'VAT Payable', 'type': 'Liability', 'is_system_account': True},
        {'code': '2200', 'name': 'Customer Advances', 'type': 'Liability', 'is_system_account': True},
        {'code': '2300', 'name': 'Payroll Liabilities', 'type': 'Liability', 'is_system_account': True},
        
        # Equity
        {'code': '3000', 'name': "Owner's Equity", 'type': 'Equity', 'is_system_account': True},
        {'code': '3100', 'name': 'Opening Balance Equity', 'type': 'Equity', 'is_system_account': True},
        {'code': '3200', 'name': 'Retained Earnings', 'type': 'Equity', 'is_system_account': True},
        
        # Revenue
        {'code': '4000', 'name': 'Sales Revenue', 'type': 'Revenue', 'is_system_account': True},
        {'code': '4100', 'name': 'Other Income', 'type': 'Revenue', 'is_system_account': True},
        
        # Expenses
        {'code': '5000', 'name': 'Cost of Goods Sold', 'type': 'Expense', 'is_system_account': True},
        {'code': '6000', 'name': 'Operating Expenses', 'type': 'Expense', 'is_system_account': True},
        {'code': '6100', 'name': 'Bad Debt Expense', 'type': 'Expense', 'is_system_account': True},
        {'code': '6200', 'name': 'Depreciation Expense', 'type': 'Expense', 'is_system_account': True},
    ]
    
    for acc_data in default_accounts:
        account = Account(
            code=acc_data['code'],
            name=acc_data['name'],
            type=acc_data['type'],
            is_system_account=acc_data['is_system_account'],
            business_id=business_id
        )
        db.add(account)


# ==================== AUTH ====================

@router.post("/auth/login")
def login(data: dict, db: Session = Depends(get_db)):
    """Login user"""
    email = data.get('email')
    password = data.get('password')
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Check subscription
    subscription_active = False
    subscription = db.query(Subscription).filter(Subscription.business_id == user.business_id).first()
    if subscription and subscription.status == 'active':
        subscription_active = True
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    # Check if website admin
    website_user = db.query(WebsiteUser).filter(WebsiteUser.user_id == user.id).first()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "business_id": user.business_id,
            "is_website_admin": website_user.is_website_admin if website_user else False,
            "subscription_active": subscription_active
        },
        "access_token": access_token
    }


# ==================== BLOG ====================

@router.get("/blog")
def get_blog_posts(
    published_only: bool = True,
    all: bool = False,
    category: str = None,
    limit: int = 10,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Get blog posts"""
    query = db.query(BlogPost)
    
    if published_only and not all:
        query = query.filter(BlogPost.is_published == True)
    
    if category:
        query = query.filter(BlogPost.category == category)
    
    total = query.count()
    posts = query.order_by(desc(BlogPost.published_at)).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "posts": [{
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "excerpt": p.excerpt,
            "content": p.content,
            "featured_image": p.featured_image,
            "category": p.category,
            "tags": json.loads(p.tags) if p.tags else [],
            "is_published": p.is_published,
            "published_at": p.published_at.isoformat() if p.published_at else None,
            "view_count": p.view_count,
            "author": {
                "id": p.author.id,
                "name": p.author.full_name
            } if p.author else None,
            "created_at": p.created_at.isoformat()
        } for p in posts],
        "total": total,
        "page": page,
        "per_page": limit
    }


@router.get("/blog/{slug}")
def get_blog_post(slug: str, db: Session = Depends(get_db)):
    """Get a single blog post by slug"""
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    post.view_count = (post.view_count or 0) + 1
    db.commit()
    
    return {
        "post": {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "excerpt": post.excerpt,
            "content": post.content,
            "featured_image": post.featured_image,
            "category": post.category,
            "tags": json.loads(post.tags) if post.tags else [],
            "is_published": post.is_published,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "view_count": post.view_count,
            "meta_title": post.meta_title,
            "meta_description": post.meta_description,
            "author": {
                "id": post.author.id,
                "name": post.author.full_name
            } if post.author else None,
            "created_at": post.created_at.isoformat()
        }
    }


@router.post("/blog")
def create_blog_post(data: BlogPostCreate, author_id: int = 1, db: Session = Depends(get_db)):
    """Create a new blog post"""
    # Check if slug exists
    existing = db.query(BlogPost).filter(BlogPost.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    post = BlogPost(
        title=data.title,
        slug=data.slug,
        excerpt=data.excerpt,
        content=data.content,
        category=data.category,
        tags=json.dumps(data.tags),
        is_published=data.is_published,
        published_at=datetime.utcnow() if data.is_published else None,
        meta_title=data.meta_title,
        meta_description=data.meta_description,
        author_id=author_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {"message": "Post created", "post_id": post.id}


@router.put("/blog/{post_id}")
def update_blog_post(post_id: int, data: BlogPostUpdate, db: Session = Depends(get_db)):
    """Update a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if data.title:
        post.title = data.title
    if data.slug:
        # Check new slug doesn't exist
        existing = db.query(BlogPost).filter(BlogPost.slug == data.slug, BlogPost.id != post_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")
        post.slug = data.slug
    if data.excerpt is not None:
        post.excerpt = data.excerpt
    if data.content is not None:
        post.content = data.content
    if data.category is not None:
        post.category = data.category
    if data.tags is not None:
        post.tags = json.dumps(data.tags)
    if data.is_published is not None:
        post.is_published = data.is_published
        if data.is_published and not post.published_at:
            post.published_at = datetime.utcnow()
    if data.meta_title is not None:
        post.meta_title = data.meta_title
    if data.meta_description is not None:
        post.meta_description = data.meta_description
    
    db.commit()
    db.refresh(post)
    
    return {"message": "Post updated", "post_id": post.id}


@router.delete("/blog/{post_id}")
def delete_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    
    return {"message": "Post deleted"}


# ==================== CONTACT ====================

@router.post("/contact")
def submit_contact(data: ContactRequest, db: Session = Depends(get_db)):
    """Submit contact form"""
    submission = ContactSubmission(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message
    )
    db.add(submission)
    db.commit()
    
    return {"message": "Contact form submitted successfully"}


@router.get("/contact")
def get_contact_submissions(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get contact submissions"""
    query = db.query(ContactSubmission)
    
    if status:
        query = query.filter(ContactSubmission.status == status)
    
    submissions = query.order_by(desc(ContactSubmission.created_at)).limit(limit).all()
    
    return {
        "submissions": [{
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "subject": s.subject,
            "message": s.message,
            "status": s.status,
            "replied_at": s.replied_at.isoformat() if s.replied_at else None,
            "created_at": s.created_at.isoformat()
        } for s in submissions]
    }


# ==================== WEBSITE CONTENT ====================

@router.get("/content")
def get_all_content(db: Session = Depends(get_db)):
    """Get all website content"""
    contents = db.query(WebsiteContent).filter(WebsiteContent.is_active == True).all()
    
    result = {}
    for c in contents:
        if c.section not in result:
            result[c.section] = {}
        result[c.section][c.key] = json.loads(c.content) if c.content else {}
    
    return {"content": result}


@router.get("/content/{section}")
def get_section_content(section: str, db: Session = Depends(get_db)):
    """Get content for a specific section"""
    contents = db.query(WebsiteContent).filter(
        WebsiteContent.section == section,
        WebsiteContent.is_active == True
    ).all()
    
    result = {}
    for c in contents:
        result[c.key] = json.loads(c.content) if c.content else {}
    
    return {"content": result}


@router.put("/content/{section}")
def update_section_content(section: str, data: dict, db: Session = Depends(get_db)):
    """Update content for a section"""
    for key, value in data.items():
        content = db.query(WebsiteContent).filter(
            WebsiteContent.section == section,
            WebsiteContent.key == key
        ).first()
        
        if content:
            content.content = json.dumps(value)
        else:
            content = WebsiteContent(
                section=section,
                key=key,
                content=json.dumps(value)
            )
            db.add(content)
    
    db.commit()
    
    return {"message": "Content updated"}


# ==================== PAYMENTS ====================

@router.get("/payments")
def get_payments(business_id: int = None, limit: int = 10, db: Session = Depends(get_db)):
    """Get payment history for a business"""
    if not business_id:
        return {"payments": []}
    
    subscription = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    if not subscription:
        return {"payments": []}
    
    payments = db.query(PaymentHistory).filter(
        PaymentHistory.subscription_id == subscription.id
    ).order_by(desc(PaymentHistory.created_at)).limit(limit).all()
    
    return {
        "payments": [{
            "id": p.id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "payment_method": p.payment_method,
            "invoice_url": p.invoice_url,
            "created_at": p.created_at.isoformat()
        } for p in payments]
    }


# ==================== USAGE ====================

@router.get("/usage")
def get_usage(business_id: int = None, db: Session = Depends(get_db)):
    """Get usage stats for a business"""
    if not business_id:
        return {"usage": {}}
    
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        return {"usage": {}}
    
    # Count branches
    branch_count = db.query(Branch).filter(Branch.business_id == business_id).count()
    
    # Count users
    user_count = db.query(User).filter(User.business_id == business_id).count()
    
    # Get plan limits
    subscription = db.query(Subscription).filter(Subscription.business_id == business_id).first()
    plan = None
    if subscription:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    
    return {
        "usage": {
            "branches": {
                "used": branch_count,
                "limit": plan.max_branches if plan else 1
            },
            "users": {
                "used": user_count,
                "limit": plan.max_users if plan else 5
            },
            "includes_agents": plan.includes_agents if plan else False
        }
    }


# ==================== ADMIN ====================

@router.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """Get admin dashboard stats"""
    total_businesses = db.query(Business).count()
    total_users = db.query(User).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.status == 'active').count()
    total_posts = db.query(BlogPost).count()
    published_posts = db.query(BlogPost).filter(BlogPost.is_published == True).count()
    new_contacts = db.query(ContactSubmission).filter(ContactSubmission.status == 'new').count()
    
    return {
        "stats": {
            "total_businesses": total_businesses,
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "total_posts": total_posts,
            "published_posts": published_posts,
            "new_contacts": new_contacts
        }
    }


@router.get("/admin/registrations")
def get_recent_registrations(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent registrations"""
    businesses = db.query(Business).order_by(desc(Business.created_at)).limit(limit).all()
    
    return {
        "registrations": [{
            "id": b.id,
            "name": b.name,
            "email": b.email,
            "created_at": b.created_at.isoformat()
        } for b in businesses]
    }


@router.get("/admin/users")
def get_users(page: int = 1, search: str = None, limit: int = 20, db: Session = Depends(get_db)):
    """Get all users"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "users": [{
            "id": u.id,
            "email": u.email,
            "name": u.full_name,
            "is_active": u.is_active,
            "business_id": u.business_id,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat()
        } for u in users],
        "total": total,
        "page": page
    }


# ==================== INIT PLANS ====================

@router.post("/init-plans")
def initialize_plans(db: Session = Depends(get_db)):
    """Initialize default subscription plans"""
    plans = [
        {
            'name': 'Basic',
            'slug': 'basic',
            'max_branches': 1,
            'max_users': 5,
            'includes_agents': False,
            'monthly_price': 29.00,
            'yearly_price': 290.00,
            'features': ['Core Accounting', 'Invoicing', 'Reports', 'CRM', 'Inventory'],
            'display_order': 1
        },
        {
            'name': 'Premium',
            'slug': 'premium',
            'max_branches': 5,
            'max_users': 25,
            'includes_agents': True,
            'monthly_price': 79.00,
            'yearly_price': 790.00,
            'features': ['Everything in Basic', 'AI Agents', 'Analytics Hub', 'HR & Payroll', 'Priority Support'],
            'display_order': 2
        },
        {
            'name': 'Advanced',
            'slug': 'advanced',
            'max_branches': 10,
            'max_users': 50,
            'includes_agents': True,
            'monthly_price': 149.00,
            'yearly_price': 1490.00,
            'features': ['Everything in Premium', 'API Access', 'Custom Reports', 'Dedicated Support'],
            'display_order': 3
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'max_branches': 999999,
            'max_users': 999999,
            'includes_agents': True,
            'monthly_price': 0.00,
            'yearly_price': 0.00,
            'features': ['Unlimited Everything', 'Custom Integrations', 'SLA Guarantee', 'Dedicated Account Manager'],
            'display_order': 4
        }
    ]
    
    created = 0
    for plan_data in plans:
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == plan_data['slug']).first()
        if not existing:
            plan = SubscriptionPlan(
                name=plan_data['name'],
                slug=plan_data['slug'],
                max_branches=plan_data['max_branches'],
                max_users=plan_data['max_users'],
                includes_agents=plan_data['includes_agents'],
                monthly_price=Decimal(str(plan_data['monthly_price'])),
                yearly_price=Decimal(str(plan_data['yearly_price'])),
                features=json.dumps(plan_data['features']),
                display_order=plan_data['display_order']
            )
            db.add(plan)
            created += 1
    
    db.commit()
    
    return {"message": f"Initialized {created} plans"}
