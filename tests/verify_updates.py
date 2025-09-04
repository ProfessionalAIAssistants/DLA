#!/usr/bin/env python3
"""
Quick verification of contact update functionality
"""
import sys
sys.path.append('src')
from core import crm_data

def verify_contact_updates():
    # Get the test contact
    contact = crm_data.get_contact(238)
    
    print("Final Contact Verification:")
    print(f"  Phone: {contact['phone']}")
    print(f"  Buyer Code: {contact['buyer_code']}")
    print(f"  Fax: {contact['fax']}")
    print(f"  Account ID: {contact['account_id']}")
    print(f"  Department: {contact['department']}")
    print(f"  Address: {contact['address']}")
    
    # Verify all expected fields were updated
    expected_updates = {
        'phone': '804-279-5901',
        'buyer_code': 'DSB0035',
        'fax': '804-279-5902',
        'account_id': 53,
        'department': 'AVIATION SUPPLY CHAIN'
    }
    
    all_good = True
    for field, expected in expected_updates.items():
        actual = contact[field]
        if actual != expected:
            print(f"❌ {field}: expected '{expected}', got '{actual}'")
            all_good = False
        else:
            print(f"✅ {field}: correctly updated to '{actual}'")
    
    if all_good:
        print("\n🎉 All contact updates verified successfully!")
    else:
        print("\n⚠️ Some updates may not have applied correctly")

if __name__ == "__main__":
    verify_contact_updates()
