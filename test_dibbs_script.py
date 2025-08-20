#!/usr/bin/env python
# coding: utf-8

"""
DIBBs Script Validator
This script checks if DIBBs.py can be properly imported and executed.
"""

import os
import sys
import importlib.util
from pathlib import Path

def validate_dibbs_import():
    """Check if DIBBs.py can be imported properly"""
    try:
        # Check if the file exists
        dibbs_path = Path("DIBBs.py")
        if not dibbs_path.exists():
            return False, "DIBBs.py file not found"
            
        # Try to import the module
        spec = importlib.util.spec_from_file_location("dibbs", dibbs_path)
        dibbs = importlib.util.module_from_spec(spec)
        sys.modules["dibbs"] = dibbs
        spec.loader.exec_module(dibbs)
        
        # Check if key functions exist
        required_functions = [
            "extract_text_from_pdf", 
            "process_pdf", 
            "find_request_numbers",
            "find_nsn_and_fsc"
        ]
        
        missing_functions = []
        for func in required_functions:
            if not hasattr(dibbs, func):
                missing_functions.append(func)
        
        if missing_functions:
            return False, f"Missing required functions: {', '.join(missing_functions)}"
        
        return True, "DIBBs.py imported successfully and contains all required functions"
    
    except Exception as e:
        return False, f"Error importing DIBBs.py: {str(e)}"

def test_extract_text_function():
    """Test if the extract_text_from_pdf function works properly"""
    try:
        # Import DIBBs module
        dibbs_path = Path("DIBBs.py")
        if not dibbs_path.exists():
            return False, "DIBBs.py file not found"
            
        spec = importlib.util.spec_from_file_location("dibbs", dibbs_path)
        dibbs = importlib.util.module_from_spec(spec)
        sys.modules["dibbs"] = dibbs
        spec.loader.exec_module(dibbs)
        
        # Find a PDF to test with
        pdf_dir = Path("To Process")
        if not pdf_dir.exists():
            return False, "To Process directory not found"
        
        pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("*.PDF"))
        if not pdf_files:
            return False, "No PDF files found in To Process directory"
        
        # Try to extract text from the first PDF
        test_pdf = pdf_files[0]
        text = dibbs.extract_text_from_pdf(str(test_pdf))
        
        if text and len(text) > 0:
            return True, f"Successfully extracted {len(text)} characters from {test_pdf.name}"
        else:
            return False, f"No text extracted from {test_pdf.name}"
    
    except Exception as e:
        return False, f"Error testing extract_text_from_pdf: {str(e)}"

def main():
    """Main function to run the DIBBs validator"""
    print("=== DIBBs Script Validator ===")
    
    # Validate DIBBs import
    import_success, import_message = validate_dibbs_import()
    print(f"DIBBs Import: {'SUCCESS' if import_success else 'FAILED'}")
    print(f"  {import_message}")
    
    # If import succeeded, test extract_text function
    if import_success:
        extract_success, extract_message = test_extract_text_function()
        print(f"\nText Extraction: {'SUCCESS' if extract_success else 'FAILED'}")
        print(f"  {extract_message}")
    
    print("=== Validation Complete ===")

if __name__ == "__main__":
    main()
