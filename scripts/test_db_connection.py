from src.core.crm_database import db
print('Testing database connection...')
tables = db.execute_query('SELECT name FROM sqlite_master WHERE type="table"')
print(f'Found {len(tables)} tables in database')
print('Tables:', [t['name'] for t in tables])
