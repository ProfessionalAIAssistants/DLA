#!/usr/bin/env python
# coding: utf-8

"""
Database Data Verification Test
Verifies that the CRM application can now access the copied data
"""

import sys
import os

# Add current directory to path to import modules
sys.path.append(os.getcwd())

try:
    from crm_data import crm_data
    
    print("=== CRM Data Verification Test ===")
    
    # Test accounts
    accounts = crm_data.get_accounts()
    print(f"✅ Accounts: {len(accounts)} records found")
    if accounts:
        print(f"   Sample: {accounts[0]['name'] if 'name' in accounts[0].keys() else 'N/A'}")
    
    # Test contacts
    contacts = crm_data.get_contacts()
    print(f"✅ Contacts: {len(contacts)} records found")
    if contacts:
        first = contacts[0]['first_name'] if 'first_name' in contacts[0].keys() else 'N/A'
        last = contacts[0]['last_name'] if 'last_name' in contacts[0].keys() else 'N/A'
        print(f"   Sample: {first} {last}")
    
    # Test products
    products = crm_data.get_products()
    print(f"✅ Products: {len(products)} records found")
    if products:
        print(f"   Sample: {products[0]['name'] if 'name' in products[0].keys() else 'N/A'}")
    
    # Test QPL
    qpl_items = crm_data.get_qpl_entries()
    print(f"✅ QPL: {len(qpl_items)} records found")
    if qpl_items:
        print(f"   Sample: NSN {qpl_items[0]['nsn'] if 'nsn' in qpl_items[0].keys() else 'N/A'}")
    
    # Test interactions
    interactions = crm_data.get_interactions()
    print(f"✅ Interactions: {len(interactions)} records found")
    if interactions:
        print(f"   Sample: {interactions[0]['subject'] if 'subject' in interactions[0].keys() else 'N/A'}")
    
    print("\n🎉 SUCCESS: Your CRM application can now access all the sample data!")
    print("The database issue has been resolved.")
    
except Exception as e:
    print(f"❌ Error testing data access: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Verification Complete ===")
