#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

def test_pdf_qpl_integration():
    """Test QPL creation during PDF processing"""
    try:
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        
        processor = DIBBsCRMProcessor()
        
        # Create test PDF data similar to what would be extracted
        test_pdf_data = {
            'request_number': 'SPE4A1-TEST-QPL',
            'nsn': '5331012715999',  # Different NSN to avoid conflicts
            'quantity': '100',
            'unit': 'EA',
            'mfr': 'MOOG INC 94697 P/N 58532-012',  # This should create QPL entries
            'delivery_days': '180',
            'fob': 'Origin',
            'packaging_type': 'Standard',
            'iso': 'NO',
            'sampling': 'NO',
            'buyer': 'Test Buyer',
            'email': 'test.buyer@dla.mil',
            'product_description': 'Test Product for QPL Integration',
            'close_date': '2025-12-31',
            'payment_history': 'Test payment history',
            'skipped': False,
            'office': 'DLA Troop Support',
            'division': 'Subsistence',
            'address': '700 Robbins Avenue, Philadelphia, PA 19111'
        }
        
        print("=== TESTING PDF QPL INTEGRATION ===")
        print(f"Test data: NSN={test_pdf_data['nsn']}, MFR={test_pdf_data['mfr']}")
        
        # Process the opportunity (this should create QPL entries)
        opportunity_id = processor.create_crm_opportunity(test_pdf_data, "test_pdf.pdf")
        
        if opportunity_id:
            print(f"✓ Created opportunity {opportunity_id}")
            
            # Check results for QPL creation
            if hasattr(processor.results, 'created_qpl_entries'):
                print(f"✓ QPL processing result: {processor.results.get('created_qpl_entries', 0)} entries created")
            
            # Verify the QPL data was actually created
            import sqlite3
            conn = sqlite3.connect('data/crm.db')
            cursor = conn.cursor()
            
            # Check for QPL account
            cursor.execute('SELECT COUNT(*) FROM accounts WHERE type = ? AND cage = ?', ('QPL', '94697'))
            qpl_accounts = cursor.fetchone()[0]
            print(f"✓ QPL accounts for CAGE 94697: {qpl_accounts}")
            
            # Check for product manufacturer entries
            cursor.execute('SELECT COUNT(*) FROM product_manufacturers WHERE cage_code = ?', ('94697',))
            qpl_entries = cursor.fetchone()[0]
            print(f"✓ Product manufacturer entries for CAGE 94697: {qpl_entries}")
            
            # Check for the product
            cursor.execute('SELECT COUNT(*) FROM products WHERE nsn = ?', (test_pdf_data['nsn'],))
            products = cursor.fetchone()[0]
            print(f"✓ Products with NSN {test_pdf_data['nsn']}: {products}")
            
            conn.close()
        else:
            print("❌ Failed to create opportunity")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_qpl_integration()
