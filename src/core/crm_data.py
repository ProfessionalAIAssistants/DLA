# CRM Data Access Layer
# Handles all database operations for the CRM system

from .crm_database import db
from datetime import datetime, date
import json

class CRMData:
    
    # ==================== ACCOUNTS ====================
    
    def create_account(self, **kwargs):
        """Create a new account"""
        fields = ['name', 'type', 'summary', 'detail', 'website', 'email', 'location',
                 'linkedin', 'parent_co', 'cage', 'image', 'video', 'is_active']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('name'):
            raise ValueError("Account name is required")
        
        # Set default values
        if 'is_active' not in valid_fields:
            valid_fields['is_active'] = True
        if 'created_date' not in valid_fields:
            valid_fields['created_date'] = 'CURRENT_TIMESTAMP'
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO accounts ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_accounts(self, filters=None, limit=None):
        """Get accounts with optional filters"""
        query = "SELECT * FROM accounts WHERE is_active = 1"
        params = []
        
        if filters:
            if filters.get('name'):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
            if filters.get('type'):
                query += " AND type = ?"
                params.append(filters['type'])
            if filters.get('location'):
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
        
        query += " ORDER BY name"
        if limit:
            query += f" LIMIT {limit}"
        
        accounts = db.execute_query(query, params if params else None)
        
        # Add calculated fields to each account
        for account in accounts:
            self._enhance_account_data(account)
        
        return accounts
    
    def get_account_by_id(self, account_id):
        """Get specific account by ID"""
        query = "SELECT * FROM accounts WHERE id = ? AND is_active = 1"
        results = db.execute_query(query, [account_id])
        return results[0] if results else None
    
    def update_account(self, account_id, **kwargs):
        """Update an existing account"""
        # Updated to match actual table schema
        fields = ['name', 'type', 'summary', 'detail', 'website', 'email', 'location', 
                 'linkedin', 'parent_co', 'cage', 'image', 'video']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return 0
        
        # Remove modified_date since accounts table doesn't have this column
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        
        query = f"UPDATE accounts SET {set_clause} WHERE id = ?"
        params = list(valid_fields.values()) + [account_id]
        
        return db.execute_update(query, params)
    
    def delete_account(self, account_id):
        """Delete an account"""
        return db.execute_update("DELETE FROM accounts WHERE id = ?", [account_id])
    
    def delete_contact(self, contact_id):
        """Delete a contact"""
        return db.execute_update("DELETE FROM contacts WHERE id = ?", [contact_id])
    
    # ==================== CONTACTS ====================
    
    def create_contact(self, **kwargs):
        """Create a new contact"""
        fields = ['first_name', 'last_name', 'title', 'email', 'phone', 'mobile', 
                 'account_id', 'department', 'reports_to', 'lead_source', 'address', 
                 'description', 'owner', 'is_active']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        # Handle name field by splitting into first_name and last_name
        if 'name' in kwargs and kwargs['name']:
            name_parts = kwargs['name'].strip().split(' ', 1)
            valid_fields['first_name'] = name_parts[0]
            if len(name_parts) > 1:
                valid_fields['last_name'] = name_parts[1]
            else:
                valid_fields['last_name'] = ''
        
        if not valid_fields.get('first_name'):
            raise ValueError("Contact first name is required")
        
        # Set default values
        if 'is_active' not in valid_fields:
            valid_fields['is_active'] = True
        
        # Remove the duplicate check for now to avoid errors
        # TODO: Fix duplicate checking logic later
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO contacts ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_contacts(self, filters=None, limit=None):
        """Get contacts with optional filters"""
        query = """
            SELECT c.*, 
                   CASE 
                       WHEN c.first_name IS NOT NULL AND c.last_name IS NOT NULL 
                       THEN c.first_name || ' ' || c.last_name
                       WHEN c.first_name IS NOT NULL 
                       THEN c.first_name
                       WHEN c.last_name IS NOT NULL 
                       THEN c.last_name
                       ELSE 'Unknown Contact'
                   END as name,
                   a.name as account_name 
            FROM contacts c 
            LEFT JOIN accounts a ON c.account_id = a.id 
            WHERE c.is_active = 1
        """
        params = []
        
        if filters:
            if filters.get('name'):
                query += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR (c.first_name || ' ' || c.last_name) LIKE ?)"
                search_term = f"%{filters['name']}%"
                params.extend([search_term, search_term, search_term])
            if filters.get('account_id'):
                query += " AND c.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('email'):
                query += " AND c.email LIKE ?"
                params.append(f"%{filters['email']}%")
        
        query += " ORDER BY c.first_name, c.last_name"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_contacts_by_account(self, account_id):
        """Get all contacts for a specific account"""
        return self.get_contacts(filters={'account_id': account_id})
    
    def get_contact_by_id(self, contact_id):
        """Get specific contact by ID"""
        query = """
            SELECT c.*, 
                   CASE 
                       WHEN c.first_name IS NOT NULL AND c.last_name IS NOT NULL 
                       THEN c.first_name || ' ' || c.last_name
                       WHEN c.first_name IS NOT NULL 
                       THEN c.first_name
                       WHEN c.last_name IS NOT NULL 
                       THEN c.last_name
                       ELSE 'Unknown Contact'
                   END as name,
                   a.name as account_name 
            FROM contacts c 
            LEFT JOIN accounts a ON c.account_id = a.id 
            WHERE c.id = ? AND c.is_active = 1
        """
        results = db.execute_query(query, [contact_id])
        return results[0] if results else None
    
    def update_contact(self, contact_id, **kwargs):
        """Update an existing contact"""
        # Updated to match actual table schema
        fields = ['first_name', 'last_name', 'name', 'title', 'email', 'phone', 'mobile', 
                 'account_id', 'department', 'reports_to', 'lead_source', 'address', 
                 'description', 'owner', 'quality', 'status', 'frequency_days', 
                 'last_communication', 'next_communication']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return 0
        
        # Check for duplicates if name or email is being updated
        if valid_fields.get('name') or valid_fields.get('email'):
            # Get current contact to use existing values if not provided
            current_contact = self.get_contact_by_id(contact_id)
            if not current_contact:
                raise ValueError("Contact not found")
            
            name = valid_fields.get('name', current_contact['name'])
            email = valid_fields.get('email', current_contact['email'])
            
            duplicates = self.check_contact_duplicate(name, email, exclude_id=contact_id)
            if duplicates:
                error_messages = [dup['message'] for dup in duplicates]
                raise ValueError("Duplicate contact found: " + "; ".join(error_messages))
        
        valid_fields['modified_date'] = datetime.now()
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        
        query = f"UPDATE contacts SET {set_clause} WHERE id = ?"
        params = list(valid_fields.values()) + [contact_id]
        
        return db.execute_update(query, params)
    
    # ==================== PRODUCTS ====================
    
    def create_product(self, **kwargs):
        """Create a new product"""
        fields = ['name', 'product_code', 'nsn', 'fsc', 'description', 'category',
                 'family', 'unit_price', 'cost_price', 'list_price', 'manufacturer',
                 'part_number']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        # Validate required fields
        if not valid_fields.get('name'):
            raise ValueError("Product name is required")
        
        if not valid_fields.get('nsn'):
            raise ValueError("NSN (National Stock Number) is required and cannot be empty")
        
        # Validate NSN format (basic validation)
        nsn = valid_fields['nsn'].strip()
        if not nsn:
            raise ValueError("NSN (National Stock Number) cannot be empty or just whitespace")
        
        # Update the NSN field with the trimmed value
        valid_fields['nsn'] = nsn
        
        # Check for NSN duplicates
        duplicates = self.check_product_duplicate(nsn)
        if duplicates:
            error_messages = [dup['message'] for dup in duplicates]
            raise ValueError("Duplicate product found: " + "; ".join(error_messages))
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO products ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_products(self, filters=None, limit=None):
        """Get products with optional filters"""
        query = "SELECT * FROM products WHERE is_active = 1"
        params = []
        
        if filters:
            if filters.get('search'):
                # Search NSN, name, description, and FSC
                query += " AND (nsn LIKE ? OR name LIKE ? OR description LIKE ? OR fsc LIKE ?)"
                search_param = f"%{filters['search']}%"
                params.extend([search_param, search_param, search_param, search_param])
            if filters.get('name'):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
            if filters.get('nsn'):
                query += " AND nsn = ?"
                params.append(filters['nsn'])
            if filters.get('fsc'):
                query += " AND fsc = ?"
                params.append(filters['fsc'])
            if filters.get('manufacturer'):
                query += " AND manufacturer LIKE ?"
                params.append(f"%{filters['manufacturer']}%")
            if filters.get('category'):
                query += " AND category = ?"
                params.append(filters['category'])
        
        # Order by NSN first, then name
        query += " ORDER BY nsn, name"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_product_by_id(self, product_id):
        """Get specific product by ID"""
        query = "SELECT * FROM products WHERE id = ? AND is_active = 1"
        results = db.execute_query(query, [product_id])
        return results[0] if results else None
    
    def update_product(self, product_id, **kwargs):
        """Update an existing product"""
        fields = ['name', 'product_code', 'nsn', 'fsc', 'description', 'category',
                 'family', 'unit_price', 'cost_price', 'list_price', 'manufacturer',
                 'part_number']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return 0
        
        # Validate NSN if it's being updated
        if 'nsn' in valid_fields:
            nsn = valid_fields['nsn']
            if not nsn or not nsn.strip():
                raise ValueError("NSN (National Stock Number) cannot be empty or just whitespace")
            
            # Update the NSN field with the trimmed value
            valid_fields['nsn'] = nsn.strip()
            
            # Check for NSN duplicates
            duplicates = self.check_product_duplicate(valid_fields['nsn'], exclude_id=product_id)
            if duplicates:
                error_messages = [dup['message'] for dup in duplicates]
                raise ValueError("Duplicate product found: " + "; ".join(error_messages))
        
        valid_fields['modified_date'] = datetime.now()
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        
        query = f"UPDATE products SET {set_clause} WHERE id = ?"
        params = list(valid_fields.values()) + [product_id]
        
        return db.execute_update(query, params)

    def add_comparable_product(self, product_id, related_product_id, notes=None):
        """Add a comparable product relationship"""
        query = """
            INSERT OR IGNORE INTO product_relationships 
            (product_id, related_product_id, relationship_type, notes, created_date)
            VALUES (?, ?, 'comparable', ?, ?)
        """
        return db.execute_update(query, [product_id, related_product_id, notes, datetime.now()])
    
    def remove_comparable_product(self, product_id, related_product_id):
        """Remove a comparable product relationship"""
        query = """
            DELETE FROM product_relationships 
            WHERE (product_id = ? AND related_product_id = ?) 
            OR (product_id = ? AND related_product_id = ?)
        """
        return db.execute_update(query, [product_id, related_product_id, related_product_id, product_id])
    
    def get_comparable_products(self, product_id):
        """Get all comparable products for a given product"""
        query = """
            SELECT p.*, pr.notes, pr.created_date as relationship_date
            FROM product_relationships pr
            JOIN products p ON (
                CASE 
                    WHEN pr.product_id = ? THEN p.id = pr.related_product_id
                    ELSE p.id = pr.product_id
                END
            )
            WHERE (pr.product_id = ? OR pr.related_product_id = ?)
            AND pr.relationship_type = 'comparable'
            AND p.is_active = 1
            ORDER BY p.name
        """
        return db.execute_query(query, [product_id, product_id, product_id])
    
    def add_product_vendor(self, product_id, vendor_id, **kwargs):
        """Add a vendor relationship to a product"""
        fields = ['vendor_part_number', 'lead_time', 'minimum_order_quantity', 
                 'price_per_unit', 'preferred_vendor', 'last_purchase_date', 'notes']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        valid_fields['product_id'] = product_id
        valid_fields['vendor_id'] = vendor_id
        valid_fields['created_date'] = datetime.now()
        valid_fields['modified_date'] = datetime.now()
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT OR REPLACE INTO product_vendors ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_product_vendors(self, product_id):
        """Get all vendors for a specific product"""
        try:
            query = """
                SELECT pv.*, a.name as vendor_name, a.cage as vendor_cage
                FROM product_vendors pv
                JOIN accounts a ON pv.vendor_id = a.id
                WHERE pv.product_id = ? AND a.is_active = 1
                ORDER BY pv.preferred_vendor DESC, a.name
            """
            return db.execute_query(query, [product_id])
        except Exception as e:
            # Table doesn't exist yet - return empty list
            print(f"Warning: product_vendors table not found: {e}")
            return []
    
    def get_vendor_products(self, vendor_id):
        """Get all products for a specific vendor"""
        query = """
            SELECT pv.*, p.name as product_name, p.nsn, p.manufacturer
            FROM product_vendors pv
            JOIN products p ON pv.product_id = p.id
            WHERE pv.vendor_id = ? AND p.is_active = 1
            ORDER BY p.name
        """
        return db.execute_query(query, [vendor_id])
    
    def update_product_vendor(self, product_id, vendor_id, **kwargs):
        """Update a product-vendor relationship"""
        fields = ['vendor_part_number', 'lead_time', 'minimum_order_quantity', 
                 'price_per_unit', 'preferred_vendor', 'last_purchase_date', 'notes']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return False
        
        valid_fields['modified_date'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        query = f"UPDATE product_vendors SET {set_clause} WHERE product_id = ? AND vendor_id = ?"
        
        params = list(valid_fields.values()) + [product_id, vendor_id]
        return db.execute_update(query, params)
    
    def get_product_rfqs(self, product_id):
        """Get all RFQs/Quotes related to a product"""
        query = """
            SELECT r.*, a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM rfqs r
            LEFT JOIN accounts a ON r.account_id = a.id
            LEFT JOIN contacts c ON r.contact_id = c.id
            WHERE r.product_id = ?
            ORDER BY r.close_date DESC, r.created_date DESC
        """
        return db.execute_query(query, [product_id])
    
    def get_product_opportunities(self, product_id):
        """Get all opportunities related to a product"""
        query = """
            SELECT o.*, a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            WHERE o.product_id = ?
            ORDER BY o.close_date DESC, o.created_date DESC
        """
        return db.execute_query(query, [product_id])
    
    def add_payment_history(self, **kwargs):
        """Add a payment history record"""
        fields = ['product_id', 'vendor_id', 'opportunity_id', 'rfq_id', 'payment_date',
                 'amount', 'payment_method', 'payment_reference', 'invoice_number',
                 'purchase_order_number', 'quantity', 'unit_price', 'payment_status',
                 'notes', 'created_by']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('payment_date') or not valid_fields.get('amount'):
            raise ValueError("Payment date and amount are required")
        
        valid_fields['created_date'] = datetime.now()
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO payment_history ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_payment_history(self, filters=None, limit=None):
        """Get payment history with optional filters"""
        query = """
            SELECT ph.*, 
                   p.name as product_name, p.nsn,
                   a.name as vendor_name,
                   o.name as opportunity_name
            FROM payment_history ph
            LEFT JOIN products p ON ph.product_id = p.id
            LEFT JOIN accounts a ON ph.vendor_id = a.id
            LEFT JOIN opportunities o ON ph.opportunity_id = o.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('product_id'):
                query += " AND ph.product_id = ?"
                params.append(filters['product_id'])
            if filters.get('vendor_id'):
                query += " AND ph.vendor_id = ?"
                params.append(filters['vendor_id'])
            if filters.get('start_date'):
                query += " AND ph.payment_date >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND ph.payment_date <= ?"
                params.append(filters['end_date'])
            if filters.get('payment_status'):
                query += " AND ph.payment_status = ?"
                params.append(filters['payment_status'])
        
        query += " ORDER BY ph.payment_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_product_payment_history(self, product_id):
        """Get payment history for a specific product"""
        return self.get_payment_history({'product_id': product_id})
    
    def get_product_summary(self, product_id):
        """Get comprehensive product summary with all relationships"""
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        summary = dict(product)
        summary['comparable_products'] = self.get_comparable_products(product_id)
        summary['vendors'] = self.get_product_vendors(product_id)
        summary['payment_history'] = self.get_product_payment_history(product_id)
        summary['qpl_entries'] = self.get_qpl_for_product(product_id)
        
        # Get related opportunities and RFQs
        summary['opportunities'] = db.execute_query("""
            SELECT id, name, stage, state, bid_price, close_date
            FROM opportunities WHERE product_id = ?
            ORDER BY close_date DESC
        """, [product_id])
        
        summary['rfqs'] = db.execute_query("""
            SELECT id, quote, lead_time, effective_date
            FROM rfqs WHERE product_id = ?
            ORDER BY effective_date DESC
        """, [product_id])
        
        return summary

    # ==================== OPPORTUNITIES ====================
    
    def create_opportunity(self, **kwargs):
        """Create a new opportunity with comprehensive field support"""
        fields = ['stage', 'state', 'bid_price', 'purchase_costs', 'packaging_shipping',
                 'bid_date', 'close_date', 'quantity', 'unit', 'mfr', 'fob', 
                 'packaging_type', 'iso', 'sampling', 'days_aod', 'packaging_info',
                 'payment', 'buyer', 'skipped', 'document', 'product_id', 
                 'contact_id', 'account_id', 'name', 'description', 'delivery_days', 'amount']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        # Calculate profit if we have the required fields
        if all(field in valid_fields for field in ['bid_price', 'purchase_costs', 'packaging_shipping', 'quantity']):
            profit = (valid_fields['bid_price'] - valid_fields['purchase_costs'] - valid_fields['packaging_shipping']) * valid_fields['quantity']
            valid_fields['profit'] = profit
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO opportunities ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_opportunities(self, filters=None, limit=None):
        """Get opportunities with calculated fields and relationships"""
        query = """
            SELECT o.*, 
                   a.name as account_name, 
                   (c.first_name || ' ' || c.last_name) as contact_name, 
                   p.name as product_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('stage'):
                query += " AND o.stage = ?"
                params.append(filters['stage'])
            if filters.get('state'):
                # Handle state filter based on stage
                state = filters['state']
                if state == 'Won':
                    query += " AND o.stage = 'Closed Won'"
                elif state == 'Bid Lost':
                    query += " AND o.stage = 'Closed Lost'"
                elif state == 'Active':
                    query += " AND o.stage NOT IN ('Closed Won', 'Closed Lost')"
            if filters.get('account_id'):
                query += " AND o.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('search'):
                query += " AND (o.name LIKE ? OR o.description LIKE ?)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
                
            # Comment out these filters that don't exist in the schema
            # Uncomment and update the database schema if needed
            # if filters.get('buyer'):
            #     query += " AND o.buyer LIKE ?"
            #     params.append(f"%{filters['buyer']}%")
            # if filters.get('mfr'):
            #     query += " AND o.mfr LIKE ?"
            #     params.append(f"%{filters['mfr']}%")
            # if filters.get('iso'):
            #     query += " AND o.iso = ?"
            #     params.append(filters['iso'])
            # if filters.get('fob'):
            #     query += " AND o.fob = ?"
            #     params.append(filters['fob'])
            # if filters.get('packaging_type'):
            #     query += " AND o.packaging_type = ?"
            #     params.append(filters['packaging_type'])
        
        query += " ORDER BY o.close_date ASC, o.bid_date DESC, o.created_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        opportunities = db.execute_query(query, params if params else None)
        
        # Add calculated fields to each opportunity
        for opportunity in opportunities:
            self._enhance_opportunity_data(opportunity)
        
        return opportunities
    
    def get_opportunities_by_date(self, date_str):
        """Get opportunities created on a specific date"""
        query = """
            SELECT o.*, 
                   a.name as account_name, 
                   (c.first_name || ' ' || c.last_name) as contact_name, 
                   p.name as product_name,
                   CASE 
                       WHEN o.close_date < date('now') AND o.stage NOT IN ('Closed Won', 'Closed Lost') THEN 'Overdue'
                       ELSE 'Active'
                   END as status_indicator
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE date(o.created_date) = ?
            ORDER BY o.created_date DESC
        """
        return db.execute_query(query, [date_str])
    
    def update_opportunity(self, opportunity_id, **kwargs):
        """Update an opportunity with automatic profit calculation"""
        valid_fields = {k: v for k, v in kwargs.items() if v is not None}
        
        if valid_fields:
            # Add modified_date timestamp
            valid_fields['modified_date'] = datetime.now().isoformat()
            
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
            query = f"UPDATE opportunities SET {set_clause} WHERE id = ?"
            params = list(valid_fields.values()) + [opportunity_id]
            
            # Execute update
            result = db.execute_update(query, params)
            
            # Recalculate profit if financial fields were updated
            if any(field in kwargs for field in ['bid_price', 'purchase_costs', 'packaging_shipping', 'quantity']):
                self.recalculate_opportunity_profit(opportunity_id)
            
            return result
        return False
    
    def recalculate_opportunity_profit(self, opportunity_id):
        """Recalculate profit for an opportunity"""
        query = """
            UPDATE opportunities 
            SET profit = CASE 
                WHEN bid_price IS NOT NULL AND purchase_costs IS NOT NULL 
                     AND packaging_shipping IS NOT NULL AND quantity IS NOT NULL 
                THEN (bid_price - purchase_costs - packaging_shipping) * quantity
                ELSE NULL 
            END
            WHERE id = ?
        """
        return db.execute_update(query, [opportunity_id])
    
    def get_opportunity_by_id(self, opportunity_id):
        """Get a single opportunity by ID with relationships"""
        query = """
            SELECT o.*, 
                   a.name as account_name, 
                   (c.first_name || ' ' || c.last_name) as contact_name, 
                   p.name as product_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        """
        result = db.execute_query(query, [opportunity_id])
        return result[0] if result else None
    
    def delete_opportunity(self, opportunity_id):
        """Delete an opportunity"""
        return db.execute_update("DELETE FROM opportunities WHERE id = ?", [opportunity_id])
    
    def get_opportunity_stats(self):
        """Get opportunity statistics"""
        stats = {}
        
        # Basic counts
        result = db.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN state = 'Active' THEN 1 END) as active,
                COUNT(CASE WHEN state = 'Won' THEN 1 END) as won,
                COUNT(CASE WHEN state = 'Bid Lost' THEN 1 END) as lost,
                COUNT(CASE WHEN state = 'No Bid' THEN 1 END) as no_bid,
                COUNT(CASE WHEN close_date < date('now') AND state NOT IN ('Won', 'Bid Lost') THEN 1 END) as overdue,
                COUNT(CASE WHEN close_date = date('now') THEN 1 END) as due_today
            FROM opportunities
        """)
        
        if result:
            stats.update(result[0])
        
        # Financial stats
        financial = db.execute_query("""
            SELECT 
                SUM(CASE WHEN state = 'Active' THEN bid_price * quantity ELSE 0 END) as pipeline_value,
                SUM(CASE WHEN state = 'Won' THEN bid_price * quantity ELSE 0 END) as won_value,
                SUM(CASE WHEN state = 'Won' THEN profit ELSE 0 END) as total_profit,
                AVG(CASE WHEN state = 'Active' THEN bid_price ELSE NULL END) as avg_bid_price
            FROM opportunities
        """)
        
        if financial:
            stats.update(financial[0])
        
        return stats
    
    def get_rfq_stats(self):
        """Get RFQ-specific statistics"""
        rfq_stats = {}
        
        # RFQ stage counts
        result = db.execute_query("""
            SELECT 
                COUNT(CASE WHEN stage = 'RFQ Requested' THEN 1 END) as rfq_requested,
                COUNT(CASE WHEN stage = 'RFQ Received' THEN 1 END) as rfq_received,
                COUNT(CASE WHEN stage IN ('RFQ Requested', 'RFQ Received') THEN 1 END) as total_rfqs,
                COUNT(CASE WHEN stage = 'RFQ Received' AND state = 'Active' THEN 1 END) as active_rfqs,
                COUNT(CASE WHEN stage = 'Submit Bid' AND state = 'Active' THEN 1 END) as ready_to_bid,
                COUNT(CASE WHEN stage = 'Submit Bid' AND close_date <= date('now', '+7 days') AND state = 'Active' THEN 1 END) as due_soon
            FROM opportunities
        """)
        
        if result:
            rfq_stats.update(result[0])
        
        return rfq_stats
    
    def get_opportunities_by_stage(self):
        """Get opportunity counts by stage"""
        query = """
            SELECT stage, 
                   COUNT(*) as count,
                   SUM(bid_price * quantity) as total_value
            FROM opportunities 
            WHERE stage IS NOT NULL
            GROUP BY stage
            ORDER BY 
                CASE stage
                    WHEN 'Prospecting' THEN 1
                    WHEN 'RFQ Requested' THEN 2
                    WHEN 'RFQ Received' THEN 3
                    WHEN 'Submit Bid' THEN 4
                    WHEN 'Project Started' THEN 5
                    ELSE 6
                END
        """
        return db.execute_query(query)
    
    def get_opportunities_by_state(self):
        """Get opportunity counts by state"""
        query = """
            SELECT state, 
                   COUNT(*) as count,
                   SUM(bid_price * quantity) as total_value
            FROM opportunities 
            WHERE state IS NOT NULL
            GROUP BY state
            ORDER BY count DESC
        """
        return db.execute_query(query)
    
    def advance_opportunity_stage(self, opportunity_id):
        """Advance opportunity to next stage"""
        opportunity = self.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return False
        
        stage_progression = {
            'Prospecting': 'RFQ Requested',
            'RFQ Requested': 'RFQ Received', 
            'RFQ Received': 'Submit Bid',
            'Submit Bid': 'Project Started',
            'Project Started': 'Project Started'  # Final stage
        }
        
        current_stage = opportunity['stage']
        next_stage = stage_progression.get(current_stage)
        
        if next_stage:
            return self.update_opportunity(opportunity_id, stage=next_stage)
        return False
    
    def mark_opportunity_won(self, opportunity_id):
        """Mark opportunity as won"""
        return self.update_opportunity(opportunity_id, state='Won', close_date=date.today().isoformat())
    
    def mark_opportunity_lost(self, opportunity_id, reason=None):
        """Mark opportunity as lost"""
        updates = {'state': 'Bid Lost', 'close_date': date.today().isoformat()}
        if reason:
            updates['description'] = f"{updates.get('description', '')}\nLost Reason: {reason}".strip()
        return self.update_opportunity(opportunity_id, **updates)
    
    def get_opportunities_due_soon(self, days=7):
        """Get opportunities due within specified days"""
        query = """
            SELECT o.*, a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            WHERE o.close_date BETWEEN date('now') AND date('now', '+{} days')
            AND o.stage NOT IN ('Closed Won', 'Closed Lost')
            ORDER BY o.close_date ASC
        """.format(days)
        return db.execute_query(query)
    
    def get_overdue_opportunities(self):
        """Get overdue opportunities"""
        query = """
            SELECT o.*, a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            WHERE o.close_date < date('now')
            AND o.stage NOT IN ('Closed Won', 'Closed Lost')
            ORDER BY o.close_date ASC
        """
        return db.execute_query(query)
    
    def get_packaging_types(self):
        """Get distinct packaging types for dropdown"""
        query = "SELECT DISTINCT packaging_type FROM opportunities WHERE packaging_type IS NOT NULL ORDER BY packaging_type"
        result = db.execute_query(query)
        
        # Add default types if not in database
        default_types = ['MIL-STD-2073-1E', 'ASTM']
        existing_types = [row['packaging_type'] for row in result] if result else []
        
        for default_type in default_types:
            if default_type not in existing_types:
                existing_types.append(default_type)
        
        return sorted(existing_types)
    
    def search_opportunities(self, search_term):
        """Search opportunities by name, description, buyer, or MFR"""
        query = """
            SELECT o.*, a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name, p.name as product_name
            FROM opportunities o
            LEFT JOIN accounts a ON o.account_id = a.id
            LEFT JOIN contacts c ON o.contact_id = c.id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.name LIKE ? OR o.description LIKE ? OR o.buyer LIKE ? OR o.mfr LIKE ?
            ORDER BY o.created_date DESC
        """
        search_pattern = f"%{search_term}%"
        return db.execute_query(query, [search_pattern, search_pattern, search_pattern, search_pattern])
    
    # ==================== RFQs ====================
    
    def create_rfq(self, **kwargs):
        """Create a new RFQ"""
        fields = ['request_number', 'pdf_name', 'pdf_path', 'solicitation_url', 'open_date', 'close_date',
                 'purchase_number', 'nsn', 'fsc', 'delivery_days', 'payment_history', 'unit', 'quantity',
                 'fob', 'iso', 'inspection_point', 'sampling', 'product_description', 'manufacturer',
                 'packaging', 'package_type', 'office', 'division', 'buyer_address', 'buyer_name',
                 'buyer_code', 'buyer_telephone', 'buyer_email', 'buyer_fax', 'buyer_info', 'status',
                 'opportunity_id', 'account_id', 'contact_id', 'product_id', 'notes']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO rfqs ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_rfqs(self, filters=None, limit=None):
        """Get RFQs with optional filters"""
        query = """
            SELECT r.*, p.name as product_name, p.nsn as product_nsn, 
                   a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM rfqs r
            LEFT JOIN products p ON r.product_id = p.id
            LEFT JOIN accounts a ON r.account_id = a.id
            LEFT JOIN contacts c ON r.contact_id = c.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('product_id'):
                query += " AND r.product_id = ?"
                params.append(filters['product_id'])
            if filters.get('account_id'):
                query += " AND r.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('status'):
                query += " AND r.status = ?"
                params.append(filters['status'])
            if filters.get('manufacturer'):
                query += " AND r.manufacturer LIKE ?"
                params.append(f"%{filters['manufacturer']}%")
            if filters.get('vendor'):
                query += " AND a.name LIKE ?"
                params.append(f"%{filters['vendor']}%")
            if filters.get('product'):
                query += " AND (p.name LIKE ? OR r.product_description LIKE ?)"
                params.append(f"%{filters['product']}%")
                params.append(f"%{filters['product']}%")
            if filters.get('open_date_from'):
                query += " AND r.open_date >= ?"
                params.append(filters['open_date_from'])
            if filters.get('close_date_to'):
                query += " AND r.close_date <= ?"
                params.append(filters['close_date_to'])
        
        query += " ORDER BY r.close_date DESC, r.created_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_rfq_by_id(self, rfq_id):
        """Get specific RFQ by ID"""
        query = """
            SELECT r.*, p.name as product_name, p.nsn as product_nsn, 
                   a.name as account_name, (c.first_name || ' ' || c.last_name) as contact_name
            FROM rfqs r
            LEFT JOIN products p ON r.product_id = p.id
            LEFT JOIN accounts a ON r.account_id = a.id
            LEFT JOIN contacts c ON r.contact_id = c.id
            WHERE r.id = ?
        """
        results = db.execute_query(query, [rfq_id])
        return results[0] if results else None
    
    def update_rfq(self, rfq_id, **kwargs):
        """Update an existing RFQ"""
        fields = ['request_number', 'status', 'notes', 'quantity', 'delivery_days', 
                 'product_id', 'account_id', 'contact_id', 'opportunity_id', 'effective_date',
                 'quote_amount', 'lead_time']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return 0
        
        valid_fields['modified_date'] = datetime.now()
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        
        query = f"UPDATE rfqs SET {set_clause} WHERE id = ?"
        params = list(valid_fields.values()) + [rfq_id]
        
        return db.execute_update(query, params)
    
    def delete_rfq(self, rfq_id):
        """Delete an RFQ"""
        return db.execute_update("DELETE FROM rfqs WHERE id = ?", [rfq_id])
    
    # ==================== QUOTES (uses same table as RFQs) ====================
    
    def get_quotes(self, filters=None, limit=None):
        """Get quotes (same as RFQs but with quote terminology)"""
        return self.get_rfqs(filters, limit)
    
    def get_quote_by_id(self, quote_id):
        """Get quote by ID (same as RFQ)"""
        return self.get_rfq_by_id(quote_id)
    
    def create_quote(self, **kwargs):
        """Create a new quote (same as RFQ)"""
        return self.create_rfq(**kwargs)
    
    def update_quote(self, quote_id, **kwargs):
        """Update an existing quote"""
        fields = ['request_number', 'status', 'notes', 'quantity', 'delivery_days', 
                 'product_id', 'account_id', 'contact_id', 'opportunity_id', 'effective_date',
                 'quote_amount', 'lead_time']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return 0
        
        valid_fields['modified_date'] = datetime.now()
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        
        query = f"UPDATE rfqs SET {set_clause} WHERE id = ?"
        params = list(valid_fields.values()) + [quote_id]
        
        return db.execute_update(query, params)
    
    def delete_quote(self, quote_id):
        """Delete a quote"""
        return db.execute_update("DELETE FROM rfqs WHERE id = ?", [quote_id])

    # ==================== TASKS ====================
    
    def create_task(self, **kwargs):
        """Create a new task"""
        fields = ['subject', 'description', 'status', 'priority', 'work_date', 'due_date',
                 'owner', 'start_date', 'completed_date', 'parent_item_type', 'parent_item_id',
                 'sub_item_type', 'sub_item_id', 'time_taken']
        
        # Handle title -> subject mapping FIRST
        if 'title' in kwargs and kwargs['title']:
            kwargs['subject'] = kwargs['title']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('subject'):
            raise ValueError("Task subject is required")
        
        # Set default values
        if 'status' not in valid_fields:
            valid_fields['status'] = 'Not Started'
        if 'priority' not in valid_fields:
            valid_fields['priority'] = 'Medium'
        if 'created_date' not in valid_fields:
            valid_fields['created_date'] = 'CURRENT_TIMESTAMP'
        if 'last_modified' not in valid_fields:
            valid_fields['last_modified'] = 'CURRENT_TIMESTAMP'
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_tasks(self, filters=None, limit=None):
        """Get tasks with optional filters"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('assigned_to'):
                query += " AND assigned_to = ?"
                params.append(filters['assigned_to'])
            if filters.get('due_date'):
                query += " AND due_date = ?"
                params.append(filters['due_date'])
            if filters.get('overdue'):
                query += " AND due_date < ? AND status != 'Completed'"
                params.append(date.today().isoformat())
        
        query += " ORDER BY due_date ASC, priority DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def complete_task(self, task_id):
        """Mark task as completed"""
        query = "UPDATE tasks SET status = 'Completed', completed_date = ?, modified_date = ? WHERE id = ?"
        return db.execute_update(query, [datetime.now(), datetime.now(), task_id])
    
    # ==================== INTERACTIONS ====================
    
    def create_interaction(self, **kwargs):
        """Create a new interaction"""
        fields = ['subject', 'description', 'type', 'direction', 'interaction_date', 'duration_minutes',
                 'location', 'outcome', 'status', 'related_to_type', 'related_to_id', 'contact_id',
                 'account_id', 'opportunity_id', 'rfq_id', 'project_id', 'created_by']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('subject'):
            raise ValueError("Interaction subject is required")
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO interactions ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_interactions(self, filters=None, limit=None):
        """Get interactions with optional filters"""
        query = """
            SELECT i.*, 
                   a.name as account_name,
                   c.first_name || ' ' || c.last_name as contact_name,
                   o.name as opportunity_name,
                   r.request_number as rfq_number
            FROM interactions i
            LEFT JOIN accounts a ON i.account_id = a.id
            LEFT JOIN contacts c ON i.contact_id = c.id
            LEFT JOIN opportunities o ON i.opportunity_id = o.id
            LEFT JOIN rfqs r ON i.rfq_id = r.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('type'):
                query += " AND i.type = ?"
                params.append(filters['type'])
            if filters.get('account_id'):
                query += " AND i.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('contact_id'):
                query += " AND i.contact_id = ?"
                params.append(filters['contact_id'])
        
        query += " ORDER BY i.interaction_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def execute_query(self, query, params=None):
        """Execute a custom query and return results"""
        return db.execute_query(query, params)
    
    def execute_update(self, query, params=None):
        """Execute a custom update/insert query"""
        return db.execute_update(query, params)
    
    def get_interactions(self, filters=None, limit=None):
        """Get interactions with optional filters"""
        query = """
            SELECT i.*, 
                   a.name as account_name,
                   c.first_name || ' ' || c.last_name as contact_name,
                   o.name as opportunity_name,
                   r.request_number as rfq_number
            FROM interactions i
            LEFT JOIN accounts a ON i.account_id = a.id
            LEFT JOIN contacts c ON i.contact_id = c.id
            LEFT JOIN opportunities o ON i.opportunity_id = o.id
            LEFT JOIN rfqs r ON i.rfq_id = r.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('type'):
                query += " AND i.type = ?"
                params.append(filters['type'])
            if filters.get('account_id'):
                query += " AND i.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('contact_id'):
                query += " AND i.contact_id = ?"
                params.append(filters['contact_id'])
        
        query += " ORDER BY i.interaction_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    # ==================== VALIDATION METHODS ====================
    
    def check_contact_duplicate(self, name, email, exclude_id=None):
        """Check for duplicate contacts by name or email (case insensitive)"""
        duplicates = []
        
        # Check for duplicate name (case insensitive)
        name_query = """
            SELECT id, first_name, last_name, email 
            FROM contacts 
            WHERE (LOWER(first_name || ' ' || last_name) = LOWER(?) OR 
                   LOWER(last_name) = LOWER(?)) 
            AND is_active = 1
        """
        name_params = [name, name]
        
        if exclude_id:
            name_query += " AND id != ?"
            name_params.extend([exclude_id])
        
        name_results = db.execute_query(name_query, name_params)
        if name_results:
            duplicates.extend([{
                'type': 'name',
                'contact': result,
                'message': f"Contact with name '{name}' already exists"
            } for result in name_results])
        
        # Check for duplicate email (case insensitive) if email provided
        if email:
            email_query = """
                SELECT id, first_name, last_name, email 
                FROM contacts 
                WHERE LOWER(email) = LOWER(?) 
                AND is_active = 1
            """
            email_params = [email]
            
            if exclude_id:
                email_query += " AND id != ?"
                email_params.append(exclude_id)
            
            email_results = db.execute_query(email_query, email_params)
            if email_results:
                duplicates.extend([{
                    'type': 'email',
                    'contact': result,
                    'message': f"Contact with email '{email}' already exists"
                } for result in email_results])
        
        return duplicates
    
    def check_product_duplicate(self, nsn, exclude_id=None):
        """Check for duplicate products by NSN (case insensitive)"""
        if not nsn:
            return []
        
        query = """
            SELECT id, name, nsn, product_code 
            FROM products 
            WHERE LOWER(nsn) = LOWER(?) 
            AND is_active = 1
        """
        params = [nsn]
        
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
        
        results = db.execute_query(query, params)
        
        if results:
            return [{
                'type': 'nsn',
                'product': result,
                'message': f"Product with NSN '{nsn}' already exists"
            } for result in results]
        
        return []

    # ==================== QPL ====================
    
    def create_qpl_entry(self, **kwargs):
        """Create a new QPL entry"""
        fields = ['name', 'nsn', 'fsc', 'product_name', 'manufacturer', 'part_number',
                 'cage_code', 'description', 'specifications', 'qualification_date',
                 'expiration_date', 'status']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('name'):
            raise ValueError("QPL entry name is required")
        
        # Set default values
        valid_fields['status'] = valid_fields.get('status', 'Active')
        valid_fields['created_date'] = datetime.now()
        valid_fields['modified_date'] = datetime.now()
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO qpl ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_qpl_entries(self, filters=None, limit=None):
        """Get QPL entries with optional filters"""
        query = """
            SELECT q.*, 
                   GROUP_CONCAT(p.name, ', ') as linked_products
            FROM qpl q
            LEFT JOIN qpl_products qp ON q.id = qp.qpl_id
            LEFT JOIN products p ON qp.product_id = p.id
            WHERE q.status = 'Active'
        """
        params = []
        
        if filters:
            if filters.get('name'):
                query += " AND q.name LIKE ?"
                params.append(f"%{filters['name']}%")
            if filters.get('manufacturer'):
                query += " AND q.manufacturer LIKE ?"
                params.append(f"%{filters['manufacturer']}%")
            if filters.get('cage_code'):
                query += " AND q.cage_code LIKE ?"
                params.append(f"%{filters['cage_code']}%")
            if filters.get('nsn'):
                query += " AND q.nsn LIKE ?"
                params.append(f"%{filters['nsn']}%")
        
        query += " GROUP BY q.id ORDER BY q.name"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_qpl_entry_by_id(self, qpl_id):
        """Get a specific QPL entry by ID"""
        query = """
            SELECT q.*, 
                   GROUP_CONCAT(p.name, ', ') as linked_products,
                   GROUP_CONCAT(p.id, ',') as linked_product_ids
            FROM qpl q
            LEFT JOIN qpl_products qp ON q.id = qp.qpl_id
            LEFT JOIN products p ON qp.product_id = p.id
            WHERE q.id = ?
            GROUP BY q.id
        """
        results = db.execute_query(query, [qpl_id])
        return results[0] if results else None
    
    def update_qpl_entry(self, qpl_id, **kwargs):
        """Update a QPL entry"""
        fields = ['name', 'nsn', 'fsc', 'product_name', 'manufacturer', 'part_number',
                 'cage_code', 'description', 'specifications', 'qualification_date',
                 'expiration_date', 'status']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            return False
        
        valid_fields['modified_date'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        query = f"UPDATE qpl SET {set_clause} WHERE id = ?"
        
        params = list(valid_fields.values()) + [qpl_id]
        return db.execute_update(query, params)
    
    def link_qpl_to_product(self, qpl_id, product_id):
        """Link a QPL entry to a product"""
        query = """
            INSERT OR IGNORE INTO qpl_products (qpl_id, product_id, created_date)
            VALUES (?, ?, ?)
        """
        return db.execute_update(query, [qpl_id, product_id, datetime.now()])
    
    def unlink_qpl_from_product(self, qpl_id, product_id):
        """Unlink a QPL entry from a product"""
        query = "DELETE FROM qpl_products WHERE qpl_id = ? AND product_id = ?"
        return db.execute_update(query, [qpl_id, product_id])
    
    def get_qpl_for_product(self, product_id):
        """Get all QPL entries linked to a specific product"""
        query = """
            SELECT q.*
            FROM qpl q
            JOIN qpl_products qp ON q.id = qp.qpl_id
            WHERE qp.product_id = ? AND q.status = 'Active'
            ORDER BY q.name
        """
        return db.execute_query(query, [product_id])
    
    def get_products_for_qpl(self, qpl_id):
        """Get all products linked to a specific QPL entry"""
        query = """
            SELECT p.*
            FROM products p
            JOIN qpl_products qp ON p.id = qp.product_id
            WHERE qp.qpl_id = ? AND p.is_active = 1
            ORDER BY p.name
        """
        return db.execute_query(query, [qpl_id])
    
    def search_qpl_by_cage(self, cage_code):
        """Search QPL entries by CAGE code"""
        query = """
            SELECT * FROM qpl 
            WHERE cage_code LIKE ? AND status = 'Active'
            ORDER BY name
        """
        return db.execute_query(query, [f"%{cage_code}%"])

    # ==================== NOTES ====================
    
    def create_note(self, note, **kwargs):
        """Create a new note"""
        if not note or not note.strip():
            raise ValueError("Note content is required")
        
        valid_fields = {
            'note': note.strip(),
            'account_id': kwargs.get('account_id'),
            'contact_id': kwargs.get('contact_id'),
            'opportunity_id': kwargs.get('opportunity_id'),
            'project_id': kwargs.get('project_id'),
            'created_by': kwargs.get('created_by'),
            'created_date': datetime.now(),
            'last_modified': datetime.now()
        }
        
        # Remove None values
        valid_fields = {k: v for k, v in valid_fields.items() if v is not None}
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO notes ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_notes(self, filters=None, limit=None):
        """Get notes with optional filters"""
        query = """
            SELECT n.*, 
                   a.name as account_name,
                   (c.first_name || ' ' || c.last_name) as contact_name,
                   o.name as opportunity_name
            FROM notes n
            LEFT JOIN accounts a ON n.account_id = a.id
            LEFT JOIN contacts c ON n.contact_id = c.id
            LEFT JOIN opportunities o ON n.opportunity_id = o.id
            WHERE n.is_active = 1
        """
        params = []
        
        if filters:
            if filters.get('account_id'):
                query += " AND n.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('contact_id'):
                query += " AND n.contact_id = ?"
                params.append(filters['contact_id'])
            if filters.get('opportunity_id'):
                query += " AND n.opportunity_id = ?"
                params.append(filters['opportunity_id'])
            if filters.get('project_id'):
                query += " AND n.project_id = ?"
                params.append(filters['project_id'])
            if filters.get('search'):
                query += " AND n.note LIKE ?"
                params.append(f"%{filters['search']}%")
        
        query += " ORDER BY n.created_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        return db.execute_query(query, params if params else None)
    
    def get_note_by_id(self, note_id):
        """Get specific note by ID"""
        query = """
            SELECT n.*, 
                   a.name as account_name,
                   (c.first_name || ' ' || c.last_name) as contact_name,
                   o.name as opportunity_name
            FROM notes n
            LEFT JOIN accounts a ON n.account_id = a.id
            LEFT JOIN contacts c ON n.contact_id = c.id
            LEFT JOIN opportunities o ON n.opportunity_id = o.id
            WHERE n.id = ? AND n.is_active = 1
        """
        results = db.execute_query(query, [note_id])
        return results[0] if results else None
    
    def update_note(self, note_id, note_content, **kwargs):
        """Update an existing note"""
        if not note_content or not note_content.strip():
            raise ValueError("Note content is required")
        
        valid_fields = {
            'note': note_content.strip(),
            'last_modified': datetime.now()
        }
        
        # Add optional relationship updates
        for field in ['account_id', 'contact_id', 'opportunity_id', 'project_id']:
            if field in kwargs:
                valid_fields[field] = kwargs[field]
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        query = f"UPDATE notes SET {set_clause} WHERE id = ?"
        
        params = list(valid_fields.values()) + [note_id]
        return db.execute_update(query, params)
    
    def delete_note(self, note_id):
        """Soft delete a note"""
        query = "UPDATE notes SET is_active = 0, last_modified = ? WHERE id = ?"
        return db.execute_update(query, [datetime.now(), note_id])
    
    def get_notes_for_account(self, account_id):
        """Get all notes for a specific account"""
        return self.get_notes({'account_id': account_id})
    
    def get_notes_for_contact(self, contact_id):
        """Get all notes for a specific contact"""
        return self.get_notes({'contact_id': contact_id})
    
    def get_notes_for_opportunity(self, opportunity_id):
        """Get all notes for a specific opportunity"""
        return self.get_notes({'opportunity_id': opportunity_id})

    # ==================== INTERACTIONS & APPOINTMENTS ====================
    
    def update_interaction(self, interaction_id, **kwargs):
        """Update an existing interaction"""
        fields = ['subject', 'description', 'type', 'direction', 'interaction_date', 'duration_minutes',
                 'location', 'outcome', 'status', 'related_to_type', 'related_to_id', 'contact_id',
                 'account_id', 'opportunity_id', 'rfq_id', 'project_id']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            raise ValueError("No valid fields provided for update")
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        values = list(valid_fields.values()) + [interaction_id]
        
        query = f"UPDATE interactions SET {set_clause} WHERE id = ?"
        return db.execute_update(query, values)
        
        # Remove None values
        valid_fields = {k: v for k, v in valid_fields.items() if v is not None}
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO interactions ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_interactions(self, filters=None, limit=None):
        """Get interactions with optional filters"""
        query = """
            SELECT i.*, 
                   (c.first_name || ' ' || c.last_name) as contact_name,
                   c.email as contact_email_addr,
                   o.name as opportunity_name,
                   a.name as account_name,
                   p.name as project_name
            FROM interactions i
            LEFT JOIN contacts c ON i.contact_id = c.id
            LEFT JOIN opportunities o ON i.opportunity_id = o.id
            LEFT JOIN accounts a ON i.account_id = a.id
            LEFT JOIN projects p ON i.project_id = p.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('contact_id'):
                query += " AND i.contact_id = ?"
                params.append(filters['contact_id'])
            if filters.get('opportunity_id'):
                query += " AND i.opportunity_id = ?"
                params.append(filters['opportunity_id'])
            if filters.get('account_id'):
                query += " AND i.account_id = ?"
                params.append(filters['account_id'])
            if filters.get('type'):
                query += " AND i.type = ?"
                params.append(filters['type'])
            if filters.get('status'):
                query += " AND i.status = ?"
                params.append(filters['status'])
            if filters.get('direction'):
                query += " AND i.direction = ?"
                params.append(filters['direction'])
            if filters.get('start_date'):
                query += " AND DATE(i.interaction_date) >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND DATE(i.interaction_date) <= ?"
                params.append(filters['end_date'])
        
        query += " ORDER BY i.interaction_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        interactions = db.execute_query(query, params if params else None)
        
        # Add calculated fields to each interaction
        for interaction in interactions:
            self._enhance_interaction_data(interaction)
        
        return interactions
    
    def get_interaction_by_id(self, interaction_id):
        """Get specific interaction by ID"""
        query = """
            SELECT i.*, 
                   (c.first_name || ' ' || c.last_name) as contact_name,
                   c.email as contact_email_addr,
                   o.name as opportunity_name,
                   a.name as account_name,
                   p.name as project_name
            FROM interactions i
            LEFT JOIN contacts c ON i.contact_id = c.id
            LEFT JOIN opportunities o ON i.opportunity_id = o.id
            LEFT JOIN accounts a ON i.account_id = a.id
            LEFT JOIN projects p ON i.project_id = p.id
            WHERE i.id = ?
        """
        results = db.execute_query(query, [interaction_id])
        return results[0] if results else None
    
    def update_interaction(self, interaction_id, **kwargs):
        """Update an existing interaction"""
        valid_fields = {}
        
        # Validate enum values if provided
        if 'direction' in kwargs:
            valid_directions = ['Received', 'Sent']
            if kwargs['direction'] not in valid_directions:
                raise ValueError(f"Direction must be one of: {', '.join(valid_directions)}")
            valid_fields['direction'] = kwargs['direction']
        
        if 'type' in kwargs:
            valid_types = ['Email', 'Text', 'Call', 'LinkedIn', 'In Person', 'Mail']
            if kwargs['type'] not in valid_types:
                raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
            valid_fields['type'] = kwargs['type']
        
        if 'status' in kwargs:
            valid_statuses = ['Completed', 'Follow up']
            if kwargs['status'] not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
            valid_fields['status'] = kwargs['status']
        
        # Add other updateable fields
        updateable_fields = ['message', 'attachments', 'subject', 'interaction_date',
                           'duration_minutes', 'location', 'outcome', 'contact_id',
                           'contact_email', 'opportunity_id', 'account_id']
        
        for field in updateable_fields:
            if field in kwargs:
                valid_fields[field] = kwargs[field]
        
        if not valid_fields:
            return False
        
        valid_fields['last_modified'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        query = f"UPDATE interactions SET {set_clause} WHERE id = ?"
        
        params = list(valid_fields.values()) + [interaction_id]
        return db.execute_update(query, params)
    
    def delete_interaction(self, interaction_id):
        """Delete an interaction"""
        query = "DELETE FROM interactions WHERE id = ?"
        return db.execute_update(query, [interaction_id])
    
    def get_interactions_for_contact(self, contact_id):
        """Get all interactions for a specific contact"""
        return self.get_interactions({'contact_id': contact_id})
    
    def get_interactions_for_opportunity(self, opportunity_id):
        """Get all interactions for a specific opportunity"""
        return self.get_interactions({'opportunity_id': opportunity_id})
    
    def get_follow_up_interactions(self):
        """Get all interactions that need follow up"""
        return self.get_interactions({'status': 'Follow up'})
    
    def get_interactions_by_type(self, interaction_type):
        """Get interactions by type (Email, Call, etc.)"""
        return self.get_interactions({'type': interaction_type})

    # ==================== TASKS ====================
    
    def create_task(self, **kwargs):
        """Create a new task"""
        fields = ['subject', 'description', 'status', 'priority', 'type', 'due_date',
                 'assigned_to', 'related_to_type', 'related_to_id']
        
        # Handle title -> subject mapping FIRST
        if 'title' in kwargs and kwargs['title']:
            kwargs['subject'] = kwargs['title']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields.get('subject'):
            raise ValueError("Task subject is required")
        
        # Set defaults
        if 'status' not in valid_fields:
            valid_fields['status'] = 'Not Started'
        if 'priority' not in valid_fields:
            valid_fields['priority'] = 'Normal'
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_tasks(self, filters=None, limit=None):
        """Get tasks with optional filters and calculated fields"""
        base_query = """
        SELECT t.*,
               a.name as account_name,
               (c.first_name || ' ' || c.last_name) as contact_name,
               o.name as opportunity_name,
               p.name as product_name
        FROM tasks t
        LEFT JOIN accounts a ON (t.parent_item_type = 'Account' AND t.parent_item_id = a.id)
        LEFT JOIN contacts c ON (t.parent_item_type = 'Contact' AND t.parent_item_id = c.id)
        LEFT JOIN opportunities o ON (t.parent_item_type = 'Opportunity' AND t.parent_item_id = o.id)
        LEFT JOIN products p ON (t.parent_item_type = 'Product' AND t.parent_item_id = p.id)
        WHERE 1=1
        """
        
        params = []
        
        if filters:
            if filters.get('id'):
                base_query += " AND t.id = ?"
                params.append(filters['id'])
            if filters.get('status'):
                base_query += " AND t.status = ?"
                params.append(filters['status'])
            if filters.get('priority'):
                base_query += " AND t.priority = ?"
                params.append(filters['priority'])
            if filters.get('owner'):
                base_query += " AND t.assigned_to LIKE ?"
                params.append(f"%{filters['owner']}%")
            if filters.get('due_date_range'):
                if filters['due_date_range'] == 'overdue':
                    base_query += " AND t.due_date < date('now') AND t.status != 'Completed'"
                elif filters['due_date_range'] == 'today':
                    base_query += " AND t.due_date = date('now')"
                elif filters['due_date_range'] == 'this_week':
                    base_query += " AND t.due_date BETWEEN date('now') AND date('now', '+7 days')"
                elif filters['due_date_range'] == 'next_week':
                    base_query += " AND t.due_date BETWEEN date('now', '+7 days') AND date('now', '+14 days')"
            if filters.get('parent_item_type'):
                base_query += " AND t.parent_item_type = ?"
                params.append(filters['parent_item_type'])
            if filters.get('parent_item_id'):
                base_query += " AND t.parent_item_id = ?"
                params.append(filters['parent_item_id'])
            if filters.get('search'):
                base_query += " AND (t.subject LIKE ? OR t.description LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        
        base_query += " ORDER BY CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END, t.due_date ASC, t.priority DESC"
        
        if limit:
            base_query += f" LIMIT {limit}"
        
        tasks = db.execute_query(base_query, params if params else None)
        
        # Enhance tasks with calculated fields
        for task in tasks:
            self._enhance_task_data(task)
        
        return tasks
    
    def _enhance_task_data(self, task):
        """Add calculated fields to task data"""
        from datetime import datetime, date
        
        # Calculate days_till_due
        if task.get('due_date'):
            try:
                if isinstance(task['due_date'], str):
                    # Try different date formats
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                    due_date = None
                    for fmt in date_formats:
                        try:
                            due_date = datetime.strptime(task['due_date'], fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if due_date is None:
                        # If none of the formats work, skip calculation
                        task['days_till_due'] = None
                        task['past_due'] = False
                        task['countdown'] = 'Invalid date'
                        return
                else:
                    due_date = task['due_date']
                
                today = date.today()
                days_diff = (due_date - today).days
                task['days_till_due'] = days_diff
                
                # Calculate past_due
                task['past_due'] = days_diff < 0 and task.get('status') != 'Completed'
                
                # Calculate countdown
                if task.get('status') == 'Completed':
                    task['countdown'] = 'Completed'
                elif days_diff < 0:
                    task['countdown'] = f"{abs(days_diff)} days overdue"
                elif days_diff == 0:
                    task['countdown'] = 'Due Today'
                elif days_diff == 1:
                    task['countdown'] = 'Due Tomorrow'
                else:
                    task['countdown'] = f"{days_diff} days remaining"
                    
            except (ValueError, TypeError):
                task['days_till_due'] = None
                task['past_due'] = False
                task['countdown'] = 'No due date'
        else:
            task['days_till_due'] = None
            task['past_due'] = False
            task['countdown'] = 'No due date'
        
        # Calculate scheduled status
        if task.get('due_date'):
            task['scheduled'] = 'Scheduled'
        else:
            task['scheduled'] = 'Not Scheduled'
    
    def _enhance_opportunity_data(self, opportunity):
        """Add calculated fields to opportunity data"""
        from datetime import datetime, date
        
        # Calculate days to close
        if opportunity.get('close_date'):
            try:
                if isinstance(opportunity['close_date'], str):
                    close_date = datetime.strptime(opportunity['close_date'], '%Y-%m-%d').date()
                else:
                    close_date = opportunity['close_date']
                
                today = date.today()
                days_diff = (close_date - today).days
                opportunity['days_to_close'] = days_diff
                
                # Calculate status indicators
                if days_diff < 0:
                    opportunity['status_indicator'] = 'Overdue'
                    opportunity['urgency'] = 'High'
                elif days_diff <= 7:
                    opportunity['status_indicator'] = 'Due Soon'
                    opportunity['urgency'] = 'High'
                elif days_diff <= 30:
                    opportunity['status_indicator'] = 'Active'
                    opportunity['urgency'] = 'Medium'
                else:
                    opportunity['status_indicator'] = 'Future'
                    opportunity['urgency'] = 'Low'
                    
            except (ValueError, TypeError):
                opportunity['days_to_close'] = None
                opportunity['status_indicator'] = 'Unknown'
                opportunity['urgency'] = 'Low'
        else:
            opportunity['days_to_close'] = None
            opportunity['status_indicator'] = 'No Close Date'
            opportunity['urgency'] = 'Low'
    
    def _enhance_project_data(self, project):
        """Add calculated fields to project data"""
        from datetime import datetime, date
        
        # Calculate project duration and progress
        if project.get('start_date') and project.get('end_date'):
            try:
                start_date = datetime.strptime(project['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(project['end_date'], '%Y-%m-%d').date()
                today = date.today()
                
                total_days = (end_date - start_date).days
                elapsed_days = (today - start_date).days
                
                # Calculate progress percentage if not stored
                if not project.get('progress_percentage'):
                    if total_days > 0:
                        project['progress_percentage'] = min(100, max(0, (elapsed_days / total_days) * 100))
                    else:
                        project['progress_percentage'] = 0
                
                # Calculate project health
                stored_progress = project.get('progress_percentage', 0)
                expected_progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0
                
                if stored_progress >= expected_progress * 0.9:
                    project['health_status'] = 'On Track'
                elif stored_progress >= expected_progress * 0.7:
                    project['health_status'] = 'At Risk'
                else:
                    project['health_status'] = 'Behind Schedule'
                
                # Calculate days remaining
                project['days_remaining'] = max(0, (end_date - today).days)
                
            except (ValueError, TypeError):
                project['progress_percentage'] = project.get('progress_percentage', 0)
                project['health_status'] = 'Unknown'
                project['days_remaining'] = None
    
    def _enhance_interaction_data(self, interaction):
        """Add calculated fields to interaction data"""
        from datetime import datetime, timedelta
        
        # Calculate default duration if not stored
        if not interaction.get('duration_minutes'):
            interaction_type = interaction.get('type', '').lower()
            default_durations = {
                'call': 15,
                'phone': 15,
                'meeting': 60,
                'email': 5,
                'demo': 90,
                'presentation': 60,
                'follow-up': 10
            }
            
            # Find matching type
            for type_key, duration in default_durations.items():
                if type_key in interaction_type:
                    interaction['duration_minutes'] = duration
                    break
            else:
                interaction['duration_minutes'] = 30  # Default fallback
        
        # Calculate age of interaction
        if interaction.get('interaction_date'):
            try:
                if isinstance(interaction['interaction_date'], str):
                    interaction_date = datetime.strptime(interaction['interaction_date'], '%Y-%m-%d %H:%M:%S')
                else:
                    interaction_date = interaction['interaction_date']
                
                age = datetime.now() - interaction_date
                interaction['days_ago'] = age.days
                
                if age.days == 0:
                    interaction['age_display'] = 'Today'
                elif age.days == 1:
                    interaction['age_display'] = 'Yesterday'
                elif age.days < 7:
                    interaction['age_display'] = f'{age.days} days ago'
                elif age.days < 30:
                    weeks = age.days // 7
                    interaction['age_display'] = f'{weeks} week{"s" if weeks > 1 else ""} ago'
                else:
                    months = age.days // 30
                    interaction['age_display'] = f'{months} month{"s" if months > 1 else ""} ago'
                    
            except (ValueError, TypeError):
                interaction['days_ago'] = None
                interaction['age_display'] = 'Unknown'
    
    def _enhance_account_data(self, account):
        """Add calculated fields to account data"""
        from datetime import datetime, date
        
        # Calculate account age
        if account.get('created_date'):
            try:
                if isinstance(account['created_date'], str):
                    created_date = datetime.strptime(account['created_date'], '%Y-%m-%d %H:%M:%S').date()
                else:
                    created_date = account['created_date']
                
                today = date.today()
                age_days = (today - created_date).days
                account['account_age_days'] = age_days
                
                if age_days < 30:
                    account['account_maturity'] = 'New'
                elif age_days < 180:
                    account['account_maturity'] = 'Growing'
                elif age_days < 365:
                    account['account_maturity'] = 'Established'
                else:
                    account['account_maturity'] = 'Mature'
                    
            except (ValueError, TypeError):
                account['account_age_days'] = None
                account['account_maturity'] = 'Unknown'
        
        # Get summary statistics (this would normally query related tables)
        account['calculated_summary'] = f"Account established {account.get('account_maturity', 'Unknown').lower()}"

    def get_task_by_id(self, task_id):
        """Get a specific task by ID with calculated fields"""
        tasks = self.get_tasks({'id': task_id})
        return tasks[0] if tasks else None
    
    def update_task(self, task_id, **kwargs):
        """Update an existing task"""
        fields = ['subject', 'description', 'status', 'work_date', 'due_date', 'owner',
                 'start_date', 'completed_date', 'parent_item_type', 'parent_item_id',
                 'sub_item_type', 'sub_item_id', 'priority', 'time_taken']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        if not valid_fields:
            raise ValueError("No valid fields to update")
        
        # Auto-set completed_date if status changed to Completed
        if valid_fields.get('status') == 'Completed' and 'completed_date' not in valid_fields:
            valid_fields['completed_date'] = datetime.now().date().isoformat()
        
        # Auto-set start_date if status changed to In Progress and no start_date
        if valid_fields.get('status') == 'In Progress':
            current_task = self.get_task_by_id(task_id)
            if current_task and not current_task.get('start_date') and 'start_date' not in valid_fields:
                valid_fields['start_date'] = datetime.now().date().isoformat()
        
        # Always update modified_date
        valid_fields['modified_date'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
        query = f"UPDATE tasks SET {set_clause} WHERE id = ?"
        
        return db.execute_update(query, list(valid_fields.values()) + [task_id])
    
    def delete_task(self, task_id):
        """Delete a task"""
        return db.execute_update("DELETE FROM tasks WHERE id = ?", [task_id])
    
    def get_task_stats(self):
        """Get task statistics"""
        stats_query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'Not Started' THEN 1 ELSE 0 END) as not_started,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Waiting' THEN 1 ELSE 0 END) as waiting,
            SUM(CASE WHEN status = 'Deferred' THEN 1 ELSE 0 END) as deferred,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_priority,
            SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as medium_priority,
            SUM(CASE WHEN priority = 'Low' THEN 1 ELSE 0 END) as low_priority,
            SUM(CASE WHEN due_date < date('now') AND status != 'Completed' THEN 1 ELSE 0 END) as overdue,
            SUM(CASE WHEN due_date = date('now') THEN 1 ELSE 0 END) as due_today,
            SUM(CASE WHEN due_date BETWEEN date('now', '+1 day') AND date('now', '+7 days') THEN 1 ELSE 0 END) as due_this_week,
            SUM(CASE WHEN due_date IS NULL AND status IN ('Not Started', 'In Progress') THEN 1 ELSE 0 END) as needs_scheduling
        FROM tasks
        """
        
        result = db.execute_query(stats_query)
        return result[0] if result else {}
    
    def get_tasks_by_status(self, status):
        """Get tasks by status"""
        return self.get_tasks({'status': status})
    
    def get_tasks_by_priority(self, priority):
        """Get tasks by priority"""
        return self.get_tasks({'priority': priority})
    
    def get_overdue_tasks(self):
        """Get overdue tasks"""
        return self.get_tasks({'due_date_range': 'overdue'})
    
    def get_tasks_due_today(self):
        """Get tasks due today"""
        return self.get_tasks({'due_date_range': 'today'})
    
    def get_tasks_due_this_week(self):
        """Get tasks due this week"""
        return self.get_tasks({'due_date_range': 'this_week'})
    
    def get_tasks_by_owner(self, owner):
        """Get tasks assigned to a specific owner"""
        return self.get_tasks({'owner': owner})
    
    def get_tasks_for_account(self, account_id):
        """Get all tasks related to an account"""
        return self.get_tasks({'account_id': account_id})
    
    def get_tasks_for_contact(self, contact_id):
        """Get all tasks related to a contact"""
        return self.get_tasks({'contact_id': contact_id})
    
    def get_tasks_for_opportunity(self, opportunity_id):
        """Get all tasks related to an opportunity"""
        return self.get_tasks({'opportunity_id': opportunity_id})
    
    def get_tasks_by_parent(self, parent_type, parent_id):
        """Get tasks by parent item"""
        return self.get_tasks({'parent_item_type': parent_type, 'parent_item_id': parent_id})
    
    def mark_task_completed(self, task_id, time_taken=None):
        """Mark a task as completed"""
        update_data = {'status': 'Completed', 'completed_date': datetime.now().date().isoformat()}
        if time_taken:
            update_data['time_taken'] = time_taken
        return self.update_task(task_id, **update_data)
    
    def start_task(self, task_id):
        """Start a task (set status to In Progress)"""
        return self.update_task(task_id, status='In Progress', start_date=datetime.now().date().isoformat())
    
    def reschedule_task(self, task_id, new_due_date):
        """Reschedule a task"""
        return self.update_task(task_id, due_date=new_due_date)
    
    def assign_task(self, task_id, owner):
        """Assign a task to an owner"""
        return self.update_task(task_id, owner=owner)
    
    def get_unscheduled_tasks(self):
        """Get tasks that need scheduling (no due date)"""
        query = "SELECT * FROM tasks WHERE due_date IS NULL ORDER BY created_date DESC"
        return db.execute_query(query)
    
    def get_tasks_needing_attention(self):
        """Get tasks that need immediate attention (overdue + high priority)"""
        query = """
        SELECT * FROM tasks 
        WHERE (due_date < date('now') AND status != 'Completed') 
           OR (priority = 'High' AND status != 'Completed')
        ORDER BY due_date ASC, priority DESC
        """
        return db.execute_query(query)

    # ==================== PROJECTS ====================
    
    def create_project(self, **kwargs):
        """Create a new project with comprehensive field support"""
        fields = ['name', 'status', 'priority', 'start_date', 'end_date', 'due_date',
                 'summary', 'description', 'vendor_id', 'parent_project_id', 'budget',
                 'actual_cost', 'progress_percentage', 'project_manager', 'team_members', 'notes']
        
        valid_fields = {k: v for k, v in kwargs.items() if k in fields and v is not None}
        
        # Ensure required fields
        if 'name' not in valid_fields:
            raise ValueError("Project name is required")
        
        placeholders = ', '.join(['?' for _ in valid_fields])
        columns = ', '.join(valid_fields.keys())
        
        query = f"INSERT INTO projects ({columns}) VALUES ({placeholders})"
        return db.execute_update(query, list(valid_fields.values()))
    
    def get_projects(self, filters=None, limit=None):
        """Get projects with calculated fields and relationships"""
        query = """
            SELECT p.*, 
                   v.name as vendor_name,
                   pp.name as parent_project_name
            FROM projects p
            LEFT JOIN accounts v ON p.vendor_id = v.id
            LEFT JOIN projects pp ON p.parent_project_id = pp.id
            WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND p.status = ?"
                params.append(filters['status'])
            if filters.get('id'):
                query += " AND p.id = ?"
                params.append(filters['id'])
            if filters.get('priority'):
                query += " AND p.priority = ?"
                params.append(filters['priority'])
            if filters.get('project_manager'):
                query += " AND p.project_manager LIKE ?"
                params.append(f"%{filters['project_manager']}%")
            if filters.get('vendor_id'):
                query += " AND p.vendor_id = ?"
                params.append(filters['vendor_id'])
            if filters.get('parent_project_id') is not None:
                if filters['parent_project_id'] is None:
                    query += " AND p.parent_project_id IS NULL"
                else:
                    query += " AND p.parent_project_id = ?"
                    params.append(filters['parent_project_id'])
            if filters.get('search'):
                query += " AND (p.name LIKE ? OR p.summary LIKE ? OR p.description LIKE ?)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%", f"%{filters['search']}%"])
            if filters.get('overdue'):
                query += " AND p.due_date < date('now') AND p.status != 'Done'"
            if filters.get('due_soon'):
                days = filters.get('due_soon_days', 7)
                query += f" AND p.due_date BETWEEN date('now') AND date('now', '+{days} days') AND p.status != 'Done'"
        
        query += " ORDER BY p.priority DESC, p.due_date ASC, p.created_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        projects = db.execute_query(query, params if params else None)
        
        # Add calculated fields to each project
        for project in projects:
            self._enhance_project_data(project)
        
        return projects
    
    def update_project(self, project_id, **kwargs):
        """Update a project with automatic timestamp updates"""
        valid_fields = {k: v for k, v in kwargs.items() if v is not None}
        
        if valid_fields:
            # Add modified_date timestamp
            valid_fields['modified_date'] = datetime.now().isoformat()
            
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in valid_fields.keys()])
            query = f"UPDATE projects SET {set_clause} WHERE id = ?"
            params = list(valid_fields.values()) + [project_id]
            
            return db.execute_update(query, params)
        return False
    
    def get_project_by_id(self, project_id):
        """Get a single project by ID with relationships"""
        query = """
            SELECT p.*, 
                   v.name as vendor_name,
                   pp.name as parent_project_name
            FROM projects p
            LEFT JOIN accounts v ON p.vendor_id = v.id
            LEFT JOIN projects pp ON p.parent_project_id = pp.id
            WHERE p.id = ?
        """
        result = db.execute_query(query, [project_id])
        return result[0] if result else None
    
    def delete_project(self, project_id):
        """Delete a project and its relationships"""
        return db.execute_update("DELETE FROM projects WHERE id = ?", [project_id])
    
    def get_project_stats(self):
        """Get project statistics"""
        stats = {}
        
        # Basic counts
        result = db.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Not Started' THEN 1 END) as not_started,
                COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN status = 'Done' THEN 1 END) as completed,
                COUNT(CASE WHEN priority = 'High' THEN 1 END) as high_priority,
                COUNT(CASE WHEN due_date < date('now') AND status != 'Done' THEN 1 END) as overdue,
                COUNT(CASE WHEN due_date = date('now') THEN 1 END) as due_today
            FROM projects
        """)
        
        if result:
            stats.update(result[0])
        
        # Financial stats
        financial = db.execute_query("""
            SELECT 
                SUM(budget) as total_budget,
                SUM(actual_cost) as total_actual_cost,
                AVG(progress_percentage) as avg_progress,
                COUNT(CASE WHEN budget IS NOT NULL AND actual_cost IS NOT NULL 
                           AND actual_cost > budget THEN 1 END) as over_budget
            FROM projects
        """)
        
        if financial:
            stats.update(financial[0])
        
        return stats
    
    def get_projects_by_status(self):
        """Get project counts by status"""
        query = """
            SELECT status, 
                   COUNT(*) as count,
                   AVG(progress_percentage) as avg_progress,
                   SUM(budget) as total_budget
            FROM projects 
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY 
                CASE status
                    WHEN 'Not Started' THEN 1
                    WHEN 'In Progress' THEN 2
                    WHEN 'Done' THEN 3
                    ELSE 4
                END
        """
        return db.execute_query(query)
    
    def get_projects_by_priority(self):
        """Get project counts by priority"""
        query = """
            SELECT priority, 
                   COUNT(*) as count,
                   AVG(progress_percentage) as avg_progress
            FROM projects 
            WHERE priority IS NOT NULL
            GROUP BY priority
            ORDER BY 
                CASE priority
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END
        """
        return db.execute_query(query)
    
    def start_project(self, project_id):
        """Start a project (change status to In Progress)"""
        return self.update_project(project_id, 
                                 status='In Progress', 
                                 start_date=date.today().isoformat())
    
    def complete_project(self, project_id):
        """Complete a project (change status to Done)"""
        return self.update_project(project_id, 
                                 status='Done', 
                                 completion_date=date.today().isoformat(),
                                 progress_percentage=100)
    
    def update_project_progress(self, project_id, percentage):
        """Update project progress percentage"""
        if 0 <= percentage <= 100:
            updates = {'progress_percentage': percentage}
            if percentage == 100:
                updates['status'] = 'Done'
                updates['completion_date'] = date.today().isoformat()
            return self.update_project(project_id, **updates)
        return False
    
    def get_overdue_projects(self):
        """Get overdue projects"""
        query = """
            SELECT p.*, v.name as vendor_name
            FROM projects p
            LEFT JOIN accounts v ON p.vendor_id = v.id
            WHERE p.due_date < date('now') 
            AND p.status != 'Done'
            ORDER BY p.due_date ASC
        """
        return db.execute_query(query)
    
    def get_projects_due_soon(self, days=7):
        """Get projects due within specified days"""
        query = """
            SELECT p.*, v.name as vendor_name
            FROM projects p
            LEFT JOIN accounts v ON p.vendor_id = v.id
            WHERE p.due_date BETWEEN date('now') AND date('now', '+{} days')
            AND p.status != 'Done'
            ORDER BY p.due_date ASC
        """.format(days)
        return db.execute_query(query)
    
    def get_active_projects(self):
        """Get all active (In Progress) projects"""
        return self.get_projects({'status': 'In Progress'})
    
    def search_projects(self, search_term):
        """Search projects by name, summary, description, or project manager"""
        query = """
            SELECT p.*, v.name as vendor_name, pp.name as parent_project_name
            FROM projects p
            LEFT JOIN accounts v ON p.vendor_id = v.id
            LEFT JOIN projects pp ON p.parent_project_id = pp.id
            WHERE p.name LIKE ? OR p.summary LIKE ? OR p.description LIKE ? OR p.project_manager LIKE ?
            ORDER BY p.created_date DESC
        """
        search_pattern = f"%{search_term}%"
        return db.execute_query(query, [search_pattern, search_pattern, search_pattern, search_pattern])
    
    def get_sub_projects(self, parent_project_id):
        """Get all sub-projects of a parent project"""
        return self.get_projects({'parent_project_id': parent_project_id})
    
    def get_project_hierarchy(self, project_id):
        """Get project hierarchy (parent and children)"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        
        result = {
            'project': project,
            'parent': None,
            'children': []
        }
        
        # Get parent project
        if project['parent_project_id']:
            result['parent'] = self.get_project_by_id(project['parent_project_id'])
        
        # Get child projects
        result['children'] = self.get_sub_projects(project_id)
        
        return result
    
    # ==================== PROJECT RELATIONSHIPS ====================
    
    def add_project_product(self, project_id, product_id, quantity=None, role=None):
        """Add a product to a project"""
        query = """
            INSERT OR REPLACE INTO project_products (project_id, product_id, quantity, role)
            VALUES (?, ?, ?, ?)
        """
        return db.execute_update(query, [project_id, product_id, quantity, role])
    
    def remove_project_product(self, project_id, product_id):
        """Remove a product from a project"""
        query = "DELETE FROM project_products WHERE project_id = ? AND product_id = ?"
        return db.execute_update(query, [project_id, product_id])
    
    def get_project_products(self, project_id):
        """Get all products associated with a project"""
        query = """
            SELECT p.*, pp.quantity, pp.role, pp.created_date as association_date
            FROM products p
            JOIN project_products pp ON p.id = pp.product_id
            WHERE pp.project_id = ?
            ORDER BY pp.created_date DESC
        """
        return db.execute_query(query, [project_id])
    
    def add_project_task(self, project_id, task_id, relationship_type='associated'):
        """Add a task to a project"""
        query = """
            INSERT OR REPLACE INTO project_tasks (project_id, task_id, relationship_type)
            VALUES (?, ?, ?)
        """
        return db.execute_update(query, [project_id, task_id, relationship_type])
    
    def remove_project_task(self, project_id, task_id):
        """Remove a task from a project"""
        query = "DELETE FROM project_tasks WHERE project_id = ? AND task_id = ?"
        return db.execute_update(query, [project_id, task_id])
    
    def get_project_tasks(self, project_id):
        """Get all tasks associated with a project"""
        query = """
            SELECT t.*, pt.relationship_type, pt.created_date as association_date
            FROM tasks t
            JOIN project_tasks pt ON t.id = pt.task_id
            WHERE pt.project_id = ?
            ORDER BY pt.created_date DESC
        """
        return db.execute_query(query, [project_id])

    def add_project_contact(self, project_id, contact_id, role=None):
        """Add a contact to a project"""
        query = """
            INSERT OR REPLACE INTO project_contacts (project_id, contact_id, role)
            VALUES (?, ?, ?)
        """
        return db.execute_update(query, [project_id, contact_id, role])
    
    def remove_project_contact(self, project_id, contact_id):
        """Remove a contact from a project"""
        query = "DELETE FROM project_contacts WHERE project_id = ? AND contact_id = ?"
        return db.execute_update(query, [project_id, contact_id])
    
    def get_project_contacts(self, project_id):
        """Get all contacts associated with a project"""
        query = """
            SELECT c.*, pc.role, pc.created_date as association_date
            FROM contacts c
            JOIN project_contacts pc ON c.id = pc.contact_id
            WHERE pc.project_id = ?
            ORDER BY pc.created_date DESC
        """
        return db.execute_query(query, [project_id])
    
    def add_project_opportunity(self, project_id, opportunity_id, relationship_type='derived_from'):
        """Add an opportunity to a project"""
        query = """
            INSERT OR REPLACE INTO project_opportunities (project_id, opportunity_id, relationship_type)
            VALUES (?, ?, ?)
        """
        return db.execute_update(query, [project_id, opportunity_id, relationship_type])
    
    def remove_project_opportunity(self, project_id, opportunity_id):
        """Remove an opportunity from a project"""
        query = "DELETE FROM project_opportunities WHERE project_id = ? AND opportunity_id = ?"
        return db.execute_update(query, [project_id, opportunity_id])
    
    def get_project_opportunities(self, project_id):
        """Get all opportunities associated with a project"""
        query = """
            SELECT o.*, po.relationship_type, po.created_date as association_date
            FROM opportunities o
            JOIN project_opportunities po ON o.id = po.opportunity_id
            WHERE po.project_id = ?
            ORDER BY po.created_date DESC
        """
        return db.execute_query(query, [project_id])
    
    def get_projects_for_opportunity(self, opportunity_id):
        """Get all projects associated with an opportunity"""
        query = """
            SELECT p.*, po.relationship_type, po.created_date as association_date
            FROM projects p
            JOIN project_opportunities po ON p.id = po.project_id
            WHERE po.opportunity_id = ?
            ORDER BY po.created_date DESC
        """
        return db.execute_query(query, [opportunity_id])
    
    def get_projects_for_vendor(self, vendor_id):
        """Get all projects for a specific vendor"""
        return self.get_projects({'vendor_id': vendor_id})
    
    def get_project_budget_summary(self, project_id):
        """Get budget summary for a project"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        
        return {
            'budget': project['budget'],
            'actual_cost': project['actual_cost'],
            'variance': project['budget_variance'],
            'progress': project['progress_percentage'],
            'status': project['status']
        }

# Initialize data access layer
crm_data = CRMData()
