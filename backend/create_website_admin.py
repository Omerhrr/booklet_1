#!/usr/bin/env python3
"""
Create Website Admin Account - Platform Owner

This script creates a website admin account for the SaaS platform owner.
Website admins can manage blog posts, website content, view all users, etc.

Usage:
    python create_website_admin.py
    python create_website_admin.py --email admin@example.com --password secret --name "Admin"
"""
import sys
import os
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, WebsiteUser, Business


def create_admin(email: str, password: str, name: str, username: str = None):
    """Create or update a website admin account"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"\n✅ Found existing user: {email}")
            
            # Ensure they have a business_id (create dummy if needed)
            if not existing_user.business_id:
                dummy_business = db.query(Business).filter(Business.name == "Platform Admin").first()
                if not dummy_business:
                    dummy_business = Business(name="Platform Admin", email=email, plan="enterprise")
                    db.add(dummy_business)
                    db.flush()
                existing_user.business_id = dummy_business.id
                db.commit()
                print(f"Linked user to Platform Admin business")
            
            # Create/update website admin record
            existing_admin = db.query(WebsiteUser).filter(
                WebsiteUser.user_id == existing_user.id
            ).first()
            
            if existing_admin:
                existing_admin.is_website_admin = True
                print("Updated existing admin record")
            else:
                admin = WebsiteUser(user_id=existing_user.id, is_website_admin=True)
                db.add(admin)
                print("Created new admin record")
            
            db.commit()
            
            print(f"\n{'='*50}")
            print(f"✅ WEBSITE ADMIN READY")
            print(f"{'='*50}")
            print(f"  Email: {email}")
            print(f"  Password: (use your existing password)")
            print(f"{'='*50}")
            print(f"\nLogin: http://localhost:5001/auth/login")
            print(f"Admin: http://localhost:5001/admin")
            return
        
        # Create dummy business for website admin
        dummy_business = db.query(Business).filter(Business.name == "Platform Admin").first()
        if not dummy_business:
            dummy_business = Business(
                name="Platform Admin",
                email=email,
                plan="enterprise"
            )
            db.add(dummy_business)
            db.flush()
            print(f"Created business 'Platform Admin'")
        
        # Generate username
        if not username:
            username = email.split('@')[0]
            counter = 1
            original = username
            while db.query(User).filter(User.username == username).first():
                username = f"{original}{counter}"
                counter += 1
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=name,
            is_superuser=True,
            is_active=True,
            business_id=dummy_business.id
        )
        db.add(user)
        db.flush()
        
        # Create website admin record
        admin = WebsiteUser(user_id=user.id, is_website_admin=True)
        db.add(admin)
        db.commit()
        
        print(f"\n{'='*50}")
        print(f"✅ WEBSITE ADMIN CREATED")
        print(f"{'='*50}")
        print(f"  Name: {name}")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"{'='*50}")
        print(f"\nLogin: http://localhost:5001/auth/login")
        print(f"Admin: http://localhost:5001/admin")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def interactive():
    print("\n" + "="*50)
    print("  BOOKLET SAAS - Website Admin Creator")
    print("="*50)
    print("\nThis creates a WEBSITE ADMIN account for the")
    print("platform owner (you). This is SEPARATE from")
    print("ERP business users who manage their companies.\n")
    
    email = input("Email: ").strip()
    if not email:
        print("Email is required")
        return
    
    name = input("Full Name: ").strip()
    if not name:
        print("Name is required")
        return
    
    username = input("Username (blank for auto): ").strip() or None
    password = getpass.getpass("Password: ")
    if not password:
        print("Password is required")
        return
    
    confirm = getpass.getpass("Confirm: ")
    if password != confirm:
        print("Passwords don't match")
        return
    
    create_admin(email, password, name, username)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", "-e")
    parser.add_argument("--password", "-p")
    parser.add_argument("--name", "-n")
    parser.add_argument("--username", "-u")
    args = parser.parse_args()
    
    if args.email and args.password and args.name:
        create_admin(args.email, args.password, args.name, args.username)
    else:
        interactive()
