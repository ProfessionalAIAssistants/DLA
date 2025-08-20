import sqlite3
import os

def add_column_if_missing(cursor, table, column, coltype):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        print(f"Adding column '{column}' to '{table}'...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    else:
        print(f"Column '{column}' already exists in '{table}'.")

def fix_projects_table(db_path):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    if not cursor.fetchone():
        print("'projects' table does not exist. Run add_projects_table.py first.")
        conn.close()
        return
    # Add missing columns
    add_column_if_missing(cursor, 'projects', 'due_date', 'TEXT')
    add_column_if_missing(cursor, 'projects', 'priority', 'INTEGER DEFAULT 0')
    add_column_if_missing(cursor, 'projects', 'created_date', 'TEXT')
    conn.commit()
    print("'projects' table columns fixed.")
    conn.close()

if __name__ == "__main__":
    db_files = ['crm.db', 'crm_database.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            fix_projects_table(db_file)
