#!/usr/bin/env python3
"""Test the create_task fix"""

import sys
import os
import json
import datetime

# Add path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))

def main():
    try:
        from crm_data import crm_data
        print("✓ Import successful")
        
        # Create processing data
        processing_data = {
            'files_processed': ['test1.pdf'],
            'opportunities_created': 1,
            'contacts_created': 0,
            'accounts_created': 1,
            'status': 'completed',
            'processing_time': '2025-01-15 10:30:00'
        }
        
        notes = 'PROCESSING_DATA:' + json.dumps(processing_data)
        print(f"✓ Notes created: {len(notes)} chars")
        
        # Test task creation
        task_data = {
            'subject': 'Test Processing Task - Fixed Method',
            'description': 'Testing that notes field is now properly stored',
            'status': 'completed',
            'priority': 'medium',
            'notes': notes,
            'type': 'processing',
            'assigned_to': 'System',
            'created_at': datetime.datetime.now().isoformat()
        }
        
        print(f"✓ Task data prepared with keys: {list(task_data.keys())}")
        
        result = crm_data.create_task(**task_data)
        print(f"✓ Task creation result: {result}")
        
        if result and 'task_id' in result:
            task_id = result['task_id']
            print(f"✓ Created task ID: {task_id}")
            
            # Retrieve and verify
            retrieved = crm_data.get_task(task_id)
            if retrieved:
                stored_notes = str(retrieved.get('notes', ''))
                print(f"✓ Retrieved task successfully")
                print(f"✓ Stored notes length: {len(stored_notes)}")
                print(f"✓ Stored notes preview: {stored_notes[:100]}...")
                
                if stored_notes.startswith('PROCESSING_DATA:'):
                    print("✅ SUCCESS: Processing data was stored correctly!")
                    return True
                else:
                    print("❌ FAIL: Processing data not found in notes")
                    return False
            else:
                print("❌ Could not retrieve created task")
                return False
        else:
            print("❌ Task creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*50}")
    print(f"TEST RESULT: {'PASSED' if success else 'FAILED'}")
    print(f"{'='*50}")
