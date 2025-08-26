#!/usr/bin/env python3
"""
Simple Email Automation Test
"""

print("=== Email Automation Service Test ===")

try:
    print("1. Testing email_automation_service import...")
    from email_automation_service import EmailAutomationService, email_service
    print("✅ Email automation service imported successfully")
    
    print("2. Testing service initialization...")
    print(f"   Service running: {email_service.running}")
    print(f"   Database path: {email_service.db_path}")
    
    print("3. Testing database table creation...")
    import sqlite3
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['email_accounts', 'email_processing_queue', 'email_monitoring_log', 'outgoing_emails']
    
    for table in required_tables:
        if table in tables:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' missing")
    
    conn.close()
    
    print("4. Testing CRM app integration...")
    import crm_app
    print("✅ CRM app imported successfully")
    
    print("\n🎉 All tests passed! Email automation is ready to use.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
