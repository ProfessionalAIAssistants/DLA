import sqlite3

def update_opportunities_stage_constraint():
    """Update the opportunities table to use the correct business stages"""
    
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    
    try:
        # First, let's check current data
        cursor.execute("SELECT DISTINCT stage FROM opportunities WHERE stage IS NOT NULL")
        current_stages = [row[0] for row in cursor.fetchall()]
        print("Current stages in database:", current_stages)
        
        # Create a new table with the correct constraints
        cursor.execute("""
            CREATE TABLE opportunities_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_id INTEGER,
                contact_id INTEGER,
                stage TEXT CHECK(stage IN ('Prospecting', 'RFQ Requested', 'RFQ Received', 'Submit Bid', 'Project Started')),
                amount REAL,
                probability INTEGER CHECK(probability >= 0 AND probability <= 100),
                close_date DATE,
                lead_source TEXT,
                next_step TEXT,
                type TEXT CHECK(type IN ('New Business', 'Existing Business', 'Amendment')),
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner TEXT,
                forecast_category TEXT, 
                state TEXT CHECK(state IN ('Active', 'No Bid', 'Past Due', 'Bid Lost', 'Won')), 
                bid_price REAL, 
                product_id INTEGER, 
                bid_date DATE, 
                mfr TEXT, 
                iso TEXT CHECK(iso IN ('Yes', 'No')), 
                fob TEXT CHECK(fob IN ('Origin', 'Destination')), 
                buyer TEXT, 
                packaging_type TEXT, 
                purchase_costs REAL, 
                packaging_shipping REAL, 
                quantity INTEGER, 
                profit REAL,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        """)
        
        # Copy all data from old table to new table, mapping old stages to new ones
        stage_mapping = {
            'Prospecting': 'Prospecting',
            'Qualification': 'RFQ Requested',
            'Proposal': 'Submit Bid',
            'Negotiation': 'Submit Bid',
            'Closed Won': 'Project Started',
            'Closed Lost': 'Submit Bid'
        }
        
        cursor.execute("SELECT * FROM opportunities")
        opportunities = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(opportunities)")
        columns = [col[1] for col in cursor.fetchall()]
        
        for opp in opportunities:
            # Convert to dict for easier handling
            opp_dict = dict(zip(columns, opp))
            
            # Map old stage to new stage
            if opp_dict['stage'] in stage_mapping:
                opp_dict['stage'] = stage_mapping[opp_dict['stage']]
            else:
                opp_dict['stage'] = 'Prospecting'  # Default fallback
                
            # Set default state if not set
            if not opp_dict['state']:
                opp_dict['state'] = 'Active'
                
            # Insert into new table
            placeholders = ', '.join(['?' for _ in columns])
            cursor.execute(f"INSERT INTO opportunities_new ({', '.join(columns)}) VALUES ({placeholders})", 
                          [opp_dict[col] for col in columns])
        
        # Drop old table and rename new table
        cursor.execute("DROP TABLE opportunities")
        cursor.execute("ALTER TABLE opportunities_new RENAME TO opportunities")
        
        conn.commit()
        print("Successfully updated opportunities table with new stage constraints!")
        
        # Verify the update
        cursor.execute("SELECT DISTINCT stage FROM opportunities WHERE stage IS NOT NULL")
        new_stages = [row[0] for row in cursor.fetchall()]
        print("New stages in database:", new_stages)
        
        cursor.execute("SELECT DISTINCT state FROM opportunities WHERE state IS NOT NULL")
        states = [row[0] for row in cursor.fetchall()]
        print("States in database:", states)
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_opportunities_stage_constraint()
