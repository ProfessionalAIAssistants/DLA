from src.core.crm_data import crm_data

contacts = crm_data.get_contacts()
print(f'Found {len(contacts)} contacts')

if contacts:
    for i, contact in enumerate(contacts[:3]):
        if contact:
            print(f'  {i+1}. Contact ID {contact.get("id")}: {contact.get("first_name")} {contact.get("last_name")}')
else:
    print('No contacts found')
