import sqlite3

conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Get the CREATE TABLE statement
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='opportunities'")
schema = cursor.fetchone()[0]

print("Opportunities table schema:")
print(schema)

conn.close()
