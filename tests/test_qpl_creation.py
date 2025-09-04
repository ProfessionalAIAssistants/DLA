#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

# Test MFR parsing directly
def test_mfr_parsing():
    try:
        from mfr_parser import MFRParser
        parser = MFRParser()
        
        # Test the exact string from the attachment
        mfr_string = "MOOG INC 94697 P/N 58532-012"
        nsn = "5331012715779"
        
        print(f"Testing MFR parsing:")
        print(f"  NSN: {nsn}")
        print(f"  MFR: {mfr_string}")
        
        # Parse manufacturers
        manufacturers = parser.parse_mfr_string(mfr_string)
        print(f"  Parsed {len(manufacturers)} manufacturers:")
        for mfr in manufacturers:
            print(f"    - {mfr['manufacturer_name']} (CAGE: {mfr['cage_code']}) P/N {mfr['part_number']}")
        
        # Test full QPL processing
        print(f"\nTesting full QPL processing...")
        result = parser.process_opportunity_mfr(
            opportunity_id=999,  # Test opportunity ID
            nsn=nsn,
            mfr_string=mfr_string,
            product_name=f"Test Product {nsn}",
            description="Test product for QPL creation"
        )
        
        print(f"  QPL Result: {result}")
        
    except Exception as e:
        print(f"Error testing MFR parsing: {e}")
        import traceback
        traceback.print_exc()

def test_pdf_processing():
    try:
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        
        processor = DIBBsCRMProcessor()
        
        # Check if the QPL creation code is properly integrated
        print("PDF Processor QPL Integration Check:")
        print(f"  Base dir: {processor.base_dir}")
        
        # Check MFR parser import
        import sys
        sys.path.append(str(processor.base_dir))
        from mfr_parser import MFRParser
        print(f"  ✓ MFR Parser imported successfully")
        
    except Exception as e:
        print(f"Error testing PDF processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== MFR Parser Test ===")
    test_mfr_parsing()
    
    print("\n=== PDF Processor Test ===")
    test_pdf_processing()
