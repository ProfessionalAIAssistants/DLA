#!/usr/bin/env python
import fitz
import re

# Extract text from PDF to see exact formatting
pdf_path = r"data\processed\Automation\5331-01-007-1611\SPE7M4-24-T-236A\SPE7M424T236A - Good.PDF"

doc = fitz.open(pdf_path)
text = ""
for page in doc:
    text += page.get_text()
doc.close()

# Find context around IAW patterns
lines = text.split('\n')
print("Lines containing IAW, REVISION, or PART PIECE:")
print("=" * 60)

for i, line in enumerate(lines):
    if any(keyword in line.upper() for keyword in ['IAW', 'REVISION NR', 'PART PIECE NUMBER']):
        print(f"Line {i}: '{line}'")
        
        # Show 2 lines before and after for context
        print("Context:")
        start = max(0, i-2)
        end = min(len(lines), i+3)
        for j in range(start, end):
            marker = ">>> " if j == i else "    "
            print(f"{marker}Line {j}: '{lines[j]}'")
        print("-" * 40)

print("\n" + "=" * 60)
print("Testing precise extraction:")

# Try extracting just the specific manufacturer lines
mfr_lines = []
for line in lines:
    line = line.strip()
    if line.startswith('IAW BASIC SPEC NR'):
        mfr_lines.append(line)
    elif line.startswith('IAW REFERENCE SPEC NR'):
        mfr_lines.append(line)
    elif line.startswith('REVISION NR') and 'DTD' in line:
        mfr_lines.append(line)
    elif line.startswith('PART PIECE NUMBER:'):
        mfr_lines.append(line)

print("Extracted manufacturer lines:")
for line in mfr_lines:
    print(f"'{line}'")

print(f"\nJoined result: '{' '.join(mfr_lines)}'")
