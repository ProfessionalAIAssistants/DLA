#!/usr/bin/env python3
"""Test RFQ email generation"""

import requests
import json

def test_rfq_generation():
    """Test generating RFQ emails for an opportunity"""
    opportunity_id = 1  # Use existing opportunity
    vendor_data = {
        'vendors': [
            {'account_id': 3},  # MOOG INC
            {'account_id': 6}   # Parker
        ],
        'template': 'Standard RFQ Request'
    }
    
    response = requests.post(
        f'http://127.0.0.1:5000/api/opportunities/{opportunity_id}/generate-vendor-emails',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(vendor_data)
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            summary = result.get('summary', {})
            success_count = summary.get('success', 0)
            total_count = summary.get('total', 0)
            error_count = summary.get('errors', 0)
            print(f'✓ Successfully generated {success_count} RFQ emails!')
            print(f'  Total: {total_count}')
            print(f'  Errors: {error_count}')
            
            emails = result.get('emails', [])
            for email in emails:
                if 'error' in email:
                    print(f'  ❌ Error: {email["error"]}')
                else:
                    vendor_name = email.get('vendor_name', 'Unknown Vendor')
                    print(f'  ✓ Email created for {vendor_name}')
        else:
            print(f'❌ Error: {result.get("message")}')
    else:
        print(f'❌ HTTP Error: {response.status_code}')
        print(response.text)

if __name__ == '__main__':
    test_rfq_generation()
