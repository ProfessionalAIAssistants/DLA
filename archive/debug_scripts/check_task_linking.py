import sqlite3

# Connect to database
conn = sqlite3.connect('data/crm.db')
cursor = conn.cursor()

# Check tasks table structure
cursor.execute('PRAGMA table_info(tasks)')
print('Tasks table structure:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

# Check recent tasks
cursor.execute('SELECT id, subject, parent_item_type, parent_item_id FROM tasks ORDER BY id DESC LIMIT 10')
print('\nRecent tasks:')
for row in cursor.fetchall():
    print(f'  ID: {row[0]}, Subject: {row[1]}, Parent Type: {row[2]}, Parent ID: {row[3]}')

# Check if there are any tasks linked to opportunities
cursor.execute("SELECT COUNT(*) FROM tasks WHERE parent_item_type = 'Opportunity'")
linked_count = cursor.fetchone()[0]
print(f'\nTasks linked to opportunities: {linked_count}')

conn.close()
