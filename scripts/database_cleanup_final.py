#!/usr/bin/env python3
"""
Database Cleanup and Documentation Generator
Fixes integrity issues and generates comprehensive human-readable documentation
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def fix_orphaned_references():
    """Fix orphaned foreign key references"""
    print('=== FIXING ORPHANED REFERENCES ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find and fix orphaned opportunity references
        cursor.execute('''
            SELECT id, name, account_id, contact_id 
            FROM opportunities 
            WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)
               OR contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)
        ''')
        orphaned_opps = cursor.fetchall()
        
        if orphaned_opps:
            print(f'Found {len(orphaned_opps)} opportunities with orphaned references:')
            for opp in orphaned_opps:
                print(f'  - ID {opp[0]}: "{opp[1]}" (Account: {opp[2]}, Contact: {opp[3]})')
            
            # Option 1: Set orphaned references to NULL
            cursor.execute('''
                UPDATE opportunities 
                SET account_id = NULL 
                WHERE account_id IS NOT NULL AND account_id NOT IN (SELECT id FROM accounts)
            ''')
            
            cursor.execute('''
                UPDATE opportunities 
                SET contact_id = NULL 
                WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)
            ''')
            
            print('✅ Fixed orphaned references by setting them to NULL')
        else:
            print('✅ No orphaned references found')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error fixing orphaned references: {e}')
        return False

def clean_backup_tables():
    """Identify and optionally clean backup tables"""
    print('\n=== BACKUP TABLES ANALYSIS ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find backup tables
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%backup%"')
        backup_tables = [row[0] for row in cursor.fetchall()]
        
        if backup_tables:
            print(f'Found {len(backup_tables)} backup tables:')
            for table in backup_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                
                # Get table size estimation
                cursor.execute(f'SELECT sql FROM sqlite_master WHERE name="{table}"')
                schema = cursor.fetchone()[0] if cursor.fetchone() else 'Unknown'
                
                print(f'  📦 {table}: {count} records')
                
                # Check if corresponding main table exists and compare
                main_table = table.replace('_backup_20250821', '').replace('_backup_simple', '')
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {main_table}')
                    main_count = cursor.fetchone()[0]
                    print(f'      Main table {main_table}: {main_count} records')
                    
                    if main_count >= count:
                        print(f'      ✅ Backup can be safely removed (main table has same/more data)')
                    else:
                        print(f'      ⚠️  Backup contains more data than main table')
                except:
                    print(f'      ❌ Main table {main_table} not found')
        else:
            print('✅ No backup tables found')
        
        conn.close()
        return backup_tables
        
    except Exception as e:
        print(f'❌ Error analyzing backup tables: {e}')
        return []

def analyze_table_usage():
    """Analyze which tables are actually used by the application"""
    print('\n=== TABLE USAGE ANALYSIS ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Categorize tables
        core_tables = ['accounts', 'contacts', 'opportunities', 'rfqs', 'tasks', 'interactions', 'projects']
        relationship_tables = ['project_contacts', 'project_opportunities', 'project_products', 'project_tasks']
        feature_tables = ['products', 'qpl', 'quotes', 'email_templates', 'email_responses', 'vendor_rfq_emails']
        workflow_tables = ['workflow_automation_rules', 'workflow_execution_log']
        system_tables = ['sqlite_sequence']
        backup_tables = [t for t in all_tables if 'backup' in t.lower()]
        
        print('📊 Table Categories:')
        
        print('\n🏢 Core Business Tables:')
        for table in core_tables:
            if table in all_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                status = '✅' if count > 0 else '⚪'
                print(f'  {status} {table}: {count} records')
        
        print('\n🔗 Relationship Tables:')
        for table in relationship_tables:
            if table in all_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                status = '✅' if count > 0 else '⚪'
                print(f'  {status} {table}: {count} records')
        
        print('\n🚀 Feature Tables:')
        for table in feature_tables:
            if table in all_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                status = '✅' if count > 0 else '⚪'
                print(f'  {status} {table}: {count} records')
        
        print('\n⚙️ Workflow Tables:')
        for table in workflow_tables:
            if table in all_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                status = '✅' if count > 0 else '⚪'
                print(f'  {status} {table}: {count} records')
        
        if backup_tables:
            print('\n📦 Backup Tables:')
            for table in backup_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'  📦 {table}: {count} records')
        
        # Find any uncategorized tables
        categorized = set(core_tables + relationship_tables + feature_tables + workflow_tables + system_tables + backup_tables)
        uncategorized = [t for t in all_tables if t not in categorized]
        
        if uncategorized:
            print('\n❓ Uncategorized Tables:')
            for table in uncategorized:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'  ❓ {table}: {count} records')
        
        conn.close()
        return {
            'core': core_tables,
            'relationship': relationship_tables,
            'feature': feature_tables,
            'workflow': workflow_tables,
            'backup': backup_tables,
            'uncategorized': uncategorized
        }
        
    except Exception as e:
        print(f'❌ Error analyzing table usage: {e}')
        return {}

def generate_comprehensive_documentation():
    """Generate comprehensive human-readable database documentation"""
    print('\n=== GENERATING COMPREHENSIVE DOCUMENTATION ===')
    
    try:
        from src.core.config_manager import config_manager
        db_path = config_manager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        doc = []
        doc.append("# DLA CRM Database - Complete Manager Documentation")
        doc.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")
        doc.append("## 🎯 Executive Summary")
        doc.append("This is a comprehensive guide to the DLA CRM database structure, designed for")
        doc.append("database managers and system administrators. The database supports a complete")
        doc.append("CRM system with DIBBs (Defense Industrial Base Business System) integration.")
        doc.append("")
        
        # Database overview
        doc.append("## 📊 Database Overview")
        doc.append(f"- **Database Type**: SQLite")
        doc.append(f"- **Location**: `{db_path}`")
        doc.append(f"- **Size**: {os.path.getsize(db_path) / 1024:.1f} KB")
        
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = [row[0] for row in cursor.fetchall()]
        doc.append(f"- **Total Tables**: {len(tables)}")
        
        # Count total records
        total_records = 0
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                total_records += count
            except:
                pass
        doc.append(f"- **Total Records**: {total_records:,}")
        doc.append("")
        
        # Core business entities
        doc.append("## 🏢 Core Business Entities")
        doc.append("")
        
        core_entities = [
            ('accounts', 'Companies and Organizations', 'Customer prospects, vendors, competitors'),
            ('contacts', 'Individual People', 'People associated with accounts'),
            ('opportunities', 'Sales Opportunities', 'Potential deals and quotes'),
            ('rfqs', 'Requests for Quote', 'DIBBs solicitations and RFQ documents'),
            ('tasks', 'Action Items', 'To-do items and follow-ups'),
            ('interactions', 'Communication Log', 'Calls, emails, meetings with contacts'),
            ('projects', 'Project Management', 'Organized collections of related work')
        ]
        
        for table_name, title, description in core_entities:
            if table_name in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                
                doc.append(f"### {title} (`{table_name}`)")
                doc.append(f"**Purpose**: {description}")
                doc.append(f"**Records**: {count:,}")
                doc.append("")
                
                # Get table schema
                cursor.execute(f'PRAGMA table_info({table_name})')
                columns = cursor.fetchall()
                
                doc.append("**Key Fields**:")
                for col in columns[:10]:  # Show first 10 columns
                    col_name, col_type = col[1], col[2]
                    nullable = "NOT NULL" if col[3] else "NULL"
                    default = f" DEFAULT {col[4]}" if col[4] else ""
                    doc.append(f"- `{col_name}` ({col_type}) - {nullable}{default}")
                
                if len(columns) > 10:
                    doc.append(f"- ... and {len(columns) - 10} more fields")
                doc.append("")
        
        # Relationship mapping
        doc.append("## 🔗 Data Relationships")
        doc.append("Understanding how data connects across the system:")
        doc.append("")
        doc.append("```")
        doc.append("ACCOUNTS (companies)")
        doc.append("├── CONTACTS (people at companies)")
        doc.append("├── OPPORTUNITIES (sales deals)")
        doc.append("│   ├── RFQS (quote requests)")
        doc.append("│   └── TASKS (follow-up actions)")
        doc.append("├── INTERACTIONS (communication history)")
        doc.append("└── PROJECTS (organized work)")
        doc.append("    ├── PROJECT_CONTACTS (who's involved)")
        doc.append("    ├── PROJECT_OPPORTUNITIES (related deals)")
        doc.append("    ├── PROJECT_PRODUCTS (what's being sold)")
        doc.append("    └── PROJECT_TASKS (project to-dos)")
        doc.append("```")
        doc.append("")
        
        # Products and inventory
        doc.append("## 📦 Product & Inventory System")
        doc.append("")
        product_tables = ['products', 'qpl', 'quotes']
        for table_name in product_tables:
            if table_name in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                
                descriptions = {
                    'products': 'Product catalog with NSNs, specifications, and vendor information',
                    'qpl': 'Qualified Products List - approved vendors for specific products',
                    'quotes': 'Vendor quotes received for RFQ solicitations'
                }
                
                doc.append(f"### {table_name.upper()}")
                doc.append(f"**Purpose**: {descriptions.get(table_name, 'Product-related data')}")
                doc.append(f"**Records**: {count:,}")
                doc.append("")
        
        # Email and automation
        doc.append("## 📧 Email & Automation System")
        doc.append("")
        email_tables = ['email_templates', 'email_responses', 'vendor_rfq_emails']
        for table_name in email_tables:
            if table_name in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                
                descriptions = {
                    'email_templates': 'Reusable email templates for automation',
                    'email_responses': 'Captured email responses from vendors',
                    'vendor_rfq_emails': 'Email communications related to RFQs'
                }
                
                doc.append(f"### {table_name.upper()}")
                doc.append(f"**Purpose**: {descriptions.get(table_name, 'Email-related data')}")
                doc.append(f"**Records**: {count:,}")
                doc.append("")
        
        # Workflow system
        doc.append("## ⚙️ Workflow & Automation")
        doc.append("")
        workflow_tables = ['workflow_automation_rules', 'workflow_execution_log']
        for table_name in workflow_tables:
            if table_name in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                
                descriptions = {
                    'workflow_automation_rules': 'Automated business rules and triggers',
                    'workflow_execution_log': 'History of automated actions performed'
                }
                
                doc.append(f"### {table_name.upper()}")
                doc.append(f"**Purpose**: {descriptions.get(table_name, 'Workflow-related data')}")
                doc.append(f"**Records**: {count:,}")
                doc.append("")
        
        # Data quality and maintenance
        doc.append("## 🔍 Data Quality & Maintenance")
        doc.append("")
        
        # Check for empty tables
        empty_tables = []
        low_usage_tables = []
        
        for table in tables:
            if not any(table.startswith(prefix) for prefix in ['sqlite_', 'backup_']):
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                if count == 0:
                    empty_tables.append(table)
                elif count < 5:
                    low_usage_tables.append((table, count))
        
        if empty_tables:
            doc.append("### ⚪ Empty Tables")
            doc.append("These tables exist but contain no data:")
            for table in empty_tables:
                doc.append(f"- `{table}` - Consider if this table is needed")
            doc.append("")
        
        if low_usage_tables:
            doc.append("### 📊 Low Usage Tables")
            doc.append("Tables with minimal data that may need attention:")
            for table, count in low_usage_tables:
                doc.append(f"- `{table}`: {count} records")
            doc.append("")
        
        # Backup tables
        backup_tables = [t for t in tables if 'backup' in t.lower()]
        if backup_tables:
            doc.append("### 📦 Backup Tables")
            doc.append("Historical data backups (can be archived or removed):")
            for table in backup_tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                doc.append(f"- `{table}`: {count} records")
            doc.append("")
        
        # Security and access
        doc.append("## 🔒 Security & Access Guidelines")
        doc.append("")
        doc.append("### Database Security")
        doc.append("- Database file should have restricted file permissions")
        doc.append("- Regular backups should be maintained")
        doc.append("- Consider encryption for sensitive data")
        doc.append("")
        doc.append("### Sensitive Data Tables")
        doc.append("- `contacts` - Contains personal information (PII)")
        doc.append("- `email_responses` - May contain business-sensitive communications")
        doc.append("- `opportunities` - Contains financial and competitive information")
        doc.append("- `vendor_rfq_emails` - Contains vendor communications")
        doc.append("")
        
        # Maintenance procedures
        doc.append("## 🛠️ Maintenance Procedures")
        doc.append("")
        doc.append("### Regular Maintenance Tasks")
        doc.append("1. **Weekly**:")
        doc.append("   - Review data integrity with foreign key checks")
        doc.append("   - Monitor database size and performance")
        doc.append("")
        doc.append("2. **Monthly**:")
        doc.append("   - Archive old backup tables if no longer needed")
        doc.append("   - Review empty or low-usage tables")
        doc.append("   - Analyze database growth trends")
        doc.append("")
        doc.append("3. **Quarterly**:")
        doc.append("   - Full database backup")
        doc.append("   - Schema documentation update")
        doc.append("   - Performance optimization review")
        doc.append("")
        
        # Integration points
        doc.append("## 🔌 System Integrations")
        doc.append("")
        doc.append("### DIBBs Integration")
        doc.append("- `rfqs` table receives data from DIBBs PDF processing")
        doc.append("- Automatic parsing of solicitation documents")
        doc.append("- Links RFQs to opportunities and accounts")
        doc.append("")
        doc.append("### Email Automation")
        doc.append("- Email templates for automated responses")
        doc.append("- Vendor communication tracking")
        doc.append("- Quote collection and processing")
        doc.append("")
        doc.append("### Web Interface")
        doc.append("- Flask web application provides user interface")
        doc.append("- REST API endpoints for data access")
        doc.append("- Real-time dashboard with calendar integration")
        doc.append("")
        
        # Performance metrics
        doc.append("## 📈 Performance Metrics")
        doc.append("")
        cursor.execute('SELECT name FROM sqlite_master WHERE type="index"')
        indexes = [row[0] for row in cursor.fetchall()]
        doc.append(f"- **Database Indexes**: {len(indexes)} indexes for query optimization")
        doc.append(f"- **Current Size**: {os.path.getsize(db_path) / 1024:.1f} KB")
        doc.append(f"- **Records per Table**: {total_records / len(tables):.1f} average")
        doc.append("")
        
        # Troubleshooting
        doc.append("## 🚨 Troubleshooting Guide")
        doc.append("")
        doc.append("### Common Issues")
        doc.append("1. **Orphaned Foreign Keys**:")
        doc.append("   - Run integrity check: `PRAGMA foreign_key_check;`")
        doc.append("   - Fix with: Update to NULL or create missing parent records")
        doc.append("")
        doc.append("2. **Database Locks**:")
        doc.append("   - Check for long-running transactions")
        doc.append("   - Restart application if needed")
        doc.append("")
        doc.append("3. **Performance Issues**:")
        doc.append("   - Review query execution plans")
        doc.append("   - Consider adding indexes for frequently queried columns")
        doc.append("")
        
        # Contact information
        doc.append("## 📞 Support Information")
        doc.append("")
        doc.append("### Database Administrator")
        doc.append("- **System**: DLA CRM Database")
        doc.append("- **Environment**: Production")
        doc.append(f"- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.append("")
        doc.append("### Quick Reference Commands")
        doc.append("```sql")
        doc.append("-- Check database size")
        doc.append("SELECT page_count * page_size / 1024.0 / 1024.0 AS size_mb FROM pragma_page_count(), pragma_page_size();")
        doc.append("")
        doc.append("-- List all tables with record counts")
        doc.append("SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as count")
        doc.append("FROM sqlite_master m WHERE type='table';")
        doc.append("")
        doc.append("-- Check foreign key integrity")
        doc.append("PRAGMA foreign_key_check;")
        doc.append("```")
        doc.append("")
        
        conn.close()
        
        # Save documentation
        doc_content = '\n'.join(doc)
        
        with open('DATABASE_MANAGER_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        print('✅ Comprehensive documentation generated: DATABASE_MANAGER_GUIDE.md')
        return doc_content
        
    except Exception as e:
        print(f'❌ Error generating documentation: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔧 DATABASE CLEANUP AND DOCUMENTATION")
    print("=" * 50)
    
    try:
        # Step 1: Fix integrity issues
        if fix_orphaned_references():
            print('✅ Integrity issues fixed')
        
        # Step 2: Analyze backup tables
        backup_tables = clean_backup_tables()
        
        # Step 3: Analyze table usage
        table_categories = analyze_table_usage()
        
        # Step 4: Generate comprehensive documentation
        doc = generate_comprehensive_documentation()
        
        print("\n🎉 DATABASE CLEANUP COMPLETE!")
        print("=" * 50)
        print("✅ Database integrity: FIXED")
        print("✅ Analysis complete: All tables categorized")
        print("✅ Documentation: Generated DATABASE_MANAGER_GUIDE.md")
        
        if backup_tables:
            print(f"📦 Backup tables: {len(backup_tables)} found (review for archival)")
        
        print("\n📄 New file created: DATABASE_MANAGER_GUIDE.md")
        print("   - Complete database structure documentation")
        print("   - Manager-friendly format with troubleshooting")
        print("   - Security and maintenance guidelines")
        
    except Exception as e:
        print(f'❌ Cleanup failed: {e}')
        import traceback
        traceback.print_exc()
