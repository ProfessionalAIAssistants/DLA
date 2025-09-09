#!/usr/bin/env python3
"""
MFR Parser for QPL Data
Parses manufacturer strings and creates QPL entries
"""

import re
import sqlite3
import os
from typing import List, Dict, Tuple

class MFRParser:
    """Parse manufacturer strings and manage QPL data"""
    
    def __init__(self, db_path: str = 'data/crm.db'):
        self.db_path = db_path
        
    def parse_mfr_string(self, mfr_string: str) -> List[Dict[str, str]]:
        """
        Parse MFR string to extract manufacturer info
        
        Examples:
        - "MOOG INC 94697 P/N 58532-012"
        - "PARKER-HANNIFIN CORPORATION 83259 P/N 708009-12 NORTHROP GRUMMAN SYSTEMS CORPORATION 26512 P/N GS570CU12"
        """
        if not mfr_string:
            return []
            
        # Pattern to match manufacturer entries
        # Looks for: [MANUFACTURER NAME] [CAGE CODE] P/N [PART NUMBER]
        pattern = r'([A-Z][A-Z\s\-&.,()]+?)\s+(\d{5})\s+P/N\s+([\w\-\/]+)'
        
        matches = re.findall(pattern, mfr_string)
        
        manufacturers = []
        for match in matches:
            manufacturer_name = match[0].strip()
            cage_code = match[1].strip()
            part_number = match[2].strip()
            
            manufacturers.append({
                'manufacturer_name': manufacturer_name,
                'cage_code': cage_code,
                'part_number': part_number
            })
        
        return manufacturers
    
    def create_or_update_qpl_account(self, manufacturer_name: str, cage_code: str) -> int:
        """Create or update QPL account for manufacturer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if account exists by CAGE code (more reliable than name)
            cursor.execute("""
                SELECT id, name FROM accounts WHERE cage = ? AND type = 'Vendor'
            """, (cage_code,))
            
            result = cursor.fetchone()
            
            if result:
                account_id, existing_name = result
                # Update name if it's different (use the most recent/complete version)
                if existing_name != manufacturer_name:
                    cursor.execute("""
                        UPDATE accounts 
                        SET name = ? 
                        WHERE id = ?
                    """, (manufacturer_name, account_id))
                    print(f"  Updated account {account_id}: {existing_name} -> {manufacturer_name}")
                return account_id
            else:
                # Create new Vendor account for QPL manufacturer
                cursor.execute("""
                    INSERT INTO accounts (name, type, cage, created_date, is_active)
                    VALUES (?, 'Vendor', ?, CURRENT_TIMESTAMP, 1)
                """, (manufacturer_name, cage_code))
                
                account_id = cursor.lastrowid
                print(f"  Created QPL account {account_id}: {manufacturer_name} (CAGE: {cage_code})")
                conn.commit()
                return account_id
                
        except Exception as e:
            print(f"  ❌ Error creating/updating QPL account: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def create_or_update_product(self, nsn: str, product_name: str = None, description: str = None) -> int:
        """Create or update product by NSN"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if product exists by NSN
            cursor.execute("SELECT id, name FROM products WHERE nsn = ?", (nsn,))
            result = cursor.fetchone()
            
            if result:
                product_id, existing_name = result
                # Update name and description if provided and different
                updates = []
                params = []
                
                if product_name and existing_name != product_name:
                    updates.append("name = ?")
                    params.append(product_name)
                
                if description:
                    updates.append("description = ?")
                    params.append(description)
                
                if updates:
                    updates.append("modified_date = CURRENT_TIMESTAMP")
                    params.append(product_id)
                    
                    cursor.execute(f"""
                        UPDATE products 
                        SET {', '.join(updates)}
                        WHERE id = ?
                    """, params)
                    print(f"  Updated product {product_id}: {nsn}")
                
                return product_id
            else:
                # Create new product
                cursor.execute("""
                    INSERT INTO products (nsn, name, description, is_active, created_date, modified_date)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (nsn, product_name or f"Product {nsn}", description))
                
                product_id = cursor.lastrowid
                print(f"  Created product {product_id}: {nsn}")
                conn.commit()
                return product_id
                
        except Exception as e:
            print(f"  ❌ Error creating/updating product: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def create_qpl_entry(self, product_id: int, account_id: int, manufacturer_name: str, cage_code: str, part_number: str) -> int:
        """Create QPL entry linking product to manufacturer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if QPL entry already exists
            cursor.execute("""
                SELECT id FROM product_manufacturers 
                WHERE product_id = ? AND account_id = ? AND part_number = ?
            """, (product_id, account_id, part_number))
            
            result = cursor.fetchone()
            
            if result:
                print(f"  QPL entry already exists: {manufacturer_name} P/N {part_number}")
                return result[0]
            else:
                # Create new QPL entry
                cursor.execute("""
                    INSERT INTO product_manufacturers 
                    (product_id, account_id, manufacturer_name, cage_code, part_number, created_date, modified_date)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (product_id, account_id, manufacturer_name, cage_code, part_number))
                
                qpl_id = cursor.lastrowid
                print(f"  Created QPL entry {qpl_id}: {manufacturer_name} P/N {part_number}")
                conn.commit()
                return qpl_id
                
        except Exception as e:
            print(f"  ❌ Error creating QPL entry: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def process_opportunity_mfr(self, opportunity_id: int, nsn: str, mfr_string: str, product_name: str = None, description: str = None) -> Dict:
        """Process MFR string for an opportunity and create QPL entries"""
        print(f"\n🔄 Processing Opportunity {opportunity_id}")
        print(f"   NSN: {nsn}")
        print(f"   MFR: {mfr_string}")
        
        # Parse manufacturers from MFR string
        manufacturers = self.parse_mfr_string(mfr_string)
        
        if not manufacturers:
            print("  ⚠️ No manufacturers found in MFR string")
            return {'success': False, 'message': 'No manufacturers parsed'}
        
        print(f"  Found {len(manufacturers)} manufacturer(s)")
        
        # Create or update product
        product_id = self.create_or_update_product(nsn, product_name, description)
        if not product_id:
            return {'success': False, 'message': 'Failed to create/update product'}
        
        # Process each manufacturer
        qpl_entries = []
        for mfr in manufacturers:
            print(f"  Processing: {mfr['manufacturer_name']} (CAGE: {mfr['cage_code']}) P/N {mfr['part_number']}")
            
            # Create or update QPL account
            account_id = self.create_or_update_qpl_account(mfr['manufacturer_name'], mfr['cage_code'])
            if not account_id:
                continue
                
            # Create QPL entry
            qpl_id = self.create_qpl_entry(
                product_id, account_id, 
                mfr['manufacturer_name'], mfr['cage_code'], mfr['part_number']
            )
            
            if qpl_id:
                qpl_entries.append(qpl_id)
        
        return {
            'success': True,
            'product_id': product_id,
            'qpl_entries': qpl_entries,
            'manufacturers_count': len(manufacturers)
        }

def test_parser():
    """Test the MFR parser with sample data"""
    parser = MFRParser()
    
    # Test cases
    test_cases = [
        "MOOG INC 94697 P/N 58532-012",
        "PARKER-HANNIFIN CORPORATION 83259 P/N 708009-12 NORTHROP GRUMMAN SYSTEMS CORPORATION 26512 P/N GS570CU12"
    ]
    
    for i, test_mfr in enumerate(test_cases, 1):
        print(f"\n=== TEST CASE {i} ===")
        manufacturers = parser.parse_mfr_string(test_mfr)
        print(f"Input: {test_mfr}")
        print(f"Parsed {len(manufacturers)} manufacturers:")
        for mfr in manufacturers:
            print(f"  - {mfr['manufacturer_name']} (CAGE: {mfr['cage_code']}) P/N {mfr['part_number']}")

if __name__ == "__main__":
    test_parser()
