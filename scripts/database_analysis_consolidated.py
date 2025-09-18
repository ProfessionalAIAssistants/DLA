#!/usr/bin/env python3
"""
Consolidated Database Analysis Tool for CRM System
Combines functionality from database_analysis.py and db_analysis.py
Analyzes database structure, checks for duplicates, and generates human-readable documentation
"""

import sqlite3
import json
import argparse
import os
from datetime import datetime
from pathlib import Path

def analyze_database_comprehensive(db_path='data/crm.db', detailed=True):
    """Comprehensive database analysis with optional detailed output"""
    if detailed:
        print("🔍 Starting Comprehensive Database Analysis...")
        print("=" * 60)
    else:
        print("=== DATABASE ANALYSIS ===")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return None, 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    if detailed:
        print(f"📊 DATABASE OVERVIEW")
        print(f"Database File: {db_path}")
        print(f"Total Tables: {len(tables)}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    else:
        print(f"Database: {db_path}")
        print(f"Total Tables: {len(tables)}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    total_records = 0
    db_structure = {}
    
    for table in tables:
        if detailed:
            print(f"🔹 TABLE: {table}")
            print("-" * 50)
        else:
            print(f"TABLE: {table}")
            print("-" * 50)
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        total_records += row_count
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        foreign_keys = cursor.fetchall()
        
        # Build column information
        column_info = []
        for col in columns:
            col_id, name, col_type, not_null, default_value, pk = col
            constraints = []
            if pk:
                constraints.append('PRIMARY KEY')
            if not_null:
                constraints.append('NOT NULL')
            if default_value is not None:
                constraints.append(f'DEFAULT {default_value}')
            
            column_info.append({
                'name': name,
                'type': col_type,
                'constraints': constraints
            })
        
        # Add foreign key constraints
        for fk in foreign_keys:
            col_name = fk[3]
            ref_table = fk[2]
            ref_col = fk[4]
            for col in column_info:
                if col['name'] == col_name:
                    col['constraints'].append(f'REFERENCES {ref_table}({ref_col})')
        
        # Display table information
        print(f"Records: {row_count:,}")
        print(f"Columns: {len(columns)}")
        print()
        
        if detailed:
            print("Schema:")
            for col in column_info:
                constraints_str = f" [{', '.join(col['constraints'])}]" if col['constraints'] else ""
                print(f"  • {col['name']} ({col['type']}){constraints_str}")
            print()
        
        # Store structure info
        table_info = {
            'row_count': row_count,
            'columns': column_info,
            'foreign_keys': foreign_keys
        }
        
        db_structure[table] = table_info
    
    if detailed:
        print("=" * 60)
        print(f"📈 TOTAL RECORDS ACROSS ALL TABLES: {total_records:,}")
        print("=" * 60)
    
    conn.close()
    return db_structure, total_records

def check_data_integrity(db_path='data/crm.db'):
    """Check for data integrity issues"""
    print("🔍 CHECKING DATA INTEGRITY...")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    issues = []
    
    # Check for duplicate entries in key tables
    duplicate_checks = {
        'accounts': ('name', 'Duplicate account names'),
        'contacts': ('email', 'Duplicate contact emails'),
        'products': ('nsn', 'Duplicate product NSNs'),
        'opportunities': ('name', 'Duplicate opportunity names')
    }
    
    for table, (column, check_name) in duplicate_checks.items():
        try:
            cursor.execute(f"SELECT {column}, COUNT(*) as cnt FROM {table} WHERE {column} IS NOT NULL GROUP BY {column} HAVING cnt > 1")
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

def check_unused_data(db_path='data/crm.db'):
    """Check for unused or empty data"""
    print("🗑️  CHECKING FOR UNUSED DATA...")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return [], []
    
    conn = sqlite3.connect(db_path)
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

def quick_db_check(db_path='data/crm.db'):
    """Quick database check similar to original check_db.py"""
    print("🔍 QUICK DATABASE CHECK")
    print("=" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in {db_path}:", tables)
        
        # Check counts for key tables
        key_tables = ['tasks', 'opportunities', 'projects', 'interactions', 'rfqs', 'accounts', 'contacts', 'products']
        for table in key_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} records")
            except:
                print(f"{table}: table doesn't exist")
        
        conn.close()
    except Exception as e:
        print(f"Error with {db_path}: {e}")

def generate_documentation(db_path='data/crm.db'):
    """Generate comprehensive documentation"""
    print("📄 GENERATING DOCUMENTATION...")
    print("=" * 60)
    
    structure, total_records = analyze_database_comprehensive(db_path, detailed=False)
    if structure is None:
        return None
        
    issues = check_data_integrity(db_path)
    empty_tables, low_usage = check_unused_data(db_path)
    
    # Create comprehensive documentation
    doc = f"""
# CRM Database Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Database Overview
- **Database File**: `{db_path}`
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

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Comprehensive Database Analysis Tool')
    parser.add_argument('--db', type=str, default='data/crm.db', help='Database file path (default: data/crm.db)')
    parser.add_argument('--quick', action='store_true', help='Quick check mode (like original check_db.py)')
    parser.add_argument('--structure', action='store_true', help='Show database structure (like original check_db_structure.py)')
    parser.add_argument('--detailed', action='store_true', help='Detailed analysis output')
    parser.add_argument('--integrity', action='store_true', help='Check data integrity only')
    parser.add_argument('--doc', action='store_true', help='Generate documentation')
    parser.add_argument('--output', type=str, help='Output file for documentation')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_db_check(args.db)
    elif args.structure:
        # Structure check similar to check_db_structure.py
        if os.path.exists(args.db):
            conn = sqlite3.connect(args.db)
            cursor = conn.cursor()
            
            print(f"Looking for database at: {args.db}")
            print(f"Database exists: {os.path.exists(args.db)}")
            
            # Get opportunities table structure as example
            try:
                cursor.execute('PRAGMA table_info(opportunities)')
                print('\\nOpportunities table columns:')
                for row in cursor.fetchall():
                    print(f'  {row[1]} - {row[2]}')
                
                # Get a sample opportunity
                cursor.execute('SELECT * FROM opportunities LIMIT 1')
                columns = [description[0] for description in cursor.description]
                sample = cursor.fetchone()
                
                print('\\nSample opportunity data:')
                if sample:
                    for i, col in enumerate(columns):
                        print(f'  {col}: {sample[i]}')
                else:
                    print('  No opportunities found in database')
            except Exception as e:
                print(f'Error analyzing opportunities table: {e}')
            
            conn.close()
        else:
            print(f"Database not found: {args.db}")
    elif args.integrity:
        check_data_integrity(args.db)
    elif args.doc:
        documentation = generate_documentation(args.db)
        if documentation:
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(documentation)
                print(f"✓ Documentation saved to: {args.output}")
            else:
                print(documentation)
    else:
        # Default: comprehensive analysis
        documentation = generate_documentation(args.db)
        if documentation and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(documentation)
            print(f"✓ Documentation saved to: {args.output}")
        elif documentation:
            print("\\n" + "="*60)
            print("DOCUMENTATION PREVIEW")
            print("="*60)
            print(documentation[:1000] + "..." if len(documentation) > 1000 else documentation)

if __name__ == "__main__":
    main()