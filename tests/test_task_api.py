import requests
import json

# Test task creation API with parent linking
task_data = {
    'subject': 'Test Task from API',
    'description': 'This is a test task to verify parent linking',
    'status': 'Not Started',
    'priority': 'Medium',
    'parent_item_type': 'Opportunity',
    'parent_item_id': 1  # Assuming there's an opportunity with ID 1
}

# Send POST request to create task
response = requests.post('http://127.0.0.1:5000/api/tasks', 
                        json=task_data, 
                        headers={'Content-Type': 'application/json'})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200 and response.json().get('success'):
    print(f"Task created successfully with ID: {response.json().get('task_id')}")
else:
    print(f"Error creating task: {response.json()}")
