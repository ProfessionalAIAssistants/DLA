#!/usr/bin/env python3
"""Remove redundant datetime imports from crm_data.py"""

def clean_crm_data_imports():
    with open('src/core/crm_data.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Skip redundant datetime imports after the main one at line 5
        if i > 10 and ('from datetime import' in line.strip() and line.strip().startswith('        from datetime import')):
            # Replace with comment
            cleaned_lines.append('        # datetime already imported at top of file')
        else:
            cleaned_lines.append(line)
    
    with open('src/core/crm_data.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print("✓ Removed redundant datetime imports from crm_data.py")

if __name__ == "__main__":
    clean_crm_data_imports()
