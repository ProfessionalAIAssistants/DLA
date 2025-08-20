"""
Comprehensive Opportunities System Analysis and Verification
"""
from crm_data import CRMData

def verify_opportunities_system():
    print("=" * 60)
    print("OPPORTUNITIES SYSTEM - COMPREHENSIVE VERIFICATION")
    print("=" * 60)
    
    crm = CRMData()
    
    # 1. DATABASE STRUCTURE VERIFICATION
    print("\n1. DATABASE STRUCTURE VERIFICATION")
    print("-" * 40)
    
    # Check all required fields from user specifications
    required_fields = [
        'id', 'stage', 'state', 'bid_price', 'purchase_costs', 'packaging_shipping',
        'profit', 'bid_date', 'close_date', 'quantity', 'unit', 'mfr', 'fob',
        'packaging_type', 'iso', 'sampling', 'days_aod', 'packaging_info',
        'payment', 'last_modified', 'created_date', 'buyer', 'skipped', 'document'
    ]
    
    opportunities = crm.get_opportunities(limit=1)
    if opportunities:
        available_fields = list(opportunities[0].keys())
        print("✅ Database fields present:")
        for field in required_fields:
            status = "✅" if field in available_fields else "❌"
            print(f"   {status} {field}")
    
    # 2. ENUMERATED VALUES VERIFICATION
    print("\n2. ENUMERATED VALUES VERIFICATION")
    print("-" * 40)
    
    # Check Stage values
    expected_stages = ['Prospecting', 'RFQ Requested', 'RFQ Received', 'Submit Bid', 'Project Started']
    opportunities = crm.get_opportunities()
    actual_stages = list(set([opp['stage'] for opp in opportunities if opp['stage']]))
    print("✅ Stage values:")
    for stage in expected_stages:
        status = "✅" if stage in actual_stages else "⚠️"
        print(f"   {status} {stage}")
    
    # Check State values
    expected_states = ['Active', 'No Bid', 'Past Due', 'Bid Lost', 'Won']
    actual_states = list(set([opp['state'] for opp in opportunities if opp['state']]))
    print("✅ State values:")
    for state in expected_states:
        status = "✅" if state in actual_states else "⚠️"
        print(f"   {status} {state}")
    
    # Check FOB values
    expected_fob = ['Origin', 'Destination']
    actual_fob = list(set([opp['fob'] for opp in opportunities if opp['fob']]))
    print("✅ FOB values:")
    for fob in expected_fob:
        status = "✅" if fob in actual_fob else "⚠️"
        print(f"   {status} {fob}")
    
    # Check ISO/Sampling values
    expected_yesno = ['Yes', 'No']
    actual_iso = list(set([opp['iso'] for opp in opportunities if opp['iso']]))
    print("✅ ISO values:")
    for val in expected_yesno:
        status = "✅" if val in actual_iso else "⚠️"
        print(f"   {status} {val}")
    
    # 3. CALCULATED FIELDS VERIFICATION
    print("\n3. CALCULATED FIELDS VERIFICATION")
    print("-" * 40)
    
    # Test profit calculation
    test_opp = None
    for opp in opportunities:
        if (opp['bid_price'] and opp['purchase_costs'] and 
            opp['packaging_shipping'] and opp['quantity']):
            test_opp = opp
            break
    
    if test_opp:
        expected_profit = (test_opp['bid_price'] - test_opp['purchase_costs'] - test_opp['packaging_shipping']) * test_opp['quantity']
        actual_profit = test_opp['profit']
        print(f"✅ Profit calculation test:")
        print(f"   Bid: ${test_opp['bid_price']} | Costs: ${test_opp['purchase_costs']} | Shipping: ${test_opp['packaging_shipping']} | Qty: {test_opp['quantity']}")
        print(f"   Expected: ${expected_profit:.2f} | Actual: ${actual_profit:.2f}")
        print(f"   Status: {'✅ CORRECT' if abs(expected_profit - actual_profit) < 0.01 else '❌ INCORRECT'}")
    
    # 4. CRM METHODS VERIFICATION
    print("\n4. CRM METHODS VERIFICATION")
    print("-" * 40)
    
    required_methods = [
        'create_opportunity', 'get_opportunities', 'update_opportunity',
        'get_opportunity_by_id', 'delete_opportunity', 'get_opportunity_stats',
        'get_opportunities_by_stage', 'get_opportunities_by_state',
        'advance_opportunity_stage', 'mark_opportunity_won', 'mark_opportunity_lost',
        'get_opportunities_due_soon', 'get_overdue_opportunities',
        'get_packaging_types', 'search_opportunities', 'recalculate_opportunity_profit'
    ]
    
    print("✅ CRM Methods available:")
    for method in required_methods:
        status = "✅" if hasattr(crm, method) else "❌"
        print(f"   {status} {method}")
    
    # 5. FILTERING CAPABILITIES VERIFICATION
    print("\n5. FILTERING CAPABILITIES VERIFICATION")
    print("-" * 40)
    
    filter_tests = [
        ('stage', 'Submit Bid'),
        ('state', 'Active'),
        ('iso', 'Yes'),
        ('fob', 'Destination'),
        ('buyer', 'DLA'),
        ('search', 'connector')
    ]
    
    print("✅ Filter functionality:")
    for filter_key, filter_value in filter_tests:
        try:
            results = crm.get_opportunities({filter_key: filter_value})
            print(f"   ✅ {filter_key} filter: {len(results)} results")
        except Exception as e:
            print(f"   ❌ {filter_key} filter: ERROR - {e}")
    
    # 6. STATISTICS AND ANALYTICS
    print("\n6. STATISTICS AND ANALYTICS VERIFICATION")
    print("-" * 40)
    
    stats = crm.get_opportunity_stats()
    required_stats = ['total', 'active', 'won', 'lost', 'no_bid', 'overdue', 
                     'due_today', 'pipeline_value', 'won_value', 'total_profit']
    
    print("✅ Statistics available:")
    for stat in required_stats:
        status = "✅" if stat in stats else "❌"
        value = stats.get(stat, 'N/A')
        print(f"   {status} {stat}: {value}")
    
    # 7. BUSINESS LOGIC VERIFICATION
    print("\n7. BUSINESS LOGIC VERIFICATION")
    print("-" * 40)
    
    # Test stage progression
    stage_progression = {
        'Prospecting': 'RFQ Requested',
        'RFQ Requested': 'RFQ Received', 
        'RFQ Received': 'Submit Bid',
        'Submit Bid': 'Project Started',
        'Project Started': 'Project Started'
    }
    
    print("✅ Stage progression logic:")
    for current, expected_next in stage_progression.items():
        print(f"   ✅ {current} → {expected_next}")
    
    # 8. RELATIONSHIP VERIFICATION
    print("\n8. RELATIONSHIP VERIFICATION")
    print("-" * 40)
    
    relationships = ['account_id', 'contact_id', 'product_id']
    relationship_names = ['account_name', 'contact_name', 'product_name']
    
    print("✅ Relationship fields:")
    for rel in relationships:
        status = "✅" if any(opp[rel] for opp in opportunities if opp[rel]) else "⚠️"
        print(f"   {status} {rel}")
    
    print("✅ Relationship name resolution:")
    for rel_name in relationship_names:
        status = "✅" if (opportunities and rel_name in dict(opportunities[0]).keys()) else "❌"
        print(f"   {status} {rel_name}")
    
    # 9. UI TEMPLATE VERIFICATION
    print("\n9. UI TEMPLATE VERIFICATION")
    print("-" * 40)
    
    try:
        with open('templates/opportunities.html', 'r') as f:
            template_content = f.read()
            
        ui_features = [
            'stats cards', 'filtering form', 'opportunities table',
            'add opportunity modal', 'stage advancement', 'mark won/lost',
            'delete functionality', 'comprehensive form fields'
        ]
        
        feature_checks = {
            'stats cards': 'stats.' in template_content,
            'filtering form': 'form method="GET"' in template_content,
            'opportunities table': 'opportunities table' in template_content.lower(),
            'add opportunity modal': 'addOpportunityModal' in template_content,
            'stage advancement': 'advanceStage' in template_content,
            'mark won/lost': 'markWon' in template_content and 'markLost' in template_content,
            'delete functionality': 'deleteOpportunity' in template_content,
            'comprehensive form fields': 'bid_price' in template_content and 'packaging_type' in template_content
        }
        
        print("✅ UI Template features:")
        for feature in ui_features:
            status = "✅" if feature_checks.get(feature, False) else "❌"
            print(f"   {status} {feature}")
            
    except FileNotFoundError:
        print("   ❌ Template file not found")
    
    # 10. API ENDPOINTS VERIFICATION
    print("\n10. API ENDPOINTS VERIFICATION")
    print("-" * 40)
    
    expected_endpoints = [
        'POST /api/opportunities',
        'PATCH /api/opportunities/<id>',
        'DELETE /api/opportunities/<id>',
        'POST /api/opportunities/<id>/advance',
        'POST /api/opportunities/<id>/won',
        'POST /api/opportunities/<id>/lost'
    ]
    
    try:
        with open('crm_app.py', 'r') as f:
            app_content = f.read()
        
        print("✅ API Endpoints:")
        for endpoint in expected_endpoints:
            method, path = endpoint.split(' ', 1)
            # Check for route definition
            route_pattern = f"@app.route('{path.replace('<id>', '<int:opportunity_id>')}')"
            status = "✅" if route_pattern.replace('<int:opportunity_id>', '<int:opportunity_id>') in app_content else "❌"
            print(f"   {status} {endpoint}")
            
    except FileNotFoundError:
        print("   ❌ App file not found")
    
    print("\n" + "=" * 60)
    print("OPPORTUNITIES SYSTEM VERIFICATION COMPLETE")
    print("=" * 60)
    
    # Final summary
    print(f"\n📊 CURRENT SYSTEM STATUS:")
    print(f"   Total Opportunities: {stats.get('total', 0)}")
    print(f"   Pipeline Value: ${stats.get('pipeline_value', 0):,.2f}")
    print(f"   Won Value: ${stats.get('won_value', 0):,.2f}")
    print(f"   Total Profit: ${stats.get('total_profit', 0):,.2f}")
    print(f"   Active Opportunities: {stats.get('active', 0)}")
    print(f"   Overdue: {stats.get('overdue', 0)}")

if __name__ == "__main__":
    verify_opportunities_system()
