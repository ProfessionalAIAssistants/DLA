import fitz
import os
from pathlib import Path

# Define the path to the PDF file
pdf_dir = Path(__file__).parent / "To Process"
pdf_files = list(pdf_dir.glob("*.PDF"))

if pdf_files:
    pdf_file = pdf_files[0]
    print(f"Processing: {pdf_file}")
    
    try:
        # Try to open and extract text from the PDF
        with fitz.open(pdf_file) as doc:
            print(f"PDF opened successfully. Pages: {doc.page_count}")
            
            # Extract text from the first page
            if doc.page_count > 0:
                page = doc.load_page(0)
                text = page.get_text()
                print(f"First page text sample: {text[:200]}...")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
else:
    print(f"No PDF files found in {pdf_dir}")
