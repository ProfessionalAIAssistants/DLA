# CRM Business Logic and Automation Engine
# Handles automation rules, calculations, and business logic

# Import crm_data using direct import 
import sys
from pathlib import Path

# Add the src directory to the path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from core import crm_data

# Create module reference for backward compatibility  
crm_data = crm_data.crm_data
from datetime import datetime, date, timedelta
import re

class CRMAutomation:
    
    def __init__(self):
        self.automation_rules = {
            'rfq_qualification': self.qualify_opportunity,
            'opportunity_creation': self.auto_create_opportunity,
            'task_assignment': self.auto_assign_tasks,
            'account_matching': self.match_or_create_account,
            'contact_matching': self.match_or_create_contact
        }
    
    def process_dibbs_solicitation(self, dibbs_data):
        """Main automation workflow for processing DIBBs DLA solicitation data"""
        
        # 1. Match or create account (government agency)
        account_id = self.match_or_create_account(dibbs_data)
        
        # 2. Match or create contact (buyer)
        contact_id = self.match_or_create_contact(dibbs_data, account_id)
        
        # 3. Check qualification criteria
        is_qualified = self.qualify_opportunity(dibbs_data)
        
        # 4. Auto-create opportunity if qualified and setting is enabled
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        processor = DIBBsCRMProcessor()
        settings = processor.get_filter_settings()
        
        opportunity_id = None
        if is_qualified and not dibbs_data.get('skipped') and settings.get('auto_create_opportunities', True):
            opportunity_id = self.auto_create_opportunity_from_solicitation(account_id, contact_id, dibbs_data)
        
        # 5. Auto-assign tasks
        self.auto_assign_tasks(None, opportunity_id, dibbs_data)
        
        return {
            'account_id': account_id,
            'contact_id': contact_id,
            'opportunity_id': opportunity_id,
            'qualified': is_qualified
        }
    
    def qualify_opportunity(self, dibbs_data):
        """Determine if DLA solicitation meets qualification criteria"""
        
        # Get settings from dibbs_crm_processor
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        processor = DIBBsCRMProcessor()
        settings = processor.get_filter_settings()
        
        # Configuration-based qualification rules from settings
        qualification_rules = {
            'min_delivery_days': settings.get('min_delivery_days', 120),
            'required_iso': settings.get('iso_required', 'NO'),
            'required_sampling': settings.get('sampling_required', 'NO'),
            'required_inspection_point': settings.get('inspection_point', 'DESTINATION'),
            'preferred_manufacturers': [m.strip() for m in settings.get('manufacturer_filter', '').split('\n') if m.strip()],
            'excluded_fsc': [],  # Add FSCs to exclude if needed
            'preferred_fsc': [f.strip() for f in settings.get('fsc_filter', '').split('\n') if f.strip()],
            'excluded_packaging_types': [],  # Add packaging types to exclude
            'preferred_packaging_types': [p.strip() for p in settings.get('packaging_filter', '').split('\n') if p.strip()],
            'min_quantity': 1
        }
        
        # Check delivery days
        delivery_days = dibbs_data.get('delivery_days')
        if delivery_days and int(delivery_days) < qualification_rules['min_delivery_days']:
            return False
        
        # Check ISO requirement
        if dibbs_data.get('iso') != qualification_rules['required_iso']:
            return False
        
        # Check sampling requirement
        if dibbs_data.get('sampling') != qualification_rules['required_sampling']:
            return False
        
        # Check inspection point
        if dibbs_data.get('inspection_point') != qualification_rules['required_inspection_point']:
            return False
        
        # Check manufacturer preference
        manufacturer = dibbs_data.get('mfr', '').lower()
        if not any(pref_mfr.lower() in manufacturer for pref_mfr in qualification_rules['preferred_manufacturers']):
            return False
        
        # Check quantity
        quantity = dibbs_data.get('quantity')
        if quantity and int(quantity) < qualification_rules['min_quantity']:
            return False
        
        # Check FSC criteria
        fsc = dibbs_data.get('fsc', '')
        if fsc:
            # Check if FSC is in excluded list
            if qualification_rules['excluded_fsc'] and fsc in qualification_rules['excluded_fsc']:
                return False
            # Check if FSC is in preferred list (if list is not empty)
            if qualification_rules['preferred_fsc'] and fsc not in qualification_rules['preferred_fsc']:
                return False
        
        # Check packaging type criteria
        packaging_type = dibbs_data.get('package_type', '')
        if packaging_type:
            # Check if packaging type is in excluded list
            if qualification_rules['excluded_packaging_types'] and packaging_type in qualification_rules['excluded_packaging_types']:
                return False
            # Check if packaging type is in preferred list (if list is not empty)
            if qualification_rules['preferred_packaging_types'] and packaging_type not in qualification_rules['preferred_packaging_types']:
                return False

        return True
    
    def match_or_create_account(self, dibbs_data):
        """Match existing account or create new one based on buyer office using intelligent matching"""
        
        office = dibbs_data.get('office', '')
        division = dibbs_data.get('division', '')
        address = dibbs_data.get('address', '')
        
        if not office:
            office = "Unknown Government Agency"
        
        # Use intelligent account matcher to respect parent-child relationships
        try:
            # Import the intelligent account matcher
            import sys
            from pathlib import Path
            root_dir = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(root_dir))
            from intelligent_account_matcher import intelligent_account_matcher
            
            print(f"[CRM Automation] Using intelligent account matcher for Office='{office}', Division='{division}'")
            account_id = intelligent_account_matcher.smart_account_match(office, division, address)
            
            if account_id:
                print(f"[CRM Automation] Intelligent matcher returned account ID: {account_id}")
                return account_id
            else:
                print(f"[CRM Automation] Intelligent matcher failed, falling back to legacy logic")
        except Exception as e:
            print(f"[CRM Automation] Failed to use intelligent matcher: {e}, falling back to legacy logic")
        
        # Fallback to original logic if intelligent matcher fails
        existing_accounts = crm_data.get_accounts({'name': office})
        
        if existing_accounts:
            return existing_accounts[0]['id']
        
        # Create new account as last resort
        account_data = {
            'name': office,
            'type': 'Customer',  # Use correct field name
            'summary': f"Government Agency - {office}",
            'billing_address': address,
            'is_active': True
        }
        
        return crm_data.create_account(**account_data)
    
    def match_or_create_contact(self, dibbs_data, account_id):
        """Match existing contact or create new one based on buyer info"""
        
        buyer_name = dibbs_data.get('buyer', '')
        buyer_email = dibbs_data.get('email', '')
        
        if not buyer_name:
            buyer_name = "Unknown Buyer"
        
        # Try to find existing contact by email
        if buyer_email:
            existing_contacts = crm_data.get_contacts({'email': buyer_email})
            if existing_contacts:
                return existing_contacts[0]['id']
        
        # Parse name into first and last
        name_parts = buyer_name.split()
        first_name = name_parts[0] if name_parts else 'Unknown'
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Buyer'
        
        # Create new contact
        contact_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': buyer_email,
            'phone': dibbs_data.get('telephone', ''),
            'account_id': account_id,
            'title': 'Contracting Officer',
            'lead_source': 'DIBBs',
            'address': dibbs_data.get('address', ''),
            'description': f"Buyer Code: {dibbs_data.get('buyer_code', '')}",
            'owner': 'System'
        }
        
        return crm_data.create_contact(**contact_data)
    
    def auto_create_opportunity_from_solicitation(self, account_id, contact_id, dibbs_data):
        """Auto-create opportunity from DLA solicitation"""
        
        # Create opportunity name from solicitation data (just the request number)
        request_number = dibbs_data.get('request_number', 'Unknown')
        opportunity_name = f"{request_number}"
        
        # Check for duplicates
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        processor = DIBBsCRMProcessor()
        settings = processor.get_filter_settings()
        
        if settings.get('skip_duplicates', True):
            existing_opps = crm_data.execute_query(
                "SELECT id FROM opportunities WHERE name LIKE ? OR description LIKE ?",
                [f"%{request_number}%", f"%{request_number}%"]
            )
            if existing_opps:
                print(f"Skipping duplicate opportunity for solicitation {request_number}")
                return existing_opps[0]['id']
        
        # Build description
        description = f"DLA Solicitation: {request_number}\n"
        if dibbs_data.get('product_description'):
            description += f"Product: {dibbs_data['product_description']}\n"
        if dibbs_data.get('nsn'):
            description += f"NSN: {dibbs_data['nsn']}\n"
        if dibbs_data.get('quantity'):
            description += f"Quantity: {dibbs_data['quantity']}\n"
        if dibbs_data.get('delivery_days'):
            description += f"Delivery Days: {dibbs_data['delivery_days']}\n"
            
        opportunity_data = {
            'name': opportunity_name,
            'account_id': account_id,
            'contact_id': contact_id,
            'stage': 'Prospecting',
            'type': 'New Business',
            'lead_source': 'DLA Solicitation',
            'description': description,
            'close_date': dibbs_data.get('close_date'),
            'quantity': dibbs_data.get('quantity'),
            'iso': 'Yes' if dibbs_data.get('iso') == 'YES' else 'No',
            'sampling': 'Yes' if dibbs_data.get('sampling') == 'YES' else 'No',
            'fob': dibbs_data.get('fob'),
            'mfr': dibbs_data.get('manufacturer')
        }
        
        opportunity_id = crm_data.create_opportunity(opportunity_data)
        
        print(f"Auto-created opportunity {opportunity_id} for DLA solicitation {request_number}")
        return opportunity_id
    
    def auto_create_opportunity(self, rfq_id, account_id, contact_id, dibbs_data):
        """Auto-create opportunity for qualified RFQs"""
        
        # Check for duplicate opportunities if setting is enabled
        from pdf.dibbs_crm_processor import DIBBsCRMProcessor
        processor = DIBBsCRMProcessor()
        settings = processor.get_filter_settings()
        
        request_number = dibbs_data.get('request_number', 'Unknown')
        
        if settings.get('skip_duplicates', True):
            # Check if opportunity already exists for this RFQ number
            existing_opps = crm_data.execute_query(
                "SELECT id FROM opportunities WHERE name LIKE ? OR description LIKE ?",
                [f"%{request_number}%", f"%{request_number}%"]
            )
            if existing_opps:
                print(f"Skipping duplicate opportunity for RFQ {request_number}")
                return existing_opps[0]['id']  # Return existing opportunity ID
        
        # Get RFQ data for opportunity name
        product_desc = dibbs_data.get('product_description', '')
        nsn = dibbs_data.get('nsn', '')
        
        # Create opportunity name (just the request number)
        opp_name = f"{request_number}"
        
        # Calculate estimated amount (if quantity and we have pricing data)
        estimated_amount = self.calculate_estimated_amount(dibbs_data)
        
        # Set close date based on RFQ close date
        close_date = dibbs_data.get('close_date')
        if close_date:
            # Convert string date to proper format if needed
            if isinstance(close_date, str):
                try:
                    close_date = datetime.strptime(close_date, '%b %d, %Y').date()
                except:
                    close_date = date.today() + timedelta(days=30)
        else:
            close_date = date.today() + timedelta(days=30)
        
        opportunity_data = {
            'name': opp_name,
            'account_id': account_id,
            'contact_id': contact_id,
            'stage': 'Prospecting',
            'amount': estimated_amount,
            'probability': 25,  # Initial probability for new RFQs
            'close_date': close_date,
            'lead_source': 'DIBBs',
            'type': 'New Business',
            'description': f"NSN: {nsn}\nQuantity: {dibbs_data.get('quantity', '')}\nDelivery Days: {dibbs_data.get('delivery_days', '')}",
            'owner': 'System',
            'forecast_category': 'Pipeline'
        }
        
        return crm_data.create_opportunity(**opportunity_data)
    
    def calculate_estimated_amount(self, dibbs_data):
        """Calculate estimated opportunity amount based on historical data"""
        
        # Get payment history to estimate pricing
        payment_history = dibbs_data.get('payment_history', '')
        quantity = dibbs_data.get('quantity', 0)
        
        if not quantity:
            return None
        
        # Parse payment history for average unit price
        unit_prices = []
        if payment_history:
            # Extract prices from payment history using regex
            price_matches = re.findall(r'\$(\d+\.?\d*)', payment_history)
            unit_prices = [float(price) for price in price_matches]
        
        if unit_prices:
            avg_price = sum(unit_prices) / len(unit_prices)
            estimated_amount = avg_price * float(quantity)
            # Add 10% markup for our quote
            return round(estimated_amount * 1.1, 2)
        
        # Default estimation if no history available
        return None
    
    def auto_assign_tasks(self, rfq_id, opportunity_id, dibbs_data):
        """Auto-assign tasks based on RFQ type and qualification"""
        
        close_date = dibbs_data.get('close_date')
        request_number = dibbs_data.get('request_number', '')
        
        # Calculate due dates
        if close_date:
            if isinstance(close_date, str):
                try:
                    close_date_obj = datetime.strptime(close_date, '%b %d, %Y').date()
                except:
                    close_date_obj = date.today() + timedelta(days=30)
            else:
                close_date_obj = close_date
        else:
            close_date_obj = date.today() + timedelta(days=30)
        
        # Task 1: Review RFQ (due within 1 day)
        review_due = date.today() + timedelta(days=1)
        crm_data.create_task(
            subject=f"Review RFQ {request_number}",
            description=f"Review qualification and determine bid strategy for RFQ {request_number}",
            type='Research',
            priority='High',
            due_date=review_due,
            status='Not Started',
            related_to_type='RFQ',
            related_to_id=rfq_id,
            assigned_to='Sales Team'
        )
        
        # Task 2: Source products (due 3 days before close)
        sourcing_due = close_date_obj - timedelta(days=3)
        if sourcing_due > date.today():
            crm_data.create_task(
                subject=f"Source products for {request_number}",
                description=f"Find suppliers and get pricing for NSN {dibbs_data.get('nsn', '')}",
                type='Research',
                priority='Normal',
                due_date=sourcing_due,
                status='Not Started',
                related_to_type='RFQ',
                related_to_id=rfq_id,
                assigned_to='Procurement Team'
            )
        
        # Task 3: Prepare quote (due 1 day before close)
        quote_due = close_date_obj - timedelta(days=1)
        if quote_due > date.today():
            crm_data.create_task(
                subject=f"Prepare quote for {request_number}",
                description=f"Compile final quote and submit for RFQ {request_number}",
                type='Quote',
                priority='High',
                due_date=quote_due,
                status='Not Started',
                related_to_type='RFQ',
                related_to_id=rfq_id,
                assigned_to='Sales Team'
            )
        
        # If opportunity created, add follow-up task
        if opportunity_id:
            followup_due = close_date_obj + timedelta(days=7)
            crm_data.create_task(
                subject=f"Follow up on RFQ {request_number} results",
                description=f"Check award status and follow up with buyer",
                type='Follow-up',
                priority='Normal',
                due_date=followup_due,
                status='Not Started',
                related_to_type='Opportunity',
                related_to_id=opportunity_id,
                assigned_to='Sales Team'
            )
    
    def calculate_sales_metrics(self):
        """Calculate key sales metrics and KPIs"""
        
        metrics = {}
        
        # RFQ Metrics
        total_rfqs = len(crm_data.get_rfqs())
        qualified_rfqs = len(crm_data.get_rfqs({'status': 'Qualified'}))
        won_rfqs = len(crm_data.get_rfqs({'status': 'Won'}))
        
        metrics['rfq_qualification_rate'] = (qualified_rfqs / total_rfqs * 100) if total_rfqs > 0 else 0
        metrics['rfq_win_rate'] = (won_rfqs / qualified_rfqs * 100) if qualified_rfqs > 0 else 0
        
        # Opportunity Metrics
        opportunities = crm_data.get_opportunities()
        won_opps = [opp for opp in opportunities if opp['stage'] == 'Closed Won']
        
        metrics['total_opportunities'] = len(opportunities)
        
        # Safely handle potentially missing columns
        metrics['total_pipeline_value'] = sum((opp['amount'] if opp['amount'] is not None else 0) for opp in opportunities if opp['stage'] not in ['Closed Won', 'Closed Lost'])
        metrics['total_won_value'] = sum((opp['amount'] if opp['amount'] is not None else 0) for opp in won_opps)
        
        # Task Metrics
        overdue_tasks = crm_data.get_tasks({'due_date_range': 'overdue'})
        pending_tasks = crm_data.get_tasks({'status': 'Not Started'})
        
        metrics['overdue_tasks'] = len(overdue_tasks)
        metrics['pending_tasks'] = len(pending_tasks)
        
        return metrics
    
    def get_daily_dashboard_data(self):
        """Get data for daily dashboard view"""
        
        today = date.today()
        
        dashboard = {
            'today_tasks': crm_data.get_tasks({'due_date_range': 'today'}),
            'overdue_tasks': crm_data.get_tasks({'due_date_range': 'overdue'}),
            'this_week_tasks': crm_data.get_tasks({'due_date_range': 'this_week'}),
            'next_week_tasks': crm_data.get_tasks({'due_date_range': 'next_week'}),
            'new_rfqs': crm_data.get_rfqs({'status': 'New'}, limit=10),
            'closing_opportunities': crm_data.execute_query(
                "SELECT * FROM opportunities WHERE close_date <= ? AND stage NOT IN ('Closed Won', 'Closed Lost') ORDER BY close_date",
                [today + timedelta(days=7)]
            ),
            'recent_opportunities': crm_data.execute_query(
                "SELECT * FROM opportunities ORDER BY created_date DESC LIMIT 6"
            ),
            'recent_interactions': crm_data.get_interactions(limit=5),
            'metrics': self.calculate_sales_metrics()
        }
        
        return dashboard

# Initialize automation engine
crm_automation = CRMAutomation()
