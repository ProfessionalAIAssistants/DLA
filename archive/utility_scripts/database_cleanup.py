#!/usr/bin/env python3
"""
Database Cleanup Script
1. Remove redundant product_manufacturers_new table
2. Fix project_products.product_id data type mismatch (TEXT → INTEGER)
"""

import sqlite3
import os

def main():
    print('=== DATABASE CLEANUP SCRIPT ===')
    
    db_path = 'data/crm.db'
    backup_path = 'data/crm_backup_before_cleanup.db'
    
    # Create backup first
    print('\n1. Creating backup...')
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f'   ✅ Backup created: {backup_path}')
    else:
        print(f'   ❌ Database not found: {db_path}')
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if product_manufacturers_new exists and has data
        print('\n2. Checking product_manufacturers_new table...')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_manufacturers_new'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute('SELECT COUNT(*) FROM product_manufacturers_new')
            row_count = cursor.fetchone()[0]
            print(f'   Table exists with {row_count} rows')
            
            if row_count > 0:
                print('   ⚠️  Table contains data! Checking if it needs to be migrated...')
                
                # Check what data exists in product_manufacturers_new vs qpls
                cursor.execute('SELECT * FROM product_manufacturers_new LIMIT 5')
                sample_data = cursor.fetchall()
                print('   Sample data from product_manufacturers_new:')
                for row in sample_data:
                    print(f'     {row}')
                
                response = input('\n   Do you want to proceed with deletion? (y/N): ')
                if response.lower() != 'y':
                    print('   Cleanup cancelled by user')
                    conn.close()
                    return
            
            # Drop the table
            print('   Dropping product_manufacturers_new table...')
            cursor.execute('DROP TABLE product_manufacturers_new')
            print('   ✅ Table dropped successfully')
            
        else:
            print('   Table does not exist - no action needed')
        
        # Fix project_products.product_id data type
        print('\n3. Fixing project_products.product_id data type...')
        
        # Check current structure
        cursor.execute("PRAGMA table_info(project_products)")
        columns = cursor.fetchall()
        print('   Current project_products structure:')
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            marker = ' ←← NEEDS FIX' if col_name == 'product_id' and col_type == 'TEXT' else ''
            print(f'     {col_name}: {col_type}{marker}')
        
        # Check if there's data in project_products
        cursor.execute('SELECT COUNT(*) FROM project_products')
        pp_count = cursor.fetchone()[0]
        print(f'   project_products has {pp_count} rows')
        
        # Check if any product_id values are non-numeric
        if pp_count > 0:
            cursor.execute('SELECT product_id FROM project_products WHERE product_id NOT GLOB "[0-9]*" OR product_id = ""')
            non_numeric = cursor.fetchall()
            if non_numeric:
                print(f'   ⚠️  Found {len(non_numeric)} non-numeric product_id values:')
                for val in non_numeric[:5]:
                    print(f'     "{val[0]}"')
        
        # Create new table with correct structure
        print('   Creating new project_products table with INTEGER product_id...')
        
        cursor.execute('''
            CREATE TABLE project_products_new (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER,
                role TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Copy data, converting product_id to INTEGER where possible
        if pp_count > 0:
            print('   Migrating data...')
            cursor.execute('''
                INSERT INTO project_products_new (id, project_id, product_id, quantity, role, created_date)
                SELECT 
                    id, 
                    project_id,
                    CASE 
                        WHEN product_id GLOB "[0-9]*" AND product_id != "" 
                        THEN CAST(product_id AS INTEGER)
                        ELSE NULL 
                    END as product_id,
                    quantity,
                    role,
                    created_date
                FROM project_products
                WHERE product_id GLOB "[0-9]*" AND product_id != ""
            ''')
            
            migrated_count = cursor.rowcount
            print(f'   Migrated {migrated_count} valid rows')
            
            if migrated_count < pp_count:
                print(f'   ⚠️  {pp_count - migrated_count} rows with invalid product_id were skipped')
        
        # Check for views that depend on project_products
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' AND sql LIKE '%project_products%'")
        dependent_views = cursor.fetchall()
        
        # Drop dependent views temporarily
        view_recreate_sql = {}
        for view_name, view_sql in dependent_views:
            print(f'   Temporarily dropping dependent view: {view_name}')
            view_recreate_sql[view_name] = view_sql
            cursor.execute(f'DROP VIEW {view_name}')
        
        # Replace old table with new one
        cursor.execute('DROP TABLE project_products')
        cursor.execute('ALTER TABLE project_products_new RENAME TO project_products')
        
        # Recreate dependent views
        for view_name, view_sql in view_recreate_sql.items():
            print(f'   Recreating dependent view: {view_name}')
            cursor.execute(view_sql)
        
        # Recreate index
        cursor.execute('CREATE INDEX idx_project_products ON project_products (project_id)')
        
        print('   ✅ project_products table updated with INTEGER product_id')
        
        # Commit all changes
        conn.commit()
        print('\n4. All changes committed successfully!')
        
        # Verify the changes
        print('\n5. Verification:')
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        has_old_table = 'product_manufacturers_new' in tables
        print(f'   product_manufacturers_new exists: {has_old_table}')
        
        # Check project_products structure
        cursor.execute("PRAGMA table_info(project_products)")
        columns = cursor.fetchall()
        product_id_type = None
        for col in columns:
            if col[1] == 'product_id':
                product_id_type = col[2]
                break
        
        print(f'   project_products.product_id type: {product_id_type}')
        
        # Check foreign keys work
        cursor.execute("PRAGMA foreign_key_check(project_products)")
        fk_violations = cursor.fetchall()
        if fk_violations:
            print(f'   ⚠️  Foreign key violations: {len(fk_violations)}')
            for violation in fk_violations:
                print(f'     {violation}')
        else:
            print('   ✅ No foreign key violations')
        
        print('\n=== DATABASE CLEANUP COMPLETE ===')
        print(f'Backup saved as: {backup_path}')
        
    except Exception as e:
        print(f'\n❌ Error during cleanup: {e}')
        conn.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
