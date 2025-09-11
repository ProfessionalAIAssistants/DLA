#!/usr/bin/env python3
"""
Create test QPL records for the new qpls table structure
"""

from src.core.crm_data import crm_data
from datetime import datetime

print('=== CREATING TEST QPL RECORDS FOR NEW QPLS TABLE ===')

# First, let's get some products and accounts to link to
try:
    products = crm_data.get_products()
    accounts = crm_data.get_accounts()
    
    print(f'Available products: {len(products)}')
    print(f'Available accounts: {len(accounts)}')
    
    # Use first few products and accounts if available
    product1_id = products[0]['id'] if products else None
    product2_id = products[1]['id'] if len(products) > 1 else None
    account1_id = accounts[0]['id'] if accounts else None
    account2_id = accounts[1]['id'] if len(accounts) > 1 else None
    
    print(f'Using product IDs: {product1_id}, {product2_id}')
    print(f'Using account IDs: {account1_id}, {account2_id}')
    
    # Create test QPL records with new structure
    test_qpls = [
        {
            'manufacturer_name': 'Boeing Company',
            'cage_code': '81205',
            'part_number': 'B737-001',
            'product_id': product1_id,
            'account_id': account1_id,
            'is_active': True
        },
        {
            'manufacturer_name': 'Lockheed Martin',
            'cage_code': '94271',
            'part_number': 'F35-PART-001',
            'product_id': product2_id,
            'account_id': account2_id,
            'is_active': True
        },
        {
            'manufacturer_name': 'General Dynamics',
            'cage_code': '16695',
            'part_number': 'GD-MIL-123',
            'product_id': product1_id,
            'account_id': account1_id,
            'is_active': True
        },
        {
            'manufacturer_name': 'Raytheon Technologies',
            'cage_code': '49956',
            'part_number': 'RTX-2024-001',
            'product_id': product2_id,
            'account_id': account2_id,
            'is_active': True
        }
    ]
    
    created_qpls = []
    
    for i, qpl_data in enumerate(test_qpls, 1):
        try:
            result = crm_data.create_qpl_entry(**qpl_data)
            if result:
                created_qpls.append(result)
                print(f'✅ Created QPL {i}: {qpl_data["manufacturer_name"]} - {qpl_data["part_number"]}')
            else:
                print(f'❌ Failed to create QPL {i}: {qpl_data["manufacturer_name"]}')
        except Exception as e:
            print(f'❌ Error creating QPL {i}: {e}')
    
    print(f'\\n📊 Successfully created {len(created_qpls)} QPL records')
    
    # Verify the records
    print('\\n=== VERIFICATION ===')
    all_qpls = crm_data.get_qpl_entries()
    print(f'Total QPLs in system: {len(all_qpls) if all_qpls else 0}')
    
    if all_qpls:
        for i, qpl in enumerate(all_qpls, 1):
            manufacturer = qpl[3] if len(qpl) > 3 else 'Unknown'  # manufacturer_name is column 3
            part_num = qpl[5] if len(qpl) > 5 else 'No part#'     # part_number is column 5
            print(f'  QPL {i}: {manufacturer} - {part_num}')
    
    print('\\n✅ QPL test data creation complete!')
    
except Exception as e:
    print(f'❌ Error in test data creation: {e}')
    import traceback
    traceback.print_exc()
