#!/usr/bin/env python3

import sqlite3
import os

def debug_nsn_join():
    db_path = "data/crm.db"
    
    if not os.path.exists(db_path):
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    cursor = conn.cursor()
    
    # Test the exact query used in get_opportunities
    print("=== TESTING JOINED QUERY WITH ROW FACTORY ===")
    try:
        query = """
            SELECT o.*, 
                   a.name as account_name, 
                   (c.first_name || ' ' || c.last_name) as contact_name, 
                   p.name as product_name,
                   p.nsn as nsn
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = 3
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            print(f"Result type: {type(result)}")
            print(f"Available keys: {list(result.keys())}")
            print(f"Opportunity Name: {result['name']}")
            print(f"Product Name: {result['product_name']}")
            print(f"NSN: {result['nsn']}")
            print(f"NSN type: {type(result['nsn'])}")
            print(f"NSN value: {repr(result['nsn'])}")
        else:
            print("No result found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    conn.close()

if __name__ == "__main__":
    debug_nsn_join()
