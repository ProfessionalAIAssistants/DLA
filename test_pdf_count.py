"""
PDF Processing Status Checker
This script checks for PDF files in the To Process directory and validates
if they can be properly processed by the DIBBs.py script.
"""

import os
import sys
import json
from pathlib import Path

def test_pdf_count():
    """Test counting PDFs in To Process directory"""
    to_process_dir = Path("To Process")
    if not to_process_dir.exists():
        print("Error: 'To Process' directory doesn't exist")
        return
    
    try:
        pdf_files = list(to_process_dir.glob("*.pdf")) + list(to_process_dir.glob("*.PDF"))
        print(f"Found {len(pdf_files)} PDF files in 'To Process' directory")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
            # Check if file is readable
            try:
                if os.access(pdf, os.R_OK):
                    print(f"    - File is readable")
                else:
                    print(f"    - File is NOT readable")
            except Exception as e:
                print(f"    - Error checking readability: {e}")
    except Exception as e:
        print(f"Error counting PDFs: {e}")

def validate_pdf_structure():
    """Check if required directories for PDF processing exist"""
    base_dir = Path().absolute()
    required_dirs = {
        "To Process": base_dir / "To Process",
        "Output": base_dir / "Output",
        "Automation": base_dir / "Automation",
        "Reviewed": base_dir / "Reviewed"
    }
    
    status = {}
    for name, path in required_dirs.items():
        status[name] = {
            "exists": path.exists(),
            "path": str(path)
        }
    
    return status

def check_pymupdf():
    """Check if PyMuPDF (fitz) is installed"""
    try:
        import fitz
        return True, fitz.__version__
    except ImportError:
        return False, None

if __name__ == "__main__":
    print("=== PDF Processing Status Checker ===")
    
    # Check PDF count
    test_pdf_count()
    
    # Check directory structure
    dir_status = validate_pdf_structure()
    print("\nDirectory Structure Status:")
    for name, status in dir_status.items():
        exists_status = "✓ EXISTS" if status["exists"] else "✗ MISSING"
        print(f"  - {name}: {exists_status} ({status['path']})")
    
    # Check PyMuPDF
    pymupdf_installed, version = check_pymupdf()
    print("\nPyMuPDF (fitz) Status:")
    if pymupdf_installed:
        print(f"  ✓ INSTALLED (Version: {version})")
    else:
        print(f"  ✗ NOT INSTALLED - Required for PDF processing")
    
    print("=== Check Complete ===")
