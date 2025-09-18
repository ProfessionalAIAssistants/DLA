#!/usr/bin/env python3
"""
Consolidated Business Data Cleaner
Combines functionality from clear_business_data.py and clear_business_data_auto.py
Removes all tasks, opportunities, projects, interactions, and quotes (RFQs) 
from the CRM database while preserving accounts, contacts, and products.
"""

import sqlite3
import sys
import argparse
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

def clear_business_data(auto_confirm=False, db_path='data/crm.db'):
    """Clear all business data while preserving core entities"""
    
    print("=" * 60)
    print("CLEARING BUSINESS DATA FROM CRM DATABASE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get before counts
        print("📊 BEFORE CLEARING:")
        print("-" * 30)
        before_counts = get_record_counts(cursor)
        
        business_tables = ['tasks', 'opportunities', 'projects', 'interactions', 'rfqs', 'quotes']
        preserved_tables = ['accounts', 'contacts', 'products']
        
        for table in business_tables:
            if before_counts.get(table, 0) > 0:
                print(f"• {table}: {before_counts[table]:,} records")
        
        print("\\n🔒 WILL BE PRESERVED:")
        print("-" * 30)
        for table in preserved_tables:
            if before_counts.get(table, 0) > 0:
                print(f"• {table}: {before_counts[table]:,} records")
        
        # Confirm deletion unless auto mode
        if not auto_confirm:
            print("\\n⚠️  WARNING: This will permanently delete all business data!")
            print("   (tasks, opportunities, projects, interactions, quotes)")
            print("   Accounts, contacts, and products will be preserved.")
            
            confirm = input("\\n🤔 Are you sure you want to continue? (yes/no): ").lower().strip()
            if confirm != 'yes':
                print("❌ Operation cancelled by user")
                return False
        
        print("\\n🗑️  CLEARING BUSINESS DATA...")
        print("-" * 40)
        
        # Clear tables in order (handling foreign key constraints)
        clear_order = [
            'project_tasks',
            'project_opportunities', 
            'project_products',
            'project_contacts',
            'tasks',
            'quotes',
            'rfqs',
            'interactions',
            'opportunities',
            'projects'
        ]
        
        cleared_tables = 0
        total_cleared = 0
        
        for table in clear_order:
            try:
                # Check if table exists and has data
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"✅ Cleared {table}: {count:,} records deleted")
                    total_cleared += count
                    cleared_tables += 1
                else:
                    print(f"⚪ {table}: Already empty")
                    
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    print(f"⚪ {table}: Table doesn't exist")
                else:
                    print(f"❌ Error clearing {table}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Get after counts
        print("\\n📊 AFTER CLEARING:")
        print("-" * 30)
        after_counts = get_record_counts(cursor)
        
        for table in business_tables:
            count = after_counts.get(table, 0)
            if count == 0:
                print(f"✅ {table}: {count} records")
            else:
                print(f"⚠️  {table}: {count} records (some remain)")
        
        print("\\n🔒 PRESERVED DATA:")
        print("-" * 30)
        for table in preserved_tables:
            before = before_counts.get(table, 0)
            after = after_counts.get(table, 0)
            if before == after:
                print(f"✅ {table}: {after:,} records (unchanged)")
            else:
                print(f"⚠️  {table}: {before:,} → {after:,} records (changed unexpectedly)")
        
        print("\\n" + "=" * 60)
        print("✅ BUSINESS DATA CLEARING COMPLETED")
        print(f"📈 Summary: {cleared_tables} tables cleared, {total_cleared:,} total records deleted")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during business data clearing: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Clear business data from CRM database')
    parser.add_argument('--auto', action='store_true', help='Auto-confirm deletion without prompting')
    parser.add_argument('--db', type=str, default='data/crm.db', help='Database file path (default: data/crm.db)')
    parser.add_argument('--preview', action='store_true', help='Preview what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if args.preview:
        # Preview mode - show what would be deleted
        print("🔍 PREVIEW MODE - No data will be deleted")
        print("=" * 60)
        
        try:
            conn = sqlite3.connect(args.db)
            cursor = conn.cursor()
            
            counts = get_record_counts(cursor)
            business_tables = ['tasks', 'opportunities', 'projects', 'interactions', 'rfqs', 'quotes']
            preserved_tables = ['accounts', 'contacts', 'products']
            
            print("📊 WOULD BE DELETED:")
            print("-" * 30)
            total_to_delete = 0
            for table in business_tables:
                count = counts.get(table, 0)
                if count > 0:
                    print(f"• {table}: {count:,} records")
                    total_to_delete += count
            
            print("\\n🔒 WOULD BE PRESERVED:")
            print("-" * 30)
            for table in preserved_tables:
                count = counts.get(table, 0)
                if count > 0:
                    print(f"• {table}: {count:,} records")
            
            print(f"\\n📈 Total records to delete: {total_to_delete:,}")
            print("\\n⚠️  Run without --preview to actually clear the data")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error during preview: {e}")
    else:
        # Actual clearing
        success = clear_business_data(args.auto, args.db)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()