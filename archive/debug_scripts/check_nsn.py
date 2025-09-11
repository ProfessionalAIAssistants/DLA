#!/usr/bin/env python3

import sqlite3
import os

def check_nsn():
    db_path = "data/crm.db"
    
    if not os.path.exists(db_path):
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check opportunities table for NSN values
    print("=== OPPORTUNITIES NSN CHECK ===")
    try:
        cursor.execute("SELECT id, name, nsn, request_number FROM opportunities LIMIT 10")
        opportunities = cursor.fetchall()
        if opportunities:
            print(f"Found {len(opportunities)} opportunities:")
            for opp in opportunities:
                print(f"  ID: {opp[0]}, Name: {opp[1]}, NSN: {opp[2]}, Request: {opp[3]}")
        else:
            print("No opportunities found in database")
    except Exception as e:
        print(f"Error checking opportunities: {e}")
    
    # Check products table for NSN values
    print("\n=== PRODUCTS NSN CHECK ===")
    try:
        cursor.execute("SELECT id, name, nsn FROM products LIMIT 10")
        products = cursor.fetchall()
        if products:
            print(f"Found {len(products)} products:")
            for product in products:
                print(f"  ID: {product[0]}, Name: {product[1]}, NSN: {product[2]}")
        else:
            print("No products found in database")
    except Exception as e:
        print(f"Error checking products: {e}")
    
    # Check table structure
    print("\n=== TABLE STRUCTURE ===")
    try:
        cursor.execute("PRAGMA table_info(opportunities)")
        columns = cursor.fetchall()
        print("Opportunities table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error checking table structure: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_nsn()
