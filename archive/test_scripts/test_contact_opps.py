#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.crm_data import CRMDataManager

crm = CRMDataManager()
print('Testing contact opportunities...')

# Get a contact ID that has opportunities
all_opps = crm.get_opportunities()
if all_opps:
    for opp in all_opps[:5]:
        if opp.get('contact_id'):
            contact_id = opp['contact_id']
            print(f'Contact ID {contact_id}:')
            filtered_opps = crm.get_opportunities({'contact_id': contact_id})
            print(f'  Found {len(filtered_opps)} opportunities')
            for op in filtered_opps:
                print(f'    {op["id"]}: {op["name"]}')
            break
else:
    print('No opportunities found')
