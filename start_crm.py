# Local CRM System - Quick Start

"""
LOCAL CRM SYSTEM FOR DIBBS PROCESSING
=====================================

A self-contained, local Notion-like CRM system that integrates with DIBBs PDF processing.

FEATURES:
- Automatic RFQ processing from DIBBs PDFs
- Account and Contact management
- Opportunity tracking with qualification rules
- Task automation and management
- Interaction logging
- Dashboard with key metrics
- Web interface and command-line tools
- No external dependencies (no cloud services, APIs, or external servers)

QUICK START:
1. Run setup: python setup_crm.py
2. Start web interface: python crm_app.py
3. Process PDFs: Use the web interface "Load PDFs" button
4. Access web interface: http://localhost:5000

COMMAND LINE USAGE:
- python crm_cli.py dashboard                    # Show dashboard
- python crm_cli.py rfqs --status New           # List new RFQs  
- python crm_cli.py tasks --status "Not Started" # List pending tasks
- python crm_cli.py process                      # Process PDFs
- python crm_cli.py create-task                  # Create new task
- python crm_cli.py search "Parker"              # Search records

FILE STRUCTURE:
├── crm_database.py       # Database schema (SQLite)
├── crm_data.py          # Data access layer
├── crm_automation.py    # Business logic & automation
├── crm_app.py          # Web interface (Flask)
├── crm_cli.py          # Command line interface
├── pdf_processor.py    # Enhanced PDF processing with CRM
├── DIBBs.py           # Original filtering logic
├── start_crm.py       # Quick start launcher
├── templates/          # HTML templates
├── To Process/         # Input PDF folder
├── Output/             # CSV output folder
├── Automation/         # Qualified PDFs folder
├── Reviewed/           # Non-qualified PDFs folder
└── crm.db              # SQLite database file

QUALIFICATION RULES:
The system automatically qualifies RFQs based on:
- Delivery days >= 120
- ISO requirement = NO
- Sampling requirement = NO  
- Inspection point = DESTINATION
- Preferred manufacturers (Parker)

AUTOMATION FEATURES:
- Auto-create accounts for government agencies
- Auto-create contacts for buyers
- Auto-create opportunities for qualified RFQs
- Auto-assign tasks based on RFQ deadlines
- Calculate estimated amounts from historical pricing

WEB INTERFACE MODULES:
- Dashboard: Key metrics and today's activities
- Accounts: Government agencies and companies
- Contacts: Buyer contacts and relationships
- Opportunities: Sales pipeline and tracking
- RFQs: Request processing and status updates
- Products: Product catalog and pricing
- Tasks: Task management and assignments  
- Interactions: Communication history

DATABASE SCHEMA:
- accounts: Government agencies and companies
- contacts: Individual buyer contacts
- opportunities: Sales pipeline opportunities
- rfqs: Request for Quote records from DIBBs
- products: Product catalog and specifications
- qpl: Qualified Products List
- tasks: Task management and assignments
- interactions: Communication and activity history

INTEGRATION WORKFLOW:
1. Place PDFs in "To Process" folder
2. Use the web interface "Load PDFs" button to process PDFs
3. System automatically:
   - Creates RFQ records
   - Matches/creates accounts and contacts
   - Qualifies RFQs based on rules
   - Creates opportunities for qualified RFQs
   - Assigns follow-up tasks
   - Moves files to appropriate folders
4. Use web interface or CLI to manage pipeline

CUSTOMIZATION:
- Modify qualification rules in crm_automation.py
- Add new database fields in crm_database.py
- Customize web interface templates in templates/
- Add new CLI commands in crm_cli.py

REQUIREMENTS:
- Python 3.7+
- Flask (web interface)
- PyMuPDF (PDF processing)
- SQLite (database - included with Python)
- No internet connection required
"""

import subprocess
import sys
import time
import threading
from pathlib import Path

def check_setup():
    """Check if system is properly set up"""
    required_files = [
        'crm_database.py',
        'crm_data.py', 
        'crm_automation.py',
        'crm_app.py',
        'pdf_processor.py'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print("Missing required files:")
        for file in missing:
            print(f"  - {file}")
        print("\nPlease ensure all files are in the current directory.")
        return False
    
    return True

def start_web_interface():
    """Start the web interface and open browser"""
    try:
        print("Starting CRM web interface...")
        # Start the Flask app in background
        subprocess.Popen([sys.executable, 'crm_app.py'])
        time.sleep(3)  # Give it time to start
        
        # Open the webpage
        import webbrowser
        webbrowser.open('http://localhost:5000')
        
        print("✓ CRM web interface started at http://localhost:5000")
        print("✓ Opening webpage in your default browser...")
        print("\nPress Ctrl+C to stop the server when done.")
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down CRM system...")
            return True
    except Exception as e:
        print(f"✗ Error starting web interface: {e}")
        return False

def main():
    print("=" * 60)
    print("LOCAL CRM SYSTEM")
    print("=" * 60)
    
    # Check setup
    if not check_setup():
        print("\nSetup incomplete. Please ensure all required files are present.")
        return
    
    print("System check passed ✓")
    print("Starting web interface...\n")
    
    # Start web interface directly
    start_web_interface()

if __name__ == "__main__":
    main()
