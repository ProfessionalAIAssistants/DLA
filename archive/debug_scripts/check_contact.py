import sqlite3

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM contacts WHERE id = 238')
contact = cursor.fetchone()

if contact:
    print('Contact 238 verification:')
    for key in contact.keys():
        print(f'  {key}: {contact[key]}')
else:
    print('Contact 238 not found')

conn.close()
