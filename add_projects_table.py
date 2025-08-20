import sqlite3
import os

def add_projects_table(db_path):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    if cursor.fetchone():
        print("'projects' table already exists.")
        conn.close()
        return
    # Create the projects table
    print("Creating 'projects' table...")
    cursor.execute('''
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    print("'projects' table created successfully.")
    conn.close()

if __name__ == "__main__":
    db_files = ['crm.db', 'crm_database.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            add_projects_table(db_file)
