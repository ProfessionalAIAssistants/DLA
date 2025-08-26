#!/usr/bin/env python3
"""
File Cleanup Analysis for DLA CRM Project
Identifies and categorizes temporary files for safe removal
"""

import os
import glob
from pathlib import Path

def analyze_files():
    """Analyze all files in the project directory"""
    
    # Core application files (KEEP)
    core_files = {
        'crm_app.py',           # Main Flask application
        'crm_data.py',          # Data access layer
        'crm_database.py',      # Database schema
        'crm_automation.py',    # Business logic
        'crm_cli.py',           # Command line interface
        'start_crm.py',         # Application launcher
        'pdf_processor.py',     # PDF processing
        'DIBBs.py',            # Original filtering logic
        'simplified_dla_processor.py',  # Alternative processor
        'improved_dibbs_parser.py',     # Enhanced parser
        'email_automation_service.py', # Email automation
        'email_automation.py',  # Email module
        'requirements.txt',     # Dependencies
        'config.json',         # Configuration
        'settings.json',       # Settings
        'email_config.json',   # Email config (if exists)
        'crm.db',              # Main database
        'crm_database.db',     # Secondary database
        'database_status.json', # Database status
        'crm_app.log',         # Application logs
        'README.md',           # Documentation
        'DLA_PDF_Processing.ipynb',  # Notebook
        'DUPLICATE_VALIDATION.md',   # Documentation
        'EMAIL_AUTOMATION_SETUP.md', # Documentation
    }
    
    # Find all Python files
    py_files = glob.glob('*.py')
    
    # Categorize files
    categories = {
        'CORE_APPLICATION': [],
        'TEMPORARY_DIAGNOSTIC': [],
        'TEST_FILES': [],
        'FIX_SCRIPTS': [],
        'CLEANUP_SCRIPTS': [],
        'CHECK_SCRIPTS': [],
        'UPDATE_SCRIPTS': [],
        'VALIDATE_SCRIPTS': [],
        'VERIFY_SCRIPTS': [],
        'DEBUG_SCRIPTS': [],
        'OPTIMIZE_SCRIPTS': [],
        'OTHER_TEMP': []
    }
    
    for file in py_files:
        if file in core_files:
            categories['CORE_APPLICATION'].append(file)
        elif file.startswith('test_'):
            categories['TEST_FILES'].append(file)
        elif file.startswith('fix_'):
            categories['FIX_SCRIPTS'].append(file)
        elif file.startswith('cleanup_'):
            categories['CLEANUP_SCRIPTS'].append(file)
        elif file.startswith('check_'):
            categories['CHECK_SCRIPTS'].append(file)
        elif file.startswith('update_'):
            categories['UPDATE_SCRIPTS'].append(file)
        elif file.startswith('validate_'):
            categories['VALIDATE_SCRIPTS'].append(file)
        elif file.startswith('verify_'):
            categories['VERIFY_SCRIPTS'].append(file)
        elif file.startswith('debug_'):
            categories['DEBUG_SCRIPTS'].append(file)
        elif file.startswith('optimize_'):
            categories['OPTIMIZE_SCRIPTS'].append(file)
        elif file.startswith(('add_', 'create_', 'analyze_', 'deep_', 'find_', 'document_', 'simple_')):
            categories['OTHER_TEMP'].append(file)
        else:
            # Check if it's a temporary diagnostic file
            temp_patterns = [
                'final_', 'quick_', 'enhanced_', 'improved_', 'advanced_',
                'comprehensive_', 'automated_', 'smart_', 'intelligent_'
            ]
            if any(file.startswith(pattern) for pattern in temp_patterns):
                categories['TEMPORARY_DIAGNOSTIC'].append(file)
            else:
                categories['CORE_APPLICATION'].append(file)  # Default to core if unsure
    
    return categories

def print_analysis():
    """Print the file analysis"""
    categories = analyze_files()
    
    print("=" * 80)
    print("FILE CLEANUP ANALYSIS - DLA CRM PROJECT")
    print("=" * 80)
    
    # Show core files to keep
    print("\n🔒 CORE APPLICATION FILES (KEEP):")
    print("-" * 40)
    for file in sorted(categories['CORE_APPLICATION']):
        print(f"   ✅ {file}")
    
    # Show files that can be safely removed
    removable_categories = [
        ('CHECK_SCRIPTS', '🔍 Check Scripts (Database/Schema diagnostics)'),
        ('CLEANUP_SCRIPTS', '🧹 Cleanup Scripts (One-time fixes)'),
        ('DEBUG_SCRIPTS', '🐛 Debug Scripts (Troubleshooting)'),
        ('FIX_SCRIPTS', '🔧 Fix Scripts (One-time corrections)'),
        ('OPTIMIZE_SCRIPTS', '⚡ Optimize Scripts (Performance tweaks)'),
        ('UPDATE_SCRIPTS', '📝 Update Scripts (Schema updates)'),
        ('VALIDATE_SCRIPTS', '✅ Validate Scripts (Verification)'),
        ('VERIFY_SCRIPTS', '🔎 Verify Scripts (Testing)'),
        ('OTHER_TEMP', '🗂️ Other Temporary Scripts'),
        ('TEMPORARY_DIAGNOSTIC', '🩺 Temporary Diagnostic Scripts'),
    ]
    
    total_removable = 0
    for category, description in removable_categories:
        if categories[category]:
            print(f"\n{description}:")
            print("-" * 40)
            for file in sorted(categories[category]):
                print(f"   ❌ {file}")
                total_removable += 1
    
    # Show test files separately
    if categories['TEST_FILES']:
        print(f"\n🧪 TEST FILES (Consider keeping recent ones):")
        print("-" * 40)
        for file in sorted(categories['TEST_FILES']):
            print(f"   ⚠️  {file}")
    
    print(f"\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"   Core files to keep: {len(categories['CORE_APPLICATION'])}")
    print(f"   Files that can be removed: {total_removable}")
    print(f"   Test files to review: {len(categories['TEST_FILES'])}")
    print("=" * 80)
    
    return categories

def generate_cleanup_command():
    """Generate PowerShell command to remove temporary files"""
    categories = analyze_files()
    
    removable_files = []
    removable_categories = [
        'CHECK_SCRIPTS', 'CLEANUP_SCRIPTS', 'DEBUG_SCRIPTS', 'FIX_SCRIPTS',
        'OPTIMIZE_SCRIPTS', 'UPDATE_SCRIPTS', 'VALIDATE_SCRIPTS', 
        'VERIFY_SCRIPTS', 'OTHER_TEMP', 'TEMPORARY_DIAGNOSTIC'
    ]
    
    for category in removable_categories:
        removable_files.extend(categories[category])
    
    if removable_files:
        print(f"\n📝 CLEANUP COMMAND:")
        print("-" * 40)
        print("Remove-Item " + ", ".join(sorted(removable_files)))
        
        print(f"\n💾 BACKUP COMMAND (run first if unsure):")
        print("-" * 40)
        print("mkdir temp_backup")
        print("Copy-Item " + ", ".join(sorted(removable_files)) + " -Destination temp_backup\\")
    
    return removable_files

if __name__ == "__main__":
    print_analysis()
    generate_cleanup_command()
