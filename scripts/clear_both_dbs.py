import sqlite3
import os

# Clear both database files
for db_file in ['crm.db', 'crm_database.db']:
    if os.path.exists(db_file):
        print(f"Clearing {db_file}...")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        tables = ['tasks', 'opportunities', 'interactions', 'rfqs']
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✅ Cleared {table}")
            except:
                print(f"  ⚠️ {table} not found")
        
        # Try to clear projects if it exists
        try:
            cursor.execute("DELETE FROM projects")
            print(f"  ✅ Cleared projects")
        except:
            print(f"  ⚠️ projects not found")
        
        # Reset auto-increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('tasks', 'opportunities', 'interactions', 'rfqs', 'projects')")
        
        conn.commit()
        conn.close()

print("✅ All specified data cleared from both databases!")
