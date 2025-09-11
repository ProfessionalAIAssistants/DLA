#!/usr/bin/env python3
"""
Directly insert a task with processing data into the database to test the template display
"""

import sqlite3
import json
import datetime

def create_test_task_with_processing_data():
    """Create a task directly in the database with processing data"""
    
    # Processing data to store
    processing_data = {
        'files_processed': ['TEST_FILE_1.PDF', 'TEST_FILE_2.PDF'],
        'opportunities_created': 2,
        'contacts_created': 1,
        'accounts_created': 1,
        'processing_time': '2025-01-15 10:30:00',
        'status': 'completed',
        'summary': 'Test processing run with sample data'
    }
    
    # Create notes with processing data
    notes = 'PROCESSING_DATA:' + json.dumps(processing_data)
    
    # Connect to database
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    
    try:
        # Insert task with processing data
        task_data = {
            'subject': 'Test Task - Processing Report Display',
            'description': 'This task was created to test the processing report template sections',
            'status': 'completed',
            'priority': 'high',
            'notes': notes,
            'assigned_to': 'System',
            'type': 'processing',
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        # Insert the task
        insert_sql = """
        INSERT INTO tasks (subject, description, status, priority, assigned_to, type, created_date, modified_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_sql, (
            task_data['subject'],
            task_data['description'], 
            task_data['status'],
            task_data['priority'],
            task_data['assigned_to'],
            task_data['type'],
            task_data['created_at'],
            task_data['updated_at']
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Successfully created task ID: {task_id}")
        print(f"📝 Notes length: {len(notes)} characters")
        print(f"🔍 Notes preview: {notes[:100]}...")
        
        # Verify the task was created
        cursor.execute("SELECT id, title, notes FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        
        if result:
            stored_notes = result[2] or ''
            print(f"✅ Task verified in database")
            print(f"📄 Stored notes length: {len(stored_notes)}")
            print(f"🔍 Stored notes preview: {stored_notes[:100]}...")
            
            if stored_notes.startswith('PROCESSING_DATA:'):
                print(f"🎉 SUCCESS: Processing data stored correctly!")
                print(f"🌐 View at: http://127.0.0.1:5000/task/{task_id}")
            else:
                print("❌ Processing data not found in stored notes")
        else:
            print("❌ Could not verify task in database")
            
        return task_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    print("Creating test task with processing data directly in database...")
    task_id = create_test_task_with_processing_data()
    
    if task_id:
        print(f"\n{'='*60}")
        print(f"✅ TEST TASK CREATED SUCCESSFULLY")
        print(f"🆔 Task ID: {task_id}")
        print(f"🌐 View at: http://127.0.0.1:5000/task/{task_id}")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"❌ TEST TASK CREATION FAILED")
        print(f"{'='*60}")
