# Local CRM Database Schema
# Self-contained CRM system for DIBBs processing

import sqlite3
from datetime import datetime
from pathlib import Path

class CRMDatabase:
    def __init__(self, db_path="crm.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self.create_tables()
    
    def create_tables(self):
        """Create all CRM tables based on Notion structure"""
        
        # Accounts Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT CHECK(type IN ('Competitor', 'Prospect Customer', 'Customer', 'Former Customer', 'Prospect Vendor', 'Vendor', 'QPL')),
                summary TEXT,
                detail TEXT,
                website TEXT,
                email TEXT,
                location TEXT,
                linkedin TEXT,
                parent_co TEXT,
                cage TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image TEXT,
                video TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Contacts Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
                title TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                mobile TEXT,
                account_id INTEGER,
                department TEXT,
                reports_to INTEGER,
                lead_source TEXT,
                address TEXT,
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (reports_to) REFERENCES contacts (id)
            )
        ''')
        
        # Products Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_code TEXT UNIQUE,
                nsn TEXT,
                fsc TEXT,
                description TEXT,
                category TEXT,
                family TEXT,
                unit_price REAL,
                cost_price REAL,
                list_price REAL,
                manufacturer TEXT,
                part_number TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Opportunities Table  
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_id INTEGER,
                contact_id INTEGER,
                stage TEXT CHECK(stage IN ('Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost')),
                amount REAL,
                probability INTEGER CHECK(probability >= 0 AND probability <= 100),
                close_date DATE,
                lead_source TEXT,
                next_step TEXT,
                type TEXT CHECK(type IN ('New Business', 'Existing Business', 'Amendment')),
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner TEXT,
                forecast_category TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        
        # RFQ (Request for Quote) Table - DIBBs Integration
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS rfqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT UNIQUE NOT NULL,
                pdf_name TEXT,
                pdf_path TEXT,
                solicitation_url TEXT,
                open_date DATE,
                close_date DATE,
                purchase_number TEXT,
                nsn TEXT,
                fsc TEXT,
                delivery_days INTEGER,
                payment_history TEXT,
                unit TEXT,
                quantity INTEGER,
                fob TEXT,
                iso TEXT,
                inspection_point TEXT,
                sampling TEXT,
                product_description TEXT,
                manufacturer TEXT,
                packaging TEXT,
                package_type TEXT,
                office TEXT,
                division TEXT,
                buyer_address TEXT,
                buyer_name TEXT,
                buyer_code TEXT,
                buyer_telephone TEXT,
                buyer_email TEXT,
                buyer_fax TEXT,
                buyer_info TEXT,
                status TEXT DEFAULT 'New' CHECK(status IN ('New', 'Reviewed', 'Quoted', 'Won', 'Lost', 'Skipped')),
                opportunity_id INTEGER,
                account_id INTEGER,
                contact_id INTEGER,
                product_id INTEGER,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (contact_id) REFERENCES contacts (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # QPL (Qualified Products List) Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS qpl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nsn TEXT NOT NULL,
                fsc TEXT,
                product_name TEXT,
                manufacturer TEXT,
                part_number TEXT,
                cage_code TEXT,
                description TEXT,
                specifications TEXT,
                qualification_date DATE,
                expiration_date DATE,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Pending')),
                product_id INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Tasks Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Not Started' CHECK(status IN ('Not Started', 'In Progress', 'Completed', 'Waiting', 'Deferred')),
                priority TEXT DEFAULT 'Normal' CHECK(priority IN ('High', 'Normal', 'Low')),
                type TEXT CHECK(type IN ('Call', 'Email', 'Meeting', 'Follow-up', 'Research', 'Quote', 'Other')),
                due_date DATE,
                completed_date DATE,
                assigned_to TEXT,
                related_to_type TEXT CHECK(related_to_type IN ('Account', 'Contact', 'Opportunity', 'RFQ')),
                related_to_id INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interactions & Appointments Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                description TEXT,
                type TEXT CHECK(type IN ('Call', 'Email', 'Meeting', 'Note', 'Demo', 'Proposal')),
                interaction_date DATETIME,
                duration_minutes INTEGER,
                location TEXT,
                outcome TEXT,
                related_to_type TEXT CHECK(related_to_type IN ('Account', 'Contact', 'Opportunity', 'RFQ')),
                related_to_id INTEGER,
                contact_id INTEGER,
                account_id INTEGER,
                opportunity_id INTEGER,
                rfq_id INTEGER,
                created_by TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (opportunity_id) REFERENCES opportunities (id),
                FOREIGN KEY (rfq_id) REFERENCES rfqs (id)
            )
        ''')
        
        # Create indexes for better performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_contacts_account ON contacts(account_id)',
            'CREATE INDEX IF NOT EXISTS idx_opportunities_account ON opportunities(account_id)',
            'CREATE INDEX IF NOT EXISTS idx_opportunities_contact ON opportunities(contact_id)',
            'CREATE INDEX IF NOT EXISTS idx_rfqs_product ON rfqs(product_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
            'CREATE INDEX IF NOT EXISTS idx_interactions_date ON interactions(interaction_date)',
            'CREATE INDEX IF NOT EXISTS idx_qpl_nsn ON qpl(nsn)'
        ]
        
        for index in indexes:
            self.conn.execute(index)
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """Execute an update/insert query"""
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)
        self.conn.commit()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

# Database instance
db = CRMDatabase()
