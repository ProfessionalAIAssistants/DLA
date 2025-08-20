"""
Test script for the PDF count API endpoint
"""

from pathlib import Path
import sys

def test_pdf_count_logic():
    """Test the logic used in the PDF count API endpoint"""
    try:
        to_process_dir = Path("To Process")
        if not to_process_dir.exists():
            print("Error: 'To Process' directory doesn't exist")
            return
        
        try:
            # Test basic file listing logic
            print("Testing simple file listing:")
            pdfs_simple = [f for f in to_process_dir.glob("*.pdf") if f.is_file()]
            pdfs_upper = [f for f in to_process_dir.glob("*.PDF") if f.is_file()]
            print(f"Found {len(pdfs_simple)} lowercase .pdf files")
            print(f"Found {len(pdfs_upper)} uppercase .PDF files")
            
            # Test the actual logic from the API endpoint
            print("\nTesting API endpoint logic:")
            pdf_count = len([f for f in to_process_dir.glob("*.pdf") if f.is_file()]) + \
                       len([f for f in to_process_dir.glob("*.PDF") if f.is_file()])
            print(f"Total PDF count: {pdf_count}")
            
            # List the actual files found
            print("\nListing files found:")
            all_pdfs = list(to_process_dir.glob("*.pdf")) + list(to_process_dir.glob("*.PDF"))
            for pdf in all_pdfs:
                print(f"  - {pdf.name}")
                
        except Exception as e:
            print(f"Error in file listing logic: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Error in test function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing PDF count API endpoint logic...")
    test_pdf_count_logic()
