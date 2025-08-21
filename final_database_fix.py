#!/usr/bin/env python
# coding: utf-8

"""
Final Database Fix Utility
Handles data transformation and constraint issues
"""

import sqlite3
import os
from datetime import datetime

def split_name(full_name):
    """Split full name into first and last name"""
    if not full_name or full_name.strip() == '':
        return 'Unknown', 'Contact'
    
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ''
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        return parts[0], ' '.join(parts[1:])

def map_interaction_type(original_type):
    """Map interaction types to valid values"""
    type_mapping = {
        'Call': 'Call',
        'Email': 'Email',
        'LinkedIn': 'Note',  # Map LinkedIn to Note
        'Text': 'Note',      # Map Text to Note
        'Meeting': 'Meeting',
        'Demo': 'Demo',
        'Proposal': 'Proposal'
    }
    return type_mapping.get(original_type, 'Note')

def copy_contacts_with_transformation():
    """Copy contacts with name splitting"""
    source_conn = sqlite3.connect('crm_database.db')
    dest_conn = sqlite3.connect('crm.db')
    
    try:
        # Get contacts from source
        source_cursor = source_conn.cursor()
        source_cursor.execute("""
            SELECT id, name, account_id, email, phone, title, created_date, modified_date
            FROM contacts
        """)
        contacts = source_cursor.fetchall()
        
        if not contacts:
            print("No contacts to copy")
            return 0
        
        # Transform and insert
        dest_cursor = dest_conn.cursor()
        copied = 0
        
        for contact in contacts:
            id_val, name, account_id, email, phone, title, created_date, modified_date = contact
            
            # Split name
            first_name, last_name = split_name(name)
            
            # Insert with transformation
            try:
                dest_cursor.execute("""
                    INSERT OR REPLACE INTO contacts 
                    (id, first_name, last_name, account_id, email, phone, title, created_date, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_val, first_name, last_name, account_id, email, phone, title, created_date, modified_date))
                copied += 1
            except Exception as e:
                print(f"Error copying contact {name}: {e}")
        
        dest_conn.commit()
        print(f"Contacts: Copied {copied} records with name transformation")
        return copied
        
    except Exception as e:
        print(f"Error in copy_contacts_with_transformation: {e}")
        return 0
    finally:
        source_conn.close()
        dest_conn.close()

def copy_interactions_with_transformation():
    """Copy interactions with type mapping"""
    source_conn = sqlite3.connect('crm_database.db')
    dest_conn = sqlite3.connect('crm.db')
    
    try:
        # Get interactions from source
        source_cursor = source_conn.cursor()
        source_cursor.execute("""
            SELECT id, subject, type, interaction_date, duration_minutes, location, outcome,
                   contact_id, account_id, opportunity_id, created_by, created_date
            FROM interactions
        """)
        interactions = source_cursor.fetchall()
        
        if not interactions:
            print("No interactions to copy")
            return 0
        
        # Transform and insert
        dest_cursor = dest_conn.cursor()
        copied = 0
        
        for interaction in interactions:
            (id_val, subject, type_val, interaction_date, duration_minutes, location, outcome,
             contact_id, account_id, opportunity_id, created_by, created_date) = interaction
            
            # Map interaction type
            mapped_type = map_interaction_type(type_val)
            
            # Insert with transformation
            try:
                dest_cursor.execute("""
                    INSERT OR REPLACE INTO interactions 
                    (id, subject, type, interaction_date, duration_minutes, location, outcome,
                     contact_id, account_id, opportunity_id, created_by, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (id_val, subject, mapped_type, interaction_date, duration_minutes, location, outcome,
                      contact_id, account_id, opportunity_id, created_by, created_date))
                copied += 1
            except Exception as e:
                print(f"Error copying interaction {id_val}: {e}")
        
        dest_conn.commit()
        print(f"Interactions: Copied {copied} records with type transformation")
        return copied
        
    except Exception as e:
        print(f"Error in copy_interactions_with_transformation: {e}")
        return 0
    finally:
        source_conn.close()
        dest_conn.close()

def final_database_fix():
    """Perform final database fixes"""
    print("=== Final Database Fix ===")
    print("Copying remaining data with transformations...")
    
    total_copied = 0
    
    # Copy contacts with name transformation
    contacts_copied = copy_contacts_with_transformation()
    total_copied += contacts_copied
    
    # Copy interactions with type mapping
    interactions_copied = copy_interactions_with_transformation()
    total_copied += interactions_copied
    
    print(f"\nFinal fix completed! Additional records copied: {total_copied}")
    return total_copied > 0

if __name__ == "__main__":
    success = final_database_fix()
    
    if success:
        print("✅ Final database fix completed!")
        print("\nRunning final diagnostic...")
        # Run diagnostic to show final state
        os.system("python direct_diagnostic.py")
    else:
        print("❌ Final database fix had issues!")
    
    print("=== Fix Complete ===")
