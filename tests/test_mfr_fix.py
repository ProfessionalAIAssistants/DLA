#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pdf.dibbs_crm_processor import DIBBsCRMProcessor
import fitz

# Test the updated manufacturer extraction
pdf_path = r"data\processed\Automation\5331-01-007-1611\SPE7M4-24-T-236A\SPE7M424T236A - Good.PDF"

# Extract text from PDF
doc = fitz.open(pdf_path)
text = ""
for page in doc:
    text += page.get_text()
doc.close()

# Create processor instance and test the find_mfr method
processor = DIBBsCRMProcessor()
result = processor.find_mfr(text)

print("Updated manufacturer extraction result:")
print("=" * 50)
print(result)
print("=" * 50)

# Compare with expected result
expected = "IAW BASIC SPEC NR MIL-DTL-25988/1B REVISION NR B DTD 06/29/2021 PART PIECE NUMBER: M25988/1-261 IAW REFERENCE SPEC NR MIL-DTL-25988D REVISION NR D DTD 01/21/2021 PART PIECE NUMBER:"

print(f"\nExpected: {expected}")
print(f"Got: {result}")
print(f"Match: {result == expected}")
