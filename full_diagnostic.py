import sqlite3
import os

def check_database():
    db_files = ['crm.db', 'crm_database.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n=== Checking {db_file} ===")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [table[0] for table in cursor.fetchall() if not table[0].startswith('sqlite_')]
                
                print(f"Tables found: {len(tables)}")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
                
                conn.close()
            except Exception as e:
                print(f"Error checking {db_file}: {e}")
        else:
            print(f"{db_file}: NOT FOUND")

def check_pdfs():
    print("\n=== Checking PDF Files ===")
    to_process_dir = "To Process"
    if os.path.exists(to_process_dir):
        pdf_files = []
        for file in os.listdir(to_process_dir):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
        
        print(f"PDF files in 'To Process': {len(pdf_files)}")
        for pdf in pdf_files:
            print(f"  - {pdf}")
    else:
        print("'To Process' directory not found")

def check_templates():
    print("\n=== Checking Templates ===")
    templates_dir = "templates"
    if os.path.exists(templates_dir):
        templates = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
        print(f"Template files: {len(templates)}")
        for template in templates:
            print(f"  - {template}")
    else:
        print("'templates' directory not found")

if __name__ == "__main__":
    print("=== DLA System Diagnostic ===")
    check_database()
    check_pdfs()
    check_templates()
    print("\n=== Diagnostic Complete ===")
