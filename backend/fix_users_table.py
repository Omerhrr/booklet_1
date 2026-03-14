#!/usr/bin/env python3
"""
Fix users table to allow NULL business_id for website admins

This script makes the business_id column nullable in the users table.
"""
import sqlite3
import os

def fix_users_table():
    db_path = os.path.join(os.path.dirname(__file__), 'erp.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Creating new database...")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print("Current users table structure:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (notnull={col[3]})")
    
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # Create new table with nullable business_id
    print("\nRecreating users table with nullable business_id...")
    
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_superuser INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            business_id INTEGER,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Copy data
    cursor.execute("""
        INSERT INTO users_new 
        SELECT id, username, email, hashed_password, full_name, is_superuser, is_active, 
               business_id, last_login, created_at, updated_at
        FROM users
    """)
    
    # Drop old table
    cursor.execute("DROP TABLE users")
    
    # Rename new table
    cursor.execute("ALTER TABLE users_new RENAME TO users")
    
    conn.commit()
    conn.close()
    
    print("✅ Done! users.business_id is now nullable.")
    print("You can now create website admins.")

if __name__ == "__main__":
    fix_users_table()
