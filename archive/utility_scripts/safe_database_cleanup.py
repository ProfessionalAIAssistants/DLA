#!/usr/bin/env python3
"""
Safe Database Cleanup Script
1. Remove redundant product_manufacturers_new table
2. Fix project_products.product_id data type mismatch (TEXT → INTEGER)
"""

import sqlite3
import os

def main():
    print('=== SAFE DATABASE CLEANUP SCRIPT ===')
    
    db_path = 'data/crm.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Check and remove product_manufacturers_new if it exists
        print('\n1. Checking for product_manufacturers_new table...')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_manufacturers_new'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute('SELECT COUNT(*) FROM product_manufacturers_new')
            row_count = cursor.fetchone()[0]
            print(f'   Found table with {row_count} rows')
            
            if row_count == 0:
                cursor.execute('DROP TABLE product_manufacturers_new')
                print('   ✅ Removed empty product_manufacturers_new table')
            else:
                print(f'   ⚠️  Table has {row_count} rows - manual review needed')
                cursor.execute('SELECT * FROM product_manufacturers_new LIMIT 3')
                sample = cursor.fetchall()
                for row in sample:
                    print(f'     {row}')
        else:
            print('   ✅ product_manufacturers_new table already removed')
        
        # 2. Check project_products table structure
        print('\n2. Checking project_products table...')
        cursor.execute("PRAGMA table_info(project_products)")
        columns = cursor.fetchall()
        
        product_id_column = None
        for col in columns:
            if col[1] == 'product_id':
                product_id_column = col
                break
        
        if product_id_column:
            col_type = product_id_column[2]
            print(f'   project_products.product_id type: {col_type}')
            
            if col_type == 'TEXT':
                print('   ⚠️  product_id is TEXT, should be INTEGER')
                
                # Check if there's data
                cursor.execute('SELECT COUNT(*) FROM project_products')
                row_count = cursor.fetchone()[0]
                print(f'   Table has {row_count} rows')
                
                if row_count == 0:
                    print('   Safe to fix since table is empty')
                    
                    # Get the current schema
                    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='project_products'")
                    current_sql = cursor.fetchone()[0]
                    print(f'   Current schema: {current_sql}')
                    
                    # Create corrected schema
                    new_sql = current_sql.replace('product_id TEXT', 'product_id INTEGER')
                    print(f'   New schema: {new_sql}')
                    
                    # Check for dependent views
                    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' AND sql LIKE '%project_products%'")
                    dependent_views = cursor.fetchall()
                    
                    if dependent_views:
                        print(f'   Found {len(dependent_views)} dependent views:')
                        for view_name, view_sql in dependent_views:
                            print(f'     - {view_name}')
                    
                    # For safety, let's just verify the foreign key constraint would work
                    print('   Verifying foreign key compatibility...')
                    cursor.execute('SELECT COUNT(*) FROM products WHERE TYPEOF(id) != "integer"')
                    non_int_products = cursor.fetchone()[0]
                    
                    if non_int_products > 0:
                        print(f'   ⚠️  Found {non_int_products} products with non-integer IDs')
                    else:
                        print('   ✅ All products have integer IDs - foreign key will work')
                        
                        # Since the table is empty, we can recreate it safely
                        cursor.execute('DROP TABLE project_products')
                        cursor.execute(new_sql)
                        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_products ON project_products (project_id)')
                        print('   ✅ Recreated project_products table with INTEGER product_id')
                    
                else:
                    print(f'   ⚠️  Table has data - would need careful migration')
                    
            elif col_type == 'INTEGER':
                print('   ✅ product_id is already INTEGER')
        else:
            print('   ❌ product_id column not found!')
        
        # 3. Final verification
        print('\n3. Final verification...')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        has_redundant = 'product_manufacturers_new' in tables
        print(f'   product_manufacturers_new exists: {has_redundant}')
        
        if 'project_products' in tables:
            cursor.execute("PRAGMA table_info(project_products)")
            columns = cursor.fetchall()
            for col in columns:
                if col[1] == 'product_id':
                    print(f'   project_products.product_id type: {col[2]}')
                    break
        
        # Check views are working
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cursor.fetchall()
        print(f'   Views in database: {len(views)}')
        
        for view_name, in views:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {view_name}')
                print(f'     ✅ {view_name} - working')
            except Exception as e:
                print(f'     ❌ {view_name} - error: {e}')
        
        conn.commit()
        print('\n✅ Database cleanup completed successfully!')
        
    except Exception as e:
        print(f'\n❌ Error during cleanup: {e}')
        conn.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
