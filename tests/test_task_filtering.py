#!/usr/bin/env python3
"""
Test script to verify task filtering by ID works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.crm_data import CRMDataManager

def test_task_filtering():
    crm_data = CRMDataManager()
    
    print("Testing task filtering by ID...")
    
    # Get all tasks first
    all_tasks = crm_data.get_tasks()
    print(f"Total tasks found: {len(all_tasks)}")
    
    if all_tasks:
        # Test filtering by first task ID
        first_task_id = all_tasks[0]['id']
        print(f"Testing filter for task ID: {first_task_id}")
        
        # Use the same method that get_task_by_id uses
        filtered_tasks = crm_data.get_tasks({'id': first_task_id})
        print(f"Filtered tasks found: {len(filtered_tasks)}")
        
        if filtered_tasks:
            found_task = filtered_tasks[0]
            print(f"Found task ID: {found_task['id']}")
            print(f"Task subject: {found_task.get('subject', 'No subject')}")
            
            if found_task['id'] == first_task_id:
                print("✓ Task filtering by ID works correctly!")
            else:
                print("✗ Task filtering returned wrong task!")
        else:
            print("✗ No tasks found with filter - this is the bug!")
    else:
        print("No tasks found in database")

if __name__ == "__main__":
    test_task_filtering()
