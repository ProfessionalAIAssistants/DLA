import sqlite3
from datetime import datetime

def analyze_database():
    print("=== DATABASE ANALYSIS ===")
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Database: data/crm.db")
    print(f"Total Tables: {len(tables)}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_records = 0
    db_structure = {}
    
    for table in tables:
        print(f"TABLE: {table}")
        print("-" * 50)
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        total_records += row_count
        
        table_info = {
            'row_count': row_count,
            'columns': []
        }
        
        print(f"Records: {row_count:,}")
        print("Columns:")
        
        for col in columns:
            col_id, name, data_type, not_null, default_val, is_pk = col
            constraints = []
            if is_pk:
                constraints.append('PRIMARY KEY')
            if not_null:
                constraints.append('NOT NULL')
            if default_val:
                constraints.append(f'DEFAULT {default_val}')
                
            table_info['columns'].append({
                'name': name,
                'type': data_type,
                'constraints': constraints
            })
            
            constraint_str = ' '.join(constraints) if constraints else ''
            print(f"  {name:<25} {data_type:<15} {constraint_str}")
        
        # Check for foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            print("Foreign Keys:")
            for fk in fks:
                print(f"  {fk[3]} -> {fk[2]}.{fk[4]}")
        
        print()
        db_structure[table] = table_info
    
    print(f"TOTAL DATABASE RECORDS: {total_records:,}")
    print()
    
    conn.close()
    return db_structure, total_records

def check_data_integrity():
    print("=== DATA INTEGRITY CHECK ===")
    
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Check for orphaned records
    integrity_checks = [
        ("Contacts without Accounts", 
         "SELECT COUNT(*) FROM contacts WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)"),
        ("Interactions without valid Contact", 
         "SELECT COUNT(*) FROM interactions WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("RFQs without valid Contact", 
         "SELECT COUNT(*) FROM rfqs WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("Opportunities without valid Account", 
         "SELECT COUNT(*) FROM opportunities WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)")
    ]
    
    for check_name, query in integrity_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count > 0:
                issues.append(f"{check_name}: {count} orphaned records")
                print(f"ISSUE: {check_name}: {count} orphaned records")
            else:
                print(f"OK: {check_name}: No issues")
        except Exception as e:
            print(f"WARNING: {check_name}: Could not check - {str(e)}")
    
    # Check for duplicates
    duplicate_checks = [
        ("Duplicate Accounts (by name)", 
         "SELECT name, COUNT(*) as cnt FROM accounts GROUP BY LOWER(name) HAVING cnt > 1"),
        ("Duplicate Contacts (by email)", 
         "SELECT email, COUNT(*) as cnt FROM contacts WHERE email IS NOT NULL GROUP BY LOWER(email) HAVING cnt > 1"),
        ("Duplicate Products (by part_number)", 
         "SELECT part_number, COUNT(*) as cnt FROM products WHERE part_number IS NOT NULL GROUP BY part_number HAVING cnt > 1")
    ]
    
    print("\n=== DUPLICATE CHECK ===")
    
    for check_name, query in duplicate_checks:
        try:
            cursor.execute(query)
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"ISSUE: {check_name}:")
                for dup in duplicates[:5]:  # Show first 5
                    print(f"   '{dup[0]}': {dup[1]} duplicates")
                if len(duplicates) > 5:
                    print(f"   ... and {len(duplicates)-5} more")
                issues.append(f"{check_name}: {len(duplicates)} sets of duplicates")
            else:
                print(f"OK: {check_name}: No duplicates found")
        except Exception as e:
            print(f"WARNING: {check_name}: Could not check - {str(e)}")
    
    conn.close()
    return issues

if __name__ == "__main__":
    try:
        structure, total_records = analyze_database()
        issues = check_data_integrity()
        
        # Generate summary
        print("\n=== SUMMARY ===")
        print(f"Total tables: {len(structure)}")
        print(f"Total records: {total_records:,}")
        if issues:
            print(f"Issues found: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("No data integrity issues found")
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
