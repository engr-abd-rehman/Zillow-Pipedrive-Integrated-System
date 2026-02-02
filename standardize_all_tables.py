#!/usr/bin/env python3
"""
Standardize all database tables to have same columns
"""

import sqlite3

DB_PATH = 'data/zillow.db'

# Standard columns that all tables should have
STANDARD_COLUMNS = [
    'deal_id',
    'address',
    'price',
    'beds',
    'baths',
    'sqft',
    'property_type',
    'agent_name',
    'agent_phone',
    'url',
    'person_id',
    'synced_at'
]

def standardize_all_tables():
    """Ensure all tables have the same columns"""
    print("=" * 80)
    print("🔧 STANDARDIZING ALL DATABASE TABLES")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['lead_in', 'no_response', 'verbal_follow_up', 'contract_follow_up',
              'day_30_follow_up', 'day_60_follow_up', 'day_90_follow_up',
              'pending', 'expired_listing', 'dead_deal']
    
    for table in tables:
        print(f"\n📊 Checking table: {table}")
        
        try:
            # Get current columns
            cursor.execute(f"PRAGMA table_info({table})")
            current_cols = [col[1] for col in cursor.fetchall()]
            
            # Find missing columns
            missing_cols = [col for col in STANDARD_COLUMNS if col not in current_cols]
            
            if missing_cols:
                print(f"   ❌ Missing columns: {', '.join(missing_cols)}")
                
                for col in missing_cols:
                    print(f"      Adding {col}...")
                    
                    # Determine column type
                    if col in ['deal_id', 'person_id']:
                        col_type = 'INTEGER'
                    elif col == 'synced_at':
                        col_type = 'TIMESTAMP'
                    else:
                        col_type = 'TEXT'
                    
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                    print(f"      ✅ Added {col}")
                
                conn.commit()
            else:
                print(f"   ✅ All standard columns present")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 Rows: {count}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ STANDARDIZATION COMPLETE!")
    print("=" * 80)
    
    # Verify
    print("\n📊 VERIFICATION:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        missing = [col for col in STANDARD_COLUMNS if col not in cols]
        status = "✅" if not missing else "❌"
        
        print(f"{status} {table:20s}: {len(cols):2d} columns, {count:4d} rows")
        if missing:
            print(f"   Missing: {', '.join(missing)}")
    
    conn.close()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    standardize_all_tables()

