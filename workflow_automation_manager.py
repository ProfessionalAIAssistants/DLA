"""
Workflow Automation Manager
Manages automated workflow improvements and task creation
"""

import sqlite3
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class WorkflowAutomationManager:
    """Manages workflow automation improvements"""
    
    def __init__(self):
        self.db_path = 'crm.db'
        self.setup_workflow_automation()
    
    def setup_workflow_automation(self):
        """Set up workflow automation tables and triggers"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create workflow_automation_rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_automation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT UNIQUE,
                    trigger_event TEXT,
                    trigger_conditions TEXT,
                    actions TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_executed TEXT,
                    execution_count INTEGER DEFAULT 0
                )
            """)
            
            # Create workflow_execution_log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_execution_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER,
                    trigger_data TEXT,
                    execution_time TEXT,
                    success BOOLEAN,
                    actions_performed TEXT,
                    error_message TEXT,
                    FOREIGN KEY (rule_id) REFERENCES workflow_automation_rules(id)
                )
            """)
            
            # Create default automation rules
            self.create_default_automation_rules(cursor)
            
            conn.commit()
            conn.close()
            logger.info("Workflow automation setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up workflow automation: {e}")
    
    def create_default_automation_rules(self, cursor):
        """Create default workflow automation rules"""
        default_rules = [
            {
                'rule_name': 'Auto-create tasks when RFQ emails sent',
                'trigger_event': 'rfq_email_sent',
                'trigger_conditions': json.dumps({'email_status': 'sent'}),
                'actions': json.dumps([
                    {'action': 'create_task', 'type': 'follow_up', 'days_delay': 7},
                    {'action': 'update_opportunity_stage', 'stage': 'Quote Requested'}
                ])
            },
            {
                'rule_name': 'Auto-create review tasks when quotes received',
                'trigger_event': 'quote_received',
                'trigger_conditions': json.dumps({'quote_amount': '> 0'}),
                'actions': json.dumps([
                    {'action': 'create_task', 'type': 'review', 'priority': 'High', 'days_delay': 1},
                    {'action': 'update_opportunity_stage', 'stage': 'Quote Received'},
                    {'action': 'create_interaction', 'type': 'Quote Received'}
                ])
            },
            {
                'rule_name': 'Auto-create projects from won opportunities',
                'trigger_event': 'opportunity_won',
                'trigger_conditions': json.dumps({'state': 'Won'}),
                'actions': json.dumps([
                    {'action': 'create_project', 'status': 'Not Started'},
                    {'action': 'create_task', 'type': 'project_planning', 'priority': 'High'},
                    {'action': 'update_opportunity_stage', 'stage': 'Project Started'}
                ])
            },
            {
                'rule_name': 'Auto-follow-up overdue RFQs',
                'trigger_event': 'rfq_overdue',
                'trigger_conditions': json.dumps({'days_since_sent': '> 7', 'response_received': False}),
                'actions': json.dumps([
                    {'action': 'create_task', 'type': 'follow_up', 'priority': 'High'},
                    {'action': 'send_reminder_email'}
                ])
            }
        ]
        
        for rule in default_rules:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO workflow_automation_rules 
                    (rule_name, trigger_event, trigger_conditions, actions)
                    VALUES (?, ?, ?, ?)
                """, (rule['rule_name'], rule['trigger_event'], 
                     rule['trigger_conditions'], rule['actions']))
            except Exception as e:
                logger.error(f"Error creating default rule {rule['rule_name']}: {e}")
    
    def trigger_workflow_event(self, event_type: str, event_data: Dict) -> List[Dict]:
        """Trigger workflow automation based on event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find matching automation rules
            cursor.execute("""
                SELECT id, rule_name, trigger_conditions, actions
                FROM workflow_automation_rules 
                WHERE trigger_event = ? AND enabled = 1
            """, (event_type,))
            
            matching_rules = cursor.fetchall()
            execution_results = []
            
            for rule in matching_rules:
                rule_id, rule_name, conditions_json, actions_json = rule
                
                try:
                    # Check if conditions are met
                    conditions = json.loads(conditions_json)
                    if self.check_conditions(event_data, conditions):
                        # Execute actions
                        actions = json.loads(actions_json)
                        result = self.execute_workflow_actions(actions, event_data)
                        
                        # Log execution
                        self.log_workflow_execution(rule_id, event_data, result['success'], 
                                                  result['actions_performed'], result.get('error'))
                        
                        # Update rule execution count
                        cursor.execute("""
                            UPDATE workflow_automation_rules 
                            SET last_executed = ?, execution_count = execution_count + 1
                            WHERE id = ?
                        """, (datetime.now().isoformat(), rule_id))
                        
                        execution_results.append({
                            'rule_name': rule_name,
                            'executed': True,
                            'result': result
                        })
                    else:
                        execution_results.append({
                            'rule_name': rule_name,
                            'executed': False,
                            'reason': 'Conditions not met'
                        })
                        
                except Exception as e:
                    logger.error(f"Error executing rule {rule_name}: {e}")
                    execution_results.append({
                        'rule_name': rule_name,
                        'executed': False,
                        'error': str(e)
                    })
            
            conn.commit()
            conn.close()
            
            return execution_results
            
        except Exception as e:
            logger.error(f"Error triggering workflow event {event_type}: {e}")
            return []
    
    def check_conditions(self, event_data: Dict, conditions: Dict) -> bool:
        """Check if event data meets automation conditions"""
        try:
            for field, condition in conditions.items():
                if field not in event_data:
                    return False
                
                value = event_data[field]
                
                if isinstance(condition, str) and condition.startswith('>'):
                    threshold = float(condition[1:].strip())
                    if not (isinstance(value, (int, float)) and value > threshold):
                        return False
                elif isinstance(condition, str) and condition.startswith('<'):
                    threshold = float(condition[1:].strip())
                    if not (isinstance(value, (int, float)) and value < threshold):
                        return False
                elif value != condition:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking conditions: {e}")
            return False
    
    def execute_workflow_actions(self, actions: List[Dict], event_data: Dict) -> Dict:
        """Execute workflow actions"""
        try:
            from crm_data import crm_data
            from enhanced_email_automation import EnhancedEmailAutomation
            
            executed_actions = []
            enhanced_email = EnhancedEmailAutomation()
            
            for action in actions:
                action_type = action.get('action')
                
                try:
                    if action_type == 'create_task':
                        task_id = self.create_automated_task(action, event_data)
                        executed_actions.append(f"Created task {task_id}")
                        
                    elif action_type == 'update_opportunity_stage':
                        opportunity_id = event_data.get('opportunity_id')
                        if opportunity_id:
                            stage = action.get('stage')
                            success = enhanced_email.auto_update_opportunity_stage(opportunity_id, stage)
                            executed_actions.append(f"Updated opportunity {opportunity_id} stage to {stage}")
                    
                    elif action_type == 'create_project':
                        project_id = self.create_automated_project(action, event_data)
                        if project_id:
                            executed_actions.append(f"Created project {project_id}")
                    
                    elif action_type == 'create_interaction':
                        interaction_id = self.create_automated_interaction(action, event_data)
                        if interaction_id:
                            executed_actions.append(f"Created interaction {interaction_id}")
                    
                    elif action_type == 'send_reminder_email':
                        self.send_automated_reminder(action, event_data)
                        executed_actions.append("Scheduled reminder email")
                        
                except Exception as e:
                    logger.error(f"Error executing action {action_type}: {e}")
                    executed_actions.append(f"Failed: {action_type} - {str(e)}")
            
            return {
                'success': True,
                'actions_performed': executed_actions
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow actions: {e}")
            return {
                'success': False,
                'actions_performed': [],
                'error': str(e)
            }
    
    def create_automated_task(self, action: Dict, event_data: Dict) -> Optional[int]:
        """Create automated task based on action and event data"""
        try:
            from crm_data import crm_data
            
            task_type = action.get('type', 'General')
            priority = action.get('priority', 'Normal')
            days_delay = action.get('days_delay', 0)
            
            # Determine task details based on event and action type
            if task_type == 'follow_up':
                subject = f"Follow-up Required: {event_data.get('subject', 'RFQ Response')}"
                description = f"Follow-up required for RFQ email.\n\nDetails:\n{json.dumps(event_data, indent=2)}"
            elif task_type == 'review':
                subject = f"Review Quote Response: {event_data.get('vendor_name', 'Vendor')}"
                description = f"Quote response received - review required.\n\nQuote Amount: ${event_data.get('quote_amount', 0):,.2f}\nLead Time: {event_data.get('lead_time_days', 'TBD')} days"
            elif task_type == 'project_planning':
                subject = f"Project Planning: {event_data.get('opportunity_name', 'New Project')}"
                description = f"Begin project planning for won opportunity.\n\nOpportunity: {event_data.get('opportunity_name', '')}\nValue: ${event_data.get('amount', 0):,.2f}"
            else:
                subject = f"Automated Task: {task_type.title()}"
                description = f"Automated task created from workflow.\n\nEvent Data:\n{json.dumps(event_data, indent=2)}"
            
            due_date = (datetime.now().date() + timedelta(days=days_delay)).isoformat()
            
            task_data = {
                'subject': subject,
                'description': description,
                'type': task_type.title(),
                'priority': priority,
                'status': 'Not Started',
                'due_date': due_date,
                'related_to_type': event_data.get('related_to_type', 'Opportunity'),
                'related_to_id': event_data.get('opportunity_id'),
                'assigned_to': 'Sales Team'
            }
            
            task_id = crm_data.create_task(**task_data)
            logger.info(f"Created automated task {task_id}: {subject}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating automated task: {e}")
            return None
    
    def create_automated_project(self, action: Dict, event_data: Dict) -> Optional[int]:
        """Create automated project from won opportunity"""
        try:
            from crm_data import crm_data
            
            opportunity_id = event_data.get('opportunity_id')
            if not opportunity_id:
                return None
            
            opportunity = crm_data.get_opportunity_by_id(opportunity_id)
            if not opportunity:
                return None
            
            project_data = {
                'name': f"Project: {opportunity.get('name', 'Unknown')}",
                'summary': f"Project automatically created from won opportunity",
                'status': action.get('status', 'Not Started'),
                'priority': 'High',
                'start_date': date.today().isoformat(),
                'project_manager': 'TBD',
                'description': f"Project created from opportunity: {opportunity.get('name', '')}\n\nOriginal amount: ${opportunity.get('amount', 0):,.2f}"
            }
            
            # Calculate budget from opportunity
            if opportunity.get('bid_price') and opportunity.get('quantity'):
                project_data['budget'] = opportunity['bid_price'] * opportunity['quantity']
            
            project_id = crm_data.create_project(**project_data)
            
            if project_id:
                # Link opportunity to project
                crm_data.update_opportunity(opportunity_id, project_id=project_id)
                logger.info(f"Created automated project {project_id} from opportunity {opportunity_id}")
            
            return project_id
            
        except Exception as e:
            logger.error(f"Error creating automated project: {e}")
            return None
    
    def create_automated_interaction(self, action: Dict, event_data: Dict) -> Optional[int]:
        """Create automated interaction record"""
        try:
            from crm_data import crm_data
            
            interaction_type = action.get('type', 'System Update')
            
            interaction_data = {
                'type': interaction_type,
                'subject': f"Automated: {interaction_type}",
                'description': f"Automated interaction created from workflow.\n\nEvent: {event_data.get('event_type', 'Unknown')}\nDetails: {json.dumps(event_data, indent=2)}",
                'interaction_date': datetime.now().date().isoformat(),
                'account_id': event_data.get('vendor_account_id'),
                'contact_id': event_data.get('contact_id'),
                'opportunity_id': event_data.get('opportunity_id'),
                'direction': 'System',
                'status': 'Completed',
                'follow_up_required': False
            }
            
            interaction_id = crm_data.create_interaction(**interaction_data)
            logger.info(f"Created automated interaction {interaction_id}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Error creating automated interaction: {e}")
            return None
    
    def send_automated_reminder(self, action: Dict, event_data: Dict):
        """Schedule automated reminder"""
        try:
            from enhanced_email_automation import EnhancedEmailAutomation
            enhanced_email = EnhancedEmailAutomation()
            
            # Schedule follow-up reminder task instead of actual email
            vendor_email_id = event_data.get('vendor_email_id')
            if vendor_email_id:
                enhanced_email.schedule_follow_up_reminder(vendor_email_id, days=1)
                logger.info(f"Scheduled automated reminder for email {vendor_email_id}")
            
        except Exception as e:
            logger.error(f"Error sending automated reminder: {e}")
    
    def log_workflow_execution(self, rule_id: int, trigger_data: Dict, success: bool, actions: List[str], error: str = None):
        """Log workflow execution for tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_execution_log 
                (rule_id, trigger_data, execution_time, success, actions_performed, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule_id, json.dumps(trigger_data), datetime.now().isoformat(), 
                 success, json.dumps(actions), error))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging workflow execution: {e}")
    
    def get_workflow_statistics(self) -> Dict:
        """Get workflow automation statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get rule statistics
            cursor.execute("""
                SELECT rule_name, execution_count, last_executed, enabled
                FROM workflow_automation_rules
                ORDER BY execution_count DESC
            """)
            rules = cursor.fetchall()
            
            # Get recent executions
            cursor.execute("""
                SELECT r.rule_name, l.execution_time, l.success, l.actions_performed
                FROM workflow_execution_log l
                JOIN workflow_automation_rules r ON l.rule_id = r.id
                ORDER BY l.execution_time DESC
                LIMIT 10
            """)
            recent_executions = cursor.fetchall()
            
            # Get success rate
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
                FROM workflow_execution_log 
                WHERE execution_time >= date('now', '-30 days')
            """)
            stats = cursor.fetchone()
            
            conn.close()
            
            total_executions = stats[0] if stats else 0
            successful_executions = stats[1] if stats else 0
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            return {
                'total_rules': len(rules),
                'active_rules': len([r for r in rules if r[3]]),  # enabled rules
                'total_executions_30d': total_executions,
                'success_rate': round(success_rate, 2),
                'rules': [
                    {
                        'name': r[0],
                        'executions': r[1],
                        'last_executed': r[2],
                        'enabled': bool(r[3])
                    } for r in rules
                ],
                'recent_executions': [
                    {
                        'rule_name': e[0],
                        'execution_time': e[1],
                        'success': bool(e[2]),
                        'actions': json.loads(e[3]) if e[3] else []
                    } for e in recent_executions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {e}")
            return {'error': str(e)}

# Integration functions for existing workflow
def trigger_rfq_email_sent_workflow(vendor_email_id: int, opportunity_id: int):
    """Trigger workflow when RFQ email is sent"""
    try:
        workflow_manager = WorkflowAutomationManager()
        
        event_data = {
            'vendor_email_id': vendor_email_id,
            'opportunity_id': opportunity_id,
            'event_type': 'rfq_email_sent',
            'timestamp': datetime.now().isoformat()
        }
        
        results = workflow_manager.trigger_workflow_event('rfq_email_sent', event_data)
        logger.info(f"Triggered RFQ email sent workflow for email {vendor_email_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error triggering RFQ email sent workflow: {e}")
        return []

def trigger_quote_received_workflow(opportunity_id: int, vendor_account_id: int, quote_data: Dict):
    """Trigger workflow when quote is received"""
    try:
        workflow_manager = WorkflowAutomationManager()
        
        event_data = {
            'opportunity_id': opportunity_id,
            'vendor_account_id': vendor_account_id,
            'quote_amount': quote_data.get('quote_amount', 0),
            'lead_time_days': quote_data.get('lead_time_days'),
            'availability': quote_data.get('availability'),
            'event_type': 'quote_received',
            'timestamp': datetime.now().isoformat()
        }
        
        results = workflow_manager.trigger_workflow_event('quote_received', event_data)
        logger.info(f"Triggered quote received workflow for opportunity {opportunity_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error triggering quote received workflow: {e}")
        return []

def trigger_opportunity_won_workflow(opportunity_id: int):
    """Trigger workflow when opportunity is won"""
    try:
        from crm_data import crm_data
        workflow_manager = WorkflowAutomationManager()
        
        opportunity = crm_data.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            return []
        
        event_data = {
            'opportunity_id': opportunity_id,
            'opportunity_name': opportunity.get('name'),
            'amount': opportunity.get('amount', 0),
            'state': 'Won',
            'event_type': 'opportunity_won',
            'timestamp': datetime.now().isoformat()
        }
        
        results = workflow_manager.trigger_workflow_event('opportunity_won', event_data)
        logger.info(f"Triggered opportunity won workflow for opportunity {opportunity_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error triggering opportunity won workflow: {e}")
        return []

if __name__ == "__main__":
    # Initialize workflow automation
    workflow_manager = WorkflowAutomationManager()
    
    # Get statistics
    stats = workflow_manager.get_workflow_statistics()
    print("Workflow Automation Statistics:", json.dumps(stats, indent=2))
    
    print("Workflow automation manager initialized successfully")
