#!/usr/bin/env python3
"""
Comprehensive Database Audit Script
Checks for useless tables, duplicates, and issues
"""

import sqlite3
import json
from collections import defaultdict, Counter

def main():
    print('=== COMPREHENSIVE DATABASE AUDIT ===')
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # 1. Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'\n1. TOTAL TABLES: {len(tables)}')
    for table in tables:
        print(f'   - {table}')
    
    # 2. Check table sizes and structure
    print('\n2. TABLE ANALYSIS:')
    table_info = {}
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            
            table_info[table] = {
                'row_count': count,
                'column_count': len(columns),
                'columns': [col[1] for col in columns]
            }
            
            status = "EMPTY" if count == 0 else "ACTIVE"
            print(f'   {table:<30} {count:>6} rows  {len(columns):>2} cols  [{status}]')
            
        except Exception as e:
            print(f'   {table:<30} ERROR: {e}')
    
    # 3. Look for suspicious tables
    print('\n3. SUSPICIOUS TABLES CHECK:')
    suspicious_patterns = ['backup', 'old', 'temp', 'test', '_new', 'copy', 'duplicate']
    suspicious_tables = []
    
    for table in tables:
        table_lower = table.lower()
        for pattern in suspicious_patterns:
            if pattern in table_lower:
                suspicious_tables.append((table, pattern, table_info.get(table, {}).get('row_count', 0)))
    
    if suspicious_tables:
        print('   Found suspicious tables:')
        for table, pattern, count in suspicious_tables:
            print(f'   - {table} (contains "{pattern}") - {count} rows')
    else:
        print('   No obviously suspicious tables found')
    
    # 4. Check for empty tables
    print('\n4. EMPTY TABLES CHECK:')
    empty_tables = [table for table, info in table_info.items() if info['row_count'] == 0]
    if empty_tables:
        print('   Empty tables (potential candidates for removal):')
        for table in empty_tables:
            print(f'   - {table}')
    else:
        print('   No empty tables found')
    
    # 5. Check for similar table structures (potential duplicates)
    print('\n5. SIMILAR TABLE STRUCTURES:')
    structure_groups = defaultdict(list)
    for table, info in table_info.items():
        if info['columns']:  # Only if we got column info
            # Create a signature based on column names
            col_signature = tuple(sorted(info['columns']))
            structure_groups[col_signature].append(table)
    
    similar_found = False
    for signature, table_list in structure_groups.items():
        if len(table_list) > 1:
            similar_found = True
            print(f'   Similar structure tables:')
            for table in table_list:
                count = table_info[table]['row_count']
                print(f'   - {table} ({count} rows)')
            print(f'     Columns: {", ".join(signature)}')
            print()
    
    if not similar_found:
        print('   No tables with identical structures found')
    
    # 6. Check specific business logic issues
    print('\n6. BUSINESS LOGIC CHECKS:')
    
    # Check for QPL-related tables
    qpl_tables = [table for table in tables if 'qpl' in table.lower()]
    print(f'   QPL-related tables: {qpl_tables}')
    
    # Check accounts
    if 'accounts' in tables:
        cursor.execute('SELECT COUNT(*) FROM accounts')
        account_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT name) FROM accounts')
        unique_names = cursor.fetchone()[0]
        
        if account_count != unique_names:
            print(f'   ⚠️  ACCOUNTS: {account_count} total, {unique_names} unique names - potential duplicates!')
        else:
            print(f'   ✅ ACCOUNTS: {account_count} accounts, all unique names')
    
    # Check contacts
    if 'contacts' in tables:
        cursor.execute('SELECT COUNT(*) FROM contacts')
        contact_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT email) FROM contacts WHERE email IS NOT NULL AND email != ""')
        unique_emails = cursor.fetchone()[0]
        
        cursor.execute('SELECT email, COUNT(*) as cnt FROM contacts WHERE email IS NOT NULL AND email != "" GROUP BY email HAVING cnt > 1')
        duplicate_emails = cursor.fetchall()
        
        if duplicate_emails:
            print(f'   ⚠️  CONTACTS: Duplicate emails found:')
            for email, count in duplicate_emails:
                print(f'      - {email}: {count} contacts')
        else:
            print(f'   ✅ CONTACTS: No duplicate emails found')
    
    # Check opportunities
    if 'opportunities' in tables:
        cursor.execute('SELECT COUNT(*) FROM opportunities')
        opp_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT name, COUNT(*) as cnt FROM opportunities GROUP BY name HAVING cnt > 1')
        duplicate_names = cursor.fetchall()
        
        if duplicate_names:
            print(f'   ⚠️  OPPORTUNITIES: Duplicate names found:')
            for name, count in duplicate_names[:5]:  # Show first 5
                print(f'      - {name}: {count} opportunities')
        else:
            print(f'   ✅ OPPORTUNITIES: No duplicate names found')
    
    # Check products
    if 'products' in tables:
        cursor.execute('SELECT COUNT(*) FROM products')
        product_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT nsn, COUNT(*) as cnt FROM products WHERE nsn IS NOT NULL AND nsn != "" GROUP BY nsn HAVING cnt > 1')
        duplicate_nsns = cursor.fetchall()
        
        if duplicate_nsns:
            print(f'   ⚠️  PRODUCTS: Duplicate NSNs found:')
            for nsn, count in duplicate_nsns:
                print(f'      - NSN {nsn}: {count} products')
        else:
            print(f'   ✅ PRODUCTS: No duplicate NSNs found')
    
    # 7. Check foreign key consistency
    print('\n7. FOREIGN KEY CONSISTENCY:')
    
    # Check opportunities -> products
    if 'opportunities' in tables and 'products' in tables:
        cursor.execute('''
            SELECT COUNT(*) FROM opportunities 
            WHERE product_id IS NOT NULL 
            AND product_id NOT IN (SELECT id FROM products)
        ''')
        orphaned_opps = cursor.fetchone()[0]
        
        if orphaned_opps > 0:
            print(f'   ⚠️  OPPORTUNITIES: {orphaned_opps} have invalid product_id references')
        else:
            print(f'   ✅ OPPORTUNITIES: All product_id references are valid')
    
    # Check contacts -> accounts
    if 'contacts' in tables and 'accounts' in tables:
        cursor.execute('''
            SELECT COUNT(*) FROM contacts 
            WHERE account_id IS NOT NULL 
            AND account_id NOT IN (SELECT id FROM accounts)
        ''')
        orphaned_contacts = cursor.fetchone()[0]
        
        if orphaned_contacts > 0:
            print(f'   ⚠️  CONTACTS: {orphaned_contacts} have invalid account_id references')
        else:
            print(f'   ✅ CONTACTS: All account_id references are valid')
    
    # Check qpls -> products and accounts
    if 'qpls' in tables and 'products' in tables and 'accounts' in tables:
        cursor.execute('''
            SELECT COUNT(*) FROM qpls 
            WHERE product_id IS NOT NULL 
            AND product_id NOT IN (SELECT id FROM products)
        ''')
        orphaned_qpl_products = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM qpls 
            WHERE account_id IS NOT NULL 
            AND account_id NOT IN (SELECT id FROM accounts)
        ''')
        orphaned_qpl_accounts = cursor.fetchone()[0]
        
        if orphaned_qpl_products > 0:
            print(f'   ⚠️  QPLS: {orphaned_qpl_products} have invalid product_id references')
        elif orphaned_qpl_accounts > 0:
            print(f'   ⚠️  QPLS: {orphaned_qpl_accounts} have invalid account_id references')
        else:
            print(f'   ✅ QPLS: All foreign key references are valid')
    
    conn.close()
    
    print('\n=== DATABASE AUDIT COMPLETE ===')

if __name__ == "__main__":
    main()
