#!/usr/bin/env python3
"""Debug task creation with processing data"""

import sqlite3
import json
from datetime import datetime

def create_test_task():
    """Create a task with processing data"""
    
    # Sample processing data
    processing_data = {
        'processed': 3,
        'created': 5,
        'skipped': 1,
        'errors': ['Sample error 1', 'Sample error 2'],
        'created_opportunities': [
            {'id': 101, 'request_number': 'SPE4A123T3230', 'nsn': '5331011267254'},
            {'id': 102, 'request_number': 'SPE4A124T2840', 'nsn': '1234567890123'},
            {'id': 103, 'request_number': 'SPE7M424T236A', 'nsn': '9876543210987'}
        ],
        'created_contacts': [
            {'id': 201, 'name': 'John Smith', 'email': 'john@dla.mil'},
            {'id': 202, 'name': 'Jane Doe', 'email': 'jane@contractor.com'}
        ],
        'created_accounts': [
            {'id': 301, 'name': 'Defense Logistics Agency'},
            {'id': 302, 'name': 'ABC Defense Contractor'}
        ],
        'created_products': [
            {'id': 401, 'nsn': '5331011267254', 'name': 'O-Ring Seal'},
            {'id': 402, 'nsn': '1234567890123', 'name': 'Gasket Assembly'}
        ],
        'updated_records': [
            {'type': 'contact', 'id': 201, 'field': 'phone', 'old_value': '', 'new_value': '555-1234'},
            {'type': 'account', 'id': 301, 'field': 'website', 'old_value': '', 'new_value': 'https://www.dla.mil'}
        ]
    }
    
    # Create task data
    today = datetime.now().strftime('%Y-%m-%d')
    subject = f"Evaluate Upload {datetime.now().strftime('%m/%d/%Y')}"
    description = f"Review PDF processing results for {datetime.now().strftime('%m/%d/%Y')}\n\nPlease review all newly created opportunities and verify data accuracy.\n\nDouble-click any opportunity in the table below to view full details."
    notes = f"PROCESSING_DATA:{json.dumps(processing_data)}"
    
    # Connect to database
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    # Insert the task
    cursor.execute("""
        INSERT INTO tasks (subject, description, status, priority, type, due_date, work_date, assigned_to, notes, created_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (subject, description, 'Not Started', 'High', 'Follow-up', today, today, 'System Generated', notes, datetime.now().isoformat()))
    
    task_id = cursor.lastrowid
    conn.commit()
    
    # Verify the task was created
    cursor.execute("SELECT id, subject, notes FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    
    if task:
        print(f"Created task ID: {task[0]}")
        print(f"Subject: {task[1]}")
        print(f"Notes length: {len(task[2])}")
        if 'PROCESSING_DATA:' in task[2]:
            print("✓ Task has processing data!")
            # Test parsing
            try:
                data_str = task[2].split('PROCESSING_DATA:')[1]
                parsed = json.loads(data_str)
                print(f"✓ Data parses successfully with {len(parsed)} keys")
                print(f"✓ Created opportunities: {len(parsed.get('created_opportunities', []))}")
            except Exception as e:
                print(f"✗ Error parsing data: {e}")
        else:
            print("✗ Task does not have processing data")
    else:
        print("✗ Failed to create task")
    
    conn.close()
    return task_id if task else None

if __name__ == "__main__":
    print("Creating test task with processing data...")
    task_id = create_test_task()
    if task_id:
        print(f"\nSuccess! Test task created with ID: {task_id}")
        print(f"Visit: http://127.0.0.1:5000/tasks/{task_id}")
    else:
        print("\nFailed to create test task")
