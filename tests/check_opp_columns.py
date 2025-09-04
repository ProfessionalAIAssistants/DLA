#!/usr/bin/env python3

import sqlite3

def check_opportunity_columns():
    conn = sqlite3.connect("data/crm.db")
    cursor = conn.cursor()
    
    # Check if opportunities table has an nsn column
    cursor.execute("PRAGMA table_info(opportunities)")
    columns = cursor.fetchall()
    
    print("Opportunities table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - Default: {col[4]}")
        
    # Check if there's any data in the nsn column of opportunities
    cursor.execute("SELECT COUNT(*) FROM opportunities WHERE nsn IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"\nOpportunities with non-null NSN: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_opportunity_columns()
