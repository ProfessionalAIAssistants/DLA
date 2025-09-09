#!/usr/bin/env python3
"""
Test the fixed create_task method to verify processing data storage works
"""

import sys
import os
import json
import datetime

# Add the src/core directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))

try:
    from crm_data import create_task, get_task
    print("Successfully imported crm_data functions")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_task_creation_with_processing_data():
    """Test creating a task with processing data in notes"""
    
    # Create test processing data
    processing_data = {
        'files_processed': ['test1.pdf', 'test2.pdf'],
        'opportunities_created': 3,
        'contacts_created': 2,
        'accounts_created': 1,
        'processing_time': '2025-01-15 10:30:00',
        'status': 'completed'
    }
    
    # Create notes with processing data (as JSON)
    notes = 'PROCESSING_DATA:' + json.dumps(processing_data)
    print(f"Notes to store: {notes}")
    print(f"Notes length: {len(notes)}")
    
    # Test the fixed create_task method
    try:
        task_data = {
            'subject': 'PDF Processing Task - Test Fixed Method',
            'description': 'Test task to verify processing data display after fix',
            'status': 'completed',
            'priority': 'medium',
            'created_at': datetime.datetime.now().isoformat(),
            'notes': notes,
            'assigned_to': 'System',
            'type': 'processing'
        }
        
        print(f"Task data keys: {list(task_data.keys())}")
        
        # Create the task
        result = create_task(task_data)
        print(f"Task creation result: {result}")
        
        if result and 'task_id' in result:
            task_id = result['task_id']
            print(f"Task created with ID: {task_id}")
            
            # Try to retrieve the task to verify notes were stored
            try:
                retrieved_task = get_task(task_id)
                if retrieved_task:
                    print(f"Retrieved task: {retrieved_task}")
                    print(f"Retrieved notes: {retrieved_task.get('notes', 'No notes found')}")
                    print(f"Retrieved notes length: {len(str(retrieved_task.get('notes', '')))}")
                else:
                    print("Failed to retrieve created task")
            except Exception as e:
                print(f"Error retrieving task: {e}")
        else:
            print("Task creation failed or returned unexpected result")
            
    except Exception as e:
        print(f"Error creating task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing fixed task creation with processing data...")
    test_task_creation_with_processing_data()
