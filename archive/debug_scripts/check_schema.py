#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('data/crm.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE name='accounts'")
schema = cursor.fetchone()[0]
print('Accounts table schema:')
print(schema)
conn.close()
