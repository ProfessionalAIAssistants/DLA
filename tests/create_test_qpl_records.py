#!/usr/bin/env python3

from src.core.crm_data import crm_data
from datetime import datetime

print('=== ADDING TEST QPL RECORDS ===')

# Add a couple of test QPL records for the task date
test_date = '2025-09-08'

try:
    # Add first QPL record
    qpl1_data = {
        'nsn': '1234567890123',
        'name': 'Test QPL Product 1',
        'manufacturer': 'Test Manufacturer A',
        'part_number': 'TM-001',
        'cage_code': '12345',
        'description': 'Test QPL product for validation',
        'status': 'Active'
    }
    
    result1 = crm_data.create_qpl_entry(**qpl1_data)
    print(f'Added QPL 1: Result = {result1}')
    
    # Add second QPL record  
    qpl2_data = {
        'nsn': '9876543210987', 
        'name': 'Test QPL Product 2',
        'manufacturer': 'Test Manufacturer B',
        'part_number': 'TM-002',
        'cage_code': '67890',
        'description': 'Second test QPL product',
        'status': 'Active'
    }
    
    result2 = crm_data.create_qpl_entry(**qpl2_data)
    print(f'Added QPL 2: Result = {result2}')
    
    # Update creation dates to match test date
    # Get the IDs of the records we just created
    all_qpls = crm_data.execute_query('SELECT id FROM qpls ORDER BY id DESC LIMIT 2')
    
    if len(all_qpls) >= 2:
        qpl1_id = all_qpls[1]['id'] if isinstance(all_qpls[1], dict) else all_qpls[1][0]
        qpl2_id = all_qpls[0]['id'] if isinstance(all_qpls[0], dict) else all_qpls[0][0]
        
        update_query1 = f"UPDATE qpls SET created_date = '{test_date} 10:00:00' WHERE id = {qpl1_id}"
        update_query2 = f"UPDATE qpls SET created_date = '{test_date} 11:00:00' WHERE id = {qpl2_id}"
        
        crm_data.execute_query(update_query1)
        crm_data.execute_query(update_query2)
        print(f'Updated QPL {qpl1_id} and {qpl2_id} creation dates to {test_date}')
    
    # Verify the records were added and updated
    verification_query = f'SELECT id, manufacturer_name, part_number, created_date FROM qpls WHERE date(created_date) = "{test_date}" ORDER BY id'
    qpl_results = crm_data.execute_query(verification_query)
    print(f'QPLs for {test_date}: {len(qpl_results)}')
    
    for qpl in qpl_results:
        if isinstance(qpl, dict):
            print(f'  - ID {qpl["id"]}: {qpl["name"]} (created: {qpl["created_date"]})')
        else:
            print(f'  - ID {qpl[0]}: {qpl[1]} (created: {qpl[2]})')
    
    print('\n✅ Successfully added and verified test QPL records!')
    
except Exception as e:
    print(f'❌ Error adding QPL records: {e}')
    import traceback
    traceback.print_exc()

print('\n=== TEST QPL ADDITION COMPLETE ===')
