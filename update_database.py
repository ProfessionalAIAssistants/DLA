"""
Database Schema Update Utility
Used to update the database schema to match the latest application requirements
"""

import os
import sqlite3
from pathlib import Path
import sys

def check_column_exists(conn, table, column):
    """Check if column exists in table"""
    try:
        cursor = conn.cursor()
        # Check if column exists in table
        cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
        return True
    except sqlite3.OperationalError:
        return False

def add_column_if_not_exists(conn, table, column, data_type="TEXT"):
    """Add column if not exists"""
    if not check_column_exists(conn, table, column):
        print(f"Adding missing column {column} to {table}")
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            print(f"Error adding column: {e}")
            return False
    else:
        print(f"Column {column} already exists in {table}")
        return False

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        return cursor.fetchone() is not None
    except sqlite3.OperationalError:
        return False

def create_table_if_not_exists(conn, table_name, create_statement):
    """Create a table if it doesn't exist"""
    if not check_table_exists(conn, table_name):
        print(f"Creating missing table {table_name}")
        try:
            conn.execute(create_statement)
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            print(f"Error creating table {table_name}: {e}")
            return False
    else:
        print(f"Table {table_name} already exists")
        return False

def update_database_schema():
    """Update database schema to match latest application requirements"""
    # Get database file path
    db_path = "crm.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return False
    
    print(f"Updating database schema for {db_path}...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Add missing tables
        
        # Create projects table if missing
        projects_table_statement = """
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT CHECK(status IN ('Not Started', 'In Progress', 'On Hold', 'Completed', 'Canceled', 'Done')),
            priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
            start_date DATE,
            end_date DATE,
            due_date DATE,
            summary TEXT,
            description TEXT,
            vendor_id INTEGER,
            parent_project_id INTEGER,
            budget REAL,
            actual_cost REAL,
            progress_percentage INTEGER CHECK(progress_percentage >= 0 AND progress_percentage <= 100),
            project_manager TEXT,
            team_members TEXT,
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES accounts(id),
            FOREIGN KEY (parent_project_id) REFERENCES projects(id)
        )
        """
        create_table_if_not_exists(conn, "projects", projects_table_statement)
        
        # Add missing columns to tables
        
        # Fix interactions table
        add_column_if_not_exists(conn, "interactions", "is_active", "INTEGER DEFAULT 1")
        add_column_if_not_exists(conn, "interactions", "last_modified", "TIMESTAMP")
        
        # Fix opportunities table
        add_column_if_not_exists(conn, "opportunities", "state", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "bid_price", "REAL")
        add_column_if_not_exists(conn, "opportunities", "product_id", "INTEGER")
        add_column_if_not_exists(conn, "opportunities", "bid_date", "DATE")
        add_column_if_not_exists(conn, "opportunities", "mfr", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "iso", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "fob", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "buyer", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "packaging_type", "TEXT")
        add_column_if_not_exists(conn, "opportunities", "purchase_costs", "REAL")
        add_column_if_not_exists(conn, "opportunities", "packaging_shipping", "REAL")
        add_column_if_not_exists(conn, "opportunities", "quantity", "INTEGER")
        add_column_if_not_exists(conn, "opportunities", "profit", "REAL")
        
        # Add any other missing columns to other tables as needed
        
        print("Database schema update completed successfully.")
        return True
    
    except Exception as e:
        print(f"Error updating database schema: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()
