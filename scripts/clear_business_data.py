#!/usr/bin/env python3
"""
Clear Business Data Script
==========================

Removes all tasks, opportunities, projects, interactions, and quotes (RFQs) 
from the CRM database while preserving accounts, contacts, and products.

This script will:
1. Clear all tasks
2. Clear all opportunities 
3. Clear all projects and project relationships
4. Clear all interactions
5. Clear all RFQs/quotes
6. Preserve accounts, contacts, and products
7. Show before/after counts
"""

import sqlite3
import sys
from datetime import datetime

def get_record_counts(cursor):
    """Get current record counts for all tables"""
    tables = [
        'tasks', 'opportunities', 'projects', 'interactions', 'rfqs',
        'project_contacts', 'project_opportunities', 'project_products', 'project_tasks',
        'quotes', 'accounts', 'contacts', 'products'
    ]
    
    counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0  # Table doesn't exist
    
    return counts

def clear_business_data():
    """Clear all business data while preserving core entities"""
    
    print("=" * 60)
    print("CLEARING BUSINESS DATA FROM CRM DATABASE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        # Get initial counts
        print("📊 BEFORE CLEARING:")
        before_counts = get_record_counts(cursor)
        for table, count in before_counts.items():
            if count > 0:
                print(f"  {table}: {count} records")
        
        print("\n🗑️ CLEARING DATA...")
        
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Clear business data tables in order (respecting dependencies)
        tables_to_clear = [
            'project_tasks',        # Project relationships first
            'project_opportunities',
            'project_products', 
            'project_contacts',
            'interactions',         # Communications
            'quotes',              # Quote responses
            'tasks',               # Tasks
            'opportunities',       # Opportunities
            'projects',            # Projects
            'rfqs'                 # RFQs/Quotes
        ]
        
        cleared_counts = {}
        for table in tables_to_clear:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                
                if count_before > 0:
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"  ✅ Cleared {table}: {count_before} records removed")
                    cleared_counts[table] = count_before
                else:
                    print(f"  ⚪ {table}: already empty")
                    cleared_counts[table] = 0
                    
            except sqlite3.OperationalError as e:
                print(f"  ⚠️ {table}: table doesn't exist ({e})")
                cleared_counts[table] = 0
        
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit changes
        conn.commit()
        
        print("\n📊 AFTER CLEARING:")
        after_counts = get_record_counts(cursor)
        preserved_tables = ['accounts', 'contacts', 'products']
        
        # Show preserved data
        print("  PRESERVED DATA:")
        for table in preserved_tables:
            count = after_counts.get(table, 0)
            print(f"    {table}: {count} records (preserved)")
        
        # Show cleared data
        print("  CLEARED DATA:")
        for table in tables_to_clear:
            count = after_counts.get(table, 0)
            cleared = cleared_counts.get(table, 0)
            if cleared > 0:
                print(f"    {table}: {cleared} records removed ✅")
            else:
                print(f"    {table}: was already empty ⚪")
        
        # Calculate total cleared
        total_cleared = sum(cleared_counts.values())
        print(f"\n🎯 SUMMARY:")
        print(f"  Total records cleared: {total_cleared}")
        print(f"  Accounts preserved: {after_counts.get('accounts', 0)}")
        print(f"  Contacts preserved: {after_counts.get('contacts', 0)}")
        print(f"  Products preserved: {after_counts.get('products', 0)}")
        
        # Vacuum database to reclaim space
        print(f"\n🧹 OPTIMIZING DATABASE...")
        cursor.execute("VACUUM")
        print("  Database optimized ✅")
        
        conn.close()
        
        print(f"\n✅ OPERATION COMPLETED SUCCESSFULLY")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Database may be in an inconsistent state.")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def confirm_operation():
    """Get user confirmation before proceeding"""
    print("⚠️  WARNING: This will permanently delete the following data:")
    print("   • All tasks")
    print("   • All opportunities") 
    print("   • All projects and project relationships")
    print("   • All interactions")
    print("   • All RFQs/quotes")
    print()
    print("✅ The following data will be preserved:")
    print("   • All accounts (companies)")
    print("   • All contacts (people)")
    print("   • All products")
    print()
    
    response = input("Are you sure you want to proceed? (type 'YES' to confirm): ")
    return response.strip().upper() == 'YES'

if __name__ == "__main__":
    if confirm_operation():
        success = clear_business_data()
        sys.exit(0 if success else 1)
    else:
        print("Operation cancelled.")
        sys.exit(0)
