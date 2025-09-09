#!/usr/bin/env python3

from src.core.crm_data import crm_data

print('=== QPL TO QPLS TABLE MIGRATION ===')

try:
    # Check if qpl table exists
    qpl_exists = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name="qpl"')
    qpls_exists = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name="qpls"')
    
    print(f'QPL table exists: {bool(qpl_exists)}')
    print(f'QPLS table exists: {bool(qpls_exists)}')
    
    if qpl_exists and not qpls_exists:
        print('\nMigrating QPL table to QPLS...')
        
        # Get current data count
        count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpl')
        record_count = count_result[0] if count_result and len(count_result) > 0 else 0
        print(f'Current QPL table has {record_count} records')
        
        # Rename table from qpl to qpls
        crm_data.execute_query('ALTER TABLE qpl RENAME TO qpls')
        print('✅ Successfully renamed table from "qpl" to "qpls"')
        
        # Verify the migration
        new_count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
        new_record_count = new_count_result[0] if new_count_result and len(new_count_result) > 0 else 0
        print(f'✅ QPLS table now has {new_record_count} records')
        
        # Verify old table is gone
        qpl_check = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name="qpl"')
        qpls_check = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name="qpls"')
        
        print(f'QPL table exists after migration: {bool(qpl_check)}')
        print(f'QPLS table exists after migration: {bool(qpls_check)}')
        
    elif qpls_exists and not qpl_exists:
        print('✅ QPLS table already exists, no migration needed')
        count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
        record_count = count_result[0] if count_result and len(count_result) > 0 else 0
        print(f'QPLS table has {record_count} records')
        
    elif qpl_exists and qpls_exists:
        print('⚠️ Both QPL and QPLS tables exist - manual intervention needed')
        qpl_count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpl')
        qpls_count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
        qpl_count = qpl_count_result[0] if qpl_count_result and len(qpl_count_result) > 0 else 0
        qpls_count = qpls_count_result[0] if qpls_count_result and len(qpls_count_result) > 0 else 0
        print(f'QPL table has {qpl_count} records')
        print(f'QPLS table has {qpls_count} records')
        
    else:
        print('⚠️ Neither QPL nor QPLS table exists')

except Exception as e:
    print(f'❌ Migration failed: {e}')
    import traceback
    traceback.print_exc()

print('\n=== MIGRATION COMPLETE ===')
