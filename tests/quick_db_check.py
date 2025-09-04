#!/usr/bin/env python3

import sqlite3
import json
from pathlib import Path

def check_database():
    """Quick database check for testing"""
    db_path = Path('data/crm.db')
    
    if not db_path.exists():
        print("Database not found!")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check processing reports
        cursor.execute('SELECT COUNT(*) FROM processing_reports')
        report_count = cursor.fetchone()[0]
        print(f'Processing reports in database: {report_count}')
        
        if report_count > 0:
            cursor.execute('SELECT id, filename, created_at FROM processing_reports ORDER BY created_at DESC LIMIT 3')
            reports = cursor.fetchall()
            print("\nRecent reports:")
            for report in reports:
                print(f'  ID: {report[0]}, File: {report[1]}, Created: {report[2]}')
        
        # Check opportunities
        cursor.execute('SELECT COUNT(*) FROM opportunities')
        opp_count = cursor.fetchone()[0]
        print(f'\nOpportunities in database: {opp_count}')
        
        if opp_count > 0:
            cursor.execute('SELECT id, name, stage, created_at FROM opportunities ORDER BY created_at DESC LIMIT 5')
            opportunities = cursor.fetchall()
            print("\nRecent opportunities:")
            for opp in opportunities:
                print(f'  ID: {opp[0]}, Name: {opp[1]}, Stage: {opp[2]}, Created: {opp[3]}')
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
