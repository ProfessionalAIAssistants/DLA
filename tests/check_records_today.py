#!/usr/bin/env python3

from src.core.crm_data import crm_data

date = '2025-09-08'
print(f'Records created on {date}:')

tables = [
    ('opportunities', 'id, name'),
    ('contacts', 'id, first_name, last_name'), 
    ('accounts', 'id, name'),
    ('products', 'id, name'),
    ('qpl', 'id, product_name')
]

for table_name, columns in tables:
    try:
        query = f'SELECT {columns} FROM {table_name} WHERE date(created_date) = "{date}"'
        results = crm_data.execute_query(query)
        print(f'  {table_name.upper()}: {len(results)} records')
        if results:
            for i, record in enumerate(results[:3]):
                print(f'    {i+1}: {record}')
    except Exception as e:
        print(f'  {table_name.upper()}: Error - {e}')

print(f'\nTotal QPLs in table:')
try:
    all_qpls = crm_data.execute_query('SELECT COUNT(*) FROM qpls')
    print(f'  QPLs table has {all_qpls[0][0]} total records')
except Exception as e:
    print(f'  QPL error: {e}')
