#!/usr/bin/env python3
"""
Consolidated Database Checker
Combines functionality from check_db.py and check_db_structure.py
Comprehensive database inspection tool for CRM system validation.
"""

import sqlite3
import os
import argparse
from datetime import datetime

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def get_table_schema(cursor, table_name):
    """Get the schema information for a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def get_table_count(cursor, table_name):
    """Get the record count for a table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except sqlite3.OperationalError:
        return 0

def check_foreign_keys(cursor, table_name):
    """Get foreign key information for a table"""
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return cursor.fetchall()

def check_indexes(cursor, table_name):
    """Get index information for a table"""
    cursor.execute(f"PRAGMA index_list({table_name})")
    return cursor.fetchall()

def analyze_database_structure(db_path, detailed=False, table_filter=None):
    """Analyze and display database structure"""
    
    print("=" * 80)
    print("DATABASE STRUCTURE ANALYSIS")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        if table_filter:
            tables = [t for t in all_tables if table_filter.lower() in t.lower()]
            if not tables:
                print(f"❌ No tables found matching filter: {table_filter}")
                return False
        else:
            tables = all_tables
        
        print(f"📊 Found {len(tables)} table(s)")
        if table_filter:
            print(f"🔍 Filtered by: {table_filter}")
        print()
        
        # Core CRM tables for validation
        expected_tables = [
            'accounts', 'contacts', 'products', 'opportunities', 
            'projects', 'tasks', 'interactions', 'rfqs', 'quotes'
        ]
        
        # Check for expected tables
        print("✅ EXPECTED TABLES STATUS:")
        print("-" * 40)
        for table in expected_tables:
            if table in all_tables:
                count = get_table_count(cursor, table)
                print(f"✅ {table}: {count:,} records")
            else:
                print(f"❌ {table}: MISSING")
        print()
        
        # Analyze each table
        for table in tables:
            print("=" * 60)
            print(f"📋 TABLE: {table.upper()}")
            print("=" * 60)
            
            # Record count
            count = get_table_count(cursor, table)
            print(f"📊 Records: {count:,}")
            
            # Schema information
            schema = get_table_schema(cursor, table)
            print("\\n🏗️  SCHEMA:")
            print("-" * 30)
            print(f"{'Column':<20} {'Type':<15} {'Null':<8} {'Default':<15} {'PK':<5}")
            print("-" * 63)
            
            for col in schema:
                cid, name, col_type, not_null, default_value, pk = col
                null_str = "NOT NULL" if not_null else "NULL"
                default_str = str(default_value) if default_value is not None else ""
                pk_str = "YES" if pk else ""
                print(f"{name:<20} {col_type:<15} {null_str:<8} {default_str:<15} {pk_str:<5}")
            
            if detailed:
                # Foreign keys
                foreign_keys = check_foreign_keys(cursor, table)
                if foreign_keys:
                    print("\\n🔗 FOREIGN KEYS:")
                    print("-" * 30)
                    for fk in foreign_keys:
                        id_fk, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                        print(f"• {from_col} → {table_ref}.{to_col}")
                
                # Indexes
                indexes = check_indexes(cursor, table)
                if indexes:
                    print("\\n📇 INDEXES:")
                    print("-" * 30)
                    for idx in indexes:
                        seq, name, unique, origin, partial = idx
                        unique_str = "UNIQUE" if unique else "INDEX"
                        print(f"• {name} ({unique_str})")
                
                # Sample data
                if count > 0:
                    print("\\n📝 SAMPLE DATA (First 3 rows):")
                    print("-" * 30)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    sample_rows = cursor.fetchall()
                    
                    # Get column names
                    col_names = [desc[1] for desc in schema]
                    
                    # Display headers
                    header = " | ".join([name[:15] for name in col_names])
                    print(header)
                    print("-" * len(header))
                    
                    # Display sample rows
                    for row in sample_rows:
                        row_str = " | ".join([str(val)[:15] if val is not None else "NULL" for val in row])
                        print(row_str)
            
            print()
        
        # Database statistics
        print("=" * 80)
        print("📈 DATABASE STATISTICS")
        print("=" * 80)
        
        total_records = sum(get_table_count(cursor, table) for table in all_tables)
        print(f"📊 Total Tables: {len(all_tables)}")
        print(f"📊 Total Records: {total_records:,}")
        print(f"📊 Database Size: {os.path.getsize(db_path):,} bytes")
        
        # Check database integrity
        print("\\n🔍 INTEGRITY CHECK:")
        print("-" * 30)
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        if integrity_result == "ok":
            print("✅ Database integrity: OK")
        else:
            print(f"❌ Database integrity: {integrity_result}")
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        if not fk_violations:
            print("✅ Foreign key constraints: OK")
        else:
            print(f"❌ Foreign key violations: {len(fk_violations)}")
            if detailed:
                for violation in fk_violations:
                    print(f"   • {violation}")
        
        conn.close()
        
        print("\\n" + "=" * 80)
        print("✅ DATABASE ANALYSIS COMPLETED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database analysis: {e}")
        return False

def quick_health_check(db_path):
    """Quick health check for essential CRM functionality"""
    
    print("⚡ QUICK HEALTH CHECK")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Essential tables and their expected relationships
        health_checks = {
            'accounts': "Core business accounts",
            'contacts': "Contact information",
            'products': "Product catalog",
            'opportunities': "Sales opportunities",
            'projects': "Active projects",
            'tasks': "Task management",
            'interactions': "Customer interactions",
        }
        
        all_good = True
        
        for table, description in health_checks.items():
            if check_table_exists(cursor, table):
                count = get_table_count(cursor, table)
                print(f"✅ {table}: {count:,} records - {description}")
            else:
                print(f"❌ {table}: MISSING - {description}")
                all_good = False
        
        if all_good:
            print("\\n🎉 All essential tables present!")
        else:
            print("\\n⚠️  Some essential tables are missing!")
        
        conn.close()
        return all_good
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Comprehensive database structure analysis')
    parser.add_argument('--db', type=str, default='data/crm.db', help='Database file path (default: data/crm.db)')
    parser.add_argument('--detailed', action='store_true', help='Show detailed analysis including foreign keys, indexes, and sample data')
    parser.add_argument('--table', type=str, help='Filter analysis to specific table (partial name matching)')
    parser.add_argument('--quick', action='store_true', help='Quick health check only')
    parser.add_argument('--both', type=str, help='Compare two database files')
    
    args = parser.parse_args()
    
    if args.both:
        # Compare two databases
        print("🔄 DATABASE COMPARISON")
        print("=" * 60)
        
        db1_path = args.db
        db2_path = args.both
        
        print(f"Database 1: {db1_path}")
        print(f"Database 2: {db2_path}")
        print()
        
        if not os.path.exists(db1_path):
            print(f"❌ Database 1 not found: {db1_path}")
            return
        
        if not os.path.exists(db2_path):
            print(f"❌ Database 2 not found: {db2_path}")
            return
        
        try:
            # Compare table counts
            conn1 = sqlite3.connect(db1_path)
            conn2 = sqlite3.connect(db2_path)
            cursor1 = conn1.cursor()
            cursor2 = conn2.cursor()
            
            # Get all tables from both databases
            cursor1.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables1 = set(row[0] for row in cursor1.fetchall())
            
            cursor2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables2 = set(row[0] for row in cursor2.fetchall())
            
            all_tables = tables1.union(tables2)
            
            print("📊 TABLE COMPARISON:")
            print("-" * 50)
            print(f"{'Table':<20} {'DB1 Count':<12} {'DB2 Count':<12} {'Difference'}")
            print("-" * 50)
            
            for table in sorted(all_tables):
                count1 = get_table_count(cursor1, table) if table in tables1 else 0
                count2 = get_table_count(cursor2, table) if table in tables2 else 0
                diff = count2 - count1
                
                status = ""
                if table not in tables1:
                    status = " (New in DB2)"
                elif table not in tables2:
                    status = " (Removed in DB2)"
                elif diff > 0:
                    status = f" (+{diff})"
                elif diff < 0:
                    status = f" ({diff})"
                
                print(f"{table:<20} {count1:<12,} {count2:<12,} {status}")
            
            conn1.close()
            conn2.close()
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
        
    elif args.quick:
        quick_health_check(args.db)
    else:
        analyze_database_structure(args.db, args.detailed, args.table)

if __name__ == "__main__":
    main()