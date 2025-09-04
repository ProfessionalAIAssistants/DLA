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
from src.core.config_manager import config_manager
from src.core.crm_data import crm_data
from src.core.crm_automation import crm_automation
from src.pdf.dibbs_crm_processor import dibbs_processor
from src.email_automation.email_automation import email_automation

# Initialize config manager and ensure directories exist
config_manager.ensure_directories()
app_config = config_manager.get_app_config()

app = Flask(__name__)

# Use configuration for secret key
app.secret_key = os.getenv('FLASK_SECRET_KEY', app_config.get('secret_key', 'your-secret-key-here'))

# Configure template and static folders
app.template_folder = 'web/templates'
app.static_folder = 'web/static'

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
    current_settings = dibbs_processor.get_filter_settings()
    
    # Get processing statistics
    stats = {
        'processed': 0,
        'skipped': 0
    }
    
    # Count files in reviewed folders using config manager
    reviewed_dir = config_manager.get_processed_dir()
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
        dibbs_processor.update_filter_settings(settings_data)
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
                    "email_method": "smtp",  # Default method
                    "smtp_configuration": {
                        "enabled": False,
                        "host": "",
                        "port": 587,
                        "username": "",
                        "from_name": "CDE Prosperity DLA Team",
                        "reply_to_email": ""
                    },
                    "gmail_oauth2": {
                        "enabled": False,
                        "client_id": "",
                        "client_secret": "",
                        "redirect_uri": "http://localhost:5000/auth/gmail/callback",
                        "user_email": ""
                    },
                    "outlook_oauth2": {
                        "enabled": False,
                        "client_id": "",
                        "client_secret": "",
                        "tenant_id": "",
                        "redirect_uri": "http://localhost:5000/auth/outlook/callback",
                        "user_email": ""
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
            
            # Update with new settings (including OAuth2 configurations)
            existing_config.update(settings_data)
            
            # Also save OAuth2 settings to separate file if provided
            if 'oauth2_method' in settings_data:
                oauth2_config_path = 'oauth2_config.json'
                oauth2_config = {}
                
                if os.path.exists(oauth2_config_path):
                    with open(oauth2_config_path, 'r') as f:
                        oauth2_config = json.load(f)
                
                # Update OAuth2 config based on method
                method = settings_data['oauth2_method']
                if method == 'gmail_oauth' and 'gmail_oauth2' in settings_data:
                    oauth2_config['gmail_oauth2'] = settings_data['gmail_oauth2']
                elif method == 'outlook_oauth' and 'outlook_oauth2' in settings_data:
                    oauth2_config['outlook_oauth2'] = settings_data['outlook_oauth2']
                
                with open(oauth2_config_path, 'w') as f:
                    json.dump(oauth2_config, f, indent=2)
            
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
        conn = sqlite3.connect(str(config_manager.get_database_path()))
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

# OAuth2 Authorization Endpoints
@app.route('/auth/gmail/initiate', methods=['POST'])
def initiate_gmail_oauth():
    """Initiate Gmail OAuth2 authorization flow"""
    try:
        import json
        import os
        
        # Load OAuth2 config
        oauth2_config_path = 'oauth2_config.json'
        if not os.path.exists(oauth2_config_path):
            return jsonify({'success': False, 'message': 'OAuth2 configuration not found'}), 400
            
        with open(oauth2_config_path, 'r') as f:
            config = json.load(f)
            
        gmail_config = config.get('gmail_oauth2', {})
        client_id = gmail_config.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'message': 'Gmail Client ID not configured'}), 400
            
        # Generate OAuth2 authorization URL
        scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={gmail_config.get('redirect_uri', 'http://localhost:5000/auth/gmail/callback')}&"
            f"scope={' '.join(scopes)}&"
            f"response_type=code&"
            f"access_type=offline"
        )
        
        return jsonify({'success': True, 'auth_url': auth_url})
        
    except Exception as e:
        app.logger.error(f"Error initiating Gmail OAuth2: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/auth/gmail/callback')
def gmail_oauth_callback():
    """Handle Gmail OAuth2 callback"""
    try:
        # This is a placeholder for OAuth2 callback handling
        # In a full implementation, you would:
        # 1. Exchange authorization code for tokens
        # 2. Store tokens securely
        # 3. Update OAuth2 configuration
        
        code = request.args.get('code')
        if not code:
            return "Authorization failed: No code received", 400
            
        # For now, just show a success message
        return """
        <html>
        <body>
            <h2>Gmail Authorization Successful!</h2>
            <p>Authorization code received. Please complete the setup in the CRM settings.</p>
            <script>
                window.opener && window.opener.postMessage('gmail_auth_success', '*');
                window.close();
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        app.logger.error(f"Error in Gmail OAuth2 callback: {e}")
        return f"Authorization error: {str(e)}", 500

@app.route('/auth/outlook/initiate', methods=['POST'])
def initiate_outlook_oauth():
    """Initiate Outlook OAuth2 authorization flow"""
    try:
        import json
        import os
        
        # Load OAuth2 config
        oauth2_config_path = 'oauth2_config.json'
        if not os.path.exists(oauth2_config_path):
            return jsonify({'success': False, 'message': 'OAuth2 configuration not found'}), 400
            
        with open(oauth2_config_path, 'r') as f:
            config = json.load(f)
            
        outlook_config = config.get('outlook_oauth2', {})
        client_id = outlook_config.get('client_id')
        tenant_id = outlook_config.get('tenant_id')
        
        if not client_id or not tenant_id:
            return jsonify({'success': False, 'message': 'Outlook Client ID or Tenant ID not configured'}), 400
            
        # Generate OAuth2 authorization URL
        scopes = [
            'https://graph.microsoft.com/Mail.Send',
            'https://graph.microsoft.com/Mail.Read',
            'https://graph.microsoft.com/User.Read'
        ]
        
        auth_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={outlook_config.get('redirect_uri', 'http://localhost:5000/auth/outlook/callback')}&"
            f"scope={' '.join(scopes)}&"
            f"response_type=code&"
            f"response_mode=query"
        )
        
        return jsonify({'success': True, 'auth_url': auth_url})
        
    except Exception as e:
        app.logger.error(f"Error initiating Outlook OAuth2: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/auth/outlook/callback')
def outlook_oauth_callback():
    """Handle Outlook OAuth2 callback"""
    try:
        code = request.args.get('code')
        if not code:
            return "Authorization failed: No code received", 400
            
        # For now, just show a success message
        return """
        <html>
        <body>
            <h2>Outlook Authorization Successful!</h2>
            <p>Authorization code received. Please complete the setup in the CRM settings.</p>
            <script>
                window.opener && window.opener.postMessage('outlook_auth_success', '*');
                window.close();
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        app.logger.error(f"Error in Outlook OAuth2 callback: {e}")
        return f"Authorization error: {str(e)}", 500

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
    
    # Get QPL products if this account is a manufacturer
    qpl_products = crm_data.get_qpl_products_for_manufacturer(account_id)
    
    return render_template('account_detail.html', 
                         account=account, 
                         contacts=contacts, 
                         opportunities=opportunities, 
                         interactions=interactions,
                         qpl_products=qpl_products)

@app.route('/qpls')
def qpls():
    """QPLs list view with pagination"""
    search = request.args.get('search', '')
    cage_code = request.args.get('cage_code', '')
    nsn = request.args.get('nsn', '')
    page = int(request.args.get('page', 1))
    
    # Build filters
    filters = {}
    if search:
        filters['manufacturer_name'] = search
    if cage_code:
        filters['cage_code'] = cage_code
    if nsn:
        filters['nsn'] = nsn
    
    # Get QPLs with related data
    qpls_list = get_qpls_with_details(filters)
    pagination = paginate_results(qpls_list, page)
    
    # Get products and accounts for modals
    products_list = crm_data.get_products()
    accounts_list = crm_data.get_accounts()
    
    return render_template('qpls.html', 
                         qpls=pagination['items'], 
                         pagination=pagination,
                         search=search, 
                         cage_code=cage_code,
                         nsn=nsn,
                         products=products_list,
                         accounts=accounts_list)

@app.route('/qpl/<int:qpl_id>')
def qpl_detail(qpl_id):
    """QPL detail view"""
    try:
        query = """
            SELECT pm.id, pm.manufacturer_name, pm.cage_code, pm.part_number, 
                   pm.is_active, pm.created_date, pm.modified_date, pm.product_id, pm.account_id,
                   p.name as product_name, p.nsn,
                   a.name as account_name
            FROM product_manufacturers pm
            LEFT JOIN products p ON pm.product_id = p.id
            LEFT JOIN accounts a ON pm.account_id = a.id
            WHERE pm.id = ?
        """
        
        result = crm_data.execute_query(query, [qpl_id])
        
        if not result:
            flash('QPL not found', 'error')
            return redirect(url_for('qpls'))
        
        qpl_data = result[0]
        qpl = {
            'id': qpl_data['id'],
            'manufacturer_name': qpl_data['manufacturer_name'],
            'cage_code': qpl_data['cage_code'],
            'part_number': qpl_data['part_number'],
            'is_active': qpl_data['is_active'],
            'created_date': datetime.fromisoformat(qpl_data['created_date']) if qpl_data['created_date'] else None,
            'modified_date': datetime.fromisoformat(qpl_data['modified_date']) if qpl_data['modified_date'] else None,
            'product_id': qpl_data['product_id'],
            'account_id': qpl_data['account_id'],
            'product_name': qpl_data['product_name'],
            'nsn': qpl_data['nsn'],
            'account_name': qpl_data['account_name']
        }
        
        # Get products and accounts for edit modal
        products_list = crm_data.get_products()
        accounts_list = crm_data.get_accounts()
        
        return render_template('qpl_detail.html', 
                             qpl=qpl,
                             products=products_list,
                             accounts=accounts_list)
                             
    except Exception as e:
        app.logger.error(f"Error loading QPL {qpl_id}: {e}")
        flash('Error loading QPL', 'error')
        return redirect(url_for('qpls'))

def get_qpls_with_details(filters=None):
    """Get QPLs with related product and account information"""
    try:
        # Base query with joins
        query = """
            SELECT pm.id, pm.manufacturer_name, pm.cage_code, pm.part_number, 
                   pm.is_active, pm.created_date, pm.product_id, pm.account_id,
                   p.name as product_name, p.nsn,
                   a.name as account_name
            FROM product_manufacturers pm
            LEFT JOIN products p ON pm.product_id = p.id
            LEFT JOIN accounts a ON pm.account_id = a.id
        """
        
        conditions = []
        params = []
        
        if filters:
            if filters.get('manufacturer_name'):
                conditions.append("pm.manufacturer_name LIKE ?")
                params.append(f"%{filters['manufacturer_name']}%")
            if filters.get('cage_code'):
                conditions.append("pm.cage_code LIKE ?")
                params.append(f"%{filters['cage_code']}%")
            if filters.get('nsn'):
                conditions.append("p.nsn LIKE ?")
                params.append(f"%{filters['nsn']}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY pm.manufacturer_name, pm.created_date DESC"
        
        results = crm_data.execute_query(query, params)
        
        # Convert to objects for template
        qpls = []
        for row in results:
            qpl = {
                'id': row['id'],
                'manufacturer_name': row['manufacturer_name'],
                'cage_code': row['cage_code'],
                'part_number': row['part_number'],
                'is_active': row['is_active'],
                'created_date': datetime.fromisoformat(row['created_date']) if row['created_date'] else None,
                'product_id': row['product_id'],
                'account_id': row['account_id'],
                'product_name': row['product_name'],
                'nsn': row['nsn'],
                'account_name': row['account_name']
            }
            qpls.append(qpl)
        
        return qpls
        
    except Exception as e:
        app.logger.error(f"Error getting QPLs: {e}")
        return []

@app.route('/create_qpl', methods=['POST'])
def create_qpl():
    """Create a new QPL"""
    try:
        manufacturer_name = request.form.get('manufacturer_name')
        cage_code = request.form.get('cage_code')
        part_number = request.form.get('part_number')
        product_id = request.form.get('product_id')
        account_id = request.form.get('account_id')
        is_active = 'is_active' in request.form
        
        if not manufacturer_name:
            flash('Manufacturer name is required', 'error')
            return redirect(url_for('qpls'))
        
        # Create the QPL
        qpl_data = {
            'manufacturer_name': manufacturer_name,
            'cage_code': cage_code if cage_code else None,
            'part_number': part_number if part_number else None,
            'product_id': int(product_id) if product_id else None,
            'account_id': int(account_id) if account_id else None,
            'is_active': is_active,
            'created_date': datetime.now().isoformat(),
            'modified_date': datetime.now().isoformat()
        }
        
        result = create_qpl_record(qpl_data)
        
        if result:
            flash(f'QPL for {manufacturer_name} created successfully', 'success')
        else:
            flash('Error creating QPL', 'error')
            
    except Exception as e:
        app.logger.error(f"Error creating QPL: {e}")
        flash('Error creating QPL', 'error')
    
    return redirect(url_for('qpls'))

def create_qpl_record(qpl_data):
    """Create a QPL record in the database"""
    try:
        query = """
            INSERT INTO product_manufacturers 
            (manufacturer_name, cage_code, part_number, product_id, account_id, 
             is_active, created_date, modified_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = [
            qpl_data['manufacturer_name'],
            qpl_data['cage_code'],
            qpl_data['part_number'],
            qpl_data['product_id'],
            qpl_data['account_id'],
            qpl_data['is_active'],
            qpl_data['created_date'],
            qpl_data['modified_date']
        ]
        
        return crm_data.execute_query(query, params, fetch=False)
        
    except Exception as e:
        app.logger.error(f"Error creating QPL record: {e}")
        return False

@app.route('/api/qpl/<int:qpl_id>')
def get_qpl_api(qpl_id):
    """Get QPL data for editing"""
    try:
        query = """
            SELECT id, manufacturer_name, cage_code, part_number, 
                   product_id, account_id, is_active
            FROM product_manufacturers 
            WHERE id = ?
        """
        
        result = crm_data.execute_query(query, [qpl_id])
        
        if result:
            qpl = result[0]
            return jsonify({
                'success': True,
                'qpl': {
                    'id': qpl['id'],
                    'manufacturer_name': qpl['manufacturer_name'],
                    'cage_code': qpl['cage_code'],
                    'part_number': qpl['part_number'],
                    'product_id': qpl['product_id'],
                    'account_id': qpl['account_id'],
                    'is_active': qpl['is_active']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'QPL not found'})
            
    except Exception as e:
        app.logger.error(f"Error getting QPL {qpl_id}: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/qpl/<int:qpl_id>', methods=['PUT'])
def update_qpl_api(qpl_id):
    """Update QPL data"""
    try:
        data = request.get_json()
        
        query = """
            UPDATE product_manufacturers 
            SET manufacturer_name = ?, cage_code = ?, part_number = ?, 
                product_id = ?, account_id = ?, is_active = ?, modified_date = ?
            WHERE id = ?
        """
        
        params = [
            data.get('manufacturer_name'),
            data.get('cage_code'),
            data.get('part_number'),
            data.get('product_id'),
            data.get('account_id'),
            data.get('is_active', False),
            datetime.now().isoformat(),
            qpl_id
        ]
        
        result = crm_data.execute_query(query, params, fetch=False)
        
        if result:
            return jsonify({'success': True, 'message': 'QPL updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update QPL'})
            
    except Exception as e:
        app.logger.error(f"Error updating QPL {qpl_id}: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/qpl/<int:qpl_id>', methods=['DELETE'])
def delete_qpl_api(qpl_id):
    """Delete QPL"""
    try:
        query = "DELETE FROM product_manufacturers WHERE id = ?"
        result = crm_data.execute_update(query, [qpl_id])
        
        return jsonify({'success': True, 'message': 'QPL deleted successfully'})
            
    except Exception as e:
        app.logger.error(f"Error deleting QPL {qpl_id}: {e}")
        return jsonify({'success': False, 'message': str(e)})

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
    
    # Get opportunity-specific tasks
    opportunity_tasks = crm_data.get_tasks({'parent_item_type': 'Opportunity', 'parent_item_id': opportunity_id})
    
    return render_template('opportunity_detail.html', 
                         opportunity=opportunity,
                         account=account,
                         contact=contact,
                         product=product,
                         interactions=interactions,
                         opportunity_tasks=opportunity_tasks)

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
            if field in data and data[field] is not None:
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
            if field in data and data[field] is not None:
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
        # datetime already imported at top of file
        
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
            # datetime already imported at top of file
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

@app.route('/quotes')
def quotes():
    """Quotes list view with pagination"""
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
    
    quotes_list = crm_data.get_quotes(filters)
    pagination = paginate_results(quotes_list, page)
    
    return render_template('quotes.html', 
                         rfqs=pagination['items'], 
                         pagination=pagination,
                         status=status, 
                         manufacturer=manufacturer,
                         vendor=vendor,
                         product=product)

# Keep legacy RFQ route for backward compatibility but redirect to quotes
@app.route('/rfqs')
def rfqs():
    """Legacy RFQ route - redirects to quotes"""
    return redirect(url_for('quotes', **request.args))

# Legacy RFQ detail route - redirects to quote detail
@app.route('/rfq/<int:rfq_id>')
def rfq_detail(rfq_id):
    """Legacy RFQ detail route - redirects to quote detail"""
    return redirect(url_for('quote_detail', quote_id=rfq_id))

@app.route('/quote/<int:quote_id>')
def quote_detail(quote_id):
    """Quote detail view"""
    quote = crm_data.get_quote_by_id(quote_id)
    if not quote:
        flash('Quote not found', 'error')
        return redirect(url_for('quotes'))
    
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
                         quote=quote,  # For quote_detail.html template
                         rfq=quote,    # For backward compatibility
                         opportunity=opportunity, 
                         account=account, 
                         contact=contact)

@app.route('/tasks')
def tasks():
    """Tasks list view with pagination"""
        # datetime already imported at top of file
    
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

# ==================== PDF FILE ROUTES ====================

@app.route('/download-pdf/<int:opportunity_id>')
def download_pdf(opportunity_id):
    """Download PDF file associated with an opportunity"""
    from flask import send_file, abort
    import os
    
    try:
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return render_template('error.html', error='Opportunity not found'), 404
        
        pdf_file_path = opportunity.get('pdf_file_path')
        if not pdf_file_path:
            return render_template('error.html', error='No PDF file is associated with this opportunity. The PDF may have been processed but not saved to the database.'), 404
        
        # Get the filename
        filename = os.path.basename(pdf_file_path)
        
        # Check multiple possible locations
        possible_paths = [
            pdf_file_path,  # Original path
            os.path.join('data', 'processed', 'Reviewed', filename),  # Reviewed folder
            os.path.join('data', 'processed', 'Automation', filename),  # Automation folder
            os.path.join('data', 'output', filename),  # Output folder
            os.path.join('data', 'upload', filename),  # Upload root
        ]
        
        actual_path = None
        for path in possible_paths:
            if os.path.exists(path):
                actual_path = path
                break
        
        if not actual_path:
            return render_template('error.html', 
                error=f'PDF file "{filename}" not found. Checked locations: {", ".join(possible_paths)}. The file may have been moved or deleted.'), 404
        
        return send_file(actual_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        app.logger.error(f"Error downloading PDF for opportunity {opportunity_id}: {str(e)}")
        return render_template('error.html', error=f'Error accessing PDF file: {str(e)}'), 500

@app.route('/view-pdf/<int:opportunity_id>')
def view_pdf(opportunity_id):
    """View PDF file associated with an opportunity in browser"""
    from flask import send_file, abort
    import os
    
    try:
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return render_template('error.html', error='Opportunity not found'), 404
        
        pdf_file_path = opportunity.get('pdf_file_path')
        if not pdf_file_path:
            return render_template('error.html', error='No PDF file is associated with this opportunity. The PDF may have been processed but not saved to the database.'), 404
        
        # Get the filename
        filename = os.path.basename(pdf_file_path)
        
        # Check multiple possible locations
        possible_paths = [
            pdf_file_path,  # Original path
            os.path.join('data', 'processed', 'Reviewed', filename),  # Reviewed folder
            os.path.join('data', 'processed', 'Automation', filename),  # Automation folder
            os.path.join('data', 'output', filename),  # Output folder
            os.path.join('data', 'upload', filename),  # Upload root
        ]
        
        actual_path = None
        for path in possible_paths:
            if os.path.exists(path):
                actual_path = path
                break
        
        if not actual_path:
            return render_template('error.html', 
                error=f'PDF file "{filename}" not found. Checked locations: {", ".join(possible_paths)}. The file may have been moved or deleted.'), 404
        
        return send_file(actual_path, as_attachment=False, download_name=filename, mimetype='application/pdf')
        
    except Exception as e:
        app.logger.error(f"Error viewing PDF for opportunity {opportunity_id}: {str(e)}")
        return render_template('error.html', error=f'Error accessing PDF file: {str(e)}'), 500

# ==================== PRODUCTS ROUTES ====================

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

@app.route('/products/<product_identifier>')
def product_detail(product_identifier):
    """Product detail page with QPL information"""
    try:
        # Try to get product by NSN first, then by ID
        product = None
        if product_identifier.isdigit():
            # If it's all digits, try ID first, then NSN
            product = crm_data.get_product_by_id(int(product_identifier))
            if not product:
                product = crm_data.get_product_by_nsn(product_identifier)
        else:
            # If it contains non-digits, treat as NSN
            product = crm_data.get_product_by_nsn(product_identifier)
        
        if not product:
            return render_template('error.html', error='Product not found'), 404
        
        # Get QPL manufacturers for this product
        qpl_manufacturers = crm_data.get_qpl_manufacturers_for_product(product['id'])
        
        # Get vendors (accounts associated with QPL entries)
        vendors = []
        qpl_account_ids = [qpl['account_id'] for qpl in qpl_manufacturers if qpl.get('account_id')]
        if qpl_account_ids:
            vendors = crm_data.get_accounts_by_ids(qpl_account_ids)
        
        # Get related opportunities by NSN to ensure correct matching
        opportunities = crm_data.get_opportunities({'nsn': product['nsn']}) if product.get('nsn') else []
        
        # Get quotes related to this product (via NSN or opportunities)
        quotes = crm_data.get_quotes_for_product(product['id'], product.get('nsn'))
        
        return render_template('product_detail.html',
                             product=product,
                             qpl_manufacturers=qpl_manufacturers,
                             vendors=vendors,
                             opportunities=opportunities,
                             quotes=quotes)
                             
    except Exception as e:
        return render_template('error.html', error=str(e))

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
        # Decode URL-encoded NSN
        from urllib.parse import unquote
        nsn = unquote(nsn)
        
        # Get the product first to get its ID
        products = crm_data.get_products({'nsn': nsn})
        if not products:
            return jsonify({'error': 'Product not found. It may have already been deleted.'}), 404
            
        product = products[0]
        product_id = product['id']
        
        # Check for dependencies (RFQs, opportunities, etc.)
        # Check RFQs
        rfqs = crm_data.execute_query("SELECT COUNT(*) as count FROM rfqs WHERE product_id = ?", [product_id])
        if rfqs and rfqs[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete product. It is referenced by {rfqs[0]["count"]} quote(s). Please remove these references first.'
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
        app.logger.error(f"Error deleting product {nsn}: {str(e)}")  # Better logging
        return jsonify({'error': f'Failed to delete product: {str(e)}'}), 500

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
        # datetime already imported at top of file
    
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
    try:
        interaction = crm_data.get_interaction_by_id(interaction_id)
        if not interaction:
            return render_template('error.html', error="Interaction not found"), 404
        
        return render_template('interaction_detail.html', interaction=interaction)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

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
    """Update RFQ status (legacy route)"""
    try:
        status = request.json.get('status')
        opportunity_id = request.json.get('opportunity_id')
        
        crm_data.update_rfq_status(rfq_id, status, opportunity_id)
        return jsonify({'success': True, 'message': 'RFQ status updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/quotes/<int:quote_id>/status', methods=['POST'])
def update_quote_status(quote_id):
    """Update quote status"""
    try:
        status = request.json.get('status')
        opportunity_id = request.json.get('opportunity_id')
        
        crm_data.update_rfq_status(quote_id, status, opportunity_id)
        return jsonify({'success': True, 'message': 'Quote status updated'})
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
    """Update a Quote"""
    try:
        data = request.json
        
        # Update the Quote
        updated = crm_data.update_quote(quote_id, **data)
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
            
        # Remove empty values but preserve parent_item fields
        important_fields = ['parent_item_type', 'parent_item_id']
        task_data = {k: v for k, v in task_data.items() if v or k in important_fields}
        
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
        
        # Get related opportunities using the new method
        opportunities = crm_data.get_opportunities_linked_to_task(task_id)
        processing_report = ""
        
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
        # datetime already imported at top of file
            updates['start_date'] = datetime.now().strftime("%Y-%m-%d")
        
        # If completing the task, set completed date
        elif status == 'Completed':
        # datetime already imported at top of file
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
        # datetime already imported at top of file
        
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
        # datetime already imported at top of file
        
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

@app.route('/api/interactions', methods=['GET'])
def api_get_interactions():
    """Get all interactions via API"""
    try:
        interactions = crm_data.get_interactions()
        return jsonify(interactions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Project detail page"""
    project = crm_data.get_project_by_id(project_id)
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('projects'))
    
    # Get related data
    vendor = None
    if project.get('vendor_id'):
        vendor = crm_data.get_account_by_id(project['vendor_id'])
    
    parent_project = None
    if project.get('parent_project_id'):
        parent_project = crm_data.get_project_by_id(project['parent_project_id'])
    
    # Get sub-projects
    sub_projects = crm_data.get_projects({'parent_project_id': project_id})
    
    # Get related tasks (if any)
    related_tasks = []
    try:
        all_tasks = crm_data.get_tasks()
        related_tasks = [task for task in all_tasks if str(project_id) in str(task.get('subject', '')) or str(project_id) in str(task.get('description', ''))]
    except:
        pass
    
    return render_template('project_detail.html',
                         project=project,
                         vendor=vendor,
                         parent_project=parent_project,
                         sub_projects=sub_projects,
                         related_tasks=related_tasks)

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
        to_process_dir = config_manager.get_upload_dir()
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
        # Check if the To Process directory exists first using config manager
        to_process_dir = config_manager.get_upload_dir()
        if not to_process_dir.exists():
            return jsonify({
                'success': False,
                'message': 'Upload directory does not exist'
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
            
        # Process the PDFs using DIBBs processor
        results = dibbs_processor.process_all_pdfs()
        
        # Generate a comprehensive report ID for viewing
        # datetime already imported at top of file
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Auto-create single review task for successful processing
        if results['processed'] > 0:
            try:
                # Create task due today
                today = datetime.now().strftime("%Y-%m-%d")
                process_date = datetime.now().strftime("%B %d, %Y")
                
                # Get created opportunities for summary
                created_opportunities = []
                if 'created_opportunities' in results and results['created_opportunities']:
                    created_opportunities = results['created_opportunities']
                
                # Simple, clean task description with NSN and proper formatting  
                task_description = f"""Please review all new opportunities

Processing Report:
{results.get('detailed_report', 'No detailed report available')}

Created Opportunities:
{chr(10).join([f"• {opp.get('request_number', 'Unknown')} (ID: {opp.get('id', 'N/A')}) - NSN: {opp.get('nsn', 'N/A')}" for opp in created_opportunities]) if created_opportunities else 'None'}"""

                # Create ONE comprehensive review task with specific title format
                task_id = crm_data.create_task(
                    subject=f"DIBBs PDF review {process_date}",
                    description=task_description,
                    status="Not Started",
                    priority="High",
                    type="Follow-up",
                    due_date=today,
                    work_date=today,  # Set work date to today
                    assigned_to="System Generated"
                )
                
                # Track task creation in results
                if 'created_tasks' not in results:
                    results['created_tasks'] = []
                results['created_tasks'].append({
                    'id': task_id,
                    'subject': f"DIBBs PDF review {process_date}",
                    'type': 'PDF Processing Review',
                    'created_opportunities': created_opportunities
                })
                
                app.logger.info(f"Auto-created review task {task_id} for PDF processing results")
                
            except Exception as task_error:
                app.logger.error(f"Error creating review task: {str(task_error)}")
                # Don't fail the whole operation if task creation fails
        
        return jsonify({
            'success': True,
            'processed': results['processed'],
            'created': results['created'],
            'updated': len(results.get('updated_contacts', [])) + len(results.get('updated_accounts', [])),
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

@app.route('/api/create_account', methods=['POST'])
def create_account():
    """Create a new account"""
    try:
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'error': 'Account name is required'}), 400
        
        # Create the account
        account_id = crm_data.create_account(**data)
        if account_id:
            return jsonify({
                'success': True, 
                'message': 'Account created successfully',
                'account_id': account_id
            })
        else:
            return jsonify({'error': 'Failed to create account'}), 500
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
        # Check if account exists
        account = crm_data.get_account_by_id(account_id)
        if not account:
            return jsonify({'error': 'Account not found. It may have already been deleted.'}), 404
        
        # Check for related contacts
        contacts = crm_data.get_contacts_by_account(account_id)
        if contacts:
            return jsonify({
                'error': f'Cannot delete account. It has {len(contacts)} associated contact(s). Please remove these contacts first.'
            }), 400
        
        # Check for related opportunities  
        opportunities = crm_data.get_opportunities(filters={'account_id': account_id})
        if opportunities:
            return jsonify({
                'error': f'Cannot delete account. It has {len(opportunities)} associated opportunity(ies). Please remove these opportunities first.'
            }), 400
        
        # Check for related interactions
        interactions = crm_data.execute_query("SELECT COUNT(*) as count FROM interactions WHERE account_id = ?", [account_id])
        if interactions and interactions[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete account. It has {interactions[0]["count"]} associated interaction(s). Please remove these interactions first.'
            }), 400
        
        # Delete the account
        deleted = crm_data.delete_account(account_id)
        if deleted:
            return jsonify({'success': True, 'message': 'Account deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete account. No rows were affected.'}), 500
    except Exception as e:
        app.logger.error(f"Error deleting account {account_id}: {str(e)}")
        return jsonify({'error': f'Failed to delete account: {str(e)}'}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        # Check if contact exists
        contact = crm_data.get_contact_by_id(contact_id)
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        # Check for related data (interactions, opportunities, etc.)
        interactions = crm_data.execute_query("SELECT COUNT(*) as count FROM interactions WHERE contact_id = ?", [contact_id])
        if interactions and interactions[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete contact. It has {interactions[0]["count"]} associated interaction(s). Please remove these interactions first.'
            }), 400
        
        # Check for related opportunities
        opportunities = crm_data.execute_query("SELECT COUNT(*) as count FROM opportunities WHERE contact_id = ?", [contact_id])
        if opportunities and opportunities[0]['count'] > 0:
            return jsonify({
                'error': f'Cannot delete contact. It has {opportunities[0]["count"]} associated opportunity(ies). Please remove these opportunities first.'
            }), 400
        
        # Delete the contact
        deleted = crm_data.delete_contact(contact_id)
        if deleted:
            return jsonify({'success': True, 'message': 'Contact deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete contact'}), 500
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
    
    # Count files in reviewed folders using config manager
    reviewed_dir = config_manager.get_processed_dir()
    if reviewed_dir.exists():
        stats['processed'] = len(list(reviewed_dir.glob("*.pdf"))) + len(list(reviewed_dir.glob("*.PDF")))
        
        skipped_dir = reviewed_dir / "Skipped"
        if skipped_dir.exists():
            stats['skipped'] = len(list(skipped_dir.glob("*.pdf"))) + len(list(skipped_dir.glob("*.PDF")))
    
    # Get all report files using config manager
    output_dir = config_manager.get_output_dir()
    report_files = []
    
    if output_dir.exists():
        for report_file in sorted(output_dir.glob("pdf_processing_report_*.json"), reverse=True):
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                # Extract summary info for listing - handle both new and legacy formats
                summary = report_data.get('summary', {})
                
                # For new format reports, use the summary data
                if summary:
                    processed_count = summary.get('files_processed', 0)
                    created_count = summary.get('opportunities_created', 0)
                    skipped_count = summary.get('files_skipped', 0)
                    errors_count = summary.get('errors', 0)
                    # For updated records, count from processed files or use fallback
                    updated_count = 0
                    if 'updated_records' in report_data:
                        for record_type, records in report_data['updated_records'].items():
                            updated_count += len(records) if isinstance(records, list) else records
                else:
                    # Legacy format fallback
                    processed_count = len(report_data.get('processed_files', []))
                    created_count = len([f for f in report_data.get('processed_files', []) if f.get('status') == 'processed'])
                    skipped_count = len(report_data.get('skipped_files', []))
                    errors_count = len(report_data.get('error_files', []))
                    updated_count = 0
                
                report_files.append({
                    'filename': report_file.name,
                    'timestamp': report_data.get('processing_start', ''),
                    'processed': processed_count,
                    'created': created_count,
                    'updated': updated_count,
                    'skipped': skipped_count,
                    'errors': errors_count
                })
            except Exception as e:
                print(f"Error reading report {report_file}: {e}")
                continue
    
    return render_template('processing_reports.html', reports=report_files, stats=stats)

@app.route('/processing-reports/<filename>')
def view_processing_report(filename):
    """View detailed processing report"""
    import json
    from pathlib import Path
    
    report_file = config_manager.get_output_dir() / filename
    
    if not report_file.exists():
        return "Report not found", 404
    
    try:
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        # Ensure compatibility with template expectations
        # Handle both old and new report formats
        if 'created_records' not in report_data:
            # Create empty structure for old reports that don't have detailed tracking
            report_data['created_records'] = {}
            report_data['updated_records'] = {}
            
            # If we have summary data, use it to populate basic structure
            if 'summary' in report_data:
                summary = report_data['summary']
                opportunities_created = summary.get('opportunities_created', 0)
                if opportunities_created > 0:
                    report_data['created_records']['opportunities'] = []
                    # Try to get opportunity IDs from processed files
                    for file_data in report_data.get('processed_files', []):
                        if 'opportunity_id' in file_data:
                            report_data['created_records']['opportunities'].append({
                                'id': file_data['opportunity_id'],
                                'name': file_data.get('rfq_data', {}).get('request_number', 'Unknown'),
                                'amount': None,
                                'created_from': file_data.get('filename', 'Unknown')
                            })
        
        # Handle file-level created_records for processed files
        for file_data in report_data.get('processed_files', []):
            if 'created_records' not in file_data:
                file_data['created_records'] = 1 if file_data.get('status') == 'processed' else 0
            if 'updated_records' not in file_data:
                file_data['updated_records'] = 0
        
        # Handle skipped files
        for file_data in report_data.get('skipped_files', []):
            if 'created_records' not in file_data:
                file_data['created_records'] = 0
            if 'updated_records' not in file_data:
                file_data['updated_records'] = 0
        
        return render_template('processing_report_detail.html', report=report_data, filename=filename)
    except Exception as e:
        return f"Error loading report: {e}", 500

@app.route('/api/processing-report/<filename>/opportunities')
def get_processing_report_opportunities(filename):
    """Get opportunities created by a specific processing report"""
    import json
    from pathlib import Path
    
    try:
        page = int(request.args.get('page', 1))
        per_page = 10
        
        report_file = config_manager.get_output_dir() / filename
        
        if not report_file.exists():
            return jsonify({'error': 'Report not found'}), 404
        
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        # Get opportunity IDs from the report
        opportunity_ids = []
        
        # From processed files
        for file_data in report_data.get('processed_files', []):
            if 'opportunity_id' in file_data:
                opportunity_ids.append(file_data['opportunity_id'])
        
        # From created records structure
        if 'created_records' in report_data and 'opportunities' in report_data['created_records']:
            for opp in report_data['created_records']['opportunities']:
                if 'id' in opp and opp['id'] not in opportunity_ids:
                    opportunity_ids.append(opp['id'])
        
        if not opportunity_ids:
            return jsonify({
                'opportunities': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        
        # Get opportunities from database with pagination
        opportunities_query = f"""
            SELECT id, name, stage, amount, created_date, description, mfr, quantity, unit, 
                   delivery_days, owner
            FROM opportunities 
            WHERE id IN ({','.join(['?' for _ in opportunity_ids])})
            ORDER BY created_date DESC
            LIMIT ? OFFSET ?
        """
        
        offset = (page - 1) * per_page
        params = opportunity_ids + [per_page, offset]
        
        opportunities = crm_data.execute_query(opportunities_query, params)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM opportunities 
            WHERE id IN ({','.join(['?' for _ in opportunity_ids])})
        """
        total_result = crm_data.execute_query(count_query, opportunity_ids)
        total = total_result[0]['total'] if total_result else 0
        
        total_pages = (total + per_page - 1) // per_page
        
        # Format opportunities for frontend
        formatted_opportunities = []
        for opp in opportunities:
            # Extract NSN from description if present
            nsn = None
            description = opp.get('description', '')
            if description and 'NSN:' in description:
                nsn_part = description.split('NSN:')[1].strip().split()[0]
                nsn = nsn_part if nsn_part else None
            
            formatted_opportunities.append({
                'id': opp['id'],
                'name': opp['name'] or f"RFQ-{opp['id']}",
                'stage': opp['stage'] or 'Prospecting',
                'amount': opp['amount'],
                'created_at': opp['created_date'],
                'nsn': nsn,
                'assigned_to': opp.get('owner')
            })
        
        return jsonify({
            'opportunities': formatted_opportunities,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-report/opportunities/<int:opportunity_id>', methods=['PUT'])
def update_processing_report_opportunity(opportunity_id):
    """Update an opportunity from processing report"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Update opportunity
        update_data = {
            'name': data.get('name'),
            'stage': data.get('stage'),
            'amount': data.get('amount'),
            'assigned_to': data.get('assigned_to')
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = crm_data.update_opportunity(opportunity_id, **update_data)
        
        if result:
            return jsonify({'success': True, 'message': 'Opportunity updated successfully'})
        else:
            return jsonify({'error': 'Failed to update opportunity'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-report/opportunities/<int:opportunity_id>', methods=['DELETE'])
def delete_processing_report_opportunity(opportunity_id):
    """Delete an opportunity from processing report"""
    try:
        # Check if opportunity exists
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Delete opportunity (this should cascade to related records)
        result = crm_data.delete_opportunity(opportunity_id)
        
        if result:
            return jsonify({'success': True, 'message': 'Opportunity deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete opportunity'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest-processing-report')
def get_latest_processing_report():
    """Get the latest processing report data"""
    import json
    from pathlib import Path
    
    output_dir = config_manager.get_output_dir()
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
@app.route('/api/vendor-emails/<email_id>', methods=['GET'])
def get_vendor_email_content(email_id):
    """Get vendor email content for preview"""
    try:
        email_content = email_automation.get_vendor_email_content(email_id)
        
        if email_content:
            return jsonify({'success': True, 'email': email_content})
        else:
            return jsonify({'success': False, 'message': 'Email not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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

# Calendar API endpoints
@app.route('/api/calendar-events', methods=['GET', 'POST'])
def api_calendar_events():
    """Get calendar events for date range"""
    try:
        from src.core.dashboard_calendar import dashboard_calendar
        
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.get_json() or {}
            start_date = data.get('start', '')
            end_date = data.get('end', '')
        else:  # GET request
            start_date = request.args.get('start', '')
            end_date = request.args.get('end', '')
        
        # Convert to datetime objects if provided
        start = None
        end = None
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', ''))
            except:
                start = None
                
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', ''))
            except:
                end = None
        
        events = dashboard_calendar.get_calendar_events(start, end)
        
        return jsonify(events)  # Return events directly for FullCalendar
        
    except Exception as e:
        logging.error(f"Error loading calendar events: {e}")
        return jsonify([]), 500  # Return empty array on error

@app.route('/api/upcoming-events', methods=['GET'])
def api_upcoming_events():
    """Get upcoming events for sidebar"""
    try:
        from src.core.dashboard_calendar import dashboard_calendar
        
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
        from src.core.dashboard_calendar import dashboard_calendar
        
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
        # Update task status in database (removing date_modified reference since column doesn't exist)
        query = "UPDATE tasks SET status = 'Completed' WHERE id = ?"
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

# ==================== QPL API ROUTES ====================

@app.route('/api/qpl-entries/<int:qpl_id>', methods=['DELETE'])
def delete_qpl_entry(qpl_id):
    """Delete a QPL entry"""
    try:
        query = "DELETE FROM product_manufacturers WHERE id = ?"
        result = crm_data.execute_update(query, (qpl_id,))
        
        return jsonify({'success': True, 'message': 'QPL entry removed successfully'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/<int:product_id>/qpl-manufacturers')
def get_product_qpl_manufacturers(product_id):
    """Get QPL manufacturers for a product"""
    try:
        manufacturers = crm_data.get_qpl_manufacturers_for_product(product_id)
        return jsonify({'success': True, 'manufacturers': manufacturers})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts/<int:account_id>/qpl-products')
def get_account_qpl_products(account_id):
    """Get QPL products for a manufacturer/account"""
    try:
        products = crm_data.get_qpl_products_for_manufacturer(account_id)
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/qpl/search')
def search_qpl_entries():
    """Search QPL entries"""
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term required'})
            
        entries = crm_data.search_qpl_entries(search_term)
        return jsonify({'success': True, 'entries': entries})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/qpl/stats')
def get_qpl_stats():
    """Get QPL summary statistics"""
    try:
        stats = crm_data.get_qpl_summary_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/<int:product_id>/qpl-export')
def export_product_qpl_data(product_id):
    """Export QPL data for a product as CSV"""
    try:
        import csv
        import io
        from flask import make_response
        
        # Get product and QPL data
        product = crm_data.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        qpl_manufacturers = crm_data.get_qpl_manufacturers_for_product(product_id)
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['NSN', 'Product Name', 'Manufacturer', 'CAGE Code', 'Part Number', 'Date Added'])
        
        # Write data
        for qpl in qpl_manufacturers:
            writer.writerow([
                product['nsn'] or '',
                product['name'] or '',
                qpl['manufacturer_name'] or '',
                qpl['cage_code'] or '',
                qpl['part_number'] or '',
                qpl['created_date'] or ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=qpl_data_{product["nsn"] or product_id}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/clear-all-reports', methods=['POST'])
def clear_all_reports():
    """Clear all processing reports"""
    try:
        output_dir = config_manager.get_output_dir()
        if not output_dir.exists():
            return jsonify({'success': True, 'message': 'No reports to clear'})
        
        # Count reports before deletion
        report_files = list(output_dir.glob("pdf_processing_report_*.json"))
        count = len(report_files)
        
        # Delete all report files
        for report_file in report_files:
            try:
                report_file.unlink()
            except Exception as e:
                print(f"Error deleting report {report_file.name}: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'Successfully cleared {count} processing reports'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete-report/<filename>', methods=['DELETE'])
def delete_report(filename):
    """Delete a specific processing report"""
    try:
        # Validate filename to prevent path traversal attacks
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'})
        
        output_dir = config_manager.get_output_dir()
        report_file = output_dir / filename
        
        if not report_file.exists():
            return jsonify({'success': False, 'error': 'Report not found'})
        
        # Ensure it's actually a processing report file
        if not filename.startswith('pdf_processing_report_') or not filename.endswith('.json'):
            return jsonify({'success': False, 'error': 'Invalid report file'})
        
        # Delete the file
        report_file.unlink()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted report: {filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to prevent 404 errors"""
    from flask import Response
    return Response(status=204)  # No content response for favicon

if __name__ == '__main__':
    # Create web directories
    Path('web/templates').mkdir(parents=True, exist_ok=True)
    Path('web/static').mkdir(parents=True, exist_ok=True)
    Path('web/static/css').mkdir(parents=True, exist_ok=True)
    Path('web/static/js').mkdir(parents=True, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
