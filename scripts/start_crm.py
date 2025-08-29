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
1. Run: python app.py                            # Start main application
2. Access web interface: http://localhost:5000
3. Process PDFs: Use the web interface "Load PDFs" button

COMMAND LINE USAGE:
- python scripts/start_crm.py dashboard         # Show dashboard
- python scripts/start_crm.py rfqs --status New # List new RFQs  
- python scripts/start_crm.py tasks             # List pending tasks
- python scripts/start_crm.py process           # Process PDFs

FILE STRUCTURE:
├── app.py                      # Main application entry point
├── src/                        # Source code
│   ├── core/                   # Core CRM modules
│   │   ├── crm_app.py         # Flask web application
│   │   ├── crm_data.py        # Data access layer
│   │   ├── crm_database.py    # Database schema
│   │   └── crm_automation.py  # Business logic
│   ├── email/                  # Email automation
│   │   └── email_automation.py
│   └── pdf/                    # PDF processing
│       └── dibbs_crm_processor.py
├── web/                        # Web interface
│   ├── templates/              # HTML templates
│   └── static/                 # CSS/JS assets
├── config/                     # Configuration files
├── data/                       # Data storage
│   ├── crm.db                 # SQLite database
│   ├── input/To Process/      # Input PDF folder
│   ├── output/Output/         # CSV output folder
│   └── processed/             # Processed files
├── scripts/                    # Utility scripts
└── docs/                       # Documentation

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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_setup():
    """Check if system is properly set up"""
    base_dir = Path(__file__).parent.parent
    required_files = [
        'src/core/crm_database.py',
        'src/core/crm_data.py', 
        'src/core/crm_automation.py',
        'src/core/crm_app.py',
        'src/pdf/dibbs_crm_processor.py'
    ]
    
    missing = []
    for file in required_files:
        if not (base_dir / file).exists():
            missing.append(file)
    
    if missing:
        print("Missing required files:")
        for file in missing:
            print(f"  - {file}")
        print("\nPlease ensure all files are in the correct directory structure.")
        return False
    
    return True

def start_web_interface():
    """Start the web interface"""
    try:
        print("Starting CRM web interface...")
        base_dir = Path(__file__).parent.parent
        app_path = base_dir / 'app.py'
        
        if app_path.exists():
            # Start the main app.py (preferred entry point)
            subprocess.Popen([sys.executable, str(app_path)])
        else:
            # Fallback to direct crm_app.py
            crm_app_path = base_dir / 'crm_app.py'
            if crm_app_path.exists():
                subprocess.Popen([sys.executable, str(crm_app_path)])
            else:
                print("Error: Neither app.py nor crm_app.py found. Please run from project root.")
                return
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
