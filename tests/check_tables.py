from src.core.crm_data import crm_data

print('All tables in database:')
tables = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table"')
for table in tables:
    if isinstance(table, dict):
        print(f'  - {table["name"]}')
    else:
        print(f'  - {table[0]}')

print('\nProduct-related tables:')
product_tables = crm_data.execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%product%"')
for table in product_tables:
    if isinstance(table, dict):
        print(f'  - {table["name"]}')
    else:
        print(f'  - {table[0]}')
