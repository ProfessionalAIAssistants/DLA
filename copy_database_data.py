#!/usr/bin/env python
# coding: utf-8

"""
Database Data Copy Utility
Copies all data from crm_database.db to crm.db to fix the empty database issue
"""

import sqlite3
import os
from datetime import datetime

def copy_table_data(source_conn, dest_conn, table_name):
    """Copy all data from one table to another"""
    try:
        # Get all data from source table
        source_cursor = source_conn.cursor()
        source_cursor.execute(f"SELECT * FROM {table_name}")
        rows = source_cursor.fetchall()
        
        if not rows:
            print(f"  {table_name}: No data to copy")
            return 0
            
        # Get column names
        source_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in source_cursor.fetchall()]
        
        # Prepare insert statement
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insert data into destination
        dest_cursor = dest_conn.cursor()
        dest_cursor.executemany(insert_sql, rows)
        dest_conn.commit()
        
        print(f"  {table_name}: Copied {len(rows)} records")
        return len(rows)
        
    except Exception as e:
        print(f"  {table_name}: Error - {e}")
        return 0

def copy_database_data():
    """Copy all data from crm_database.db to crm.db"""
    source_db = "crm_database.db"
    dest_db = "crm.db"
    
    if not os.path.exists(source_db):
        print(f"Source database {source_db} not found!")
        return False
        
    if not os.path.exists(dest_db):
        print(f"Destination database {dest_db} not found!")
        return False
    
    print(f"Copying data from {source_db} to {dest_db}...")
    print(f"Started at: {datetime.now()}")
    
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(source_db)
        dest_conn = sqlite3.connect(dest_db)
        
        # Get list of common tables (that exist in both databases)
        source_cursor = source_conn.cursor()
        dest_cursor = dest_conn.cursor()
        
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        source_tables = set(row[0] for row in source_cursor.fetchall())
        
        dest_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        dest_tables = set(row[0] for row in dest_cursor.fetchall())
        
        # Find common tables
        common_tables = source_tables.intersection(dest_tables)
        
        print(f"Found {len(common_tables)} common tables to copy:")
        
        total_copied = 0
        for table in sorted(common_tables):
            # Skip backup tables
            if table.endswith('_backup'):
                print(f"  {table}: Skipping backup table")
                continue
                
            copied = copy_table_data(source_conn, dest_conn, table)
            total_copied += copied
        
        source_conn.close()
        dest_conn.close()
        
        print(f"\nData copy completed!")
        print(f"Total records copied: {total_copied}")
        print(f"Finished at: {datetime.now()}")
        
        return True
        
    except Exception as e:
        print(f"Error during data copy: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Data Copy Utility ===")
    success = copy_database_data()
    if success:
        print("✅ Data copy completed successfully!")
        print("Your CRM application should now show the data.")
    else:
        print("❌ Data copy failed!")
    print("=== Copy Complete ===")
