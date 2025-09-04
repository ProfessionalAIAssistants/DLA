import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the CRM app to get the initialized crm_data instance
import crm_app

# Test the create_task method directly
crm_data = crm_app.crm_data

# Test with the exact same data that would come from the API
test_data = {
    'subject': 'Debug Test Task',
    'description': 'Testing direct CRMDatabase.create_task call',
    'status': 'Not Started',
    'priority': 'Medium',
    'parent_item_type': 'Opportunity',
    'parent_item_id': 1
}

print(f"Test data: {test_data}")

try:
    task_id = crm_data.create_task(**test_data)
    print(f"Task created with ID: {task_id}")
    
    # Verify it was created correctly
    task = crm_data.get_task_by_id(task_id)
    print(f"Created task: {task}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
