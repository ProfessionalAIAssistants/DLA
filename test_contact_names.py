#!/usr/bin/env python
# coding: utf-8

"""
Quick Contact Names Test
Tests if contact names are now displaying properly after the fix
"""

import sys
import os
sys.path.append(os.getcwd())

try:
    from crm_data import crm_data
    
    print("=== Contact Names Test ===")
    
    # Test getting contacts with names
    contacts = crm_data.get_contacts(limit=5)
    print(f"Found {len(contacts)} contacts")
    
    for i, contact in enumerate(contacts, 1):
        name = contact.get('name', 'N/A')
        email = contact.get('email', 'No email')
        first_name = contact.get('first_name', 'N/A')
        last_name = contact.get('last_name', 'N/A')
        
        print(f"{i}. Name: '{name}' | First: '{first_name}' | Last: '{last_name}' | Email: {email}")
    
    print("\n✅ Contact names fix test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=== Test Complete ===")
