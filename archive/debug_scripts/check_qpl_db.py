#!/usr/bin/env python3
"""Check QPL database data"""

from src.core.crm_data import crm_data
import sqlite3

# Check raw QPL data with column names
conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM qpls')
qpls = cursor.fetchall()

print('QPL Data:')
for qpl in qpls:
    print(f'  ID: {qpl["id"]}, Product: {qpl["product_id"]}, Account: {qpl["account_id"]}')
    print(f'  Manufacturer: {qpl["manufacturer_name"]}, Part: {qpl["part_number"]}')
    print()

conn.close()

# Now test the specific function
print('=== Function Test ===')
for product_id in [1, 2, 3]:
    qpl_data = crm_data.get_qpl_manufacturers_for_product(product_id)
    print(f'Product {product_id}: {len(qpl_data)} QPL entries')
    if qpl_data and len(qpl_data) > 0:
        print(f'  First entry type: {type(qpl_data[0])}')
        if isinstance(qpl_data[0], dict):
            print(f'  Keys: {list(qpl_data[0].keys())}')
        else:
            print(f'  Value: {qpl_data[0]}')
