#!/usr/bin/env python3
"""
Add pdf_file_path column to opportunities table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.crm_database import db

def add_pdf_file_path_column():
    """Add pdf_file_path column to opportunities table"""
    try:
        # Check if column already exists
        cursor = db.execute_query("PRAGMA table_info(opportunities)")
        columns = [row[1] for row in cursor]
        
        if 'pdf_file_path' not in columns:
            print("Adding pdf_file_path column to opportunities table...")
            db.execute_update("ALTER TABLE opportunities ADD COLUMN pdf_file_path TEXT")
            print("✓ Successfully added pdf_file_path column")
        else:
            print("pdf_file_path column already exists")
            
    except Exception as e:
        print(f"Error adding pdf_file_path column: {e}")

if __name__ == "__main__":
    add_pdf_file_path_column()
