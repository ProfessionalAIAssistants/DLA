# CRM Business Logic and Automation Engine
# Handles automation rules, calculations, and business logic

from crm_data import crm_data
from datetime import datetime, date, timedelta
import re

class CRMAutomation:
    
    def __init__(self):
        self.automation_rules = {
            'rfq_qualification': self.qualify_rfq,
            'opportunity_creation': self.auto_create_opportunity,
            'task_assignment': self.auto_assign_tasks,
            'account_matching': self.match_or_create_account,
            'contact_matching': self.match_or_create_contact
        }
    
    def process_dibbs_rfq(self, dibbs_data):
        """Main automation workflow for processing DIBBs RFQ data"""
        
        # 1. Create RFQ record
        rfq_id = crm_data.create_rfq_from_dibbs(dibbs_data)
        
        # 2. Match or create account (government agency)
        account_id = self.match_or_create_account(dibbs_data)
        
        # 3. Match or create contact (buyer)
        contact_id = self.match_or_create_contact(dibbs_data, account_id)
        
        # 4. Update RFQ with account and contact links
        crm_data.execute_update(
            "UPDATE rfqs SET account_id = ?, contact_id = ? WHERE id = ?",
            [account_id, contact_id, rfq_id]
        )
        
        # 5. Check qualification criteria
        is_qualified = self.qualify_rfq(dibbs_data)
        
        # 6. Auto-create opportunity if qualified
        opportunity_id = None
        if is_qualified and not dibbs_data.get('skipped'):
            opportunity_id = self.auto_create_opportunity(rfq_id, account_id, contact_id, dibbs_data)
            crm_data.update_rfq_status(rfq_id, 'Qualified', opportunity_id)
        
        # 7. Auto-assign tasks
        self.auto_assign_tasks(rfq_id, opportunity_id, dibbs_data)
        
        return {
            'rfq_id': rfq_id,
            'account_id': account_id,
            'contact_id': contact_id,
            'opportunity_id': opportunity_id,
            'qualified': is_qualified
        }
    
    def qualify_rfq(self, dibbs_data):
        """Determine if RFQ meets qualification criteria"""
        
        # Configuration-based qualification rules
        qualification_rules = {
            'min_delivery_days': 120,
            'required_iso': 'NO',
            'required_sampling': 'NO',
            'required_inspection_point': 'DESTINATION',
            'preferred_manufacturers': ['Parker', 'Monkey Monkey'],
            'excluded_fsc': [],  # Add FSCs to exclude if needed
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
        
        return True
    
    def match_or_create_account(self, dibbs_data):
        """Match existing account or create new one based on buyer office"""
        
        office = dibbs_data.get('office', '')
        division = dibbs_data.get('division', '')
        
        if not office:
            office = "Unknown Government Agency"
        
        # Try to find existing account
        existing_accounts = crm_data.get_accounts({'name': office})
        
        if existing_accounts:
            return existing_accounts[0]['id']
        
        # Create new account
        account_data = {
            'name': office,
            'account_type': 'Customer',
            'account_source': 'DIBBs',
            'industry': 'Government',
            'billing_address': dibbs_data.get('address', ''),
            'description': f"Division: {division}",
            'owner': 'System'
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
    
    def auto_create_opportunity(self, rfq_id, account_id, contact_id, dibbs_data):
        """Auto-create opportunity for qualified RFQs"""
        
        # Get RFQ data for opportunity name
        request_number = dibbs_data.get('request_number', 'Unknown')
        product_desc = dibbs_data.get('product_description', '')
        nsn = dibbs_data.get('nsn', '')
        
        # Create opportunity name
        opp_name = f"RFQ {request_number} - {product_desc[:50]}"
        
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
        overdue_tasks = crm_data.get_tasks({'overdue': True})
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
