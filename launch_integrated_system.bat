@echo off
REM Zillow Scraper System Launcher
REM Launches the PyQt5 UI

echo ========================================
echo   Zillow Scraper System
echo ========================================
echo.
echo Starting UI...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyQt5 is not installed
    echo Installing PyQt5...
    pip install PyQt5
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo ERROR: requests is not installed
    echo Installing requests...
    pip install requests
)

python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo ERROR: beautifulsoup4 is not installed
    echo Installing beautifulsoup4...
    pip install beautifulsoup4
)

REM Launch UI
echo.
echo Launching Zillow Scraper UI...
echo.
python zillow_integrated_ui.py

REM If UI closes with error
if errorlevel 1 (
    echo.
    echo ERROR: UI failed to start
    echo Check the error message above
    pause
)

