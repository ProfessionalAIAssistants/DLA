"""
Test script to diagnose potential issues in the CRM application
"""

import os
from pathlib import Path
import sys

def check_environment():
    """Check if all required modules are installed"""
    try:
        import PyPDF2
        print("PyPDF2 module is installed")
    except ImportError:
        print("PyPDF2 module is NOT installed")
    
    try:
        import flask
        print("Flask module is installed")
    except ImportError:
        print("Flask module is NOT installed")

def check_directories():
    """Check if required directories exist"""
    to_process = Path("To Process")
    print(f"To Process directory exists: {to_process.exists()}")
    if to_process.exists():
        pdfs = list(to_process.glob('*.pdf')) + list(to_process.glob('*.PDF'))
        print(f"PDFs in To Process directory: {len(pdfs)}")
    
    reviewed = Path("Reviewed")
    print(f"Reviewed directory exists: {reviewed.exists()}")

def check_database():
    """Check if database exists and is accessible"""
    db_path = Path("crm.db")
    print(f"Database file exists: {db_path.exists()}")
    
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Database tables: {[table[0] for table in tables]}")
            conn.close()
        except Exception as e:
            print(f"Error accessing database: {e}")

def test_pdf_processor():
    """Test PDF processor functionality"""
    try:
        from pdf_processor import pdf_processor
        print("PDF processor imported successfully")
        
        to_process = Path("To Process")
        if to_process.exists() and len(list(to_process.glob('*.pdf')) + list(to_process.glob('*.PDF'))) > 0:
            # Test PDF file count
            try:
                pdf_files = list(to_process.glob("*.pdf")) + list(to_process.glob("*.PDF"))
                print(f"Found {len(pdf_files)} PDF files")
            except Exception as e:
                print(f"Error counting PDF files: {e}")
    except Exception as e:
        print(f"Error testing PDF processor: {e}")

if __name__ == "__main__":
    print("\n=== Environment Check ===")
    check_environment()
    
    print("\n=== Directory Check ===")
    check_directories()
    
    print("\n=== Database Check ===")
    check_database()
    
    print("\n=== PDF Processor Check ===")
    test_pdf_processor()
