#!/usr/bin/env python3
"""
Remove backup tables from the database
"""

import sqlite3
from src.core.config_manager import config_manager

def remove_backup_tables():
    print('🗑️  REMOVING BACKUP TABLES')
    print('=' * 50)

    db_path = config_manager.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    backup_tables = [
        'rfqs_backup_20250821',
        'opportunities_backup_20250821', 
        'rfqs_backup_simple'
    ]

    # Get initial database size
    cursor.execute('PRAGMA page_count')
    page_count = cursor.fetchone()[0]
    cursor.execute('PRAGMA page_size')
    page_size = cursor.fetchone()[0]
    initial_size = (page_count * page_size) / 1024

    print('📊 Before removal:')
    for table in backup_tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'  {table}: {count} records')

    print(f'Database size: {initial_size:.1f} KB')

    # Remove backup tables
    print('\n🗑️  Removing backup tables...')
    for table in backup_tables:
        print(f'  Dropping {table}...')
        cursor.execute(f'DROP TABLE IF EXISTS {table}')
        print(f'  ✅ {table} removed')

    # Clean up sqlite_sequence table
    cleanup_names = "', '".join(backup_tables)
    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN ('{cleanup_names}')")

    # Commit changes
    conn.commit()

    # Get final database size
    cursor.execute('PRAGMA page_count')
    page_count = cursor.fetchone()[0]
    cursor.execute('PRAGMA page_size')
    page_size = cursor.fetchone()[0]
    final_size = (page_count * page_size) / 1024

    print(f'\n📊 After removal:')
    print(f'Database size: {final_size:.1f} KB')
    print(f'Space saved: {initial_size - final_size:.1f} KB')

    # Vacuum to reclaim space
    print('\n🧹 Vacuuming database to reclaim space...')
    cursor.execute('VACUUM')

    # Get final size after vacuum
    cursor.execute('PRAGMA page_count')
    page_count = cursor.fetchone()[0]
    cursor.execute('PRAGMA page_size')
    page_size = cursor.fetchone()[0]
    vacuum_size = (page_count * page_size) / 1024

    print(f'Final database size: {vacuum_size:.1f} KB')
    print(f'Total space reclaimed: {initial_size - vacuum_size:.1f} KB')

    # Verify remaining tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
    remaining_tables = [row[0] for row in cursor.fetchall()]
    print(f'\n✅ Database now has {len(remaining_tables)} tables')

    # Check that no backup tables remain
    backup_remaining = [t for t in remaining_tables if 'backup' in t.lower()]
    if backup_remaining:
        print(f'⚠️  Warning: {len(backup_remaining)} backup tables still exist: {backup_remaining}')
    else:
        print('✅ All backup tables successfully removed')

    conn.close()

    print('\n🎉 BACKUP CLEANUP COMPLETE!')
    return True

if __name__ == "__main__":
    try:
        remove_backup_tables()
    except Exception as e:
        print(f'❌ Error removing backup tables: {e}')
        import traceback
        traceback.print_exc()
