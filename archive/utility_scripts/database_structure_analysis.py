#!/usr/bin/env python3
"""
Database Structure Analysis
Shows table schemas, relationships, and structure without data content
"""

import sqlite3

def main():
    print('=== DATABASE STRUCTURE ANALYSIS ===')
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # 1. Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'\n📊 TOTAL TABLES: {len(tables)}')
    
    # 2. Show detailed structure for each table
    for table in tables:
        if table == 'sqlite_sequence':  # Skip SQLite internal table
            continue
            
        print(f'\n🗂️  TABLE: {table.upper()}')
        print('=' * (len(table) + 10))
        
        try:
            # Get column information
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            
            print('   COLUMNS:')
            for col in columns:
                col_id, name, data_type, not_null, default_val, is_pk = col
                
                # Format column info
                pk_marker = ' [PK]' if is_pk else ''
                not_null_marker = ' NOT NULL' if not_null else ''
                default_marker = f' DEFAULT {default_val}' if default_val is not None else ''
                
                print(f'   - {name:<25} {data_type:<15}{pk_marker}{not_null_marker}{default_marker}')
            
            # Get foreign keys
            cursor.execute(f'PRAGMA foreign_key_list({table})')
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print('   FOREIGN KEYS:')
                for fk in foreign_keys:
                    fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                    print(f'   - {from_col} → {ref_table}.{to_col}')
            
            # Get indexes
            cursor.execute(f'PRAGMA index_list({table})')
            indexes = cursor.fetchall()
            
            table_indexes = []
            for index in indexes:
                seq, name, unique, origin, partial = index
                if not name.startswith('sqlite_autoindex'):  # Skip auto-generated indexes
                    cursor.execute(f'PRAGMA index_info({name})')
                    index_cols = cursor.fetchall()
                    col_names = [col[2] for col in index_cols]
                    unique_marker = ' [UNIQUE]' if unique else ''
                    table_indexes.append(f'   - {name}: ({", ".join(col_names)}){unique_marker}')
            
            if table_indexes:
                print('   INDEXES:')
                for idx in table_indexes:
                    print(idx)
                    
        except Exception as e:
            print(f'   ERROR: {e}')
    
    # 3. Show relationships summary
    print(f'\n🔗 FOREIGN KEY RELATIONSHIPS SUMMARY:')
    print('=' * 35)
    
    all_relationships = []
    for table in tables:
        if table == 'sqlite_sequence':
            continue
            
        try:
            cursor.execute(f'PRAGMA foreign_key_list({table})')
            foreign_keys = cursor.fetchall()
            
            for fk in foreign_keys:
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                all_relationships.append(f'{table}.{from_col} → {ref_table}.{to_col}')
                
        except Exception as e:
            continue
    
    if all_relationships:
        for rel in sorted(all_relationships):
            print(f'   {rel}')
    else:
        print('   No foreign key relationships defined')
    
    # 4. Show indexes summary
    print(f'\n📇 ALL INDEXES SUMMARY:')
    print('=' * 22)
    
    cursor.execute("""
        SELECT name, tbl_name, sql 
        FROM sqlite_master 
        WHERE type='index' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY tbl_name, name
    """)
    
    indexes = cursor.fetchall()
    if indexes:
        current_table = None
        for index_name, table_name, sql in indexes:
            if table_name != current_table:
                print(f'\n   {table_name.upper()}:')
                current_table = table_name
            print(f'   - {index_name}')
    else:
        print('   No custom indexes found')
    
    # 5. Check for potential structure issues
    print(f'\n⚠️  STRUCTURE ANALYSIS:')
    print('=' * 22)
    
    # Look for similar table names
    suspicious_patterns = ['backup', 'old', 'temp', 'test', '_new', 'copy', 'duplicate']
    suspicious_tables = []
    
    for table in tables:
        table_lower = table.lower()
        for pattern in suspicious_patterns:
            if pattern in table_lower:
                suspicious_tables.append((table, pattern))
    
    if suspicious_tables:
        print('   📋 Potentially redundant tables:')
        for table, pattern in suspicious_tables:
            print(f'   - {table} (contains "{pattern}")')
    
    # Look for tables with identical structures
    print('\n   🔍 Structure similarity check:')
    from collections import defaultdict
    
    structure_groups = defaultdict(list)
    for table in tables:
        if table == 'sqlite_sequence':
            continue
            
        try:
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            col_signature = tuple(sorted([col[1] + ':' + col[2] for col in columns]))
            structure_groups[col_signature].append(table)
        except:
            continue
    
    similar_found = False
    for signature, table_list in structure_groups.items():
        if len(table_list) > 1:
            similar_found = True
            print(f'   - Identical structures: {", ".join(table_list)}')
    
    if not similar_found:
        print('   ✅ No tables with identical structures found')
    
    conn.close()
    
    print('\n=== STRUCTURE ANALYSIS COMPLETE ===')

if __name__ == "__main__":
    main()
