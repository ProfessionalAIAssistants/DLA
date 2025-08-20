#!/usr/bin/env python
# coding: utf-8

"""
Direct Database Checker - bypasses terminal issues
This script directly connects to the database and checks for data.
"""

import sqlite3
import os
import json
from pathlib import Path

def main():
    print("=== DIRECT DATABASE DIAGNOSTIC ===")
    
    # Check both database files
    db_files = ['crm.db', 'crm_database.db']
    results = {}
    
    for db_file in db_files:
        print(f"\nChecking {db_file}...")
        if not os.path.exists(db_file):
            print(f"  ❌ {db_file} NOT FOUND")
            results[db_file] = {"status": "not_found"}
            continue
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"  ✅ {db_file} found with {len(tables)} tables")
            
            table_info = {}
            total_records = 0
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"    📊 {table}: {count} records")
                    table_info[table] = count
                    total_records += count
                except Exception as e:
                    print(f"    ❌ {table}: Error - {str(e)}")
                    table_info[table] = f"Error: {str(e)}"
            
            results[db_file] = {
                "status": "found",
                "tables": table_info,
                "total_records": total_records
            }
            
            # Check for key tables
            key_tables = ['accounts', 'opportunities', 'interactions', 'projects']
            missing_tables = [t for t in key_tables if t not in tables]
            if missing_tables:
                print(f"    ⚠️  Missing key tables: {', '.join(missing_tables)}")
            
            conn.close()
            
        except Exception as e:
            print(f"  ❌ Error accessing {db_file}: {str(e)}")
            results[db_file] = {"status": "error", "error": str(e)}
    
    # Check PDF files
    print(f"\nChecking PDF files...")
    to_process = Path("To Process")
    if to_process.exists():
        pdf_files = list(to_process.glob("*.pdf")) + list(to_process.glob("*.PDF"))
        print(f"  📁 Found {len(pdf_files)} PDF files")
        for pdf in pdf_files:
            print(f"    - {pdf.name}")
        results["pdf_files"] = {"count": len(pdf_files), "files": [p.name for p in pdf_files]}
    else:
        print(f"  ❌ 'To Process' directory not found")
        results["pdf_files"] = {"count": 0, "error": "Directory not found"}
    
    # Check critical files
    print(f"\nChecking critical files...")
    critical_files = ['crm_app.py', 'crm_data.py', 'DIBBs.py', 'pdf_processor.py']
    for file in critical_files:
        exists = os.path.exists(file)
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status} {file}")
    
    # Save results
    with open('diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to diagnostic_results.json")
    print("=== DIAGNOSTIC COMPLETE ===")

if __name__ == "__main__":
    main()
