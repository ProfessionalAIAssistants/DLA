#!/usr/bin/env python3
"""Quick script to check QPL data"""

import sqlite3

def check_qpls():
    conn = sqlite3.connect('data/crm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Count total QPLs
    cursor.execute("SELECT COUNT(*) as count FROM qpls")
    total = cursor.fetchone()['count']
    print(f"Total QPLs in database: {total}")
    
    # Check sample QPL entries with product info
    cursor.execute("""
        SELECT q.id, q.manufacturer_name, q.cage_code, q.part_number, 
               q.product_id, p.name as product_name, p.nsn,
               a.name as account_name
        FROM qpls q
        LEFT JOIN products p ON q.product_id = p.id
        LEFT JOIN accounts a ON q.account_id = a.id
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    print("\nSample QPL entries:")
    for row in rows:
        print(f"QPL ID: {row['id']}")
        print(f"  Manufacturer: {row['manufacturer_name']}")
        print(f"  CAGE Code: {row['cage_code']}")
        print(f"  Part Number: {row['part_number']}")
        print(f"  Product ID: {row['product_id']}")
        print(f"  Product Name: {row['product_name'] or 'None'}")
        print(f"  NSN: {row['nsn'] or 'None'}")
        print(f"  Account: {row['account_name'] or 'None'}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_qpls()
