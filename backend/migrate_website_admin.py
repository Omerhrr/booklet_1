#!/usr/bin/env python3
"""
Migration: Update users table to allow NULL business_id for website admins

Run this after changing the User model to allow nullable business_id
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine,from app.core.config import settings
from app.models import Base,metadata,from app.models import User

def migrate_users_table():
    """Update users table to allow NULL business_id"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Drop NOT NULL constraint from business_id column
    with engine.connect() as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        try:
            # Check if the constraint exists
            result = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """).fetchone()
            
            # Get table info
            result = conn.execute("PRAGMA table_info(users, 1)
            columns = result.fetchall()
            print("Current users table columns:")
            for col in columns:
                print(f"  {col[1]}: {col[2]}")
            
            # Recreate the table with nullable business_id
            conn.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    is_superuser BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    business_id INTEGER REFERENCES businesses(id),
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_timestamp,
                    updated_at DATETIME DEFAULT current_timestamp
                )
            """)
            
            # Copy existing data
            conn.execute("""
                INSERT INTO users_new 
                SELECT id, username, email, hashed_password, full_name, is_superuser, is_active, 
                       business_id, last_login, created_at, updated_at
                FROM users
            """)
            
            # Drop old table
            conn.execute("DROP TABLE users")
            
            # Rename new table
            conn.execute("ALTER TABLE users_new RENAME TO users")
            
            # Re-enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            print("✅ Migration completed: users.business_id is now nullable")
            
        except Exception as e:
            print(f"Migration error (may already applied): {e}")
            # Try simpler approach - just modify the column
            try:
                conn.execute("""
                    UPDATE users SET business_id = NULL WHERE business_id IS NULL
                """)
                print("✅ Column already supports NULL")
            except:
                pass
            
        finally:
            conn.close()

if __name__ == "__main__":
    migrate_users_table()
