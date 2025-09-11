#!/usr/bin/env python3
"""
Test script to verify PDF processing creates proper accounts and contacts
"""

from src.core.crm_data import crm_data

def test_pdf_integration():
    print("Testing PDF Processing Integration...")
    
    # Test data simulating what would come from PDF parsing
    test_pdf_data = {
        'request_number': 'SPE4A1-TEST-123',
        'office': 'DLA AVIATION',
        'division': 'AVIATION SUPPLY CHAIN',
        'address': '6090 STRATHMORE ROAD\nRICHMOND VA 23237\nUSA',
        'buyer': 'Scott Brunner',
        'buyer_code': 'DSB0035',
        'telephone': '804-279-5901',
        'email': 'test.new.buyer@dla.mil',
        'fax': '',
        'nsn': '1234567890123',
        'product_description': 'Test Product',
        'quantity': '100',
        'unit': 'EA',
        'mfr': 'TEST MFR',
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
    
    # Test the create_crm_opportunity method
    try:
        opportunity_id = processor.create_crm_opportunity(test_pdf_data, '')
        print(f"✅ Created opportunity: {opportunity_id}")
        
        # Verify the opportunity was created with proper links
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if opportunity:
            print(f"  - Opportunity Name: {opportunity['name']}")
            print(f"  - Contact ID: {opportunity.get('contact_id', 'None')}")
            print(f"  - Account ID: {opportunity.get('account_id', 'None')}")
            print(f"  - Buyer: {opportunity.get('buyer', 'None')}")
            
            # Check contact details
            if opportunity.get('contact_id'):
                contact = crm_data.get_contact_by_id(opportunity['contact_id'])
                if contact:
                    print(f"  - Contact Name: {contact.get('first_name', '')} {contact.get('last_name', '')}")
                    print(f"  - Contact Email: {contact.get('email', 'None')}")
                    print(f"  - Contact Phone: {contact.get('phone', 'None')}")
                    print(f"  - Contact Buyer Code: {contact.get('buyer_code', 'None')}")
                    print(f"  - Contact Fax: {contact.get('fax', 'None')}")
            
            # Check account details
            if opportunity.get('account_id'):
                account = crm_data.get_account_by_id(opportunity['account_id'])
                if account:
                    print(f"  - Account Name: {account.get('name', 'None')}")
                    print(f"  - Account Address: {account.get('billing_address', 'None')}")
        
    except Exception as e:
        print(f"❌ Error creating opportunity: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pdf_integration()
