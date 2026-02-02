@echo off
REM Quick launcher for Zillow Scraper UI
REM Alternative to launch_integrated_system.bat

echo Starting Zillow Scraper UI...
python zillow_pipedrive_ui.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start UI
    echo.
    echo Possible solutions:
    echo 1. Install Python: python.org
    echo 2. Install PyQt5: pip install PyQt5
    echo 3. Install requests: pip install requests
    echo 4. Install beautifulsoup4: pip install beautifulsoup4
    echo.
    pause
)

