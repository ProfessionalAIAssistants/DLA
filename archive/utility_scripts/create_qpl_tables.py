#!/usr/bin/env python3
"""
QPL (Qualified Products List) Database Setup
Creates the necessary tables and relationships for QPL management
"""

import sqlite3
import os
import sys

def create_qpl_tables():
    """Create QPL-related database tables"""
    
    # Connect to database
    db_path = os.path.join('data', 'crm.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create product_manufacturers table (QPL entries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_manufacturers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                manufacturer_name TEXT NOT NULL,
                cage_code TEXT,
                part_number TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                UNIQUE(product_id, account_id, part_number)
            )
        """)
        print("✓ Created product_manufacturers table")
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_manufacturers_product_id 
            ON product_manufacturers (product_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_manufacturers_account_id 
            ON product_manufacturers (account_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_manufacturers_cage_code 
            ON product_manufacturers (cage_code)
        """)
        print("✓ Created indexes")
        
        # Update accounts table to ensure type field can handle QPL
        cursor.execute("""
            UPDATE accounts SET type = 'QPL' 
            WHERE type IS NULL AND cage IS NOT NULL
        """)
        print("✓ Updated existing accounts with CAGE codes to QPL type")
        
        # Create a view for easy QPL lookups
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS qpl_view AS
            SELECT 
                pm.id as qpl_id,
                p.nsn,
                p.name as product_name,
                p.description as product_description,
                a.name as manufacturer_name,
                a.cage as cage_code,
                pm.part_number,
                pm.is_active,
                pm.created_date
            FROM product_manufacturers pm
            JOIN products p ON pm.product_id = p.id
            JOIN accounts a ON pm.account_id = a.id
            WHERE pm.is_active = 1 AND a.type = 'QPL'
            ORDER BY p.nsn, a.name
        """)
        print("✓ Created QPL view")
        
        conn.commit()
        print("\n🎉 QPL database structure created successfully!")
        
        # Show current counts
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE type = 'QPL'")
        qpl_account_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_manufacturers")
        qpl_entry_count = cursor.fetchone()[0]
        
        print(f"\nCurrent Status:")
        print(f"  Products: {product_count}")
        print(f"  QPL Accounts: {qpl_account_count}")
        print(f"  QPL Entries: {qpl_entry_count}")
        
    except Exception as e:
        print(f"❌ Error creating QPL tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_qpl_tables()
