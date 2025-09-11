#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.crm_data import CRMData

def test_nsn_display():
    crm = CRMData()
    
    try:
        # Create a test product with NSN
        print("Creating test product with NSN...")
        product_id = crm.create_product(
            name="Test Product NSN 9876543210123",
            nsn="9876543210123",
            description="Test product for NSN display"
        )
        print(f"Created product ID: {product_id}")
        
        # Create a test account
        print("Creating test account...")
        account_id = crm.create_account(
            name="Test Account NSN",
            type="Customer"
        )
        print(f"Created account ID: {account_id}")
        
        # Create a test opportunity linked to the product
        print("Creating test opportunity...")
        opp_id = crm.create_opportunity(
            name="Test Opportunity NSN",
            product_id=product_id,
            account_id=account_id,
            stage="Prospecting",
            quantity=10,
            description="Test opportunity to verify NSN display"
        )
        print(f"Created opportunity ID: {opp_id}")
        
        # Retrieve the opportunity to check NSN
        print("\nRetrieving opportunity with NSN...")
        opp = crm.get_opportunity_by_id(opp_id)
        if opp:
            print(f"Opportunity: {opp['name']}")
            print(f"Product: {opp['product_name']}")
            print(f"NSN (old): {opp.get('nsn', 'NOT FOUND')}")
            print(f"Product NSN (new): {opp.get('product_nsn', 'NOT FOUND')}")
        else:
            print("Could not retrieve opportunity")
        
        # Get all opportunities
        print("\nRetrieving all opportunities...")
        opps = crm.get_opportunities()
        for opp in opps:
            print(f"  ID: {opp['id']}, Name: {opp['name']}, NSN: {opp.get('nsn', 'N/A')}, Product NSN: {opp.get('product_nsn', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nsn_display()
