# Command Line Interface for Local CRM System

import argparse
import sys
from pathlib import Path
from datetime import datetime, date

# Import CRM modules
try:
    from crm_data import crm_data
    from crm_automation import crm_automation
    CRM_AVAILABLE = True
except ImportError:
    print("CRM modules not available. Run setup_crm.py first.")
    sys.exit(1)

def list_rfqs(status=None, limit=10):
    """List RFQs with optional status filter"""
    filters = {}
    if status:
        filters['status'] = status
    
    rfqs = crm_data.get_rfqs(filters, limit)
    
    print(f"\nRFQs ({len(rfqs)} found):")
    print("-" * 80)
    print(f"{'ID':<5} {'Request#':<15} {'Status':<10} {'NSN':<15} {'Close Date':<12}")
    print("-" * 80)
    
    for rfq in rfqs:
        print(f"{rfq['id']:<5} {rfq['request_number']:<15} {rfq['status']:<10} {rfq['nsn'] or 'N/A':<15} {rfq['close_date'] or 'N/A':<12}")

def list_tasks(status=None, limit=10):
    """List tasks with optional status filter"""
    filters = {}
    if status:
        filters['status'] = status
    
    tasks = crm_data.get_tasks(filters, limit)
    
    print(f"\nTasks ({len(tasks)} found):")
    print("-" * 80)
    print(f"{'ID':<5} {'Subject':<30} {'Status':<15} {'Due Date':<12} {'Priority':<8}")
    print("-" * 80)
    
    for task in tasks:
        print(f"{task['id']:<5} {task['subject'][:29]:<30} {task['status']:<15} {task['due_date'] or 'N/A':<12} {task['priority']:<8}")

def list_opportunities(stage=None, limit=10):
    """List opportunities with optional stage filter"""
    filters = {}
    if stage:
        filters['stage'] = stage
    
    opportunities = crm_data.get_opportunities(filters, limit)
    
    print(f"\nOpportunities ({len(opportunities)} found):")
    print("-" * 100)
    print(f"{'ID':<5} {'Name':<30} {'Stage':<15} {'Amount':<12} {'Close Date':<12} {'Account':<20}")
    print("-" * 100)
    
    for opp in opportunities:
        amount_str = f"${opp['amount']:,.2f}" if opp['amount'] else "N/A"
        print(f"{opp['id']:<5} {opp['name'][:29]:<30} {opp['stage']:<15} {amount_str:<12} {opp['close_date'] or 'N/A':<12} {opp['account_name'] or 'N/A':<20}")

def show_dashboard():
    """Show dashboard summary"""
    dashboard_data = crm_automation.get_daily_dashboard_data()
    metrics = dashboard_data['metrics']
    
    print("\n" + "=" * 60)
    print("LOCAL CRM DASHBOARD")
    print("=" * 60)
    
    print(f"\nKEY METRICS:")
    print(f"Pipeline Value:     ${metrics['total_pipeline_value']:,.2f}")
    print(f"Total Won:          ${metrics['total_won_value']:,.2f}")
    print(f"Pending Tasks:      {metrics['pending_tasks']}")
    print(f"Overdue Tasks:      {metrics['overdue_tasks']}")
    print(f"Total Opportunities: {metrics['total_opportunities']}")
    print(f"RFQ Qualification Rate: {metrics['rfq_qualification_rate']:.1f}%")
    print(f"RFQ Win Rate:       {metrics['rfq_win_rate']:.1f}%")
    
    print(f"\nTODAY'S TASKS ({len(dashboard_data['today_tasks'])}):")
    for task in dashboard_data['today_tasks'][:5]:
        print(f"  • {task['subject']} ({task['priority']} priority)")
    
    print(f"\nOVERDUE TASKS ({len(dashboard_data['overdue_tasks'])}):")
    for task in dashboard_data['overdue_tasks'][:5]:
        print(f"  • {task['subject']} (Due: {task['due_date']})")
    
    print(f"\nRECENT RFQs ({len(dashboard_data['new_rfqs'])}):")
    for rfq in dashboard_data['new_rfqs'][:5]:
        print(f"  • {rfq['request_number']} - {rfq['status']} ({rfq['close_date']})")

def process_pdfs():
    """Process PDFs using integrated DIBBs parser"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'DIBBs_integrated.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Error running PDF processing: {e}")

def create_task_interactive():
    """Interactive task creation"""
    print("\nCreate New Task")
    print("-" * 20)
    
    subject = input("Task subject: ")
    description = input("Description (optional): ")
    priority = input("Priority (High/Normal/Low) [Normal]: ") or "Normal"
    assigned_to = input("Assigned to: ")
    due_date = input("Due date (YYYY-MM-DD) [today]: ")
    
    if not due_date:
        due_date = date.today().isoformat()
    
    try:
        task_id = crm_data.create_task(
            subject=subject,
            description=description if description else None,
            priority=priority,
            assigned_to=assigned_to if assigned_to else None,
            due_date=due_date
        )
        print(f"✓ Task created successfully (ID: {task_id})")
    except Exception as e:
        print(f"✗ Error creating task: {e}")

def complete_task_by_id(task_id):
    """Mark task as completed"""
    try:
        result = crm_data.complete_task(task_id)
        if result:
            print(f"✓ Task {task_id} marked as completed")
        else:
            print(f"✗ Task {task_id} not found")
    except Exception as e:
        print(f"✗ Error completing task: {e}")

def search_records(query):
    """Search across all record types"""
    print(f"\nSearch results for: '{query}'")
    print("-" * 50)
    
    # Search accounts
    accounts = crm_data.get_accounts({'name': query}, limit=5)
    if accounts:
        print("ACCOUNTS:")
        for account in accounts:
            print(f"  • {account['name']} ({account['account_type']})")
    
    # Search contacts
    contacts = crm_data.get_contacts({'name': query}, limit=5)
    if contacts:
        print("CONTACTS:")
        for contact in contacts:
            print(f"  • {contact['first_name']} {contact['last_name']} ({contact['account_name'] or 'No Account'})")
    
    # Search RFQs
    rfqs = crm_data.execute_query(
        "SELECT * FROM rfqs WHERE request_number LIKE ? OR product_description LIKE ? LIMIT 5",
        [f"%{query}%", f"%{query}%"]
    )
    if rfqs:
        print("RFQs:")
        for rfq in rfqs:
            print(f"  • {rfq['request_number']} - {rfq['status']}")

def main():
    parser = argparse.ArgumentParser(description='Local CRM System CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Show dashboard summary')
    
    # RFQ commands
    rfq_parser = subparsers.add_parser('rfqs', help='List RFQs')
    rfq_parser.add_argument('--status', help='Filter by status')
    rfq_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    # Task commands
    task_parser = subparsers.add_parser('tasks', help='List tasks')
    task_parser.add_argument('--status', help='Filter by status')
    task_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    # Opportunity commands
    opp_parser = subparsers.add_parser('opportunities', help='List opportunities')
    opp_parser.add_argument('--stage', help='Filter by stage')
    opp_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    # Process PDFs
    subparsers.add_parser('process', help='Process PDFs with DIBBs parser')
    
    # Create task
    subparsers.add_parser('create-task', help='Create new task (interactive)')
    
    # Complete task
    complete_parser = subparsers.add_parser('complete-task', help='Mark task as completed')
    complete_parser.add_argument('task_id', type=int, help='Task ID to complete')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search records')
    search_parser.add_argument('query', help='Search query')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'dashboard':
        show_dashboard()
    elif args.command == 'rfqs':
        list_rfqs(args.status, args.limit)
    elif args.command == 'tasks':
        list_tasks(args.status, args.limit)
    elif args.command == 'opportunities':
        list_opportunities(args.stage, args.limit)
    elif args.command == 'process':
        process_pdfs()
    elif args.command == 'create-task':
        create_task_interactive()
    elif args.command == 'complete-task':
        complete_task_by_id(args.task_id)
    elif args.command == 'search':
        search_records(args.query)

if __name__ == "__main__":
    main()
