#!/usr/bin/env python3

from src.core.crm_data import crm_data

print('=== DATABASE QPL/QPLS TABLE CHECK ===')

# Check what QPL-related tables exist
try:
    tables = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%qpl%"')
    print('QPL-related tables found:', [table[0] for table in tables])
except Exception as e:
    print(f'Error checking tables: {e}')

# Check if old qpl table exists (should not exist)
try:
    qpl_schema = crm_data.execute_query('PRAGMA table_info(qpl)')
    if qpl_schema:
        print('\nWARNING: Old QPL table still exists!')
        print('Old QPL table schema:')
        for col in qpl_schema:
            print(f'  {col}')
        
        # Check data count
        count = crm_data.execute_query('SELECT COUNT(*) FROM qpl')
        print(f'Old QPL table record count: {count[0][0] if count else 0}')
    else:
        print('\nGood: Old QPL table does not exist')
    
except Exception as e:
    print(f'\nGood: Old QPL table does not exist - {e}')

# Check if qpls table exists
try:
    qpls_schema = crm_data.execute_query('PRAGMA table_info(qpls)')
    print('\nQPLS table schema:')
    for col in qpls_schema:
        print(f'  {col}')
        
    # Check data count
    count = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
    print(f'\nQPLS table record count: {count[0][0] if count else 0}')
    
except Exception as e:
    print(f'QPLS table error: {e}')
