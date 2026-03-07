"""
Script to add AI permissions to existing admin roles
Run this once to fix missing AI permissions for existing businesses
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Permission, Role, RolePermission


def add_ai_permissions():
    db = SessionLocal()
    
    try:
        # First, ensure AI permissions exist
        ai_permissions = [
            {"name": "ai:use", "category": "AI Assistant", "description": "Use AI assistant for chat and analysis"},
            {"name": "ai:configure", "category": "AI Assistant", "description": "Configure AI settings and providers"},
            {"name": "ai:view_usage", "category": "AI Assistant", "description": "View AI usage statistics"},
        ]
        
        print("Checking/Creating AI permissions...")
        for perm_data in ai_permissions:
            existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not existing:
                perm = Permission(**perm_data)
                db.add(perm)
                print(f"  Created permission: {perm_data['name']}")
            else:
                print(f"  Permission exists: {perm_data['name']}")
        
        db.commit()
        
        # Get all AI permission IDs
        ai_perm_ids = [p.id for p in db.query(Permission).filter(Permission.name.like("ai:%")).all()]
        print(f"\nAI Permission IDs: {ai_perm_ids}")
        
        # Find all Admin roles (is_system=True or name='Admin')
        admin_roles = db.query(Role).filter(
            (Role.is_system == True) | (Role.name == "Admin")
        ).all()
        
        print(f"\nFound {len(admin_roles)} admin roles to update")
        
        for role in admin_roles:
            print(f"\nProcessing role: {role.name} (ID: {role.id}, Business: {role.business_id})")
            
            # Get existing permission IDs for this role
            existing_perm_ids = [rp.permission_id for rp in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()]
            print(f"  Existing permissions count: {len(existing_perm_ids)}")
            
            # Add missing AI permissions
            added = 0
            for perm_id in ai_perm_ids:
                if perm_id not in existing_perm_ids:
                    role_perm = RolePermission(role_id=role.id, permission_id=perm_id)
                    db.add(role_perm)
                    added += 1
                    print(f"  Added permission ID {perm_id} to role")
            
            if added > 0:
                print(f"  Added {added} new permissions")
            else:
                print(f"  No new permissions needed")
        
        db.commit()
        print("\n✅ Successfully added AI permissions to all admin roles!")
        
        # Verify
        print("\n--- Verification ---")
        for role in admin_roles:
            perm_count = db.query(RolePermission).filter(RolePermission.role_id == role.id).count()
            ai_perm_count = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id.in_(ai_perm_ids)
            ).count()
            print(f"Role '{role.name}': {perm_count} total permissions, {ai_perm_count} AI permissions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_ai_permissions()
