import sqlite3

# Check data/crm.db
try:
    conn = sqlite3.connect('data/crm.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables in data/crm.db:", tables)
    
    # Check counts
    for table in ['tasks', 'opportunities', 'projects', 'interactions', 'rfqs']:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} records")
        except:
            print(f"{table}: table doesn't exist")
    
    conn.close()
except Exception as e:
    print(f"Error with data/crm.db: {e}")

print("\n" + "="*50 + "\n")

# Check root crm.db  
try:
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables in crm.db:", tables)
    
    conn.close()
except Exception as e:
    print(f"Error with crm.db: {e}")
