import sqlite3

conn = sqlite3.connect('data/crm.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('Tables in database:')
for table in tables:
    print(f'  - {table[0]}')

# Check if we have opportunities
cursor.execute("SELECT COUNT(*) FROM opportunities")
opp_count = cursor.fetchone()[0]
print(f'\nOpportunities: {opp_count}')

conn.close()
