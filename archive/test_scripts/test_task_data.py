#!/usr/bin/env python3
"""
Test script to add processing data to a task
"""

import sqlite3
import json
import sys
from datetime import datetime

def update_task_with_processing_data(task_id):
    """Add processing data to an existing task"""
    
    # Test processing data
    processing_data = {
        'processed': 3,
        'created': 5,
        'skipped': 1,
        'errors': ['Test error 1', 'Test error 2'],
        'created_opportunities': [
            {'id': 1, 'request_number': 'TEST123', 'nsn': '5331011267254'},
            {'id': 2, 'request_number': 'TEST456', 'nsn': '1234567890123'}
        ],
        'created_contacts': [
            {'id': 1, 'name': 'Test Contact 1'},
            {'id': 2, 'name': 'Test Contact 2'}
        ],
        'created_accounts': [
            {'id': 1, 'name': 'Test Company 1'}
        ],
        'created_products': [
            {'id': 1, 'nsn': '5331011267254', 'name': 'Test Product 1'}
        ],
        'updated_records': []
    }
    
    # Create the notes string
    notes_string = f"PROCESSING_DATA:{json.dumps(processing_data)}"
    
    try:
        # Connect to database
        conn = sqlite3.connect('data/crm.db')
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute('SELECT id, subject, notes FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            print(f"Task with ID {task_id} not found")
            return False
        
        print(f"Found task: {task[1]}")
        print(f"Current notes length: {len(task[2]) if task[2] else 0}")
        
        # Update the task with processing data
        cursor.execute('UPDATE tasks SET notes = ? WHERE id = ?', (notes_string, task_id))
        conn.commit()
        
        # Verify the update
        cursor.execute('SELECT notes FROM tasks WHERE id = ?', (task_id,))
        updated_task = cursor.fetchone()
        
        if updated_task and 'PROCESSING_DATA:' in updated_task[0]:
            print(f"SUCCESS: Task {task_id} now has processing data")
            print(f"Notes length: {len(updated_task[0])}")
            
            # Test parsing
            data_str = updated_task[0].split('PROCESSING_DATA:')[1]
            parsed_data = json.loads(data_str)
            print(f"Parsed data keys: {list(parsed_data.keys())}")
            print(f"Created opportunities: {len(parsed_data.get('created_opportunities', []))}")
            return True
        else:
            print("ERROR: Failed to add processing data")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def list_all_tasks():
    """List all tasks in the database"""
    try:
        conn = sqlite3.connect('data/crm.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, subject, notes FROM tasks ORDER BY id')
        tasks = cursor.fetchall()
        
        print(f"Found {len(tasks)} tasks:")
        for task_id, subject, notes in tasks:
            print(f"  Task {task_id}: {subject}")
            if notes and 'PROCESSING_DATA:' in notes:
                print(f"    -> HAS PROCESSING DATA")
            else:
                print(f"    -> No processing data")
        
        conn.close()
        return tasks
        
    except Exception as e:
        print(f"Error listing tasks: {e}")
        return []

if __name__ == "__main__":
    print("=== Task Processing Data Test ===")
    
    # List all tasks first
    print("\n1. Listing all tasks:")
    tasks = list_all_tasks()
    
    if tasks:
        # Update the first task (or task ID 1)
        task_id = 1
        print(f"\n2. Adding processing data to task {task_id}:")
        success = update_task_with_processing_data(task_id)
        
        if success:
            print(f"\n3. Task {task_id} has been updated with test processing data!")
            print("You can now test the web interface.")
        else:
            print(f"\nFailed to update task {task_id}")
    else:
        print("No tasks found in the database")
