#!/usr/bin/env python3
"""
Enhanced version of your working scraper with JSON extraction for more properties
"""

import requests
import csv
import json
import time
import re
import urllib.parse
from bs4 import BeautifulSoup

# Configuration
SCRAPER_API_KEY = '91b405af27e201a62e346fefbdca9664'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

def get_client_urls():
    """Get the 10 client-provided URLs directly in code"""
    client_urls = [
        # 1. AS-IS Properties
        "https://www.zillow.com/fl/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A34.639525177290345%2C%22south%22%3A20.393022319423494%2C%22east%22%3A-71.15933732812502%2C%22west%22%3A-96.44986467187502%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22att%22%3A%7B%22value%22%3A%22AS-IS%22%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A6%2C%22category%22%3A%22cat1%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22usersSearchTerm%22%3A%22Florida%22%2C%22schoolId%22%3Anull%7D",

        # 2. INVESTOR SPECIAL
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22INVESTOR%20SPECIAL%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 3. INVESTOR opportunity
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22INVESTOR%20opportunity%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 4. NEEDS WORK
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22NEEDS%20WORK%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 5. OUTDATED
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22OUTDATED%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 6. DATED
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22DATED%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 7. FIXER UPPER
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22FIXER%20UPPER%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 8. MOTIVATED
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22MOTIVATED%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 9. TLC (Tender Loving Care)
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22TLC%22%7D%7D%2C%22isListVisible%22%3Atrue%7D",

        # 10. DATED (Duplicate for more coverage)
        "https://www.zillow.com/fl/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-109.09512834375002%2C%22east%22%3A-58.51407365625002%2C%22south%22%3A12.669268671208503%2C%22north%22%3A41.0022787229105%7D%2C%22mapZoom%22%3A5%2C%22usersSearchTerm%22%3A%22FL%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A14%2C%22regionType%22%3A2%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22days%22%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22price%22%3A%7B%22min%22%3A100000%2C%22max%22%3A400000%7D%2C%22mp%22%3A%7B%22min%22%3A504%2C%22max%22%3A2015%7D%2C%22beds%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A2%2C%22max%22%3Anull%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22gar%22%3A%7B%22value%22%3Atrue%7D%2C%22sqft%22%3A%7B%22min%22%3A1000%2C%22max%22%3Anull%7D%2C%22lot%22%3A%7B%22min%22%3A0%2C%22max%22%3A43560%2C%22units%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A1970%2C%22max%22%3Anull%7D%2C%2255plus%22%3A%7B%22value%22%3A%22e%22%7D%2C%22att%22%3A%7B%22value%22%3A%22DATED%22%7D%7D%2C%22isListVisible%22%3Atrue%7D"
    ]

    print(f"✅ Loaded {len(client_urls)} client URLs directly from code")
    return client_urls

def build_zillow_url(page_number, url_index=0):
    """Build ScraperAPI URL using client's provided URLs - Sequential processing"""
    client_urls = get_client_urls()

    if not client_urls:
        print("❌ No client URLs found!")
        return None

    # Use specific URL index (for sequential processing)
    if url_index >= len(client_urls):
        print(f"❌ URL index {url_index} out of range (max: {len(client_urls)-1})")
        return None

    base_url = client_urls[url_index]

    # Add pagination to the URL if it doesn't have it
    if '_p/' not in base_url:
        # Insert pagination before the query parameters
        if '?' in base_url:
            url_parts = base_url.split('?', 1)
            base_url = f"{url_parts[0]}{page_number}_p/?{url_parts[1]}"
        else:
            base_url = f"{base_url}{page_number}_p/"
    else:
        # Replace existing pagination
        import re
        base_url = re.sub(r'/\d+_p/', f'/{page_number}_p/', base_url)

    # Build ScraperAPI URL
    scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(base_url)}"

    # Get URL filter name for display
    filter_names = ["AS-IS", "INVESTOR SPECIAL", "INVESTOR opportunity", "NEEDS WORK", "OUTDATED",
                   "DATED", "FIXER UPPER", "MOTIVATED", "TLC", "DATED (Extra)"]
    filter_name = filter_names[url_index] if url_index < len(filter_names) else f"URL {url_index + 1}"

    print(f"🔄 Using {filter_name} (URL {url_index + 1}/{len(client_urls)}) for page {page_number}")
    return scraper_url

def load_existing_urls_from_csv():
    existing_urls = set()
    try:
        with open('zillow_florida_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) > 7:  # URL column index (8th column = index 7) - FIXED
                    url = row[7].strip()  # URL column is at index 7 - FIXED
                    if url and url != 'N/A':  # Only add valid URLs
                        existing_urls.add(url)
        print(f"📋 Loaded {len(existing_urls)} existing properties from CSV")
        if existing_urls:
            print(f"🔍 First few existing URLs: {list(existing_urls)[:3]}")
    except FileNotFoundError:
        print("📄 No existing CSV file found, starting fresh")
        with open('zillow_florida_data.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Address', 'Beds', 'Baths', 'Sqft', 'Price', 'Agent_Name', 'Agent_Phone', 'URL'])
    return existing_urls

def is_rental_property(price_text):
    """Check if property is rental (price per month)"""
    if not price_text or price_text == 'N/A':
        return False

    # Check for rental indicators
    rental_indicators = ['/mo', '/month', 'per month', 'monthly', 'rent']
    price_lower = price_text.lower()

    for indicator in rental_indicators:
        if indicator in price_lower:
            return True

    return False

def extract_properties_from_json(html_content):
    """ENHANCED: Extract more properties from JSON data"""
    properties = []
    
    try:
        print("🔍 Extracting properties from JSON data...")
        
        zpid_pattern = r'"zpid":"([^"]+)"'
        zpid_matches = re.finditer(zpid_pattern, html_content)
        
        zpid_contexts = []
        for match in zpid_matches:
            zpid = match.group(1)
            start = max(0, match.start() - 500)
            end = min(len(html_content), match.end() + 500)
            context = html_content[start:end]
            zpid_contexts.append((zpid, context))
        
        print(f"🆔 Found {len(zpid_contexts)} ZPID contexts in JSON")
        
        property_data = []
        for zpid, context in zpid_contexts:
            prop_data = {'zpid': zpid}
            
            patterns = {
                'address': r'"address":"([^"]+)"',
                'price': r'"price":"([^"]+)"',
                'detailUrl': r'"detailUrl":"([^"]+)"'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, context)
                if match:
                    value = match.group(1).strip('"')
                    prop_data[field] = value
            
            if 'address' in prop_data:
                property_data.append(prop_data)
        
        # Remove duplicates based on ZPID
        unique_properties = {}
        for prop in property_data:
            zpid = prop.get('zpid')
            if zpid and (zpid not in unique_properties or len(prop) > len(unique_properties[zpid])):
                unique_properties[zpid] = prop
        
        # Convert to expected format and filter out rentals
        for prop_data in unique_properties.values():
            price = prop_data.get('price', 'N/A')

            # Skip rental properties
            if is_rental_property(price):
                print(f"🔄 Skipping rental property: {prop_data.get('address', 'N/A')} - Price: {price}")
                continue

            prop = {
                'address': prop_data.get('address', 'N/A'),
                'price': price,
                'beds': 'N/A',
                'baths': 'N/A',
                'area': 'N/A',
                'detailUrl': prop_data.get('detailUrl', 'N/A')
            }
            properties.append(prop)
        
        print(f"✅ Successfully extracted {len(properties)} unique properties from JSON")
        
    except Exception as e:
        print(f"❌ Error extracting from JSON: {str(e)}")
    
    return properties

def fetch_properties(page):
    """ENHANCED: Your original function with JSON extraction added"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url = build_zillow_url(page)
            print(f"🔍 Fetching page {page} (Attempt {attempt + 1}/{max_retries})...")
            print(f"🌐 URL: {url}")

            # Your original timeout and retry logic (UNCHANGED)
            response = requests.get(url, headers=HEADERS, timeout=90)
            print(f"📊 Response Status: {response.status_code}")

            response.raise_for_status()
            break  # Success, exit retry loop

        except requests.exceptions.Timeout:
            print(f"⏰ Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed due to timeout")
                return []
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print(f"❌ All {max_retries} attempts failed")
                return []

    try:
        # Parse HTML to extract properties (ORIGINAL WORKING METHOD)
        soup = BeautifulSoup(response.text, 'html.parser')
        property_cards = soup.find_all("article", {"data-test": "property-card"})
        print(f"✅ Found {len(property_cards)} property cards")

        properties = []

        # Your original HTML parsing logic (RESTORED)
        for card in property_cards:
                try:
                    prop = {}

                    # Extract address
                    address_element = card.find("address")
                    if not address_element:
                        address_element = card.select_one('a[data-test="property-card-link"] address')
                    if address_element:
                        prop['address'] = address_element.get_text(strip=True)
                    else:
                        prop['address'] = 'N/A'

                    # Extract price
                    price_element = card.find("span", {"data-test": "property-card-price"})
                    if price_element:
                        prop['price'] = price_element.get_text(strip=True)
                    else:
                        prop['price'] = 'N/A'

                    # Extract beds, baths, sqft
                    prop['beds'] = 'N/A'
                    prop['baths'] = 'N/A'
                    prop['area'] = 'N/A'

                    # Your original detail extraction logic (UNCHANGED)
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
                            elif ('sqft' in text or 'sq ft' in text or 'ft²' in text) and prop['area'] == 'N/A':
                                if any(char.isdigit() for char in text):
                                    prop['area'] = element.get_text(strip=True)

                    # Extract URL
                    link_element = card.find("a", {"data-test": "property-card-link"})
                    if link_element and link_element.get('href'):
                        href = link_element['href'].split('?')[0]
                        if href.startswith('/homedetails'):
                            prop['detailUrl'] = href
                        elif href.startswith('https://www.zillow.com/homedetails'):
                            prop['detailUrl'] = href.replace('https://www.zillow.com', '')
                        else:
                            prop['detailUrl'] = href
                    else:
                        prop['detailUrl'] = 'N/A'

                    properties.append(prop)

                except Exception as e:
                    print(f"❌ Error parsing property card: {str(e)}")
                    continue

        print(f"✅ Successfully parsed {len(properties)} properties")

        # Debug: Show first property if available
        if properties:
            print(f"🔍 First property: {properties[0]}")

        return properties

    except Exception as e:
        print(f"❌ Error fetching page {page}: {str(e)}")
        print(f"❌ Response text (first 500 chars): {response.text[:500] if 'response' in locals() else 'No response'}")
        return []

# SIMPLIFIED: Working agent extraction (FIXED)
def get_agent_info(detail_url):
    try:
        if not detail_url or detail_url == 'N/A':
            return {'agent_name': 'N/A', 'agent_phone': 'N/A'}

        # Ensure proper URL construction
        if detail_url.startswith('https://'):
            zillow_url = detail_url
        elif detail_url.startswith('/'):
            zillow_url = f"https://www.zillow.com{detail_url}"
        else:
            zillow_url = f"https://www.zillow.com/{detail_url}"

        encoded_zillow_url = urllib.parse.quote(zillow_url, safe=':/?#[]@!$&\'()*+,;=')
        full_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={encoded_zillow_url}"

        print(f"🔍 Extracting agent info from: {zillow_url}")

        # Simple request with retry
        max_retries = 2
        for attempt in range(max_retries):
            try:
                res = requests.get(full_url, headers=HEADERS, timeout=45)
                res.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    return {'agent_name': 'N/A', 'agent_phone': 'N/A'}
                time.sleep(3)

        agent = {'agent_name': 'N/A', 'agent_phone': 'N/A'}

        # Parse HTML
        soup = BeautifulSoup(res.content, 'html.parser')

        # Method 1: Simple seller attribution check (MOST RELIABLE)
        seller_attr = soup.find('div', {'data-testid': 'seller-attribution'})
        if seller_attr:
            print(f"   ✅ Found seller-attribution div")

            # Get all spans in seller attribution
            spans = seller_attr.find_all('span')
            print(f"   📋 Found {len(spans)} spans")

            # Look for agent name and phone in spans
            for i, span in enumerate(spans):
                span_text = span.get_text(strip=True)
                print(f"   Span {i+1}: '{span_text}'")

                # Check if this is a phone number
                if re.match(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', span_text):
                    # Clean phone number (remove trailing comma)
                    clean_phone = re.sub(r'[,\s]+$', '', span_text).strip()
                    if agent['agent_phone'] == 'N/A':  # Only set if not already found
                        agent['agent_phone'] = clean_phone
                        print(f"   ✅ Found phone: {clean_phone}")

                # Check if this is an agent name (not "Listed by:" and has 2+ words)
                elif (span_text and
                      not span_text.startswith('Listed by') and
                      not span_text.startswith('Listing provided by') and
                      len(span_text.split()) >= 2 and
                      len(span_text) > 5 and
                      not re.match(r'^\d', span_text) and
                      agent['agent_name'] == 'N/A'):  # Only set if not already found
                    agent['agent_name'] = span_text
                    print(f"   ✅ Found agent name: {span_text}")

            # If we found both, return immediately
            if agent['agent_name'] != 'N/A' and agent['agent_phone'] != 'N/A':
                print(f"   🎯 Complete agent info found!")
                return agent

        # Method 2: JSON extraction (RESTORED - THIS WAS WORKING!)
        if agent['agent_name'] == 'N/A' or agent['agent_phone'] == 'N/A':
            print(f"   🔄 Trying JSON extraction...")

            # JSON patterns that were working before
            json_patterns = [
                # Standard patterns
                r'"listingAgent":(\{.*?\})',
                r'"agent":\s*\{[^}]*"name":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',
                r'"contactAgent"[^}]*"name":\s*"([^"]+)"[^}]*"phone":\s*"([^"]+)"',
                r'"listingAgentName":\s*"([^"]+)".*?"listingAgentPhone":\s*"([^"]+)"',

                # Enhanced patterns for better extraction
                r'"agentName":\s*"([^"]+)"[^}]*"agentPhoneNumber":\s*"([^"]+)"',
                r'"displayName":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',
                r'"agentDisplayName":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',
                r'"listingAgentDisplayName":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',

                # Contact patterns
                r'"contactInfo"[^}]*"name":\s*"([^"]+)"[^}]*"phone":\s*"([^"]+)"',
                r'"agentContact"[^}]*"displayName":\s*"([^"]+)"[^}]*"phoneNumber":\s*"([^"]+)"',
                r'"primaryAgent"[^}]*"name":\s*"([^"]+)"[^}]*"phone":\s*"([^"]+)"'
            ]

            for i, pattern in enumerate(json_patterns, 1):
                match = re.search(pattern, res.text)
                if match:
                    try:
                        if i == 1:  # listingAgent object
                            agent_json = json.loads(match.group(1))
                            potential_name = agent_json.get('name', agent_json.get('displayName', 'N/A'))
                            potential_phone = agent_json.get('phoneNumber', agent_json.get('phone', 'N/A'))
                        else:  # Direct name/phone patterns
                            potential_name = match.group(1)
                            potential_phone = match.group(2) if len(match.groups()) > 1 else 'N/A'

                        # Update agent info if found
                        if potential_name and potential_name != 'N/A' and len(potential_name) > 2:
                            if agent['agent_name'] == 'N/A':
                                agent['agent_name'] = potential_name
                        if potential_phone and potential_phone != 'N/A':
                            if agent['agent_phone'] == 'N/A':
                                agent['agent_phone'] = potential_phone

                        if agent['agent_name'] != 'N/A' and agent['agent_phone'] != 'N/A':
                            print(f"   ✅ Found via JSON pattern {i}: {agent['agent_name']} - {agent['agent_phone']}")
                            break
                        elif agent['agent_name'] != 'N/A':
                            print(f"   ✅ Found agent name via JSON pattern {i}: {agent['agent_name']}")
                        elif agent['agent_phone'] != 'N/A':
                            print(f"   ✅ Found agent phone via JSON pattern {i}: {agent['agent_phone']}")

                    except Exception as e:
                        continue

        # Method 3: Simple text pattern search (FALLBACK)
        if agent['agent_name'] == 'N/A' or agent['agent_phone'] == 'N/A':
            print(f"   � Trying text pattern search...")

            # Simple patterns for name + phone combinations
            text_patterns = [
                # Pattern 1: "Name (phone)" or "Name phone"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[\(,]?\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',

                # Pattern 2: "Listed by: Name Phone"
                r'Listed\s+by[:\s]*([A-Za-z\s]+?)\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',

                # Pattern 3: "Name, phone"
                r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
            ]

            for i, pattern in enumerate(text_patterns, 1):
                match = re.search(pattern, res.text, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    potential_phone = match.group(2).strip()

                    # Validate name (reasonable length, not generic terms)
                    if (len(potential_name) > 5 and
                        len(potential_name) < 50 and
                        not any(word in potential_name.lower() for word in ['contact', 'agent', 'listing', 'phone'])):

                        if agent['agent_name'] == 'N/A':
                            agent['agent_name'] = potential_name
                        if agent['agent_phone'] == 'N/A':
                            agent['agent_phone'] = potential_phone

                        print(f"   ✅ Found via pattern {i}: {potential_name} - {potential_phone}")
                        break

        # Method 4: Contact buttons (SIMPLE)
        if agent['agent_name'] == 'N/A':
            contact_buttons = soup.find_all('button', string=re.compile(r'Contact.*', re.IGNORECASE))
            for button in contact_buttons:
                button_text = button.get_text(strip=True)
                if 'Contact' in button_text and len(button_text) > 8:
                    agent_name = button_text.replace('Contact', '').strip()
                    if agent_name and agent_name not in ['Agent', 'Listing Agent']:
                        agent['agent_name'] = agent_name
                        print(f"   ✅ Found agent via contact button: {agent_name}")
                        break

        # Method 5: Phone number search (SIMPLE)
        if agent['agent_phone'] == 'N/A':
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phone_matches = re.findall(phone_pattern, res.text)
            if phone_matches:
                for phone in phone_matches:
                    # Skip toll-free numbers
                    if not any(x in phone for x in ['800', '888', '877', '866', '844']):
                        agent['agent_phone'] = phone
                        print(f"   ✅ Found phone via search: {phone}")
                        break

        # Clean up phone number format
        if agent['agent_phone'] != 'N/A':
            phone_clean = re.sub(r'\D+', '', agent['agent_phone'])[-10:]
            if len(phone_clean) == 10:
                agent['agent_phone'] = f"({phone_clean[:3]}) {phone_clean[3:6]}-{phone_clean[6:]}"

        # Final result
        if agent['agent_name'] != 'N/A' or agent['agent_phone'] != 'N/A':
            print(f"   ✅ Agent extraction successful: {agent['agent_name']} - {agent['agent_phone']}")
        else:
            print(f"   ⚠️ No agent found - might be FSBO or private listing")

        return agent
    except Exception as e:
        print(f"❌ Error fetching agent info for {detail_url}: {str(e)}")
        print(f"❌ Agent extraction failed - URL: {detail_url}")

        # Try one more time with direct Zillow access (no ScraperAPI)
        try:
            print(f"   🔄 Trying direct access without ScraperAPI...")
            direct_response = requests.get(detail_url, headers=HEADERS, timeout=30)
            if direct_response.status_code == 200:
                soup = BeautifulSoup(direct_response.content, 'html.parser')

                # Quick seller attribution check
                seller_attr = soup.find('div', {'data-testid': 'seller-attribution'})
                if seller_attr:
                    spans = seller_attr.find_all('span')
                    if len(spans) >= 3:
                        for i, span in enumerate(spans):
                            span_text = span.get_text(strip=True)
                            if (span_text and
                                not span_text.startswith('Listed by') and
                                not re.match(r'^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', span_text) and
                                len(span_text.split()) >= 2):

                                # Found agent name, look for phone
                                for phone_span in spans:
                                    phone_text = phone_span.get_text(strip=True)
                                    phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', phone_text)
                                    if phone_match:
                                        print(f"   ✅ Direct access found: {span_text} - {phone_match.group(1)}")
                                        return {'agent_name': span_text, 'agent_phone': phone_match.group(1)}

                                # Return name even without phone
                                print(f"   ⚠️ Direct access found name only: {span_text}")
                                return {'agent_name': span_text, 'agent_phone': 'N/A'}
        except:
            pass

        # Final fallback - return N/A instead of generic values
        print(f"   ❌ All extraction methods failed")
        return {'agent_name': 'N/A', 'agent_phone': 'N/A'}

# Your original add_property_to_csv function (UNCHANGED)
def add_property_to_csv(address, beds, baths, sqft, price, agent_name, agent_phone, url):
    with open('zillow_florida_data.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([address, beds, baths, sqft, price, agent_name, agent_phone, url])

def get_property_details(detail_url):
    """Extract detailed property information from individual property page"""
    try:
        if not detail_url or detail_url == 'N/A':
            return {'beds': 'N/A', 'baths': 'N/A', 'sqft': 'N/A', 'price': 'N/A'}

        # Ensure proper URL construction
        if detail_url.startswith('https://'):
            zillow_url = detail_url
        elif detail_url.startswith('/'):
            zillow_url = f"https://www.zillow.com{detail_url}"
        else:
            zillow_url = f"https://www.zillow.com/{detail_url}"

        encoded_zillow_url = urllib.parse.quote(zillow_url, safe=':/?#[]@!$&\'()*+,;=')
        full_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={encoded_zillow_url}"
        res = requests.get(full_url, headers=HEADERS, timeout=60)
        res.raise_for_status()

        soup = BeautifulSoup(res.content, 'html.parser')

        property_details = {
            'beds': 'N/A',
            'baths': 'N/A',
            'sqft': 'N/A',
            'price': 'N/A'
        }

        # Extract price
        price_selectors = [
            'span[data-testid="price"]',
            '.ds-price .ds-value',
            '.notranslate'
        ]

        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem and '$' in price_elem.get_text():
                property_details['price'] = price_elem.get_text(strip=True)
                break

        # Extract property facts - Method 1: Factsheet
        facts_section = soup.find('div', {'data-testid': 'bdp-factsheet'})
        if facts_section:
            facts = facts_section.find_all('span')
            for fact in facts:
                text = fact.get_text(strip=True)
                # Look for clean patterns in factsheet
                if re.match(r'^\d{1,2}bd$', text.lower()) and property_details['beds'] == 'N/A':
                    property_details['beds'] = text
                elif re.match(r'^\d{1,2}ba$', text.lower()) and property_details['baths'] == 'N/A':
                    property_details['baths'] = text
                elif re.match(r'^[\d,]{3,6}sqft$', text.lower()) and property_details['sqft'] == 'N/A':
                    property_details['sqft'] = text

        # Method 2: Search all spans for patterns
        if property_details['beds'] == 'N/A' or property_details['baths'] == 'N/A' or property_details['sqft'] == 'N/A':
            all_spans = soup.find_all('span')
            for span in all_spans:
                text = span.get_text(strip=True)
                # Look for exact patterns like "3bd", "2ba", "1,200sqft"
                if re.match(r'^\d{1,2}bd$', text.lower()) and property_details['beds'] == 'N/A':
                    property_details['beds'] = text
                elif re.match(r'^\d{1,2}ba$', text.lower()) and property_details['baths'] == 'N/A':
                    property_details['baths'] = text
                elif re.match(r'^[\d,]{3,6}sqft$', text.lower()) and property_details['sqft'] == 'N/A':
                    property_details['sqft'] = text

        # Method 2.5: Look for individual numbers next to "beds", "baths", "sqft" (ENHANCED)
        if property_details['beds'] == 'N/A' or property_details['baths'] == 'N/A' or property_details['sqft'] == 'N/A':

            # Look for beds
            if property_details['beds'] == 'N/A':
                bed_spans = soup.find_all('span', string=re.compile(r'^\d{1,2}$'))
                for span in bed_spans:
                    next_span = span.find_next_sibling('span')
                    if next_span and 'bed' in next_span.get_text().lower():
                        beds_num = span.get_text().strip()
                        if 1 <= int(beds_num) <= 20:
                            property_details['beds'] = f"{beds_num}bd"
                            break

            # Look for baths
            if property_details['baths'] == 'N/A':
                bath_spans = soup.find_all('span', string=re.compile(r'^\d{1,2}$'))
                for span in bath_spans:
                    next_span = span.find_next_sibling('span')
                    if next_span and 'bath' in next_span.get_text().lower():
                        baths_num = span.get_text().strip()
                        if 1 <= int(baths_num) <= 20:
                            property_details['baths'] = f"{baths_num}ba"
                            break

            # Look for sqft
            if property_details['sqft'] == 'N/A':
                sqft_spans = soup.find_all('span', string=re.compile(r'^[\d,]{3,6}$'))
                for span in sqft_spans:
                    next_span = span.find_next_sibling('span')
                    if next_span and 'sqft' in next_span.get_text().lower():
                        sqft_num = span.get_text().strip()
                        property_details['sqft'] = f"{sqft_num}sqft"
                        break

        # Method 3: Look in structured data
        if property_details['beds'] == 'N/A' or property_details['baths'] == 'N/A' or property_details['sqft'] == 'N/A':
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if 'numberOfBedrooms' in data and property_details['beds'] == 'N/A':
                            property_details['beds'] = f"{data['numberOfBedrooms']}bd"
                        if 'numberOfBathroomsTotal' in data and property_details['baths'] == 'N/A':
                            property_details['baths'] = f"{data['numberOfBathroomsTotal']}ba"
                        if 'floorSize' in data and property_details['sqft'] == 'N/A':
                            property_details['sqft'] = f"{data['floorSize']}sqft"
                except:
                    continue

        return property_details

    except Exception as e:
        print(f"❌ Error extracting property details: {str(e)}")
        return {'beds': 'N/A', 'baths': 'N/A', 'sqft': 'N/A', 'price': 'N/A'}

# Your original main scraping function (UNCHANGED except for duplicate fix)
def scrape_zillow_complete():
    print("🚀 Starting Enhanced Zillow Florida Properties Scraper...")
    print("=" * 60)

    # Load existing URLs to avoid duplicates (FIXED)
    existing_urls = load_existing_urls_from_csv()

    page = 1
    total_new_properties = 0
    total_skipped = 0
    consecutive_empty_pages = 0

    while True:
        print(f"\n📄 Processing page {page}...")

        # Fetch properties from current page (ENHANCED)
        properties = fetch_properties(page)

        # If no properties found, check if we should stop
        if not properties:
            consecutive_empty_pages += 1
            print(f"❌ No properties found on page {page}")

            if consecutive_empty_pages >= 3:  # Stop after 3 consecutive empty pages
                print("🛑 Stopping: Found 3 consecutive empty pages")
                break
            else:
                page += 1
                continue
        else:
            consecutive_empty_pages = 0  # Reset counter

        print(f"✅ Found {len(properties)} properties on page {page}")

        page_new_count = 0
        page_skip_count = 0

        # Process each property
        for i, prop in enumerate(properties, 1):
            try:
                # Extract basic property data
                address = prop.get('address', 'N/A')
                beds = prop.get('beds', 'N/A')
                baths = prop.get('baths', 'N/A')
                sqft = prop.get('area', 'N/A')
                price = prop.get('price', 'N/A')
                detail_url = prop.get('detailUrl', 'N/A')

                # Create full URL for display and CSV
                if detail_url and detail_url != 'N/A':
                    if detail_url.startswith('https://'):
                        full_url = detail_url
                    elif detail_url.startswith('/'):
                        full_url = f"https://www.zillow.com{detail_url}"
                    else:
                        full_url = f"https://www.zillow.com/{detail_url}"
                else:
                    full_url = 'N/A'

                # Check for duplicates (FIXED)
                if full_url in existing_urls:
                    page_skip_count += 1
                    total_skipped += 1
                    print(f"⏭️  Property {i}/{len(properties)}: Skipped duplicate - {full_url}")
                    continue

                # New property - process it
                page_new_count += 1
                total_new_properties += 1

                print(f"\n🏠 Property {i}/{len(properties)} (New #{total_new_properties}):")
                print(f"📍 Address: {address}")
                print(f"💰 Price: {price}")
                print(f"🛏️  Beds: {beds} | 🚿 Baths: {baths} | 📐 Sqft: {sqft}")

                # Fetch agent details
                print(f"🔍 Fetching agent details...")
                agent_info = get_agent_info(detail_url)

                # Enhanced debug output - check for failed extraction
                if agent_info['agent_name'] == 'N/A' and agent_info['agent_phone'] == 'N/A':
                    print(f"⚠️  WARNING: No agent info found - retrying once...")
                    # Retry once more for failed results
                    time.sleep(2)  # Brief delay before retry
                    agent_info = get_agent_info(detail_url)

                print(f"👤 Agent: {agent_info['agent_name']}")
                print(f"📞 Phone: {agent_info['agent_phone']}")
                print(f"🔗 URL: {full_url}")

                # Add to CSV immediately (URL moved to last column)
                add_property_to_csv(
                    address, beds, baths, sqft, price,
                    agent_info['agent_name'], agent_info['agent_phone'], full_url
                )

                # Add to existing URLs set
                existing_urls.add(full_url)

                print("✅ Added to CSV")
                print("-" * 50)

                # Small delay to be polite
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ Error processing property {i}: {str(e)}")
                continue

        # Page summary
        print(f"\n📊 Page {page} Summary:")
        print(f"   🆕 New properties: {page_new_count}")
        print(f"   ⏭️  Skipped duplicates: {page_skip_count}")
        print(f"   📈 Total new so far: {total_new_properties}")
        print(f"   📈 Total skipped so far: {total_skipped}")

        page += 1

        # Small delay between pages
        time.sleep(1)

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 SCRAPING COMPLETED!")
    print(f"📊 Final Statistics:")
    print(f"   🆕 Total new properties added: {total_new_properties}")
    print(f"   ⏭️  Total duplicates skipped: {total_skipped}")
    print(f"   📄 Total pages processed: {page - 1}")
    print(f"   📁 Data saved to: zillow_florida_data.csv")
    print("=" * 60)

def complete_missing_details():
    """Complete missing details for existing properties"""
    print("🔧 Starting Property Details Completion")
    print("=" * 60)

    # Read existing properties
    properties = []
    try:
        with open('zillow_florida_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                properties.append(row)
    except FileNotFoundError:
        print("❌ No CSV file found")
        return

    print(f"📋 Found {len(properties)} properties")

    # Find incomplete properties
    incomplete_properties = []
    for i, prop in enumerate(properties):
        missing_fields = []

        if not prop.get('Beds', '').strip() or prop.get('Beds', '').strip() == 'N/A':
            missing_fields.append('Beds')
        if not prop.get('Baths', '').strip() or prop.get('Baths', '').strip() == 'N/A':
            missing_fields.append('Baths')
        if not prop.get('Sqft', '').strip() or prop.get('Sqft', '').strip() == 'N/A':
            missing_fields.append('Sqft')
        if not prop.get('Agent_Name', '').strip() or prop.get('Agent_Name', '').strip() == 'N/A':
            missing_fields.append('Agent_Name')
        if not prop.get('Agent_Phone', '').strip() or prop.get('Agent_Phone', '').strip() == 'N/A':
            missing_fields.append('Agent_Phone')

        if missing_fields and prop.get('URL', '').strip():
            prop['missing_fields'] = missing_fields
            prop['index'] = i
            incomplete_properties.append(prop)

    print(f"⚠️  Found {len(incomplete_properties)} incomplete properties with URLs")

    if not incomplete_properties:
        print("✅ All properties are complete!")
        return

    # Ask how many to process
    max_to_process = input(f"\nHow many properties to complete? (1-{len(incomplete_properties)}, or 'all'): ").strip()

    if max_to_process.lower() == 'all':
        properties_to_process = incomplete_properties
    else:
        try:
            max_count = int(max_to_process)
            properties_to_process = incomplete_properties[:max_count]
        except:
            print("❌ Invalid input, processing first 10 properties")
            properties_to_process = incomplete_properties[:10]

    print(f"\n🔍 Processing {len(properties_to_process)} properties...")

    # Process properties
    completed_count = 0

    for i, prop in enumerate(properties_to_process, 1):
        address = prop.get('Address', '')
        url = prop.get('URL', '')
        missing = prop.get('missing_fields', [])
        prop_index = prop.get('index', 0)

        print(f"\n🏠 Property {i}/{len(properties_to_process)}")
        print(f"   📍 Address: {address}")
        print(f"   🔗 URL: {url[:80]}...")
        print(f"   ⚠️  Missing: {', '.join(missing)}")

        updated_fields = []

        # Get property details
        if 'Beds' in missing or 'Baths' in missing or 'Sqft' in missing:
            print(f"   🔍 Getting property details...")
            property_details = get_property_details(url)

            if property_details['beds'] != 'N/A' and 'Beds' in missing:
                properties[prop_index]['Beds'] = property_details['beds']
                updated_fields.append(f"Beds: {property_details['beds']}")

            if property_details['baths'] != 'N/A' and 'Baths' in missing:
                properties[prop_index]['Baths'] = property_details['baths']
                updated_fields.append(f"Baths: {property_details['baths']}")

            if property_details['sqft'] != 'N/A' and 'Sqft' in missing:
                properties[prop_index]['Sqft'] = property_details['sqft']
                updated_fields.append(f"Sqft: {property_details['sqft']}")

        # Get agent info
        if 'Agent_Name' in missing or 'Agent_Phone' in missing:
            print(f"   🔍 Getting agent info...")
            agent_info = get_agent_info(url)

            if agent_info['agent_name'] != 'N/A' and 'Agent_Name' in missing:
                properties[prop_index]['Agent_Name'] = agent_info['agent_name']
                updated_fields.append(f"Agent: {agent_info['agent_name']}")

            if agent_info['agent_phone'] != 'N/A' and 'Agent_Phone' in missing:
                properties[prop_index]['Agent_Phone'] = agent_info['agent_phone']
                updated_fields.append(f"Phone: {agent_info['agent_phone']}")

        if updated_fields:
            print(f"      ✅ Updated: {', '.join(updated_fields)}")
            completed_count += 1
        else:
            print(f"      ⚠️  No new data found")

        # Rate limiting
        if i < len(properties_to_process):
            print(f"   ⏳ Waiting 4 seconds...")
            time.sleep(4)

    # Save updated data
    print(f"\n💾 Saving updated data...")

    headers = ['Address', 'Beds', 'Baths', 'Sqft', 'Price', 'Agent_Name', 'Agent_Phone', 'URL']

    with open('zillow_florida_data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for prop in properties:
            clean_row = {}
            for header in headers:
                clean_row[header] = prop.get(header, '').strip()
            writer.writerow(clean_row)

    print(f"\n🎉 COMPLETION SUMMARY:")
    print(f"   🎯 Properties processed: {len(properties_to_process)}")
    print(f"   ✅ Successfully completed: {completed_count}")
    print(f"   📁 Updated file: zillow_florida_data.csv")

if __name__ == "__main__":
    print("🎯 Enhanced Working Zillow Scraper")
    print("✅ Your original working code + JSON extraction for more properties")
    print("✅ Fixed duplicate detection + all your original features")
    print("\n" + "=" * 60)
    print("Choose option:")
    print("1. Start new scraping")
    print("2. Complete missing details for existing properties")

    choice = input("\nEnter choice (1/2): ").strip()

    if choice == '1':
        scrape_zillow_complete()
    elif choice == '2':
        complete_missing_details()
    else:
        print("❌ Invalid choice")
