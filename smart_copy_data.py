#!/usr/bin/env python
# coding: utf-8

"""
Smart Database Data Copy Utility
Copies data between databases with schema mapping to handle column differences
"""

import sqlite3
import os
from datetime import datetime

def get_table_columns(conn, table_name):
    """Get column information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [(row[1], row[2]) for row in cursor.fetchall()]  # [(name, type), ...]

def smart_copy_table_data(source_conn, dest_conn, table_name, column_mapping=None):
    """Copy data with smart column mapping"""
    try:
        # Get column info from both tables
        source_columns = dict(get_table_columns(source_conn, table_name))
        dest_columns = dict(get_table_columns(dest_conn, table_name))
        
        # Find common columns or use mapping
        if column_mapping and table_name in column_mapping:
            # Use provided mapping
            mapped_columns = []
            select_columns = []
            for dest_col, source_col in column_mapping[table_name].items():
                if source_col in source_columns and dest_col in dest_columns:
                    mapped_columns.append(dest_col)
                    select_columns.append(source_col)
        else:
            # Use common columns
            common_columns = set(source_columns.keys()).intersection(set(dest_columns.keys()))
            mapped_columns = list(common_columns)
            select_columns = list(common_columns)
        
        if not mapped_columns:
            print(f"  {table_name}: No compatible columns found")
            return 0
        
        # Get data from source
        select_sql = f"SELECT {', '.join(select_columns)} FROM {table_name}"
        source_cursor = source_conn.cursor()
        source_cursor.execute(select_sql)
        rows = source_cursor.fetchall()
        
        if not rows:
            print(f"  {table_name}: No data to copy")
            return 0
        
        # Insert into destination
        placeholders = ', '.join(['?' for _ in mapped_columns])
        columns_str = ', '.join(mapped_columns)
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        dest_cursor = dest_conn.cursor()
        dest_cursor.executemany(insert_sql, rows)
        dest_conn.commit()
        
        print(f"  {table_name}: Copied {len(rows)} records using columns: {', '.join(mapped_columns)}")
        return len(rows)
        
    except Exception as e:
        print(f"  {table_name}: Error - {e}")
        return 0

def smart_copy_database_data():
    """Copy data with intelligent column mapping"""
    source_db = "crm_database.db"
    dest_db = "crm.db"
    
    if not os.path.exists(source_db) or not os.path.exists(dest_db):
        print(f"Database files not found!")
        return False
    
    print(f"Smart copying data from {source_db} to {dest_db}...")
    
    # Define column mappings for problematic tables
    column_mapping = {
        'contacts': {
            # dest_column: source_column
            'id': 'id',
            'account_id': 'account_id',
            'email': 'email',
            'phone': 'phone',
            'title': 'title',
            'created_date': 'created_date',
            'modified_date': 'modified_date'
        },
        'qpl': {
            'id': 'id',
            'nsn': 'nsn',
            'fsc': 'fsc',
            'manufacturer': 'manufacturer',
            'part_number': 'part_number',
            'cage_code': 'cage_code',
            'description': 'description',
            'specifications': 'specifications',
            'qualification_date': 'qualification_date',
            'expiration_date': 'expiration_date',
            'status': 'status',
            'created_date': 'created_date',
            'modified_date': 'modified_date'
        },
        'interactions': {
            'id': 'id',
            'subject': 'subject',
            'type': 'type',
            'interaction_date': 'interaction_date',
            'duration_minutes': 'duration_minutes',
            'location': 'location',
            'outcome': 'outcome',
            'contact_id': 'contact_id',
            'account_id': 'account_id',
            'opportunity_id': 'opportunity_id',
            'created_by': 'created_by',
            'created_date': 'created_date'
        }
    }
    
    try:
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
        
        print(f"Smart copying {len(common_tables)} tables:")
        
        total_copied = 0
        for table in sorted(common_tables):
            if table.endswith('_backup'):
                continue
                
            copied = smart_copy_table_data(source_conn, dest_conn, table, column_mapping)
            total_copied += copied
        
        source_conn.close()
        dest_conn.close()
        
        print(f"\nSmart copy completed! Total records: {total_copied}")
        return True
        
    except Exception as e:
        print(f"Error during smart copy: {e}")
        return False

if __name__ == "__main__":
    print("=== Smart Database Data Copy ===")
    success = smart_copy_database_data()
    if success:
        print("✅ Smart copy completed!")
    else:
        print("❌ Smart copy failed!")
    print("=== Copy Complete ===")
