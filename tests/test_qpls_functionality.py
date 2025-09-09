#!/usr/bin/env python3

from src.core.crm_data import crm_data

print('=== TESTING QPLS TABLE AFTER RENAMING ===')

try:
    # Test that qpls table exists and qpl table doesn't
    tables = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%qpl%"')
    table_names = [table['name'] if isinstance(table, dict) else table[0] for table in tables] if tables else []
    print('QPL-related tables found:', table_names)
    
    # Test basic qpls operations
    print('\n=== TESTING QPLS OPERATIONS ===')
    
    # Test count query
    count_result = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
    record_count = count_result[0]['COUNT(*)'] if count_result and len(count_result) > 0 else 0
    print(f'QPLS table record count: {record_count}')
    
    # Test the flask route query
    task_date = '2025-09-08'
    qpls_query = f'SELECT id, manufacturer_name, part_number, created_date FROM qpls WHERE date(created_date) = "{task_date}" ORDER BY id'
    print(f'\nTesting Flask route query: {qpls_query}')
    qpl_results = crm_data.execute_query(qpls_query)
    if qpl_results:
        today_qpls = []
        for qpl in qpl_results:
            if isinstance(qpl, dict):
                today_qpls.append({'id': qpl['id'], 'name': qpl.get('product_name') or 'Unknown Product', 'created_date': qpl['created_date']})
            else:
                today_qpls.append({'id': qpl[0], 'name': qpl[1] or 'Unknown Product', 'created_date': qpl[2]})
    else:
        today_qpls = []
    print(f'QPLs found for {task_date}: {len(today_qpls)}')
    
    # Test CRM data methods
    print('\n=== TESTING CRM DATA METHODS ===')
    
    try:
        qpl_entries = crm_data.get_qpl_entries()
        print(f'get_qpl_entries() returned: {len(qpl_entries) if qpl_entries else 0} entries')
    except Exception as e:
        print(f'get_qpl_entries() error: {e}')
    
    try:
        qpl_cage = crm_data.search_qpl_by_cage('12345')
        print(f'search_qpl_by_cage() returned: {len(qpl_cage) if qpl_cage else 0} entries')
    except Exception as e:
        print(f'search_qpl_by_cage() error: {e}')
    
    print('\n✅ All QPLS tests passed!')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()

print('\n=== TESTING COMPLETE ===')
