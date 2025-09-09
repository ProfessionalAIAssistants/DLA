#!/usr/bin/env python3
"""
Debug script to test task creation in load_pdfs function
"""

import json
from datetime import datetime
from src.core.crm_data import crm_data

def debug_task_creation():
    """Test the exact same task creation logic as in load_pdfs"""
    
    # Simulate the same data structure as in load_pdfs
    results = {
        'processed': 3,
        'created': 3,
        'created_opportunities': [
            {'id': 1, 'request_number': 'TEST-001'},
            {'id': 2, 'request_number': 'TEST-002'},
            {'id': 3, 'request_number': 'TEST-003'}
        ],
        'created_contacts': [],
        'created_accounts': [],
        'created_products': [],
        'updated_contacts': [],
        'updated_accounts': []
    }
    
    print("Starting task creation debug...")
    print(f"Results processed: {results['processed']}")
    
    if results['processed'] > 0:
        try:
            # Create task due today (exact same code as load_pdfs)
            today = datetime.now().strftime("%Y-%m-%d")
            process_date = datetime.now().strftime("%m/%d/%Y")  # Changed format for title
            
            # Get created opportunities for summary
            created_opportunities = []
            if 'created_opportunities' in results and results['created_opportunities']:
                created_opportunities = results['created_opportunities']
            
            # Get all created records for detailed report
            created_accounts = results.get('created_accounts', [])
            created_contacts = results.get('created_contacts', [])
            created_products = results.get('created_products', [])
            updated_records = results.get('updated_contacts', []) + results.get('updated_accounts', [])
            
            # Build simple task description  
            task_description = f"""Review PDF processing results for {process_date}

Please review all newly created opportunities and verify data accuracy.

Double-click any opportunity in the table below to view full details."""

            print("Task description created:")
            print(task_description)
            
            # Store processing data for later use in task detail
            processing_data = {
                'processed': results['processed'],
                'created': results['created'],
                'skipped': results.get('skipped', 0),
                'errors': results.get('errors', []),
                'created_opportunities': created_opportunities,
                'created_contacts': created_contacts,
                'created_accounts': created_accounts,
                'created_products': created_products,
                'updated_records': updated_records
            }
            
            print("Processing data prepared:")
            print(json.dumps(processing_data, indent=2))
            
            # Create ONE comprehensive review task with new title format
            print("Calling crm_data.create_task...")
            task_id = crm_data.create_task(
                subject=f"Evaluate Upload {process_date}",
                description=f"{task_description}\n\nPROCESSING_DATA:{json.dumps(processing_data)}",
                status="Not Started",
                priority="High",
                type="Follow-up",
                due_date=today,
                work_date=today,  # Set work date to today
                assigned_to="System Generated"
            )
            
            print(f"Task created successfully with ID: {task_id}")
            
            # Link created opportunities to the task
            for opp in created_opportunities:
                if opp.get('id'):
                    try:
                        print(f"Linking opportunity {opp['id']} to task {task_id}...")
                        crm_data.link_opportunity_to_task(opp['id'], task_id)
                        print(f"Successfully linked opportunity {opp['id']}")
                    except Exception as link_error:
                        print(f"Error linking opportunity {opp['id']} to task {task_id}: {str(link_error)}")
            
            # Verify task was created
            tasks = crm_data.get_tasks(filters={'id': task_id})
            if tasks:
                print(f"Task verification successful: {tasks[0]['subject']}")
                return task_id
            else:
                print("ERROR: Task was not found after creation!")
                return None
                
        except Exception as task_error:
            print(f"ERROR creating review task: {str(task_error)}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print("No processing detected, task creation skipped")
        return None

if __name__ == "__main__":
    task_id = debug_task_creation()
    if task_id:
        print(f"\nSUCCESS: Task created with ID {task_id}")
    else:
        print("\nFAILED: Task was not created")
