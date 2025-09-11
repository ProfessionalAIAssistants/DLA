#!/usr/bin/env python3
"""Add test vendor accounts and contacts for RFQ testing"""

import sqlite3

def add_test_vendors():
    """Add test vendor accounts"""
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # Add test vendor accounts
    test_vendors = [
        ('Parker Hannifin Corp', 'Vendor', '01234', 'https://parker.com', 'Cleveland, OH'),
        ('Honeywell International', 'Vendor', '70210', 'https://honeywell.com', 'Charlotte, NC'),
        ('Boeing Company', 'QPL', '81205', 'https://boeing.com', 'Chicago, IL')
    ]
    
    for vendor_name, vendor_type, cage, website, location in test_vendors:
        cursor.execute('''
            INSERT OR IGNORE INTO accounts (name, type, cage, website, location, created_date, is_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (vendor_name, vendor_type, cage, website, location))
    
    # Add contacts for the vendor accounts
    test_contacts = [
        (3, 'John', 'Smith', 'john.smith@moog.com', 'Sales Representative', '+1-716-652-2000'),  # MOOG INC
        (6, 'Sarah', 'Johnson', 'sarah.johnson@parker.com', 'Account Manager', '+1-216-896-3000'),  # Parker
        (7, 'Mike', 'Wilson', 'mike.wilson@honeywell.com', 'Business Development', '+1-704-627-6000'),  # Honeywell
        (8, 'Lisa', 'Brown', 'lisa.brown@boeing.com', 'Sales Director', '+1-312-544-2000')  # Boeing
    ]
    
    for account_id, first_name, last_name, email, title, phone in test_contacts:
        cursor.execute('''
            INSERT OR IGNORE INTO contacts 
            (account_id, first_name, last_name, email, title, phone, created_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (account_id, first_name, last_name, email, title, phone))
    
    conn.commit()
    
    # Show updated vendor accounts
    cursor.execute('SELECT id, name, type, cage FROM accounts WHERE type IN ("Vendor", "QPL") ORDER BY name')
    vendor_accounts = cursor.fetchall()
    print('Updated vendor and QPL accounts:')
    for acc in vendor_accounts:
        cage_display = acc[3] if acc[3] else 'None'
        print(f'  Account {acc[0]}: {acc[1]} (Type: {acc[2]}, CAGE: {cage_display})')
    
    # Show contacts for vendor accounts
    cursor.execute('''
        SELECT c.id, a.name, c.first_name, c.last_name, c.email, c.title
        FROM contacts c
        JOIN accounts a ON c.account_id = a.id
        WHERE a.type IN ("Vendor", "QPL")
        ORDER BY a.name, c.last_name
    ''')
    contacts = cursor.fetchall()
    print('\nVendor contacts:')
    for contact in contacts:
        print(f'  {contact[1]}: {contact[2]} {contact[3]} ({contact[4]}) - {contact[5]}')
    
    conn.close()
    print(f'\n✓ Added test vendor accounts and contacts')

if __name__ == '__main__':
    add_test_vendors()
