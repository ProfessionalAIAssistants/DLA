#!/usr/bin/env python
# coding: utf-8

"""
Schema Comparison Utility
Compares table schemas between crm_database.db and crm.db
"""

import sqlite3
import os

def get_table_schema(conn, table_name):
    """Get the schema of a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row[2] for row in cursor.fetchall()}  # {column_name: type}

def compare_schemas():
    """Compare schemas between the two databases"""
    source_db = "crm_database.db"
    dest_db = "crm.db"
    
    if not os.path.exists(source_db) or not os.path.exists(dest_db):
        print("One or both databases not found!")
        return
    
    source_conn = sqlite3.connect(source_db)
    dest_conn = sqlite3.connect(dest_db)
    
    # Get common tables
    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    source_tables = set(row[0] for row in source_cursor.fetchall())
    
    dest_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    dest_tables = set(row[0] for row in dest_cursor.fetchall())
    
    common_tables = source_tables.intersection(dest_tables)
    
    print("=== Schema Comparison ===")
    
    for table in sorted(common_tables):
        if table.endswith('_backup'):
            continue
            
        source_schema = get_table_schema(source_conn, table)
        dest_schema = get_table_schema(dest_conn, table)
        
        print(f"\n📋 Table: {table}")
        
        # Check for missing columns in destination
        missing_in_dest = set(source_schema.keys()) - set(dest_schema.keys())
        if missing_in_dest:
            print(f"  ❌ Missing in crm.db: {', '.join(missing_in_dest)}")
        
        # Check for extra columns in destination
        extra_in_dest = set(dest_schema.keys()) - set(source_schema.keys())
        if extra_in_dest:
            print(f"  ➕ Extra in crm.db: {', '.join(extra_in_dest)}")
        
        if not missing_in_dest and not extra_in_dest:
            print(f"  ✅ Schemas match")
    
    source_conn.close()
    dest_conn.close()

if __name__ == "__main__":
    compare_schemas()
