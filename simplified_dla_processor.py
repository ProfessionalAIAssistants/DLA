import os
import sys
import re
import csv
import json
import shutil
import fitz  # PyMuPDF
import argparse
from pathlib import Path
from datetime import datetime

def create_directories():
    """Create necessary directories for processing"""
    base_dir = Path(__file__).parent
    pdf_dir = base_dir / "To Process"
    summary_dir = base_dir / "Output"
    automation_dir = base_dir / "Automation"
    reviewed_dir = base_dir / "Reviewed"
    
    # Create directories if they don't exist
    summary_dir.mkdir(exist_ok=True)
    automation_dir.mkdir(exist_ok=True)
    reviewed_dir.mkdir(exist_ok=True)
    
    return base_dir, pdf_dir, summary_dir, automation_dir, reviewed_dir

def extract_text_from_pdf(pdf_file):
    """Extract all text from a PDF file"""
    text = ""
    try:
        with fitz.open(pdf_file) as doc:
            print(f"PDF {os.path.basename(pdf_file)} has {doc.page_count} pages")
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from {os.path.basename(pdf_file)}: {str(e)}")
        return None

def find_request_number(text):
    """Find the request number in the PDF text"""
    request_no_pattern = r'1\. REQUEST NO\.\s*(\S+)\s*'
    match = re.search(request_no_pattern, text)
    return match.group(1) if match else "Unknown"

def find_nsn_and_fsc(text):
    """Find NSN and FSC values in the PDF text"""
    nsn_fsc_pattern = r'NSN/FSC:(\d+)/(\d+)'
    match = re.search(nsn_fsc_pattern, text)
    if match:
        fsc = match.group(2)
        nsn = fsc + match.group(1)
        return nsn, fsc
    else:
        nsn_material_pattern = r'NSN/MATERIAL:(\d+)'
        match = re.search(nsn_material_pattern, text)
        if match:
            if not match.group(1).startswith(("5331", "5330")):
                nsn = "5331" + match.group(1)
            else:
                nsn = match.group(1)
            return nsn, "Unknown"
    return "Unknown", "Unknown"

def find_purchase_number(text):
    """Find the purchase request number in the PDF text"""
    purchase_no_pattern = r'3\.\s*REQUISITION/PURCHASE REQUEST NO\.\s*(\S+)\s*'
    match = re.search(purchase_no_pattern, text)
    return match.group(1) if match else "Unknown"

def process_pdf(pdf_file):
    """Process a single PDF file and extract key information"""
    text = extract_text_from_pdf(pdf_file)
    if not text:
        return None
    
    # Extract key information
    request_number = find_request_number(text)
    nsn, fsc = find_nsn_and_fsc(text)
    purchase_number = find_purchase_number(text)
    
    return {
        "pdf_name": os.path.basename(pdf_file),
        "request_number": request_number,
        "nsn": nsn,
        "fsc": fsc,
        "purchase_number": purchase_number
    }

def process_pdfs(pdf_dir, summary_dir, automation_dir, reviewed_dir):
    """Process all PDFs in the input directory"""
    pdf_files = list(Path(pdf_dir).glob("*.PDF"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return
    
    today_str = datetime.today().strftime("%Y-%m-%d")
    csv_file_path = Path(summary_dir) / f"{today_str}_simplified_output.csv"
    
    # Create CSV file with headers
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["PDF File", "Request Number", "NSN", "FSC", "Purchase Number"])
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        result = process_pdf(str(pdf_file))
        if result:
            # Write to CSV
            with open(csv_file_path, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    result["pdf_name"],
                    result["request_number"],
                    result["nsn"],
                    result["fsc"],
                    result["purchase_number"]
                ])
            
            # Save JSON summary
            json_file_path = Path(summary_dir) / f"{result['request_number']}.json"
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(result, file, indent=4)
            
            print(f"Saved data for {result['request_number']}")

def main():
    """Main function to run the DLA PDF processor"""
    parser = argparse.ArgumentParser(description="Process DLA PDF files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        print("Running in verbose mode")
    
    print("DLA PDF Processor - Simplified Version")
    base_dir, pdf_dir, summary_dir, automation_dir, reviewed_dir = create_directories()
    
    print(f"Base directory: {base_dir}")
    print(f"PDF directory: {pdf_dir}")
    print(f"Summary directory: {summary_dir}")
    
    pdf_files = list(Path(pdf_dir).glob("*.PDF"))
    print(f"Found {len(pdf_files)} PDF files to process")
    
    process_pdfs(pdf_dir, summary_dir, automation_dir, reviewed_dir)
    print("Processing complete")

if __name__ == "__main__":
    main()
