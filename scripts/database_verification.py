#!/usr/bin/env python3
"""
Database Verification Script
Checks all database files and verifies the active database configuration
"""

import sqlite3
import os
from pathlib import Path

def check_database_files():
    """Check what database files exist in the workspace"""
    print('=== DATABASE FILES IN WORKSPACE ===')
    base_dir = Path('.')
    db_files = list(base_dir.rglob('*.db'))
    
    if not db_files:
        print('No database files found!')
        return []
    
    for db_file in db_files:
        size_kb = os.path.getsize(db_file) / 1024
        print(f'Found: {db_file} ({size_kb:.1f} KB)')
    
    return db_files

def verify_active_database():
    """Verify the active database from configuration"""
    print('\n=== VERIFYING ACTIVE DATABASE ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        print(f'Configured database: {db_path}')
        print(f'Database exists: {db_path.exists()}')
        
        if not db_path.exists():
            print('❌ Configured database does not exist!')
            return False
            
        # Check database structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [row[0] for row in cursor.fetchall()]
        print(f'✅ Active database has {len(tables)} tables')
        
        # Check for data in main tables
        main_tables = ['accounts', 'contacts', 'opportunities', 'rfqs', 'tasks', 'interactions', 'projects']
        total_records = 0
        
        print('\nData Summary:')
        for table in main_tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                total_records += count
                status = '✅' if count > 0 else '⚪'
                print(f'  {status} {table}: {count} records')
            except sqlite3.OperationalError:
                print(f'  ❌ {table}: table not found')
        
        print(f'\nTotal records across main tables: {total_records}')
        
        # Check for backup tables
        backup_tables = [t for t in tables if 'backup' in t.lower()]
        if backup_tables:
            print(f'\nBackup tables found: {len(backup_tables)}')
            for table in backup_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'  📦 {table}: {count} records')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error verifying database: {e}')
        return False

def check_data_integrity():
    """Check for data integrity issues"""
    print('\n=== DATA INTEGRITY CHECK ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        issues = []
        
        # Check for orphaned foreign keys
        tables_with_fk = [
            ('contacts', 'account_id', 'accounts', 'id'),
            ('opportunities', 'account_id', 'accounts', 'id'),
            ('opportunities', 'contact_id', 'contacts', 'id'),
            ('tasks', 'account_id', 'accounts', 'id'),
            ('tasks', 'contact_id', 'contacts', 'id'),
            ('interactions', 'account_id', 'accounts', 'id'),
            ('interactions', 'contact_id', 'contacts', 'id'),
        ]
        
        for table, fk_col, ref_table, ref_col in tables_with_fk:
            try:
                query = f'''
                SELECT COUNT(*) FROM {table} 
                WHERE {fk_col} IS NOT NULL 
                AND {fk_col} NOT IN (SELECT {ref_col} FROM {ref_table})
                '''
                cursor.execute(query)
                orphaned = cursor.fetchone()[0]
                if orphaned > 0:
                    issues.append(f'{table}.{fk_col}: {orphaned} orphaned references')
                    print(f'  ⚠️  {table}.{fk_col}: {orphaned} orphaned references')
            except sqlite3.OperationalError as e:
                print(f'  ❌ Error checking {table}.{fk_col}: {e}')
        
        if not issues:
            print('  ✅ No data integrity issues found')
        
        conn.close()
        return issues
        
    except Exception as e:
        print(f'❌ Error checking data integrity: {e}')
        return [f'Integrity check failed: {e}']

if __name__ == "__main__":
    try:
        # Check all database files
        db_files = check_database_files()
        
        # Verify the active database
        active_ok = verify_active_database()
        
        # Check data integrity
        integrity_issues = check_data_integrity()
        
        print('\n=== SUMMARY ===')
        print(f'Database files found: {len(db_files)}')
        print(f'Active database OK: {"✅" if active_ok else "❌"}')
        print(f'Data integrity issues: {len(integrity_issues)}')
        
        if integrity_issues:
            print('\nIssues to fix:')
            for issue in integrity_issues:
                print(f'  - {issue}')
        
        if active_ok and not integrity_issues:
            print('\n🎉 Database is clean and ready to use!')
        
    except Exception as e:
        print(f'❌ Script error: {e}')
        import traceback
        traceback.print_exc()
