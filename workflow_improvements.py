"""
Workflow Enhancement Script for CRM System
Implements missing features for the complete PDF-to-Project workflow
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

class WorkflowEnhancer:
    def __init__(self):
        self.db_path = "crm.db"
        
    def add_missing_tables(self):
        """Add tables for enhanced workflow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vendor RFQ Emails table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendor_rfq_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                vendor_account_id INTEGER,
                vendor_contact_id INTEGER,
                rfq_email_id TEXT UNIQUE,  -- Unique ID for tracking responses
                subject TEXT,
                email_body TEXT,
                sent_date DATETIME,
                status TEXT DEFAULT 'Sent',  -- Sent, Responded, No Response
                response_received_date DATETIME,
                response_email_body TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                FOREIGN KEY (vendor_account_id) REFERENCES accounts (id),
                FOREIGN KEY (vendor_contact_id) REFERENCES contacts (id)
            )
        ''')
        
        # Email Templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,  -- RFQ_REQUEST, QUOTE_FOLLOWUP, etc
                subject_template TEXT,
                body_template TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Enhanced quotes table (separate from RFQs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                vendor_account_id INTEGER,
                vendor_contact_id INTEGER,
                rfq_email_id INTEGER,
                quote_number TEXT,
                quote_amount DECIMAL(15, 2),
                lead_time TEXT,
                valid_until DATE,
                terms TEXT,
                status TEXT DEFAULT 'Received',  -- Received, Under Review, Accepted, Rejected
                received_date DATETIME,
                reviewed_date DATETIME,
                decision_date DATETIME,
                notes TEXT,
                document_path TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                FOREIGN KEY (vendor_account_id) REFERENCES accounts (id),
                FOREIGN KEY (vendor_contact_id) REFERENCES contacts (id),
                FOREIGN KEY (rfq_email_id) REFERENCES vendor_rfq_emails (id)
            )
        ''')
        
        # Enhanced interactions for email tracking
        cursor.execute('''
            ALTER TABLE interactions ADD COLUMN email_type TEXT;
        ''')
        
        cursor.execute('''
            ALTER TABLE interactions ADD COLUMN reference_id TEXT;
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Enhanced database schema created")
    
    def add_email_templates(self):
        """Add default email templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        templates = [
            {
                'name': 'RFQ Request to Vendor',
                'type': 'RFQ_REQUEST',
                'subject_template': 'RFQ {rfq_number} - {product_description}',
                'body_template': '''Dear {contact_name},

We are requesting a quote for the following opportunity:

RFQ Number: {rfq_number}
Product: {product_description}
NSN: {nsn}
Quantity: {quantity}
Delivery Required: {delivery_date}

Please provide your best quote including:
- Unit price
- Lead time
- Terms and conditions
- Any certifications or compliance requirements

Please reply to this email with your quote. Reference ID: {rfq_email_id}

Best regards,
{sender_name}
{company_name}'''
            },
            {
                'name': 'Quote Follow-up',
                'type': 'QUOTE_FOLLOWUP',
                'subject_template': 'Follow-up: RFQ {rfq_number}',
                'body_template': '''Dear {contact_name},

We sent you an RFQ on {sent_date} for {product_description}.

We would appreciate receiving your quote by {deadline_date} to ensure consideration.

Reference ID: {rfq_email_id}

Thank you,
{sender_name}'''
            }
        ]
        
        for template in templates:
            cursor.execute('''
                INSERT OR REPLACE INTO email_templates 
                (name, type, subject_template, body_template)
                VALUES (?, ?, ?, ?)
            ''', (template['name'], template['type'], 
                  template['subject_template'], template['body_template']))
        
        conn.commit()
        conn.close()
        print("✅ Email templates added")
    
    def add_workflow_functions(self):
        """Add workflow-specific database functions"""
        # This would be implemented in crm_data.py
        workflow_code = '''
# Add these methods to CRMData class:

def generate_rfq_emails(self, opportunity_id, vendor_list):
    """Generate RFQ emails for multiple vendors"""
    emails = []
    opportunity = self.get_opportunity_by_id(opportunity_id)
    
    for vendor in vendor_list:
        rfq_email_id = f"RFQ-{opportunity_id}-{vendor['id']}-{int(datetime.now().timestamp())}"
        
        # Create email record
        email_data = {
            'opportunity_id': opportunity_id,
            'vendor_account_id': vendor['id'],
            'vendor_contact_id': vendor.get('contact_id'),
            'rfq_email_id': rfq_email_id,
            'subject': f"RFQ {opportunity['name']} - Quote Request",
            'email_body': self._generate_email_body(opportunity, vendor, rfq_email_id),
            'sent_date': datetime.now().isoformat(),
            'status': 'Pending'
        }
        
        # Store in database
        query = """INSERT INTO vendor_rfq_emails 
                   (opportunity_id, vendor_account_id, vendor_contact_id, 
                    rfq_email_id, subject, email_body, sent_date, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        
        email_id = db.execute_update(query, [
            email_data['opportunity_id'], email_data['vendor_account_id'],
            email_data['vendor_contact_id'], email_data['rfq_email_id'],
            email_data['subject'], email_data['email_body'],
            email_data['sent_date'], email_data['status']
        ])
        
        emails.append({'id': email_id, **email_data})
    
    return emails

def process_vendor_response(self, rfq_email_id, response_email):
    """Process vendor email response and create quote"""
    # Find original RFQ email
    rfq_email = self.execute_query(
        "SELECT * FROM vendor_rfq_emails WHERE rfq_email_id = ?",
        [rfq_email_id]
    )
    
    if not rfq_email:
        return None
    
    rfq_email = rfq_email[0]
    
    # Parse email for quote information
    quote_data = self._parse_quote_from_email(response_email)
    
    # Create quote record
    quote_id = self.create_quote(
        opportunity_id=rfq_email['opportunity_id'],
        vendor_account_id=rfq_email['vendor_account_id'],
        vendor_contact_id=rfq_email['vendor_contact_id'],
        rfq_email_id=rfq_email['id'],
        **quote_data
    )
    
    # Update RFQ email status
    self.execute_update(
        "UPDATE vendor_rfq_emails SET status = ?, response_received_date = ? WHERE id = ?",
        ['Responded', datetime.now().isoformat(), rfq_email['id']]
    )
    
    # Create interaction record
    self.create_interaction(
        type='Email',
        direction='Inbound',
        subject=f"Quote Response: {rfq_email['subject']}",
        notes=response_email.get('body', ''),
        contact_id=rfq_email['vendor_contact_id'],
        account_id=rfq_email['vendor_account_id'],
        opportunity_id=rfq_email['opportunity_id'],
        email_type='QUOTE_RESPONSE',
        reference_id=rfq_email_id
    )
    
    return quote_id

def create_project_from_opportunity(self, opportunity_id):
    """Auto-create project when opportunity is won"""
    opportunity = self.get_opportunity_by_id(opportunity_id)
    if not opportunity:
        return None
    
    project_data = {
        'name': f"Project: {opportunity['name']}",
        'summary': f"Project created from won opportunity: {opportunity['name']}",
        'status': 'Not Started',
        'priority': 'High',
        'start_date': datetime.now().date().isoformat(),
        'project_manager': 'TBD',
        'budget': opportunity.get('bid_price', 0) * opportunity.get('quantity', 1),
        'description': f"""Project automatically created from opportunity {opportunity['name']}.

Original RFQ Details:
- Product: {opportunity.get('description', 'N/A')}
- Quantity: {opportunity.get('quantity', 'N/A')}
- Bid Amount: ${opportunity.get('bid_price', 0):,.2f}
- Delivery Required: {opportunity.get('close_date', 'TBD')}

Next Steps:
1. Assign project manager
2. Create detailed project plan
3. Set up vendor agreements
4. Begin procurement process
"""
    }
    
    project_id = self.create_project(**project_data)
    
    # Link opportunity to project
    self.execute_update(
        "UPDATE opportunities SET project_id = ? WHERE id = ?",
        [project_id, opportunity_id]
    )
    
    return project_id
'''
        
        print("✅ Workflow functions documented (implement in crm_data.py)")
        return workflow_code

    def create_workflow_routes(self):
        """Create Flask routes for workflow automation"""
        routes_code = '''
    routes_code = '''
# Add these routes to crm_app.py:

@app.route('/api/opportunities/<int:opportunity_id>/send-rfqs', methods=['POST'])
def send_rfq_emails(opportunity_id):
    """Send RFQ emails to selected vendors"""
    try:
        data = request.get_json()
        vendor_list = data.get('vendors', [])
        
        if not vendor_list:
            return jsonify({'success': False, 'message': 'No vendors selected'})
        
        # Generate RFQ emails
        emails = crm_data.generate_rfq_emails(opportunity_id, vendor_list)
        
        # TODO: Integrate with actual email service (SMTP/SendGrid/etc)
        # For now, just create the records
        
        # Update opportunity status
        crm_data.update_opportunity(opportunity_id, stage='RFQ Requested')
        
        # Create review task
        task_id = crm_data.create_task(
            subject=f"Follow up on RFQ responses for Opportunity {opportunity_id}",
            description=f"Monitor vendor responses for {len(emails)} RFQ emails sent",
            status="Not Started",
            priority="High",
            due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            opportunity_id=opportunity_id
        )
        
        return jsonify({
            'success': True,
            'emails_sent': len(emails),
            'task_created': task_id,
            'message': f'RFQ emails generated for {len(emails)} vendors'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/quotes')
def get_opportunity_quotes(opportunity_id):
    """Get all quotes for an opportunity"""
    try:
        quotes = crm_data.execute_query("""
            SELECT q.*, a.name as vendor_name, c.first_name, c.last_name
            FROM quotes q
            LEFT JOIN accounts a ON q.vendor_account_id = a.id
            LEFT JOIN contacts c ON q.vendor_contact_id = c.id
            WHERE q.opportunity_id = ?
            ORDER BY q.quote_amount ASC
        """, [opportunity_id])
        
        return jsonify({'success': True, 'quotes': quotes})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/auto-project', methods=['POST'])
def create_project_from_won_opportunity(opportunity_id):
    """Auto-create project when opportunity is marked as won"""
    try:
        # Verify opportunity is won
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'success': False, 'message': 'Opportunity not found'})
        
        if opportunity.get('state') != 'Won':
            return jsonify({'success': False, 'message': 'Opportunity must be marked as Won first'})
        
        # Create project
        project_id = crm_data.create_project_from_opportunity(opportunity_id)
        
        if project_id:
            return jsonify({
                'success': True,
                'project_id': project_id,
                'message': 'Project created successfully from won opportunity'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to create project'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-responses', methods=['POST'])
def process_email_response():
    """Process incoming email responses (webhook endpoint)"""
    try:
        email_data = request.get_json()
        
        # Extract RFQ ID from email subject or body
        rfq_email_id = extract_rfq_id_from_email(email_data)
        
        if rfq_email_id:
            quote_id = crm_data.process_vendor_response(rfq_email_id, email_data)
            
            if quote_id:
                # Create review task
                crm_data.create_task(
                    subject=f"Review new quote #{quote_id}",
                    description="New vendor quote received and parsed",
                    status="Not Started",
                    priority="High",
                    due_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                return jsonify({'success': True, 'quote_id': quote_id})
        
        return jsonify({'success': False, 'message': 'Could not process email'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
'''
    
    print("✅ Flask routes documented (implement in crm_app.py)")
    return routes_code

def create_ui_enhancements(self):
    """Create UI enhancements for workflow"""
    ui_code = '''
<!-- Add to opportunity_detail.html -->

<!-- RFQ Email Section -->
<div class="card mb-4">
    <div class="card-header">
        <h5 class="mb-0"><i class="fas fa-envelope me-2"></i>RFQ Management</h5>
    </div>
    <div class="card-body">
        {% if opportunity.stage == 'RFQ Requested' %}
        <div class="alert alert-info">
            <i class="fas fa-info-circle me-2"></i>
            RFQ emails have been sent to vendors. Monitor responses below.
        </div>
        {% endif %}
        
        <div class="row">
            <div class="col-md-6">
                <button class="btn btn-primary" onclick="sendRFQEmails({{ opportunity.id }})">
                    <i class="fas fa-paper-plane me-2"></i>Send RFQ to Vendors
                </button>
            </div>
            <div class="col-md-6">
                <button class="btn btn-outline-secondary" onclick="viewQuotes({{ opportunity.id }})">
                    <i class="fas fa-file-invoice-dollar me-2"></i>View Quotes
                </button>
            </div>
        </div>
    </div>
</div>

<!-- Quotes Summary -->
<div id="quotesSection" class="card mb-4" style="display: none;">
    <div class="card-header">
        <h5 class="mb-0"><i class="fas fa-chart-line me-2"></i>Quote Analysis</h5>
    </div>
    <div class="card-body">
        <div id="quotesTable"></div>
    </div>
</div>

<script>
function sendRFQEmails(opportunityId) {
    // Show vendor selection modal
    showVendorSelectionModal(opportunityId);
}

function showVendorSelectionModal(opportunityId) {
    // Implementation for vendor selection
    // This would show a modal with vendor checkboxes
    // Then call /api/opportunities/{id}/send-rfqs
}

function viewQuotes(opportunityId) {
    fetch(`/api/opportunities/${opportunityId}/quotes`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayQuotes(data.quotes);
            document.getElementById('quotesSection').style.display = 'block';
        }
    });
}

function displayQuotes(quotes) {
    const quotesTable = document.getElementById('quotesTable');
    
    if (quotes.length === 0) {
        quotesTable.innerHTML = '<p class="text-muted">No quotes received yet.</p>';
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Vendor</th>
                        <th>Quote Amount</th>
                        <th>Lead Time</th>
                        <th>Received</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    quotes.forEach(quote => {
        html += `
            <tr>
                <td>${quote.vendor_name}</td>
                <td>$${quote.quote_amount?.toLocaleString() || 'TBD'}</td>
                <td>${quote.lead_time || 'TBD'}</td>
                <td>${quote.received_date ? new Date(quote.received_date).toLocaleDateString() : 'Pending'}</td>
                <td><span class="badge bg-${quote.status === 'Accepted' ? 'success' : 'secondary'}">${quote.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="reviewQuote(${quote.id})">
                        <i class="fas fa-eye"></i> Review
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    quotesTable.innerHTML = html;
}

// Auto-create project when opportunity is won
function markWon(opportunityId) {
    if (confirm('Mark this opportunity as Won and create a project?')) {
        fetch(`/api/opportunities/${opportunityId}/won`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Auto-create project
                fetch(`/api/opportunities/${opportunityId}/auto-project`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(projectData => {
                    if (projectData.success) {
                        alert(`Opportunity won! Project #${projectData.project_id} created automatically.`);
                        location.reload();
                    }
                });
            }
        });
    }
}
</script>
'''
    
    print("✅ UI enhancements documented (implement in templates)")
    return ui_code

if __name__ == "__main__":
    enhancer = WorkflowEnhancer()
    
    print("🚀 CRM Workflow Enhancement Script")
    print("=" * 50)
    
    # Create enhanced database schema
    enhancer.add_missing_tables()
    enhancer.add_email_templates()
    
    # Generate code for implementation
    workflow_functions = enhancer.add_workflow_functions()
    flask_routes = enhancer.create_workflow_routes()
    ui_enhancements = enhancer.create_ui_enhancements()
    
    print("\n📋 IMPLEMENTATION SUMMARY:")
    print("=" * 50)
    print("✅ Database schema enhanced with:")
    print("   - vendor_rfq_emails table")
    print("   - email_templates table") 
    print("   - quotes table")
    print("   - Enhanced interactions table")
    
    print("\n📝 CODE TO IMPLEMENT:")
    print("1. Add workflow functions to crm_data.py")
    print("2. Add Flask routes to crm_app.py")
    print("3. Enhance UI templates")
    print("4. Set up email service integration")
    
    print("\n🔄 COMPLETE WORKFLOW WILL BE:")
    print("1. ✅ Load PDFs → Parse → Create Opportunities")
    print("2. ✅ Manual review of opportunities")
    print("3. 🆕 Set status to 'Quote Requested' → Generate vendor RFQ emails")
    print("4. 🆕 Email vendors with unique tracking IDs")
    print("5. 🆕 Log email interactions")
    print("6. 🆕 Process email responses → Create quotes")
    print("7. 🆕 Auto-parse quote details")
    print("8. 🆕 Update opportunity to 'Quote Received'")
    print("9. 🆕 Create review tasks")
    print("10. ✅ Submit bid → Wait for win")
    print("11. 🆕 Mark won → Auto-create project")
    
    print("\n⚠️  NEXT STEPS:")
    print("1. Run this script to update database")
    print("2. Implement the documented code")
    print("3. Set up email service (SMTP/SendGrid)")
    print("4. Configure email parsing webhooks")
    print("5. Test the complete workflow")
