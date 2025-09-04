#!/usr/bin/env python3
"""
Database Analysis Tool for CRM System
Analyzes database structure, checks for duplicates, and generates human-readable documentation
"""

import sqlite3
import json
from datetime import datetime

def analyze_database():
    """Comprehensive database analysis"""
    print("🔍 Starting Database Analysis...")
    print("=" * 60)
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 DATABASE OVERVIEW")
    print(f"Database File: data/crm.db")
    print(f"Total Tables: {len(tables)}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_records = 0
    db_structure = {}
    
    for table in tables:
        print(f"📋 TABLE: {table}")
        print("-" * 50)
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        total_records += row_count
        
        table_info = {
            'row_count': row_count,
            'columns': []
        }
        
        print(f"📈 Records: {row_count:,}")
        print("📝 Columns:")
        
        for col in columns:
            col_id, name, data_type, not_null, default_val, is_pk = col
            constraints = []
            if is_pk:
                constraints.append('PRIMARY KEY')
            if not_null:
                constraints.append('NOT NULL')
            if default_val:
                constraints.append(f'DEFAULT {default_val}')
                
            table_info['columns'].append({
                'name': name,
                'type': data_type,
                'constraints': constraints
            })
            
            constraint_str = ' '.join(constraints) if constraints else ''
            print(f"  {name:<25} {data_type:<15} {constraint_str}")
        
        # Check for foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            print("🔗 Foreign Keys:")
            for fk in fks:
                print(f"  {fk[3]} → {fk[2]}.{fk[4]}")
        
        # Check for indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        if indexes:
            print("📑 Indexes:")
            for idx in indexes:
                print(f"  {idx[1]} ({'UNIQUE' if idx[2] else 'NON-UNIQUE'})")
        
        print()
        db_structure[table] = table_info
    
    print(f"💾 TOTAL DATABASE RECORDS: {total_records:,}")
    print()
    
    conn.close()
    return db_structure, total_records

def check_data_integrity():
    """Check for data integrity issues"""
    print("🔍 CHECKING DATA INTEGRITY...")
    print("=" * 60)
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Check for orphaned records (common foreign key issues)
    integrity_checks = [
        ("Contacts without Accounts", 
         "SELECT COUNT(*) FROM contacts WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)"),
        ("Interactions without valid Contact", 
         "SELECT COUNT(*) FROM interactions WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("RFQs without valid Contact", 
         "SELECT COUNT(*) FROM rfqs WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("Opportunities without valid Account", 
         "SELECT COUNT(*) FROM opportunities WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)"),
        ("Tasks without valid assigned_to", 
         "SELECT COUNT(*) FROM tasks WHERE assigned_to IS NOT NULL AND assigned_to NOT IN (SELECT id FROM contacts)")
    ]
    
    for check_name, query in integrity_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count > 0:
                issues.append(f"❌ {check_name}: {count} orphaned records")
                print(f"❌ {check_name}: {count} orphaned records")
            else:
                print(f"✅ {check_name}: No issues")
        except Exception as e:
            print(f"⚠️  {check_name}: Could not check - {str(e)}")
    
    # Check for duplicate data
    duplicate_checks = [
        ("Duplicate Accounts (by name)", 
         "SELECT name, COUNT(*) as cnt FROM accounts GROUP BY LOWER(name) HAVING cnt > 1"),
        ("Duplicate Contacts (by email)", 
         "SELECT email, COUNT(*) as cnt FROM contacts WHERE email IS NOT NULL GROUP BY LOWER(email) HAVING cnt > 1"),
        ("Duplicate Products (by part_number)", 
         "SELECT part_number, COUNT(*) as cnt FROM products WHERE part_number IS NOT NULL GROUP BY part_number HAVING cnt > 1")
    ]
    
    print("\n🔍 CHECKING FOR DUPLICATES...")
    print("-" * 40)
    
    for check_name, query in duplicate_checks:
        try:
            cursor.execute(query)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"❌ {check_name}:")
                for dup in duplicates[:5]:  # Show first 5
                    print(f"   '{dup[0]}': {dup[1]} duplicates")
                if len(duplicates) > 5:
                    print(f"   ... and {len(duplicates)-5} more")
                issues.append(f"{check_name}: {len(duplicates)} sets of duplicates")
            else:
                print(f"✅ {check_name}: No duplicates found")
        except Exception as e:
            print(f"⚠️  {check_name}: Could not check - {str(e)}")
    
    conn.close()
    return issues

def check_unused_data():
    """Check for unused or empty data"""
    print("\n🗑️  CHECKING FOR UNUSED DATA...")
    print("=" * 60)
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # Get tables with zero records
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    empty_tables = []
    low_usage_tables = []
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            empty_tables.append(table)
            print(f"🗑️  Empty table: {table}")
        elif count < 5:
            low_usage_tables.append((table, count))
            print(f"⚠️  Low usage table: {table} ({count} records)")
    
    if not empty_tables and not low_usage_tables:
        print("✅ All tables have reasonable data usage")
    
    conn.close()
    return empty_tables, low_usage_tables

def generate_documentation():
    """Generate comprehensive documentation"""
    print("\n📄 GENERATING DOCUMENTATION...")
    print("=" * 60)
    
    structure, total_records = analyze_database()
    issues = check_data_integrity()
    empty_tables, low_usage = check_unused_data()
    
    # Create comprehensive documentation
    doc = f"""
# CRM Database Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Database Overview
- **Database File**: `data/crm.db`
- **Total Tables**: {len(structure)}
- **Total Records**: {total_records:,}

## Table Summary
"""
    
    for table_name, table_info in structure.items():
        doc += f"\n### {table_name.upper()}\n"
        doc += f"- **Records**: {table_info['row_count']:,}\n"
        doc += f"- **Columns**: {len(table_info['columns'])}\n"
        doc += "\n**Schema**:\n"
        for col in table_info['columns']:
            constraints = ' | '.join(col['constraints']) if col['constraints'] else ''
            doc += f"- `{col['name']}` ({col['type']}) {constraints}\n"
    
    if issues:
        doc += "\n## Data Integrity Issues\n"
        for issue in issues:
            doc += f"- {issue}\n"
    else:
        doc += "\n## Data Integrity\n✅ No issues found\n"
    
    if empty_tables:
        doc += "\n## Empty Tables\n"
        for table in empty_tables:
            doc += f"- {table}\n"
    
    if low_usage:
        doc += "\n## Low Usage Tables\n"
        for table, count in low_usage:
            doc += f"- {table} ({count} records)\n"
    
    return doc

if __name__ == "__main__":
    try:
        documentation = generate_documentation()
        
        # Save documentation to file
        with open('DATABASE_STRUCTURE.md', 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print("\n✅ Analysis complete!")
        print("📄 Documentation saved to: DATABASE_STRUCTURE.md")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
