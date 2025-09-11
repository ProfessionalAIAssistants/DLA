#!/usr/bin/env python3
"""Update accounts with QPL entries to have QPL account type"""

import sqlite3

def update_qpl_account_types():
    """Update vendor accounts that have QPL entries to QPL type"""
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    try:
        # First, let's see current account types
        cursor.execute('SELECT DISTINCT type FROM accounts WHERE type IS NOT NULL')
        types = cursor.fetchall()
        print('Current account types:', [t[0] for t in types])
        
        # Find accounts that should be QPL type (have QPL entries but are currently Vendor)
        cursor.execute('''
            SELECT DISTINCT a.id, a.name, a.type, a.cage
            FROM accounts a
            JOIN qpls q ON a.id = q.account_id
            WHERE a.type = 'Vendor'
            ORDER BY a.name
        ''')
        vendor_accounts_with_qpl = cursor.fetchall()
        
        print(f'\nAccounts currently typed as "Vendor" but have QPL entries:')
        for acc in vendor_accounts_with_qpl:
            print(f'  Account {acc[0]}: {acc[1]} (Type: {acc[2]}, CAGE: {acc[3]})')
        
        # Update these accounts to QPL type
        if vendor_accounts_with_qpl:
            account_ids = [acc[0] for acc in vendor_accounts_with_qpl]
            placeholders = ','.join(['?' for _ in account_ids])
            cursor.execute(f'''
                UPDATE accounts 
                SET type = 'QPL'
                WHERE id IN ({placeholders})
            ''', account_ids)
            
            updated_count = cursor.rowcount
            conn.commit()
            print(f'\n✓ Updated {updated_count} accounts from "Vendor" to "QPL" type')
        else:
            print('\nNo accounts need updating')
    
    except Exception as e:
        print(f'Error: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_qpl_account_types()
