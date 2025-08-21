import sqlite3

conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Get the CREATE TABLE statement for tasks
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
schema = cursor.fetchone()[0]

print("Tasks table schema:")
print(schema)

conn.close()
