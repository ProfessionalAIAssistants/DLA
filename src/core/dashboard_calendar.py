"""
Dashboard Calendar System
========================

Provides calendar data and events for the dashboard calendar widget.
Integrates with CRM data to show tasks, opportunities, projects, and interactions.
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import crm_data

# Create module reference for backward compatibility
crm_data = crm_data.crm_data

class DashboardCalendar:
    """Dashboard Calendar data provider"""
    
    def __init__(self):
        """Initialize the dashboard calendar"""
        pass
    
    def get_calendar_events(self, start_date=None, end_date=None):
        """
        Get calendar events for the specified date range
        Returns events in FullCalendar format
        """
        # Expand date range to show more historical and future events
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)  # Show 1 year back
        if not end_date:
            end_date = datetime.now() + timedelta(days=365)    # Show 1 year ahead
            
        events = []
        
        # Get tasks
        tasks = crm_data.get_tasks()
        for task in tasks:
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                    if start_date <= due_date <= end_date:
                        # Determine task status and color
                        is_overdue = due_date < datetime.now()
                        color = '#dc3545' if is_overdue else '#17a2b8'  # Red if overdue, blue otherwise
                        
                        events.append({
                            'id': f"task_{task['id']}",
                            'title': f"📋 {task['subject']}",
                            'start': due_date.isoformat(),
                            'color': color,
                            'className': 'task-event' + (' overdue' if is_overdue else ''),
                            'extendedProps': {
                                'type': 'task',
                                'taskId': task['id'],
                                'description': f"{task.get('priority', 'Medium')} priority - {task.get('status', 'Not Started')}",
                                'priority': task.get('priority', 'Medium').lower(),
                                'status': task.get('status', 'Not Started'),
                                'overdue': is_overdue,
                                'url': f"/tasks/{task['id']}"
                            }
                        })
                except (ValueError, TypeError):
                    continue
        
        # Get opportunities with close dates
        opportunities = crm_data.get_opportunities()
        for opp in opportunities:
            if opp.get('close_date'):
                try:
                    close_date = datetime.fromisoformat(opp['close_date'].replace('Z', '+00:00'))
                    if start_date <= close_date <= end_date:
                        # Color based on stage and state
                        stage = (opp.get('stage') or '').lower()
                        state = (opp.get('state') or '').lower()
                        
                        if 'won' in state or 'won' in stage:
                            color = '#28a745'  # Green for won
                        elif 'lost' in state or 'lost' in stage:
                            color = '#dc3545'  # Red for lost
                        elif 'no bid' in state:
                            color = '#6c757d'  # Gray for no bid
                        elif close_date < datetime.now():
                            color = '#ffc107'  # Yellow for past due
                        else:
                            color = '#fd7e14'  # Orange for active
                        
                        events.append({
                            'id': f"opportunity_{opp['id']}",
                            'title': f"💼 {opp['name']}",
                            'start': close_date.isoformat(),
                            'color': color,
                            'className': 'opportunity-event',
                            'extendedProps': {
                                'type': 'opportunity',
                                'opportunityId': opp['id'],
                                'stage': opp.get('stage', ''),
                                'value': opp.get('value', 0),
                                'description': f"{opp.get('stage', 'Unknown stage')} - ${opp.get('value', 0):,.2f}",
                                'url': f"/opportunity/{opp['id']}"
                            }
                        })
                except (ValueError, TypeError):
                    continue
        
        # Get projects with due dates
        projects = crm_data.get_projects()
        for project in projects:
            # Add project start dates
            if project.get('start_date'):
                try:
                    start_date_proj = datetime.fromisoformat(project['start_date'].replace('Z', '+00:00'))
                    if start_date <= start_date_proj <= end_date:
                        events.append({
                            'id': f"project_start_{project['id']}",
                            'title': f"🚀 {project['name']} (Start)",
                            'start': start_date_proj.isoformat(),
                            'color': '#28a745',  # Green for start
                            'className': 'project-start',
                            'extendedProps': {
                                'type': 'project',
                                'projectId': project['id'],
                                'eventType': 'start',
                                'description': f"Project start date",
                                'url': f"/project/{project['id']}"
                            }
                        })
                except (ValueError, TypeError):
                    continue
            
            # Add project due dates
            if project.get('due_date'):
                try:
                    due_date_proj = datetime.fromisoformat(project['due_date'].replace('Z', '+00:00'))
                    if start_date <= due_date_proj <= end_date:
                        is_overdue = due_date_proj < datetime.now()
                        color = '#dc3545' if is_overdue else '#fd7e14'  # Red if overdue, orange otherwise
                        
                        events.append({
                            'id': f"project_due_{project['id']}",
                            'title': f"📅 {project['name']} (Due)",
                            'start': due_date_proj.isoformat(),
                            'color': color,
                            'className': 'project-due' + (' overdue' if is_overdue else ''),
                            'extendedProps': {
                                'type': 'project',
                                'projectId': project['id'],
                                'eventType': 'due',
                                'description': f"Project due date{'- OVERDUE' if is_overdue else ''}",
                                'overdue': is_overdue,
                                'url': f"/project/{project['id']}"
                            }
                        })
                except (ValueError, TypeError):
                    continue
        
        # Get interactions (meetings, calls, etc.)
        interactions = crm_data.get_interactions()
        for interaction in interactions:
            if interaction.get('interaction_date'):
                try:
                    interaction_date = datetime.fromisoformat(interaction['interaction_date'].replace('Z', '+00:00'))
                    if start_date <= interaction_date <= end_date:
                        # Color based on interaction type
                        int_type = interaction.get('type', '').lower()
                        if 'meeting' in int_type:
                            color = '#6f42c1'  # Purple
                        elif 'call' in int_type:
                            color = '#20c997'  # Teal
                        else:
                            color = '#17a2b8'  # Blue
                        
                        events.append({
                            'id': f"interaction_{interaction['id']}",
                            'title': f"🤝 {interaction.get('type', 'Interaction')}",
                            'start': interaction_date.isoformat(),
                            'color': color,
                            'className': 'interaction',
                            'extendedProps': {
                                'type': 'interaction',
                                'interactionId': interaction['id'],
                                'interactionType': interaction.get('type', ''),
                                'notes': interaction.get('notes', '')
                            }
                        })
                except (ValueError, TypeError):
                    continue
        
        return events
    
    def get_upcoming_events(self, days=7):
        """Get upcoming events for the next N days"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        events = self.get_calendar_events(start_date, end_date)
        
        # Sort by date
        events.sort(key=lambda x: x['start'])
        
        # Transform to format expected by frontend
        upcoming_events = []
        for event in events:
            try:
                event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                upcoming_events.append({
                    'title': event['title'],
                    'date': event['start'],
                    'description': event.get('extendedProps', {}).get('description', 'No description'),
                    'priority': event.get('extendedProps', {}).get('priority', 'medium'),
                    'type': event.get('extendedProps', {}).get('type', 'event'),
                    'overdue': event.get('extendedProps', {}).get('overdue', False),
                    'url': event.get('extendedProps', {}).get('url', None)
                })
            except (ValueError, TypeError):
                continue
        
        return upcoming_events
    
    def get_overdue_events(self):
        """Get overdue tasks and projects"""
        now = datetime.now()
        overdue_events = []
        
        # Overdue tasks
        tasks = crm_data.get_tasks()
        for task in tasks:
            if task.get('due_date') and task.get('status', '').lower() != 'completed':
                try:
                    due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                    if due_date < now:
                        overdue_events.append({
                            'type': 'task',
                            'id': task['id'],
                            'title': task['subject'],
                            'due_date': due_date.isoformat(),
                            'days_overdue': (now - due_date).days
                        })
                except (ValueError, TypeError):
                    continue
        
        # Overdue projects
        projects = crm_data.get_projects()
        for project in projects:
            if project.get('due_date') and project.get('status', '').lower() not in ['completed', 'cancelled']:
                try:
                    due_date = datetime.fromisoformat(project['due_date'].replace('Z', '+00:00'))
                    if due_date < now:
                        overdue_events.append({
                            'type': 'project',
                            'id': project['id'],
                            'title': project['name'],
                            'due_date': due_date.isoformat(),
                            'days_overdue': (now - due_date).days
                        })
                except (ValueError, TypeError):
                    continue
        
        return overdue_events
    
    def get_calendar_summary(self):
        """Get calendar statistics and summary"""
        now = datetime.now()
        
        # Get tasks
        tasks = crm_data.get_tasks()
        task_stats = {
            'total': len(tasks),
            'completed': len([t for t in tasks if t.get('status', '').lower() == 'completed']),
            'overdue': 0,
            'due_today': 0,
            'due_this_week': 0
        }
        
        for task in tasks:
            if task.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(task['due_date'].replace('Z', '+00:00'))
                    if due_date.date() == now.date():
                        task_stats['due_today'] += 1
                    elif due_date.date() <= (now + timedelta(days=7)).date():
                        task_stats['due_this_week'] += 1
                    if due_date < now and task.get('status', '').lower() != 'completed':
                        task_stats['overdue'] += 1
                except (ValueError, TypeError):
                    continue
        
        # Get opportunities
        opportunities = crm_data.get_opportunities()
        opp_stats = {
            'total': len(opportunities),
            'closing_this_week': 0,
            'closing_this_month': 0
        }
        
        for opp in opportunities:
            if opp.get('close_date'):
                try:
                    close_date = datetime.fromisoformat(opp['close_date'].replace('Z', '+00:00'))
                    if close_date.date() <= (now + timedelta(days=7)).date():
                        opp_stats['closing_this_week'] += 1
                    if close_date.date() <= (now + timedelta(days=30)).date():
                        opp_stats['closing_this_month'] += 1
                except (ValueError, TypeError):
                    continue
        
        return {
            'tasks': task_stats,
            'opportunities': opp_stats,
            'last_updated': now.isoformat()
        }

# Create global instance
dashboard_calendar = DashboardCalendar()
