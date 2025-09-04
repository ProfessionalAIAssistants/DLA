#!/usr/bin/env python3
"""
Test script for payment history extraction in DIBBs CRM processor
"""
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from pdf.dibbs_crm_processor import DIBBsCRMProcessor

def test_payment_history_extraction():
    """Test the payment history extraction functionality"""
    print("Testing DIBBs CRM Processor Payment History Extraction")
    print("=" * 60)
    
    # Initialize processor
    processor = DIBBsCRMProcessor()
    
    # Test the payment history function with a mock table
    test_table = """CAGE   Contract Number      Quantity   Unit Cost    AWD Date  Surplus Material
12345  ABC123              100.0      50.25       2023-01-15  N
67890  DEF456              200.0      75.50       2023-02-20  Y
"""
    
    # Mock the extract_table_text method for testing
    original_extract = processor.extract_table_text
    def mock_extract_table_text(pdf_file, keyword, skip_count):
        if "CAGE   Contract Number" in keyword:
            return test_table
        return original_extract(pdf_file, keyword, skip_count)
    
    processor.extract_table_text = mock_extract_table_text
    
    # Test payment history extraction
    try:
        result = processor.find_payment_history("test.pdf")
        print("Payment History Extraction Result:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        if result and result != "Manually Check" and result != "No payment history found":
            print("✅ Payment history extraction successful!")
            print("Sample format:")
            lines = result.split('\n')
            for i, line in enumerate(lines[:3]):  # Show first 3 lines
                if line.strip():
                    print(f"  Line {i+1}: {line}")
        else:
            print("❌ Payment history extraction returned:", result)
            
    except Exception as e:
        print(f"❌ Error during payment history extraction: {e}")
        import traceback
        traceback.print_exc()
    
    # Restore original method
    processor.extract_table_text = original_extract
    
    print("\nTesting complete!")

if __name__ == "__main__":
    test_payment_history_extraction()
