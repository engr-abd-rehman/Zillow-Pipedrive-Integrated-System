═══════════════════════════════════════════════════════════════════════════════
    ZILLOW PIPEDRIVE INTEGRATED SYSTEM - USER GUIDE
═══════════════════════════════════════════════════════════════════════════════

📁 FOLDER STRUCTURE:
────────────────────────────────────────────────────────────────────────────────
ZillowSystem/
├── ZillowPipedriveSystem.exe    ← Main application (double-click to run)
├── config.ini                   ← Configuration file (API keys, paths)
├── scraping_urls.txt            ← Zillow search URLs (editable)
├── data/
│   └── zillow.db                ← SQLite database (auto-created)
├── zillow_florida_data.csv      ← CSV export (auto-created)
└── README.txt                   ← This file


🚀 QUICK START:
────────────────────────────────────────────────────────────────────────────────
1. Extract all files to a folder (e.g., C:\ZillowSystem)
2. Double-click "ZillowPipedriveSystem.exe"
3. Go to "Auto Scraper" tab
4. Set "Maximum Properties to Scrape" (e.g., 50)
5. Click "START SCRAPING"
6. Done! Properties will be scraped and saved automatically.


⚙️ CONFIGURATION (config.ini):
────────────────────────────────────────────────────────────────────────────────
To update API keys or settings:

1. Right-click "config.ini" → Open with Notepad
2. Edit the values:

   [SCRAPINGBEE]
   api_key = YOUR_SCRAPINGBEE_API_KEY_HERE

   [PIPEDRIVE]
   api_token = YOUR_PIPEDRIVE_API_TOKEN_HERE
   api_url = https://api.pipedrive.com/v1

   [DATABASE]
   db_path = data/zillow.db

   [CSV]
   csv_path = zillow_florida_data.csv

   [URLS]
   urls_file = scraping_urls.txt

3. Save and close
4. Restart the application


🗄️ VIEW DATABASE:
────────────────────────────────────────────────────────────────────────────────
To view database in DB Browser for SQLite:

1. Open "DB Browser for SQLite" (download from sqlitebrowser.org if needed)
2. Click "Open Database"
3. Navigate to "data" folder
4. Select "zillow.db"
5. Browse all tables:
   - lead_in
   - no_response
   - verbal_follow_up
   - contract_follow_up
   - day_30_follow_up
   - day_60_follow_up
   - day_90_follow_up
   - pending
   - expired_listing
   - dead_deal


📊 VIEW CSV FILE:
────────────────────────────────────────────────────────────────────────────────
1. Double-click "zillow_florida_data.csv"
2. Opens in Excel automatically
3. View/edit all scraped properties
4. Columns: Address, Price, Beds, Baths, Sqft, Agent Name, Agent Phone, etc.


📝 EDIT SCRAPING URLS:
────────────────────────────────────────────────────────────────────────────────
To add/remove Zillow search URLs:

1. Right-click "scraping_urls.txt" → Open with Notepad
2. Add new URLs or remove existing ones
3. Format:
   # Category Name (comment)
   https://www.zillow.com/...

4. Save and close
5. Restart scraper to use new URLs


🔄 USING THE APPLICATION:
────────────────────────────────────────────────────────────────────────────────

TAB 1: PROPERTIES DATABASE
- View properties by stage (Lead In, No Response, etc.)
- Filter by property type
- Export to CSV
- Open property in browser

TAB 2: CSV EDITOR
- Load and edit CSV file
- Add/remove properties manually
- Save changes

TAB 3: AUTO SCRAPER
- Set maximum properties to scrape
- Set delay between properties
- Start/stop scraping
- View real-time scraping log
- Progress bar shows completion

TAB 4: PIPEDRIVE SYNC
- Check New Properties: See what's in Pipedrive but not in database
- Check Stage Changes: See which deals moved to different stages
- Sync Stage Changes: Update database with Pipedrive changes
- Full Sync: Complete sync from Pipedrive to database
- Remove Duplicates: Clean up duplicate entries


⚠️ TROUBLESHOOTING:
────────────────────────────────────────────────────────────────────────────────

Problem: "API key invalid" or "Authentication failed"
Solution: Update config.ini with correct ScrapingBee or Pipedrive API key

Problem: "Database locked" or "Database is locked"
Solution: Close DB Browser for SQLite before running the application

Problem: "No properties found" during scraping
Solution: Check that scraping_urls.txt contains valid Zillow search URLs

Problem: "Config file not found"
Solution: Application will auto-create config.ini with default values

Problem: Application won't start
Solution: Make sure all files are in the same folder, especially config.ini


📞 SUPPORT:
────────────────────────────────────────────────────────────────────────────────
For technical support or questions:
Email: support@yourdomain.com
Phone: +1-XXX-XXX-XXXX


═══════════════════════════════════════════════════════════════════════════════
Version 1.0 | Last Updated: 2026-02-01
═══════════════════════════════════════════════════════════════════════════════

