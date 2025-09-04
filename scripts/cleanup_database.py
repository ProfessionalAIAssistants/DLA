#!/usr/bin/env python3
"""
Database Cleanup Script
Removes all data from specified tables while preserving table structures
"""

import sqlite3
import os
from datetime import datetime

def cleanup_database():
    """Clear data from specified tables while keeping structures"""
    
    # Check which database file exists
    db_files = ['crm_database.db', 'crm.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("❌ No database file found (checked: crm_database.db, crm.db)")
        return False
    
    print(f"🔧 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tables to clear (data only, keep structure)
        tables_to_clear = [
            'tasks',
            'opportunities', 
            'projects',
            'interactions',
            'rfqs'  # This is the quotes table
        ]
        
        print(f"🗑️ Clearing data from {len(tables_to_clear)} tables...")
        
        # Check which tables exist and clear them
        for table_name in tables_to_clear:
            try:
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    # Count records before deletion
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count_before = cursor.fetchone()[0]
                    
                    # Clear the table data
                    cursor.execute(f"DELETE FROM {table_name}")
                    
                    # Reset auto-increment counter
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                    
                    print(f"  ✅ {table_name}: Removed {count_before} records")
                else:
                    print(f"  ⚠️ {table_name}: Table not found")
                    
            except sqlite3.Error as e:
                print(f"  ❌ {table_name}: Error - {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify tables are empty
        print(f"\n📊 Verification:")
        for table_name in tables_to_clear:
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    status = "✅" if count == 0 else "❌"
                    print(f"  {status} {table_name}: {count} records remaining")
            except sqlite3.Error:
                print(f"  ⚠️ {table_name}: Could not verify")
        
        conn.close()
        print(f"\n🎉 Database cleanup completed successfully!")
        print(f"📝 All table structures preserved and ready for new data")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DLA CRM Database Cleanup")
    print("=" * 50)
    print("This will remove all data from:")
    print("  • Tasks")
    print("  • Opportunities") 
    print("  • Projects")
    print("  • Interactions")
    print("  • Quotes (RFQs)")
    print("\nTable structures will be preserved.")
    print("=" * 50)
    
    cleanup_database()
