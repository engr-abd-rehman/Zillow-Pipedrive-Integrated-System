#!/usr/bin/env python3
"""
Advanced Zillow Scraper with Multiple Agent Extraction Patterns
- Sequential URL scraping (AS-IS → TLC → etc.)
- Multiple agent extraction patterns
- Property type tracking
- CSV + Database duplicate checking
- Auto-upload to Pipedrive
- Configuration from config.ini file
"""

import requests
import sqlite3
import re
import time
import csv
import os
from bs4 import BeautifulSoup
from datetime import datetime
from config_manager import get_config

# Load configuration
config = get_config()

# ScrapingBee API Configuration (from config.ini)
SCRAPINGBEE_API_KEY = config.get_scrapingbee_api_key()

# Pipedrive API Configuration (from config.ini)
PIPEDRIVE_API_TOKEN = config.get_pipedrive_api_token()
PIPEDRIVE_API_URL = config.get_pipedrive_api_url()

# Paths (from config.ini)
DB_PATH = config.get_database_path()
CSV_PATH = config.get_csv_path()
URLS_FILE = config.get_urls_file()

# URL Categories (in order)
URL_CATEGORIES = [
    "AS-IS Properties",
    "INVESTOR SPECIAL Properties",
    "INVESTOR OPPORTUNITY Properties",
    "NEEDS WORK Properties",
    "OUTDATED Properties",
    "DATED Properties",
    "NEEDS UPDATING Properties",
    "FIXER UPPER Properties",
    "MOTIVATED Properties",
    "TLC Properties"
]

class AdvancedZillowScraper:
    """Advanced scraper with multiple agent extraction patterns"""
    
    def __init__(self, db_path=DB_PATH, csv_path=CSV_PATH):
        self.db_path = db_path
        self.csv_path = csv_path
        self.scraped_count = 0
        self.duplicate_count = 0
        self.uploaded_count = 0
        
    def log(self, message):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    def add_pagination_to_url(self, url, page):
        """Add pagination parameter to Zillow URL"""
        import urllib.parse

        if page == 1:
            # First page - keep pagination empty
            return url

        # For page 2+, we need to modify the pagination parameter
        # Current: "pagination":%7B%7D (which is "pagination":{})
        # Target: "pagination":%7B%22currentPage%22%3A2%7D (which is "pagination":{"currentPage":2})

        try:
            # Decode URL
            decoded = urllib.parse.unquote(url)

            # Replace empty pagination with page number
            # From: "pagination":{}
            # To: "pagination":{"currentPage":2}
            pagination_json = f'"pagination":{{"currentPage":{page}}}'

            # Replace in decoded URL
            if '"pagination":{}' in decoded:
                decoded = decoded.replace('"pagination":{}', pagination_json)
            elif '"pagination":{' in decoded:
                # Already has pagination, replace it
                import re
                decoded = re.sub(r'"pagination":\{[^}]*\}', pagination_json, decoded)

            # Re-encode URL
            return urllib.parse.quote(decoded, safe=':/?#[]@!$&\'()*+,;=')

        except Exception as e:
            self.log(f"   ⚠️ Pagination URL error: {str(e)}, using original URL")
            return url

    def fetch_with_scrapingbee(self, url, use_stealth=False):
        """Fetch URL using ScrapingBee API with retry logic"""
        # Try Premium Proxy first (unless stealth explicitly requested)
        if not use_stealth:
            params = {
                'api_key': SCRAPINGBEE_API_KEY,
                'url': url,
                'render_js': 'true',
                'premium_proxy': 'true',
                'block_resources': 'false'
            }

            try:
                response = requests.get('https://app.scrapingbee.com/api/v1', params=params, timeout=120)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 500:
                    self.log(f"   ⚠️ Premium proxy blocked (500), trying Stealth proxy...")
                    # Fall through to stealth proxy
                else:
                    self.log(f"❌ ScrapingBee error: HTTP {response.status_code}")
                    return None

            except Exception as e:
                self.log(f"   ⚠️ Premium proxy failed: {str(e)}, trying Stealth proxy...")
                # Fall through to stealth proxy

        # Try Stealth Proxy (75 credits)
        params = {
            'api_key': SCRAPINGBEE_API_KEY,
            'url': url,
            'render_js': 'true',
            'stealth_proxy': 'true',
            'block_resources': 'false'
        }

        try:
            response = requests.get('https://app.scrapingbee.com/api/v1', params=params, timeout=120)

            if response.status_code == 200:
                return response.text
            else:
                self.log(f"❌ Stealth proxy error: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log(f"❌ Stealth proxy failed: {str(e)}")
            return None
    
    def parse_search_results(self, html):
        """Parse search results page to extract property listings"""
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        # Find property cards
        property_cards = soup.find_all('article', {'data-test': 'property-card'})
        
        for card in property_cards:
            try:
                # Extract address
                address_elem = card.find('address')
                if not address_elem:
                    continue
                address = address_elem.get_text(strip=True)
                
                # Extract price
                price_elem = card.find('span', {'data-test': 'property-card-price'})
                price = price_elem.get_text(strip=True) if price_elem else 'N/A'
                
                # Extract beds/baths/sqft
                beds_elem = card.find('li', string=re.compile(r'\d+\s*bd'))
                baths_elem = card.find('li', string=re.compile(r'\d+\s*ba'))
                sqft_elem = card.find('li', string=re.compile(r'\d+\s*sqft'))
                
                beds = beds_elem.get_text(strip=True) if beds_elem else 'N/A'
                baths = baths_elem.get_text(strip=True) if baths_elem else 'N/A'
                sqft = sqft_elem.get_text(strip=True) if sqft_elem else 'N/A'
                
                # Extract URL
                link_elem = card.find('a', {'data-test': 'property-card-link'})
                url = ''
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    url = f"https://www.zillow.com{href}" if href.startswith('/') else href

                properties.append({
                    'address': address,
                    'price': price,
                    'beds': beds,
                    'baths': baths,
                    'sqft': sqft,
                    'url': url,
                    'agent_name': 'N/A',
                    'agent_phone': 'N/A'
                })

            except Exception as e:
                continue

        return properties

    def extract_agent_info_advanced(self, url):
        """Extract agent info with ENHANCED patterns from cleaned_zillow_scraper_before.py"""
        html = self.fetch_with_scrapingbee(url)
        if not html:
            return {'agent_name': 'N/A', 'agent_phone': 'N/A'}

        soup = BeautifulSoup(html, 'html.parser')
        agent_info = {'agent_name': 'N/A', 'agent_phone': 'N/A'}

        # ===== METHOD 1: seller-attribution (MOST RELIABLE) =====
        try:
            seller_attr = soup.find('div', {'data-testid': 'seller-attribution'})
            if seller_attr:
                self.log("   ✅ Found seller-attribution div")
                spans = seller_attr.find_all('span')

                for span in spans:
                    span_text = span.get_text(strip=True)

                    # Check if this is a phone number
                    if re.match(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', span_text):
                        clean_phone = re.sub(r'[,\s]+$', '', span_text).strip()
                        if agent_info['agent_phone'] == 'N/A':
                            agent_info['agent_phone'] = clean_phone

                    # Check if this is an agent name
                    elif (span_text and
                          not span_text.startswith('Listed by') and
                          not span_text.startswith('Listing provided by') and
                          not span_text.startswith('Listing Provided by') and
                          len(span_text.split()) >= 2 and
                          len(span_text) > 5 and
                          not re.match(r'^\d', span_text) and
                          agent_info['agent_name'] == 'N/A'):
                        agent_info['agent_name'] = span_text

                # If found both, return immediately
                if agent_info['agent_name'] != 'N/A' and agent_info['agent_phone'] != 'N/A':
                    self.log(f"   🎯 Method 1 success: {agent_info['agent_name']} - {agent_info['agent_phone']}")
                    return agent_info
        except:
            pass

        # ===== METHOD 2: attribution-LISTING_AGENT (NEW - FROM BROWSER TEST) =====
        try:
            listing_agent = soup.find('p', {'data-testid': 'attribution-LISTING_AGENT'})
            if listing_agent:
                self.log("   ✅ Found attribution-LISTING_AGENT")
                spans = listing_agent.find_all('span')
                for i, span in enumerate(spans):
                    span_text = span.get_text(strip=True)

                    # First span is usually agent name
                    if i == 0 and agent_info['agent_name'] == 'N/A':
                        if len(span_text) > 5 and not re.match(r'^\d', span_text):
                            agent_info['agent_name'] = span_text

                    # Look for phone in any span
                    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', span_text)
                    if phone_match and agent_info['agent_phone'] == 'N/A':
                        clean_phone = re.sub(r'[,\s]+$', '', phone_match.group(0)).strip()
                        agent_info['agent_phone'] = clean_phone

                if agent_info['agent_name'] != 'N/A' and agent_info['agent_phone'] != 'N/A':
                    self.log(f"   🎯 Method 2 success: {agent_info['agent_name']} - {agent_info['agent_phone']}")
                    return agent_info
        except:
            pass

        # ===== METHOD 3: attribution-BROKER =====
        try:
            broker_elem = soup.find('p', {'data-testid': 'attribution-BROKER'})
            if broker_elem:
                self.log("   ✅ Found attribution-BROKER")
                spans = broker_elem.find_all('span')
                for span in spans:
                    span_text = span.get_text(strip=True)

                    # Extract phone
                    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', span_text)
                    if phone_match and agent_info['agent_phone'] == 'N/A':
                        agent_info['agent_phone'] = phone_match.group(0)

                    # Extract broker name as fallback
                    elif (len(span_text) > 3 and
                          not re.match(r'^\d', span_text) and
                          agent_info['agent_name'] == 'N/A'):
                        agent_info['agent_name'] = span_text
        except:
            pass

        # ===== METHOD 4: JSON extraction patterns =====
        if agent_info['agent_name'] == 'N/A' or agent_info['agent_phone'] == 'N/A':
            try:
                json_patterns = [
                    r'"listingAgent":(\{.*?\})',
                    r'"agent":\s*\{[^}]*"name":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',
                    r'"contactAgent"[^}]*"name":\s*"([^"]+)"[^}]*"phone":\s*"([^"]+)"',
                    r'"agentName":\s*"([^"]+)"[^}]*"agentPhoneNumber":\s*"([^"]+)"',
                    r'"displayName":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"'
                ]

                for i, pattern in enumerate(json_patterns, 1):
                    match = re.search(pattern, html)
                    if match:
                        try:
                            if 'listingAgent' in pattern:
                                import json
                                agent_json = json.loads(match.group(1))
                                if agent_info['agent_name'] == 'N/A':
                                    agent_info['agent_name'] = agent_json.get('name', agent_json.get('displayName', 'N/A'))
                                if agent_info['agent_phone'] == 'N/A':
                                    agent_info['agent_phone'] = agent_json.get('phoneNumber', agent_json.get('phone', 'N/A'))
                            else:
                                if agent_info['agent_name'] == 'N/A' and len(match.groups()) >= 1:
                                    agent_info['agent_name'] = match.group(1)
                                if agent_info['agent_phone'] == 'N/A' and len(match.groups()) >= 2:
                                    agent_info['agent_phone'] = match.group(2)

                            if agent_info['agent_name'] != 'N/A' and agent_info['agent_phone'] != 'N/A':
                                self.log(f"   🎯 Method 4 (JSON pattern {i}) success")
                                break
                        except:
                            continue
            except:
                pass

        # ===== METHOD 5: Text pattern search =====
        if agent_info['agent_name'] == 'N/A' or agent_info['agent_phone'] == 'N/A':
            try:
                text_patterns = [
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[\(,]?\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                    r'Listed\s+by[:\s]*([A-Za-z\s]+?)\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                    r'Listing\s+Provided\s+by[:\s]*([A-Za-z\s]+?)\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
                ]

                for pattern in text_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        potential_name = match.group(1).strip()
                        potential_phone = match.group(2).strip()

                        if (len(potential_name) > 5 and len(potential_name) < 50 and
                            not any(word in potential_name.lower() for word in ['contact', 'listing', 'phone'])):
                            if agent_info['agent_name'] == 'N/A':
                                agent_info['agent_name'] = potential_name
                            if agent_info['agent_phone'] == 'N/A':
                                agent_info['agent_phone'] = potential_phone
                            self.log(f"   🎯 Method 5 (text pattern) success")
                            break
            except:
                pass

        # ===== METHOD 6: Phone-only search (fallback) =====
        if agent_info['agent_phone'] == 'N/A':
            try:
                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                phone_matches = re.findall(phone_pattern, html)
                for phone in phone_matches:
                    # Skip toll-free numbers
                    if not any(x in phone for x in ['800', '888', '877', '866', '844']):
                        agent_info['agent_phone'] = phone
                        self.log(f"   ✅ Method 6 (phone-only) found: {phone}")
                        break
            except:
                pass

        # Clean phone format
        if agent_info['agent_phone'] != 'N/A':
            try:
                phone_clean = re.sub(r'\D+', '', agent_info['agent_phone'])[-10:]
                if len(phone_clean) == 10:
                    agent_info['agent_phone'] = f"({phone_clean[:3]}) {phone_clean[3:6]}-{phone_clean[6:]}"
            except:
                pass

        return agent_info

    def is_duplicate_in_csv(self, address):
        """Check if property exists in CSV"""
        if not os.path.exists(self.csv_path):
            return False

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('address', '').strip().lower() == address.strip().lower():
                        return True
        except:
            pass

        return False

    def is_duplicate_in_database(self, address):
        """Check if property exists in any database table (case-insensitive)"""
        if not os.path.exists(self.db_path):
            return False

        # Normalize address for comparison
        normalized_address = address.strip().lower()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = ['lead_in', 'no_response', 'responded', 'verbal_follow_up',
                  'contract_follow_up', 'day_30_follow_up', 'day_60_follow_up',
                  'day_90_follow_up', 'pending', 'expired_listing', 'dead_deal']

        for table in tables:
            try:
                # Case-insensitive comparison using LOWER()
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE LOWER(TRIM(address)) = ?", (normalized_address,))
                if cursor.fetchone()[0] > 0:
                    conn.close()
                    return True
            except:
                continue

        conn.close()
        return False

    def save_to_csv(self, property_data):
        """Save property to CSV file"""
        try:
            # Check if file exists
            file_exists = os.path.exists(self.csv_path)

            # Prepare row
            row = {
                'address': property_data['address'],
                'price': property_data['price'],
                'beds': property_data['beds'],
                'baths': property_data['baths'],
                'sqft': property_data['sqft'],
                'property_type': property_data['property_type'],
                'agent_name': property_data['agent_name'],
                'agent_phone': property_data['agent_phone'],
                'url': property_data['url'],
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Write to CSV
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['address', 'price', 'beds', 'baths', 'sqft', 'property_type',
                             'agent_name', 'agent_phone', 'url', 'scraped_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write header if new file
                if not file_exists:
                    writer.writeheader()

                writer.writerow(row)

            return True
        except Exception as e:
            self.log(f"   ❌ CSV save error: {str(e)}")
            return False

    def save_to_database(self, property_data):
        """Save property to database (lead_in table)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lead_in (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER UNIQUE,
                    address TEXT,
                    beds TEXT,
                    baths TEXT,
                    sqft TEXT,
                    price TEXT,
                    property_type TEXT,
                    agent_name TEXT,
                    agent_phone TEXT,
                    person_id INTEGER,
                    synced_at TEXT
                )
            ''')

            # Insert property
            cursor.execute('''
                INSERT INTO lead_in (address, beds, baths, sqft, price, property_type,
                                    agent_name, agent_phone, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                property_data['address'],
                property_data['beds'],
                property_data['baths'],
                property_data['sqft'],
                property_data['price'],
                property_data['property_type'],
                property_data['agent_name'],
                property_data['agent_phone'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.log(f"   ❌ Database save error: {str(e)}")
            return False

    def upload_to_pipedrive(self, property_data):
        """Upload property to Pipedrive with notes and person"""
        try:
            # Step 1: Create or find Person
            person_id = self.create_or_find_person(
                property_data['agent_name'],
                property_data['agent_phone'],
                property_data['address']
            )

            if not person_id:
                return {'success': False, 'error': 'Failed to create/find person'}

            # Step 2: Create Deal
            deal_id = self.create_deal(property_data, person_id)

            if not deal_id:
                return {'success': False, 'error': 'Failed to create deal'}

            # Step 3: Create Note
            note_created = self.create_note(deal_id, property_data)

            return {
                'success': True,
                'deal_id': deal_id,
                'person_id': person_id,
                'note_created': note_created
            }
        except Exception as e:
            self.log(f"   ❌ Pipedrive upload error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_or_find_person(self, agent_name, agent_phone, property_address):
        """Create or find person in Pipedrive"""
        try:
            # Search by phone
            if agent_phone and agent_phone != 'N/A':
                r = requests.get(
                    f"{PIPEDRIVE_API_URL}/persons/search",
                    params={'api_token': PIPEDRIVE_API_TOKEN, 'term': agent_phone, 'fields': 'phone'},
                    timeout=30
                )

                if r.status_code == 200:
                    results = r.json().get('data', {}).get('items', [])
                    if results:
                        return results[0].get('item', {}).get('id')

            # Create new person
            person_data = {
                'name': agent_name,
                'phone': [{'value': agent_phone, 'primary': True}] if agent_phone != 'N/A' else [],
                'e1e3aea16d6dd6827c567816d150a0567c54449c': property_address
            }

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/persons",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=person_data,
                timeout=30
            )

            if r.status_code == 201:
                return r.json().get('data', {}).get('id')

            return None
        except:
            return None

    def create_deal(self, property_data, person_id):
        """Create deal in Pipedrive"""
        try:
            # Clean price
            price_value = property_data['price'].replace('$', '').replace(',', '').strip()
            try:
                price_value = float(price_value)
            except:
                price_value = 0

            deal_data = {
                'title': property_data['address'],
                'value': price_value,
                'currency': 'USD',
                'person_id': person_id,
                'stage_id': 101,  # Lead In
                '2ad561ae448ea1e1cdfa03632d7b579b7aca0c46': property_data['agent_name'],
                'e21efd113e42560cb52b1f3d62ec046158477c4e': property_data['agent_phone']
            }

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/deals",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=deal_data,
                timeout=30
            )

            if r.status_code == 201:
                return r.json().get('data', {}).get('id')

            return None
        except:
            return None

    def create_note(self, deal_id, property_data):
        """Create formatted note for deal"""
        try:
            note_content = f"""🏠 PROPERTY DETAILS
📍 Address: {property_data['address']}
💰 Price: {property_data['price']}
🛏️ Beds: {property_data['beds']} | 🛁 Baths: {property_data['baths']} | 📐 Sqft: {property_data['sqft']}

👤 Agent: {property_data['agent_name']}
📞 Agent Phone: {property_data['agent_phone']}

🔗 Property URL: {property_data['url']}
📋 Scraped From: {property_data['property_type']}

📅 Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            note_data = {'content': note_content, 'deal_id': deal_id}

            r = requests.post(
                f"{PIPEDRIVE_API_URL}/notes",
                params={'api_token': PIPEDRIVE_API_TOKEN},
                json=note_data,
                timeout=30
            )

            return r.status_code == 201
        except:
            return False

    def scrape_url(self, search_url, property_type, max_properties=50):
        """Scrape properties from a single URL with PAGINATION support"""
        self.log(f"🔍 Scraping: {property_type}")
        self.log(f"   URL: {search_url[:80]}...")

        all_properties = []
        page = 1
        consecutive_empty = 0

        # Loop through pages until we have enough properties or no more pages
        while len(all_properties) < max_properties:
            self.log(f"\n   📄 Fetching page {page}...")

            # Add pagination to URL
            paginated_url = self.add_pagination_to_url(search_url, page)

            # Fetch search results
            html = self.fetch_with_scrapingbee(paginated_url)
            if not html:
                self.log(f"   ❌ Failed to fetch page {page}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    self.log(f"   🛑 Stopping: 3 consecutive failed pages")
                    break
                page += 1
                continue

            # Parse properties
            properties = self.parse_search_results(html)

            if not properties:
                consecutive_empty += 1
                self.log(f"   ⚠️ Page {page}: No properties found")
                if consecutive_empty >= 3:
                    self.log(f"   🛑 Stopping: 3 consecutive empty pages")
                    break
                page += 1
                continue

            # Reset consecutive empty counter
            consecutive_empty = 0
            self.log(f"   ✅ Page {page}: Found {len(properties)} properties")

            # Add properties to list
            all_properties.extend(properties)

            # Check if we have enough
            if len(all_properties) >= max_properties:
                self.log(f"   ✅ Collected {len(all_properties)} properties (target: {max_properties})")
                break

            # Move to next page
            page += 1

            # Small delay between pages
            time.sleep(2)

        # Limit to max_properties
        all_properties = all_properties[:max_properties]
        self.log(f"\n   📊 Total properties collected: {len(all_properties)}")

        # Process each property
        saved_count = 0
        for i, prop in enumerate(all_properties, 1):
            self.log(f"\n   [{i}/{len(all_properties)}] {prop['address']}")

            # Check duplicates
            if self.is_duplicate_in_csv(prop['address']):
                self.log(f"      ⚠️  Duplicate in CSV - Skipping")
                self.duplicate_count += 1
                continue

            if self.is_duplicate_in_database(prop['address']):
                self.log(f"      ⚠️  Duplicate in Database - Skipping")
                self.duplicate_count += 1
                continue

            # Extract agent info
            if prop['url']:
                self.log(f"      🔍 Extracting agent info...")
                agent_info = self.extract_agent_info_advanced(prop['url'])
                prop['agent_name'] = agent_info['agent_name']
                prop['agent_phone'] = agent_info['agent_phone']
                self.log(f"      👤 Agent: {prop['agent_name']}")
                self.log(f"      📞 Phone: {prop['agent_phone']}")

            # Add property type
            prop['property_type'] = property_type

            # Save to CSV
            self.log(f"      💾 Saving to CSV...")
            if self.save_to_csv(prop):
                self.log(f"      ✅ Saved to CSV")

            # Save to Database
            self.log(f"      💾 Saving to Database...")
            if self.save_to_database(prop):
                self.log(f"      ✅ Saved to Database")

            # Upload to Pipedrive
            self.log(f"      📤 Uploading to Pipedrive...")
            if self.upload_to_pipedrive(prop):
                self.log(f"      ✅ Uploaded to Pipedrive")
                self.uploaded_count += 1

            saved_count += 1
            self.scraped_count += 1

            # Rate limiting
            time.sleep(2)

        self.log(f"\n   ✅ Completed {property_type}: {saved_count} new properties")
        return saved_count

    def load_urls_from_file(self):
        """Load URLs from file with categories"""
        urls = []

        try:
            with open(URLS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_category = None
            for line in lines:
                line = line.strip()

                # Extract category from comment
                if line.startswith('#') and any(cat in line for cat in URL_CATEGORIES):
                    for cat in URL_CATEGORIES:
                        if cat in line:
                            current_category = cat
                            break

                # Extract URL
                elif line.startswith('http') and current_category:
                    urls.append({
                        'url': line,
                        'category': current_category
                    })

        except Exception as e:
            self.log(f"❌ Error loading URLs: {str(e)}")

        return urls

    def load_urls(self):
        """Load URLs for UI - returns list of (url, property_type) tuples"""
        urls_data = self.load_urls_from_file()
        return [(item['url'], item['category']) for item in urls_data]

    def scrape_properties_from_url(self, url, property_type, max_properties=5, log_callback=None):
        """Scrape properties from a single URL - for UI use with PAGINATION support

        Args:
            url: Zillow search URL
            property_type: Category name
            max_properties: Maximum properties to scrape
            log_callback: Optional callback function for logging (for UI)
        """
        properties = []
        page = 1
        consecutive_empty = 0

        # Helper function for logging
        def log_msg(msg):
            if log_callback:
                log_callback(msg)
            else:
                self.log(msg)

        try:
            # Loop through pages until we have enough properties
            while len(properties) < max_properties:
                log_msg(f"   📄 Page {page}...")

                # Add pagination to URL
                paginated_url = self.add_pagination_to_url(url, page)

                # Fetch page
                html = self.fetch_with_scrapingbee(paginated_url)
                if not html:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        log_msg(f"   🛑 Stopping: 3 consecutive failed pages")
                        break
                    page += 1
                    continue

                # Extract properties
                soup = BeautifulSoup(html, 'html.parser')
                property_cards = soup.find_all('article', {'data-test': 'property-card'})

                if not property_cards:
                    consecutive_empty += 1
                    log_msg(f"   ⚠️ Page {page}: No properties found")
                    if consecutive_empty >= 3:
                        log_msg(f"   🛑 Stopping: 3 consecutive empty pages")
                        break
                    page += 1
                    continue

                # Reset consecutive empty counter
                consecutive_empty = 0
                page_properties = 0

                for card in property_cards:
                    # Stop if we have enough properties
                    if len(properties) >= max_properties:
                        break

                    try:
                        prop = {}

                        # Extract address
                        address_elem = card.find('address')
                        if address_elem:
                            prop['address'] = address_elem.get_text(strip=True)
                        else:
                            continue

                        # Extract price
                        price_elem = card.find('span', {'data-test': 'property-card-price'})
                        if price_elem:
                            prop['price'] = price_elem.get_text(strip=True)
                        else:
                            prop['price'] = 'N/A'

                        # Extract beds, baths, sqft - ENHANCED METHOD
                        prop['beds'] = 'N/A'
                        prop['baths'] = 'N/A'
                        prop['sqft'] = 'N/A'

                        # Method 1: Look in all li, span, and div elements
                        detail_selectors = [
                            card.find_all("li"),
                            card.find_all("span"),
                            card.find_all("div", class_=lambda x: x and 'bed' in x.lower()),
                            card.find_all("div", class_=lambda x: x and 'bath' in x.lower()),
                            card.find_all("div", class_=lambda x: x and 'sqft' in x.lower())
                        ]

                        all_elements = []
                        for selector_result in detail_selectors:
                            all_elements.extend(selector_result)

                        for element in all_elements:
                            text = element.get_text().lower().strip()
                            if text:
                                # Extract beds
                                if ('bed' in text or 'bd' in text) and prop['beds'] == 'N/A':
                                    if any(char.isdigit() for char in text):
                                        prop['beds'] = element.get_text(strip=True)

                                # Extract baths
                                elif ('bath' in text or 'ba' in text) and prop['baths'] == 'N/A':
                                    if any(char.isdigit() for char in text):
                                        prop['baths'] = element.get_text(strip=True)

                                # Extract sqft
                                elif ('sqft' in text or 'sq ft' in text or 'ft²' in text) and prop['sqft'] == 'N/A':
                                    if any(char.isdigit() for char in text):
                                        prop['sqft'] = element.get_text(strip=True)

                        # Extract URL
                        link_elem = card.find('a', {'data-test': 'property-card-link'})
                        if link_elem and link_elem.get('href'):
                            href = link_elem['href'].split('?')[0]
                            if href.startswith('/homedetails'):
                                prop['url'] = f"https://www.zillow.com{href}"
                            elif href.startswith('https://www.zillow.com/homedetails'):
                                prop['url'] = href
                            else:
                                prop['url'] = f"https://www.zillow.com{href}"
                        else:
                            continue

                        # Add property type
                        prop['property_type'] = property_type

                        # Add to list
                        properties.append(prop)
                        page_properties += 1

                    except Exception as e:
                        continue

                log_msg(f"   ✅ Page {page}: Collected {page_properties} properties (Total: {len(properties)})")

                # Check if we have enough
                if len(properties) >= max_properties:
                    break

                # Move to next page
                page += 1
                time.sleep(2)  # Delay between pages

        except Exception as e:
            log_msg(f"❌ Error scraping URL: {str(e)}")

        return properties[:max_properties]  # Limit to max_properties

    def run_sequential_scraping(self, max_per_url=50, loop=True):
        """Run sequential scraping through all URLs"""
        self.log("=" * 80)
        self.log("🚀 STARTING ADVANCED ZILLOW SCRAPER")
        self.log("=" * 80)

        while True:
            # Load URLs
            urls = self.load_urls_from_file()
            self.log(f"\n📋 Loaded {len(urls)} URLs from {URLS_FILE}")

            if not urls:
                self.log("❌ No URLs found!")
                break

            # Reset counters for this cycle
            cycle_start = datetime.now()
            self.scraped_count = 0
            self.duplicate_count = 0
            self.uploaded_count = 0

            # Scrape each URL sequentially
            for i, url_data in enumerate(urls, 1):
                self.log(f"\n{'='*80}")
                self.log(f"URL {i}/{len(urls)}: {url_data['category']}")
                self.log(f"{'='*80}")

                self.scrape_url(url_data['url'], url_data['category'], max_per_url)

                # Wait between URLs
                if i < len(urls):
                    self.log(f"\n⏳ Waiting 5 seconds before next URL...")
                    time.sleep(5)

            # Cycle summary
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds() / 60

            self.log(f"\n{'='*80}")
            self.log(f"🎉 CYCLE COMPLETE!")
            self.log(f"{'='*80}")
            self.log(f"   ✅ New properties scraped: {self.scraped_count}")
            self.log(f"   ⚠️  Duplicates skipped: {self.duplicate_count}")
            self.log(f"   📤 Uploaded to Pipedrive: {self.uploaded_count}")
            self.log(f"   ⏱️  Duration: {duration:.1f} minutes")
            self.log(f"{'='*80}")

            # Loop back or exit
            if not loop:
                break

            self.log(f"\n🔄 Starting new cycle from AS-IS Properties...")
            self.log(f"⏳ Waiting 10 seconds...\n")
            time.sleep(10)


if __name__ == "__main__":
    scraper = AdvancedZillowScraper()

    # Run with loop=False for single cycle, loop=True for continuous
    scraper.run_sequential_scraping(max_per_url=50, loop=True)

