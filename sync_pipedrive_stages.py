#!/usr/bin/env python3
"""
Sync Pipedrive stages and deals with local database
Fetches latest stage IDs and names, then syncs all deals
"""

import requests
import sqlite3
import json

# Pipedrive API Configuration
PIPEDRIVE_API_TOKEN = "d43b4e8b2f06c9ccee9c7eefe6fbfcef4c9f2fe1"
PIPEDRIVE_API_URL = "https://api.pipedrive.com/v1"

# Database Configuration
DB_PATH = 'data/zillow.db'


def get_all_stages():
    """Get all stages from Pipedrive"""
    url = f"{PIPEDRIVE_API_URL}/stages"
    params = {'api_token': PIPEDRIVE_API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data', [])
        
        return []
    except Exception as e:
        print(f"❌ Error fetching stages: {str(e)}")
        return []


def get_all_deals():
    """Get all deals from Pipedrive"""
    url = f"{PIPEDRIVE_API_URL}/deals"
    
    all_deals = []
    start = 0
    limit = 500
    
    print("🔍 Fetching all deals from Pipedrive...")
    
    while True:
        params = {
            'api_token': PIPEDRIVE_API_TOKEN,
            'start': start,
            'limit': limit,
            'status': 'all_not_deleted'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            if not data.get('success'):
                break
            
            deals = data.get('data', [])
            
            if not deals:
                break
            
            all_deals.extend(deals)
            print(f"   Fetched {len(all_deals)} deals...")
            
            additional_data = data.get('additional_data', {})
            pagination = additional_data.get('pagination', {})
            
            if not pagination.get('more_items_in_collection'):
                break
            
            start = pagination.get('next_start', start + limit)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            break
    
    return all_deals


def display_stages(stages):
    """Display all stages"""
    print("\n" + "=" * 80)
    print("📊 PIPEDRIVE STAGES")
    print("=" * 80)
    
    if not stages:
        print("❌ No stages found")
        return
    
    # Group by pipeline
    pipelines = {}
    for stage in stages:
        pipeline_id = stage.get('pipeline_id')
        pipeline_name = stage.get('pipeline_name', 'Unknown Pipeline')
        
        if pipeline_id not in pipelines:
            pipelines[pipeline_id] = {
                'name': pipeline_name,
                'stages': []
            }
        
        pipelines[pipeline_id]['stages'].append(stage)
    
    for pipeline_id, pipeline_data in pipelines.items():
        print(f"\n🔷 Pipeline: {pipeline_data['name']} (ID: {pipeline_id})")
        print("-" * 80)
        
        for stage in pipeline_data['stages']:
            stage_id = stage.get('id')
            stage_name = stage.get('name')
            order_nr = stage.get('order_nr', 0)
            deal_probability = stage.get('deal_probability', 0)
            
            print(f"   {order_nr}. {stage_name}")
            print(f"      Stage ID: {stage_id}")
            print(f"      Probability: {deal_probability}%")
            print()


def create_stage_mapping(stages):
    """Create mapping of stage IDs to table names"""
    print("\n" + "=" * 80)
    print("🗺️ STAGE TO TABLE MAPPING")
    print("=" * 80)
    
    # Define mapping based on stage names
    stage_mapping = {}
    
    for stage in stages:
        stage_id = stage.get('id')
        stage_name = stage.get('name', '').lower()
        
        # Map stage names to database tables
        if 'lead' in stage_name or 'new' in stage_name:
            table = 'lead_in'
        elif 'no response' in stage_name or 'no-response' in stage_name:
            table = 'no_response'
        elif 'responded' in stage_name or 'response' in stage_name:
            table = 'responded'
        elif 'verbal' in stage_name:
            table = 'verbal_follow_up'
        elif 'contract' in stage_name:
            table = 'contract_follow_up'
        elif '30' in stage_name:
            table = 'day_30_follow_up'
        elif '60' in stage_name:
            table = 'day_60_follow_up'
        elif '90' in stage_name:
            table = 'day_90_follow_up'
        elif 'pending' in stage_name or 'closing' in stage_name:
            table = 'pending'
        elif 'expired' in stage_name:
            table = 'expired_listing'
        elif 'dead' in stage_name or 'lost' in stage_name or 'closed' in stage_name:
            table = 'dead_deal'
        else:
            table = 'lead_in'  # Default
        
        stage_mapping[stage_id] = {
            'name': stage.get('name'),
            'table': table
        }
        
        print(f"   Stage ID {stage_id}: '{stage.get('name')}' → Table: {table}")
    
    return stage_mapping


def main():
    print("=" * 80)
    print("🔄 PIPEDRIVE SYNC - STAGES & DEALS")
    print("=" * 80)
    
    # Step 1: Get all stages
    print("\n📥 Fetching stages from Pipedrive...")
    stages = get_all_stages()
    
    if not stages:
        print("❌ Failed to fetch stages")
        return
    
    print(f"✅ Found {len(stages)} stages")
    
    # Step 2: Display stages
    display_stages(stages)
    
    # Step 3: Create stage mapping
    stage_mapping = create_stage_mapping(stages)
    
    # Save mapping to file for reference
    with open('stage_mapping.json', 'w') as f:
        json.dump(stage_mapping, f, indent=2)
    
    print(f"\n✅ Stage mapping saved to 'stage_mapping.json'")
    
    print("\n" + "=" * 80)
    print("✅ STAGE SYNC COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()

