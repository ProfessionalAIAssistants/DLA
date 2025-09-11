"""
Email Automation System for Vendor Quote Requests
Generates professional RFQ emails with templates
"""

import sqlite3
from datetime import datetime, timedelta
import re
from pathlib import Path
from typing import Dict, List, Optional

class EmailAutomation:
    def __init__(self, db_path=None):
        # Default to data directory database path
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            self.db_path = str(base_dir / 'data' / 'crm.db')
        else:
            self.db_path = db_path
        self._ensure_email_tables()
        self._add_default_templates()
    
    def _ensure_email_tables(self):
        """Ensure email automation tables exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create vendor_rfq_emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_rfq_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                vendor_account_id INTEGER,
                vendor_contact_id INTEGER,
                rfq_email_id TEXT UNIQUE,
                subject TEXT,
                email_body TEXT,
                status TEXT DEFAULT 'Draft',
                created_date TEXT,
                sent_date TEXT,
                response_received_date TEXT,
                response_data TEXT,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                FOREIGN KEY (vendor_account_id) REFERENCES accounts (id),
                FOREIGN KEY (vendor_contact_id) REFERENCES contacts (id)
            )
        """)
        
        # Create email_templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                type TEXT,
                subject_template TEXT,
                body_template TEXT,
                variables TEXT,
                is_active INTEGER DEFAULT 1,
                created_date TEXT,
                modified_date TEXT
            )
        """)
        
        # Create quotes table (enhanced from RFQs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_email_id TEXT,
                vendor_account_id INTEGER,
                quote_number TEXT,
                quote_amount DECIMAL(10,2),
                lead_time TEXT,
                delivery_terms TEXT,
                validity_period TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Pending',
                quote_date TEXT,
                response_date TEXT,
                FOREIGN KEY (rfq_email_id) REFERENCES vendor_rfq_emails (id),
                FOREIGN KEY (vendor_account_id) REFERENCES accounts (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _add_default_templates(self):
        """Add default email templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        templates = [
            {
                'name': 'Standard RFQ Request',
                'type': 'RFQ',
                'subject_template': 'RFQ for {nsn} - {product_name} (Qty: {quantity})',
                'body_template': """Dear Sir/Madam,

We hope this message finds you well. We are reaching out to request a quote for the following item:

**REQUEST DETAILS:**
Supplier: {manufacturer}
P/N: {part_number}
Quantity: {quantity}
NSN: {nsn}

Please reply to this email with your quote. If you have any questions or need additional information, please don't hesitate to contact us.

Thank you for your time and consideration.

Best regards,
{buyer_name}""",
                'variables': 'nsn,product_name,manufacturer,part_number,quantity,buyer_name'
            },
            {
                'name': 'Urgent RFQ Request',
                'type': 'RFQ',
                'subject_template': 'URGENT RFQ {request_number} - {product_name} (Qty: {quantity}) - Response Needed ASAP',
                'body_template': """URGENT REQUEST - IMMEDIATE ATTENTION REQUIRED

Dear {vendor_contact_name},

We have an urgent requirement for the following item and need your immediate attention:

**URGENT REQUEST DETAILS:**
• Request Number: {request_number}
• Product: {product_name}
• Manufacturer: {manufacturer}
• Part Number: {part_number}
• Quantity: {quantity}
• URGENT DELIVERY REQUIRED BY: {required_delivery_date}

**CRITICAL SPECIFICATIONS:**
{product_description}

**IMMEDIATE ACTION REQUIRED:**
Due to the urgent nature of this request, we need your quote by {quote_deadline}.

Please respond immediately with:
• Best available pricing
• Earliest possible delivery date
• Product availability confirmation
• Lead time details

**CONTACT FOR IMMEDIATE RESPONSE:**
{buyer_name}
Direct Line: {buyer_phone}
Email: {buyer_email}

Time is critical - please respond as soon as possible.

Thank you for your urgent attention to this matter.

{buyer_name}
{buyer_title}
{company_name}

Reference ID: {rfq_email_id}""",
                'variables': 'request_number,product_name,manufacturer,part_number,quantity,required_delivery_date,product_description,quote_deadline,buyer_name,buyer_phone,buyer_email,buyer_title,company_name,vendor_contact_name,rfq_email_id'
            }
        ]
        
        for template in templates:
            cursor.execute("""
                INSERT OR REPLACE INTO email_templates 
                (name, type, subject_template, body_template, variables, created_date, modified_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                template['name'],
                template['type'],
                template['subject_template'],
                template['body_template'],
                template['variables'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def generate_rfq_email(self, opportunity_id: int, vendor_account_id: int, 
                          vendor_contact_id: Optional[int] = None, template_name: str = 'Standard RFQ Request') -> Dict:
        """Generate RFQ email for a specific vendor"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get opportunity details
        cursor.execute("""
            SELECT o.*, p.name as product_name, p.manufacturer, p.part_number, 
                   p.nsn, p.description as product_description,
                   a.name as account_name
            FROM opportunities o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN accounts a ON o.account_id = a.id
            WHERE o.id = ?
        """, (opportunity_id,))
        opportunity = cursor.fetchone()
        
        if not opportunity:
            conn.close()
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Get vendor account details
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (vendor_account_id,))
        vendor_account = cursor.fetchone()
        
        if not vendor_account:
            conn.close()
            raise ValueError(f"Vendor account {vendor_account_id} not found")
        
        # Get vendor contact details
        vendor_contact = None
        if vendor_contact_id:
            cursor.execute("SELECT * FROM contacts WHERE id = ? AND account_id = ?", 
                          (vendor_contact_id, vendor_account_id))
            vendor_contact = cursor.fetchone()
        
        # If no specific contact, get the first contact for the vendor
        if not vendor_contact:
            cursor.execute("""
                SELECT * FROM contacts WHERE account_id = ? 
                ORDER BY id ASC LIMIT 1
            """, (vendor_account_id,))
            vendor_contact = cursor.fetchone()
        
        # Get email template
        cursor.execute("SELECT * FROM email_templates WHERE name = ? AND is_active = 1", (template_name,))
        template = cursor.fetchone()
        
        if not template:
            conn.close()
            raise ValueError(f"Template '{template_name}' not found")
        
        # Generate unique RFQ email ID
        rfq_email_id = f"RFQ-{opportunity_id}-{vendor_account_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare template variables
        # Extract manufacturer and part number from mfr field if available
        mfr_text = opportunity['manufacturer'] if opportunity['manufacturer'] else opportunity['mfr'] if opportunity['mfr'] else ''
        
        # Try to extract part number from mfr field (format: "MANUFACTURER P/N PARTNUMBER")
        part_number = 'TBD'
        manufacturer = 'TBD'
        
        if mfr_text:
            if 'P/N' in mfr_text:
                parts = mfr_text.split('P/N')
                if len(parts) >= 2:
                    manufacturer = parts[0].strip()
                    part_number = parts[1].strip()
                else:
                    manufacturer = mfr_text
            else:
                manufacturer = mfr_text
        
        # Use explicit part_number field if available
        try:
            if opportunity['part_number']:
                part_number = opportunity['part_number']
        except (KeyError, IndexError):
            pass
        
        variables = {
            'request_number': f"RFQ-{opportunity['id']}-{datetime.now().strftime('%Y%m%d')}",
            'product_name': opportunity['product_name'] if opportunity['product_name'] else 'Product Name Not Available',
            'manufacturer': manufacturer,
            'part_number': part_number,
            'nsn': opportunity['nsn'] if opportunity['nsn'] else 'TBD',
            'quantity': opportunity['quantity'] if opportunity['quantity'] else 1,
            'delivery_address': 'DLA Distribution Center (Address to be provided)',
            'product_description': opportunity['product_description'] if opportunity['product_description'] else opportunity['description'] if opportunity['description'] else 'Description not available',
            'required_delivery_date': opportunity['close_date'] if opportunity['close_date'] else 'TBD',
            'fob_terms': opportunity['fob'] if opportunity['fob'] else 'DESTINATION',
            'iso_required': opportunity['iso'] if opportunity['iso'] else 'YES',
            'quote_deadline': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'buyer_name': opportunity['buyer'] if opportunity['buyer'] else 'THE BUYER',
            'buyer_email': 'buyer@company.com',
            'buyer_phone': '(555) 123-4567',
            'buyer_title': 'Procurement Specialist',
            'company_name': 'CDE Prosperity',
            'vendor_contact_name': f"{vendor_contact['first_name']} {vendor_contact['last_name']}" if vendor_contact else 'Sir/Madam',
            'rfq_email_id': rfq_email_id
        }
        
        # Replace template placeholders
        subject = self._replace_template_variables(template['subject_template'], variables)
        body = self._replace_template_variables(template['body_template'], variables)
        
        # Save email to database
        cursor.execute("""
            INSERT INTO vendor_rfq_emails 
            (opportunity_id, vendor_account_id, vendor_contact_id, rfq_email_id, 
             subject, email_body, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opportunity_id, vendor_account_id, vendor_contact_id, rfq_email_id,
            subject, body, 'Draft', datetime.now().isoformat()
        ))
        
        email_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            'id': email_id,
            'rfq_email_id': rfq_email_id,
            'subject': subject,
            'body': body,
            'vendor_name': vendor_account['name'],
            'vendor_email': vendor_contact['email'] if vendor_contact else None,
            'vendor_contact_name': variables['vendor_contact_name'],
            'status': 'Draft',
            'created_date': datetime.now().isoformat()
        }
    
    def _replace_template_variables(self, template: str, variables: Dict) -> str:
        """Replace template variables with actual values"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def generate_bulk_rfq_emails(self, opportunity_id: int, vendor_list: List[Dict], 
                                template_name: str = 'Standard RFQ Request') -> List[Dict]:
        """Generate RFQ emails for multiple vendors"""
        emails = []
        
        for vendor in vendor_list:
            vendor_account_id = vendor['account_id']
            vendor_contact_id = vendor.get('contact_id')
            
            try:
                email = self.generate_rfq_email(
                    opportunity_id, vendor_account_id, vendor_contact_id, template_name
                )
                emails.append(email)
            except Exception as e:
                print(f"Error generating email for vendor {vendor_account_id}: {e}")
                emails.append({
                    'vendor_account_id': vendor_account_id,
                    'error': str(e),
                    'status': 'Error'
                })
        
        return emails
    
    def get_vendor_emails_for_opportunity(self, opportunity_id: int) -> List[Dict]:
        """Get all vendor emails for an opportunity"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ve.*, a.name as vendor_name, c.first_name, c.last_name, c.email
            FROM vendor_rfq_emails ve
            LEFT JOIN accounts a ON ve.vendor_account_id = a.id
            LEFT JOIN contacts c ON ve.vendor_contact_id = c.id
            WHERE ve.opportunity_id = ?
            ORDER BY ve.created_date DESC
        """, (opportunity_id,))
        
        emails = []
        for row in cursor.fetchall():
            emails.append(dict(row))
        
        conn.close()
        return emails
    
    def update_email_status(self, email_id: int, status: str, response_data: str = None) -> bool:
        """Update email status and response data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ['status = ?']
        values = [status]
        
        if status == 'Sent':
            update_fields.append('sent_date = ?')
            values.append(datetime.now().isoformat())
        elif status == 'Responded':
            update_fields.append('response_received_date = ?')
            values.append(datetime.now().isoformat())
            if response_data:
                update_fields.append('response_data = ?')
                values.append(response_data)
        
        values.append(email_id)
        
        cursor.execute(f"""
            UPDATE vendor_rfq_emails 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_email_templates(self) -> List[Dict]:
        """Get all available email templates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM email_templates 
            WHERE is_active = 1 
            ORDER BY type, name
        """)
        
        templates = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return templates
    
    def preview_email(self, opportunity_id: int, vendor_account_id: int, 
                     template_name: str = 'Standard RFQ Request') -> Dict:
        """Preview email without saving to database"""
        # This generates the email content but doesn't save it
        # Useful for previewing before sending
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get opportunity details (same as generate_rfq_email but without saving)
        cursor.execute("""
            SELECT o.*, p.name as product_name, p.manufacturer, p.part_number, 
                   p.nsn, p.description as product_description
            FROM opportunities o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        """, (opportunity_id,))
        opportunity = cursor.fetchone()
        
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (vendor_account_id,))
        vendor_account = cursor.fetchone()
        
        cursor.execute("SELECT * FROM email_templates WHERE name = ?", (template_name,))
        template = cursor.fetchone()
        
        conn.close()
        
        if not all([opportunity, vendor_account, template]):
            return {'error': 'Missing required data for preview'}
        
        # Generate preview variables (simplified)
        variables = {
            'request_number': opportunity['request_number'] if opportunity['request_number'] else f"REQ-{opportunity['id']}",
            'product_name': opportunity['product_name'] if opportunity['product_name'] else 'Product Name',
            'manufacturer': opportunity['manufacturer'] if opportunity['manufacturer'] else 'TBD',
            'quantity': opportunity['quantity'] if opportunity['quantity'] else 1,
            'vendor_contact_name': 'Vendor Contact',
            'buyer_name': 'THE BUYER'
        }
        
        # Create preview
        subject = self._replace_template_variables(template['subject_template'], variables)
        body = self._replace_template_variables(template['body_template'], variables)
        
        return {
            'subject': subject,
            'body': body,
            'vendor_name': vendor_account['name'],
            'template_name': template_name
        }
    
    def get_vendor_email_content(self, email_id: str) -> Dict:
        """Get the content of a specific vendor email for preview"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ve.*, a.name as vendor_name, c.first_name, c.last_name, c.email as vendor_email
            FROM vendor_rfq_emails ve
            LEFT JOIN accounts a ON ve.vendor_account_id = a.id
            LEFT JOIN contacts c ON ve.vendor_contact_id = c.id
            WHERE ve.rfq_email_id = ?
        """, (email_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        else:
            return None

# Global instance
email_automation = EmailAutomation()
