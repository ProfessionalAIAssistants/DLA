#!/usr/bin/env python
import fitz
import re
import sys
from pathlib import Path

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def find_mfr_current(text):
    """Current manufacturer extraction method"""
    mfr_pattern = r'^(.+?\s+\w{5}\s+P/N\s+.+)$'
    matches = re.findall(mfr_pattern, text, re.MULTILINE)
    
    if matches:
        return '\n'.join(match.strip() for match in matches)
    return "Manually Check"

def find_mfr_improved(text):
    """Improved manufacturer extraction method for the specific format"""
    # Look for patterns like "IAW BASIC SPEC NR MIL-DTL-25988/1B"
    patterns = [
        r'IAW\s+BASIC\s+SPEC\s+NR\s+[^\n]+',
        r'REVISION\s+NR\s+[^\n]+',
        r'PART\s+PIECE\s+NUMBER:\s+[^\n]+',
        r'IAW\s+REFERENCE\s+SPEC\s+NR\s+[^\n]+'
    ]
    
    found_parts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_parts.extend(matches)
    
    if found_parts:
        return '\n'.join(found_parts)
    
    # Fallback to original pattern
    return find_mfr_current(text)

# Test the PDF
pdf_path = r"data\processed\Automation\5331-01-007-1611\SPE7M4-24-T-236A\SPE7M424T236A - Good.PDF"
if Path(pdf_path).exists():
    print("Extracting text from PDF...")
    text = extract_pdf_text(pdf_path)
    
    if text:
        print("="*60)
        print("EXTRACTED TEXT (first 2000 characters):")
        print("="*60)
        print(text[:2000])
        print("="*60)
        
        print("\nTesting current manufacturer extraction:")
        current_result = find_mfr_current(text)
        print(f"Current result: {current_result}")
        
        print("\nTesting improved manufacturer extraction:")
        improved_result = find_mfr_improved(text)
        print(f"Improved result: {improved_result}")
        
        # Also look for specific patterns in the text
        print("\n" + "="*60)
        print("SEARCHING FOR SPECIFIC PATTERNS:")
        print("="*60)
        
        # Search for IAW patterns
        iaw_matches = re.findall(r'IAW[^\n]*', text, re.IGNORECASE)
        if iaw_matches:
            print("Found IAW patterns:")
            for match in iaw_matches:
                print(f"  - {match}")
        
        # Search for MIL-DTL patterns  
        mil_matches = re.findall(r'MIL-DTL[^\n]*', text, re.IGNORECASE)
        if mil_matches:
            print("Found MIL-DTL patterns:")
            for match in mil_matches:
                print(f"  - {match}")
                
        # Search for PART PIECE NUMBER patterns
        part_matches = re.findall(r'PART\s+PIECE\s+NUMBER[^\n]*', text, re.IGNORECASE)
        if part_matches:
            print("Found PART PIECE NUMBER patterns:")
            for match in part_matches:
                print(f"  - {match}")
        
    else:
        print("Failed to extract text from PDF")
else:
    print(f"PDF file not found: {pdf_path}")
