#!/usr/bin/env python
# coding: utf-8

"""
Projects Table Column Fix
Adds missing columns to the projects table that the application expects
"""

import sqlite3
import os

def add_missing_project_columns():
    """Add all missing columns to the projects table"""
    db_path = "crm.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    print("Adding missing columns to projects table...")
    
    # Define missing columns that the application expects
    missing_columns = [
        ('summary', 'TEXT'),
        ('vendor_id', 'INTEGER'),
        ('parent_project_id', 'INTEGER'),
        ('budget', 'REAL'),
        ('actual_cost', 'REAL'),
        ('progress_percentage', 'INTEGER CHECK(progress_percentage >= 0 AND progress_percentage <= 100)'),
        ('project_manager', 'TEXT'),
        ('team_members', 'TEXT'),
        ('notes', 'TEXT'),
        ('completion_date', 'DATE'),
        ('last_modified', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(projects)")
        existing_columns = set(row[1] for row in cursor.fetchall())
        
        added_count = 0
        for column_name, column_type in missing_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                    added_count += 1
                except Exception as e:
                    print(f"❌ Error adding {column_name}: {e}")
            else:
                print(f"⏭️ Column {column_name} already exists")
        
        conn.commit()
        conn.close()
        
        print(f"\nCompleted! Added {added_count} missing columns to projects table.")
        return True
        
    except Exception as e:
        print(f"Error updating projects table: {e}")
        return False

if __name__ == "__main__":
    print("=== Projects Table Column Fix ===")
    success = add_missing_project_columns()
    
    if success:
        print("✅ Projects table updated successfully!")
        
        # Verify the fix
        print("\nVerifying columns...")
        import sqlite3
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Projects table now has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col}")
        conn.close()
        
    else:
        print("❌ Projects table update failed!")
    
    print("=== Fix Complete ===")
