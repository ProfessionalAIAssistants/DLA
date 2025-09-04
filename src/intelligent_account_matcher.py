"""
Intelligent Account Management for DLA CRM
Prevents duplicate account creation by checking parent-child relationships
"""
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from core import crm_data
    crm_data = crm_data.crm_data
except ImportError:
    # Fallback import method
    import sqlite3
    print("[IntelligentAccountMatcher] Warning: Could not import crm_data module, using direct database access")
    
    class DirectCRMData:
        def __init__(self):
            self.db_path = Path(__file__).parent / "data" / "crm.db"
        
        def get_accounts(self, filters=None):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if filters and 'name' in filters:
                cursor.execute("SELECT * FROM accounts WHERE name = ?", (filters['name'],))
            else:
                cursor.execute("SELECT * FROM accounts")
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
        
        def get_account_by_id(self, account_id):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                return dict(zip(columns, row))
            conn.close()
            return None
        
        def create_account(self, **kwargs):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build insert query dynamically
            columns = list(kwargs.keys())
            placeholders = ['?' for _ in columns]
            values = list(kwargs.values())
            
            query = f"INSERT INTO accounts ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            
            account_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return account_id
    
    crm_data = DirectCRMData()

class IntelligentAccountMatcher:
    """
    Intelligent account matching that respects parent-child relationships
    Prevents creating duplicate accounts like "DLA LAND AND MARITIME FLUID HANDLING DIVISION"
    when "DLA LAND AND MARITIME" (parent) and "FLUID HANDLING DIVISION" (child) already exist
    """
    
    def __init__(self):
        self.debug = True
    
    def log(self, message):
        """Debug logging"""
        if self.debug:
            print(f"[AccountMatcher] {message}")
    
    def normalize_name(self, name):
        """Normalize account name for comparison"""
        if not name:
            return ""
        return name.upper().strip().replace("  ", " ")
    
    def find_parent_child_match(self, office, division):
        """
        Find existing parent-child account structure
        Returns (parent_account_id, child_account_id) or (None, None)
        """
        if not office or not division:
            return None, None
        
        office_norm = self.normalize_name(office)
        division_norm = self.normalize_name(division)
        
        # Get all accounts to check relationships
        all_accounts = crm_data.get_accounts()
        
        parent_account = None
        child_account = None
        
        # Find potential parent account (exact match for office)
        for account in all_accounts:
            account_name_norm = self.normalize_name(account.get('name', ''))
            
            # Check for exact office match as parent
            if account_name_norm == office_norm:
                parent_account = account
                self.log(f"Found potential parent account: {account['name']} (ID: {account['id']})")
                break
        
        # If parent found, look for child account with this parent
        if parent_account:
            parent_name = parent_account['name']
            
            for account in all_accounts:
                account_name_norm = self.normalize_name(account.get('name', ''))
                parent_co_norm = self.normalize_name(account.get('parent_co', ''))
                
                # Check if this is a child of our parent and matches the division
                if (parent_co_norm == office_norm and 
                    (division_norm in account_name_norm or account_name_norm == division_norm)):
                    child_account = account
                    self.log(f"Found child account: {account['name']} (ID: {account['id']}) with parent: {account['parent_co']}")
                    break
        
        return (parent_account['id'] if parent_account else None, 
                child_account['id'] if child_account else None)
    
    def find_exact_combined_match(self, office, division):
        """
        Find existing account that matches the combined office+division name
        This is to detect the problematic accounts we want to avoid creating
        """
        if not office or not division:
            return None
        
        # Create the problematic combined name patterns
        combined_patterns = [
            f"{office} {division}",
            f"{office}  {division}",  # With double space
            f"{division} {office}",
            f"{office} - {division}",
            f"{office}-{division}"
        ]
        
        all_accounts = crm_data.get_accounts()
        
        for pattern in combined_patterns:
            pattern_norm = self.normalize_name(pattern)
            
            for account in all_accounts:
                account_name_norm = self.normalize_name(account.get('name', ''))
                if account_name_norm == pattern_norm:
                    self.log(f"Found existing combined account (problematic): {account['name']} (ID: {account['id']})")
                    return account['id']
        
        return None
    
    def smart_account_match(self, office, division, address=None):
        """
        Intelligently match or create accounts respecting parent-child relationships
        
        Returns:
            account_id: The ID of the account to use (child account if parent-child exists)
        
        Logic:
        1. Check for existing parent-child structure
        2. If found, return child account ID
        3. If only parent exists, create child and return child ID
        4. If neither exists, create both and return child ID
        5. Avoid creating combined names like "DLA LAND AND MARITIME FLUID HANDLING DIVISION"
        """
        
        if not office and not division:
            self.log("No office or division provided")
            return None
        
        # Use office as fallback if no division
        if not division:
            division = office
        
        # Use division as fallback if no office  
        if not office:
            office = division
        
        self.log(f"Processing: Office='{office}', Division='{division}'")
        
        # 1. Check for existing parent-child structure
        parent_id, child_id = self.find_parent_child_match(office, division)
        
        if parent_id and child_id:
            self.log(f"Using existing parent-child structure: Parent={parent_id}, Child={child_id}")
            return child_id
        
        # 2. Check if problematic combined account already exists
        combined_id = self.find_exact_combined_match(office, division)
        if combined_id:
            self.log(f"WARNING: Found problematic combined account {combined_id}. This should be fixed!")
            return combined_id
        
        # 3. If only parent exists, create child
        if parent_id and not child_id:
            self.log(f"Parent exists (ID: {parent_id}), creating child account for: {division}")
            
            child_data = {
                'name': division,
                'parent_co': office,
                'type': 'Customer',
                'summary': f"Division of {office}",
                'billing_address': address or '',
                'is_active': True
            }
            
            try:
                child_id = crm_data.create_account(**child_data)
                self.log(f"Created child account: {division} (ID: {child_id}) with parent: {office}")
                return child_id
            except Exception as e:
                self.log(f"Failed to create child account: {e}")
                return parent_id  # Fallback to parent
        
        # 4. If neither parent nor child exists, create both
        if not parent_id and not child_id:
            self.log(f"Creating new parent-child structure: Parent='{office}', Child='{division}'")
            
            # Create parent first
            parent_data = {
                'name': office,
                'type': 'Customer',
                'summary': f"Defense Logistics Agency - {office}",
                'billing_address': address or '',
                'is_active': True
            }
            
            try:
                parent_id = crm_data.create_account(**parent_data)
                self.log(f"Created parent account: {office} (ID: {parent_id})")
                
                # Only create child if division is different from office
                if self.normalize_name(division) != self.normalize_name(office):
                    child_data = {
                        'name': division,
                        'parent_co': office,
                        'type': 'Customer', 
                        'summary': f"Division of {office}",
                        'billing_address': address or '',
                        'is_active': True
                    }
                    
                    child_id = crm_data.create_account(**child_data)
                    self.log(f"Created child account: {division} (ID: {child_id}) with parent: {office}")
                    return child_id
                else:
                    # Division same as office, just return parent
                    return parent_id
                    
            except Exception as e:
                self.log(f"Failed to create account structure: {e}")
                return None
        
        # 5. Fallback: if we have child but no parent (shouldn't happen, but just in case)
        if child_id and not parent_id:
            self.log(f"Using existing child account: {child_id}")
            return child_id
        
        self.log("No account match found or created")
        return None

# Global instance for easy import
intelligent_account_matcher = IntelligentAccountMatcher()
