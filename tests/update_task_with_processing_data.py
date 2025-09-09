import sqlite3
import json

# Check existing tasks
conn = sqlite3.connect(r'data\crm.db')
cursor = conn.cursor()

cursor.execute("SELECT id, subject, description FROM tasks ORDER BY id DESC LIMIT 5")
tasks = cursor.fetchall()

print("Existing tasks:")
for task in tasks:
    notes_len = len(str(task[2])) if task[2] else 0
    print(f"ID {task[0]}: {task[1]} (notes: {notes_len} chars)")

# Let's update the first task with processing data
if tasks:
    task_id = tasks[0][0]
    
    processing_data = {
        'files_processed': ['SAMPLE1.PDF', 'SAMPLE2.PDF'],
        'opportunities_created': 2,
        'contacts_created': 1,
        'accounts_created': 1,
        'processing_time': '2025-01-15 10:30:00',
        'status': 'completed'
    }
    
    notes = 'PROCESSING_DATA:' + json.dumps(processing_data)
    
    cursor.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes, task_id))
    conn.commit()
    
    print(f"\n✅ Updated task {task_id} with processing data")
    print(f"📝 Notes length: {len(notes)}")
    print(f"🌐 View at: http://127.0.0.1:5000/task/{task_id}")

conn.close()
print("\nDone!")
