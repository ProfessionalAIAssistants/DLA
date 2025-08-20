#!/usr/bin/env python
# coding: utf-8

"""
Database Table Status Checker
This script checks the existing tables in the database and counts records in each table.
"""

import os
import sqlite3
import json
from pathlib import Path

def get_db_path():
    """Get the path to the SQLite database file"""
    # Try common locations
    possible_paths = [
        'crm.db',
        'data/crm.db',
        'database/crm.db',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def check_tables():
    """Check existing tables and count records"""
    db_path = get_db_path()
    
    if not db_path:
        print("ERROR: Database file not found!")
        return
    
    print(f"Using database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall() if not table[0].startswith('sqlite_')]
        
        print(f"Found {len(tables)} tables in the database:")
        
        # Check record count for each table
        results = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} records")
                
                # Get sample records if table has data
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    columns = [desc[0] for desc in cursor.description]
                    print(f"    Columns: {', '.join(columns)}")
                
                results[table] = {
                    "count": count,
                    "status": "OK"
                }
            except sqlite3.Error as e:
                print(f"  - {table}: ERROR - {str(e)}")
                results[table] = {
                    "count": 0,
                    "status": f"Error: {str(e)}"
                }
        
        # Save results to JSON file
        with open('database_status.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to database_status.json")
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Database Table Status Checker ===")
    check_tables()
    print("=== Check Complete ===")
