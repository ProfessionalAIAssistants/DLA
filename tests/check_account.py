import sqlite3

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM accounts WHERE id = 53')
account = cursor.fetchone()

if account:
    print('Account 53 verification:')
    for key in account.keys():
        print(f'  {key}: {account[key]}')
else:
    print('Account 53 not found')

conn.close()
