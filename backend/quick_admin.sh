#!/bin/bash
# Quick script to create website admin
# Usage: ./quick_admin.sh email@example.com YourPassword "Your Name"

cd "$(dirname "$0")"

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: ./quick_admin.sh <email> <password> <name>"
    echo "Example: ./quick_admin.sh admin@booklet.com mypassword 'Platform Admin'"
    exit 1
fi

python3 -c "
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, WebsiteUser

db = SessionLocal()
email = '$1'
password = '$2'
name = '$3'
username = email.split('@')[0]

# Make username unique
counter = 1
original_username = username
while db.query(User).filter(User.username == username).first():
    username = f'{original_username}{counter}'
    counter += 1

# Check if user exists
existing = db.query(User).filter(User.email == email).first()
if existing:
    # Check/create website admin
    wa = db.query(WebsiteUser).filter(WebsiteUser.user_id == existing.id).first()
    if wa:
        wa.is_website_admin = True
    else:
        wa = WebsiteUser(user_id=existing.id, is_website_admin=True)
        db.add(wa)
    db.commit()
    print()
    print('✅ Updated existing user to website admin!')
else:
    # Create new user
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=name,
        is_superuser=True,
        is_active=True,
        business_id=None
    )
    db.add(user)
    db.flush()
    wa = WebsiteUser(user_id=user.id, is_website_admin=True)
    db.add(wa)
    db.commit()
    print()
    print('✅ Created new website admin!')
    print('   Password: ' + password)

print()
print('=' * 40)
print('Website Admin Credentials:')
print('  Email: ' + email)
print('=' * 40)
print('Login at: http://localhost:5001/auth/login')
print('Admin Panel: http://localhost:5001/admin')
print()
db.close()
"
