#!/usr/bin/env python3

import sys
sys.path.append('.')
from crm_app import app
from src.core.crm_data import crm_data
import json

print('=== TESTING UPDATED QPL LOGIC ===')

with app.app_context():
    task_id = 1
    task = crm_data.get_task_by_id(task_id)
    
    if task.get('description') and '<!-- PROCESSING_DATA:' in task['description']:
        start_marker = '<!-- PROCESSING_DATA:'
        end_marker = ' -->'
        start_index = task['description'].find(start_marker) + len(start_marker)
        end_index = task['description'].find(end_marker, start_index)
        
        if end_index > start_index:
            data_str = task['description'][start_index:end_index]
            processing_data = json.loads(data_str)
            
            task_date = task.get('created_date', '')[:10]
            print(f'Task date: {task_date}')
            
            # Test QPL query with corrected table name and column
            try:
                qpls_query = f'SELECT id, manufacturer_name, created_date FROM qpls WHERE date(created_date) = "{task_date}" ORDER BY id'
                print(f'QPL query: {qpls_query}')
                qpl_results = crm_data.execute_query(qpls_query)
                print(f'QPL query results: {qpl_results}')
                today_qpls = [{'id': qpl[0], 'name': qpl[1] or 'Unknown Product', 'created_date': qpl[2]} for qpl in qpl_results]
                print(f'QPLs found for today: {len(today_qpls)}')
                for qpl in today_qpls:
                    print(f'  - QPL: {qpl}')
                
            except Exception as qpl_error:
                print(f'QPL error: {qpl_error}')
                today_qpls = []
    
    print('\n=== ALSO TESTING ALL TABLES FOR COMPARISON ===')
    
    # Test all record types for comparison
    task_date = '2024-12-26'  # Use known date
    print(f'Testing all records for date: {task_date}')
    
    tables = [
        ('opportunities', 'id, name, created_date'),
        ('contacts', 'id, first_name, last_name, created_date'), 
        ('accounts', 'id, name, created_date'),
        ('products', 'id, name, created_date'),
        ('qpl', 'id, product_name, created_date')
    ]
    
    for table_name, columns in tables:
        try:
            query = f'SELECT {columns} FROM {table_name} WHERE date(created_date) = "{task_date}" ORDER BY id'
            print(f'\n{table_name.upper()} query: {query}')
            results = crm_data.execute_query(query)
            print(f'{table_name.upper()} results: {len(results)} records found')
            for i, record in enumerate(results[:3]):  # Show first 3
                print(f'  {i+1}: {record}')
        except Exception as e:
            print(f'{table_name.upper()} error: {e}')
