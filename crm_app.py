# Local CRM Web Interface
# Flask-based web interface for the CRM system

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, timedelta
import json
import os
import traceback
import logging
import sqlite3
from pathlib import Path

# Import our CRM modules
from crm_data import crm_data
from crm_automation import crm_automation
from pdf_processor import pdf_processor
from email_automation import email_automation

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configure template and static folders
app.template_folder = 'templates'
app.static_folder = 'static'

# Add custom Jinja2 filters
@app.template_filter('to_datetime')
def to_datetime_filter(date_string):
    """Convert ISO date string to datetime object"""
    try:
        # Handle ISO format with microseconds: 2025-08-21T07:13:48.728809
        if '.' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return datetime.now()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crm_app.log')
    ]
)

# Add built-in functions to Jinja2 environment
app.jinja_env.globals.update(abs=abs)

def paginate_results(data, page, per_page=10):
    """Paginate a list of results"""
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': data[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page < (total + per_page - 1) // per_page,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < (total + per_page - 1) // per_page else None
    }

@app.route('/')
def dashboard():
    """Main dashboard view"""
    dashboard_data = crm_automation.get_daily_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data)

@app.route('/settings')
def settings():
    """Settings page for PDF processing filters"""
    current_settings = pdf_processor.get_filter_settings()
    
    # Get processing statistics
    stats = {
        'processed': 0,
        'skipped': 0
    }
    
    # Count files in reviewed folders
    reviewed_dir = Path("Reviewed")
    if reviewed_dir.exists():
        stats['processed'] = len(list(reviewed_dir.glob("*.pdf"))) + len(list(reviewed_dir.glob("*.PDF")))
        
        skipped_dir = reviewed_dir / "Skipped"
        if skipped_dir.exists():
            stats['skipped'] = len(list(skipped_dir.glob("*.pdf"))) + len(list(skipped_dir.glob("*.PDF")))
    
    return render_template('settings.html', settings=current_settings, stats=stats)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update PDF processing filter settings"""
    try:
        settings_data = request.get_json()
        pdf_processor.update_filter_settings(settings_data)
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings/automation', methods=['POST'])
def update_automation_settings():
    """Update automation settings"""
    try:
        # For now, just return success - implement actual automation settings storage later
        settings_data = request.get_json() or {}
        
        # Log what settings were received
        app.logger.info(f"Automation settings updated: {settings_data}")
        
        return jsonify({'success': True, 'message': 'Automation settings saved successfully'})
    except Exception as e:
        app.logger.error(f"Error updating automation settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings/email', methods=['GET', 'POST'])
def handle_email_settings():
    """Handle email settings GET and POST requests"""
    if request.method == 'GET':
        try:
            # Load email settings from config file
            import os
            import json
            
            config_path = 'email_config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                return jsonify({'success': True, 'settings': settings})
            else:
                # Return default settings
                default_settings = {
                    "smtp_configuration": {
                        "enabled": False,
                        "host": "",
                        "port": 587,
                        "username": "",
                        "from_name": "CDE Prosperity DLA Team",
                        "reply_to_email": ""
                    },
                    "rfq_automation": {
                        "enabled": False,
                        "require_manual_review": True,
                        "auto_send_approved": False,
                        "default_priority": "Normal",
                        "quote_deadline_days": 10,
                        "max_daily_sends": 50,
                        "follow_up_delay_days": 3,
                        "business_hours_only": True,
                        "weekend_sending": False,
                        "business_start_hour": 8,
                        "business_end_hour": 17
                    },
                    "response_processing": {
                        "enabled": True,
                        "auto_parse_responses": True,
                        "require_quote_review": True,
                        "parse_pdf_attachments": True,
                        "create_follow_up_tasks": True
                    },
                    "notification_settings": {
                        "notification_email": "",
                        "daily_summary_time": "17:00",
                        "notify_on_rfq_sent": True,
                        "notify_on_response_received": True,
                        "alert_on_urgent_quotes": True,
                        "send_daily_digest": False
                    }
                }
                return jsonify({'success': True, 'settings': default_settings})
        except Exception as e:
            app.logger.error(f"Error loading email settings: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            import json
            import os
            
            settings_data = request.get_json() or {}
            
            # Save to email_config.json
            config_path = 'email_config.json'
            
            # Load existing config if it exists
            existing_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
            
            # Update with new settings
            existing_config.update(settings_data)
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            app.logger.info(f"Email settings updated and saved to {config_path}")
            
            return jsonify({'success': True, 'message': 'Email settings saved successfully'})
        except Exception as e:
            app.logger.error(f"Error updating email settings: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings/email/test', methods=['POST'])
def test_email_connection():
    """Test email connection with provided settings"""
    try:
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        settings_data = request.get_json() or {}
        smtp_config = settings_data.get('smtp_configuration', {})
        
        if not smtp_config.get('enabled'):
            return jsonify({'success': False, 'message': 'Email is not enabled'})
        
        if not all([smtp_config.get('host'), smtp_config.get('username'), smtp_config.get('password')]):
            return jsonify({'success': False, 'message': 'Missing required SMTP configuration'})
        
        # Test SMTP connection
        try:
            if smtp_config.get('use_tls', True):
                context = ssl.create_default_context()
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()
            
            return jsonify({'success': True, 'message': 'Email connection test successful'})
            
        except smtplib.SMTPAuthenticationError:
            return jsonify({'success': False, 'message': 'Authentication failed. Check username and password.'})
        except smtplib.SMTPConnectError:
            return jsonify({'success': False, 'message': 'Could not connect to SMTP server. Check host and port.'})
        except Exception as smtp_error:
            return jsonify({'success': False, 'message': f'SMTP error: {str(smtp_error)}'})
        
    except Exception as e:
        app.logger.error(f"Error testing email connection: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/settings/email/status', methods=['GET'])
def get_email_status():
    """Get current email system status"""
    try:
        import os
        import json
        
        # Check if email is configured
        config_path = 'email_config.json'
        connection_status = 'not_configured'
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                smtp_config = config.get('smtp_configuration', {})
                if smtp_config.get('enabled') and smtp_config.get('host') and smtp_config.get('username'):
                    connection_status = 'configured'
        
        # Get email statistics from database
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        # Emails sent today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM vendor_rfq_emails 
            WHERE DATE(sent_date) = ? AND status = 'Sent'
        """, (today,))
        emails_sent_today = cursor.fetchone()[0]
        
        # Responses received this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM vendor_rfq_emails 
            WHERE response_received_date >= ?
        """, (week_ago,))
        responses_received = cursor.fetchone()[0]
        
        conn.close()
        
        status = {
            'connection_status': connection_status,
            'emails_sent_today': emails_sent_today,
            'responses_received': responses_received
        }
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        app.logger.error(f"Error getting email status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/accounts')
def accounts():
    """Accounts list view with pagination"""
    search = request.args.get('search', '')
    account_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if search:
        filters['name'] = search
    if account_type:
        filters['type'] = account_type
    
    accounts_list = crm_data.get_accounts(filters)
    pagination = paginate_results(accounts_list, page)
    
    return render_template('accounts.html', 
                         accounts=pagination['items'], 
                         pagination=pagination,
                         search=search, 
                         account_type=account_type)

@app.route('/account/<int:account_id>')
def account_detail(account_id):
    """Account detail view"""
    account = crm_data.get_account_by_id(account_id)
    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('accounts'))
    
    # Get related records
    contacts = crm_data.get_contacts({'account_id': account_id})
    opportunities = crm_data.get_opportunities({'account_id': account_id})
    interactions = crm_data.get_interactions({'account_id': account_id})
    
    return render_template('account_detail.html', 
                         account=account, 
                         contacts=contacts, 
                         opportunities=opportunities, 
                         interactions=interactions)

@app.route('/contacts')
def contacts():
    """Contacts list view with pagination"""
    search = request.args.get('search', '')
    account_id = request.args.get('account_id', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if search:
        filters['name'] = search
    if account_id:
        filters['account_id'] = account_id
    
    contacts_list = crm_data.get_contacts(filters)
    accounts_list = crm_data.get_accounts()  # For filter dropdown
    pagination = paginate_results(contacts_list, page)
    
    return render_template('contacts.html', 
                         contacts=pagination['items'], 
                         pagination=pagination,
                         accounts=accounts_list, 
                         search=search, 
                         account_id=account_id)

@app.route('/contact/<int:contact_id>')
def contact_detail(contact_id):
    """Contact detail view"""
    contact = crm_data.get_contact_by_id(contact_id)
    if not contact:
        flash('Contact not found', 'error')
        return redirect(url_for('contacts'))
    
    # Get related records
    interactions = crm_data.get_interactions({'contact_id': contact_id})
    opportunities = crm_data.get_opportunities({'contact_id': contact_id})
    
    # Get account info if available
    account = None
    if contact.get('account_id'):
        account = crm_data.get_account_by_id(contact['account_id'])
    
    return render_template('contact_detail.html', 
                         contact=contact, 
                         account=account,
                         interactions=interactions, 
                         opportunities=opportunities)

@app.route('/opportunities')
def opportunities():
    """Opportunities list view with comprehensive filtering and pagination"""
    # Get filter parameters
    stage = request.args.get('stage', '')
    state = request.args.get('state', '')
    iso = request.args.get('iso', '')
    fob = request.args.get('fob', '')
    buyer = request.args.get('buyer', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    # Build filters
    filters = {}
    if stage:
        filters['stage'] = stage
    if state:
        filters['state'] = state
    if iso:
        filters['iso'] = iso
    if fob:
        filters['fob'] = fob
    if buyer:
        filters['buyer'] = buyer
    if search:
        filters['search'] = search
    
    # Get opportunities and stats
    opportunities_list = crm_data.get_opportunities(filters)
    stats = crm_data.get_opportunity_stats()
    
    # Calculate RFQ-specific stats
    rfq_stats = crm_data.get_rfq_stats()
    
    pagination = paginate_results(opportunities_list, page)
    
    # Get related data for dropdowns
    accounts_list = crm_data.get_accounts()
    contacts_list = crm_data.get_contacts()
    products_list = crm_data.get_products()
    
    return render_template('opportunities.html', 
                         opportunities=pagination['items'],
                         pagination=pagination,
                         stats=stats,
                         rfq_stats=rfq_stats,
                         accounts=accounts_list,
                         contacts=contacts_list,
                         products=products_list,
                         stage=stage,
                         state=state,
                         iso=iso,
                         fob=fob,
                         buyer=buyer,
                         search=search)

@app.route('/opportunity/<int:opportunity_id>')
def opportunity_detail(opportunity_id):
    """Opportunity detail view"""
    opportunity = crm_data.get_opportunity_by_id(opportunity_id)
    if not opportunity:
        return render_template('error.html', message='Opportunity not found'), 404
    
    # Get related data
    account = crm_data.get_account_by_id(opportunity['account_id']) if opportunity['account_id'] else None
    contact = crm_data.get_contact_by_id(opportunity['contact_id']) if opportunity['contact_id'] else None
    product = crm_data.get_product_by_id(opportunity['product_id']) if opportunity['product_id'] else None
    
    # Get related interactions
    interactions = crm_data.get_interactions({'opportunity_id': opportunity_id})
    
    return render_template('opportunity_detail.html', 
                         opportunity=opportunity,
                         account=account,
                         contact=contact,
                         product=product,
                         interactions=interactions)

# ==================== OPPORTUNITIES API ROUTES ====================

@app.route('/api/opportunities', methods=['POST'])
def create_opportunity_api():
    """Create a new opportunity via API"""
    try:
        data = {}
        # Handle form data or JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Convert numeric fields
        numeric_fields = ['bid_price', 'purchase_costs', 'packaging_shipping', 'quantity', 'days_aod']
        for field in numeric_fields:
            if field in data and data[field]:
                try:
                    data[field] = float(data[field]) if field != 'quantity' and field != 'days_aod' else int(data[field])
                except ValueError:
                    return jsonify({'success': False, 'message': f'Invalid {field} value'})
        
        # Convert relationship fields
        relationship_fields = ['account_id', 'contact_id', 'product_id']
        for field in relationship_fields:
            if field in data and data[field]:
                try:
                    data[field] = int(data[field])
                except ValueError:
                    data[field] = None
        
        # Create opportunity
        opportunity_id = crm_data.create_opportunity(**data)
        
        if opportunity_id:
            return jsonify({'success': True, 'id': opportunity_id})
        else:
            return jsonify({'success': False, 'message': 'Failed to create opportunity'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>', methods=['GET'])
def get_opportunity_api(opportunity_id):
    """Get a single opportunity via API"""
    try:
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if opportunity:
            # Convert Row object to dict for JSON serialization
            opportunity_dict = dict(opportunity) if opportunity else None
            return jsonify({'success': True, 'opportunity': opportunity_dict})
        else:
            return jsonify({'success': False, 'message': 'Opportunity not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>', methods=['PATCH'])
def update_opportunity_api(opportunity_id):
    """Update an opportunity via API"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Convert numeric fields
        numeric_fields = ['bid_price', 'purchase_costs', 'packaging_shipping', 'quantity', 'days_aod']
        for field in numeric_fields:
            if field in data and data[field]:
                try:
                    data[field] = float(data[field]) if field != 'quantity' and field != 'days_aod' else int(data[field])
                except ValueError:
                    return jsonify({'success': False, 'message': f'Invalid {field} value'})
        
        result = crm_data.update_opportunity(opportunity_id, **data)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to update opportunity'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>', methods=['DELETE'])
def delete_opportunity_api(opportunity_id):
    """Delete an opportunity via API"""
    try:
        result = crm_data.delete_opportunity(opportunity_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete opportunity'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/advance', methods=['POST'])
def advance_opportunity_stage_api(opportunity_id):
    """Advance an opportunity to the next stage"""
    try:
        result = crm_data.advance_opportunity_stage(opportunity_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to advance stage or already at final stage'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/won', methods=['POST'])
def mark_opportunity_won_api(opportunity_id):
    """Mark an opportunity as won"""
    try:
        result = crm_data.mark_opportunity_won(opportunity_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to mark opportunity as won'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/lost', methods=['POST'])
def mark_opportunity_lost_api(opportunity_id):
    """Mark an opportunity as lost"""
    try:
        data = request.get_json() if request.is_json else {}
        reason = data.get('reason', '')
        
        result = crm_data.mark_opportunity_lost(opportunity_id, reason)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to mark opportunity as lost'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/create-project', methods=['POST'])
def create_project_from_opportunity(opportunity_id):
    """Auto-create project when opportunity is won"""
    try:
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'success': False, 'message': 'Opportunity not found'})
        
        # Create project with opportunity data
        from datetime import date
        
        # Safely get numeric values with proper defaults
        bid_price = opportunity.get('bid_price') or 0
        quantity = opportunity.get('quantity') or 0
        
        project_data = {
            'name': f"Project: {opportunity['name']}",
            'summary': f"Project created from won opportunity: {opportunity['name']}",
            'status': 'Not Started',
            'priority': 'High',
            'start_date': date.today().isoformat(),
            'project_manager': 'TBD',
            'description': f"""Project automatically created from opportunity {opportunity['name']}.

Original RFQ Details:
- Product: {opportunity.get('description', 'N/A')}
- Quantity: {quantity}
- Bid Amount: ${bid_price:,.2f}
- Delivery Required: {opportunity.get('close_date', 'TBD')}

Next Steps:
1. Assign project manager
2. Create detailed project plan
3. Set up vendor agreements
4. Begin procurement process
"""
        }
        
        # Calculate budget from opportunity
        if bid_price and quantity:
            project_data['budget'] = bid_price * quantity
        
        project_id = crm_data.create_project(**project_data)
        
        if project_id:
            # Link opportunity to project
            crm_data.update_opportunity(opportunity_id, project_id=project_id)
            
            # Update opportunity state to Won if not already
            if opportunity.get('state') != 'Won':
                crm_data.update_opportunity(opportunity_id, state='Won', stage='Project Started')
            
            # Create initial project task
            from datetime import datetime
            crm_data.create_task(
                subject=f"Project Planning: {opportunity['name']}",
                description=f"""Initial project planning for {opportunity['name']}:

1. Review opportunity requirements
2. Assign project manager
3. Create detailed timeline
4. Set up vendor communications
5. Begin procurement process

Project ID: {project_id}
Opportunity ID: {opportunity_id}
""",
                status="Not Started",
                priority="High",
                due_date=date.today().isoformat(),
                parent_item_type="Project",
                parent_item_id=project_id
            )
            
            return jsonify({
                'success': True,
                'project_id': project_id,
                'message': 'Project created successfully from opportunity'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to create project'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/rfqs')
def rfqs():
    """RFQs list view with pagination"""
    status = request.args.get('status', '')
    manufacturer = request.args.get('manufacturer', '')
    vendor = request.args.get('vendor', '')
    product = request.args.get('product', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if status:
        filters['status'] = status
    if manufacturer:
        filters['manufacturer'] = manufacturer
    if vendor:
        filters['vendor'] = vendor
    if product:
        filters['product'] = product
    
    rfqs_list = crm_data.get_rfqs(filters)
    pagination = paginate_results(rfqs_list, page)
    
    return render_template('rfqs.html', 
                         rfqs=pagination['items'], 
                         pagination=pagination,
                         status=status, 
                         manufacturer=manufacturer,
                         vendor=vendor,
                         product=product)

@app.route('/quotes')
def quotes():
    """Quotes list view with pagination (same as RFQs but with quotes template)"""
    status = request.args.get('status', '')
    manufacturer = request.args.get('manufacturer', '')
    vendor = request.args.get('vendor', '')
    product = request.args.get('product', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if status:
        filters['status'] = status
    if manufacturer:
        filters['manufacturer'] = manufacturer
    if vendor:
        filters['vendor'] = vendor
    if product:
        filters['product'] = product
    
    rfqs_list = crm_data.get_rfqs(filters)
    pagination = paginate_results(rfqs_list, page)
    
    return render_template('quotes.html', 
                         rfqs=pagination['items'], 
                         pagination=pagination,
                         status=status, 
                         manufacturer=manufacturer,
                         vendor=vendor,
                         product=product)

@app.route('/rfq/<int:rfq_id>')
def rfq_detail(rfq_id):
    """RFQ detail view"""
    rfq = crm_data.execute_query("SELECT * FROM rfqs WHERE id = ?", [rfq_id])
    if not rfq:
        flash('RFQ not found', 'error')
        return redirect(url_for('rfqs'))
    
    rfq = rfq[0]
    
    # Get related records
    opportunity = None
    if rfq['opportunity_id']:
        opp_results = crm_data.execute_query("SELECT * FROM opportunities WHERE id = ?", [rfq['opportunity_id']])
        opportunity = opp_results[0] if opp_results else None
    
    account = None
    if rfq['account_id']:
        account = crm_data.get_account_by_id(rfq['account_id'])
    
    contact = None
    if rfq['contact_id']:
        contact = crm_data.get_contact_by_id(rfq['contact_id'])
    
    return render_template('rfq_detail.html', 
                         rfq=rfq, 
                         opportunity=opportunity, 
                         account=account, 
                         contact=contact)

@app.route('/quote/<int:quote_id>')
def quote_detail(quote_id):
    """Quote detail view (same as RFQ but with quote template)"""
    quote = crm_data.execute_query("SELECT * FROM rfqs WHERE id = ?", [quote_id])
    if not quote:
        flash('Quote not found', 'error')
        return redirect(url_for('quotes'))
    
    quote = quote[0]
    
    # Get related records
    opportunity = None
    if quote['opportunity_id']:
        opp_results = crm_data.execute_query("SELECT * FROM opportunities WHERE id = ?", [quote['opportunity_id']])
        opportunity = opp_results[0] if opp_results else None
    
    account = None
    if quote['account_id']:
        account = crm_data.get_account_by_id(quote['account_id'])
    
    contact = None
    if quote['contact_id']:
        contact = crm_data.get_contact_by_id(quote['contact_id'])
    
    return render_template('quote_detail.html', 
                         quote=quote, 
                         opportunity=opportunity, 
                         account=account, 
                         contact=contact)

@app.route('/tasks')
def tasks():
    """Tasks list view with pagination"""
    from datetime import date
    
    # Get filter parameters
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    due_date = request.args.get('due_date_range', '') or request.args.get('due_date', '')
    owner = request.args.get('owner', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    # Build filters
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    if owner:
        filters['owner'] = owner
    if search:
        filters['search'] = search
    if due_date:
        if due_date == 'overdue':
            filters['due_date_range'] = 'overdue'
        elif due_date == 'today':
            filters['due_date_range'] = 'today'
        elif due_date == 'this_week':
            filters['due_date_range'] = 'this_week'
        elif due_date == 'next_week':
            filters['due_date_range'] = 'next_week'
    
    # Get tasks and stats
    tasks_list = crm_data.get_tasks(filters)
    stats = crm_data.get_task_stats()
    pagination = paginate_results(tasks_list, page)
    
    return render_template('tasks.html', 
                         tasks=pagination['items'], 
                         pagination=pagination,
                         stats=stats,
                         today=date.today().isoformat(),
                         status=status, 
                         priority=priority,
                         due_date_range=due_date,
                         owner=owner,
                         search=search)

@app.route('/products')
def products():
    """Products list view with pagination"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    fsc = request.args.get('fsc', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if search:
        # Search both name and NSN
        filters['search'] = search
    if category:
        filters['category'] = category
    if fsc:
        filters['fsc'] = fsc
    
    products_list = crm_data.get_products(filters)
    pagination = paginate_results(products_list, page)
    
    return render_template('products.html', 
                         products=pagination['items'], 
                         pagination=pagination,
                         search=search, 
                         category=category,
                         fsc=fsc)

@app.route('/api/products/<nsn>')
def api_get_product(nsn):
    """API endpoint to get product details by NSN"""
    try:
        # Get product by NSN instead of ID
        products = crm_data.get_products({'nsn': nsn})
        if products:
            product = products[0]
            # Convert sqlite3.Row to dict for JSON serialization
            product_dict = dict(product)
            return jsonify(product_dict)
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<nsn>', methods=['PUT'])
def api_update_product(nsn):
    """API endpoint to update product details by NSN"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Get the product first to get its ID
        products = crm_data.get_products({'nsn': nsn})
        if not products:
            return jsonify({'error': 'Product not found'}), 404
            
        product = products[0]
        product_id = product['id']
        
        # Update the product using the existing update method
        rows_affected = crm_data.update_product(product_id, **data)
        
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Product updated successfully'})
        else:
            return jsonify({'error': 'No changes made or product not found'}), 400
            
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<nsn>', methods=['DELETE'])
def api_delete_product(nsn):
    """API endpoint to delete product by NSN"""
    try:
        # Get the product first to get its ID
        products = crm_data.get_products({'nsn': nsn})
        if not products:
            return jsonify({'error': 'Product not found'}), 404
            
        product = products[0]
        product_id = product['id']
        
        # Check for dependencies (RFQs, opportunities, etc.)
        # Check RFQs
        rfqs = crm_data.execute_query("SELECT COUNT(*) as count FROM rfqs WHERE product_id = ?", [product_id])
        if rfqs and rfqs[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete product. It is referenced by {rfqs[0]["count"]} RFQ(s). Please remove these references first.'
            }), 400
            
        # Check opportunities
        opportunities = crm_data.execute_query("SELECT COUNT(*) as count FROM opportunities WHERE product_id = ?", [product_id])
        if opportunities and opportunities[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete product. It is referenced by {opportunities[0]["count"]} opportunity(ies). Please remove these references first.'
            }), 400
        
        # Delete the product
        rows_affected = crm_data.execute_update("DELETE FROM products WHERE id = ?", [product_id])
        
        if rows_affected > 0:
            return jsonify({'success': True, 'message': 'Product deleted successfully'})
        else:
            return jsonify({'error': 'Product not found or already deleted'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<nsn>/relationships')
def api_get_product_relationships(nsn):
    """API endpoint to get product relationships (RFQs, opportunities, vendors)"""
    try:
        # Get product by NSN to get its ID
        products = crm_data.get_products({'nsn': nsn})
        if not products:
            return jsonify({'error': 'Product not found'}), 404
            
        product = products[0]
        product_id = product['id']
        
        # Get related RFQs (now called Quotes)
        rfqs = crm_data.get_product_rfqs(product_id)
        
        # Get related opportunities
        opportunities = crm_data.get_product_opportunities(product_id)
        
        # Get vendors
        vendors = crm_data.get_product_vendors(product_id)
        
        return jsonify({
            'success': True,
            'rfqs': [dict(rfq) for rfq in rfqs] if rfqs else [],
            'opportunities': [dict(opp) for opp in opportunities] if opportunities else [],
            'vendors': [dict(vendor) for vendor in vendors] if vendors else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/interactions')
def interactions():
    """Interactions list view"""
    from datetime import datetime, timedelta
    
    # Get filters from request
    filters = {}
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('direction'):
        filters['direction'] = request.args.get('direction')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date')
    if request.args.get('end_date'):
        filters['end_date'] = request.args.get('end_date')
    if request.args.get('contact_id'):
        filters['contact_id'] = request.args.get('contact_id')
    if request.args.get('opportunity_id'):
        filters['opportunity_id'] = request.args.get('opportunity_id')
    
    interactions_list = crm_data.get_interactions(filters)
    
    # Calculate stats with error handling
    all_interactions = crm_data.get_interactions()
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    stats = {
        'total': len(all_interactions),
        'today': 0,
        'this_week': 0,
        'pending': 0
    }
    
    try:
        for i in all_interactions:
            # Check for pending status
            if i['status'] == 'Pending':
                stats['pending'] += 1
            
            # Check date-based stats if interaction_date exists
            if i['interaction_date']:
                try:
                    interaction_date = datetime.strptime(i['interaction_date'], '%Y-%m-%d %H:%M:%S').date()
                    if interaction_date == today:
                        stats['today'] += 1
                    if interaction_date >= week_start:
                        stats['this_week'] += 1
                except ValueError:
                    continue  # Skip if date parsing fails
    except Exception:
        pass  # If stats calculation fails, use defaults
    
    return render_template('interactions.html', 
                         interactions=interactions_list,
                         stats=stats,
                         filters=request.args)

@app.route('/interactions/<int:interaction_id>')
def interaction_detail(interaction_id):
    """Interaction detail view"""
    # Redirect to interactions page with the interaction_id parameter
    # This will automatically open the interaction detail modal
    return redirect(url_for('interactions', interaction_id=interaction_id))

# API Routes for AJAX operations

@app.route('/api/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark task as completed"""
    try:
        crm_data.complete_task(task_id)
        return jsonify({'success': True, 'message': 'Task completed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/update_rfq_status/<int:rfq_id>', methods=['POST'])
def update_rfq_status(rfq_id):
    """Update RFQ status"""
    try:
        status = request.json.get('status')
        opportunity_id = request.json.get('opportunity_id')
        
        crm_data.update_rfq_status(rfq_id, status, opportunity_id)
        return jsonify({'success': True, 'message': 'RFQ status updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/rfqs/<int:rfq_id>', methods=['DELETE'])
def delete_rfq(rfq_id):
    """Delete an RFQ"""
    try:
        # Check if RFQ exists
        rfq = crm_data.get_rfq_by_id(rfq_id)
        if not rfq:
            return jsonify({'error': 'RFQ not found'}), 404
        
        # Delete the RFQ
        deleted = crm_data.delete_rfq(rfq_id)
        if deleted:
            return jsonify({'success': True, 'message': 'RFQ deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete RFQ'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rfqs', methods=['POST'])
def create_rfq():
    """Create a new RFQ"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['request_number', 'status', 'product_id', 'account_id', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create the RFQ
        rfq_id = crm_data.create_rfq(**data)
        if rfq_id:
            return jsonify({'success': True, 'rfq_id': rfq_id, 'message': 'RFQ created successfully'})
        else:
            return jsonify({'error': 'Failed to create RFQ'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rfqs/<int:rfq_id>', methods=['PUT'])
def update_rfq(rfq_id):
    """Update an RFQ"""
    try:
        data = request.json
        
        # Update the RFQ
        updated = crm_data.update_rfq(rfq_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'RFQ updated successfully'})
        else:
            return jsonify({'error': 'RFQ not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== QUOTE API ROUTES ====================

@app.route('/api/quotes', methods=['POST'])
def create_quote():
    """Create a new Quote (same as RFQ)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['request_number', 'status', 'product_id', 'account_id', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create the Quote (using RFQ table)
        quote_id = crm_data.create_rfq(**data)
        if quote_id:
            return jsonify({'success': True, 'quote_id': quote_id, 'message': 'Quote created successfully'})
        else:
            return jsonify({'error': 'Failed to create Quote'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quotes/<int:quote_id>', methods=['PUT'])
def update_quote(quote_id):
    """Update a Quote (same as RFQ)"""
    try:
        data = request.json
        
        # Update the Quote (using RFQ table)
        updated = crm_data.update_rfq(quote_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Quote updated successfully'})
        else:
            return jsonify({'error': 'Quote not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quotes/<int:quote_id>', methods=['DELETE'])
def delete_quote(quote_id):
    """Delete a Quote (same as RFQ)"""
    try:
        deleted = crm_data.delete_rfq(quote_id)
        if deleted:
            return jsonify({'success': True, 'message': 'Quote deleted successfully'})
        else:
            return jsonify({'error': 'Quote not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_quote_status/<int:quote_id>', methods=['POST'])
def update_quote_status(quote_id):
    """Update Quote status (same as RFQ)"""
    try:
        data = request.json
        status = data.get('status')
        
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        
        # Update the Quote status (using RFQ table)
        updated = crm_data.update_rfq(quote_id, status=status)
        if updated:
            return jsonify({'success': True, 'message': f'Quote status updated to {status}'})
        else:
            return jsonify({'error': 'Quote not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_task', methods=['POST'])
def create_task():
    """Create new task"""
    try:
        task_data = request.json
        task_id = crm_data.create_task(**task_data)
        return jsonify({'success': True, 'task_id': task_id, 'message': 'Task created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks', methods=['POST'])
def create_task_api():
    """Create new task via API"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            task_data = request.get_json()
        else:
            task_data = request.form.to_dict()
        
        # Convert numeric fields
        if 'parent_item_id' in task_data and task_data['parent_item_id']:
            task_data['parent_item_id'] = int(task_data['parent_item_id'])
        if 'time_taken' in task_data and task_data['time_taken']:
            task_data['time_taken'] = int(task_data['time_taken'])
            
        # Remove empty values
        task_data = {k: v for k, v in task_data.items() if v}
        
        task_id = crm_data.create_task(**task_data)
        return jsonify({'success': True, 'task_id': task_id, 'message': 'Task created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task_api(task_id):
    """Get a single task via API"""
    try:
        task = crm_data.get_task_by_id(task_id)
        if task:
            return jsonify(task)
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PATCH'])
def update_task_api(task_id):
    """Update a task via API"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Convert numeric fields
        if 'time_taken' in data and data['time_taken']:
            data['time_taken'] = int(data['time_taken'])
            
        result = crm_data.update_task(task_id, **data)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to update task'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
def start_task_api(task_id):
    """Start a task via API"""
    try:
        result = crm_data.update_task(task_id, status='In Progress')
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to start task'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/tasks/<int:task_id>')
def task_detail(task_id):
    """Show task detail page"""
    try:
        task = crm_data.get_task_by_id(task_id)
        if not task:
            return render_template('error.html', error='Task not found'), 404
        
        # Get related opportunities if this is a processing task
        opportunities = []
        processing_report = ""
        
        if 'processing' in task.get('subject', '').lower() or 'pdf' in task.get('subject', '').lower():
            # For processing tasks, get opportunities created around the same time
            if task.get('created_date'):
                # Get opportunities created on the same day as the task
                from datetime import datetime, timedelta
                try:
                    task_date = datetime.strptime(task['created_date'][:10], '%Y-%m-%d')
                    # Get opportunities from the task creation date
                    date_str = task_date.strftime('%Y-%m-%d')
                    opportunities = crm_data.get_opportunities_by_date(date_str)
                except:
                    # Fallback to today's opportunities
                    from datetime import date
                    today = date.today().strftime('%Y-%m-%d')
                    opportunities = crm_data.get_opportunities_by_date(today)
            
            # Extract processing report from task description if available
            if task.get('description'):
                desc = task['description']
                if 'PROCESSING REPORT:' in desc:
                    parts = desc.split('PROCESSING REPORT:')
                    if len(parts) > 1:
                        processing_report = parts[1].split('REPORT ID:')[0].strip()
            
        edit_mode = request.args.get('edit') == 'true'
        
        return render_template('task_detail.html', 
                             task=task, 
                             opportunities=opportunities,
                             processing_report=processing_report,
                             edit_mode=edit_mode)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/tasks/<int:task_id>/status', methods=['POST'])
def update_task_status(task_id):
    """Update task status"""
    try:
        data = request.json
        status = data.get('status')
        
        if not status:
            return jsonify({'success': False, 'error': 'Status is required'})
        
        # Handle status changes with automatic date updates
        updates = {'status': status}
        
        # If starting the task, set start date
        if status == 'In Progress':
            from datetime import datetime
            updates['start_date'] = datetime.now().strftime("%Y-%m-%d")
        
        # If completing the task, set completed date
        elif status == 'Completed':
            from datetime import datetime
            updates['completed_date'] = datetime.now().strftime("%Y-%m-%d")
        
        result = crm_data.update_task(task_id, **updates)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """Start a task - sets status to In Progress and records start date"""
    try:
        from datetime import datetime
        
        updates = {
            'status': 'In Progress',
            'start_date': datetime.now().strftime("%Y-%m-%d")
        }
        
        result = crm_data.update_task(task_id, **updates)
        
        if result:
            return jsonify({'success': True, 'message': 'Task started successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/end', methods=['POST'])
def end_task(task_id):
    """End a task - sets status to Completed and records completion date"""
    try:
        from datetime import datetime
        
        updates = {
            'status': 'Completed',
            'completed_date': datetime.now().strftime("%Y-%m-%d")
        }
        
        result = crm_data.update_task(task_id, **updates)
        
        if result:
            return jsonify({'success': True, 'message': 'Task completed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to complete task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/reschedule', methods=['POST'])
def reschedule_task(task_id):
    """Reschedule task due date"""
    try:
        data = request.json
        due_date = data.get('due_date')
        
        if not due_date:
            return jsonify({'success': False, 'error': 'Due date is required'})
        
        result = crm_data.update_task(task_id, due_date=due_date)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to reschedule task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/priority', methods=['POST'])
def update_task_priority(task_id):
    """Update task priority"""
    try:
        data = request.json
        priority = data.get('priority')
        
        if not priority:
            return jsonify({'success': False, 'error': 'Priority is required'})
        
        result = crm_data.update_task(task_id, priority=priority)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update priority'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/work-date', methods=['POST'])
def update_task_work_date(task_id):
    """Update task work date"""
    try:
        data = request.json
        work_date = data.get('work_date')
        
        if not work_date:
            return jsonify({'success': False, 'error': 'Work date is required'})
        
        result = crm_data.update_task(task_id, work_date=work_date)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to update work date'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/log-time', methods=['POST'])
def log_task_time(task_id):
    """Log time spent on task"""
    try:
        data = request.json
        time_taken = data.get('time_taken')
        
        if time_taken is None:
            return jsonify({'success': False, 'error': 'Time taken is required'})
        
        result = crm_data.update_task(task_id, time_taken=time_taken)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to log time'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/link-opportunity', methods=['POST'])
def link_task_to_opportunity(task_id):
    """Link task to opportunity"""
    try:
        data = request.json
        opportunity_id = data.get('opportunity_id')
        
        if not opportunity_id:
            return jsonify({'success': False, 'error': 'Opportunity ID is required'})
        
        result = crm_data.update_task(task_id, opportunity_id=opportunity_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to link to opportunity'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/link-account', methods=['POST'])
def link_task_to_account(task_id):
    """Link task to account"""
    try:
        data = request.json
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({'success': False, 'error': 'Account ID is required'})
        
        result = crm_data.update_task(task_id, account_id=account_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to link to account'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>', methods=['POST'])
def update_task(task_id):
    """Update task"""
    try:
        # Get form data
        data = {}
        for field in ['subject', 'description', 'status', 'priority', 'work_date', 
                     'due_date', 'owner', 'start_date', 'completed_date', 'time_taken',
                     'parent_item_type', 'parent_item_id']:
            value = request.form.get(field)
            if value and value.strip():
                # Convert numeric fields
                if field in ['time_taken', 'parent_item_id'] and value.isdigit():
                    data[field] = int(value)
                else:
                    data[field] = value.strip()
        
        result = crm_data.update_task(task_id, **data)
        
        if result:
            return redirect(f'/tasks/{task_id}')
        else:
            return jsonify({'success': False, 'error': 'Failed to update task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task_route(task_id):
    """Delete task via POST"""
    try:
        result = crm_data.delete_task(task_id)
        
        if result:
            return redirect('/tasks')
        else:
            return jsonify({'success': False, 'error': 'Failed to delete task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete task"""
    try:
        result = crm_data.delete_task(task_id)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete task'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create_interaction', methods=['POST'])
def create_interaction():
    """Create new interaction"""
    try:
        interaction_data = request.json
        interaction_id = crm_data.create_interaction(**interaction_data)
        return jsonify({'success': True, 'interaction_id': interaction_id, 'message': 'Interaction created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/interactions', methods=['POST'])
def api_create_interaction():
    """Create new interaction via API"""
    try:
        interaction_data = request.json
        interaction_id = crm_data.create_interaction(**interaction_data)
        return jsonify({'success': True, 'interaction_id': interaction_id, 'message': 'Interaction created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/interactions/<int:interaction_id>', methods=['GET'])
def api_get_interaction(interaction_id):
    """Get single interaction by ID"""
    try:
        interaction = crm_data.get_interaction_by_id(interaction_id)
        if interaction:
            return jsonify(interaction)
        else:
            return jsonify({'error': 'Interaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interactions/<int:interaction_id>', methods=['PUT'])
def api_update_interaction(interaction_id):
    """Update interaction by ID"""
    try:
        interaction_data = request.json
        success = crm_data.update_interaction(interaction_id, **interaction_data)
        if success:
            return jsonify({'success': True, 'message': 'Interaction updated'})
        else:
            return jsonify({'success': False, 'message': 'Interaction not found or no changes made'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/interactions/<int:interaction_id>', methods=['DELETE'])
def api_delete_interaction(interaction_id):
    """Delete interaction by ID"""
    try:
        success = crm_data.delete_interaction(interaction_id)
        if success:
            return jsonify({'success': True, 'message': 'Interaction deleted'})
        else:
            return jsonify({'success': False, 'message': 'Interaction not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/contacts', methods=['GET'])
def api_get_contacts():
    """Get all contacts for dropdowns with optional account filtering"""
    try:
        # Get query parameters
        account_id = request.args.get('account_id')
        
        # Build filters
        filters = {}
        if account_id:
            filters['account_id'] = account_id
        
        contacts = crm_data.get_contacts(filters=filters if filters else None)
        # Convert sqlite3.Row objects to dictionaries
        contacts_list = []
        for contact in contacts:
            contact_dict = dict(contact)
            contacts_list.append(contact_dict)
        return jsonify(contacts_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/opportunities', methods=['GET'])
def api_get_opportunities():
    """Get all opportunities for dropdowns"""
    try:
        opportunities = crm_data.get_opportunities()
        # Convert sqlite3.Row objects to dictionaries
        opportunities_list = []
        for opportunity in opportunities:
            opportunity_dict = dict(opportunity)
            opportunities_list.append(opportunity_dict)
        return jsonify(opportunities_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
def api_get_accounts():
    """Get all accounts for dropdowns"""
    try:
        accounts = crm_data.get_accounts()
        account_type = request.args.get('type')  # Filter by type if specified
        
        # Convert sqlite3.Row objects to dictionaries
        accounts_list = []
        for account in accounts:
            account_dict = dict(account)
            
            # Filter by type if specified
            if account_type == 'vendor':
                # For vendor filtering, include all accounts that could be vendors
                # You can enhance this logic based on your data structure
                accounts_list.append(account_dict)
            elif account_type and account_dict.get('type') == account_type:
                accounts_list.append(account_dict)
            elif not account_type:
                accounts_list.append(account_dict)
        
        return jsonify({'success': True, 'accounts': accounts_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get all projects for dropdowns"""
    try:
        projects = crm_data.get_projects()
        # Convert sqlite3.Row objects to dictionaries
        projects_list = []
        for project in projects:
            project_dict = dict(project)
            projects_list.append(project_dict)
        return jsonify(projects_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products for dropdowns"""
    try:
        products = crm_data.get_products()
        # Convert sqlite3.Row objects to dictionaries
        products_list = []
        for product in products:
            product_dict = dict(product)
            products_list.append(product_dict)
        return jsonify(products_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_dibbs', methods=['POST'])
def process_dibbs():
    """Process DIBBs data (called by integrated DIBBs parser)"""
    try:
        dibbs_data = request.json
        result = crm_automation.process_dibbs_solicitation(dibbs_data)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/create_contact', methods=['POST'])
def create_contact():
    """Create new contact with duplicate validation"""
    try:
        contact_data = request.json
        contact_id = crm_data.create_contact(**contact_data)
        return jsonify({'success': True, 'contact_id': contact_id, 'message': 'Contact created successfully'})
    except ValueError as e:
        # This will catch our duplicate validation errors
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating contact: {str(e)}'}), 500

@app.route('/api/update_contact/<int:contact_id>', methods=['POST'])
def update_contact(contact_id):
    """Update existing contact with duplicate validation"""
    try:
        contact_data = request.json
        updated = crm_data.update_contact(contact_id, **contact_data)
        if updated:
            return jsonify({'success': True, 'message': 'Contact updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No changes made'}), 400
    except ValueError as e:
        # This will catch our duplicate validation errors
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating contact: {str(e)}'}), 500

@app.route('/api/create_product', methods=['POST'])
def create_product():
    """Create new product with NSN duplicate validation"""
    try:
        product_data = request.json
        product_id = crm_data.create_product(**product_data)
        return jsonify({'success': True, 'product_id': product_id, 'message': 'Product created successfully'})
    except ValueError as e:
        # This will catch our duplicate validation errors
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating product: {str(e)}'}), 500

@app.route('/api/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    """Update existing product with NSN duplicate validation"""
    try:
        product_data = request.json
        updated = crm_data.update_product(product_id, **product_data)
        if updated:
            return jsonify({'success': True, 'message': 'Product updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'No changes made'}), 400
    except ValueError as e:
        # This will catch our duplicate validation errors
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating product: {str(e)}'}), 500

@app.route('/api/check_contact_duplicate', methods=['POST'])
def check_contact_duplicate():
    """Check for contact duplicates before creating/updating"""
    try:
        data = request.json
        name = data.get('name', '')
        email = data.get('email', '')
        exclude_id = data.get('exclude_id')
        
        duplicates = crm_data.check_contact_duplicate(name, email, exclude_id)
        
        return jsonify({
            'has_duplicates': len(duplicates) > 0,
            'duplicates': duplicates
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check_product_duplicate', methods=['POST'])
def check_product_duplicate():
    """Check for product NSN duplicates before creating/updating"""
    try:
        data = request.json
        nsn = data.get('nsn', '')
        exclude_id = data.get('exclude_id')
        
        duplicates = crm_data.check_product_duplicate(nsn, exclude_id)
        
        return jsonify({
            'has_duplicates': len(duplicates) > 0,
            'duplicates': duplicates
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search')
def search():
    """Global search across all entities"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = []
    
    # Search accounts
    accounts = crm_data.get_accounts({'name': query}, limit=5)
    for account in accounts:
        results.append({
            'type': 'Account',
            'id': account['id'],
            'name': account['name'],
            'url': url_for('account_detail', account_id=account['id'])
        })
    
    # Search contacts
    contacts = crm_data.get_contacts({'name': query}, limit=5)
    for contact in contacts:
        results.append({
            'type': 'Contact',
            'id': contact['id'],
            'name': f"{contact['first_name']} {contact['last_name']}",
            'url': f"/contact/{contact['id']}"  # Would need to create this route
        })
    
    # Search RFQs
    rfqs = crm_data.execute_query(
        "SELECT * FROM rfqs WHERE request_number LIKE ? OR product_description LIKE ? LIMIT 5",
        [f"%{query}%", f"%{query}%"]
    )
    for rfq in rfqs:
        results.append({
            'type': 'RFQ',
            'id': rfq['id'],
            'name': f"RFQ {rfq['request_number']}",
            'url': url_for('rfq_detail', rfq_id=rfq['id'])
        })
    
    return jsonify(results)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format currency values"""
    if value is None:
        return "$0.00"
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@app.template_filter('date')
def date_filter(value):
    """Format date values"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            if value.strip() == "":
                return ""
            # Try parsing different date formats
            for fmt in ['%Y-%m-%d', '%b %d, %Y', '%m/%d/%Y']:
                try:
                    value = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return value  # Return original if no format matches
        except:
            return value
    if hasattr(value, 'strftime'):
        return value.strftime('%m/%d/%Y')
    return str(value)

@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime values"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            if value.strip() == "":
                return ""
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except:
            return value
    if hasattr(value, 'strftime'):
        return value.strftime('%m/%d/%Y %I:%M %p')
    return str(value)

# Projects page and API endpoints
@app.route('/projects')
def projects():
    # Get filter parameters
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    project_manager = request.args.get('project_manager', '')
    vendor_id = request.args.get('vendor_id', '')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    # Build filters dictionary
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    if project_manager:
        filters['project_manager'] = project_manager
    if vendor_id and vendor_id.isdigit():
        filters['vendor_id'] = int(vendor_id)
    if search:
        filters['search'] = search
    
    # Get filtered projects
    projects_list = crm_data.get_projects(filters)
    pagination = paginate_results(projects_list, page)
    
    # Get statistics
    stats = crm_data.get_project_stats()
    
    # Get vendors for filter dropdown
    vendors = crm_data.get_accounts({'type': 'Vendor'})
    
    # Get potential parent projects (excluding sub-projects to avoid deep nesting)
    parent_projects = crm_data.get_projects({'parent_project_id': None})
    
    return render_template('projects.html', 
                         projects=pagination['items'], 
                         pagination=pagination,
                         stats=stats,
                         vendors=vendors,
                         parent_projects=parent_projects,
                         status=status,
                         priority=priority,
                         project_manager=project_manager,
                         vendor_id=vendor_id,
                         search=search)

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    try:
        # Get form data
        name = request.form.get('name')
        if not name:
            return jsonify({'success': False, 'message': 'Project name is required'}), 400
        
        project_data = {
            'name': name,
            'status': request.form.get('status', 'Not Started'),
            'priority': request.form.get('priority', 'Medium'),
            'summary': request.form.get('summary'),
            'description': request.form.get('description'),
            'start_date': request.form.get('start_date') or None,
            'due_date': request.form.get('due_date') or None,
            'progress_percentage': int(request.form.get('progress_percentage', 0)),
            'budget': float(request.form.get('budget')) if request.form.get('budget') else None,
            'project_manager': request.form.get('project_manager'),
            'team_members': request.form.get('team_members'),
            'vendor_id': int(request.form.get('vendor_id')) if request.form.get('vendor_id') else None,
            'parent_project_id': int(request.form.get('parent_project_id')) if request.form.get('parent_project_id') else None,
            'notes': request.form.get('notes')
        }
        
        project_id = crm_data.create_project(**project_data)
        return jsonify({'success': True, 'project_id': project_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>/start', methods=['POST'])
def api_start_project(project_id):
    try:
        crm_data.start_project(project_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>/complete', methods=['POST'])
def api_complete_project(project_id):
    try:
        crm_data.complete_project(project_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>/progress', methods=['POST'])
def api_update_project_progress(project_id):
    try:
        data = request.get_json()
        percentage = data.get('percentage')
        if percentage is None or not (0 <= percentage <= 100):
            return jsonify({'success': False, 'message': 'Valid percentage (0-100) required'}), 400
        
        crm_data.update_project_progress(project_id, percentage)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    try:
        crm_data.delete_project(project_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# PDF Processing API Routes
@app.route('/api/pdf-count')
def get_pdf_count():
    """Get count of PDFs in To Process folder"""
    try:
        to_process_dir = Path("To Process")
        if not to_process_dir.exists():
            return jsonify({'count': 0, 'status': 'No directory'})
        
        try:
            # First approach: direct globbing
            pdf_files_lower = list(to_process_dir.glob("*.pdf"))
            pdf_files_upper = list(to_process_dir.glob("*.PDF"))
            pdf_count = len([f for f in pdf_files_lower if f.is_file()]) + \
                       len([f for f in pdf_files_upper if f.is_file()])
                
            # Add detailed information for debugging
            file_info = []
            all_pdfs = pdf_files_lower + pdf_files_upper
            for pdf in all_pdfs:
                if pdf.is_file():
                    file_info.append({
                        'name': pdf.name,
                        'size': os.path.getsize(pdf) if os.path.exists(pdf) else 0
                    })
            
            return jsonify({
                'count': pdf_count, 
                'status': 'success',
                'files': file_info
            })
        except Exception as e:
            # Fall back to a simpler approach
            import os
            pdf_files = [f for f in os.listdir(str(to_process_dir)) 
                        if f.lower().endswith('.pdf')]
            return jsonify({
                'count': len(pdf_files),
                'status': 'fallback',
                'error': str(e)
            })
            
    except Exception as e:
        app.logger.error(f"Error in get_pdf_count: {str(e)}")
        return jsonify({'count': 0, 'status': 'error', 'error': str(e)}), 500

@app.route('/api/load-pdfs', methods=['POST'])
def load_pdfs():
    """Process PDFs from To Process folder and load into database"""
    try:
        # Check if the To Process directory exists first
        to_process_dir = Path("To Process")
        if not to_process_dir.exists():
            return jsonify({
                'success': False,
                'message': 'To Process directory does not exist'
            }), 404
            
        # Check if there are PDFs to process
        pdf_files = list(to_process_dir.glob("*.pdf")) + list(to_process_dir.glob("*.PDF"))
        if not pdf_files:
            return jsonify({
                'success': True,
                'message': 'No PDF files to process',
                'processed': 0,
                'created': 0,
                'updated': 0,
                'errors': []
            })
            
        # Process the PDFs
        results = pdf_processor.process_all_pdfs()
        
        # Generate a comprehensive report ID for viewing
        from datetime import datetime
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Auto-create review task for successful processing
        if results['processed'] > 0:
            try:
                # Create task due today
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Get created opportunities for linking
                created_opportunities = []
                if 'created_opportunities' in results and results['created_opportunities']:
                    created_opportunities = results['created_opportunities']
                
                # Build detailed task description with processing results
                task_description = f"""PDF Processing completed on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PROCESSING RESULTS:
• Files Processed: {results['processed']}
• Opportunities Created: {results['created']}
• Records Updated: {results['updated']}
• Files Skipped: {results.get('skipped', 0)}
• Errors: {len(results['errors'])}

REQUIRED ACTIONS:
1. Review Processing Report:
   - Detailed processing report is displayed below
   - Check for any errors or issues
   - Verify all PDFs were processed correctly

2. Examine New Opportunities:
   - Review newly created opportunities in the table below
   - Verify opportunity details and stages
   - Assign to appropriate team members

3. Follow-up Actions:
   - Update opportunity stages as needed
   - Create quotes for qualified opportunities
   - Schedule follow-up interactions

PROCESSING REPORT:
{results.get('detailed_report', 'No detailed report available')}

REPORT ID: {report_id}
"""
                
                # Create the task with enhanced information
                task_id = crm_data.create_task(
                    subject=f"Review PDF Processing Results - {results['processed']} files processed",
                    description=task_description,
                    status="Not Started",
                    priority="High",
                    type="Follow-up",
                    due_date=today,
                    assigned_to="System Generated",
                    # Store additional data for display
                    processing_report=results.get('detailed_report', ''),
                    report_id=report_id,
                    created_opportunities=created_opportunities
                )
                
                app.logger.info(f"Auto-created review task {task_id} for PDF processing results")
                
            except Exception as task_error:
                app.logger.error(f"Error creating review task: {str(task_error)}")
                # Don't fail the whole operation if task creation fails
        
        return jsonify({
            'success': True,
            'processed': results['processed'],
            'created': results['created'],
            'updated': results['updated'],
            'skipped': results.get('skipped', 0),
            'errors': results['errors'],
            'report_id': report_id,
            'detailed_report_available': True,
            'review_task_created': results['processed'] > 0
        })
    except Exception as e:
        app.logger.error(f"Error in load_pdfs: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

# API endpoints for edit functionality
@app.route('/api/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    """Get account details for editing"""
    try:
        account = crm_data.get_account_by_id(account_id)
        if account:
            # Convert SQLite Row to dictionary
            account_dict = dict(account) if hasattr(account, 'keys') else account
            return jsonify(account_dict)
        else:
            return jsonify({'error': 'Account not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """Update account details"""
    try:
        data = request.json
        updated = crm_data.update_account(account_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Account updated successfully'})
        else:
            return jsonify({'error': 'Account not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an account"""
    try:
        # Check if account has any related data
        account = crm_data.get_account_by_id(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Check for related contacts
        contacts = crm_data.get_contacts_by_account(account_id)
        if contacts:
            return jsonify({
                'error': f'Cannot delete account. It has {len(contacts)} associated contact(s). Please remove these contacts first.'
            }), 400
        
        # Check for related opportunities
        opportunities = crm_data.get_opportunities(account_id=account_id)
        if opportunities:
            return jsonify({
                'error': f'Cannot delete account. It has {len(opportunities)} associated opportunity(ies). Please remove these opportunities first.'
            }), 400
        
        # Delete the account
        deleted = crm_data.delete_account(account_id)
        if deleted:
            return jsonify({'success': True, 'message': 'Account deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete account'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get contact details for editing"""
    try:
        contact = crm_data.get_contact_by_id(contact_id)
        if contact:
            # Convert SQLite Row to dictionary
            contact_dict = dict(contact) if hasattr(contact, 'keys') else contact
            return jsonify(contact_dict)
        else:
            return jsonify({'error': 'Contact not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def update_contact_put(contact_id):
    """Update contact details (PUT method)"""
    try:
        data = request.json
        updated = crm_data.update_contact(contact_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Contact updated successfully'})
        else:
            return jsonify({'error': 'Contact not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details for editing"""
    try:
        project = crm_data.get_project_by_id(project_id)
        if project:
            # Convert SQLite Row to dictionary
            project_dict = dict(project) if hasattr(project, 'keys') else project
            return jsonify(project_dict)
        else:
            return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project details"""
    try:
        data = request.json
        updated = crm_data.update_project(project_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Project updated successfully'})
        else:
            return jsonify({'error': 'Project not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interactions/<int:interaction_id>', methods=['GET'])
def get_interaction(interaction_id):
    """Get interaction details for editing"""
    try:
        interaction = crm_data.get_interaction_by_id(interaction_id)
        if interaction:
            # Convert SQLite Row to dictionary
            interaction_dict = dict(interaction) if hasattr(interaction, 'keys') else interaction
            return jsonify(interaction_dict)
        else:
            return jsonify({'error': 'Interaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interactions/<int:interaction_id>', methods=['PUT'])
def update_interaction(interaction_id):
    """Update interaction details"""
    try:
        data = request.json
        updated = crm_data.update_interaction(interaction_id, **data)
        if updated:
            return jsonify({'success': True, 'message': 'Interaction updated successfully'})
        else:
            return jsonify({'error': 'Interaction not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/processing-reports')
def processing_reports():
    """View processing reports"""
    import glob
    import json
    from pathlib import Path
    
    # Get processing statistics
    stats = {
        'processed': 0,
        'skipped': 0
    }
    
    # Count files in reviewed folders
    reviewed_dir = Path("Reviewed")
    if reviewed_dir.exists():
        stats['processed'] = len(list(reviewed_dir.glob("*.pdf"))) + len(list(reviewed_dir.glob("*.PDF")))
        
        skipped_dir = reviewed_dir / "Skipped"
        if skipped_dir.exists():
            stats['skipped'] = len(list(skipped_dir.glob("*.pdf"))) + len(list(skipped_dir.glob("*.PDF")))
    
    # Get all report files
    output_dir = Path("Output")
    report_files = []
    
    if output_dir.exists():
        for report_file in sorted(output_dir.glob("pdf_processing_report_*.json"), reverse=True):
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                # Extract summary info for listing
                report_files.append({
                    'filename': report_file.name,
                    'timestamp': report_data.get('processing_start', ''),
                    'processed': report_data.get('processed', 0),
                    'created': report_data.get('created', 0),
                    'updated': report_data.get('updated', 0),
                    'skipped': report_data.get('skipped', 0),
                    'errors': len(report_data.get('errors', []))
                })
            except Exception as e:
                print(f"Error reading report {report_file}: {e}")
    
    return render_template('processing_reports.html', reports=report_files, stats=stats)

@app.route('/processing-reports/<filename>')
def view_processing_report(filename):
    """View detailed processing report"""
    import json
    from pathlib import Path
    
    report_file = Path("Output") / filename
    
    if not report_file.exists():
        return "Report not found", 404
    
    try:
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        return render_template('processing_report_detail.html', report=report_data, filename=filename)
    except Exception as e:
        return f"Error loading report: {e}", 500

@app.route('/api/latest-processing-report')
def get_latest_processing_report():
    """Get the latest processing report data"""
    import json
    from pathlib import Path
    
    output_dir = Path("Output")
    if not output_dir.exists():
        return jsonify({'error': 'No reports found'}), 404
    
    # Get the most recent report
    report_files = sorted(output_dir.glob("pdf_processing_report_*.json"), reverse=True)
    
    if not report_files:
        return jsonify({'error': 'No reports found'}), 404
    
    try:
        with open(report_files[0], 'r') as f:
            report_data = json.load(f)
        return jsonify(report_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== EMAIL AUTOMATION API ROUTES ====================

@app.route('/api/opportunities/<int:opportunity_id>/generate-vendor-emails', methods=['POST'])
def generate_vendor_emails_api(opportunity_id):
    """Generate RFQ emails for multiple vendors"""
    try:
        data = request.get_json()
        vendor_list = data.get('vendors', [])
        template_name = data.get('template', 'Standard RFQ Request')
        
        if not vendor_list:
            return jsonify({'success': False, 'message': 'No vendors specified'})
        
        # Generate emails for all vendors
        emails = email_automation.generate_bulk_rfq_emails(opportunity_id, vendor_list, template_name)
        
        success_count = len([e for e in emails if 'error' not in e])
        error_count = len([e for e in emails if 'error' in e])
        
        return jsonify({
            'success': True,
            'message': f'Generated {success_count} emails successfully. {error_count} errors.',
            'emails': emails,
            'summary': {
                'total': len(emails),
                'success': success_count,
                'errors': error_count
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/vendor-emails', methods=['GET'])
def get_vendor_emails_api(opportunity_id):
    """Get all vendor emails for an opportunity"""
    try:
        emails = email_automation.get_vendor_emails_for_opportunity(opportunity_id)
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-templates', methods=['GET'])
def get_email_templates_api():
    """Get all available email templates"""
    try:
        templates = email_automation.get_email_templates()
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-preview', methods=['POST'])
def preview_email_api():
    """Preview email content without saving"""
    try:
        data = request.get_json()
        opportunity_id = data.get('opportunity_id')
        vendor_account_id = data.get('vendor_account_id')
        template_name = data.get('template', 'Standard RFQ Request')
        
        if not all([opportunity_id, vendor_account_id]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        preview = email_automation.preview_email(opportunity_id, vendor_account_id, template_name)
        
        if 'error' in preview:
            return jsonify({'success': False, 'message': preview['error']})
        
        return jsonify({'success': True, 'preview': preview})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/vendor-emails/<int:email_id>/status', methods=['PUT'])
def update_email_status_api(email_id):
    """Update email status"""
    try:
        data = request.get_json()
        status = data.get('status')
        response_data = data.get('response_data')
        
        if not status:
            return jsonify({'success': False, 'message': 'Status required'})
        
        success = email_automation.update_email_status(email_id, status, response_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update status'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/generate-single-vendor-email', methods=['POST'])
def generate_single_vendor_email_api(opportunity_id):
    """Generate RFQ email for a single vendor"""
    try:
        data = request.get_json()
        vendor_account_id = data.get('vendor_account_id')
        vendor_contact_id = data.get('vendor_contact_id')
        template_name = data.get('template', 'Standard RFQ Request')
        
        if not vendor_account_id:
            return jsonify({'success': False, 'message': 'Vendor account ID required'})
        
        email = email_automation.generate_rfq_email(
            opportunity_id, vendor_account_id, vendor_contact_id, template_name
        )
        
        return jsonify({'success': True, 'email': email})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Enhanced Email Automation Endpoints
@app.route('/api/vendor-emails/<int:email_id>/mark-sent', methods=['POST'])
def mark_vendor_email_sent(email_id):
    """Mark vendor email as sent with enhanced tracking"""
    try:
        from enhanced_email_automation import EnhancedEmailAutomation
        enhanced_automation = EnhancedEmailAutomation()
        
        data = request.get_json() or {}
        tracking_id = data.get('tracking_id')
        
        success = enhanced_automation.mark_email_sent(email_id, tracking_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Email marked as sent and interaction created'})
        else:
            return jsonify({'success': False, 'message': 'Failed to mark email as sent'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/vendor-emails/<int:email_id>/tracking', methods=['GET'])
def get_email_tracking_status(email_id):
    """Get detailed tracking status for vendor email"""
    try:
        from enhanced_email_automation import EnhancedEmailAutomation
        enhanced_automation = EnhancedEmailAutomation()
        
        tracking_data = enhanced_automation.get_email_tracking_status(email_id)
        
        return jsonify({'success': True, 'tracking': tracking_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/vendor-emails/bulk-update-status', methods=['POST'])
def bulk_update_vendor_email_status():
    """Bulk update status for multiple vendor emails"""
    try:
        data = request.get_json()
        email_ids = data.get('email_ids', [])
        status = data.get('status', 'Sent')
        
        if not email_ids:
            return jsonify({'success': False, 'message': 'No email IDs provided'})
        
        from enhanced_email_automation import EnhancedEmailAutomation
        enhanced_automation = EnhancedEmailAutomation()
        
        updated_count = enhanced_automation.bulk_update_email_status(email_ids, status)
        
        return jsonify({
            'success': True, 
            'message': f'Updated {updated_count} emails to status: {status}',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-responses/process', methods=['POST'])
def process_email_response():
    """Process vendor email response with all 4 required features"""
    try:
        from enhanced_email_response_processor import EnhancedEmailResponseProcessor
        processor = EnhancedEmailResponseProcessor()
        
        email_data = request.get_json()
        
        if not email_data:
            return jsonify({'success': False, 'message': 'No email data provided'})
        
        # Process email with all 4 features:
        # 1. Create new quote from email response
        # 2. Update interaction from vendor response  
        # 3. Parse email response auto-load quote
        # 4. Update opportunity to "quote received"
        result = processor.process_complete_email_response(email_data)
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error processing email response: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-responses/test', methods=['POST'])
def test_email_response_processing():
    """Test endpoint for email response processing features"""
    try:
        from enhanced_email_response_processor import test_email_response_features
        
        result = test_email_response_features()
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error testing email response processing: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/quotes/create-from-email', methods=['POST'])
def create_quote_from_email():
    """Feature 1: Create new quote from email response"""
    try:
        from enhanced_email_response_processor import EnhancedEmailResponseProcessor
        processor = EnhancedEmailResponseProcessor()
        
        data = request.get_json()
        email_data = data.get('email_data', {})
        opportunity_id = data.get('opportunity_id')
        vendor_account_id = data.get('vendor_account_id')
        
        if not all([email_data, opportunity_id, vendor_account_id]):
            return jsonify({'success': False, 'message': 'Missing required data'})
        
        quote_id = processor.create_new_quote_from_email_response(email_data, opportunity_id, vendor_account_id)
        
        return jsonify({
            'success': bool(quote_id),
            'quote_id': quote_id,
            'message': 'Quote created successfully' if quote_id else 'Failed to create quote'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating quote from email: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/interactions/update-from-email', methods=['POST'])
def update_interaction_from_email():
    """Feature 2: Update interaction from vendor response"""
    try:
        from enhanced_email_response_processor import EnhancedEmailResponseProcessor
        processor = EnhancedEmailResponseProcessor()
        
        data = request.get_json()
        email_data = data.get('email_data', {})
        opportunity_id = data.get('opportunity_id')
        vendor_account_id = data.get('vendor_account_id')
        
        if not all([email_data, opportunity_id, vendor_account_id]):
            return jsonify({'success': False, 'message': 'Missing required data'})
        
        interaction_id = processor.update_interaction_from_vendor_response(email_data, opportunity_id, vendor_account_id)
        
        return jsonify({
            'success': bool(interaction_id),
            'interaction_id': interaction_id,
            'message': 'Interaction updated successfully' if interaction_id else 'Failed to update interaction'
        })
        
    except Exception as e:
        app.logger.error(f"Error updating interaction from email: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/quotes/parse-from-email', methods=['POST'])
def parse_quote_from_email():
    """Feature 3: Parse email response auto-load quote"""
    try:
        from enhanced_email_response_processor import EnhancedEmailResponseProcessor
        processor = EnhancedEmailResponseProcessor()
        
        email_data = request.get_json()
        
        if not email_data:
            return jsonify({'success': False, 'message': 'No email data provided'})
        
        quote_data = processor.parse_email_response_auto_load_quote(email_data)
        
        return jsonify({
            'success': True,
            'quote_data': quote_data,
            'message': 'Quote data parsed successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error parsing quote from email: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/mark-quote-received', methods=['POST'])
def mark_opportunity_quote_received(opportunity_id):
    """Feature 4: Update opportunity status to "quote received" """
    try:
        from enhanced_email_response_processor import EnhancedEmailResponseProcessor
        processor = EnhancedEmailResponseProcessor()
        
        data = request.get_json() or {}
        quote_data = data.get('quote_data', {})
        
        success = processor.update_opportunity_to_quote_received(opportunity_id, quote_data)
        
        return jsonify({
            'success': success,
            'message': 'Opportunity updated to Quote Received' if success else 'Failed to update opportunity'
        })
        
    except Exception as e:
        app.logger.error(f"Error marking opportunity quote received: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ==================== EMAIL AUTOMATION SERVICE ENDPOINTS ====================

@app.route('/api/email-automation/status', methods=['GET'])
def get_email_automation_status():
    """Get email automation service status"""
    try:
        from email_automation_service import email_service
        
        # Check if service is running
        service_running = email_service.running
        
        # Get basic statistics
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        # Count email accounts
        cursor.execute("SELECT COUNT(*) FROM email_accounts WHERE enabled = 1")
        result = cursor.fetchone()
        active_accounts = result[0] if result else 0
        
        # Count pending emails
        cursor.execute("SELECT COUNT(*) FROM email_processing_queue WHERE status = 'pending'")
        result = cursor.fetchone()
        pending_emails = result[0] if result else 0
        
        # Count today's processed emails
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM email_processing_queue WHERE DATE(last_attempt) = ? AND status = 'completed'", (today,))
        result = cursor.fetchone()
        emails_processed_today = result[0] if result else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'status': {
                'service_running': service_running,
                'active_accounts': active_accounts,
                'pending_emails': pending_emails,
                'emails_processed_today': emails_processed_today,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/start', methods=['POST'])
def start_email_automation():
    """Start email automation service"""
    try:
        from email_automation_service import email_service
        
        if email_service.running:
            return jsonify({'success': False, 'message': 'Email automation is already running'})
        
        email_service.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Email automation service started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/stop', methods=['POST'])
def stop_email_automation():
    """Stop email automation service"""
    try:
        from email_automation_service import email_service
        
        if not email_service.running:
            return jsonify({'success': False, 'message': 'Email automation is not running'})
        
        email_service.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Email automation service stopped successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/accounts', methods=['GET', 'POST'])
def manage_email_accounts():
    """Manage email accounts for monitoring"""
    if request.method == 'GET':
        try:
            conn = sqlite3.connect('crm.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, account_name, email_address, account_type, server_host, 
                       server_port, use_ssl, enabled, last_check, check_frequency_minutes
                FROM email_accounts
                ORDER BY account_name
            """)
            
            accounts = []
            for row in cursor.fetchall():
                accounts.append({
                    'id': row[0],
                    'account_name': row[1],
                    'email_address': row[2],
                    'account_type': row[3],
                    'server_host': row[4],
                    'server_port': row[5],
                    'use_ssl': bool(row[6]),
                    'enabled': bool(row[7]),
                    'last_check': row[8],
                    'check_frequency_minutes': row[9]
                })
            
            conn.close()
            
            return jsonify({'success': True, 'accounts': accounts})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    elif request.method == 'POST':
        try:
            from email_automation_service import email_service
            
            data = request.get_json()
            
            success = email_service.add_email_account(
                data['account_name'],
                data['email_address'],
                data['account_type'],
                data['server_host'],
                data['server_port'],
                data['username'],
                data['password'],
                data.get('use_ssl', True),
                data.get('check_frequency_minutes', 5)
            )
            
            if success:
                return jsonify({'success': True, 'message': 'Email account added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to add email account'})
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/accounts/<int:account_id>', methods=['PUT', 'DELETE'])
def update_email_account(account_id):
    """Update or delete email account"""
    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            conn = sqlite3.connect('crm.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE email_accounts 
                SET enabled = ?, check_frequency_minutes = ?
                WHERE id = ?
            """, (data.get('enabled', True), data.get('check_frequency_minutes', 5), account_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Email account updated successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    elif request.method == 'DELETE':
        try:
            conn = sqlite3.connect('crm.db')
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM email_accounts WHERE id = ?", (account_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Email account deleted successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/check-now', methods=['POST'])
def check_emails_now():
    """Manually trigger email check for all accounts"""
    try:
        from email_automation_service import email_service
        
        # Run check in background thread
        import threading
        
        def run_check():
            email_service.check_all_accounts()
        
        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Email check initiated for all accounts'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/send-email', methods=['POST'])
def send_automated_email():
    """Send email through automation service with tracking"""
    try:
        from email_automation_service import email_service
        
        data = request.get_json()
        
        success = email_service.send_email_smtp(
            data['to_email'],
            data['subject'],
            data['content'],
            data.get('opportunity_id'),
            data.get('account_id'),
            data.get('contact_id'),
            data.get('email_type', 'general')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/processing-queue', methods=['GET'])
def get_email_processing_queue():
    """Get email processing queue status"""
    try:
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sender_email, subject, received_date, priority, status, 
                   processing_attempts, error_message, related_opportunity_id
            FROM email_processing_queue
            ORDER BY priority ASC, received_date DESC
            LIMIT 100
        """)
        
        queue_items = []
        for row in cursor.fetchall():
            queue_items.append({
                'id': row[0],
                'sender_email': row[1],
                'subject': row[2],
                'received_date': row[3],
                'priority': row[4],
                'status': row[5],
                'processing_attempts': row[6],
                'error_message': row[7],
                'related_opportunity_id': row[8]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'queue': queue_items})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/email-automation/statistics', methods=['GET'])
def get_email_automation_statistics():
    """Get comprehensive email automation statistics"""
    try:
        from email_automation_service import email_service
        
        # Get daily statistics
        stats = email_service.get_daily_email_statistics()
        
        # Get additional statistics
        conn = sqlite3.connect('crm.db')
        cursor = conn.cursor()
        
        # Weekly statistics
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM email_processing_queue 
            WHERE DATE(received_date) >= ?
        """, (week_ago,))
        emails_this_week = cursor.fetchone()[0]
        
        # Monthly statistics
        month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM email_processing_queue 
            WHERE DATE(received_date) >= ?
        """, (month_ago,))
        emails_this_month = cursor.fetchone()[0]
        
        # Account status
        cursor.execute("""
            SELECT account_name, last_check, 
                   (SELECT COUNT(*) FROM email_processing_queue epq 
                    WHERE DATE(epq.received_date) = DATE('now') 
                    AND epq.account_id = ea.id) as emails_today
            FROM email_accounts ea
            WHERE enabled = 1
        """)
        account_status = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'daily': stats,
                'weekly': {
                    'emails_received': emails_this_week
                },
                'monthly': {
                    'emails_received': emails_this_month
                },
                'accounts': [
                    {
                        'name': row[0],
                        'last_check': row[1],
                        'emails_today': row[2]
                    } for row in account_status
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/automation/process-tasks', methods=['POST'])
def process_automated_tasks():
    """Process pending automated tasks"""
    try:
        from enhanced_email_automation import EnhancedEmailAutomation
        enhanced_automation = EnhancedEmailAutomation()
        
        processed_count = enhanced_automation.process_pending_automated_tasks()
        
        return jsonify({
            'success': True, 
            'message': f'Processed {processed_count} automated tasks',
            'processed_count': processed_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Workflow Automation Endpoints
@app.route('/api/workflow/trigger/<event_type>', methods=['POST'])
def trigger_workflow_event(event_type):
    """Trigger workflow automation event"""
    try:
        from workflow_automation_manager import WorkflowAutomationManager
        workflow_manager = WorkflowAutomationManager()
        
        event_data = request.get_json() or {}
        event_data['event_type'] = event_type
        event_data['timestamp'] = datetime.now().isoformat()
        
        results = workflow_manager.trigger_workflow_event(event_type, event_data)
        
        return jsonify({
            'success': True,
            'message': f'Triggered {len(results)} workflow rules',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/workflow/statistics', methods=['GET'])
def get_workflow_statistics():
    """Get workflow automation statistics"""
    try:
        from workflow_automation_manager import WorkflowAutomationManager
        workflow_manager = WorkflowAutomationManager()
        
        stats = workflow_manager.get_workflow_statistics()
        
        return jsonify({'success': True, 'statistics': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/opportunities/<int:opportunity_id>/mark-won', methods=['POST'])
def mark_opportunity_won_with_automation(opportunity_id):
    """Mark opportunity as won and trigger automation"""
    try:
        # Mark opportunity as won
        success = crm_data.update_opportunity(opportunity_id, 
            state='Won', 
            stage='Project Started',
            modified_date=datetime.now().isoformat()
        )
        
        if success:
            # Trigger workflow automation
            from workflow_automation_manager import trigger_opportunity_won_workflow
            automation_results = trigger_opportunity_won_workflow(opportunity_id)
            
            return jsonify({
                'success': True,
                'message': 'Opportunity marked as won and automation triggered',
                'automation_results': automation_results
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update opportunity'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Calendar API endpoints
@app.route('/api/calendar-events', methods=['POST'])
def api_calendar_events():
    """Get calendar events for date range"""
    try:
        from dashboard_calendar import dashboard_calendar
        
        data = request.get_json()
        start_date = data.get('start', '')
        end_date = data.get('end', '')
        
        # Convert to date objects
        start = datetime.fromisoformat(start_date.replace('Z', '')).date() if start_date else None
        end = datetime.fromisoformat(end_date.replace('Z', '')).date() if end_date else None
        
        events = dashboard_calendar.get_calendar_events(start, end)
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        logging.error(f"Error loading calendar events: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'events': []
        }), 500

@app.route('/api/upcoming-events', methods=['GET'])
def api_upcoming_events():
    """Get upcoming events for sidebar"""
    try:
        from dashboard_calendar import dashboard_calendar
        
        days = request.args.get('days', 7, type=int)
        events = dashboard_calendar.get_upcoming_events(days)
        
        return jsonify({
            'success': True,
            'events': events
        })
        
    except Exception as e:
        logging.error(f"Error loading upcoming events: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'events': []
        }), 500

@app.route('/api/calendar-summary', methods=['GET'])
def api_calendar_summary():
    """Get calendar summary statistics"""
    try:
        from dashboard_calendar import dashboard_calendar
        
        summary = dashboard_calendar.get_calendar_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logging.error(f"Error loading calendar summary: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'summary': {}
        }), 500

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def api_complete_task(task_id):
    """Mark a task as complete"""
    try:
        # Update task status in database
        query = "UPDATE tasks SET status = 'Completed', date_modified = CURRENT_TIMESTAMP WHERE id = ?"
        crm_data.execute_query(query, (task_id,))
        
        return jsonify({
            'success': True,
            'message': 'Task marked as complete'
        })
        
    except Exception as e:
        logging.error(f"Error completing task {task_id}: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 errors"""
    from flask import Response
    return Response(status=204)  # No content response for favicon

if __name__ == '__main__':
    # Create templates and static directories
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    Path('static/css').mkdir(exist_ok=True)
    Path('static/js').mkdir(exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
