#!/usr/bin/env python3
"""
Consolidated Database Cleanup Tool
Combines functionality from cleanup_database.py and database_cleanup_final.py
Advanced database maintenance with backup, cleanup, and optimization features.
"""

import sqlite3
import os
import shutil
import argparse
from datetime import datetime

def create_backup(db_path, backup_suffix="_backup"):
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}{backup_suffix}_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def analyze_database_issues(cursor):
    """Analyze database for common issues"""
    issues = []
    
    print("🔍 ANALYZING DATABASE ISSUES...")
    print("-" * 40)
    
    # Check for orphaned records
    orphan_checks = [
        ("contacts", "account_id", "accounts", "id", "Contacts without valid accounts"),
        ("opportunities", "account_id", "accounts", "id", "Opportunities without valid accounts"),
        ("opportunities", "contact_id", "contacts", "id", "Opportunities without valid contacts"),
        ("projects", "account_id", "accounts", "id", "Projects without valid accounts"),
        ("tasks", "project_id", "projects", "id", "Tasks without valid projects"),
        ("interactions", "contact_id", "contacts", "id", "Interactions without valid contacts"),
    ]
    
    for child_table, child_col, parent_table, parent_col, description in orphan_checks:
        try:
            query = f"""
            SELECT COUNT(*) FROM {child_table} 
            WHERE {child_col} IS NOT NULL 
            AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            if count > 0:
                issues.append((description, count, "orphaned_records"))
                print(f"⚠️  {description}: {count} records")
            else:
                print(f"✅ {description}: Clean")
                
        except sqlite3.OperationalError as e:
            print(f"⚪ {description}: Unable to check ({e})")
    
    # Check for duplicate records
    duplicate_checks = [
        ("accounts", "name", "Accounts with duplicate names"),
        ("contacts", "email", "Contacts with duplicate emails"),
        ("products", "name", "Products with duplicate names"),
    ]
    
    for table, column, description in duplicate_checks:
        try:
            query = f"""
            SELECT COUNT(*) FROM (
                SELECT {column} FROM {table} 
                WHERE {column} IS NOT NULL 
                GROUP BY {column} 
                HAVING COUNT(*) > 1
            )
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            if count > 0:
                issues.append((description, count, "duplicates"))
                print(f"⚠️  {description}: {count} duplicated values")
            else:
                print(f"✅ {description}: No duplicates")
                
        except sqlite3.OperationalError as e:
            print(f"⚪ {description}: Unable to check ({e})")
    
    # Check for empty/null critical fields
    null_checks = [
        ("accounts", "name", "Accounts without names"),
        ("contacts", "name", "Contacts without names"),
        ("products", "name", "Products without names"),
    ]
    
    for table, column, description in null_checks:
        try:
            query = f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL OR {column} = ''"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            if count > 0:
                issues.append((description, count, "null_values"))
                print(f"⚠️  {description}: {count} records")
            else:
                print(f"✅ {description}: Clean")
                
        except sqlite3.OperationalError as e:
            print(f"⚪ {description}: Unable to check ({e})")
    
    return issues

def fix_orphaned_records(cursor, fix_mode="report"):
    """Fix orphaned records based on mode"""
    print(f"\\n🔧 FIXING ORPHANED RECORDS (Mode: {fix_mode})...")
    print("-" * 50)
    
    fixes_applied = 0
    
    # Define fixes for orphaned records
    orphan_fixes = [
        ("contacts", "account_id", "SET account_id = NULL", "Remove invalid account references from contacts"),
        ("opportunities", "account_id", "DELETE", "Remove opportunities without valid accounts"),
        ("opportunities", "contact_id", "SET contact_id = NULL", "Remove invalid contact references from opportunities"),
        ("projects", "account_id", "SET account_id = NULL", "Remove invalid account references from projects"),
        ("tasks", "project_id", "DELETE", "Remove tasks without valid projects"),
        ("interactions", "contact_id", "DELETE", "Remove interactions without valid contacts"),
    ]
    
    for child_table, child_col, action, description in orphan_fixes:
        try:
            # First check how many records would be affected
            if "account" in child_col:
                parent_table = "accounts"
                parent_col = "id"
            elif "contact" in child_col:
                parent_table = "contacts" 
                parent_col = "id"
            elif "project" in child_col:
                parent_table = "projects"
                parent_col = "id"
            else:
                continue
            
            check_query = f"""
            SELECT COUNT(*) FROM {child_table} 
            WHERE {child_col} IS NOT NULL 
            AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
            """
            cursor.execute(check_query)
            affected_count = cursor.fetchone()[0]
            
            if affected_count > 0:
                if fix_mode == "report":
                    print(f"📋 Would fix: {description} ({affected_count} records)")
                elif fix_mode == "fix":
                    if action.startswith("DELETE"):
                        fix_query = f"""
                        DELETE FROM {child_table} 
                        WHERE {child_col} IS NOT NULL 
                        AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
                        """
                    else:  # SET action
                        fix_query = f"""
                        UPDATE {child_table} 
                        {action}
                        WHERE {child_col} IS NOT NULL 
                        AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
                        """
                    
                    cursor.execute(fix_query)
                    fixes_applied += affected_count
                    print(f"✅ Fixed: {description} ({affected_count} records)")
            else:
                print(f"✅ No issues: {description}")
                
        except sqlite3.OperationalError as e:
            print(f"❌ Error fixing {child_table}.{child_col}: {e}")
    
    return fixes_applied

def optimize_database(cursor):
    """Optimize database performance"""
    print("\\n⚡ OPTIMIZING DATABASE...")
    print("-" * 30)
    
    optimizations = [
        ("VACUUM", "Rebuild database to reclaim space"),
        ("ANALYZE", "Update query planner statistics"),
        ("REINDEX", "Rebuild all indexes"),
    ]
    
    for command, description in optimizations:
        try:
            print(f"🔄 {description}...")
            cursor.execute(command)
            print(f"✅ {command} completed")
        except Exception as e:
            print(f"❌ {command} failed: {e}")

def cleanup_database(db_path, mode="analyze", create_backup_flag=True):
    """Main database cleanup function"""
    
    print("=" * 80)
    print("DATABASE CLEANUP TOOL")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Mode: {mode}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    # Create backup if requested
    backup_path = None
    if create_backup_flag and mode in ["fix", "optimize", "full"]:
        backup_path = create_backup(db_path)
        if not backup_path:
            print("❌ Cannot proceed without backup")
            return False
        print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Analyze issues
        issues = analyze_database_issues(cursor)
        
        if not issues:
            print("\\n🎉 No issues found! Database is clean.")
        else:
            print(f"\\n📋 Found {len(issues)} issue types")
        
        total_fixes = 0
        
        # Apply fixes based on mode
        if mode in ["fix", "full"]:
            if issues:
                print("\\n" + "=" * 60)
                print("APPLYING FIXES")
                print("=" * 60)
                
                # Fix orphaned records
                fixes = fix_orphaned_records(cursor, "fix")
                total_fixes += fixes
                
                # Commit fixes
                conn.commit()
                print(f"\\n✅ Applied {total_fixes} fixes")
            else:
                print("\\n✅ No fixes needed")
        
        elif mode == "report":
            if issues:
                print("\\n" + "=" * 60)
                print("RECOMMENDED FIXES")
                print("=" * 60)
                fix_orphaned_records(cursor, "report")
                print("\\n💡 Run with --mode fix to apply these fixes")
        
        # Optimize database
        if mode in ["optimize", "full"]:
            optimize_database(cursor)
        
        # Final summary
        print("\\n" + "=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        
        if backup_path:
            print(f"💾 Backup created: {backup_path}")
        
        print(f"🔍 Issues analyzed: {len(issues)} types found")
        
        if mode in ["fix", "full"]:
            print(f"🔧 Fixes applied: {total_fixes}")
        
        if mode in ["optimize", "full"]:
            print("⚡ Database optimized")
        
        # File size info
        file_size = os.path.getsize(db_path)
        print(f"📊 Database size: {file_size:,} bytes")
        
        conn.close()
        
        print("\\n✅ Database cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during database cleanup: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Comprehensive database cleanup and maintenance')
    parser.add_argument('--db', type=str, default='data/crm.db', help='Database file path (default: data/crm.db)')
    parser.add_argument('--mode', type=str, choices=['analyze', 'report', 'fix', 'optimize', 'full'], 
                       default='analyze', help='Cleanup mode (default: analyze)')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup (not recommended)')
    parser.add_argument('--backup-path', type=str, help='Custom backup file path')
    
    args = parser.parse_args()
    
    # Mode descriptions
    mode_descriptions = {
        'analyze': 'Analyze database for issues (read-only)',
        'report': 'Analyze issues and show recommended fixes',
        'fix': 'Apply fixes for data integrity issues',
        'optimize': 'Optimize database performance (VACUUM, ANALYZE, REINDEX)',
        'full': 'Complete cleanup: analyze, fix, and optimize'
    }
    
    print(f"🎯 Selected mode: {args.mode} - {mode_descriptions[args.mode]}")
    print()
    
    # Confirm destructive operations
    if args.mode in ['fix', 'optimize', 'full'] and not args.no_backup:
        if args.mode == 'full':
            print("⚠️  FULL mode will analyze, fix issues, and optimize the database")
        elif args.mode == 'fix':
            print("⚠️  FIX mode will modify database records to fix integrity issues")
        elif args.mode == 'optimize':
            print("⚠️  OPTIMIZE mode will rebuild the database structure")
        
        confirm = input("\\n🤔 Continue? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("❌ Operation cancelled by user")
            return
        print()
    
    success = cleanup_database(
        args.db, 
        args.mode, 
        not args.no_backup
    )
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()