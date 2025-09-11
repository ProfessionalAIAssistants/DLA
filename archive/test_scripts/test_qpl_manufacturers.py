#!/usr/bin/env python3
"""Test QPL manufacturers for product details"""

from src.core.crm_data import crm_data

print('=== QPL MANUFACTURERS TEST ===')

# Test for each product
for product_id in [1, 2, 3]:
    print(f'Product {product_id}:')
    product = crm_data.get_product_by_id(product_id)
    if product:
        print(f'  Product Name: {product.get("name")}')
        print(f'  Product NSN: {product.get("nsn")}')
        
        qpl_manufacturers = crm_data.get_qpl_manufacturers_for_product(product_id)
        print(f'  QPL Manufacturers Count: {len(qpl_manufacturers) if qpl_manufacturers else 0}')
        
        if qpl_manufacturers:
            for i, qpl in enumerate(qpl_manufacturers):
                if isinstance(qpl, dict):
                    print(f'    QPL {i+1}: {qpl.get("manufacturer_name")} - {qpl.get("part_number")} (ID: {qpl.get("id")})')
                    print(f'      Account ID: {qpl.get("account_id")}')
                else:
                    print(f'    QPL {i+1}: {qpl}')
        else:
            print('    No QPL manufacturers found')
    else:
        print(f'  Product not found')
    print()

# Also check raw QPL data
print('=== RAW QPL DATA ===')
raw_qpls = crm_data.execute_query('SELECT * FROM qpls')
print(f'Total QPLs in database: {len(raw_qpls) if raw_qpls else 0}')
for qpl in raw_qpls:
    print(f'  QPL ID {qpl[0]}: Product {qpl[1]}, Account {qpl[2]}, Mfr: {qpl[3]}')
