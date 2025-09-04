import sqlite3

# Compare the two database files
def compare_databases():
    try:
        # Root database
        conn1 = sqlite3.connect('crm.db')
        cursor1 = conn1.cursor()
        cursor1.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables1 = [row[0] for row in cursor1.fetchall()]
        
        # Data folder database  
        conn2 = sqlite3.connect('data/crm.db')
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables2 = [row[0] for row in cursor2.fetchall()]
        
        print("ROOT crm.db:")
        print(f"  Tables: {len(tables1)}")
        print(f"  Table names: {tables1}")
        
        print("\nDATA/crm.db:")
        print(f"  Tables: {len(tables2)}")
        print(f"  Table names: {tables2}")
        
        # Check accounts count
        if 'accounts' in tables1:
            cursor1.execute("SELECT COUNT(*) FROM accounts")
            count1 = cursor1.fetchone()[0]
            print(f"\nROOT crm.db accounts: {count1}")
        
        if 'accounts' in tables2:
            cursor2.execute("SELECT COUNT(*) FROM accounts") 
            count2 = cursor2.fetchone()[0]
            print(f"DATA/crm.db accounts: {count2}")
        
        conn1.close()
        conn2.close()
        
        # Recommendation
        print("\n" + "="*50)
        if len(tables2) > len(tables1) and 'accounts' in tables2:
            print("RECOMMENDATION: Keep data/crm.db (has actual data)")
            print("ACTION: Delete root crm.db (empty/minimal)")
        else:
            print("RECOMMENDATION: Check which database has your data")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    compare_databases()
