#!/usr/bin/env python3
"""
Test script to verify PDF processing updates existing contacts and accounts
"""

from src.core.crm_data import crm_data

def test_pdf_update_functionality():
    print("Testing PDF Processing Update Functionality...")
    
    # First, create a basic contact and account that will be updated
    print("\n1. Creating initial contact and account...")
    
    # Create initial account
    initial_account_data = {
        'name': 'DLA AVIATION AVIATION SUPPLY CHAIN',
        'type': 'Customer',
        'summary': 'Initial account',
        'is_active': True
    }
    
    try:
        account_id = crm_data.create_account(**initial_account_data)
        print(f"   ✅ Created initial account: {account_id}")
    except Exception as e:
        print(f"   Account may already exist: {e}")
        # Find existing account
        accounts = crm_data.get_accounts({'name': 'DLA AVIATION AVIATION SUPPLY CHAIN'})
        account_id = accounts[0]['id'] if accounts else None
        print(f"   📋 Using existing account: {account_id}")
    
    # Create initial contact (minimal info)
    initial_contact_data = {
        'first_name': 'Scott',
        'last_name': 'Brunner', 
        'email': 'Scott.Brunner.test@dla.mil',  # Use test email
        'lead_source': 'Initial Import',
        'is_active': True
    }
    
    try:
        contact_id = crm_data.create_contact(**initial_contact_data)
        print(f"   ✅ Created initial contact: {contact_id}")
    except Exception as e:
        print(f"   Contact may already exist: {e}")
        # Find existing contact
        contacts = crm_data.get_contacts({'email': 'Scott.Brunner.test@dla.mil'})
        contact_id = contacts[0]['id'] if contacts else None
        print(f"   📋 Using existing contact: {contact_id}")
    
    # Show initial state
    print("\n2. Initial Contact State:")
    if contact_id:
        contact = crm_data.get_contact_by_id(contact_id)
        print(f"   Name: {contact.get('first_name', '')} {contact.get('last_name', '')}")
        print(f"   Email: {contact.get('email', 'None')}")
        print(f"   Phone: {contact.get('phone', 'None')}")
        print(f"   Buyer Code: {contact.get('buyer_code', 'None')}")
        print(f"   Fax: {contact.get('fax', 'None')}")
        print(f"   Account ID: {contact.get('account_id', 'None')}")
    
    print("\n3. Initial Account State:")
    if account_id:
        account = crm_data.get_account_by_id(account_id)
        print(f"   Name: {account.get('name', 'None')}")
        print(f"   Summary: {account.get('summary', 'None')}")
        print(f"   Billing Address: {account.get('billing_address', 'None')}")
    
    # Now test PDF processing with enhanced data
    print("\n4. Processing PDF with enhanced data...")
    
    test_pdf_data = {
        'request_number': 'SPE4A1-UPDATE-TEST',
        'office': 'DLA AVIATION',
        'division': 'AVIATION SUPPLY CHAIN',
        'address': '6090 STRATHMORE ROAD\nRICHMOND VA 23237\nUSA',
        'buyer': 'Scott Brunner',
        'buyer_code': 'DSB0035',
        'telephone': '804-279-5901',
        'email': 'Scott.Brunner.test@dla.mil',
        'fax': '804-279-5902',
        'nsn': '1234567890124',
        'product_description': 'Updated Test Product',
        'quantity': '150',
        'unit': 'EA',
        'mfr': 'UPDATED MFR',
        'delivery_days': '120',
        'fob': 'ORIGIN',
        'packaging_type': 'Standard',
        'iso': 'NO',
        'sampling': 'NO',
        'close_date': '2025-12-31'
    }
    
    # Import the processor
    from src.pdf.dibbs_crm_processor import DIBBsCRMProcessor
    processor = DIBBsCRMProcessor()
    
    # Test the create_crm_opportunity method (which should update existing records)
    try:
        opportunity_id = processor.create_crm_opportunity(test_pdf_data, '')
        print(f"   ✅ Processed PDF - Opportunity: {opportunity_id}")
        
        # Check the results for updates
        if hasattr(processor.results, 'updated_contacts') and processor.results['updated_contacts']:
            print(f"   📞 Contact Updates: {len(processor.results['updated_contacts'])}")
            for update in processor.results['updated_contacts']:
                print(f"      - {update['name']}: {', '.join(update['updates'])}")
        
        if hasattr(processor.results, 'updated_accounts') and processor.results['updated_accounts']:
            print(f"   🏢 Account Updates: {len(processor.results['updated_accounts'])}")
            for update in processor.results['updated_accounts']:
                print(f"      - {update['name']}: {', '.join(update['updates'])}")
        
    except Exception as e:
        print(f"   ❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Show final state
    print("\n5. Updated Contact State:")
    if contact_id:
        contact = crm_data.get_contact_by_id(contact_id)
        print(f"   Name: {contact.get('first_name', '')} {contact.get('last_name', '')}")
        print(f"   Email: {contact.get('email', 'None')}")
        print(f"   Phone: {contact.get('phone', 'None')} ← Should be updated")
        print(f"   Buyer Code: {contact.get('buyer_code', 'None')} ← Should be updated")
        print(f"   Fax: {contact.get('fax', 'None')} ← Should be updated")
        print(f"   Account ID: {contact.get('account_id', 'None')} ← Should be linked")
    
    print("\n6. Updated Account State:")
    if account_id:
        account = crm_data.get_account_by_id(account_id)
        print(f"   Name: {account.get('name', 'None')}")
        print(f"   Summary: {account.get('summary', 'None')} ← Should be updated")
        print(f"   Billing Address: {account.get('billing_address', 'None')} ← Should be updated")
    
    print("\n✅ Update functionality test completed!")

if __name__ == '__main__':
    test_pdf_update_functionality()
