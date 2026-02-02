#!/usr/bin/env python3
"""
Complete Pipedrive to Database Sync
Syncs all deals from Pipedrive "On Market" pipeline to database
"""

import requests
import sqlite3

# Pipedrive API Configuration
PIPEDRIVE_API_TOKEN = "d43b4e8b2f06c9ccee9c7eefe6fbfcef4c9f2fe1"
PIPEDRIVE_API_URL = "https://api.pipedrive.com/v1"

# Database Configuration
DB_PATH = 'data/zillow.db'

# Stage to Table Mapping (On Market pipeline - ID: 9)
STAGE_MAPPING = {
    101: 'lead_in',              # Lead In
    109: 'no_response',          # No Response
    134: 'verbal_follow_up',     # Verbal Follow Up
    104: 'contract_follow_up',   # Contract Follow up
    111: 'day_30_follow_up',     # 30 Day Follow Up
    113: 'day_60_follow_up',     # 60 Day Follow Up
    112: 'day_90_follow_up',     # 90 Day Follow Up
    114: 'pending',              # Pending
    105: 'expired_listing',      # Expired Listing
    133: 'dead_deal',            # Dead Deal
}


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
            
            pagination = data.get('additional_data', {}).get('pagination', {})
            if not pagination.get('more_items_in_collection'):
                break
            
            start = pagination.get('next_start', start + limit)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            break
    
    return all_deals


def clear_all_tables():
    """Clear all database tables"""
    print("\n🗑️ Clearing all database tables...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['lead_in', 'no_response', 'responded', 'verbal_follow_up',
              'contract_follow_up', 'day_30_follow_up', 'day_60_follow_up',
              'day_90_follow_up', 'pending', 'expired_listing', 'dead_deal']
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   ✅ Cleared {table}")
        except:
            pass
    
    conn.commit()
    conn.close()
    print("✅ All tables cleared")


def sync_deals_to_database(deals):
    """Sync deals to database"""
    print(f"\n📥 Syncing {len(deals)} deals to database...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {'total': len(deals), 'synced': 0, 'skipped': 0, 'errors': 0, 'by_table': {}}
    
    for deal in deals:
        try:
            deal_id = deal.get('id')
            title = deal.get('title', 'N/A')
            stage_id = deal.get('stage_id')
            value = deal.get('value', 0)
            
            # Skip if not in our pipeline
            if stage_id not in STAGE_MAPPING:
                stats['skipped'] += 1
                continue
            
            # Get custom fields
            agent_name = deal.get('e1e3aea16d6dd6827c567816d150a0567c54449c', 'N/A')
            agent_phone = deal.get('4e0f8a4b4c6dd6827c567816d150a0567c54449c', 'N/A')
            zillow_link = deal.get('a4e0f8a4b4c6dd6827c567816d150a0567c54449c', 'N/A')
            
            table = STAGE_MAPPING[stage_id]
            
            cursor.execute(f"""
                INSERT INTO {table} (deal_id, address, price, agent_name, agent_phone, url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (deal_id, title, value, agent_name, agent_phone, zillow_link))
            
            stats['synced'] += 1
            stats['by_table'][table] = stats['by_table'].get(table, 0) + 1
            
        except Exception as e:
            stats['errors'] += 1
            print(f"   ❌ Error syncing deal {deal_id} (Stage {stage_id}): {str(e)}")
    
    conn.commit()
    conn.close()
    return stats


def main():
    print("=" * 80)
    print("🔄 FULL PIPEDRIVE TO DATABASE SYNC")
    print("=" * 80)
    
    deals = get_all_deals()
    if not deals:
        print("❌ No deals found")
        return
    
    print(f"✅ Found {len(deals)} deals")
    
    clear_all_tables()
    stats = sync_deals_to_database(deals)
    
    print("\n" + "=" * 80)
    print("📊 SYNC STATISTICS")
    print("=" * 80)
    print(f"Total: {stats['total']}, Synced: {stats['synced']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
    print(f"\n📋 By Table:")
    for table, count in sorted(stats['by_table'].items()):
        print(f"   {table}: {count}")
    print("\n✅ SYNC COMPLETE!")


if __name__ == '__main__':
    main()

