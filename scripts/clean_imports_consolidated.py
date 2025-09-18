#!/usr/bin/env python3
"""
Consolidated Import Cleaner
Removes redundant datetime imports from multiple source files
"""

import argparse
import os
import re

def clean_datetime_imports(file_path, indentation_level=0):
    """Clean redundant datetime imports from a file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"🔧 Cleaning datetime imports from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        cleaned_lines = []
        main_import_found = False
        
        # Generate appropriate indentation
        indent = ' ' * (indentation_level * 4)
        
        for i, line in enumerate(lines):
            # Detect the main datetime import (usually at the top)
            if not main_import_found and 'from datetime import' in line.strip():
                main_import_found = True
                cleaned_lines.append(line)
                continue
            
            # Remove redundant datetime imports after the first one
            if (main_import_found and 
                'from datetime import' in line.strip() and 
                line.strip().startswith(indent + 'from datetime import')):
                # Replace with comment
                cleaned_lines.append(f"{indent}# datetime already imported at top of file")
            else:
                cleaned_lines.append(line)
        
        # Write back the cleaned content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))
        
        print(f"✓ Successfully cleaned {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning {file_path}: {e}")
        return False

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Clean redundant datetime imports from Python files')
    parser.add_argument('--all', action='store_true', help='Clean all known target files')
    parser.add_argument('--file', type=str, help='Clean specific file')
    parser.add_argument('--indent', type=int, default=0, help='Indentation level for target imports (default: 0)')
    
    args = parser.parse_args()
    
    if args.all:
        # Clean all known target files
        targets = [
            ('crm_app.py', 0),
            ('src/core/crm_data.py', 2),
            ('src/pdf/dibbs_crm_processor.py', 3)
        ]
        
        print("🧹 Cleaning redundant datetime imports from all target files...")
        print("=" * 60)
        
        success_count = 0
        for file_path, indent_level in targets:
            if clean_datetime_imports(file_path, indent_level):
                success_count += 1
        
        print("=" * 60)
        print(f"✓ Successfully cleaned {success_count}/{len(targets)} files")
        
    elif args.file:
        # Clean specific file
        clean_datetime_imports(args.file, args.indent)
        
    else:
        # Interactive mode
        print("🧹 Interactive Import Cleaner")
        print("=" * 40)
        print("Available target files:")
        print("1. crm_app.py")
        print("2. src/core/crm_data.py")
        print("3. src/pdf/dibbs_crm_processor.py")
        print("4. Custom file")
        print("5. All files")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            clean_datetime_imports('crm_app.py', 0)
        elif choice == '2':
            clean_datetime_imports('src/core/crm_data.py', 2)
        elif choice == '3':
            clean_datetime_imports('src/pdf/dibbs_crm_processor.py', 3)
        elif choice == '4':
            file_path = input("Enter file path: ").strip()
            indent_level = int(input("Enter indentation level (0-4): ") or "0")
            clean_datetime_imports(file_path, indent_level)
        elif choice == '5':
            # Same as --all
            targets = [
                ('crm_app.py', 0),
                ('src/core/crm_data.py', 2),
                ('src/pdf/dibbs_crm_processor.py', 3)
            ]
            
            print("🧹 Cleaning all target files...")
            success_count = 0
            for file_path, indent_level in targets:
                if clean_datetime_imports(file_path, indent_level):
                    success_count += 1
            
            print(f"✓ Successfully cleaned {success_count}/{len(targets)} files")
        else:
            print("❌ Invalid option selected")

if __name__ == "__main__":
    main()