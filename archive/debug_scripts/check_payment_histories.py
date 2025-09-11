#!/usr/bin/env python3
"""Check opportunity payment histories"""

from src.core.crm_data import crm_data

# Check opportunities and their payment history
opportunities = crm_data.get_opportunities()
print(f'Total opportunities: {len(opportunities) if opportunities else 0}')

if opportunities:
    for i, opp in enumerate(opportunities[:3]):
        print(f'Opportunity {i+1}:')
        print(f'  ID: {opp.get("id")}')
        print(f'  Name: {opp.get("name")}')
        print(f'  NSN: {opp.get("nsn")}')
        payment_history = opp.get('payment_history', '')
        if payment_history:
            print(f'  Payment History Length: {len(payment_history)}')
            print(f'  Payment History Preview: {payment_history[:150]}...')
        else:
            print('  Payment History: None or empty')
        print()

# Also check product 1 specifically 
product = crm_data.get_product_by_id(1)
if product:
    print(f'Product 1: {product.get("name")} (NSN: {product.get("nsn")})')
    # Get opportunities for this product by NSN
    product_opps = crm_data.get_opportunities({'nsn': product.get('nsn')}) if product.get('nsn') else []
    print(f'Opportunities for this product: {len(product_opps)}')
    for opp in product_opps:
        print(f'  - {opp.get("name")} (Payment History: {len(opp.get("payment_history", ""))} chars)')
