# Local CRM Web Interface
# Flask-based web interface for the CRM system

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, timedelta
import json
import os
import traceback
import logging
from pathlib import Path

# Import our CRM modules
from crm_data import crm_data
from crm_automation import crm_automation
from pdf_processor import pdf_processor

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

def paginate_results(data, page, per_page=5):
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

@app.route('/rfqs')
def rfqs():
    """RFQs list view with pagination"""
    status = request.args.get('status', '')
    manufacturer = request.args.get('manufacturer', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if status:
        filters['status'] = status
    if manufacturer:
        filters['manufacturer'] = manufacturer
    
    rfqs_list = crm_data.get_rfqs(filters)
    pagination = paginate_results(rfqs_list, page)
    
    return render_template('rfqs.html', 
                         rfqs=pagination['items'], 
                         pagination=pagination,
                         status=status, 
                         manufacturer=manufacturer)

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

@app.route('/tasks')
def tasks():
    """Tasks list view with pagination"""
    from datetime import date
    
    status = request.args.get('status', '')
    assigned_to = request.args.get('assigned_to', '')
    page = int(request.args.get('page', 1))
    
    filters = {}
    if status:
        filters['status'] = status
    if assigned_to:
        filters['assigned_to'] = assigned_to
    
    tasks_list = crm_data.get_tasks(filters)
    overdue_tasks = crm_data.get_tasks({'overdue': True})
    pagination = paginate_results(tasks_list, page)
    
    return render_template('tasks.html', 
                         tasks=pagination['items'], 
                         pagination=pagination,
                         overdue_count=len(overdue_tasks),
                         today=date.today().isoformat(),
                         status=status, 
                         assigned_to=assigned_to)

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
    """Get all contacts for dropdowns"""
    try:
        contacts = crm_data.get_contacts()
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
        # Convert sqlite3.Row objects to dictionaries
        accounts_list = []
        for account in accounts:
            account_dict = dict(account)
            accounts_list.append(account_dict)
        return jsonify(accounts_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        result = crm_automation.process_dibbs_rfq(dibbs_data)
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
        
        return jsonify({
            'success': True,
            'processed': results['processed'],
            'created': results['created'],
            'updated': results['updated'],
            'skipped': results.get('skipped', 0),
            'errors': results['errors'],
            'report_id': report_id,
            'detailed_report_available': True
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
    
    return render_template('processing_reports.html', reports=report_files)

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

if __name__ == '__main__':
    # Create templates and static directories
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    Path('static/css').mkdir(exist_ok=True)
    Path('static/js').mkdir(exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
