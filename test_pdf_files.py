"""
Detailed test script for PDF processing
"""

import os
from pathlib import Path
import PyPDF2

def test_pdf_files():
    """Test access and reading of PDF files"""
    to_process_dir = Path("To Process")
    if not to_process_dir.exists():
        print("Error: 'To Process' directory doesn't exist")
        return
    
    # Get all PDF files
    pdf_files = list(to_process_dir.glob("*.pdf")) + list(to_process_dir.glob("*.PDF"))
    print(f"Found {len(pdf_files)} PDF files in 'To Process' directory")
    
    for pdf in pdf_files:
        print(f"\nTesting file: {pdf.name}")
        
        # Check if file exists
        print(f"  - File exists: {pdf.exists()}")
        
        # Check if file is readable
        try:
            readable = os.access(pdf, os.R_OK)
            print(f"  - File is readable: {readable}")
        except Exception as e:
            print(f"  - Error checking readability: {e}")
        
        # Try to open and read the PDF
        try:
            with open(pdf, 'rb') as f:
                print(f"  - Successfully opened file")
                try:
                    reader = PyPDF2.PdfReader(f)
                    print(f"  - Successfully created PDF reader object")
                    print(f"  - Number of pages: {len(reader.pages)}")
                    
                    # Try to read the first page
                    try:
                        text = reader.pages[0].extract_text()
                        print(f"  - Successfully extracted text from first page")
                        print(f"  - First 100 chars: {text[:100].replace(chr(10), ' ')}")
                    except Exception as e:
                        print(f"  - Error extracting text from first page: {e}")
                
                except Exception as e:
                    print(f"  - Error creating PDF reader: {e}")
        except Exception as e:
            print(f"  - Error opening file: {e}")

if __name__ == "__main__":
    print("Testing PDF processing functionality...")
    test_pdf_files()
