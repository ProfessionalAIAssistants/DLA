"""
Email Settings Management Utility
Provides functions for managing email configuration and validation
"""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailSettingsManager:
    """Manages email configuration settings"""
    
    def __init__(self, config_path: str = 'email_config.json'):
        self.config_path = config_path
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default email configuration"""
        return {
            "smtp_configuration": {
                "enabled": False,
                "host": "",
                "port": 587,
                "username": "",
                "password": "",
                "use_tls": True,
                "timeout": 30,
                "from_name": "CDE Prosperity DLA Team",
                "from_email": "",
                "reply_to_email": ""
            },
            "rfq_automation": {
                "enabled": False,
                "require_manual_review": True,
                "auto_send_approved": False,
                "default_priority": "Normal",
                "max_daily_sends": 50,
                "business_hours_only": True,
                "business_start_hour": 8,
                "business_end_hour": 17,
                "weekend_sending": False,
                "quote_deadline_days": 10,
                "follow_up_delay_days": 3,
                "max_follow_ups": 2
            },
            "email_tracking": {
                "enabled": True,
                "delivery_receipts": True,
                "read_receipts": False,
                "response_monitoring": True,
                "auto_parse_responses": True,
                "log_all_interactions": True
            },
            "response_processing": {
                "enabled": True,
                "auto_create_quotes": True,
                "require_quote_review": True,
                "parse_pdf_attachments": True,
                "extract_pricing": True,
                "create_follow_up_tasks": True,
                "notify_on_response": True
            },
            "workflow_automation": {
                "auto_create_opportunities": True,
                "auto_assign_tasks": False,
                "send_confirmation_emails": True,
                "send_daily_digest": False,
                "alert_on_urgent_quotes": True,
                "auto_escalate_overdue": True,
                "escalation_delay_hours": 24
            },
            "notification_settings": {
                "email_notifications": True,
                "notification_email": "",
                "notify_on_rfq_sent": True,
                "notify_on_response_received": True,
                "notify_on_quote_deadline": True,
                "daily_summary_time": "17:00",
                "weekly_report_day": "Friday"
            },
            "email_templates": {
                "use_custom_templates": True,
                "signature_template": "\n\nBest regards,\n{sender_name}\nCDE Prosperity DLA Team\n{company_phone}\n{company_email}",
                "auto_include_company_logo": False,
                "template_language": "English"
            },
            "security_settings": {
                "encrypt_stored_passwords": True,
                "require_authentication": True,
                "session_timeout_minutes": 30,
                "log_email_access": True,
                "restrict_sending_domains": False,
                "allowed_domains": []
            },
            "advanced_settings": {
                "retry_failed_sends": True,
                "max_retry_attempts": 3,
                "retry_delay_minutes": 15,
                "batch_sending": False,
                "batch_size": 10,
                "rate_limit_per_hour": 100,
                "debug_mode": False,
                "log_level": "INFO"
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load email configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.default_config, config)
            else:
                logger.info(f"Config file {self.config_path} not found, using defaults")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"Error loading email config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save email configuration to file"""
        try:
            # Validate config before saving
            if not self.validate_config(config):
                logger.error("Invalid configuration provided")
                return False
            
            # Merge with existing config
            existing_config = self.load_config()
            merged_config = self._merge_configs(existing_config, config)
            
            with open(self.config_path, 'w') as f:
                json.dump(merged_config, f, indent=2)
            
            logger.info(f"Email configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving email config: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate email configuration"""
        try:
            # Check SMTP configuration if enabled
            smtp_config = config.get('smtp_configuration', {})
            if smtp_config.get('enabled', False):
                required_fields = ['host', 'username', 'from_email']
                for field in required_fields:
                    if not smtp_config.get(field):
                        logger.error(f"Missing required SMTP field: {field}")
                        return False
                
                # Validate port
                port = smtp_config.get('port', 587)
                if not isinstance(port, int) or port < 1 or port > 65535:
                    logger.error(f"Invalid SMTP port: {port}")
                    return False
            
            # Check RFQ automation settings
            rfq_config = config.get('rfq_automation', {})
            if rfq_config.get('enabled', False):
                # Validate numeric fields
                numeric_fields = ['max_daily_sends', 'quote_deadline_days', 'follow_up_delay_days', 
                                'business_start_hour', 'business_end_hour']
                for field in numeric_fields:
                    value = rfq_config.get(field)
                    if value is not None and not isinstance(value, int):
                        logger.error(f"Invalid numeric value for {field}: {value}")
                        return False
                
                # Validate business hours
                start_hour = rfq_config.get('business_start_hour', 8)
                end_hour = rfq_config.get('business_end_hour', 17)
                if start_hour >= end_hour:
                    logger.error(f"Invalid business hours: {start_hour} >= {end_hour}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False
    
    def _merge_configs(self, base_config: Dict[str, Any], update_config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries"""
        result = base_config.copy()
        
        for key, value in update_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration specifically"""
        config = self.load_config()
        return config.get('smtp_configuration', {})
    
    def get_rfq_automation_config(self) -> Dict[str, Any]:
        """Get RFQ automation configuration specifically"""
        config = self.load_config()
        return config.get('rfq_automation', {})
    
    def is_email_enabled(self) -> bool:
        """Check if email functionality is enabled"""
        smtp_config = self.get_smtp_config()
        return smtp_config.get('enabled', False) and bool(smtp_config.get('host'))
    
    def is_rfq_automation_enabled(self) -> bool:
        """Check if RFQ automation is enabled"""
        rfq_config = self.get_rfq_automation_config()
        return rfq_config.get('enabled', False) and self.is_email_enabled()
    
    def requires_manual_review(self) -> bool:
        """Check if manual review is required for RFQs"""
        rfq_config = self.get_rfq_automation_config()
        return rfq_config.get('require_manual_review', True)
    
    def export_config(self, file_path: str) -> bool:
        """Export current configuration to a file"""
        try:
            config = self.load_config()
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Import file not found: {file_path}")
                return False
            
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            if self.save_config(config):
                logger.info(f"Configuration imported from {file_path}")
                return True
            else:
                logger.error("Failed to save imported configuration")
                return False
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False

# Global instance for easy access
email_settings = EmailSettingsManager()

# Utility functions for backward compatibility
def load_email_config() -> Dict[str, Any]:
    """Load email configuration (compatibility function)"""
    return email_settings.load_config()

def save_email_config(config: Dict[str, Any]) -> bool:
    """Save email configuration (compatibility function)"""
    return email_settings.save_config(config)

def is_email_enabled() -> bool:
    """Check if email is enabled (compatibility function)"""
    return email_settings.is_email_enabled()

def requires_manual_review() -> bool:
    """Check if manual review is required (compatibility function)"""
    return email_settings.requires_manual_review()

if __name__ == "__main__":
    # Test the email settings manager
    manager = EmailSettingsManager()
    
    print("🔧 Testing Email Settings Manager")
    print(f"📧 Email enabled: {manager.is_email_enabled()}")
    print(f"🤖 RFQ automation enabled: {manager.is_rfq_automation_enabled()}")
    print(f"👀 Manual review required: {manager.requires_manual_review()}")
    
    # Load and display current config
    config = manager.load_config()
    print(f"📋 Current SMTP host: {config['smtp_configuration']['host']}")
    print(f"🏢 Business hours: {config['rfq_automation']['business_start_hour']}:00 - {config['rfq_automation']['business_end_hour']}:00")
    print("✅ Email Settings Manager test complete")
