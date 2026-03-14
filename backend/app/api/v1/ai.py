"""
AI Assistant API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user, PlanFeatureChecker
from app.models import User, Permission, Role, RolePermission, UserBranchRole
from app.services.ai_service import AIService
from app.services.permission_service import PermissionService, seed_permissions

router = APIRouter(prefix="/ai", tags=["AI Assistant"], dependencies=[Depends(PlanFeatureChecker("ai"))])
logger = logging.getLogger(__name__)


# ==================== SCHEMAS ====================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: Optional[int] = None
    tokens_used: Optional[int] = None
    blocked: Optional[bool] = None
    error: Optional[str] = None
    code: Optional[str] = None


class AISettingsCreate(BaseModel):
    provider: str = 'zai'  # zai, openai, gemini, claude
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    is_enabled: bool = False
    allow_data_access: bool = True
    daily_request_limit: int = 1000
    monthly_request_limit: int = 30000


class AISettingsUpdate(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_enabled: Optional[bool] = None
    allow_data_access: Optional[bool] = None
    daily_request_limit: Optional[int] = None
    monthly_request_limit: Optional[int] = None


class ConversationResponse(BaseModel):
    id: int
    title: str
    is_archived: bool
    is_starred: bool
    created_at: datetime
    updated_at: datetime
    message_count: int


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    has_error: bool


class UsageStatsResponse(BaseModel):
    period_days: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    by_provider: dict


# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings")
async def get_ai_settings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get AI settings for the current business"""
    # Only users with ai:configure permission can view settings
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'ai:configure'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view AI settings"
        )
    
    ai_service = AIService(db)
    settings = ai_service.get_settings(current_user.business_id)
    
    if not settings:
        return {
            "configured": False,
            "provider": None,
            "model_name": None,
            "is_enabled": False,
            "allow_data_access": True,
            "daily_request_limit": 1000,
            "monthly_request_limit": 30000,
            "max_tokens": 4096,
            "temperature": 0.7
        }
    
    return {
        "configured": True,
        "id": settings.id,
        "provider": settings.provider,
        "model_name": settings.model_name,
        "is_enabled": settings.is_enabled,
        "allow_data_access": settings.allow_data_access,
        "daily_request_limit": settings.daily_request_limit,
        "monthly_request_limit": settings.monthly_request_limit,
        "max_tokens": settings.max_tokens,
        "temperature": float(settings.temperature) if settings.temperature else 0.7,
        "configured_by": settings.configured_by,
        "created_at": settings.created_at.isoformat() if settings.created_at else None,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
    }


@router.post("/settings")
async def create_or_update_ai_settings(
    request: AISettingsCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create or update AI settings (admin only)"""
    # Only users with ai:configure permission can modify settings
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'ai:configure'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to configure AI settings"
        )
    
    ai_service = AIService(db)
    
    try:
        settings = ai_service.create_or_update_settings(
            business_id=current_user.business_id,
            configured_by=current_user.id,
            provider=request.provider,
            api_key=request.api_key,
            api_endpoint=request.api_endpoint,
            model_name=request.model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            is_enabled=request.is_enabled,
            allow_data_access=request.allow_data_access,
            daily_request_limit=request.daily_request_limit,
            monthly_request_limit=request.monthly_request_limit
        )
        
        return {
            "success": True,
            "id": settings.id,
            "message": "AI settings saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save AI settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )


@router.patch("/settings")
async def update_ai_settings(
    request: AISettingsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update specific AI settings"""
    perm_service = PermissionService(db)
    if not perm_service.user_has_permission(current_user, 'ai:configure'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to configure AI settings"
        )
    
    ai_service = AIService(db)
    settings = ai_service.get_settings(current_user.business_id)
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI settings not found. Please create settings first."
        )
    
    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    
    if 'api_key' in update_data and update_data['api_key']:
        settings.api_key_encrypted = ai_service._encrypt_api_key(update_data['api_key'])
    
    for field in ['provider', 'api_endpoint', 'model_name', 'max_tokens', 'temperature',
                  'is_enabled', 'allow_data_access', 'daily_request_limit', 'monthly_request_limit']:
        if field in update_data:
            setattr(settings, field, update_data[field])
    
    db.commit()
    
    return {"success": True, "message": "Settings updated"}


# ==================== CHAT ENDPOINTS ====================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Send a message to the AI assistant"""
    ai_service = AIService(db)

    response, status_code = await ai_service.chat(
        user=current_user,
        message=request.message,
        conversation_id=request.conversation_id
    )

    if status_code != 200:
        # Return the specific error message from the service
        raise HTTPException(
            status_code=status_code,
            detail=response.get('error', 'Failed to get AI response')
        )

    return ChatResponse(**response)


@router.get("/conversations")
async def get_conversations(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all conversations for the current user"""
    ai_service = AIService(db)
    conversations = ai_service.get_user_conversations(
        user_id=current_user.id,
        business_id=current_user.business_id,
        include_archived=include_archived
    )
    
    # Get message count for each conversation
    result = []
    for conv in conversations:
        from sqlalchemy import func
        from app.models import AIMessage
        msg_count = db.query(func.count(AIMessage.id)).filter(
            AIMessage.conversation_id == conv.id
        ).scalar()
        
        result.append({
            "id": conv.id,
            "title": conv.title,
            "is_archived": conv.is_archived,
            "is_starred": conv.is_starred,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "message_count": msg_count
        })
    
    return {"conversations": result}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific conversation with messages"""
    ai_service = AIService(db)
    messages = ai_service.get_conversation_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit
    )
    
    if not messages and conversation_id:
        # Check if conversation exists but belongs to another user
        from app.models import AIConversation
        conv = db.query(AIConversation).filter(
            AIConversation.id == conversation_id
        ).first()
        if conv and conv.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation"
            )
    
    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "has_error": msg.has_error
            }
            for msg in messages
        ]
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a conversation"""
    ai_service = AIService(db)
    success = ai_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you do not have permission to delete it"
        )
    
    return {"success": True, "message": "Conversation deleted"}


@router.patch("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Archive or unarchive a conversation"""
    from app.models import AIConversation
    
    conv = db.query(AIConversation).filter(
        AIConversation.id == conversation_id,
        AIConversation.user_id == current_user.id
    ).first()
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conv.is_archived = not conv.is_archived
    db.commit()
    
    return {
        "success": True,
        "is_archived": conv.is_archived,
        "message": "Conversation archived" if conv.is_archived else "Conversation unarchived"
    }


# ==================== USAGE ENDPOINTS ====================

@router.get("/usage")
async def get_usage_stats(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get AI usage statistics"""
    perm_service = PermissionService(db)
    
    # Users with ai:view_usage or ai:configure can view usage
    if not (perm_service.user_has_permission(current_user, 'ai:view_usage') or
            perm_service.user_has_permission(current_user, 'ai:configure')):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view usage statistics"
        )
    
    ai_service = AIService(db)
    stats = ai_service.get_usage_stats(
        business_id=current_user.business_id,
        days=days
    )
    
    return stats


# ==================== PROVIDER INFO ====================

@router.get("/providers")
async def get_available_providers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get list of available AI providers and their models"""
    return {
        "providers": [
            {
                "id": "zai",
                "name": "Z.ai (GLM)",
                "models": [
                    {"id": "glm-5", "name": "GLM-5 (Latest)"},
                    {"id": "glm-4.7", "name": "GLM-4.7"},
                    {"id": "glm-4.6", "name": "GLM-4.6"},
                    {"id": "glm-4.5-air", "name": "GLM-4.5-Air (Recommended)"},
                    {"id": "glm-4.5", "name": "GLM-4.5"},
                ],
                "default_model": "glm-4.5-air",
                "requires_api_key": True,
                "description": "Z.ai GLM models. Get an API key from https://z.ai/ - requires credits."
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "models": [
                    {"id": "gpt-4o", "name": "GPT-4o (Recommended)"},
                    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast)"},
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                    {"id": "gpt-4", "name": "GPT-4"},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                    {"id": "o1-preview", "name": "o1 Preview (Reasoning)"},
                    {"id": "o1-mini", "name": "o1 Mini (Reasoning)"},
                ],
                "default_model": "gpt-4o",
                "requires_api_key": True
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": [
                    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash (Latest)"},
                    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
                    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
                    {"id": "gemini-pro", "name": "Gemini Pro"},
                ],
                "default_model": "gemini-2.0-flash",
                "requires_api_key": True
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "models": [
                    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4 (Latest)"},
                    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
                    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
                ],
                "default_model": "claude-sonnet-4-20250514",
                "requires_api_key": True
            },
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "models": [
                    # Free models
                    {"id": "openrouter/auto", "name": "Auto (Let OpenRouter choose best)"},
                    {"id": "openrouter/auto-r1", "name": "Auto with Reasoning (Free)"},
                    # Popular free models
                    {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash (Free)"},
                    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)"},
                    {"id": "qwen/qwen-2.5-72b-instruct:free", "name": "Qwen 2.5 72B (Free)"},
                    {"id": "deepseek/deepseek-r1:free", "name": "DeepSeek R1 (Free)"},
                    {"id": "stepfun/step-3.5-flash:free", "name": "Step 3.5 Flash (Free)"},
                    # Premium models
                    {"id": "openai/gpt-4o", "name": "GPT-4o via OpenRouter"},
                    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet via OpenRouter"},
                    {"id": "google/gemini-pro", "name": "Gemini Pro via OpenRouter"},
                    {"id": "meta-llama/llama-3.1-405b-instruct", "name": "Llama 3.1 405B"},
                    {"id": "deepseek/deepseek-chat", "name": "DeepSeek Chat"},
                ],
                "default_model": "openrouter/auto",
                "requires_api_key": True,
                "description": "OpenRouter provides access to 200+ AI models. Get an API key from https://openrouter.ai/keys - includes free models!"
            }
        ]
    }


# ==================== FIX PERMISSIONS ====================

@router.post("/fix-permissions")
async def fix_ai_permissions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Fix AI permissions for the current user's admin role.
    This is a one-time fix for existing businesses that don't have AI permissions.
    """
    # First ensure all permissions exist
    seed_permissions(db)
    
    # Get all AI permission IDs
    ai_perm_ids = [p.id for p in db.query(Permission).filter(Permission.name.like("ai:%")).all()]
    
    if not ai_perm_ids:
        return {"success": False, "message": "AI permissions not found in database"}
    
    # Find admin role for current user's business
    admin_role = db.query(Role).filter(
        Role.business_id == current_user.business_id,
        (Role.is_system == True) | (Role.name == "Admin")
    ).first()
    
    if not admin_role:
        # Try to find any role for this business
        admin_role = db.query(Role).filter(
            Role.business_id == current_user.business_id
        ).first()
    
    if not admin_role:
        return {"success": False, "message": "No role found for your business"}
    
    # Ensure user is assigned to this role (using UserBranchRole)
    user_role = db.query(UserBranchRole).filter(
        UserBranchRole.user_id == current_user.id,
        UserBranchRole.role_id == admin_role.id
    ).first()
    
    user_was_assigned = False
    if not user_role:
        # Get user's branch if available
        branch_id = current_user.selected_branch_id if hasattr(current_user, 'selected_branch_id') else None
        if not branch_id:
            # Get first branch of the business
            from app.models import Branch
            first_branch = db.query(Branch).filter(Branch.business_id == current_user.business_id).first()
            branch_id = first_branch.id if first_branch else None
        
        user_role = UserBranchRole(
            user_id=current_user.id, 
            role_id=admin_role.id,
            branch_id=branch_id
        )
        db.add(user_role)
        user_was_assigned = True
    
    # Get existing permission IDs for this role
    existing_perm_ids = [rp.permission_id for rp in db.query(RolePermission).filter(
        RolePermission.role_id == admin_role.id
    ).all()]
    
    # Add missing AI permissions
    added = []
    for perm_id in ai_perm_ids:
        if perm_id not in existing_perm_ids:
            role_perm = RolePermission(role_id=admin_role.id, permission_id=perm_id)
            db.add(role_perm)
            added.append(perm_id)
    
    db.commit()
    
    # Also return the current status
    return {
        "success": True,
        "message": f"Fixed permissions: Added {len(added)} AI permissions to role '{admin_role.name}'",
        "permissions_added": len(added),
        "role_name": admin_role.name,
        "user_assigned_to_role": user_was_assigned,
        "ai_permissions": [p.name for p in db.query(Permission).filter(Permission.id.in_(ai_perm_ids)).all()]
    }


@router.get("/status")
async def get_ai_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get AI status for current user - useful for debugging"""
    perm_service = PermissionService(db)
    ai_service = AIService(db)
    
    # Check permissions
    user_perms = perm_service.get_user_permissions(current_user)
    ai_perms = {p for p in user_perms if p.startswith('ai:')}
    
    # Check settings
    settings = ai_service.get_settings(current_user.business_id)
    
    return {
        "user_id": current_user.id,
        "business_id": current_user.business_id,
        "ai_permissions": list(ai_perms),
        "has_ai_use": "ai:use" in user_perms,
        "has_ai_configure": "ai:configure" in user_perms,
        "settings_exist": settings is not None,
        "is_enabled": settings.is_enabled if settings else False,
        "provider": settings.provider if settings else None,
        "model_name": settings.model_name if settings else None,
    }
