from src.core.crm_data import crm_data

print('=== CHECKING QPL STATUS ===')

try:
    # Check all QPLs in database
    all_qpls = crm_data.execute_query('SELECT id, manufacturer_name, part_number, created_date FROM qpls ORDER BY id')
    print(f'Total QPLs in database: {len(all_qpls)}')
    
    for qpl in all_qpls:
        if isinstance(qpl, dict):
            print(f'  ID {qpl["id"]}: {qpl["product_name"]} (NSN: {qpl["nsn"]}, created: {qpl["created_date"]})')
        else:
            print(f'  ID {qpl[0]}: {qpl[1]} (NSN: {qpl[2]}, created: {qpl[3]})')
    
    # Check QPLs for specific date
    task_date = '2025-09-08'
    date_qpls = crm_data.execute_query(f'SELECT id, manufacturer_name, part_number, created_date FROM qpls WHERE date(created_date) = "{task_date}"')
    print(f'\nQPLs for {task_date}: {len(date_qpls)}')
    
    for qpl in date_qpls:
        if isinstance(qpl, dict):
            print(f'  ID {qpl["id"]}: {qpl["product_name"]} (created: {qpl["created_date"]})')
        else:
            print(f'  ID {qpl[0]}: {qpl[1]} (created: {qpl[2]})')
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
