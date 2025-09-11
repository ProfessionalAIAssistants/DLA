import sqlite3
import os

# Check database structure
db_path = os.path.join(os.getcwd(), 'data', 'crm.db')
print(f"Looking for database at: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get opportunities table structure
    cursor.execute('PRAGMA table_info(opportunities)')
    print('\nOpportunities table columns:')
    for row in cursor.fetchall():
        print(f'  {row[1]} - {row[2]}')
    
    # Get a sample opportunity to see data structure
    cursor.execute('SELECT * FROM opportunities LIMIT 1')
    columns = [description[0] for description in cursor.description]
    sample = cursor.fetchone()
    
    print('\nSample opportunity data:')
    if sample:
        for i, col in enumerate(columns):
            print(f'  {col}: {sample[i]}')
    else:
        print('  No opportunities found in database')
    
    conn.close()
else:
    print("Database file not found!")
