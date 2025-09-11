#!/usr/bin/env python3
"""Test QPL links"""

from src.core.crm_data import crm_data

# Check QPL 1
qpl = crm_data.get_qpl_entry_by_id(1)
if qpl:
    print(f"QPL 1:")
    print(f"  Product ID: {qpl.get('product_id')}")
    print(f"  Account ID: {qpl.get('account_id')}")
    print(f"  Manufacturer: {qpl.get('manufacturer_name')}")
else:
    print("No QPL 1 found")

# Check QPL 2 
qpl2 = crm_data.get_qpl_entry_by_id(2)
if qpl2:
    print(f"QPL 2:")
    print(f"  Product ID: {qpl2.get('product_id')}")
    print(f"  Account ID: {qpl2.get('account_id')}")
    print(f"  Manufacturer: {qpl2.get('manufacturer_name')}")
else:
    print("No QPL 2 found")
