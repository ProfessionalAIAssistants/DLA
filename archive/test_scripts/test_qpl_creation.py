#!/usr/bin/env python3
"""Test QPL account creation with new account type"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path('.').resolve()))

from mfr_parser import MFRParser
import sqlite3

def test_qpl_account_creation():
    """Test that new QPL accounts are created with QPL type"""
    print('=== TESTING QPL ACCOUNT CREATION WITH NEW TYPE ===')
    
    # Create a test parser
    parser = MFRParser()
    
    # Test creating a new manufacturer account
    test_mfr = 'TEST COMPANY INC 12345 P/N ABC-123'
    print(f'Testing manufacturer string: {test_mfr}')
    
    try:
        result = parser.process_opportunity_mfr(
            opportunity_id=1,  # Use existing opportunity
            nsn='1234567890123',
            mfr_string=test_mfr,
            product_name='Test Product',
            description='Test Description'
        )
        
        print(f'Result: {result}')
        
        if result.get('success'):
            # Check the created account type
            conn = sqlite3.connect('data/crm.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, type, cage FROM accounts WHERE cage = ?', ('12345',))
            account = cursor.fetchone()
            if account:
                print(f'✓ Created account: ID {account[0]}, Name: {account[1]}, Type: {account[2]}, CAGE: {account[3]}')
                
                if account[2] == 'QPL':
                    print('✓ Account correctly created with QPL type!')
                else:
                    print(f'❌ Account created with wrong type: {account[2]} (expected QPL)')
            else:
                print('❌ Account not found')
            
            conn.close()
        else:
            print(f'❌ Failed to process QPL: {result.get("error")}')
            
    except Exception as e:
        print(f'❌ Error during test: {e}')

if __name__ == '__main__':
    test_qpl_account_creation()
