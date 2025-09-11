#!/usr/bin/env python3
"""
Add test opportunities with future close dates for calendar testing
"""

from src.core.crm_data import crm_data
from datetime import datetime, timedelta

def add_test_opportunities():
    # Create opportunities with future close dates
    test_opportunities = [
        {
            'name': 'Test Future Opportunity 1',
            'description': 'Test opportunity for calendar display',
            'stage': 'Prospecting',
            'close_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'amount': 50000,
            'quantity': 100,
            'mfr': 'TEST-MFR',
            'buyer': 'Test Buyer',
            'fob': 'Origin'
        },
        {
            'name': 'Test Future Opportunity 2',
            'description': 'Another test opportunity for calendar',
            'stage': 'RFQ Requested',
            'close_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'amount': 75000,
            'quantity': 200,
            'mfr': 'TEST-MFR-2',
            'buyer': 'Test Buyer 2',
            'fob': 'Destination'
        },
        {
            'name': 'Test Future Opportunity 3',
            'description': 'Third test opportunity for calendar',
            'stage': 'Project Started',
            'close_date': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
            'amount': 100000,
            'quantity': 150,
            'mfr': 'TEST-MFR-3',
            'buyer': 'Test Buyer 3',
            'fob': 'Origin'
        }
    ]
    
    print("Adding test opportunities with future close dates...")
    
    for opp_data in test_opportunities:
        try:
            opp_id = crm_data.create_opportunity(**opp_data)
            print(f"Created opportunity {opp_id}: {opp_data['name']} - Close Date: {opp_data['close_date']}")
        except Exception as e:
            print(f"Error creating opportunity {opp_data['name']}: {e}")
    
    print("\nTest opportunities added successfully!")

if __name__ == '__main__':
    add_test_opportunities()
