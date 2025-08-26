"""
Comprehensive Email Automation Service
Implements: IMAP/POP3 monitoring, SMTP integration, scheduled processing, email parsing
"""

import imaplib
import poplib
import smtplib
import email
import email.mime.text
import email.mime.multipart
import email.mime.base
from email.header import decode_header
from email.utils import parseaddr
import sqlite3
import threading
import time
import schedule
import logging
from datetime import datetime, timedelta
import json
import re
import ssl
from typing import Dict, List, Optional, Tuple
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailAutomationService:
    """Complete email automation service with monitoring, sending, and processing"""
    
    def __init__(self):
        self.db_path = 'crm.db'
        self.config_path = 'email_config.json'
        self.running = False
        self.monitoring_thread = None
        self.setup_database()
        
    def setup_database(self):
        """Set up email automation tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Email accounts table for monitoring multiple accounts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT UNIQUE,
                    email_address TEXT,
                    account_type TEXT, -- 'IMAP', 'POP3', 'SMTP'
                    server_host TEXT,
                    server_port INTEGER,
                    use_ssl BOOLEAN DEFAULT 1,
                    username TEXT,
                    password TEXT, -- Encrypted
                    enabled BOOLEAN DEFAULT 1,
                    last_check TEXT,
                    check_frequency_minutes INTEGER DEFAULT 5,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Email monitoring log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_monitoring_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    check_time TEXT,
                    emails_found INTEGER DEFAULT 0,
                    emails_processed INTEGER DEFAULT 0,
                    errors TEXT,
                    processing_time_seconds REAL,
                    FOREIGN KEY (account_id) REFERENCES email_accounts (id)
                )
            """)
            
            # Email processing queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_processing_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    account_id INTEGER,
                    sender_email TEXT,
                    recipient_email TEXT,
                    subject TEXT,
                    content TEXT,
                    received_date TEXT,
                    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
                    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
                    processing_attempts INTEGER DEFAULT 0,
                    last_attempt TEXT,
                    related_opportunity_id INTEGER,
                    related_account_id INTEGER,
                    related_contact_id INTEGER,
                    created_interaction_id INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (account_id) REFERENCES email_accounts (id),
                    FOREIGN KEY (related_opportunity_id) REFERENCES opportunities (id),
                    FOREIGN KEY (related_account_id) REFERENCES accounts (id),
                    FOREIGN KEY (related_contact_id) REFERENCES contacts (id),
                    FOREIGN KEY (created_interaction_id) REFERENCES interactions (id)
                )
            """)
            
            # Outgoing email tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outgoing_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT,
                    recipient_email TEXT,
                    sender_email TEXT,
                    subject TEXT,
                    content TEXT,
                    sent_date TEXT,
                    delivery_status TEXT DEFAULT 'sent', -- sent, delivered, bounced, failed
                    tracking_id TEXT,
                    opportunity_id INTEGER,
                    account_id INTEGER,
                    contact_id INTEGER,
                    interaction_id INTEGER,
                    email_type TEXT, -- 'rfq', 'follow_up', 'quote_response', 'general'
                    FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (contact_id) REFERENCES contacts (id),
                    FOREIGN KEY (interaction_id) REFERENCES interactions (id)
                )
            """)
            
            # Email parsing rules
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_parsing_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT,
                    rule_type TEXT, -- 'subject_pattern', 'sender_pattern', 'content_pattern'
                    pattern TEXT, -- Regex pattern
                    action TEXT, -- 'create_interaction', 'link_opportunity', 'create_quote'
                    priority INTEGER DEFAULT 5,
                    enabled BOOLEAN DEFAULT 1,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Email automation database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up email automation database: {e}")
    
    def load_configuration(self) -> Dict:
        """Load email configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading email configuration: {e}")
            return {}
    
    def save_configuration(self, config: Dict):
        """Save email configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Email configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving email configuration: {e}")
    
    def add_email_account(self, account_name: str, email_address: str, account_type: str,
                         server_host: str, server_port: int, username: str, password: str,
                         use_ssl: bool = True, check_frequency: int = 5) -> bool:
        """Add email account for monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Encrypt password (basic implementation - use proper encryption in production)
            encrypted_password = self.encrypt_password(password)
            
            cursor.execute("""
                INSERT OR REPLACE INTO email_accounts 
                (account_name, email_address, account_type, server_host, server_port, 
                 use_ssl, username, password, check_frequency_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (account_name, email_address, account_type, server_host, server_port,
                  use_ssl, username, encrypted_password, check_frequency))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Email account {account_name} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding email account: {e}")
            return False
    
    def encrypt_password(self, password: str) -> str:
        """Basic password encryption (implement proper encryption in production)"""
        # This is a placeholder - implement proper encryption
        import base64
        return base64.b64encode(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Basic password decryption"""
        import base64
        return base64.b64decode(encrypted_password.encode()).decode()
    
    def start_monitoring(self):
        """Start email monitoring service"""
        if self.running:
            logger.warning("Email monitoring already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Schedule automated tasks
        schedule.every(5).minutes.do(self.check_all_accounts)
        schedule.every(1).hours.do(self.process_pending_emails)
        schedule.every(6).hours.do(self.cleanup_old_logs)
        schedule.every().day.at("08:00").do(self.send_daily_digest)
        
        logger.info("Email monitoring service started")
    
    def stop_monitoring(self):
        """Stop email monitoring service"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Email monitoring service stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def check_all_accounts(self):
        """Check all enabled email accounts for new messages"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, account_name, email_address, account_type, server_host, 
                       server_port, use_ssl, username, password, check_frequency_minutes, last_check
                FROM email_accounts 
                WHERE enabled = 1
            """)
            
            accounts = cursor.fetchall()
            conn.close()
            
            for account in accounts:
                account_id, name, email_addr, acc_type, host, port, use_ssl, username, encrypted_pass, freq, last_check = account
                
                # Check if it's time to check this account
                if last_check:
                    last_check_time = datetime.fromisoformat(last_check)
                    if datetime.now() - last_check_time < timedelta(minutes=freq):
                        continue
                
                logger.info(f"Checking email account: {name}")
                
                if acc_type.upper() == 'IMAP':
                    self.check_imap_account(account_id, host, port, username, 
                                          self.decrypt_password(encrypted_pass), use_ssl)
                elif acc_type.upper() == 'POP3':
                    self.check_pop3_account(account_id, host, port, username, 
                                          self.decrypt_password(encrypted_pass), use_ssl)
                
                # Update last check time
                self.update_account_last_check(account_id)
                
        except Exception as e:
            logger.error(f"Error checking email accounts: {e}")
    
    def check_imap_account(self, account_id: int, host: str, port: int, 
                          username: str, password: str, use_ssl: bool = True):
        """Check IMAP account for new emails"""
        start_time = time.time()
        emails_found = 0
        emails_processed = 0
        errors = []
        
        try:
            # Connect to IMAP server
            if use_ssl:
                mail = imaplib.IMAP4_SSL(host, port)
            else:
                mail = imaplib.IMAP4(host, port)
            
            mail.login(username, password)
            mail.select('INBOX')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == 'OK':
                email_ids = messages[0].split()
                emails_found = len(email_ids)
                
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            email_body = msg_data[0][1]
                            message = email.message_from_bytes(email_body)
                            
                            # Process email
                            if self.process_incoming_email(account_id, message):
                                emails_processed += 1
                                
                    except Exception as e:
                        error_msg = f"Error processing email {email_id}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            error_msg = f"Error connecting to IMAP server: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        finally:
            # Log monitoring session
            processing_time = time.time() - start_time
            self.log_monitoring_session(account_id, emails_found, emails_processed, 
                                      '; '.join(errors), processing_time)
    
    def check_pop3_account(self, account_id: int, host: str, port: int, 
                          username: str, password: str, use_ssl: bool = True):
        """Check POP3 account for new emails"""
        start_time = time.time()
        emails_found = 0
        emails_processed = 0
        errors = []
        
        try:
            # Connect to POP3 server
            if use_ssl:
                mail = poplib.POP3_SSL(host, port)
            else:
                mail = poplib.POP3(host, port)
            
            mail.user(username)
            mail.pass_(password)
            
            # Get number of messages
            num_messages = len(mail.list()[1])
            emails_found = num_messages
            
            for i in range(1, num_messages + 1):
                try:
                    # Retrieve email
                    raw_email = b"\n".join(mail.retr(i)[1])
                    message = email.message_from_bytes(raw_email)
                    
                    # Process email
                    if self.process_incoming_email(account_id, message):
                        emails_processed += 1
                        # Optionally delete processed emails
                        # mail.dele(i)
                        
                except Exception as e:
                    error_msg = f"Error processing email {i}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            mail.quit()
            
        except Exception as e:
            error_msg = f"Error connecting to POP3 server: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        finally:
            # Log monitoring session
            processing_time = time.time() - start_time
            self.log_monitoring_session(account_id, emails_found, emails_processed, 
                                      '; '.join(errors), processing_time)
    
    def process_incoming_email(self, account_id: int, message: email.message.Message) -> bool:
        """Process incoming email and create interaction"""
        try:
            # Extract email details
            sender = parseaddr(message.get('From', ''))[1]
            recipient = parseaddr(message.get('To', ''))[1]
            subject = self.decode_header_value(message.get('Subject', ''))
            message_id = message.get('Message-ID', '')
            date_received = message.get('Date', datetime.now().isoformat())
            
            # Extract email content
            content = self.extract_email_content(message)
            
            # Determine priority based on content and sender
            priority = self.calculate_email_priority(sender, subject, content)
            
            # Add to processing queue
            queue_id = self.add_to_processing_queue(
                message_id, account_id, sender, recipient, subject, content,
                date_received, priority
            )
            
            if queue_id:
                # Process immediately for high priority emails
                if priority <= 3:
                    self.process_queued_email(queue_id)
                
                logger.info(f"Email from {sender} added to processing queue")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing incoming email: {e}")
            return False
    
    def extract_email_content(self, message: email.message.Message) -> str:
        """Extract text content from email message"""
        content = ""
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        content += payload.decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html":
                    # Extract text from HTML if no plain text available
                    if not content:
                        payload = part.get_payload(decode=True)
                        if payload:
                            # Simple HTML to text conversion
                            html_content = payload.decode('utf-8', errors='ignore')
                            content += re.sub('<[^<]+?>', '', html_content)
        else:
            payload = message.get_payload(decode=True)
            if payload:
                content = payload.decode('utf-8', errors='ignore')
        
        return content.strip()
    
    def decode_header_value(self, value: str) -> str:
        """Decode email header value"""
        try:
            decoded_parts = decode_header(value)
            decoded_value = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_value += part.decode(encoding)
                    else:
                        decoded_value += part.decode('utf-8', errors='ignore')
                else:
                    decoded_value += part
            
            return decoded_value
        except:
            return value
    
    def calculate_email_priority(self, sender: str, subject: str, content: str) -> int:
        """Calculate email priority based on content analysis"""
        priority = 5  # Default medium priority
        
        # High priority indicators
        high_priority_words = ['urgent', 'asap', 'emergency', 'critical', 'deadline', 'quote', 'rfq', 'bid']
        if any(word.lower() in subject.lower() for word in high_priority_words):
            priority = 2
        
        # Low priority indicators
        low_priority_words = ['newsletter', 'unsubscribe', 'marketing', 'promotion']
        if any(word.lower() in subject.lower() for word in low_priority_words):
            priority = 8
        
        # Known vendor emails get medium-high priority
        if self.is_known_vendor_email(sender):
            priority = min(priority, 3)
        
        return priority
    
    def is_known_vendor_email(self, email_address: str) -> bool:
        """Check if email is from a known vendor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM accounts a
                JOIN contacts c ON a.id = c.account_id
                WHERE LOWER(c.email) = LOWER(?) OR LOWER(a.email) = LOWER(?)
            """, (email_address, email_address))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking known vendor: {e}")
            return False
    
    def add_to_processing_queue(self, message_id: str, account_id: int, sender: str, 
                               recipient: str, subject: str, content: str, 
                               received_date: str, priority: int) -> Optional[int]:
        """Add email to processing queue"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO email_processing_queue 
                (message_id, account_id, sender_email, recipient_email, subject, 
                 content, received_date, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (message_id, account_id, sender, recipient, subject, content, 
                  received_date, priority))
            
            queue_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return queue_id
            
        except Exception as e:
            logger.error(f"Error adding email to processing queue: {e}")
            return None
    
    def process_pending_emails(self):
        """Process pending emails in the queue"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get pending emails ordered by priority
            cursor.execute("""
                SELECT id FROM email_processing_queue 
                WHERE status = 'pending' AND processing_attempts < 3
                ORDER BY priority ASC, received_date ASC
                LIMIT 50
            """)
            
            queue_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for queue_id in queue_ids:
                self.process_queued_email(queue_id)
                
        except Exception as e:
            logger.error(f"Error processing pending emails: {e}")
    
    def process_queued_email(self, queue_id: int):
        """Process a specific queued email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update status to processing
            cursor.execute("""
                UPDATE email_processing_queue 
                SET status = 'processing', processing_attempts = processing_attempts + 1,
                    last_attempt = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), queue_id))
            
            # Get email details
            cursor.execute("""
                SELECT sender_email, recipient_email, subject, content, received_date
                FROM email_processing_queue 
                WHERE id = ?
            """, (queue_id,))
            
            email_data = cursor.fetchone()
            if not email_data:
                return
            
            sender, recipient, subject, content, received_date = email_data
            
            # Find related CRM records
            opportunity_id, account_id, contact_id = self.find_related_crm_records(sender, subject, content)
            
            # Create interaction
            interaction_id = self.create_email_interaction(
                sender, recipient, subject, content, received_date,
                opportunity_id, account_id, contact_id
            )
            
            # Update queue record
            if interaction_id:
                cursor.execute("""
                    UPDATE email_processing_queue 
                    SET status = 'completed', related_opportunity_id = ?, 
                        related_account_id = ?, related_contact_id = ?, 
                        created_interaction_id = ?
                    WHERE id = ?
                """, (opportunity_id, account_id, contact_id, interaction_id, queue_id))
                
                # Process email response if it's a vendor quote
                if self.is_quote_response_email(subject, content):
                    self.process_quote_response_email(sender, subject, content, opportunity_id, account_id)
            else:
                cursor.execute("""
                    UPDATE email_processing_queue 
                    SET status = 'failed', error_message = 'Failed to create interaction'
                    WHERE id = ?
                """, (queue_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Processed queued email {queue_id}")
            
        except Exception as e:
            error_msg = f"Error processing queued email {queue_id}: {e}"
            logger.error(error_msg)
            
            # Update queue with error
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE email_processing_queue 
                    SET status = 'failed', error_message = ?
                    WHERE id = ?
                """, (error_msg, queue_id))
                conn.commit()
                conn.close()
            except:
                pass
    
    def find_related_crm_records(self, sender_email: str, subject: str, content: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Find related opportunity, account, and contact based on email content"""
        opportunity_id = None
        account_id = None
        contact_id = None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find contact by email
            cursor.execute("""
                SELECT id, account_id FROM contacts 
                WHERE LOWER(email) = LOWER(?)
            """, (sender_email,))
            
            contact_result = cursor.fetchone()
            if contact_result:
                contact_id, account_id = contact_result
            
            # If no contact, try to find account by email
            if not account_id:
                cursor.execute("""
                    SELECT id FROM accounts 
                    WHERE LOWER(email) = LOWER(?)
                """, (sender_email,))
                
                account_result = cursor.fetchone()
                if account_result:
                    account_id = account_result[0]
            
            # Try to find opportunity by keywords in subject or content
            opportunity_keywords = re.findall(r'\b(?:RFQ|rfq|opportunity|quote|bid)\s*#?(\w+)', subject + ' ' + content, re.IGNORECASE)
            
            if opportunity_keywords and account_id:
                for keyword in opportunity_keywords:
                    cursor.execute("""
                        SELECT id FROM opportunities 
                        WHERE account_id = ? AND (
                            LOWER(name) LIKE LOWER(?) OR 
                            LOWER(description) LIKE LOWER(?) OR
                            LOWER(notes) LIKE LOWER(?)
                        )
                        ORDER BY created_date DESC
                        LIMIT 1
                    """, (account_id, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                    
                    opp_result = cursor.fetchone()
                    if opp_result:
                        opportunity_id = opp_result[0]
                        break
            
            # If still no opportunity but we have account, get most recent open opportunity
            if not opportunity_id and account_id:
                cursor.execute("""
                    SELECT id FROM opportunities 
                    WHERE account_id = ? AND stage NOT IN ('Won', 'Lost', 'Closed')
                    ORDER BY created_date DESC
                    LIMIT 1
                """, (account_id,))
                
                opp_result = cursor.fetchone()
                if opp_result:
                    opportunity_id = opp_result[0]
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error finding related CRM records: {e}")
        
        return opportunity_id, account_id, contact_id
    
    def create_email_interaction(self, sender: str, recipient: str, subject: str, 
                               content: str, received_date: str, opportunity_id: Optional[int],
                               account_id: Optional[int], contact_id: Optional[int]) -> Optional[int]:
        """Create interaction record for received email"""
        try:
            from crm_data import crm_data
            
            interaction_data = {
                'type': 'Email',
                'direction': 'Received',
                'subject': f"Email: {subject}",
                'message': f"""Email received from: {sender}
To: {recipient}
Date: {received_date}
Subject: {subject}

Content:
{content[:1000]}{'...' if len(content) > 1000 else ''}""",
                'interaction_date': received_date,
                'account_id': account_id,
                'contact_id': contact_id,
                'opportunity_id': opportunity_id,
                'contact_email': sender,
                'status': 'Completed',
                'created_by': 'Email Automation',
                'created_date': datetime.now().isoformat()
            }
            
            interaction_id = crm_data.create_interaction(**interaction_data)
            logger.info(f"Created interaction {interaction_id} for email from {sender}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Error creating email interaction: {e}")
            return None
    
    def is_quote_response_email(self, subject: str, content: str) -> bool:
        """Check if email is a quote response"""
        quote_indicators = [
            'quote', 'pricing', 'price', 'cost', 'proposal', 'bid', 'estimate',
            'lead time', 'delivery', 'availability', 'stock'
        ]
        
        text_to_check = (subject + ' ' + content).lower()
        return any(indicator in text_to_check for indicator in quote_indicators)
    
    def process_quote_response_email(self, sender: str, subject: str, content: str,
                                   opportunity_id: Optional[int], account_id: Optional[int]):
        """Process email as a quote response"""
        try:
            from enhanced_email_response_processor import EnhancedEmailResponseProcessor
            
            processor = EnhancedEmailResponseProcessor()
            
            email_data = {
                'sender': sender,
                'subject': subject,
                'content': content,
                'received_date': datetime.now().isoformat()
            }
            
            if opportunity_id and account_id:
                # Use the existing email response processor
                result = processor.process_complete_email_response(email_data)
                
                if result.get('success'):
                    logger.info(f"Processed quote response email from {sender}")
                else:
                    logger.warning(f"Failed to process quote response email: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"Error processing quote response email: {e}")
    
    def send_email_smtp(self, to_email: str, subject: str, content: str, 
                       opportunity_id: Optional[int] = None, account_id: Optional[int] = None,
                       contact_id: Optional[int] = None, email_type: str = 'general') -> bool:
        """Send email via SMTP and track it"""
        try:
            config = self.load_configuration()
            smtp_config = config.get('smtp_configuration', {})
            
            if not smtp_config.get('enabled'):
                logger.warning("SMTP not enabled")
                return False
            
            # Create email message
            msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = f"{smtp_config.get('from_name', 'CRM')} <{smtp_config.get('from_email', smtp_config.get('username'))}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Reply-To'] = smtp_config.get('reply_to_email', smtp_config.get('username'))
            
            # Add content
            msg.attach(email.mime.text.MIMEText(content, 'html' if '<html>' in content.lower() else 'plain'))
            
            # Connect to SMTP server
            if smtp_config.get('use_tls', True):
                server = smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 587))
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 25))
            
            # Login and send
            server.login(smtp_config['username'], smtp_config['password'])
            text = msg.as_string()
            server.sendmail(smtp_config['username'], to_email, text)
            server.quit()
            
            # Track outgoing email
            message_id = msg['Message-ID']
            self.track_outgoing_email(
                message_id, to_email, smtp_config['username'], subject, content,
                opportunity_id, account_id, contact_id, email_type
            )
            
            # Create outgoing interaction
            self.create_outgoing_email_interaction(
                to_email, subject, content, opportunity_id, account_id, contact_id
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def track_outgoing_email(self, message_id: str, recipient: str, sender: str,
                           subject: str, content: str, opportunity_id: Optional[int],
                           account_id: Optional[int], contact_id: Optional[int],
                           email_type: str):
        """Track outgoing email in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO outgoing_emails 
                (message_id, recipient_email, sender_email, subject, content,
                 sent_date, opportunity_id, account_id, contact_id, email_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (message_id, recipient, sender, subject, content,
                  datetime.now().isoformat(), opportunity_id, account_id, 
                  contact_id, email_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking outgoing email: {e}")
    
    def create_outgoing_email_interaction(self, recipient: str, subject: str, content: str,
                                        opportunity_id: Optional[int], account_id: Optional[int],
                                        contact_id: Optional[int]) -> Optional[int]:
        """Create interaction record for sent email"""
        try:
            from crm_data import crm_data
            
            interaction_data = {
                'type': 'Email',
                'direction': 'Sent',
                'subject': f"Email Sent: {subject}",
                'message': f"""Email sent to: {recipient}
Subject: {subject}
Sent: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Content:
{content[:1000]}{'...' if len(content) > 1000 else ''}""",
                'interaction_date': datetime.now().date().isoformat(),
                'account_id': account_id,
                'contact_id': contact_id,
                'opportunity_id': opportunity_id,
                'contact_email': recipient,
                'status': 'Completed',
                'created_by': 'Email Automation',
                'created_date': datetime.now().isoformat()
            }
            
            interaction_id = crm_data.create_interaction(**interaction_data)
            logger.info(f"Created interaction {interaction_id} for sent email to {recipient}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Error creating outgoing email interaction: {e}")
            return None
    
    def update_account_last_check(self, account_id: int):
        """Update last check timestamp for email account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE email_accounts 
                SET last_check = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), account_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating account last check: {e}")
    
    def log_monitoring_session(self, account_id: int, emails_found: int, 
                             emails_processed: int, errors: str, processing_time: float):
        """Log email monitoring session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_monitoring_log 
                (account_id, check_time, emails_found, emails_processed, 
                 errors, processing_time_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_id, datetime.now().isoformat(), emails_found,
                  emails_processed, errors, processing_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging monitoring session: {e}")
    
    def cleanup_old_logs(self):
        """Clean up old monitoring logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete logs older than 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor.execute("""
                DELETE FROM email_monitoring_log 
                WHERE check_time < ?
            """, (cutoff_date,))
            
            # Delete completed queue items older than 7 days
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor.execute("""
                DELETE FROM email_processing_queue 
                WHERE status = 'completed' AND last_attempt < ?
            """, (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info("Old email logs cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def send_daily_digest(self):
        """Send daily email digest"""
        try:
            config = self.load_configuration()
            if not config.get('notification_settings', {}).get('send_daily_digest', False):
                return
            
            # Get daily statistics
            stats = self.get_daily_email_statistics()
            
            # Create digest content
            digest_content = f"""
Daily Email Automation Report - {datetime.now().strftime('%Y-%m-%d')}

Summary:
- Emails Received: {stats['emails_received']}
- Emails Processed: {stats['emails_processed']}
- Interactions Created: {stats['interactions_created']}
- Quote Responses: {stats['quote_responses']}
- Processing Errors: {stats['processing_errors']}

Recent Activity:
{self.format_recent_activity(stats['recent_activity'])}

System Status: {'✅ Normal' if stats['processing_errors'] < 5 else '⚠️ Issues Detected'}
"""
            
            notification_email = config.get('notification_settings', {}).get('notification_email')
            if notification_email:
                self.send_email_smtp(
                    notification_email,
                    f"Daily Email Automation Digest - {datetime.now().strftime('%Y-%m-%d')}",
                    digest_content,
                    email_type='digest'
                )
            
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")
    
    def get_daily_email_statistics(self) -> Dict:
        """Get daily email processing statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            
            # Count emails received today
            cursor.execute("""
                SELECT COUNT(*) FROM email_processing_queue 
                WHERE DATE(received_date) = ?
            """, (today,))
            emails_received = cursor.fetchone()[0]
            
            # Count emails processed today
            cursor.execute("""
                SELECT COUNT(*) FROM email_processing_queue 
                WHERE DATE(last_attempt) = ? AND status = 'completed'
            """, (today,))
            emails_processed = cursor.fetchone()[0]
            
            # Count interactions created today
            cursor.execute("""
                SELECT COUNT(*) FROM email_processing_queue 
                WHERE DATE(last_attempt) = ? AND created_interaction_id IS NOT NULL
            """, (today,))
            interactions_created = cursor.fetchone()[0]
            
            # Count quote responses
            cursor.execute("""
                SELECT COUNT(*) FROM email_processing_queue 
                WHERE DATE(received_date) = ? AND (
                    LOWER(subject) LIKE '%quote%' OR 
                    LOWER(subject) LIKE '%price%' OR
                    LOWER(content) LIKE '%quote%'
                )
            """, (today,))
            quote_responses = cursor.fetchone()[0]
            
            # Count processing errors
            cursor.execute("""
                SELECT COUNT(*) FROM email_processing_queue 
                WHERE DATE(last_attempt) = ? AND status = 'failed'
            """, (today,))
            processing_errors = cursor.fetchone()[0]
            
            # Get recent activity
            cursor.execute("""
                SELECT sender_email, subject, status, last_attempt
                FROM email_processing_queue 
                WHERE DATE(received_date) = ?
                ORDER BY last_attempt DESC
                LIMIT 10
            """, (today,))
            recent_activity = cursor.fetchall()
            
            conn.close()
            
            return {
                'emails_received': emails_received,
                'emails_processed': emails_processed,
                'interactions_created': interactions_created,
                'quote_responses': quote_responses,
                'processing_errors': processing_errors,
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting daily statistics: {e}")
            return {
                'emails_received': 0,
                'emails_processed': 0,
                'interactions_created': 0,
                'quote_responses': 0,
                'processing_errors': 0,
                'recent_activity': []
            }
    
    def format_recent_activity(self, activity_list: List) -> str:
        """Format recent activity for digest"""
        if not activity_list:
            return "No recent activity"
        
        formatted = []
        for sender, subject, status, timestamp in activity_list:
            status_icon = {'completed': '✅', 'failed': '❌', 'pending': '⏳'}.get(status, '❓')
            formatted.append(f"{status_icon} {sender}: {subject[:50]}{'...' if len(subject) > 50 else ''}")
        
        return '\n'.join(formatted)

# Global service instance
email_service = EmailAutomationService()

def start_email_automation():
    """Start the email automation service"""
    email_service.start_monitoring()

def stop_email_automation():
    """Stop the email automation service"""
    email_service.stop_monitoring()

if __name__ == "__main__":
    # Test configuration
    print("🚀 Starting Email Automation Service...")
    
    # Example: Add email account
    # email_service.add_email_account(
    #     "Main Account",
    #     "your-email@domain.com",
    #     "IMAP",
    #     "imap.gmail.com",
    #     993,
    #     "your-email@domain.com",
    #     "your-password",
    #     True,
    #     5
    # )
    
    # Start monitoring
    email_service.start_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping Email Automation Service...")
        email_service.stop_monitoring()
