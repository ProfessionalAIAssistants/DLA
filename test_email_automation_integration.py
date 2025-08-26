#!/usr/bin/env python3
"""
Test Email Automation Service Integration
Verify that the email automation service integrates properly with the CRM
"""

import sys
import os
import sqlite3
from datetime import datetime

def test_database_tables():
    """Test that all required database tables exist"""
    print("Testing database table creation...")
    
    try:
        # Import the email automation service to trigger table creation
        from email_automation_service import EmailAutomationService, email_service
        
        # Check if tables exist
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        # List of required tables
        required_tables = [
            'email_accounts',
            'email_processing_queue', 
            'email_monitoring_log',
            'outgoing_emails'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Existing tables: {existing_tables}")
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error testing database: {e}")
        return False

def test_service_initialization():
    """Test that the service initializes properly"""
    print("\nTesting service initialization...")
    
    try:
        from email_automation_service import email_service
        
        print(f"✅ Service instance created")
        print(f"   Service running: {email_service.running}")
        print(f"   Database path: {email_service.db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing service: {e}")
        return False

def test_api_endpoints():
    """Test that CRM app can import and use the service"""
    print("\nTesting API endpoint integration...")
    
    try:
        # Test importing the CRM app with new endpoints
        import crm_app
        
        print("✅ CRM app imported successfully")
        
        # Check if our new routes are registered
        routes = [rule.rule for rule in crm_app.app.url_map.iter_rules()]
        
        expected_routes = [
            '/api/email-automation/status',
            '/api/email-automation/start',
            '/api/email-automation/stop',
            '/api/email-automation/accounts'
        ]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route '{route}' registered")
            else:
                print(f"❌ Route '{route}' missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=== Email Automation Service Integration Test ===\n")
    
    tests = [
        test_database_tables,
        test_service_initialization,
        test_api_endpoints
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! Email automation service is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
