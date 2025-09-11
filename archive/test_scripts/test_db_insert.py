import sqlite3

# Connect to database and check the exact columns in tasks table
conn = sqlite3.connect('data/crm.db')
cursor = conn.cursor()

# Get detailed table info
cursor.execute('PRAGMA table_info(tasks)')
columns = cursor.fetchall()
print('Tasks table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]}) - nullable: {not col[3]}, default: {col[4]}')

# Check if the fields are missing from the allowed fields in create_task
cursor.execute("INSERT INTO tasks (subject, parent_item_type, parent_item_id) VALUES (?, ?, ?)", 
               ('Direct DB Test', 'Opportunity', 1))
conn.commit()

# Check if it worked
cursor.execute('SELECT id, subject, parent_item_type, parent_item_id FROM tasks WHERE subject = ?', ('Direct DB Test',))
result = cursor.fetchone()
if result:
    print(f'\nDirect DB insert worked: ID: {result[0]}, Subject: {result[1]}, Parent Type: {result[2]}, Parent ID: {result[3]}')
else:
    print('\nDirect DB insert failed')

conn.close()
