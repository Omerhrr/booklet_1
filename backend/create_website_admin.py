#!/usr/bin/env python3
"""
Create Website Admin Account

This script creates a website admin account for the SaaS platform owner.
Website admins can manage blog posts, website content, view all users, etc.

Usage:
    python create_website_admin.py --email admin@example.com --password yourpassword --name "Admin Name"

Or run interactively to create a new admin.
"""
import sys
import os
import argparse

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, WebsiteUser


def create_admin(email: str, password: str, name: str, username: str = None):
    """Create or update a website admin account"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"User with email {email} already exists.")
            
            # Check if already a website admin
            existing_admin = db.query(WebsiteUser).filter(
                WebsiteUser.user_id == existing_user.id
            ).first()
            
            if existing_admin:
                if not existing_admin.is_website_admin:
                    existing_admin.is_website_admin = True
                    db.commit()
                    print(f"Updated {email} to be a website admin.")
                else:
                    print(f"{email} is already a website admin.")
            else:
                # Create website admin record
                admin = WebsiteUser(
                    user_id=existing_user.id,
                    is_website_admin=True
                )
                db.add(admin)
                db.commit()
                print(f"Created website admin record for {email}.")
            
            print(f"\nWebsite Admin Login:")
            print(f"  Email: {email}")
            print(f"  Password: (your existing password)")
            print(f"\nLogin at: http://localhost:5001/auth/login")
            return
        
        # Generate username from email if not provided
        if not username:
            username = email.split('@')[0]
            
            # Ensure unique username
            counter = 1
            original_username = username
            while db.query(User).filter(User.username == username).first():
                username = f"{original_username}{counter}"
                counter += 1
        
        # Create new admin user (no business_id - they're the platform owner)
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=name,
            is_superuser=True,  # Platform admin is superuser
            is_active=True,
            business_id=None  # No business - they manage the platform
        )
        db.add(user)
        db.flush()  # Get the user ID
        
        # Create website admin record
        admin = WebsiteUser(
            user_id=user.id,
            is_website_admin=True
        )
        db.add(admin)
        db.commit()
        
        print(f"\n✅ Website Admin Created Successfully!")
        print(f"=" * 40)
        print(f"  Name: {name}")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"=" * 40)
        print(f"\nLogin at: http://localhost:5001/auth/login")
        print(f"Admin Dashboard: http://localhost:5001/admin")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Create a website admin account')
    parser.add_argument('--email', '-e', help='Admin email address')
    parser.add_argument('--password', '-p', help='Admin password')
    parser.add_argument('--name', '-n', help='Admin full name')
    parser.add_argument('--username', '-u', help='Admin username (optional, derived from email if not provided)')
    
    args = parser.parse_args()
    
    if args.email and args.password and args.name:
        create_admin(args.email, args.password, args.name, args.username)
    else:
        print("Booklet SaaS - Website Admin Creator")
        print("=" * 40)
        print("\nThis will create a website admin account for managing the platform.")
        print("Website admins can: manage blog posts, website content, view all users, etc.\n")
        
        email = input("Email address: ").strip()
        if not email:
            print("Email is required.")
            return
        
        name = input("Full name: ").strip()
        if not name:
            print("Name is required.")
            return
        
        username = input("Username (press Enter to use email prefix): ").strip()
        if not username:
            username = None
        
        import getpass
        password = getpass.getpass("Password: ").strip()
        if not password:
            print("Password is required.")
            return
        
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("Passwords do not match.")
            return
        
        create_admin(email, password, name, username)


if __name__ == "__main__":
    main()
