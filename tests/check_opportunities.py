#!/usr/bin/env python3
"""
Check opportunities for calendar display
"""

from src.core.crm_data import crm_data

def check_opportunities():
    opportunities = crm_data.get_opportunities()
    print(f'Total opportunities: {len(opportunities)}')
    print('\nOpportunities with close_date:')
    
    count_with_close_date = 0
    for opp in opportunities[:10]:  # Show first 10
        close_date = opp.get('close_date', 'None')
        if close_date and close_date != 'None':
            count_with_close_date += 1
        print(f'ID: {opp["id"]}, Name: {opp["name"]}, Close Date: {close_date}')
    
    print(f'\nOpportunities with close_date: {count_with_close_date}/{len(opportunities)}')

if __name__ == '__main__':
    check_opportunities()
