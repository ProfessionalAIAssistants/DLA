#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.crm_data import CRMData

def test_existing_nsn():
    crm = CRMData()
    
    try:
        # Get existing opportunity
        print("Retrieving existing opportunity...")
        opp = crm.get_opportunity_by_id(3)
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
    test_existing_nsn()
