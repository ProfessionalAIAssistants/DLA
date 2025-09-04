#!/usr/bin/env python3
"""Remove redundant datetime imports from crm_app.py"""

import re

def clean_redundant_imports():
    with open('crm_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track lines to remove redundant imports (after line 5 which has the main import)
    lines = content.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Skip redundant datetime imports after the main one at the top
        if i > 5 and ('from datetime import' in line.strip() and line.strip().startswith('from datetime import')):
            # Replace with comment
            cleaned_lines.append('        # datetime already imported at top of file')
        else:
            cleaned_lines.append(line)
    
    # Write back the cleaned content
    with open('crm_app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print("✓ Removed redundant datetime imports from crm_app.py")

if __name__ == "__main__":
    clean_redundant_imports()
