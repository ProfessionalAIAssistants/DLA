#!/usr/bin/env python3
import sqlite3

# Connect to database
conn = sqlite3.connect('../data/crm.db')
cursor = conn.cursor()

# Check if payment_history column exists
cursor.execute("PRAGMA table_info(opportunities)")
columns = cursor.fetchall()

payment_history_exists = any(col[1] == 'payment_history' for col in columns)
print(f"Payment history column exists: {payment_history_exists}")

if payment_history_exists:
    print("✅ Payment history column is already in the opportunities table")
else:
    print("❌ Payment history column is missing from the opportunities table")

print(f"Total columns in opportunities table: {len(columns)}")
print("Last 5 columns:")
for col in columns[-5:]:
    print(f"  {col[1]} ({col[2]})")

conn.close()
