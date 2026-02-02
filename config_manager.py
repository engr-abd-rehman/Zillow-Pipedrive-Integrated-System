#!/usr/bin/env python3
"""
Configuration Manager for Zillow Pipedrive System
Reads settings from config.ini file
Falls back to defaults if config file is missing
"""

import configparser
import os

class ConfigManager:
    """Manages configuration from config.ini file"""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Default values (fallback if config.ini missing)
        self.defaults = {
            'SCRAPINGBEE': {
                'api_key': 'YOUR_API_KEY'
            },
            'PIPEDRIVE': {
                'api_token': 'YOUR_API_KEY',
                'api_url': 'https://api.pipedrive.com/v1'
            },
            'DATABASE': {
                'db_path': 'data/zillow.db'
            },
            'CSV': {
                'csv_path': 'zillow_florida_data.csv'
            },
            'URLS': {
                'urls_file': 'scraping_urls.txt'
            }
        }
        
        # Load config
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                print(f"✅ Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"⚠️ Error reading config file: {e}")
                print(f"⚠️ Using default configuration")
                self.create_default_config()
        else:
            print(f"⚠️ Config file not found: {self.config_file}")
            print(f"✅ Creating default config.ini...")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default config.ini file"""
        for section, values in self.defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in values.items():
                self.config.set(section, key, value)
        
        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            print(f"✅ Created default config file: {self.config_file}")
        except Exception as e:
            print(f"⚠️ Could not create config file: {e}")
    
    def get(self, section, key, fallback=None):
        """Get configuration value"""
        try:
            return self.config.get(section, key)
        except:
            # Fallback to defaults
            if section in self.defaults and key in self.defaults[section]:
                return self.defaults[section][key]
            return fallback
    
    # Convenience methods for common settings
    
    def get_scrapingbee_api_key(self):
        """Get ScrapingBee API key"""
        return self.get('SCRAPINGBEE', 'api_key')
    
    def get_pipedrive_api_token(self):
        """Get Pipedrive API token"""
        return self.get('PIPEDRIVE', 'api_token')
    
    def get_pipedrive_api_url(self):
        """Get Pipedrive API URL"""
        return self.get('PIPEDRIVE', 'api_url')
    
    def get_database_path(self):
        """Get database path"""
        return self.get('DATABASE', 'db_path')
    
    def get_csv_path(self):
        """Get CSV file path"""
        return self.get('CSV', 'csv_path')
    
    def get_urls_file(self):
        """Get URLs file path"""
        return self.get('URLS', 'urls_file')


# Global config instance
_config = None

def get_config():
    """Get global config instance"""
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config

